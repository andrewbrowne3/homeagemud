"""
Tests for world.structures.

No Evennia dependencies:

    python3 -m unittest world.test_structures
"""

import unittest

from world import fiefgrid, structures


class TestLookup(unittest.TestCase):
    def test_exact_name(self):
        name, entry = structures.find("sawmill")
        self.assertEqual(name, "sawmill")
        self.assertEqual(entry["acres"], 3)

    def test_case_and_whitespace(self):
        self.assertEqual(structures.find("  SawMill ")[0], "sawmill")

    def test_unique_prefix(self):
        self.assertEqual(structures.find("saw")[0], "sawmill")
        self.assertEqual(structures.find("orch")[0], "orchard")

    def test_ambiguous_prefix_names_the_options(self):
        # "c" matches both cottage and chapel
        with self.assertRaises(structures.UnknownStructure) as ctx:
            structures.find("c")
        self.assertIn("chapel", str(ctx.exception))
        self.assertIn("cottage", str(ctx.exception))

    def test_unknown_points_at_the_catalogue(self):
        with self.assertRaises(structures.UnknownStructure) as ctx:
            structures.find("cathedral")
        self.assertIn("catalogue", str(ctx.exception))

    def test_empty_input(self):
        with self.assertRaises(structures.UnknownStructure):
            structures.find("")


class TestNaming(unittest.TestCase):
    def test_articles(self):
        self.assertEqual(structures.display_name("sawmill"), "a sawmill")
        self.assertEqual(structures.display_name("orchard"), "an orchard")


class TestCatalogue(unittest.TestCase):
    def test_nothing_is_too_big_for_a_plot(self):
        for name, entry in structures.CATALOGUE.items():
            self.assertLessEqual(
                entry["acres"], fiefgrid.ACRES_PER_PLOT,
                f"{name} cannot fit on any plot",
            )
            self.assertGreater(entry["acres"], 0, f"{name} takes no space")

    def test_listing_is_cheapest_first(self):
        lines = structures.format_catalogue().splitlines()[1:]
        acres = [int(line.split("--")[1].split("acre")[0]) for line in lines]
        self.assertEqual(acres, sorted(acres))

    def test_every_entry_is_described(self):
        for name, entry in structures.CATALOGUE.items():
            self.assertTrue(entry.get("desc"), f"{name} has no description")


if __name__ == "__main__":
    unittest.main()
