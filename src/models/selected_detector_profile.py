"""Evasion denominator, score margin and feature usage of the selected XGBoost.

Validation only. The selected configuration (max_depth=3, n_estimators=100)
comes from the pre-declared selection rule of the tuning step. The test
segment, Thursday and Friday are never loaded.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from xgboost import XGBClassifier

from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    fit_preprocessor,
    target_from_labels,
    transform_frame,
)
from src.data.temporal_split import assign_temporal_segments

DATA_DIR = Path("data/raw/CICIDS2017_improved")
SEED = 42
STRATEGY = "exclude"
THRESHOLD = 0.5
PARAMS = {"max_depth": 3, "n_estimators": 100}


def side(name: str) -> str:
    """Name-based grouping only; not a judgement of attacker controllability."""
    lowered = name.lower()
    if "fwd" in lowered:
        return "fwd"
    if "bwd" in lowered:
        return "bwd"
    return "other"


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    validation = raw[segments == "validation"]
    del raw
    y_train = target_from_labels(train["Label"])
    y_val = target_from_labels(validation["Label"])

    # fit only on the train segment
    fitted = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    x_train = transform_frame(train, fitted)
    x_val = transform_frame(validation, fitted)

    model = XGBClassifier(
        learning_rate=0.1,
        tree_method="hist",
        n_jobs=-1,
        random_state=SEED,
        importance_type="gain",
        **PARAMS,
    )
    model.fit(x_train, y_train)
    scores = model.predict_proba(x_val)[:, 1]

    frame = pd.DataFrame(
        {
            "label": validation["Label"].to_numpy(),
            "target": y_val.to_numpy(),
            "score": scores,
        }
    )
    frame["detected"] = frame["score"] >= THRESHOLD
    attacks = frame[frame["target"] == 1]
    detected = attacks[attacks["detected"]]
    print(f"validation attack flows: {len(attacks)}")
    print(f"detected at {THRESHOLD}: {len(detected)} | missed: {len(attacks) - len(detected)}")

    by_family = attacks.groupby("label")["detected"].agg(["size", "sum", "mean"])
    by_family.columns = ["flows", "detected", "detected_rate"]
    print("\n=== Evasion denominator per family (attacks detected at 0.5) ===")
    print(by_family.round(4).to_string())

    quantiles = (
        detected.groupby("label")["score"].quantile([0.05, 0.5, 0.95]).unstack().round(4)
    )
    print("\n=== Scores of detected attacks (quantiles 5 / 50 / 95 %) ===")
    print(quantiles.to_string())

    names = fitted.transformer.get_feature_names_out()
    importance = pd.Series(model.feature_importances_, index=names)
    print("\n=== Top 15 gain importances (correlated features share credit) ===")
    print(importance.sort_values(ascending=False).head(15).round(4).to_string())

    groups = importance.groupby(importance.index.map(side)).sum().round(4)
    print("\n=== Gain by name-based group (fwd / bwd / other) ===")
    print(groups.to_string())


if __name__ == "__main__":
    main()