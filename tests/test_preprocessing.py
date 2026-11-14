import unittest

import numpy as np
import pandas as pd

from src.data.preprocessing import (
    fit_preprocessor,
    prepare_working_frame,
    replace_infinities,
    select_feature_columns,
    transform_frame,
)


def synthetic_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2],
            "Flow ID": ["a", "b"],
            "Src IP": ["10.0.0.1", "10.0.0.2"],
            "Dst IP": ["10.0.0.3", "10.0.0.4"],
            "Src Port": [1000, 1001],
            "Dst Port": [80, 443],
            "Timestamp": ["2017-07-03", "2017-07-03"],
            "Label": ["BENIGN", "DDoS"],
            "Attempted Category": [-1, 0],
            "source_day": ["monday", "monday"],
            "Protocol": [6, 17],
            "Flow Duration": [1.0, 2.0],
            "Flow Bytes/s": [np.inf, 100.0],
            "Fwd Header Length": [-4.0, 8.0],
            "Bwd Header Length": [0.0, 16.0],
            "Signal": [1.0, 3.0],
        }
    )


class PreprocessingTests(unittest.TestCase):
    def test_infinities_are_replaced_in_a_copy(self):
        frame = synthetic_frame()
        working = replace_infinities(frame)
        self.assertTrue(np.isnan(working.loc[0, "Flow Bytes/s"]))
        self.assertTrue(np.isinf(frame.loc[0, "Flow Bytes/s"]))

    def test_impute_strategy_marks_negative_headers_as_missing(self):
        working = prepare_working_frame(synthetic_frame(), "impute")
        self.assertTrue(np.isnan(working.loc[0, "Fwd Header Length"]))

    def test_exclude_strategy_removes_header_features_only_from_X(self):
        columns = select_feature_columns(
            synthetic_frame(),
            header_strategy="exclude",
        )
        self.assertNotIn("Fwd Header Length", columns)
        self.assertNotIn("Bwd Header Length", columns)
        self.assertNotIn("Src Port", columns)
        self.assertIn("Protocol", columns)

    def test_pipeline_fits_statistics_on_training_only(self):
        train = synthetic_frame()
        validation = synthetic_frame().assign(Signal=[1000.0, 2000.0], Protocol=[1, 99])
        fitted = fit_preprocessor(train, header_strategy="impute")
        numeric_imputer = fitted.transformer.named_transformers_["numeric"].named_steps["imputer"]
        signal_index = fitted.numeric_columns.index("Signal")
        self.assertEqual(numeric_imputer.statistics_[signal_index], 2.0)
        transformed = transform_frame(validation, fitted)
        self.assertEqual(transformed.shape[0], 2)

    def test_unknown_protocol_category_is_ignored(self):
        train = synthetic_frame()
        validation = synthetic_frame().assign(Protocol=[999, 998])
        fitted = fit_preprocessor(train, header_strategy="impute")
        transformed = transform_frame(validation, fitted)
        self.assertEqual(transformed.shape[0], 2)
