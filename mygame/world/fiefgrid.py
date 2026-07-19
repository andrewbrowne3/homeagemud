"""
Fief land geometry.

A fief is a square mile of land laid out as a 3x3 grid of *wards*, each ward
itself a 3x3 grid of *plots* -- 81 plots in all. Every plot has a compass
address: "NE.C" is the centre plot of the northeast ward.

The nesting is a memory aid, not a zoom level. "The centre of the northeast
ward" is something a player can hold in their head and say out loud; "plot 43"
is not. Two levels of nine chunk the land into pieces small enough to memorise,
and the compass names double as directions -- the address tells you both where
you are and which way to walk.

The same address also flattens to a 9x9 coordinate grid, so a player can step
one plot at a time and cross ward boundaries without the hierarchy getting in
the way. Zoom (nine big cells at a time) and pan (one plot at a time) are two
views of this one model; neither is a degraded version of the other.

Coordinates are (x, y) with x running 0..8 west to east and y running 0..8
south to north, so "north" is always +y.

This module deliberately imports nothing from Evennia: it is pure geometry and
naming, and can be tested on its own.
"""

# A fief is nominally a square mile (640 acres). We use 648 so that it divides
# evenly by nine twice -- 648 -> 72 per ward -> 8 per plot -- which keeps every
# acre count in the game an exact integer.
ACRES_PER_PLOT = 8
PLOTS_PER_WARD = 9
WARDS_PER_FIEF = 9
ACRES_PER_WARD = ACRES_PER_PLOT * PLOTS_PER_WARD  # 72
ACRES_PER_FIEF = ACRES_PER_WARD * WARDS_PER_FIEF  # 648

GRID_SIZE = 9  # the flattened fief is 9x9 plots

# Offsets of each cell within a 3x3 block, as (dx, dy) with y increasing north.
CELL_OFFSETS = {
    "NW": (0, 2), "N": (1, 2), "NE": (2, 2),
    "W":  (0, 1), "C": (1, 1), "E":  (2, 1),
    "SW": (0, 0), "S": (1, 0), "SE": (2, 0),
}

# Always read a 3x3 block in this order -- top row west to east, then middle,
# then bottom. Never sort by contents or activity: a fixed order is what lets a
# player memorise the shape of their land after a few passes.
READ_ORDER = ["NW", "N", "NE", "W", "C", "E", "SW", "S", "SE"]

CELL_NAMES = {
    "NW": "northwest", "N": "north", "NE": "northeast",
    "W": "west", "C": "center", "E": "east",
    "SW": "southwest", "S": "south", "SE": "southeast",
}

# Compass steps, again with y increasing north.
DIRECTIONS = {
    "north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0),
    "northeast": (1, 1), "northwest": (-1, 1),
    "southeast": (1, -1), "southwest": (-1, -1),
}

DIRECTION_ALIASES = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "ne": "northeast", "nw": "northwest",
    "se": "southeast", "sw": "southwest",
    "up": "north", "down": "south", "left": "west", "right": "east",
}


class BadAddress(ValueError):
    """Raised when a land address cannot be parsed."""


def parse_direction(text):
    """
    Resolve a direction name or alias to its canonical name.

    Accepts arrow-key names too ("left", "up"), so the web client can send the
    same command a player would type. Returns None if unrecognised.
    """
    if not text:
        return None
    key = text.strip().lower()
    key = DIRECTION_ALIASES.get(key, key)
    return key if key in DIRECTIONS else None


def parse_address(text):
    """
    Parse a land address into a (ward, plot) tuple; plot is None for a whole ward.

    Accepts "NE", "ne.c", "NE C" and "ne/c" alike -- players typing by ear
    should not have to remember a separator.
    """
    if not text:
        raise BadAddress("No address given.")
    parts = text.replace("/", " ").replace(".", " ").split()
    if not parts or len(parts) > 2:
        raise BadAddress(f"'{text}' is not a land address.")
    cells = []
    for part in parts:
        cell = part.strip().upper()
        if cell not in CELL_OFFSETS:
            raise BadAddress(f"'{part}' is not a ward or plot name.")
        cells.append(cell)
    ward = cells[0]
    plot = cells[1] if len(cells) == 2 else None
    return ward, plot


def normalize(text):
    """Return the canonical spelling of an address, e.g. "ne c" -> "NE.C"."""
    ward, plot = parse_address(text)
    return f"{ward}.{plot}" if plot else ward


def to_xy(address):
    """Convert a full plot address to (x, y) on the flattened 9x9 grid."""
    ward, plot = parse_address(address)
    if plot is None:
        raise BadAddress(f"'{address}' names a ward, not a single plot.")
    wx, wy = CELL_OFFSETS[ward]
    px, py = CELL_OFFSETS[plot]
    return wx * 3 + px, wy * 3 + py


def from_xy(x, y):
    """Convert (x, y) on the flattened 9x9 grid back to a plot address."""
    if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
        raise BadAddress(f"({x}, {y}) is outside the fief.")
    ward = _cell_at(x // 3, y // 3)
    plot = _cell_at(x % 3, y % 3)
    return f"{ward}.{plot}"


def _cell_at(dx, dy):
    for name, offset in CELL_OFFSETS.items():
        if offset == (dx, dy):
            return name
    raise BadAddress(f"No cell at offset ({dx}, {dy}).")


def step(address, direction):
    """
    Move one plot in a direction.

    Returns the new address, or None if that step would leave the fief -- the
    caller is expected to give a distinct boundary cue rather than silently
    staying put, so a player moving by ear can feel the edge.
    """
    canonical = parse_direction(direction)
    if canonical is None:
        raise BadAddress(f"'{direction}' is not a direction.")
    dx, dy = DIRECTIONS[canonical]
    x, y = to_xy(address)
    nx, ny = x + dx, y + dy
    if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
        return None
    return from_xy(nx, ny)


def ward_of(address):
    """The ward an address belongs to."""
    return parse_address(address)[0]


def plots_in(ward):
    """All nine plot addresses of a ward, in fixed reading order."""
    name = parse_address(ward)[0]
    return [f"{name}.{cell}" for cell in READ_ORDER]


def ward_number(ward):
    """
    The ward's 1-9 number, counting row-major from the northwest corner.

    Ward 3 is therefore the northeast corner. Numbers are for display only --
    the compass names are what get spoken and stored.
    """
    name = parse_address(ward)[0]
    return READ_ORDER.index(name) + 1


def speak(address):
    """
    Say an address aloud, e.g. "NE.C" -> "the center plot of the northeast ward".

    This is the phrase a screen reader announces on arrival, so it reads as
    English rather than as coordinates.
    """
    ward, plot = parse_address(address)
    ward_phrase = f"the {CELL_NAMES[ward]} ward"
    if plot is None:
        return ward_phrase
    return f"the {CELL_NAMES[plot]} plot of {CELL_NAMES[ward]} ward"


def bearing(address):
    """
    Describe a plot's position within the whole fief as counted steps.

    Gives a player a second, numeric way to track where they are -- useful for
    holding a position in mind, and for saying it to someone else.
    """
    x, y = to_xy(address)
    return f"{x + 1} east, {y + 1} north, of 9"


def edge_cue(address, direction):
    """The boundary message for a step that would leave the fief."""
    canonical = parse_direction(direction) or direction
    return f"The fief ends there. You are at its {canonical}ern edge."
