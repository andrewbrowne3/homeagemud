"""
Tests for world.fiefgrid.

fiefgrid has no Evennia dependencies, so these run under plain unittest:

    python3 -m unittest world.test_fiefgrid
"""

import unittest

from world import fiefgrid


class TestParsing(unittest.TestCase):
    def test_accepts_separators_and_casing(self):
        for text in ("NE.C", "ne.c", "ne c", "NE/C", "  ne . c  "):
            self.assertEqual(fiefgrid.normalize(text), "NE.C")

    def test_ward_only_address(self):
        self.assertEqual(fiefgrid.normalize("ne"), "NE")
        self.assertEqual(fiefgrid.parse_address("ne"), ("NE", None))

    def test_rejects_nonsense(self):
        for text in ("", "XX", "NE.XX", "NE.C.SW", "42"):
            with self.assertRaises(fiefgrid.BadAddress):
                fiefgrid.parse_address(text)


class TestCoordinates(unittest.TestCase):
    def test_corners(self):
        # Northwest corner of the northwest ward is the fief's northwest corner.
        self.assertEqual(fiefgrid.to_xy("NW.NW"), (0, 8))
        self.assertEqual(fiefgrid.to_xy("SE.SE"), (8, 0))
        self.assertEqual(fiefgrid.to_xy("NE.NE"), (8, 8))
        self.assertEqual(fiefgrid.to_xy("SW.SW"), (0, 0))

    def test_dead_centre(self):
        self.assertEqual(fiefgrid.to_xy("C.C"), (4, 4))

    def test_roundtrip_all_81_plots(self):
        seen = set()
        for ward in fiefgrid.READ_ORDER:
            for plot in fiefgrid.plots_in(ward):
                x, y = fiefgrid.to_xy(plot)
                self.assertEqual(fiefgrid.from_xy(x, y), plot)
                seen.add((x, y))
        # every plot maps to a distinct square, and they tile the 9x9 grid
        self.assertEqual(len(seen), 81)

    def test_ward_address_has_no_single_coordinate(self):
        with self.assertRaises(fiefgrid.BadAddress):
            fiefgrid.to_xy("NE")


class TestStepping(unittest.TestCase):
    def test_step_within_a_ward(self):
        self.assertEqual(fiefgrid.step("NE.C", "north"), "NE.N")
        self.assertEqual(fiefgrid.step("NE.C", "south"), "NE.S")

    def test_step_crosses_ward_boundary(self):
        # Walking west off the west edge of the centre ward lands you in the
        # east column of the west ward -- where you would actually be standing.
        self.assertEqual(fiefgrid.step("C.W", "west"), "W.E")
        self.assertEqual(fiefgrid.step("C.N", "north"), "N.S")

    def test_step_off_the_fief_returns_none(self):
        self.assertIsNone(fiefgrid.step("NW.NW", "north"))
        self.assertIsNone(fiefgrid.step("NW.NW", "west"))
        self.assertIsNone(fiefgrid.step("SE.SE", "southeast"))

    def test_arrow_key_aliases(self):
        self.assertEqual(fiefgrid.step("C.C", "up"), fiefgrid.step("C.C", "north"))
        self.assertEqual(fiefgrid.step("C.C", "right"), fiefgrid.step("C.C", "east"))

    def test_walking_the_full_width(self):
        # Eight steps east from the west edge should reach the east edge, and
        # the ninth should fall off.
        here = "NW.NW"
        for _ in range(8):
            here = fiefgrid.step(here, "east")
        self.assertEqual(here, "NE.NE")
        self.assertIsNone(fiefgrid.step(here, "east"))

    def test_rejects_bad_direction(self):
        with self.assertRaises(fiefgrid.BadAddress):
            fiefgrid.step("C.C", "widdershins")


class TestNaming(unittest.TestCase):
    def test_client_ward_numbering(self):
        # The client counts row-major from the northwest, so the top-right
        # corner is ward 3.
        self.assertEqual(fiefgrid.ward_number("NE"), 3)
        self.assertEqual(fiefgrid.ward_number("NW"), 1)
        self.assertEqual(fiefgrid.ward_number("SE"), 9)

    def test_spoken_form(self):
        self.assertEqual(fiefgrid.speak("NE.C"),
                         "the center plot of northeast ward")
        self.assertEqual(fiefgrid.speak("NE"), "the northeast ward")

    def test_read_order_is_fixed(self):
        self.assertEqual(fiefgrid.READ_ORDER[0], "NW")
        self.assertEqual(fiefgrid.READ_ORDER[-1], "SE")
        self.assertEqual(len(fiefgrid.READ_ORDER), 9)

    def test_bearing_counts_from_one(self):
        self.assertEqual(fiefgrid.bearing("NW.NW"), "1 east, 9 north, of 9")


class TestAcreage(unittest.TestCase):
    def test_divides_evenly_twice(self):
        self.assertEqual(fiefgrid.ACRES_PER_FIEF, 648)
        self.assertEqual(fiefgrid.ACRES_PER_FIEF / 9, fiefgrid.ACRES_PER_WARD)
        self.assertEqual(fiefgrid.ACRES_PER_WARD / 9, fiefgrid.ACRES_PER_PLOT)


if __name__ == "__main__":
    unittest.main()
