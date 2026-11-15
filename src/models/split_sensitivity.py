"""Phase 4.5-a: sensitivity of the per-stratum split to gap size and duplicates.

Monday-Wednesday only. Models are fitted on the train segment and evaluated on
the validation segment. The test segment, Thursday and Friday are never used.
Hyperparameters are the ones fixed in advance in earlier phases (no tuning).
"""

from __future__ import annotations

import time
from pathlib import Path

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
from xgboost import XGBClassifier

from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    fit_preprocessor,
    select_feature_columns,
    target_from_labels,
    transform_frame,
)
from src.data.temporal_split import assign_temporal_segments

DATA_DIR = Path("data/raw/CICIDS2017_improved")
SEED = 42
STRATEGY = "exclude"
THRESHOLD = 0.5
MIN_FAMILY_FLOWS = 100
CONFIGS = (
    {"name": "gap1%", "gap": 0.01, "dedup": False},
    {"name": "gap5%", "gap": 0.05, "dedup": False},
    {"name": "gap1%+dedup", "gap": 0.01, "dedup": True},
    {"name": "gap5%+dedup", "gap": 0.05, "dedup": True},
)


def deduplicate_before_split(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with an identical model feature vector, keeping the earliest."""
    times = pd.to_datetime(frame["Timestamp"], format="ISO8601")
    ordered = frame.loc[times.sort_values(kind="stable").index]
    columns = select_feature_columns(ordered, header_strategy=STRATEGY)
    return ordered[~ordered.duplicated(subset=columns, keep="first")]


def min_family_recall(labels: pd.Series, y_true: pd.Series, flagged) -> float:
    """Lowest detection rate among attack families with enough validation flows."""
    table = pd.DataFrame(
        {"label": labels.to_numpy(), "target": y_true.to_numpy(), "flagged": flagged}
    )
    attacks = table[table["target"] == 1]
    stats = attacks.groupby("label")["flagged"].agg(["size", "mean"])
    return float(stats[stats["size"] >= MIN_FAMILY_FLOWS]["mean"].min())


def score_model(name, model, x_train, y_train, x_val, y_val, labels, config):
    start = time.perf_counter()
    model.fit(x_train, y_train)
    seconds = time.perf_counter() - start
    scores = model.predict_proba(x_val)[:, 1]
    flagged = (scores >= THRESHOLD).astype(int)
    _, fp, fn, _ = confusion_matrix(y_val, flagged).ravel()
    return {
        "config": config["name"],
        "model": name,
        "PR-AUC": average_precision_score(y_val, scores),
        "precision": precision_score(y_val, flagged, zero_division=0),
        "recall": recall_score(y_val, flagged, zero_division=0),
        "F1": f1_score(y_val, flagged, zero_division=0),
        "FP": fp,
        "FN": fn,
        "min_family_recall": min_family_recall(labels, y_val, flagged),
        "fit_s": round(seconds, 1),
    }


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}

    rows = []
    for config in CONFIGS:
        frame = deduplicate_before_split(raw) if config["dedup"] else raw
        removed = len(raw) - len(frame)
        segments = assign_temporal_segments(frame, gap_fraction=config["gap"])
        train = frame[segments == "train"]
        validation = frame[segments == "validation"]
        y_train = target_from_labels(train["Label"])
        y_val = target_from_labels(validation["Label"])
        print(
            f"\n--- {config['name']}: removed duplicates={removed} | "
            f"train={len(train)} | validation={len(validation)} | "
            f"validation attack share={y_val.mean():.4f}"
        )

        # fit only on the train segment
        scaled = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=True)
        plain = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
        xs_train, xs_val = transform_frame(train, scaled), transform_frame(validation, scaled)
        xp_train, xp_val = transform_frame(train, plain), transform_frame(validation, plain)
        labels = validation["Label"]

        rows.append(score_model(
            "LogReg", LogisticRegression(max_iter=500, random_state=SEED),
            xs_train, y_train, xs_val, y_val, labels, config))
        rows.append(score_model(
            "RandomForest",
            RandomForestClassifier(n_estimators=100, min_samples_leaf=5, n_jobs=-1, random_state=SEED),
            xp_train, y_train, xp_val, y_val, labels, config))
        rows.append(score_model(
            "XGBoost",
            XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                          tree_method="hist", n_jobs=-1, random_state=SEED),
            xp_train, y_train, xp_val, y_val, labels, config))

    print("\n=== Sensitivity table (validation segment, threshold 0.5) ===")
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == "__main__":
    main()