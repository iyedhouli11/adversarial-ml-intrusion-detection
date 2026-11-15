"""Phase 4.3: Random Forest baseline.

Trained on Monday-Wednesday, evaluated on Thursday (validation).
Friday (final test) is never loaded. Hyperparameters are fixed in advance
(no tuning in this step) and documented in the constants below.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    fit_preprocessor,
    target_from_labels,
    transform_frame,
)
from src.models.logreg_baseline import per_label_table

DATA_DIR = Path("data/raw/CICIDS2017_improved")
SEED = 42
STRATEGY = "exclude"
N_ESTIMATORS = 100
MIN_SAMPLES_LEAF = 5
THRESHOLDS = (0.5, 0.3, 0.1, 0.05, 0.01)


def main() -> None:
    train = load_split(DATA_DIR, "train")
    validation = load_split(DATA_DIR, "validation")
    assert set(train["source_day"]) == {"monday", "tuesday", "wednesday"}
    assert set(validation["source_day"]) == {"thursday"}

    y_train = target_from_labels(train["Label"])
    y_val = target_from_labels(validation["Label"])

    # fit only on training; no scaling needed for trees
    fitted = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    x_train = transform_frame(train, fitted)
    x_val = transform_frame(validation, fitted)

    model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        n_jobs=-1,
        random_state=SEED,
    )
    start = time.perf_counter()
    model.fit(x_train, y_train)
    train_seconds = time.perf_counter() - start

    start = time.perf_counter()
    scores = model.predict_proba(x_val)[:, 1]
    infer_seconds = time.perf_counter() - start

    print(
        f"=== RandomForest (strategy={STRATEGY}, n_estimators={N_ESTIMATORS}, "
        f"min_samples_leaf={MIN_SAMPLES_LEAF}, seed={SEED}) ==="
    )
    print(f"train time: {train_seconds:.1f}s | inference on Thursday: {infer_seconds:.2f}s")
    print(
        f"PR-AUC: {average_precision_score(y_val, scores):.4f} "
        f"(random reference = attack share = {y_val.mean():.4f})"
    )

    labels = validation["Label"].to_numpy()
    portscan = labels == "Infiltration - Portscan"
    benign = labels == "BENIGN"

    rows = []
    for threshold in THRESHOLDS:
        flagged = (scores >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_val, flagged).ravel()
        rows.append(
            {
                "threshold": threshold,
                "TN": tn,
                "FP": fp,
                "FN": fn,
                "TP": tp,
                "precision": precision_score(y_val, flagged, zero_division=0),
                "recall": recall_score(y_val, flagged),
                "F1": f1_score(y_val, flagged, zero_division=0),
                "alerts_per_10k": round(float(flagged.mean()) * 10_000),
                "portscan_recall": float(flagged[portscan].mean()),
                "benign_flag_rate": float(flagged[benign].mean()),
            }
        )
    print("\n=== Metrics per threshold (validation only; no threshold selected) ===")
    print(pd.DataFrame(rows).round(4).to_string(index=False))

    flagged_default = (scores >= 0.5).astype(int)
    print("\nFlagged-as-attack rate per original label (threshold 0.5):")
    print(per_label_table(validation["Label"], y_val, flagged_default).to_string(index=False))

    names = fitted.transformer.get_feature_names_out()
    importances = pd.Series(model.feature_importances_, index=names)
    print("\nTop 10 impurity-based importances (correlated features share credit):")
    print(importances.sort_values(ascending=False).head(10).round(4).to_string())


if __name__ == "__main__":
    main()