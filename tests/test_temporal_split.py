import unittest

import pandas as pd

from src.data.temporal_split import assign_temporal_segments


def make_frame(n: int, *, label: str = "DoS Hulk", day: str = "wednesday") -> pd.DataFrame:
    times = pd.date_range("2017-07-05 10:00:00", periods=n, freq="s")
    return pd.DataFrame(
        {
            "Timestamp": times.strftime("%Y-%m-%d %H:%M:%S"),
            "Label": label,
            "source_day": day,
        }
    )


class TemporalSplitTests(unittest.TestCase):
    def test_sixty_twenty_twenty_without_gap(self) -> None:
        segments = assign_temporal_segments(make_frame(10), gap_fraction=0.0)
        self.assertEqual(
            segments.value_counts().to_dict(),
            {"train": 6, "validation": 2, "test": 2},
        )

    def test_gap_separates_segments_in_time_order(self) -> None:
        segments = assign_temporal_segments(make_frame(1000), gap_fraction=0.01)
        self.assertGreater(int((segments == "gap").sum()), 0)
        train = segments.index[segments == "train"]
        validation = segments.index[segments == "validation"]
        test = segments.index[segments == "test"]
        # make_frame is chronological, so index order is time order
        self.assertLess(train.max(), validation.min())
        self.assertLess(validation.max(), test.min())

    def test_input_row_order_does_not_matter(self) -> None:
        frame = make_frame(100).sample(frac=1.0, random_state=0)
        segments = assign_temporal_segments(frame, gap_fraction=0.0)
        times = pd.to_datetime(frame["Timestamp"], format="ISO8601")
        self.assertLess(
            times[segments == "train"].max(), times[segments == "validation"].min()
        )
        self.assertLess(
            times[segments == "validation"].max(), times[segments == "test"].min()
        )

    def test_each_day_label_stratum_is_cut_separately(self) -> None:
        frame = pd.concat(
            [
                make_frame(10, label="A", day="monday"),
                make_frame(10, label="B", day="tuesday"),
            ],
            ignore_index=True,
        )
        segments = assign_temporal_segments(frame, gap_fraction=0.0)
        for label in ("A", "B"):
            self.assertEqual(
                segments[frame["Label"] == label].value_counts().to_dict(),
                {"train": 6, "validation": 2, "test": 2},
            )

    def test_invalid_fractions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assign_temporal_segments(make_frame(10), fractions=(0.5, 0.5, 0.5))

    def test_input_frame_is_not_modified(self) -> None:
        frame = make_frame(20)
        before = frame.copy(deep=True)
        segments = assign_temporal_segments(frame)
        pd.testing.assert_frame_equal(frame, before)
        self.assertTrue(segments.index.equals(frame.index))


if __name__ == "__main__":
    unittest.main()