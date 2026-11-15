"""Second batch of relation checks (train segment only).

Tests the pooled-variance reconstruction, inter-arrival-time relations, flag
sums and the Total TCP Flow Time anomaly. Validation, test, Thursday and
Friday are never loaded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.dataset_loader import load_split
from src.data.feature_relations import DATA_DIR, STRATEGY, add_equality, add_order
from src.data.preprocessing import prepare_working_frame
from src.data.temporal_split import assign_temporal_segments


def pooled_variance(c: pd.DataFrame, *, sample: bool) -> pd.Series:
    """Overall packet-length variance rebuilt from per-direction mean, std and count."""
    n_f, n_b = c["Total Fwd Packet"], c["Total Bwd packets"]
    m_f, m_b = c["Fwd Packet Length Mean"], c["Bwd Packet Length Mean"]
    s_f, s_b = c["Fwd Packet Length Std"], c["Bwd Packet Length Std"]
    total = n_f + n_b
    mean = c["Packet Length Mean"]
    between = n_f * (m_f - mean) ** 2 + n_b * (m_b - mean) ** 2
    if sample:
        within = (n_f - 1).clip(lower=0) * s_f**2 + (n_b - 1).clip(lower=0) * s_b**2
        return (within + between) / (total - 1)
    within = n_f * s_f**2 + n_b * s_b**2
    return (within + between) / total


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    del raw

    c = prepare_working_frame(train, STRATEGY)
    n_f, n_b = c["Total Fwd Packet"], c["Total Bwd packets"]
    total = n_f + n_b
    duration = c["Flow Duration"]
    everywhere = pd.Series(True, index=c.index)

    results: list[dict] = []
    add_equality(results, "Packet Length Variance = pooled variance (sample, n-1)",
                 c["Packet Length Variance"], pooled_variance(c, sample=True), total > 1)
    add_equality(results, "Packet Length Variance = pooled variance (population, n)",
                 c["Packet Length Variance"], pooled_variance(c, sample=False), total > 1)

    fwd_min = c["Fwd Packet Length Min"].where(n_f > 0, np.inf)
    bwd_min = c["Bwd Packet Length Min"].where(n_b > 0, np.inf)
    add_equality(results, "Packet Length Min = min over non-empty directions",
                 c["Packet Length Min"], np.minimum(fwd_min, bwd_min), total > 0)

    add_equality(results, "Flow IAT Mean x (packets-1) = Flow Duration",
                 c["Flow IAT Mean"] * (total - 1), duration, total > 1)
    add_equality(results, "Fwd IAT Mean x (Fwd packets-1) = Fwd IAT Total",
                 c["Fwd IAT Mean"] * (n_f - 1), c["Fwd IAT Total"], n_f > 1)
    add_equality(results, "Bwd IAT Mean x (Bwd packets-1) = Bwd IAT Total",
                 c["Bwd IAT Mean"] * (n_b - 1), c["Bwd IAT Total"], n_b > 1)

    add_equality(results, "PSH Flag Count = Fwd PSH Flags + Bwd PSH Flags",
                 c["PSH Flag Count"], c["Fwd PSH Flags"] + c["Bwd PSH Flags"], everywhere)
    add_equality(results, "RST Flag Count = Fwd RST Flags + Bwd RST Flags",
                 c["RST Flag Count"], c["Fwd RST Flags"] + c["Bwd RST Flags"], everywhere)

    add_equality(results, "Subflow Fwd Bytes = Total Length of Fwd Packet",
                 c["Subflow Fwd Bytes"], c["Total Length of Fwd Packet"], everywhere)
    add_equality(results, "Subflow Bwd Bytes = Total Length of Bwd Packet",
                 c["Subflow Bwd Bytes"], c["Total Length of Bwd Packet"], everywhere)

    add_order(results, "Flow IAT Min <= Flow IAT Mean", c["Flow IAT Min"], c["Flow IAT Mean"])
    add_order(results, "Flow IAT Mean <= Flow IAT Max", c["Flow IAT Mean"], c["Flow IAT Max"])
    add_order(results, "Flow IAT Max <= Flow Duration", c["Flow IAT Max"], duration)

    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 80)
    print(f"train rows: {len(c)}")
    print("\n=== Relation checks (share of eligible rows where the relation holds) ===")
    print(pd.DataFrame(results).to_string(index=False))

    violating = c["Total TCP Flow Time"] > duration * 1.001
    print(
        f"\nTotal TCP Flow Time > Flow Duration: {int(violating.sum())} rows "
        f"({violating.mean():.4f})"
    )
    ratio = (c["Total TCP Flow Time"] / duration)[violating & (duration > 0)]
    print(f"median ratio (TCP time / duration) among violating rows: {ratio.median():.3f}")
    frame = pd.DataFrame(
        {"protocol": c["Protocol"], "label": c["Label"], "violating": violating}
    )
    print("\nViolations by Protocol:")
    print(frame.groupby("protocol")["violating"].agg(["size", "sum", "mean"]).round(4).to_string())
    print("\nViolations by Label:")
    print(frame.groupby("label")["violating"].agg(["size", "sum", "mean"]).round(4).to_string())


if __name__ == "__main__":
    main()