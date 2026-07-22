"""
The catalogue of things that can be built on a plot.

Plain data, no Evennia imports, so it can be tested and extended without
touching the build command. Every entry carries three numbers and a picture:

  acres   -- how much of a plot it fills. A plot is eight acres (see
             world/fiefgrid.py), so a keep takes a whole one and a smithy leaves
             room for seven more things. This is the *space* limit, enforced in
             typeclasses/fiefs.py.
  timber  -- \\
  coin    -- / what it costs to raise, spent from the builder's purse. These are
             the *economic* limit, enforced in commands/fief.py's do_build. They
             are tunable in one line and do not touch any other system.
  icon    -- the glyph the web map draws for it. Decorative only: a screen
             reader never reads it (the map marks it aria-hidden and keeps the
             spoken name in the cell's label), so it helps sighted players
             without taking anything away from blind ones.

Adding a building type is still a single line here -- it just has more on it now.

Names are matched leniently -- by unique prefix -- because a player typing by
ear should not have to spell "barracks" exactly to find out what it costs.
"""

CATALOGUE = {
    "cottage":  {"acres": 1, "timber": 5,  "coin": 20,  "icon": "🏠", "desc": "housing for a tenant family"},
    "smithy":   {"acres": 1, "timber": 4,  "coin": 30,  "icon": "🔨", "desc": "a forge and anvil"},
    "chapel":   {"acres": 2, "timber": 8,  "coin": 60,  "icon": "⛪", "desc": "a small place of worship"},
    "granary":  {"acres": 2, "timber": 10, "coin": 40,  "icon": "🌾", "desc": "dry storage for grain"},
    "sawmill":  {"acres": 3, "timber": 12, "coin": 50,  "icon": "🪚", "desc": "cuts timber into planks"},
    "barracks": {"acres": 4, "timber": 20, "coin": 120, "icon": "🛡️", "desc": "quarters for a garrison"},
    "millpond": {"acres": 4, "timber": 6,  "coin": 80,  "icon": "💧", "desc": "impounded water to drive a mill"},
    "orchard":  {"acres": 6, "timber": 4,  "coin": 40,  "icon": "🌳", "desc": "fruit trees in rows"},
    "keep":     {"acres": 8, "timber": 40, "coin": 400, "icon": "🏰", "desc": "a fortified tower; fills a whole plot"},
}

# Drawn when a stored structure names a kind that has since left the catalogue,
# so an old save still shows *something* on the map rather than a blank.
DEFAULT_ICON = "▪"


class UnknownStructure(ValueError):
    """Raised when a structure name matches nothing, or matches too much."""


def article(name):
    """"a sawmill", but "an orchard"."""
    return "an" if name[:1].lower() in "aeiou" else "a"


def display_name(name):
    """The name as it should be spoken, e.g. "a sawmill"."""
    return f"{article(name)} {name}"


def find(text):
    """
    Resolve typed text to a catalogue entry.

    Returns (name, entry). Raises UnknownStructure if nothing matches, or if a
    prefix is ambiguous -- and says which options it was torn between, so the
    player can hear how to narrow it.
    """
    if not text or not text.strip():
        raise UnknownStructure("Build what?")
    key = text.strip().lower()
    if key in CATALOGUE:
        return key, CATALOGUE[key]
    matches = sorted(name for name in CATALOGUE if name.startswith(key))
    if not matches:
        raise UnknownStructure(
            f"There is nothing called '{text.strip()}' to build. "
            "Type 'build' on its own to hear the whole catalogue."
        )
    if len(matches) > 1:
        raise UnknownStructure(
            f"'{text.strip()}' could mean " + " or ".join(matches) + "."
        )
    return matches[0], CATALOGUE[matches[0]]


def icon_for(kind):
    """The map glyph for a catalogue kind, or a neutral mark if it is unknown."""
    entry = CATALOGUE.get(kind or "")
    return entry["icon"] if entry else DEFAULT_ICON


def format_catalogue():
    """
    The whole catalogue, cheapest first.

    Ordered by acre cost rather than alphabetically: a player deciding what
    fits in the room they have left cares about size before spelling. Each line
    reads the space it takes and then what it costs, so a player weighing a
    purchase hears all three numbers in one breath.
    """
    lines = ["You can build:"]
    for name in sorted(CATALOGUE, key=lambda n: (CATALOGUE[n]["acres"], n)):
        entry = CATALOGUE[name]
        acres = entry["acres"]
        plural = "" if acres == 1 else "s"
        lines.append(
            f"  {name} -- {acres} acre{plural}, "
            f"{entry['timber']} timber, {entry['coin']} coin, {entry['desc']}."
        )
    return "\n".join(lines)
