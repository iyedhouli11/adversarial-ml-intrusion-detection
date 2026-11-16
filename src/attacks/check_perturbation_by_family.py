"""Per-family feasibility of padding and delay (train segment only).

Separates padding-only, delay-only and combined perturbations for effective
attack flows, applies a 1500-byte MTU rule inside this measurement only, and
shows which columns leave the train bounds. No model is queried. Validation,
test, Thursday and Friday are never loaded.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.attacks.perturbation import (
    BOUND_RTOL,
    CHANGED_COLUMNS,
    perturb,
    rejection_reasons,
)
from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    prepare_working_frame,
    select_feature_columns,
    target_from_labels,
)
from src.data.temporal_split import assign_temporal_segments

DATA_DIR = Path("data/raw/CICIDS2017_improved")
STRATEGY = "exclude"
AMPLITUDES = (0.1, 0.25, 0.5, 1.0, 2.0)
MTU = 1500
FOCUS = ("DoS Slowloris", "DoS Slowhttptest", "DoS GoldenEye")
MODES = {
    "padding": lambda factor: (factor, 1.0),
    "delay": lambda factor: (1.0, factor),
    "both": lambda factor: (factor, factor),
}


def bounds_by_column(candidate: pd.DataFrame, lower: pd.Series, upper: pd.Series) -> pd.Series:
    """Share of rows where each changed column leaves the train range."""
    columns = list(CHANGED_COLUMNS)
    values, low, high = candidate[columns], lower[columns], upper[columns]
    below = values.lt(low - low.abs() * BOUND_RTOL - 1e-9, axis=1)
    above = values.gt(high + high.abs() * BOUND_RTOL + 1e-9, axis=1)
    return (below | above).mean()


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    del raw

    working = prepare_working_frame(train, STRATEGY)
    columns = select_feature_columns(working, header_strategy=STRATEGY)
    features_all = working[columns]
    lower, upper = features_all.min(), features_all.max()  # bounds from all train rows
    labels_all = working["Label"]
    effective = target_from_labels(labels_all).to_numpy() == 1
    features = features_all[effective]
    labels = labels_all[effective].to_numpy()
    print(f"effective attack flows in train: {len(features)}")

    pd.set_option("display.width", 220)
    fwd_max = features["Fwd Packet Length Max"]
    headroom = (MTU / fwd_max.where(fwd_max > 0)).groupby(labels).quantile([0.05, 0.5, 0.95])
    print("\n=== Largest padding factor before an MTU of 1500 (quantiles 5 / 50 / 95 %) ===")
    print(headroom.unstack().round(3).to_string())

    records = []
    for mode, make in MODES.items():
        for amplitude in AMPLITUDES:
            s, t = make(1.0 + amplitude)
            candidate = perturb(features, s, t)
            reasons = rejection_reasons(features, candidate, lower, upper)
            mtu = (candidate["Fwd Packet Length Max"] > MTU).to_numpy()
            frame = pd.DataFrame(
                {
                    "label": labels,
                    "rejected": reasons.any(axis=1).to_numpy() | mtu,
                    "mtu": mtu,
                    "bounds": reasons["out_of_bounds"].to_numpy(),
                }
            )
            grouped = frame.groupby("label").mean()
            grouped["mode"], grouped["A"] = mode, amplitude
            records.append(grouped.reset_index())
    result = pd.concat(records)

    for mode in MODES:
        part = result[result["mode"] == mode]
        print(f"\n=== {mode}: share rejected (any rule, MTU included) ===")
        print(part.pivot(index="label", columns="A", values="rejected").round(4).to_string())
    print("\n=== padding: share rejected by the MTU rule alone ===")
    part = result[result["mode"] == "padding"]
    print(part.pivot(index="label", columns="A", values="mtu").round(4).to_string())
    print("\n=== delay: share rejected by the train bounds alone ===")
    part = result[result["mode"] == "delay"]
    print(part.pivot(index="label", columns="A", values="bounds").round(4).to_string())

    candidate = perturb(features, 1.0, 1.25)
    print("\n=== Columns leaving the train bounds, delay only, A = 0.25 (top 5) ===")
    for family in FOCUS:
        share = bounds_by_column(candidate[labels == family], lower, upper)
        top = share[share > 0].sort_values(ascending=False).head(5).round(4)
        print(f"{family}: {top.to_dict()}")


if __name__ == "__main__":
    main()