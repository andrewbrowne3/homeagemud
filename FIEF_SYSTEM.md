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
  cottage -- 1 acre, 5 timber, 20 coin, housing for a tenant family.
  smithy -- 1 acre, 4 timber, 30 coin, a forge and anvil.
  chapel -- 2 acres, 8 timber, 60 coin, a small place of worship.
  granary -- 2 acres, 10 timber, 40 coin, dry storage for grain.
  sawmill -- 3 acres, 12 timber, 50 coin, cuts timber into planks.
  barracks -- 4 acres, 20 timber, 120 coin, quarters for a garrison.
  millpond -- 4 acres, 6 timber, 80 coin, impounded water to drive a mill.
  orchard -- 6 acres, 4 timber, 40 coin, fruit trees in rows.
  keep -- 8 acres, 40 timber, 400 coin, a fortified tower; fills a whole plot.

> build sawmill at NE.C
You raise a sawmill on the center plot of northeast ward (NE.C).
3 acres taken, 5 of 8 left. 12 timber, 50 coin spent; 88 timber and 950 coin remain.

> build orchard
No room: the center plot of northeast ward has 5 of 8 acres open,
and that needs 6.

> build keep
You cannot afford a keep: it needs 40 timber (you have 12) and 400 coin (you have 50).
```

Every refusal tells you the number — whether it's acres that won't fit or a purse
that won't stretch — so a player never has to go and check somewhere else. Adding
a new building type to that catalogue is still one line; it just carries a price
now.

Two costs are in play. **Acres** are the room a plot has (a plot is eight of
them); **timber and coin** are what the building costs to raise, spent from your
purse. `purse` (or `wallet`) says what you're holding. See the economy note
below for where timber and coin come from.

`demolish` (or `raze`) pulls something back down and frees its acres. It does not
refund timber or coin — pulling a thing down does not un-spend what it cost.

### The map

There's a **Map** button in the command bar. It shows nine squares. Click the
top-right one and that ward fills the panel as its own nine squares — the screen
Bob wanted. Arrow keys move, Enter zooms in, Escape backs out.

The map never gets busier as you go deeper. It's always nine squares, at every
level. That's what makes it work on a phone: you're never rendering 81 tiny
cells, you're rendering nine big ones and throwing away eight-ninths of the land
each time you go in.

The squares are big and each built thing draws as an **icon** — a keep 🏰, a
sawmill 🪚, an orchard 🌳 — so a sighted player reads a plot at a glance. At the
fief level, where a whole ward can hold nine plots' worth of building, each ward
shows a fill bar instead: how much of its land is spoken for. None of this costs
the text side anything: the icons are decorative and marked so a screen reader
skips them, still reading the same spoken description of what stands where. The
map serves both kinds of player from the one set of squares.

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

## Settled since the last round

- **648 acres stays.** It divides evenly by nine twice; the eight-acre plot is
  the unit.
- **Plots stay two levels, 8 acres each.** What got bigger was the *map* — larger
  squares with icons — not the land. Per-acre precision (a third level) remains a
  later option; the address scheme still allows it.
- **Demolishing large buildings does not ask "are you sure?"** It's fast and
  quiet, which is what a screen-reader player doing routine teardown wants.
- **Timber and coin are in.** Building now costs both, on top of acres (see the
  costs above), spent from a purse. What's still open is *how you earn them* —
  that decision is below.

## Decisions we still need from you

**1. Who is allowed to build?** Right now a fief with no house set is open to
anyone, and once a house holds it, only that house may build or demolish. That's
a placeholder. The real question is how building rights flow through homage — can
a lord grant a tenant the right to build on one ward? Can a steward act for an
absent lord? Does demolishing need more authority than building? This is the
biggest open item and it's a game-design question, not a technical one. (It's
also where the purse will likely move: a **house treasury** rather than a
personal one, once we know how a house is modelled.)

**2. How do players earn timber and coin?** The purse and the spending are
built, but for now resources only enter by a staff `grant`. You floated walking
into a plot to gather, or completing tasks for a payout, or structures producing
over time — any mix is possible, because every one of them will pour into the
same single doorway the code already routes through. This is the next real piece
of the economy.

---

## What exists today

Working and tested: the layout and addressing, text navigation with position
tracking, the building catalogue with acre capacity **and timber/coin costs**,
build and demolish, the purse and a staff `grant`, and the accessible web map
**with icons and ward fill-bars**. 96 automated tests cover it.

Not built yet: any way to *earn* timber or coin in play (only the staff grant so
far), ownership beyond the house placeholder above, structures as places you can
walk into (they're currently records on the land), and any way for a player to
be granted a fief in the first place — fiefs are created by an admin for now.
