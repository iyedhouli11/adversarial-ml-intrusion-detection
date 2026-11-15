"""Phase 4.3-b: logistic regression and random forest on the per-stratum split.

Monday-Wednesday only. The train segment fits everything (preprocessing and
model); the validation segment is used for evaluation. The test segment,
Thursday and Friday are never used here. Hyperparameters are fixed in advance.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
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
from src.data.temporal_split import assign_temporal_segments
from src.models.logreg_baseline import per_label_table

DATA_DIR = Path("data/raw/CICIDS2017_improved")
SEED = 42
STRATEGY = "exclude"
THRESHOLD = 0.5


def duplicate_report(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    columns: list[str],
    y_val: pd.Series,
) -> None:
    """Share of validation rows whose raw feature vector also occurs in train."""
    train_hash = pd.util.hash_pandas_object(train[columns], index=False).to_numpy()
    val_hash = pd.util.hash_pandas_object(validation[columns], index=False).to_numpy()
    duplicated = np.isin(val_hash, train_hash)
    attack = y_val.to_numpy() == 1
    print("=== Exact duplicates of training rows in the validation segment ===")
    print(f"all rows:    {duplicated.mean():.4f}")
    print(f"attack rows: {duplicated[attack].mean():.4f}")
    print(f"normal rows: {duplicated[~attack].mean():.4f}")


def evaluate(
    name: str,
    model: Any,
    x_train: Any,
    y_train: pd.Series,
    x_val: Any,
    y_val: pd.Series,
    val_labels: pd.Series,
) -> None:
    start = time.perf_counter()
    model.fit(x_train, y_train)
    train_seconds = time.perf_counter() - start

    start = time.perf_counter()
    scores = model.predict_proba(x_val)[:, 1]
    infer_seconds = time.perf_counter() - start
    flagged = (scores >= THRESHOLD).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_val, flagged).ravel()
    print(f"\n=== {name} (strategy={STRATEGY}, threshold {THRESHOLD}) ===")
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
    print(per_label_table(val_labels, y_val, flagged).to_string(index=False))


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

    # fit only on the train segment; validation only receives transform
    scaled = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=True)
    duplicate_report(train, validation, list(scaled.feature_columns), y_val)
    evaluate(
        "LogisticRegression",
        LogisticRegression(max_iter=500, random_state=SEED),
        transform_frame(train, scaled),
        y_train,
        transform_frame(validation, scaled),
        y_val,
        validation["Label"],
    )

    unscaled = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    evaluate(
        "RandomForest",
        RandomForestClassifier(
            n_estimators=100, min_samples_leaf=5, n_jobs=-1, random_state=SEED
        ),
        transform_frame(train, unscaled),
        y_train,
        transform_frame(validation, unscaled),
        y_val,
        validation["Label"],
    )


if __name__ == "__main__":
    main()