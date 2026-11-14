import unittest

import numpy as np
import pandas as pd

from src.data.preprocessing import target_from_labels


class LabelMappingTests(unittest.TestCase):
    def test_normal_attempted_and_effective_labels(self):
        labels = pd.Series(
            [
                "BENIGN",
                "FTP-Patator - Attempted",
                "DoS Hulk",
                "Infiltration - Portscan",
            ]
        )
        result = target_from_labels(labels)
        self.assertEqual(result.tolist(), [0, 0, 1, 1])

    def test_unknown_labels_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown labels"):
            target_from_labels(pd.Series(["BENIGN", "New Unknown Label"]))

    def test_original_labels_are_not_modified(self):
        labels = pd.Series(["BENIGN", "DDoS"])
        original = labels.copy(deep=True)
        target_from_labels(labels)
        pd.testing.assert_series_equal(labels, original)

    def test_missing_label_is_not_silently_normal(self):
        with self.assertRaisesRegex(ValueError, "<MISSING>"):
            target_from_labels(pd.Series(["BENIGN", np.nan]))
