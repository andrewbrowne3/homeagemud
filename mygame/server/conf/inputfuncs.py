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


def _account(session):
    return session.account


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
    do_list_scenes(_account(session), session)
