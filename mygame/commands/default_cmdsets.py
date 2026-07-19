"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""

from evennia import default_cmds

# ⬇️ ADD THIS IMPORT
from evennia.contrib.full_systems.evscaperoom.commands import CmdEvscapeRoomStart
from evennia.contrib.base_systems.building_menu import GenericBuildingCmd
from commands.command import (
    CmdCreateScene,
    CmdJoinScene,
    CmdLeaveScene,
    CmdListScenes,
    CmdScore,
)
from commands.fief import (
    CmdBuild,
    CmdDemolish,
    CmdFief,
    CmdGoto,
    CmdStep,
    CmdSurvey,
    CmdWhere,
)


def _add_scene_cmds(cmdset):
    cmdset.add(CmdCreateScene())
    cmdset.add(CmdJoinScene())
    cmdset.add(CmdLeaveScene())
    cmdset.add(CmdListScenes())


def _add_fief_cmds(cmdset):
    cmdset.add(CmdFief())
    cmdset.add(CmdWhere())
    cmdset.add(CmdSurvey())
    cmdset.add(CmdStep())
    cmdset.add(CmdGoto())
    cmdset.add(CmdBuild())
    cmdset.add(CmdDemolish())


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()

        # ⬇️ ADD THIS COMMAND
        self.add(CmdEvscapeRoomStart())
        self.add(GenericBuildingCmd())
        self.add(CmdScore())
        _add_scene_cmds(self)
        # land commands are character-only: the survey cursor lives on the
        # character, so they are not added to the AccountCmdSet
        _add_fief_cmds(self)

class AccountCmdSet(default_cmds.AccountCmdSet):
    key = "DefaultAccount"
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        _add_scene_cmds(self)


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    key = "DefaultUnloggedin"
    def at_cmdset_creation(self):
        super().at_cmdset_creation()


class SessionCmdSet(default_cmds.SessionCmdSet):
    key = "DefaultSession"
    def at_cmdset_creation(self):
        super().at_cmdset_creation()

