"""
Input functions

Handle OOB commands sent from the webclient via ``Evennia.msg(cmdname, args, kwargs)``.
"""

from commands.command import (
    do_create_scene,
    do_join_scene,
    do_leave_scene,
    do_list_scenes,
)
from commands.fief import (
    do_build,
    do_demolish,
    do_goto,
    do_select_fief,
    do_step,
    do_survey,
    do_where,
)


def _account(session):
    return session.account


def _character(session):
    """The puppeted character; land commands act on the character, not account."""
    return session.puppet


def createscene(session, *args, **kwargs):
    title = kwargs.get("title", "").strip()
    description = kwargs.get("description", "").strip()
    do_create_scene(_account(session), session, title, description)


def joinscene(session, *args, **kwargs):
    do_join_scene(
        _account(session),
        session,
        scene_id=kwargs.get("scene_id"),
        title=kwargs.get("title"),
    )


def leavescene(session, *args, **kwargs):
    do_leave_scene(
        _account(session),
        session,
        scene_id=kwargs.get("scene_id"),
        title=kwargs.get("title"),
    )


def listscenes(session, *args, **kwargs):
    # called from the webclient on auto-refresh; keep it silent (no chat spam)
    do_list_scenes(_account(session), session, verbose=False)


# -- land -------------------------------------------------------
# A map UI sends these; they call the same functions as the typed commands, so
# clicking a plot and typing "goto NE.C" cannot drift apart.


def fief(session, *args, **kwargs):
    do_select_fief(_character(session), session, name=kwargs.get("name"))


def fiefwhere(session, *args, **kwargs):
    do_where(_character(session), session)


def fiefsurvey(session, *args, **kwargs):
    do_survey(_character(session), session, target=kwargs.get("address"))


def fiefstep(session, *args, **kwargs):
    do_step(_character(session), session, direction=kwargs.get("direction"))


def fiefgoto(session, *args, **kwargs):
    do_goto(_character(session), session, target=kwargs.get("address"))


def fiefbuild(session, *args, **kwargs):
    do_build(_character(session), session,
             what=kwargs.get("what"), where=kwargs.get("address"))


def fiefdemolish(session, *args, **kwargs):
    do_demolish(_character(session), session,
                what=kwargs.get("what"), where=kwargs.get("address"))
