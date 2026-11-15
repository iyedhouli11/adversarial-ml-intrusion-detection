"""Phase 4.2-b: threshold diagnostic for the logistic baseline.

Validation (Thursday) only. This script chooses no threshold; it only
describes how the scores behave. Friday is never loaded.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score

from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    fit_preprocessor,
    target_from_labels,
    transform_frame,
)

DATA_DIR = Path("data/raw/CICIDS2017_improved")
SEED = 42
STRATEGY = "exclude"
THRESHOLDS = (0.5, 0.3, 0.1, 0.05, 0.01, 0.001)
QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)


def main() -> None:
    train = load_split(DATA_DIR, "train")
    validation = load_split(DATA_DIR, "validation")
    assert set(validation["source_day"]) == {"thursday"}

    y_train = target_from_labels(train["Label"])
    y_val = target_from_labels(validation["Label"])

    fitted = fit_preprocessor(train, header_strategy=STRATEGY)
    x_train = transform_frame(train, fitted)
    x_val = transform_frame(validation, fitted)

    model = LogisticRegression(max_iter=500, random_state=SEED).fit(x_train, y_train)
    scores = model.predict_proba(x_val)[:, 1]

    labels = validation["Label"].to_numpy()
    portscan = labels == "Infiltration - Portscan"
    benign = labels == "BENIGN"

    rows = []
    for threshold in THRESHOLDS:
        flagged = scores >= threshold
        rows.append(
            {
                "threshold": threshold,
                "alerts_per_10k_flows": round(float(flagged.mean()) * 10_000),
                "precision": precision_score(y_val, flagged, zero_division=0),
                "recall": recall_score(y_val, flagged),
                "portscan_recall": float(flagged[portscan].mean()),
                "benign_flag_rate": float(flagged[benign].mean()),
            }
        )
    print(f"=== Threshold diagnostic (strategy={STRATEGY}, validation only) ===")
    print(pd.DataFrame(rows).round(4).to_string(index=False))

    quantiles = pd.DataFrame(
        {
            "portscan": pd.Series(scores[portscan]).quantile(list(QUANTILES)),
            "benign": pd.Series(scores[benign]).quantile(list(QUANTILES)),
        }
    )
    print("\n=== Score quantiles (probability of attack) ===")
    print(quantiles.round(4).to_string())


if __name__ == "__main__":
    main()