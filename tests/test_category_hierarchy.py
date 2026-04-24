import unittest
from unittest.mock import patch

import category_hierarchy


class CategoryHierarchyTests(unittest.TestCase):
    def tearDown(self):
        category_hierarchy.clear_hierarchy_cache()

    def test_exact_subcategory_match_beats_loose_substring(self):
        with patch.object(
            category_hierarchy,
            "get_category_hierarchy",
            return_value={"Entertainment": ["Music", "Musicals and Theatres"]},
        ):
            main_cat, subcat, is_random = category_hierarchy.find_category_match("music")

        self.assertEqual(main_cat, "Entertainment")
        self.assertEqual(subcat, "Entertainment_Music")
        self.assertFalse(is_random)

    def test_main_category_match_returns_randomized_group(self):
        with patch.object(
            category_hierarchy,
            "get_category_hierarchy",
            return_value={"Science": ["Nature", "Computers"]},
        ):
            main_cat, subcat, is_random = category_hierarchy.find_category_match("science")

        self.assertEqual(main_cat, "Science")
        self.assertIsNone(subcat)
        self.assertTrue(is_random)


if __name__ == "__main__":
    unittest.main()
