"""Phase 4.4: XGBoost on the per-stratum temporal split.

Monday-Wednesday only. The train segment fits everything (preprocessing and
model); the validation segment is used for evaluation. The test segment,
Thursday and Friday are never used here. Hyperparameters are fixed in advance.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from xgboost import XGBClassifier

from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    fit_preprocessor,
    target_from_labels,
    transform_frame,
)
from src.data.temporal_split import assign_temporal_segments
from src.models.logreg_baseline import per_label_table

DATA_DIR = Path("data/raw/CICIDS2017_improved")
SEED = 42
STRATEGY = "exclude"
THRESHOLD = 0.5
N_ESTIMATORS = 200
MAX_DEPTH = 6
LEARNING_RATE = 0.1


def main() -> None:
    frame = load_split(DATA_DIR, "train")
    assert set(frame["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(frame)
    train = frame[segments == "train"]
    validation = frame[segments == "validation"]
    del frame
    print(f"train rows: {len(train)} | validation rows: {len(validation)}")

    y_train = target_from_labels(train["Label"])
    y_val = target_from_labels(validation["Label"])

    # fit only on the train segment; trees need no scaling
    fitted = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    x_train = transform_frame(train, fitted)
    x_val = transform_frame(validation, fitted)

    model = XGBClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        learning_rate=LEARNING_RATE,
        tree_method="hist",
        n_jobs=-1,
        random_state=SEED,
    )
    start = time.perf_counter()
    model.fit(x_train, y_train)
    train_seconds = time.perf_counter() - start

    start = time.perf_counter()
    scores = model.predict_proba(x_val)[:, 1]
    infer_seconds = time.perf_counter() - start
    flagged = (scores >= THRESHOLD).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_val, flagged).ravel()
    print(
        f"\n=== XGBoost (strategy={STRATEGY}, n_estimators={N_ESTIMATORS}, "
        f"max_depth={MAX_DEPTH}, lr={LEARNING_RATE}, seed={SEED}, threshold {THRESHOLD}) ==="
    )
    print(f"train time: {train_seconds:.1f}s | inference: {infer_seconds:.2f}s")
    print(f"confusion matrix  TN={tn} FP={fp} FN={fn} TP={tp}")
    print(f"precision: {precision_score(y_val, flagged, zero_division=0):.4f}")
    print(f"recall:    {recall_score(y_val, flagged, zero_division=0):.4f}")
    print(f"F1:        {f1_score(y_val, flagged, zero_division=0):.4f}")
    print(
        f"PR-AUC:    {average_precision_score(y_val, scores):.4f} "
        f"(random reference = attack share = {y_val.mean():.4f})"
    )
    print("\nFlagged-as-attack rate per original label (validation segment):")
    print(per_label_table(validation["Label"], y_val, flagged).to_string(index=False))

    names = fitted.transformer.get_feature_names_out()
    importances = pd.Series(model.feature_importances_, index=names)
    print("\nTop 10 gain-based importances (correlated features share credit):")
    print(importances.sort_values(ascending=False).head(10).round(4).to_string())


if __name__ == "__main__":
    main()