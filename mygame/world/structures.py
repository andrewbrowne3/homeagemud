"""
The catalogue of things that can be built on a plot.

Plain data, no Evennia imports, so it can be tested and extended without
touching the build command. Acre costs are what make a plot fill up: a plot is
eight acres (see world/fiefgrid.py), so a keep takes a whole one and a smithy
leaves room for seven more things.

Names are matched leniently -- by unique prefix -- because a player typing by
ear should not have to spell "barracks" exactly to find out what it costs.
"""

CATALOGUE = {
    "cottage":  {"acres": 1, "desc": "housing for a tenant family"},
    "smithy":   {"acres": 1, "desc": "a forge and anvil"},
    "chapel":   {"acres": 2, "desc": "a small place of worship"},
    "granary":  {"acres": 2, "desc": "dry storage for grain"},
    "sawmill":  {"acres": 3, "desc": "cuts timber into planks"},
    "barracks": {"acres": 4, "desc": "quarters for a garrison"},
    "millpond": {"acres": 4, "desc": "impounded water to drive a mill"},
    "orchard":  {"acres": 6, "desc": "fruit trees in rows"},
    "keep":     {"acres": 8, "desc": "a fortified tower; fills a whole plot"},
}


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


def format_catalogue():
    """
    The whole catalogue, cheapest first.

    Ordered by acre cost rather than alphabetically: a player deciding what
    fits in the room they have left cares about size before spelling.
    """
    lines = ["You can build:"]
    for name in sorted(CATALOGUE, key=lambda n: (CATALOGUE[n]["acres"], n)):
        entry = CATALOGUE[name]
        acres = entry["acres"]
        plural = "" if acres == 1 else "s"
        lines.append(f"  {name} -- {acres} acre{plural}, {entry['desc']}.")
    return "\n".join(lines)
