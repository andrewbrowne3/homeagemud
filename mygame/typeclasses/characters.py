"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

from evennia.objects.objects import DefaultCharacter
from evennia.typeclasses.attributes import AttributeProperty

from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    Roleplay stats sheet
    --------------------
    The fields below back the ``score`` command. They are stored as Evennia
    Attributes, so they can be set in-game (``set self/house = York``), from a
    builder command, or from future character-creation code. Each has a safe
    default so ``score`` never errors on an unset field. The character's
    in-game name (``key``) is used for "Name", so it is not duplicated here.

    These are intentionally simple placeholders. The real systems behind them
    (skill progression, house mechanics, homage/allegiance rules) are a larger
    follow-on task.
    """

    surname = AttributeProperty(default="n/a", autocreate=False)
    charclass = AttributeProperty(default="Commoner", autocreate=False)
    title = AttributeProperty(default="n/a", autocreate=False)
    house = AttributeProperty(default="n/a", autocreate=False)
    # homage: an ordered list of allegiances, e.g. ["Baron Lew", "Thieves guild"]
    homage = AttributeProperty(default=list, autocreate=False)
    # skills: a mapping of skill name -> level, e.g. {"Weaver": 5, "Forage": 9}
    skills = AttributeProperty(default=dict, autocreate=False)
