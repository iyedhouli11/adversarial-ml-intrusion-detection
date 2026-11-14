"""Leakage-aware loading helpers for the daily CIC-IDS2017 files."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Literal

import pandas as pd

SplitName = Literal["train", "validation", "test"]

SPLIT_FILES: dict[SplitName, tuple[str, ...]] = {
    "train": ("monday.csv", "tuesday.csv", "wednesday.csv"),
    "validation": ("thursday.csv",),
    "test": ("friday.csv",),
}


def split_file_names(split: SplitName) -> tuple[str, ...]:
    """Return the immutable daily-file definition for a protocol split."""

    if split not in SPLIT_FILES:
        raise ValueError(f"Unknown split {split!r}; expected train, validation or test.")
    return SPLIT_FILES[split]


def source_days_for_split(split: SplitName) -> tuple[str, ...]:
    """Return source-day names without reading any data."""

    return tuple(Path(filename).stem for filename in split_file_names(split))


def load_daily_file(
    data_dir: Path | str,
    filename: str,
    *,
    usecols: Iterable[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Load one daily CSV into a working copy and attach its source day."""

    allowed_files = {name for names in SPLIT_FILES.values() for name in names}
    if filename not in allowed_files:
        raise ValueError(f"Unexpected daily file: {filename}")

    path = Path(data_dir) / filename
    if not path.is_file():
        raise FileNotFoundError(path)

    frame = pd.read_csv(
        path,
        encoding="cp1252",
        usecols=list(usecols) if usecols is not None else None,
        nrows=nrows,
        low_memory=True,
    )
    frame = frame.copy()
    frame["source_day"] = Path(filename).stem
    return frame


def load_split(
    data_dir: Path | str,
    split: SplitName,
    *,
    usecols: Iterable[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Load one protocol split, reading daily files sequentially."""

    frames = [
        load_daily_file(data_dir, filename, usecols=usecols, nrows=nrows)
        for filename in split_file_names(split)
    ]
    return pd.concat(frames, ignore_index=True)
