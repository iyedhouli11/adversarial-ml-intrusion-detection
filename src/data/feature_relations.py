"""Relations between model features and attack destination ports (train segment only).

Measures, on the train segment, whether the formulas that link flow features
hold in this dataset. Nothing is assumed: each relation is measured.
Validation, test, Thursday and Friday are never loaded.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.data.dataset_loader import load_split
from src.data.preprocessing import prepare_working_frame
from src.data.temporal_split import assign_temporal_segments

DATA_DIR = Path("data/raw/CICIDS2017_improved")
STRATEGY = "exclude"
RTOL = 1e-3
ATOL = 1e-6
MICRO = 1e6  # assumption to verify: durations are in microseconds


def add_equality(results, name, left, right, eligible):
    mask = eligible & left.notna() & right.notna()
    lv = left[mask].to_numpy(dtype=float)
    rv = right[mask].to_numpy(dtype=float)
    holds = np.isclose(lv, rv, rtol=RTOL, atol=ATOL)
    rel = np.abs(lv - rv) / np.maximum(np.abs(rv), 1e-9)
    results.append(
        {
            "relation": name,
            "rows": int(mask.sum()),
            "holds_share": round(float(holds.mean()), 4) if len(lv) else float("nan"),
            "median_rel_err": float(np.median(rel)) if len(lv) else float("nan"),
        }
    )


def add_order(results, name, small, large):
    mask = small.notna() & large.notna()
    holds = (small[mask] <= large[mask] * (1 + RTOL) + ATOL).to_numpy()
    results.append(
        {
            "relation": name,
            "rows": int(mask.sum()),
            "holds_share": round(float(holds.mean()), 4) if len(holds) else float("nan"),
            "median_rel_err": float("nan"),
        }
    )


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    del raw

    c = prepare_working_frame(train, STRATEGY)
    everywhere = pd.Series(True, index=c.index)
    duration = c["Flow Duration"]
    positive = duration > 0
    fwd_pkts = c["Total Fwd Packet"]
    bwd_pkts = c["Total Bwd packets"]
    fwd_len = c["Total Length of Fwd Packet"]
    bwd_len = c["Total Length of Bwd Packet"]

    results: list[dict] = []
    add_equality(results, "Packet Length Variance = Packet Length Std^2",
                 c["Packet Length Variance"], c["Packet Length Std"] ** 2, everywhere)
    add_equality(results, "Fwd Segment Size Avg = Fwd Packet Length Mean",
                 c["Fwd Segment Size Avg"], c["Fwd Packet Length Mean"], everywhere)
    add_equality(results, "Bwd Segment Size Avg = Bwd Packet Length Mean",
                 c["Bwd Segment Size Avg"], c["Bwd Packet Length Mean"], everywhere)
    add_equality(results, "Total Length Fwd = Fwd Length Mean x Total Fwd Packet",
                 fwd_len, c["Fwd Packet Length Mean"] * fwd_pkts, everywhere)
    add_equality(results, "Total Length Bwd = Bwd Length Mean x Total Bwd packets",
                 bwd_len, c["Bwd Packet Length Mean"] * bwd_pkts, everywhere)
    add_equality(results, "Flow Packets/s = (Fwd+Bwd packets) / Duration x 1e6",
                 c["Flow Packets/s"], (fwd_pkts + bwd_pkts) / duration * MICRO, positive)
    add_equality(results, "Flow Bytes/s = (Length Fwd+Bwd) / Duration x 1e6",
                 c["Flow Bytes/s"], (fwd_len + bwd_len) / duration * MICRO, positive)
    add_equality(results, "Fwd Packets/s = Total Fwd Packet / Duration x 1e6",
                 c["Fwd Packets/s"], fwd_pkts / duration * MICRO, positive)
    add_equality(results, "Bwd Packets/s = Total Bwd packets / Duration x 1e6",
                 c["Bwd Packets/s"], bwd_pkts / duration * MICRO, positive)
    add_equality(results, "Down/Up Ratio = Total Bwd packets / Total Fwd Packet",
                 c["Down/Up Ratio"], bwd_pkts / fwd_pkts, fwd_pkts > 0)
    add_equality(results, "Packet Length Mean = (Length Fwd+Bwd) / (Fwd+Bwd packets)",
                 c["Packet Length Mean"], (fwd_len + bwd_len) / (fwd_pkts + bwd_pkts),
                 (fwd_pkts + bwd_pkts) > 0)
    add_equality(results, "Average Packet Size = Packet Length Mean",
                 c["Average Packet Size"], c["Packet Length Mean"], everywhere)
    add_equality(results, "Packet Length Max = max(Fwd Max, Bwd Max)",
                 c["Packet Length Max"],
                 np.maximum(c["Fwd Packet Length Max"], c["Bwd Packet Length Max"]),
                 everywhere)
    add_order(results, "Fwd IAT Total <= Flow Duration", c["Fwd IAT Total"], duration)
    add_order(results, "Total TCP Flow Time <= Flow Duration",
              c["Total TCP Flow Time"], duration)
    add_order(results, "Fwd Packet Length Min <= Mean",
              c["Fwd Packet Length Min"], c["Fwd Packet Length Mean"])
    add_order(results, "Fwd Packet Length Mean <= Max",
              c["Fwd Packet Length Mean"], c["Fwd Packet Length Max"])

    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 80)
    print(f"train rows: {len(c)} | tolerance: relative {RTOL}")
    print("\n=== Relation checks (share of eligible rows where the relation holds) ===")
    print(pd.DataFrame(results).to_string(index=False))

    print("\n=== Top 3 destination ports per label (share of the label's flows) ===")
    for label, part in c.groupby("Label"):
        top = part["Dst Port"].value_counts(normalize=True).head(3).round(3)
        print(f"{label}: {top.to_dict()}")


if __name__ == "__main__":
    main()