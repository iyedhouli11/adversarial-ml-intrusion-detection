"""Phase 4.2: logistic-regression baseline.

Trained on Monday-Wednesday, evaluated on Thursday (validation).
Friday (final test) is never loaded here.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
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

DATA_DIR = Path("data/raw/CICIDS2017_improved")
SEED = 42
THRESHOLD = 0.5
MAX_ITER = 500


def per_label_table(labels: pd.Series, y_true: pd.Series, flagged) -> pd.DataFrame:
    """Share of flows flagged as attack, per original label.

    For effective attacks (target 1) this is the recall of that family.
    For BENIGN / Attempted (target 0) it is the false-positive rate.
    """
    frame = pd.DataFrame(
        {
            "label": labels.to_numpy(),
            "target": y_true.to_numpy(),
            "flagged": flagged,
        }
    )
    table = (
        frame.groupby(["target", "label"])
        .agg(n=("flagged", "size"), flagged_rate=("flagged", "mean"))
        .reset_index()
    )
    table["flagged_rate"] = table["flagged_rate"].round(4)
    return table


def run_strategy(strategy: str, train: pd.DataFrame, validation: pd.DataFrame) -> None:
    y_train = target_from_labels(train["Label"])
    y_val = target_from_labels(validation["Label"])

    # fit only on training; validation only receives transform
    fitted = fit_preprocessor(train, header_strategy=strategy)
    x_train = transform_frame(train, fitted)
    x_val = transform_frame(validation, fitted)

    model = LogisticRegression(max_iter=MAX_ITER, random_state=SEED)
    start = time.perf_counter()
    model.fit(x_train, y_train)
    train_seconds = time.perf_counter() - start

    start = time.perf_counter()
    scores = model.predict_proba(x_val)[:, 1]
    infer_seconds = time.perf_counter() - start
    flagged = (scores >= THRESHOLD).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_val, flagged).ravel()
    print(f"\n=== header_strategy={strategy} (threshold {THRESHOLD}) ===")
    print(f"iterations used: {model.n_iter_[0]} / max {MAX_ITER}")
    print(f"train time: {train_seconds:.1f}s | inference on Thursday: {infer_seconds:.2f}s")
    print(f"confusion matrix  TN={tn} FP={fp} FN={fn} TP={tp}")
    print(f"precision: {precision_score(y_val, flagged, zero_division=0):.4f}")
    print(f"recall:    {recall_score(y_val, flagged, zero_division=0):.4f}")
    print(f"F1:        {f1_score(y_val, flagged, zero_division=0):.4f}")
    print(
        f"PR-AUC:    {average_precision_score(y_val, scores):.4f} "
        f"(random reference = attack share = {y_val.mean():.4f})"
    )
    print("\nFlagged-as-attack rate per original label:")
    print(per_label_table(validation["Label"], y_val, flagged).to_string(index=False))


def main() -> None:
    train = load_split(DATA_DIR, "train")
    validation = load_split(DATA_DIR, "validation")
    assert set(train["source_day"]) == {"monday", "tuesday", "wednesday"}
    assert set(validation["source_day"]) == {"thursday"}

    for strategy in ("impute", "exclude"):
        run_strategy(strategy, train, validation)


if __name__ == "__main__":
    main()