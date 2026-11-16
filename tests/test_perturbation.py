import unittest

import numpy as np
import pandas as pd

from src.attacks.perturbation import (
    CHANGED_COLUMNS,
    order_violations,
    out_of_bounds,
    perturb,
)

MICRO = 1e6


def _std(values: np.ndarray) -> float:
    return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0


def make_flow(fwd_len, bwd_len, fwd_t, bwd_t) -> dict[str, float]:
    """Build every column the perturbation reads, packet by packet."""
    fl = np.asarray(fwd_len, dtype=float)
    bl = np.asarray(bwd_len, dtype=float)
    ft = np.sort(np.asarray(fwd_t, dtype=float))
    bt = np.sort(np.asarray(bwd_t, dtype=float))
    all_t = np.sort(np.concatenate([ft, bt]))
    all_len = np.concatenate([fl, bl])
    fwd_iat, all_iat = np.diff(ft), np.diff(all_t)
    duration = all_t[-1] - all_t[0]
    total = len(all_len)
    return {
        "Total Fwd Packet": float(len(fl)),
        "Total Bwd packets": float(len(bl)),
        "Total Length of Fwd Packet": fl.sum(),
        "Total Length of Bwd Packet": bl.sum(),
        "Fwd Packet Length Max": fl.max(),
        "Fwd Packet Length Min": fl.min(),
        "Fwd Packet Length Mean": fl.mean(),
        "Fwd Packet Length Std": _std(fl),
        "Bwd Packet Length Max": bl.max(),
        "Bwd Packet Length Min": bl.min(),
        "Bwd Packet Length Mean": bl.mean(),
        "Bwd Packet Length Std": _std(bl),
        "Fwd Segment Size Avg": fl.mean(),
        "Flow Duration": duration,
        "Fwd IAT Total": fwd_iat.sum(),
        "Fwd IAT Mean": fwd_iat.mean(),
        "Fwd IAT Std": _std(fwd_iat),
        "Fwd IAT Max": fwd_iat.max(),
        "Fwd IAT Min": fwd_iat.min(),
        "Flow IAT Mean": all_iat.mean(),
        "Flow IAT Std": _std(all_iat),
        "Flow IAT Max": all_iat.max(),
        "Flow IAT Min": all_iat.min(),
        "Flow Packets/s": total / duration * MICRO,
        "Flow Bytes/s": all_len.sum() / duration * MICRO,
        "Fwd Packets/s": len(fl) / duration * MICRO,
        "Bwd Packets/s": len(bl) / duration * MICRO,
        "Packet Length Mean": all_len.mean(),
        "Average Packet Size": all_len.mean(),
        "Packet Length Max": all_len.max(),
        "Packet Length Min": all_len.min(),
        "Packet Length Std": _std(all_len),
        "Packet Length Variance": _std(all_len) ** 2,
        "Down/Up Ratio": len(bl) / len(fl),
    }


FLOW_A = {"fwd_len": [100, 200, 300], "bwd_len": [50, 1500], "fwd_t": [0, 10, 40], "bwd_t": [5, 20]}
FLOW_B = {
    "fwd_len": [0, 0, 40, 60],
    "bwd_len": [1000, 20, 20],
    "fwd_t": [100, 105, 150, 160],
    "bwd_t": [101, 120, 130],
}


class PerturbationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame([make_flow(**FLOW_A), make_flow(**FLOW_B)])

    def assert_frames_close(self, left: pd.DataFrame, right: pd.DataFrame) -> None:
        self.assertEqual(sorted(left.columns), sorted(right.columns))
        for column in left.columns:
            np.testing.assert_allclose(
                left[column].to_numpy(dtype=float),
                right[column].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9,
                err_msg=column,
            )

    def test_identity_reproduces_every_column(self) -> None:
        self.assert_frames_close(perturb(self.frame, 1.0, 1.0), self.frame)

    def test_padding_matches_a_flow_rebuilt_from_padded_packets(self) -> None:
        s = 1.5
        rebuilt = pd.DataFrame(
            [
                make_flow(**{**FLOW_A, "fwd_len": np.array(FLOW_A["fwd_len"]) * s}),
                make_flow(**{**FLOW_B, "fwd_len": np.array(FLOW_B["fwd_len"]) * s}),
            ]
        )
        self.assert_frames_close(perturb(self.frame, s, 1.0), rebuilt)

    def test_delay_stretches_forward_intervals_and_duration(self) -> None:
        t = 2.0
        out = perturb(self.frame, 1.0, t)
        for column in ("Fwd IAT Total", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min"):
            np.testing.assert_allclose(out[column], self.frame[column] * t)
        duration = self.frame["Flow Duration"] + (t - 1.0) * self.frame["Fwd IAT Total"]
        total = self.frame["Total Fwd Packet"] + self.frame["Total Bwd packets"]
        np.testing.assert_allclose(out["Flow Duration"], duration)
        np.testing.assert_allclose(out["Flow Packets/s"], total / duration * MICRO)
        np.testing.assert_allclose(out["Flow IAT Mean"], duration / (total - 1.0))
        for column in (
            "Flow IAT Min",
            "Flow IAT Max",
            "Flow IAT Std",
            "Bwd Packet Length Std",
            "Total Length of Fwd Packet",
        ):
            np.testing.assert_allclose(out[column], self.frame[column])

    def test_large_delay_breaks_flow_iat_order(self) -> None:
        unchanged = order_violations(perturb(self.frame, 1.0, 1.0))
        self.assertFalse(unchanged.to_numpy().any())
        delayed = order_violations(perturb(self.frame, 1.0, 3.0))
        self.assertTrue(delayed["flow_iat_mean_above_max"].any())

    def test_out_of_bounds_flags_changed_values_only(self) -> None:
        lower, upper = self.frame.min(), self.frame.max()
        self.assertFalse(out_of_bounds(perturb(self.frame, 1.0, 1.0), lower, upper).any())
        self.assertTrue(out_of_bounds(perturb(self.frame, 1.5, 1.0), lower, upper).any())

    def test_factors_below_one_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            perturb(self.frame, 0.9, 1.0)
        with self.assertRaises(ValueError):
            perturb(self.frame, 1.0, 0.5)

    def test_input_frame_is_not_modified(self) -> None:
        before = self.frame.copy(deep=True)
        perturb(self.frame, 2.0, 2.0)
        pd.testing.assert_frame_equal(self.frame, before)

    def test_zero_duration_keeps_original_rates(self) -> None:
        frame = self.frame.copy()
        frame["Flow Duration"] = 0.0
        frame["Fwd IAT Total"] = 0.0
        frame["Flow Packets/s"] = 7.0
        out = perturb(frame, 1.0, 2.0)
        np.testing.assert_allclose(out["Flow Packets/s"], 7.0)
        self.assertTrue(np.isfinite(out[list(CHANGED_COLUMNS)].to_numpy(dtype=float)).all())


if __name__ == "__main__":
    unittest.main()