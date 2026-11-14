import unittest

import pandas as pd

from src.data.preprocessing import select_feature_columns

METADATA = [
    "id", "Flow ID", "Src IP", "Dst IP", "Timestamp",
    "Label", "Attempted Category", "attempted_flag", "source_day",
]


class FeatureContractTests(unittest.TestCase):
    def setUp(self) -> None:
        columns = METADATA + [
            "Src Port", "Dst Port", "Protocol", "Flow Duration",
            "Fwd Header Length", "Bwd Header Length",
        ]
        self.frame = pd.DataFrame(columns=columns)

    def test_metadata_and_labels_never_enter_features(self) -> None:
        features = select_feature_columns(self.frame, header_strategy="impute")
        for column in METADATA:
            self.assertNotIn(column, features)

    def test_ports_excluded_by_default_and_optional(self) -> None:
        default = select_feature_columns(self.frame, header_strategy="impute")
        with_ports = select_feature_columns(
            self.frame, header_strategy="impute", include_ports=True
        )
        self.assertNotIn("Src Port", default)
        self.assertNotIn("Dst Port", default)
        self.assertIn("Dst Port", with_ports)
        self.assertIn("Protocol", default)


if __name__ == "__main__":
    unittest.main()