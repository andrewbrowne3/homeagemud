# The Fief Land System

A walkthrough of how land works in HomageMUD, what's built and playable today,
and the handful of decisions still open.

---

## The layout

A fief is a square mile of land, divided the way you described: a tic-tac-toe
grid of **wards**, each ward itself a tic-tac-toe grid of **plots**.

```
        The whole fief                 Inside the northeast ward
   ┌──────┬──────┬──────┐           ┌──────┬──────┬──────┐
   │  NW  │  N   │  NE  │           │  NW  │  N   │  NE  │
   │  1   │  2   │  3   │           │      │      │      │
   ├──────┼──────┼──────┤           ├──────┼──────┼──────┤
   │  W   │  C   │  E   │  ──────►  │  W   │  C   │  E   │
   │  4   │  5   │  6   │           │      │      │      │
   ├──────┼──────┼──────┤           ├──────┼──────┼──────┤
   │  SW  │  S   │  SE  │           │  SW  │  S   │  SE  │
   │  7   │  8   │  9   │           │      │      │      │
   └──────┴──────┴──────┘           └──────┴──────┴──────┘
      648 acres, 9 wards                72 acres, 9 plots
                                        8 acres per plot
```

Wards are numbered the way you counted them — left to right, top to bottom — so
**the top-right corner is ward 3**, exactly as in your example. Alongside the
numbers every ward and plot has a compass name, and the names are what the game
actually speaks: "the center plot of the northeast ward," written `NE.C`.

**81 plots in total, 8 acres each.**

### A note on the acreage

You said a square mile, 640 acres. The system uses **648**. The reason is that
648 divides evenly by nine twice — 648 → 72 per ward → 8 per plot — where 640
gives 71.1 and then 7.9. Eight acres of trailing decimals in every acre count,
forever, versus eight acres of difference from a literal square mile. If you'd
rather have exactly 640 and live with the fractions, it's a one-line change.

### The thing worth deciding

Your example said players click "the acres they want to build on." With two
levels, the smallest thing a player can click is an **8-acre plot**, not an
acre. That may well be right — 81 plots is already a lot of land to manage — but
it's worth saying out loud:

- **Two levels (what's built):** 81 plots, 8 acres each. A plot holds several
  buildings side by side.
- **Three levels:** 729 plots, just under an acre each. True per-acre building,
  but a lot more drilling to get anywhere.

The address scheme was built so a third level can be added later without
changing anything else. `NE.C` simply becomes `NE.C.SW`.

---

## Playing it

### Looking around

A player brings up their fief and hears the whole square mile at once:

```
> fief Ashford
Surveying Ashford. Cursor at the center plot of center ward.
Ashford -- 648 acres in 9 wards.
  1. northwest ward (NW): nothing built, 0 of 72 acres used.
  2. north ward (N): nothing built, 0 of 72 acres used.
  3. northeast ward (NE): 2 structures, 5 of 72 acres used.
  ...
```

Then they go to the corner they care about — Bob's top-right — and it fills the
screen on its own:

```
> survey NE
Northeast ward (NE), ward 3 of 9: 5 of 72 acres used.
  northwest (NE.NW): empty, 0 of 8 acres used.
  north (NE.N): a millpond, 4 of 8 acres used.
  center (NE.C): a sawmill, a granary, 5 of 8 acres used.
  ...
```

### Building

```
> build
You can build:
  cottage -- 1 acre, housing for a tenant family.
  smithy -- 1 acre, a forge and anvil.
  chapel -- 2 acres, a small place of worship.
  granary -- 2 acres, dry storage for grain.
  sawmill -- 3 acres, cuts timber into planks.
  barracks -- 4 acres, quarters for a garrison.
  millpond -- 4 acres, impounded water to drive a mill.
  orchard -- 6 acres, fruit trees in rows.
  keep -- 8 acres, a fortified tower; fills a whole plot.

> build sawmill at NE.C
You raise a sawmill on the center plot of northeast ward (NE.C).
3 acres taken, 5 of 8 left.

> build orchard
No room: the center plot of northeast ward has 5 of 8 acres open,
and that needs 6.
```

Every refusal tells you the number, so a player never has to go and check
somewhere else whether a thing will fit. Adding a new building type to that
catalogue is one line — it's a list, not code.

`demolish` (or `raze`) pulls something back down and frees its acres.

### The map

There's a **Map** button in the command bar. It shows nine squares. Click the
top-right one and that ward fills the panel as its own nine squares — the screen
Bob wanted. Arrow keys move, Enter zooms in, Escape backs out.

The map never gets busier as you go deeper. It's always nine squares, at every
level. That's what makes it work on a phone: you're never rendering 81 tiny
cells, you're rendering nine big ones and throwing away eight-ninths of the land
each time you go in.

---

## Built for blind players first

This shaped the whole design, so it's worth explaining what it bought us.

The grid isn't only a way to fit land on a small screen. It's a **coordinate
system a player can hold in their head**. Nobody remembers "plot 43." Everybody
remembers "the center of the northeast ward." Two levels of nine chunk 648 acres
into pieces that are memorable, and the compass names double as directions — the
address tells you where you are *and* which way to walk.

Concretely:

- **`where` is one line and free to repeat.** That's the tracking line — a
  player asks it as often as they like without being buried in text. `survey` is
  the verbose one, for when they want the detail.
- **The reading order never changes.** Wards and plots are always read
  northwest, north, northeast, then west, center, east, then southwest, south,
  southeast. Never sorted by what's most active. A fixed order is what lets
  someone memorise the shape of their land after a few passes.
- **Crossing a ward is announced; the fief edge sounds different.** *"Crossing
  into the north ward"* versus *"The fief ends there."* A player moving by ear
  always knows which of the two just happened.
- **Both walking and jumping.** `step north` to explore, `goto NE.C` when you
  know where you're going. Navigating blind without a teleport is exhausting.
- **Nothing is map-only.** Every single thing the map can do can be typed, and
  the map is literally driven by the same commands underneath. For some players
  the text *is* the whole interface.

The map itself is built as a proper accessible grid — a screen reader treats it
as a grid natively, announces each square as you arrive, and the map's arrow
keys never steal the command line's arrow keys or focus.

---

## Where a player's position lives

One deliberate choice worth knowing: a player using these commands is **not
walking around on the land**. They're moving a survey cursor over a map, the way
you'd run a finger across a chart, while standing wherever they actually are.

That's what your example described — Bob managing his holdings, not hiking to
the northeast corner. It also means the land doesn't need 81 rooms per fief.
If you later want players to physically walk their fields, that's a separate
layer built on the same addresses.

---

## Decisions we need from you

**1. Who is allowed to build?** Right now a fief with no house set is open to
anyone, and once a house holds it, only that house may build or demolish. That's
a placeholder. The real question is how building rights flow through homage — can
a lord grant a tenant the right to build on one ward? Can a steward act for an
absent lord? Does demolishing need more authority than building? This is the
biggest open item and it's a game-design question, not a technical one.

**2. Plot size.** 8-acre plots, or add a third level for near-acre precision?
(See above.)

**3. 648 acres or exactly 640?** (See above.)

**4. Should demolishing a large building ask "are you sure?"** Right now it
doesn't — `demolish keep` takes down eight acres of masonry instantly. A
confirmation on everything would be tedious for a screen-reader player doing
routine teardown; a confirmation only above some size threshold might be the
right balance.

**5. What does building actually cost?** At the moment it costs acres and
nothing else. No timber, no coin, no time to construct, and demolishing refunds
nothing. Whenever the economy arrives, this is where it plugs in.

---

## What exists today

Working and tested: the layout and addressing, text navigation with position
tracking, the building catalogue with capacity limits, build and demolish, and
the accessible web map. 83 automated tests cover it.

Not built yet: ownership beyond the placeholder above, any economy, structures
as places you can walk into (they're currently records on the land), and any way
for a player to be granted a fief in the first place — fiefs are created by an
admin for now.
