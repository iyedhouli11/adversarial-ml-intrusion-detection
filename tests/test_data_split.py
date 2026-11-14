import unittest

from src.data.dataset_loader import source_days_for_split, split_file_names


class DataSplitTests(unittest.TestCase):
    def test_protocol_days_are_fixed(self):
        self.assertEqual(
            split_file_names("train"),
            ("monday.csv", "tuesday.csv", "wednesday.csv"),
        )
        self.assertEqual(split_file_names("validation"), ("thursday.csv",))
        self.assertEqual(split_file_names("test"), ("friday.csv",))

    def test_test_day_is_not_in_training_or_validation(self):
        self.assertNotIn("friday", source_days_for_split("train"))
        self.assertNotIn("friday", source_days_for_split("validation"))
        self.assertEqual(source_days_for_split("test"), ("friday",))

    def test_unknown_split_is_rejected(self):
        with self.assertRaises(ValueError):
            split_file_names("random")
