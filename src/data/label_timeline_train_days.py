"""Label timeline per training day (Monday-Wednesday only).

Shows how original labels are spread across time deciles inside each day.
Thursday (validation) and Friday (final test) are never loaded.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.dataset_loader import load_daily_file

DATA_DIR = Path("data/raw/CICIDS2017_improved")
TRAIN_DAYS = ("monday.csv", "tuesday.csv", "wednesday.csv")
N_BINS = 10


def main() -> None:
    for filename in TRAIN_DAYS:
        frame = load_daily_file(DATA_DIR, filename, usecols=["Timestamp", "Label"])
        frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], format="ISO8601")
        frame = frame.sort_values("Timestamp").reset_index(drop=True)
        n_rows = len(frame)
        # decile 0 = earliest tenth of the flows of the day, 9 = latest tenth
        frame["time_decile"] = (frame.index * N_BINS // n_rows).astype(int)

        print(f"\n=== {filename} | {n_rows} flows ===")
        print(f"first: {frame['Timestamp'].iloc[0]} | last: {frame['Timestamp'].iloc[-1]}")
        print(pd.crosstab(frame["Label"], frame["time_decile"]).to_string())


if __name__ == "__main__":
    main()