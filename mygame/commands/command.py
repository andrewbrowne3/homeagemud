"""
Commands

Commands describe the input the account can do to the game.

"""

import evennia
from evennia.commands.command import Command as BaseCommand
from evennia.utils.search import search_channel

SCENE_TAG = "scene"
SCENE_TAG_CATEGORY = "chat"


def _scene_channels():
    """All channels tagged as user-created scenes."""
    from evennia.comms.models import ChannelDB
    return ChannelDB.objects.get_by_tag(key=SCENE_TAG, category=SCENE_TAG_CATEGORY)


def scene_payload(channel):
    subs = channel.subscriptions.all()
    return {
        "id": channel.id,
        "title": channel.key,
        "description": channel.db.desc or "",
        "members": [acc.username for acc in subs],
        "member_count": len(subs),
    }


def _resolve_channel(scene_id=None, title=None):
    if scene_id:
        from evennia.comms.models import ChannelDB
        return ChannelDB.objects.filter(id=scene_id).first()
    if title:
        matches = search_channel(title, exact=True)
        return matches[0] if matches else None
    return None


def _resolve_account(caller):
    """Given a caller (Account or Character/Session), return the Account."""
    if hasattr(caller, "username"):
        return caller
    account = getattr(caller, "account", None)
    if account:
        return account
    # sessions have .account
    return None


def _reply(session, msg=None, oob_cmd=None, oob_payload=None):
    if msg and session:
        session.msg(text=msg)
    if oob_cmd and session:
        session.msg(**{oob_cmd: (tuple(), oob_payload or {})})


def _session_from_caller(caller):
    session = getattr(caller, "session", None)
    if session:
        return session
    sessions = getattr(caller, "sessions", None)
    if sessions and sessions.count():
        return sessions.get()[0]
    return None


def do_create_scene(account, session, title, description=""):
    if not title:
        _reply(session, msg="Usage: createscene <title>[=<description>]")
        return
    if search_channel(title, exact=True):
        _reply(session, msg=f"A scene named '{title}' already exists.")
        return
    channel = evennia.create_channel(
        title,
        desc=description,
        locks=f"control:id({account.id}) or perm(Admin);listen:all();send:all()",
        typeclass="typeclasses.channels.Channel",
    )
    channel.tags.add(SCENE_TAG, category=SCENE_TAG_CATEGORY)
    channel.connect(account)
    _reply(session, msg=f"Scene '{title}' created. You are now subscribed.",
           oob_cmd="scene_created", oob_payload=scene_payload(channel))


def do_join_scene(account, session, scene_id=None, title=None):
    channel = _resolve_channel(scene_id=scene_id, title=title)
    if not channel or not channel.tags.has(SCENE_TAG, category=SCENE_TAG_CATEGORY):
        _reply(session, msg="Scene not found.")
        return
    channel.connect(account)
    _reply(session, msg=f"Joined scene '{channel.key}'.",
           oob_cmd="scene_joined", oob_payload=scene_payload(channel))


def do_leave_scene(account, session, scene_id=None, title=None):
    channel = _resolve_channel(scene_id=scene_id, title=title)
    if not channel:
        _reply(session, msg="Scene not found.")
        return
    channel.disconnect(account)
    _reply(session, msg=f"Left scene '{channel.key}'.",
           oob_cmd="scene_left", oob_payload={"id": channel.id, "title": channel.key})


def do_list_scenes(account, session):
    scenes = [scene_payload(c) for c in _scene_channels()]
    _reply(session, oob_cmd="scene_list", oob_payload={"scenes": scenes})
    if not scenes:
        _reply(session, msg="No active scenes.")
        return
    lines = ["Active scenes:"]
    for s in scenes:
        lines.append(f"  [{s['id']}] {s['title']} ({s['member_count']} in)")
    _reply(session, msg="\n".join(lines))


class CmdCreateScene(BaseCommand):
    """
    Create a new roleplay scene (a temporary chat room).

    Usage: createscene <title>[=<description>]
    """

    key = "createscene"
    locks = "cmd:pperm(Player)"
    help_category = "Scenes"

    def func(self):
        title, description = "", ""
        if self.args:
            if "=" in self.args:
                title, description = [p.strip() for p in self.args.split("=", 1)]
            else:
                title = self.args.strip()
        account = _resolve_account(self.caller)
        session = _session_from_caller(self.caller)
        do_create_scene(account, session, title, description)


class CmdJoinScene(BaseCommand):
    """
    Join an existing scene.

    Usage: joinscene <title>
    """

    key = "joinscene"
    locks = "cmd:pperm(Player)"
    help_category = "Scenes"

    def func(self):
        account = _resolve_account(self.caller)
        session = _session_from_caller(self.caller)
        do_join_scene(account, session, title=self.args.strip() if self.args else None)


class CmdLeaveScene(BaseCommand):
    """
    Leave a scene.

    Usage: leavescene <title>
    """

    key = "leavescene"
    locks = "cmd:pperm(Player)"
    help_category = "Scenes"

    def func(self):
        account = _resolve_account(self.caller)
        session = _session_from_caller(self.caller)
        do_leave_scene(account, session, title=self.args.strip() if self.args else None)


class CmdListScenes(BaseCommand):
    """
    List active scenes.

    Usage: listscenes
    """

    key = "listscenes"
    locks = "cmd:pperm(Player)"
    help_category = "Scenes"

    def func(self):
        account = _resolve_account(self.caller)
        session = _session_from_caller(self.caller)
        do_list_scenes(account, session)


class Command(BaseCommand):
    """
    Base command (you may see this if a child command had no help text defined)

    Note that the class's `__doc__` string is used by Evennia to create the
    automatic help entry for the command, so make sure to document consistently
    here. Without setting one, the parent's docstring will show (like now).

    """

    # Each Command class implements the following methods, called in this order
    # (only func() is actually required):
    #
    #     - at_pre_cmd(): If this returns anything truthy, execution is aborted.
    #     - parse(): Should perform any extra parsing needed on self.args
    #         and store the result on self.
    #     - func(): Performs the actual work.
    #     - at_post_cmd(): Extra actions, often things done after
    #         every command, like prompts.
    #
    pass


# -------------------------------------------------------------
#
# The default commands inherit from
#
#   evennia.commands.default.muxcommand.MuxCommand.
#
# If you want to make sweeping changes to default commands you can
# uncomment this copy of the MuxCommand parent and add
#
#   COMMAND_DEFAULT_CLASS = "commands.command.MuxCommand"
#
# to your settings file. Be warned that the default commands expect
# the functionality implemented in the parse() method, so be
# careful with what you change.
#
# -------------------------------------------------------------

# from evennia.utils import utils
#
#
# class MuxCommand(Command):
#     """
#     This sets up the basis for a MUX command. The idea
#     is that most other Mux-related commands should just
#     inherit from this and don't have to implement much
#     parsing of their own unless they do something particularly
#     advanced.
#
#     Note that the class's __doc__ string (this text) is
#     used by Evennia to create the automatic help entry for
#     the command, so make sure to document consistently here.
#     """
#     def has_perm(self, srcobj):
#         """
#         This is called by the cmdhandler to determine
#         if srcobj is allowed to execute this command.
#         We just show it here for completeness - we
#         are satisfied using the default check in Command.
#         """
#         return super().has_perm(srcobj)
#
#     def at_pre_cmd(self):
#         """
#         This hook is called before self.parse() on all commands
#         """
#         pass
#
#     def at_post_cmd(self):
#         """
#         This hook is called after the command has finished executing
#         (after self.func()).
#         """
#         pass
#
#     def parse(self):
#         """
#         This method is called by the cmdhandler once the command name
#         has been identified. It creates a new set of member variables
#         that can be later accessed from self.func() (see below)
#
#         The following variables are available for our use when entering this
#         method (from the command definition, and assigned on the fly by the
#         cmdhandler):
#            self.key - the name of this command ('look')
#            self.aliases - the aliases of this cmd ('l')
#            self.permissions - permission string for this command
#            self.help_category - overall category of command
#
#            self.caller - the object calling this command
#            self.cmdstring - the actual command name used to call this
#                             (this allows you to know which alias was used,
#                              for example)
#            self.args - the raw input; everything following self.cmdstring.
#            self.cmdset - the cmdset from which this command was picked. Not
#                          often used (useful for commands like 'help' or to
#                          list all available commands etc)
#            self.obj - the object on which this command was defined. It is often
#                          the same as self.caller.
#
#         A MUX command has the following possible syntax:
#
#           name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]
#
#         The 'name[ with several words]' part is already dealt with by the
#         cmdhandler at this point, and stored in self.cmdname (we don't use
#         it here). The rest of the command is stored in self.args, which can
#         start with the switch indicator /.
#
#         This parser breaks self.args into its constituents and stores them in the
#         following variables:
#           self.switches = [list of /switches (without the /)]
#           self.raw = This is the raw argument input, including switches
#           self.args = This is re-defined to be everything *except* the switches
#           self.lhs = Everything to the left of = (lhs:'left-hand side'). If
#                      no = is found, this is identical to self.args.
#           self.rhs: Everything to the right of = (rhs:'right-hand side').
#                     If no '=' is found, this is None.
#           self.lhslist - [self.lhs split into a list by comma]
#           self.rhslist - [list of self.rhs split into a list by comma]
#           self.arglist = [list of space-separated args (stripped, including '=' if it exists)]
#
#           All args and list members are stripped of excess whitespace around the
#           strings, but case is preserved.
#         """
#         raw = self.args
#         args = raw.strip()
#
#         # split out switches
#         switches = []
#         if args and len(args) > 1 and args[0] == "/":
#             # we have a switch, or a set of switches. These end with a space.
#             switches = args[1:].split(None, 1)
#             if len(switches) > 1:
#                 switches, args = switches
#                 switches = switches.split('/')
#             else:
#                 args = ""
#                 switches = switches[0].split('/')
#         arglist = [arg.strip() for arg in args.split()]
#
#         # check for arg1, arg2, ... = argA, argB, ... constructs
#         lhs, rhs = args, None
#         lhslist, rhslist = [arg.strip() for arg in args.split(',')], []
#         if args and '=' in args:
#             lhs, rhs = [arg.strip() for arg in args.split('=', 1)]
#             lhslist = [arg.strip() for arg in lhs.split(',')]
#             rhslist = [arg.strip() for arg in rhs.split(',')]
#
#         # save to object properties:
#         self.raw = raw
#         self.switches = switches
#         self.args = args.strip()
#         self.arglist = arglist
#         self.lhs = lhs
#         self.lhslist = lhslist
#         self.rhs = rhs
#         self.rhslist = rhslist
#
#         # if the class has the account_caller property set on itself, we make
#         # sure that self.caller is always the account if possible. We also create
#         # a special property "character" for the puppeted object, if any. This
#         # is convenient for commands defined on the Account only.
#         if hasattr(self, "account_caller") and self.account_caller:
#             if utils.inherits_from(self.caller, "evennia.objects.objects.DefaultObject"):
#                 # caller is an Object/Character
#                 self.character = self.caller
#                 self.caller = self.caller.account
#             elif utils.inherits_from(self.caller, "evennia.accounts.accounts.DefaultAccount"):
#                 # caller was already an Account
#                 self.character = self.caller.get_puppet(self.session)
#             else:
#                 self.character = None
