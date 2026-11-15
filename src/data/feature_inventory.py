"""Feature inventory for the threat-model audit (train segment only).

Prints every column of the working data, which ones enter the model, and
simple statistics computed on the train segment. Validation, test, Thursday
and Friday are never loaded.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.dataset_loader import load_split
from src.data.preprocessing import prepare_working_frame, select_feature_columns
from src.data.temporal_split import assign_temporal_segments

DATA_DIR = Path("data/raw/CICIDS2017_improved")
STRATEGY = "exclude"


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    del raw

    working = prepare_working_frame(train, STRATEGY)
    columns = select_feature_columns(working, header_strategy=STRATEGY)
    excluded = [name for name in working.columns if name not in columns]
    print(f"train rows: {len(working)}")
    print(f"model input columns: {len(columns)}")
    print(f"excluded from model input ({len(excluded)}): {excluded}")

    rows = []
    for name in columns:
        series = working[name]
        numeric = pd.api.types.is_numeric_dtype(series)
        rows.append(
            {
                "column": name,
                "dtype": str(series.dtype),
                "n_unique": int(series.nunique(dropna=True)),
                "min": series.min() if numeric else "",
                "max": series.max() if numeric else "",
                "zero_share": round(float((series == 0).mean()), 4) if numeric else "",
                "nan_share": round(float(series.isna().mean()), 6),
            }
        )
    pd.set_option("display.float_format", "{:.6g}".format)
    pd.set_option("display.width", 220)
    print("\n=== Model input columns (statistics on the train segment) ===")
    print(pd.DataFrame(rows).to_string(index=False))

    if "Protocol" in columns:
        print("\n=== Protocol values (train segment) ===")
        print(working["Protocol"].value_counts().to_string())


if __name__ == "__main__":
    main()