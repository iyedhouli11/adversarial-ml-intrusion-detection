"""Per-stratum temporal split for the training days (Monday-Wednesday).

Observed in the label timeline: inside one day, attacks run in narrow time
windows, so a plain 80/20 cut of the day leaves almost no attack in the last
20 %. Here each stratum (source day x original label) is ordered by time and
cut separately: first part -> train, next part -> validation, last part ->
test, with a small gap around each cut to limit near-duplicate neighbours.

Only Timestamp and Label are read. Thursday and Friday are never loaded.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.dataset_loader import load_daily_file
from src.data.preprocessing import target_from_labels

DATA_DIR = Path("data/raw/CICIDS2017_improved")
TRAIN_DAYS = ("monday.csv", "tuesday.csv", "wednesday.csv")
SEGMENT_ORDER = ("train", "validation", "test", "gap")
DEFAULT_FRACTIONS = (0.60, 0.20, 0.20)
DEFAULT_GAP_FRACTION = 0.01


def assign_temporal_segments(
    frame: pd.DataFrame,
    *,
    fractions: tuple[float, float, float] = DEFAULT_FRACTIONS,
    gap_fraction: float = DEFAULT_GAP_FRACTION,
    time_column: str = "Timestamp",
    label_column: str = "Label",
    day_column: str = "source_day",
) -> pd.Series:
    """Label each row train / validation / test / gap, aligned to frame.index.

    The input frame is not modified.
    """
    if (
        len(fractions) != 3
        or any(value <= 0 for value in fractions)
        or abs(sum(fractions) - 1.0) > 1e-9
    ):
        raise ValueError("fractions must be three positive numbers summing to 1")
    if not 0.0 <= gap_fraction < min(fractions) / 2:
        raise ValueError("gap_fraction must be >= 0 and below half the smallest fraction")

    times = pd.to_datetime(frame[time_column], format="ISO8601")
    if times.isna().any():
        raise ValueError("Missing timestamps cannot be ordered")

    work = pd.DataFrame(
        {
            "day": frame[day_column].to_numpy(),
            "label": frame[label_column].to_numpy(),
            "time": times.to_numpy(),
        }
    ).sort_values("time", kind="stable")

    groups = work.groupby(["day", "label"], sort=False)
    rank = groups.cumcount().to_numpy()
    size = groups["time"].transform("size").to_numpy()
    position = rank / size  # 0 = earliest flow of the stratum, close to 1 = latest

    first_cut = fractions[0]
    second_cut = round(fractions[0] + fractions[1], 12)
    segment = np.select(
        [
            np.abs(position - first_cut) < gap_fraction,
            np.abs(position - second_cut) < gap_fraction,
            position < first_cut,
            position < second_cut,
        ],
        ["gap", "gap", "train", "validation"],
        default="test",
    )

    positional = pd.Series(segment, index=work.index, name="segment").sort_index()
    positional.index = frame.index
    return positional


def main() -> None:
    frames = [
        load_daily_file(DATA_DIR, name, usecols=["Timestamp", "Label"])
        for name in TRAIN_DAYS
    ]
    frame = pd.concat(frames, ignore_index=True)
    assert set(frame["source_day"]) == {"monday", "tuesday", "wednesday"}
    frame["segment"] = assign_temporal_segments(frame)
    frame["target"] = target_from_labels(frame["Label"]).astype("int64")

    counts = pd.crosstab([frame["source_day"], frame["Label"]], frame["segment"])
    print("=== Rows per (day, label) and segment ===")
    print(counts.reindex(columns=list(SEGMENT_ORDER), fill_value=0).to_string())

    summary = frame.groupby("segment").agg(
        rows=("target", "size"), attacks=("target", "sum")
    )
    summary["attack_share"] = (summary["attacks"] / summary["rows"]).round(4)
    print("\n=== Attack share per segment ===")
    print(summary.reindex(list(SEGMENT_ORDER)).to_string())

    times = pd.to_datetime(frame["Timestamp"], format="ISO8601")
    for (day, label), part in frame.assign(time=times).groupby(["source_day", "Label"]):
        spans = part.groupby("segment")["time"].agg(["min", "max"])
        present = [name for name in SEGMENT_ORDER[:3] if name in spans.index]
        for earlier, later in itertools.pairwise(present):
            assert spans.loc[earlier, "max"] <= spans.loc[later, "min"], (
                day,
                label,
                earlier,
                later,
            )
    print("\nTemporal order check: PASS")


if __name__ == "__main__":
    main()