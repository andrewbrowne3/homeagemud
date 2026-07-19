"""
Functional tests for the land navigation commands.

Drives the real commands against a real Fief object, so these cover the wiring
(cursor storage, search, cmdset arguments) that the pure fiefgrid tests cannot.

    evennia test --settings settings.py commands.test_fief
"""

import evennia
from evennia.utils.test_resources import EvenniaCommandTest

from commands import fief as fief_cmds


class TestFiefNavigation(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.fief = evennia.create_object(
            "typeclasses.fiefs.Fief", key="Ashford"
        )
        self.fief.add_structure("NE.C", "a sawmill", 3)
        self.fief.add_structure("NE.C", "a granary", 2)

    def _select(self):
        self.call(fief_cmds.CmdFief(), "Ashford")

    # -- selecting and overview ---------------------------------

    def test_must_select_a_fief_first(self):
        out = self.call(fief_cmds.CmdWhere(), "")
        self.assertIn("not surveying any fief", out)

    def test_overview_lists_nine_wards_in_fixed_order(self):
        self._select()
        out = self.call(fief_cmds.CmdFief(), "")
        for number, name in enumerate(
            ["northwest", "north", "northeast", "west", "center",
             "east", "southwest", "south", "southeast"], start=1
        ):
            self.assertIn(f"{number}. {name} ward", out)
        # the client's numbering: top-right is ward 3
        self.assertIn("3. northeast ward", out)

    def test_overview_aggregates_acres(self):
        self._select()
        out = self.call(fief_cmds.CmdFief(), "")
        self.assertIn("2 structures, 5 of 72 acres used", out)

    # -- position tracking --------------------------------------

    def test_cursor_starts_at_centre(self):
        self._select()
        out = self.call(fief_cmds.CmdWhere(), "")
        self.assertIn("The center plot of center ward (C.C)", out)
        self.assertIn("5 east, 5 north, of 9", out)

    def test_where_is_terse_survey_is_verbose(self):
        self._select()
        terse = self.call(fief_cmds.CmdWhere(), "")
        verbose = self.call(fief_cmds.CmdSurvey(), "")
        self.assertNotIn("Around you", terse)
        self.assertIn("Around you", verbose)
        self.assertIn("Nothing stands here", verbose)

    def test_survey_reports_structures_and_room(self):
        self._select()
        out = self.call(fief_cmds.CmdSurvey(), "NE.C")
        self.assertIn("a sawmill (3 acres)", out)
        self.assertIn("a granary (2 acres)", out)
        self.assertIn("5 of 8 acres used", out)

    def test_survey_a_whole_ward_lists_nine_plots(self):
        self._select()
        out = self.call(fief_cmds.CmdSurvey(), "NE")
        self.assertIn("ward 3 of 9", out)
        for cell in ["NE.NW", "NE.N", "NE.NE", "NE.W", "NE.C",
                     "NE.E", "NE.SW", "NE.S", "NE.SE"]:
            self.assertIn(cell, out)

    # -- movement -----------------------------------------------

    def test_step_moves_the_cursor_and_persists(self):
        self._select()
        self.call(fief_cmds.CmdStep(), "north")
        self.assertEqual(fief_cmds.cursor_of(self.char1), "C.N")
        out = self.call(fief_cmds.CmdWhere(), "")
        self.assertIn("(C.N)", out)

    def test_crossing_a_ward_boundary_is_announced(self):
        self._select()
        self.call(fief_cmds.CmdGoto(), "C.N")
        out = self.call(fief_cmds.CmdStep(), "north")
        self.assertIn("Crossing into the north ward", out)
        self.assertIn("(N.S)", out)

    def test_staying_inside_a_ward_is_not_announced(self):
        self._select()
        out = self.call(fief_cmds.CmdStep(), "north")
        self.assertNotIn("Crossing", out)

    def test_fief_edge_gives_a_distinct_cue(self):
        self._select()
        self.call(fief_cmds.CmdGoto(), "NW.NW")
        out = self.call(fief_cmds.CmdStep(), "north")
        self.assertIn("The fief ends there", out)
        # and the cursor must not have moved
        self.assertEqual(fief_cmds.cursor_of(self.char1), "NW.NW")

    def test_abbreviated_and_arrow_directions(self):
        self._select()
        self.call(fief_cmds.CmdStep(), "n")
        self.assertEqual(fief_cmds.cursor_of(self.char1), "C.N")
        self.call(fief_cmds.CmdStep(), "right")
        self.assertEqual(fief_cmds.cursor_of(self.char1), "C.NE")

    def test_goto_a_bare_ward_lands_on_its_centre(self):
        self._select()
        out = self.call(fief_cmds.CmdGoto(), "NE")
        self.assertEqual(fief_cmds.cursor_of(self.char1), "NE.C")
        self.assertIn("5 of 8 acres used", out)

    def test_goto_rejects_nonsense(self):
        self._select()
        out = self.call(fief_cmds.CmdGoto(), "somewhere")
        self.assertIn("not a ward or plot name", out)

    def test_step_without_direction_lists_options(self):
        self._select()
        out = self.call(fief_cmds.CmdStep(), "")
        self.assertIn("Step which way?", out)


class TestBuilding(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.fief = evennia.create_object("typeclasses.fiefs.Fief", key="Ashford")
        self.call(fief_cmds.CmdFief(), "Ashford")

    def test_bare_build_reads_the_catalogue(self):
        out = self.call(fief_cmds.CmdBuild(), "")
        self.assertIn("You can build:", out)
        self.assertIn("sawmill -- 3 acres", out)
        self.assertIn("cottage -- 1 acre,", out)  # singular for one acre

    def test_builds_on_the_cursor_plot_by_default(self):
        self.call(fief_cmds.CmdGoto(), "NE.C")
        out = self.call(fief_cmds.CmdBuild(), "sawmill")
        self.assertIn("You raise a sawmill", out)
        self.assertIn("(NE.C)", out)
        self.assertIn("3 acres taken, 5 of 8 left", out)
        self.assertEqual(len(self.fief.structures_at("NE.C")), 1)

    def test_builds_at_an_explicit_address(self):
        out = self.call(fief_cmds.CmdBuild(), "granary at SW.NE")
        self.assertIn("(SW.NE)", out)
        self.assertEqual(self.fief.acres_used("SW.NE"), 2)
        # the cursor must not have moved
        self.assertEqual(fief_cmds.cursor_of(self.char1), "C.C")

    def test_abbreviated_name(self):
        out = self.call(fief_cmds.CmdBuild(), "saw")
        self.assertIn("a sawmill", out)

    def test_single_acre_reads_as_singular(self):
        out = self.call(fief_cmds.CmdBuild(), "cottage")
        self.assertIn("1 acre taken", out)
        self.assertNotIn("1 acres", out)

    def test_ambiguous_name_is_refused_with_options(self):
        out = self.call(fief_cmds.CmdBuild(), "c")
        self.assertIn("could mean", out)
        self.assertEqual(self.fief.structures_at("C.C"), [])

    def test_unknown_name_is_refused(self):
        out = self.call(fief_cmds.CmdBuild(), "cathedral")
        self.assertIn("nothing called", out)

    def test_plot_fills_up(self):
        self.call(fief_cmds.CmdBuild(), "orchard")          # 6 of 8
        out = self.call(fief_cmds.CmdBuild(), "sawmill")    # needs 3, only 2 left
        self.assertIn("No room", out)
        self.assertIn("2 of 8 acres open", out)
        self.assertEqual(len(self.fief.structures_at("C.C")), 1)

    def test_cannot_build_on_a_whole_ward(self):
        out = self.call(fief_cmds.CmdBuild(), "sawmill at NE")
        self.assertIn("Name a single plot", out)

    def test_bad_address_is_refused(self):
        out = self.call(fief_cmds.CmdBuild(), "sawmill at nowhere")
        self.assertIn("not a ward or plot name", out)

    def test_structure_records_its_catalogue_kind(self):
        self.call(fief_cmds.CmdBuild(), "sawmill")
        self.assertEqual(self.fief.structures_at("C.C")[0]["kind"], "sawmill")

    def test_built_structure_shows_up_when_surveying(self):
        self.call(fief_cmds.CmdBuild(), "sawmill at NE.C")
        out = self.call(fief_cmds.CmdSurvey(), "NE")
        self.assertIn("center (NE.C): a sawmill", out)


class TestDemolishing(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.fief = evennia.create_object("typeclasses.fiefs.Fief", key="Ashford")
        self.call(fief_cmds.CmdFief(), "Ashford")
        self.call(fief_cmds.CmdBuild(), "sawmill")   # 3 acres on C.C
        self.call(fief_cmds.CmdBuild(), "granary")   # 2 acres on C.C

    def test_pulls_down_and_frees_the_acres(self):
        out = self.call(fief_cmds.CmdDemolish(), "sawmill")
        self.assertIn("You pull down a sawmill", out)
        self.assertIn("3 acres freed", out)
        self.assertIn("6 of 8 now open", out)
        self.assertEqual(self.fief.acres_used("C.C"), 2)

    def test_only_the_named_structure_goes(self):
        self.call(fief_cmds.CmdDemolish(), "sawmill")
        remaining = [s["name"] for s in self.fief.structures_at("C.C")]
        self.assertEqual(remaining, ["a granary"])

    def test_bare_demolish_reads_back_what_is_there(self):
        out = self.call(fief_cmds.CmdDemolish(), "")
        self.assertIn("Standing there: a sawmill, a granary", out)
        self.assertEqual(len(self.fief.structures_at("C.C")), 2)

    def test_empty_plot_says_so(self):
        self.call(fief_cmds.CmdGoto(), "SW.SW")
        out = self.call(fief_cmds.CmdDemolish(), "")
        self.assertIn("Nothing stands on", out)

    def test_demolish_at_an_explicit_address(self):
        self.call(fief_cmds.CmdBuild(), "keep at NE.C")
        out = self.call(fief_cmds.CmdDemolish(), "keep at NE.C")
        self.assertIn("(NE.C)", out)
        self.assertEqual(self.fief.structures_at("NE.C"), [])
        # the cursor stayed put, and C.C was untouched
        self.assertEqual(fief_cmds.cursor_of(self.char1), "C.C")
        self.assertEqual(len(self.fief.structures_at("C.C")), 2)

    def test_abbreviated_name(self):
        out = self.call(fief_cmds.CmdDemolish(), "saw")
        self.assertIn("a sawmill", out)

    def test_naming_something_not_there(self):
        out = self.call(fief_cmds.CmdDemolish(), "orchard")
        self.assertIn("no 'orchard'", out)
        self.assertIn("Standing there:", out)
        self.assertEqual(len(self.fief.structures_at("C.C")), 2)

    def test_duplicates_take_one_and_account_for_the_rest(self):
        self.call(fief_cmds.CmdGoto(), "NE.C")
        for _ in range(3):
            self.call(fief_cmds.CmdBuild(), "cottage")
        out = self.call(fief_cmds.CmdDemolish(), "cottage")
        self.assertIn("2 more cottages still stand here", out)
        self.assertEqual(len(self.fief.structures_at("NE.C")), 2)

    def test_last_duplicate_reads_as_singular(self):
        self.call(fief_cmds.CmdGoto(), "NE.C")
        self.call(fief_cmds.CmdBuild(), "cottage")
        self.call(fief_cmds.CmdBuild(), "cottage")
        out = self.call(fief_cmds.CmdDemolish(), "cottage")
        self.assertIn("1 more cottage still stands here", out)

    def test_emptying_a_plot_leaves_no_stored_entry(self):
        # storage stays sparse: an emptied plot drops out of the dict
        self.call(fief_cmds.CmdDemolish(), "sawmill")
        self.call(fief_cmds.CmdDemolish(), "granary")
        self.assertNotIn("C.C", self.fief.structures)
        self.assertEqual(self.fief.acres_free("C.C"), 8)

    def test_rebuilding_after_demolishing_fits(self):
        self.call(fief_cmds.CmdDemolish(), "sawmill")
        out = self.call(fief_cmds.CmdBuild(), "orchard")  # 6, needs the freed room
        self.assertIn("You raise an orchard", out)

    def test_raze_is_an_alias(self):
        self.assertIn("raze", fief_cmds.CmdDemolish.aliases)

    def test_another_house_may_not_demolish(self):
        self.fief.house = "House Marlow"
        self.char1.attributes.add("house", "House Vane")
        out = self.call(fief_cmds.CmdDemolish(), "sawmill")
        self.assertIn("held by House Marlow", out)
        self.assertEqual(len(self.fief.structures_at("C.C")), 2)


class TestBuildPermission(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.fief = evennia.create_object("typeclasses.fiefs.Fief", key="Ashford")
        self.call(fief_cmds.CmdFief(), "Ashford")

    def test_unclaimed_fief_is_open(self):
        out = self.call(fief_cmds.CmdBuild(), "sawmill")
        self.assertIn("You raise", out)

    def test_another_house_is_refused(self):
        self.fief.house = "House Marlow"
        self.char1.attributes.add("house", "House Vane")
        out = self.call(fief_cmds.CmdBuild(), "sawmill")
        self.assertIn("held by House Marlow", out)
        self.assertEqual(self.fief.structures_at("C.C"), [])

    def test_own_house_may_build(self):
        self.fief.house = "House Marlow"
        self.char1.attributes.add("house", "house marlow")  # case-insensitive
        out = self.call(fief_cmds.CmdBuild(), "sawmill")
        self.assertIn("You raise", out)


class TestMapPayload(EvenniaCommandTest):
    """
    The web map renders straight from this payload.

    Its shape is a contract with web/static/webclient/js/plugins/fiefmap.js --
    if a key here is renamed, the map silently draws nothing, so it is pinned.
    """

    def setUp(self):
        super().setUp()
        self.fief = evennia.create_object("typeclasses.fiefs.Fief", key="Ashford")
        self.fief.add_structure("NE.C", "a sawmill", 3, kind="sawmill")

    def _payload(self, address="C.C"):
        return fief_cmds._payload(self.fief, address)

    def test_carries_both_levels_at_once(self):
        p = self._payload()
        self.assertEqual(len(p["wards"]), 9)
        self.assertEqual(len(p["plots"]), 9)

    def test_cells_follow_the_text_reading_order(self):
        from world import fiefgrid

        p = self._payload()
        self.assertEqual(p["order"], list(fiefgrid.READ_ORDER))
        self.assertEqual([w["ward"] for w in p["wards"]], list(fiefgrid.READ_ORDER))

    def test_plots_are_those_of_the_cursor_ward(self):
        p = self._payload("NE.C")
        self.assertTrue(all(a["address"].startswith("NE.") for a in p["plots"]))
        # index 4 is the centre of a 3x3 in reading order
        self.assertEqual(p["plots"][4]["address"], "NE.C")

    def test_keys_the_map_reads_are_all_present(self):
        p = self._payload("NE.C")
        for key in ("fief", "cursor", "ward", "plot", "order", "wards", "plots"):
            self.assertIn(key, p)
        for key in ("ward", "number", "name", "structures",
                    "acres_used", "acres_total"):
            self.assertIn(key, p["wards"][0])
        for key in ("address", "spoken", "bearing", "structures",
                    "acres_used", "acres_total"):
            self.assertIn(key, p["plots"][0])

    def test_structure_entries_carry_a_name_for_the_cell(self):
        p = self._payload("NE.C")
        self.assertEqual(p["plots"][4]["structures"][0]["name"], "a sawmill")

    def test_payload_is_json_serialisable(self):
        import json

        json.dumps(self._payload("NE.C"))  # raises if anything is not a plain type


class TestCmdsetWiring(EvenniaCommandTest):
    """The land commands must actually reach a player, and shadow nothing."""

    def test_land_commands_are_on_the_character_cmdset(self):
        from commands.default_cmdsets import CharacterCmdSet

        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        keys = [cmd.key for cmd in cmdset.commands]
        for key in ("fief", "where", "survey", "step", "goto", "build", "demolish"):
            self.assertIn(key, keys)

    def test_no_command_key_is_defined_twice(self):
        from commands.default_cmdsets import CharacterCmdSet

        cmdset = CharacterCmdSet()
        cmdset.at_cmdset_creation()
        keys = [cmd.key for cmd in cmdset.commands]
        self.assertEqual(sorted(keys), sorted(set(keys)))

    def test_every_oob_handler_exists_for_the_map_ui(self):
        from server.conf import inputfuncs

        for name in ("fief", "fiefwhere", "fiefsurvey", "fiefstep",
                     "fiefgoto", "fiefbuild", "fiefdemolish"):
            self.assertTrue(callable(getattr(inputfuncs, name, None)),
                            f"missing OOB handler: {name}")


class TestFiefCapacity(EvenniaCommandTest):
    def setUp(self):
        super().setUp()
        self.fief = evennia.create_object("typeclasses.fiefs.Fief", key="Ashford")

    def test_structure_must_fit_in_the_plot(self):
        ok, msg = self.fief.add_structure("NE.C", "a keep", 9)
        self.assertFalse(ok)
        self.assertIn("No room", msg)

    def test_filling_a_plot_exactly_is_allowed(self):
        ok, _ = self.fief.add_structure("NE.C", "a keep", 8)
        self.assertTrue(ok)
        self.assertEqual(self.fief.acres_free("NE.C"), 0)
        ok, _ = self.fief.add_structure("NE.C", "a shed", 1)
        self.assertFalse(ok)

    def test_cannot_build_on_a_whole_ward(self):
        ok, msg = self.fief.add_structure("NE", "a keep", 1)
        self.assertFalse(ok)
        self.assertIn("single plot", msg)
