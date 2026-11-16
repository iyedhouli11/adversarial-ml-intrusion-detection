"""Feasibility preview of the perturbation layer (train segment only).

Runs the identity test and measures how often perturbed candidates would be
rejected, per label and amplitude. No model is queried. Validation, test,
Thursday and Friday are never loaded.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.attacks.perturbation import CHANGED_COLUMNS, perturb, rejection_reasons
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


def identity_report(features: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in CHANGED_COLUMNS:
        before = features[column].to_numpy(dtype=float)
        after = candidate[column].to_numpy(dtype=float)
        finite_before, finite_after = np.isfinite(before), np.isfinite(after)
        both = finite_before & finite_after
        close = np.isclose(before[both], after[both], rtol=1e-3, atol=1e-6)
        rows.append(
            {
                "column": column,
                "not_close_rows": int((~close).sum()),
                "finiteness_changed": int((finite_before != finite_after).sum()),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    del raw

    working = prepare_working_frame(train, STRATEGY)
    columns = select_feature_columns(working, header_strategy=STRATEGY)
    features = working[columns]
    labels = working["Label"]
    is_attack = target_from_labels(labels).to_numpy() == 1
    lower, upper = features.min(), features.max()
    print(f"train rows: {len(features)} | model columns: {len(columns)}")

    pd.set_option("display.width", 220)
    identity = perturb(features, 1.0, 1.0)
    print("\n=== Identity test (s = t = 1) ===")
    print(identity_report(features, identity).to_string(index=False))
    reasons = rejection_reasons(features, identity, lower, upper)
    print(f"rows flagged at identity: {int(reasons.any(axis=1).sum())} of {len(reasons)}")
    print(reasons.sum().to_string())

    by_label: dict[str, pd.Series] = {}
    by_reason: dict[str, pd.Series] = {}
    for amplitude in AMPLITUDES:
        factor = 1.0 + amplitude
        candidate = perturb(features, factor, factor)
        reasons = rejection_reasons(features, candidate, lower, upper)
        rejected = pd.DataFrame(
            {"label": labels.to_numpy(), "rejected": reasons.any(axis=1).to_numpy()}
        )
        by_label[f"A={amplitude}"] = rejected.groupby("label")["rejected"].mean()
        by_reason[f"A={amplitude}"] = reasons[is_attack].mean()

    table = pd.DataFrame(by_label).round(4)
    table.insert(0, "flows", labels.value_counts())
    print("\n=== Share of candidates rejected (s = t = 1 + A), train segment ===")
    print(table.to_string())
    print("\n=== Rejection reasons among attack flows (share of flows) ===")
    print(pd.DataFrame(by_reason).round(4).to_string())

    over_mtu = pd.Series((features["Fwd Packet Length Max"] > MTU).to_numpy())
    print(f"\n=== Share of flows with Fwd Packet Length Max > {MTU}, per label ===")
    print(over_mtu.groupby(labels.to_numpy()).mean().round(4).to_string())


if __name__ == "__main__":
    main()