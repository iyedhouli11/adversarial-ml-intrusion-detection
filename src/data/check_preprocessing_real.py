"""Real-data sanity check of the preprocessing pipeline (train + validation only).

Friday (final test) is never loaded here.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    HEADER_LENGTH_COLUMNS,
    fit_preprocessor,
    target_from_labels,
    transform_frame,
)

DATA_DIR = Path("data/raw/CICIDS2017_improved")


def all_finite(matrix) -> bool:
    values = matrix.data if sparse.issparse(matrix) else np.asarray(matrix)
    return bool(np.isfinite(values).all())


def describe(name: str, frame: pd.DataFrame) -> pd.Series:
    mem_gib = frame.memory_usage(deep=True).sum() / 1024**3
    print(f"\n=== {name} ===")
    print(f"shape: {frame.shape}, memory: {mem_gib:.2f} GiB")
    print("source_day:", frame["source_day"].value_counts().to_dict())
    target = target_from_labels(frame["Label"])  # raises on unknown labels
    print("target counts (0=normal/attempted, 1=attack):", target.value_counts().to_dict())
    print(f"attack share: {target.mean():.4%}")
    print("original labels:", frame["Label"].value_counts().to_dict())
    for column in HEADER_LENGTH_COLUMNS:
        if column in frame.columns:
            print(f"negative {column}: {int((frame[column] < 0).sum())}")
    return target


def main() -> None:
    start = time.perf_counter()
    train = load_split(DATA_DIR, "train")
    validation = load_split(DATA_DIR, "validation")
    describe("TRAIN (Mon+Tue+Wed)", train)
    describe("VALIDATION (Thu)", validation)

    assert set(train["source_day"]) == {"monday", "tuesday", "wednesday"}
    assert set(validation["source_day"]) == {"thursday"}

    for strategy in ("impute", "exclude"):
        fitted = fit_preprocessor(train, header_strategy=strategy)
        x_train = transform_frame(train, fitted)
        x_val = transform_frame(validation, fitted)
        print(f"\n=== header_strategy={strategy} ===")
        print("numeric columns:", len(fitted.numeric_columns))
        print("categorical columns:", fitted.categorical_columns)
        print("X_train:", x_train.shape, "finite:", all_finite(x_train))
        print("X_val:  ", x_val.shape, "finite:", all_finite(x_val))
        print("header columns in X:",
              [c for c in HEADER_LENGTH_COLUMNS if c in fitted.feature_columns])
        del x_train, x_val

    print(f"\nElapsed: {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()