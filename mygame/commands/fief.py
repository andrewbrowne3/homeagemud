"""
Fief land navigation.

Text-first navigation over a fief's 81 plots. A player is not walking the land
here -- they are moving a survey cursor over it, the way they would run a finger
over a map -- so nothing in this module moves a character between rooms.

Everything a player can do by clicking, they can do by typing, because the map
UI and the commands both call the same `do_*` functions (the convention used by
the scene commands in commands/command.py). Announcements are terse by default
(`where`) with detail on request (`survey`), because narrating a full plot
description on every step makes moving three squares by ear unbearable.
"""

from evennia.commands.command import Command as BaseCommand

from world import fiefgrid, structures

from .command import _session_from_caller


def _reply(character, session, msg=None, oob_cmd=None, oob_payload=None):
    """
    Answer the player.

    Text goes to the character rather than the session: a character always has
    somewhere to send output, whereas a session may be absent (a command run
    from a script, or under test), and land commands must never fall silent.
    The session is used only for the optional OOB payload a map UI listens for.
    """
    if msg:
        character.msg(msg)
    if oob_cmd and session:
        session.msg(**{oob_cmd: (tuple(), oob_payload or {})})


# Character attributes holding the survey cursor.
CURRENT_FIEF_ATTR = "fief_current"
CURSOR_ATTR = "fief_cursor"

DEFAULT_CURSOR = "C.C"  # start dead centre, an easy landmark to return to


# -------------------------------------------------------------
# cursor state
# -------------------------------------------------------------


def current_fief(character):
    """The fief this character is currently surveying, or None."""
    return character.attributes.get(CURRENT_FIEF_ATTR, default=None)


def cursor_of(character):
    """Where the survey cursor sits, defaulting to the centre of the fief."""
    return character.attributes.get(CURSOR_ATTR, default=DEFAULT_CURSOR)


def set_cursor(character, address):
    character.attributes.add(CURSOR_ATTR, fiefgrid.normalize(address))


def _require_fief(character, session):
    """Fetch the surveyed fief, explaining how to pick one if there isn't one."""
    fief = current_fief(character)
    if not fief:
        _reply(character, session, msg="You are not surveying any fief. Use: fief <name>")
        return None
    return fief


# -------------------------------------------------------------
# rendering
# -------------------------------------------------------------


def _structure_phrase(structures):
    if not structures:
        return "Nothing stands here."
    parts = [f"{s['name']} ({s.get('acres', 0)} acres)" for s in structures]
    return "Standing here: " + ", ".join(parts) + "."


def format_position(fief, address, verbose=False):
    """
    Describe where the cursor is.

    Terse form is one line -- the tracking line a player can ask for over and
    over without it costing them anything. Verbose adds contents and the
    neighbouring plots, for building a mental picture of the surroundings.
    """
    summary = fief.plot_summary(address)
    used, total = summary["acres_used"], summary["acres_total"]
    headline = (
        f"{summary['spoken'].capitalize()} ({summary['address']}). "
        f"{summary['bearing']}. {used} of {total} acres used."
    )
    if not verbose:
        return headline

    lines = [headline, _structure_phrase(summary["structures"])]
    neighbours = []
    for direction in ("north", "east", "south", "west"):
        neighbour = fiefgrid.step(address, direction)
        if neighbour is None:
            neighbours.append(f"{direction}, the edge of the fief")
        else:
            neighbours.append(f"{direction}, {fiefgrid.speak(neighbour)}")
    lines.append("Around you: " + "; ".join(neighbours) + ".")
    return "\n".join(lines)


def format_fief_overview(fief):
    """The whole fief as nine wards, always in the same reading order."""
    lines = [
        f"{fief.key} -- {fiefgrid.ACRES_PER_FIEF} acres in "
        f"{fiefgrid.WARDS_PER_FIEF} wards."
    ]
    for ward in fiefgrid.READ_ORDER:
        s = fief.ward_summary(ward)
        structures = (
            "nothing built" if not s["structures"]
            else f"{s['structures']} structure" + ("s" if s["structures"] != 1 else "")
        )
        lines.append(
            f"  {s['number']}. {s['name']} ward ({s['ward']}): {structures}, "
            f"{s['acres_used']} of {s['acres_total']} acres used."
        )
    return "\n".join(lines)


def format_ward(fief, ward):
    """A ward's nine plots, always in the same reading order."""
    summary = fief.ward_summary(ward)
    lines = [
        f"{summary['name'].capitalize()} ward ({summary['ward']}), ward "
        f"{summary['number']} of 9: {summary['acres_used']} of "
        f"{summary['acres_total']} acres used."
    ]
    for address in fiefgrid.plots_in(ward):
        plot = fief.plot_summary(address)
        cell = fiefgrid.parse_address(address)[1]
        contents = (
            "empty" if not plot["structures"]
            else ", ".join(s["name"] for s in plot["structures"])
        )
        lines.append(
            f"  {fiefgrid.CELL_NAMES[cell]} ({address}): {contents}, "
            f"{plot['acres_used']} of {plot['acres_total']} acres used."
        )
    return "\n".join(lines)


def _payload(fief, address):
    """
    OOB payload so a map UI renders exactly what the text describes.

    Carries both levels at once -- all nine wards and all nine plots of the
    current ward -- so zooming in and out is instant and never disagrees with
    what was just announced. It is only eighteen small summaries; the saving
    from sending less is not worth a round trip mid-navigation.

    `cells` is in fiefgrid.READ_ORDER, so the client can lay out a 3x3 grid by
    index without knowing the compass scheme, and the reading order stays the
    same in the map as it is in the text.
    """
    address = fiefgrid.normalize(address)
    ward = fiefgrid.ward_of(address)
    return {
        "fief": fief.key,
        "cursor": address,
        "ward": fief.ward_summary(ward),
        "plot": fief.plot_summary(address),
        "order": list(fiefgrid.READ_ORDER),
        "wards": [fief.ward_summary(name) for name in fiefgrid.READ_ORDER],
        "plots": [fief.plot_summary(plot) for plot in fiefgrid.plots_in(ward)],
        "acres_per_plot": fiefgrid.ACRES_PER_PLOT,
        "acres_per_ward": fiefgrid.ACRES_PER_WARD,
    }


# -------------------------------------------------------------
# actions -- shared by the commands below and by web OOB input
# -------------------------------------------------------------


def do_select_fief(character, session, name=None):
    """Choose which fief to survey."""
    if not name:
        fief = current_fief(character)
        if not fief:
            _reply(character, session, msg="You are not surveying any fief. Use: fief <name>")
            return
        _reply(character, session, msg=format_fief_overview(fief),
               oob_cmd="fief_overview", oob_payload=_payload(fief, cursor_of(character)))
        return

    fief = character.search(name, global_search=True,
                            typeclass="typeclasses.fiefs.Fief")
    if not fief:
        return  # search() already reported the failure
    character.attributes.add(CURRENT_FIEF_ATTR, fief)
    set_cursor(character, DEFAULT_CURSOR)
    _reply(
        character,
        session,
        msg=f"Surveying {fief.key}. Cursor at {fiefgrid.speak(DEFAULT_CURSOR)}.\n"
            + format_fief_overview(fief),
        oob_cmd="fief_overview",
        oob_payload=_payload(fief, DEFAULT_CURSOR),
    )


def do_where(character, session):
    """Announce the cursor position. Terse, and cheap to ask repeatedly."""
    fief = _require_fief(character, session)
    if not fief:
        return
    address = cursor_of(character)
    _reply(character, session, msg=f"{fief.key}: {format_position(fief, address)}",
           oob_cmd="fief_where", oob_payload=_payload(fief, address))


def do_survey(character, session, target=None):
    """Full detail of a plot or ward; no argument means the cursor's plot."""
    fief = _require_fief(character, session)
    if not fief:
        return
    if not target:
        address = cursor_of(character)
        _reply(character, session, msg=format_position(fief, address, verbose=True),
               oob_cmd="fief_survey", oob_payload=_payload(fief, address))
        return
    try:
        ward, plot = fiefgrid.parse_address(target)
    except fiefgrid.BadAddress as err:
        _reply(character, session, msg=str(err))
        return
    if plot is None:
        _reply(character, session, msg=format_ward(fief, ward),
               oob_cmd="fief_ward", oob_payload={"fief": fief.key,
                                                 "ward": fief.ward_summary(ward)})
        return
    address = f"{ward}.{plot}"
    _reply(character, session, msg=format_position(fief, address, verbose=True),
           oob_cmd="fief_survey", oob_payload=_payload(fief, address))


def do_step(character, session, direction=None):
    """
    Move the cursor one plot.

    Leaving the fief gives a distinct boundary cue rather than silently staying
    put, and crossing into a new ward is announced, so a player moving by ear
    always knows which of the two happened.
    """
    fief = _require_fief(character, session)
    if not fief:
        return
    if not fiefgrid.parse_direction(direction or ""):
        _reply(character, session, msg="Step which way? north, south, east, west, "
                            "northeast, northwest, southeast or southwest.")
        return

    here = cursor_of(character)
    there = fiefgrid.step(here, direction)
    if there is None:
        _reply(character, session, msg=fiefgrid.edge_cue(here, direction))
        return

    set_cursor(character, there)
    crossed = fiefgrid.ward_of(there) != fiefgrid.ward_of(here)
    prefix = (
        f"Crossing into {fiefgrid.speak(fiefgrid.ward_of(there))}. " if crossed else ""
    )
    _reply(character, session, msg=prefix + format_position(fief, there),
           oob_cmd="fief_moved", oob_payload=_payload(fief, there))


def _target_plot(character, session, where, verb):
    """
    The plot an action applies to: an explicit address, else the cursor.

    Returns None if the address was unusable, having already explained why --
    callers just bail. Defaulting to the cursor is what lets a player step to a
    plot and then act without naming it.
    """
    if not where:
        return cursor_of(character)
    try:
        ward, plot = fiefgrid.parse_address(where)
    except fiefgrid.BadAddress as err:
        _reply(character, session, msg=str(err))
        return None
    if plot is None:
        _reply(character, session,
               msg=f"Name a single plot to {verb}, such as NE.C, "
                   "not a whole ward.")
        return None
    return f"{ward}.{plot}"


def may_alter(character, fief):
    """
    Whether this character may change what stands on this fief.

    Covers both raising and pulling down -- the right to build and the right to
    demolish are the same right here. Returns (ok, reason). A fief with no house
    set is unclaimed and open to anyone, which keeps testing and early play
    simple; once a fief is held, only that house may alter it.
    """
    house = (fief.attributes.get("house", default="n/a") or "n/a").strip()
    if house.lower() in ("", "n/a", "none"):
        return True, ""
    mine = (character.attributes.get("house", default="n/a") or "n/a").strip()
    if mine.lower() == house.lower():
        return True, ""
    return False, f"{fief.key} is held by {house}. You may not alter its land."


def do_build(character, session, what=None, where=None):
    """
    Raise a structure on a plot.

    With no arguments this reads the catalogue instead of failing, so a player
    can always discover what is available and what it costs without having to
    remember a separate command. `where` defaults to the survey cursor, so the
    common case is: step to the plot, then say what to build.
    """
    fief = _require_fief(character, session)
    if not fief:
        return
    if not what:
        _reply(character, session, msg=structures.format_catalogue())
        return

    try:
        kind, entry = structures.find(what)
    except structures.UnknownStructure as err:
        _reply(character, session, msg=str(err))
        return

    address = _target_plot(character, session, where, verb="build on")
    if address is None:
        return

    allowed, reason = may_alter(character, fief)
    if not allowed:
        _reply(character, session, msg=reason)
        return

    name = structures.display_name(kind)
    ok, msg = fief.add_structure(address, name, entry["acres"], kind=kind)
    if not ok:
        _reply(character, session, msg=msg)
        return

    free = fief.acres_free(address)
    taken = entry["acres"]
    _reply(
        character,
        session,
        msg=(f"You raise {name} on {fiefgrid.speak(address)} ({address}). "
             f"{taken} acre{'' if taken == 1 else 's'} taken, {free} of "
             f"{fiefgrid.ACRES_PER_PLOT} left."),
        oob_cmd="fief_built",
        oob_payload=_payload(fief, address),
    )


def _standing_here(fief, address):
    """What is on a plot, as a spoken list for prompts and error messages."""
    standing = fief.structures_at(address)
    if not standing:
        return "Nothing stands there."
    return "Standing there: " + ", ".join(s["name"] for s in standing) + "."


def do_demolish(character, session, what=None, where=None):
    """
    Pull down a structure, freeing its acres.

    With no argument this reads back what is standing on the plot rather than
    failing, so a player can always hear their options. Where several of the
    same thing stand together, one is taken down and the rest are accounted
    for out loud -- guessing silently would leave a player unsure what changed.
    """
    fief = _require_fief(character, session)
    if not fief:
        return

    address = _target_plot(character, session, where, verb="demolish on")
    if address is None:
        return

    standing = fief.structures_at(address)
    if not standing:
        _reply(character, session,
               msg=f"Nothing stands on {fiefgrid.speak(address)} to pull down.")
        return
    if not what:
        _reply(character, session,
               msg=f"{_standing_here(fief, address)} "
                   "Say which to pull down, e.g. demolish sawmill.")
        return

    allowed, reason = may_alter(character, fief)
    if not allowed:
        _reply(character, session, msg=reason)
        return

    key = what.strip().lower()
    matches = [
        (i, s) for i, s in enumerate(standing)
        if s.get("kind", "").startswith(key) or key in s["name"].lower()
    ]
    if not matches:
        _reply(character, session,
               msg=f"There is no '{what.strip()}' on {fiefgrid.speak(address)}. "
                   + _standing_here(fief, address))
        return

    kinds = sorted({s.get("kind") or s["name"] for _, s in matches})
    if len(kinds) > 1:
        _reply(character, session,
               msg=f"'{what.strip()}' could mean " + " or ".join(kinds) + ".")
        return

    index, target = matches[0]
    ok, removed = fief.remove_structure(address, index)
    if not ok:
        _reply(character, session, msg="That is no longer standing there.")
        return

    freed = removed.get("acres", 0)
    remaining = len(matches) - 1
    tail = ""
    if remaining:
        plural = "" if remaining == 1 else "s"
        verb = "stands" if remaining == 1 else "stand"
        tail = f" {remaining} more {kinds[0]}{plural} still {verb} here."
    _reply(
        character,
        session,
        msg=(f"You pull down {removed['name']} on {fiefgrid.speak(address)} "
             f"({address}). {freed} acre{'' if freed == 1 else 's'} freed, "
             f"{fief.acres_free(address)} of {fiefgrid.ACRES_PER_PLOT} "
             f"now open.{tail}"),
        oob_cmd="fief_demolished",
        oob_payload=_payload(fief, address),
    )


def do_goto(character, session, target=None):
    """Jump the cursor straight to an address, for players who know the way."""
    fief = _require_fief(character, session)
    if not fief:
        return
    if not target:
        _reply(character, session, msg="Go where? Give a plot address, such as NE.C.")
        return
    try:
        ward, plot = fiefgrid.parse_address(target)
    except fiefgrid.BadAddress as err:
        _reply(character, session, msg=str(err))
        return
    if plot is None:
        # a bare ward means its centre -- the natural place to arrive
        plot = "C"
    address = f"{ward}.{plot}"
    set_cursor(character, address)
    _reply(character, session, msg=format_position(fief, address),
           oob_cmd="fief_moved", oob_payload=_payload(fief, address))


# -------------------------------------------------------------
# commands
# -------------------------------------------------------------


class CmdFief(BaseCommand):
    """
    Survey a fief you hold, ward by ward.

    Usage:
      fief            -- overview of the fief you are surveying
      fief <name>     -- begin surveying a named fief

    The fief is nine wards, each nine plots. Wards are always listed in the
    same order -- northwest, north, northeast, then west, center, east, then
    southwest, south, southeast -- so the layout stays memorable.
    """

    key = "fief"
    locks = "cmd:all()"
    help_category = "Land"

    def func(self):
        do_select_fief(self.caller, _session_from_caller(self.caller),
                       name=self.args.strip() if self.args else None)


class CmdWhere(BaseCommand):
    """
    Say where your survey cursor is, in one line.

    Usage: where

    Cheap to ask as often as you like -- this is how you keep track of your
    place. Use `survey` when you want the full detail.
    """

    key = "where"
    locks = "cmd:all()"
    help_category = "Land"

    def func(self):
        do_where(self.caller, _session_from_caller(self.caller))


class CmdSurvey(BaseCommand):
    """
    Describe a plot or a whole ward in full.

    Usage:
      survey              -- the plot your cursor is on, and its neighbours
      survey <ward>       -- all nine plots of a ward, e.g. survey NE
      survey <plot>       -- one plot in detail, e.g. survey NE.C
    """

    key = "survey"
    locks = "cmd:all()"
    help_category = "Land"

    def func(self):
        do_survey(self.caller, _session_from_caller(self.caller),
                  target=self.args.strip() if self.args else None)


class CmdStep(BaseCommand):
    """
    Move your survey cursor one plot across the land.

    Usage: step <direction>

    Directions are north, south, east, west and the four diagonals, and may be
    abbreviated (n, se). Ward boundaries are crossed as you come to them and
    announced; the edge of the fief stops you with a distinct message.
    """

    key = "step"
    locks = "cmd:all()"
    help_category = "Land"

    def func(self):
        do_step(self.caller, _session_from_caller(self.caller),
                direction=self.args.strip() if self.args else None)


class CmdBuild(BaseCommand):
    """
    Raise a structure on a plot of your land.

    Usage:
      build                      -- hear everything you can build, and its cost
      build <thing>              -- build on the plot your cursor is on
      build <thing> at <plot>    -- e.g. build sawmill at NE.C

    Each plot holds eight acres, so what fits depends on what is already there.
    Names may be shortened as long as they stay unambiguous.
    """

    key = "build"
    locks = "cmd:all()"
    help_category = "Land"

    def func(self):
        args = (self.args or "").strip()
        what, where = args, None
        if " at " in args:
            what, where = [part.strip() for part in args.split(" at ", 1)]
        do_build(self.caller, _session_from_caller(self.caller),
                 what=what or None, where=where or None)


class CmdDemolish(BaseCommand):
    """
    Pull down a structure, freeing the acres it stood on.

    Usage:
      demolish                    -- hear what stands on your cursor's plot
      demolish <thing>            -- pull it down on the plot your cursor is on
      demolish <thing> at <plot>  -- e.g. demolish sawmill at NE.C

    If several of the same thing stand on one plot, one is taken down and you
    are told how many remain.
    """

    key = "demolish"
    aliases = ["raze"]
    locks = "cmd:all()"
    help_category = "Land"

    def func(self):
        args = (self.args or "").strip()
        what, where = args, None
        if " at " in args:
            what, where = [part.strip() for part in args.split(" at ", 1)]
        do_demolish(self.caller, _session_from_caller(self.caller),
                    what=what or None, where=where or None)


class CmdGoto(BaseCommand):
    """
    Send your survey cursor straight to an address.

    Usage:
      goto <plot>    -- e.g. goto NE.C
      goto <ward>    -- e.g. goto NE, arriving at that ward's center plot
    """

    key = "goto"
    locks = "cmd:all()"
    help_category = "Land"

    def func(self):
        do_goto(self.caller, _session_from_caller(self.caller),
                target=self.args.strip() if self.args else None)
