"""Phase 4.5-c: hyperparameter tuning on the validation segment.

Monday-Wednesday only. Every model is fitted on the train segment of the
per-stratum split (gap 1 %) and scored on the validation segment. The test
segment, Thursday and Friday are never loaded.

The grid and the selection rule are declared here before any run:
best PR-AUC; configurations within TOLERANCE of the best are treated as tied
and the simplest one is kept.
"""

from __future__ import annotations

import itertools
import time
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score
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
TOLERANCE = 0.001

GRID: dict[str, dict[str, list]] = {
    "LogReg": {"C": [0.01, 0.1, 1.0, 10.0]},
    "RandomForest": {"n_estimators": [100, 300], "min_samples_leaf": [1, 5, 20]},
    "XGBoost": {"max_depth": [3, 6, 9], "n_estimators": [100, 200]},
}


def make_model(name: str, params: dict):
    if name == "LogReg":
        return LogisticRegression(max_iter=500, random_state=SEED, **params)
    if name == "RandomForest":
        return RandomForestClassifier(n_jobs=-1, random_state=SEED, **params)
    if name == "XGBoost":
        return XGBClassifier(
            learning_rate=0.1,
            tree_method="hist",
            n_jobs=-1,
            random_state=SEED,
            **params,
        )
    raise ValueError(f"Unknown model {name}")


def complexity(name: str, params: dict) -> tuple:
    """Smaller tuple = simpler model; used only to break ties."""
    if name == "LogReg":
        return (params["C"],)
    if name == "RandomForest":
        return (params["n_estimators"], -params["min_samples_leaf"])
    return (params["max_depth"], params["n_estimators"])


def expand(grid: dict[str, list]) -> list[dict]:
    keys = list(grid)
    return [dict(zip(keys, values)) for values in itertools.product(*grid.values())]


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    validation = raw[segments == "validation"]
    del raw
    y_train = target_from_labels(train["Label"])
    y_val = target_from_labels(validation["Label"])
    print(f"train={len(train)} | validation={len(validation)}")

    # fit only on the train segment
    scaled = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=True)
    plain = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    data = {
        True: (transform_frame(train, scaled), transform_frame(validation, scaled)),
        False: (transform_frame(train, plain), transform_frame(validation, plain)),
    }

    rows = []
    for name, grid in GRID.items():
        for params in expand(grid):
            x_train, x_val = data[name == "LogReg"]
            model = make_model(name, params)
            start = time.perf_counter()
            model.fit(x_train, y_train)
            seconds = time.perf_counter() - start
            scores = model.predict_proba(x_val)[:, 1]
            flagged = (scores >= THRESHOLD).astype(int)
            _, fp, fn, _ = confusion_matrix(y_val, flagged).ravel()
            rows.append(
                {
                    "model": name,
                    "params": str(params),
                    "PR-AUC": average_precision_score(y_val, scores),
                    "F1": f1_score(y_val, flagged),
                    "FP": fp,
                    "FN": fn,
                    "fit_s": round(seconds, 1),
                    "_params": params,
                }
            )
            print(f"done: {name} {params} -> PR-AUC {rows[-1]['PR-AUC']:.6f}")
            del model

    table = pd.DataFrame(rows)
    shown = table.drop(columns="_params")
    print("\n=== All configurations (validation segment, threshold 0.5) ===")
    print(shown.round(6).to_string(index=False))

    print(f"\n=== Selection rule: best PR-AUC, ties within {TOLERANCE} -> simplest ===")
    for name in GRID:
        part = [row for row in rows if row["model"] == name]
        best = max(row["PR-AUC"] for row in part)
        tied = [row for row in part if row["PR-AUC"] >= best - TOLERANCE]
        chosen = min(tied, key=lambda row: complexity(name, row["_params"]))
        print(
            f"{name}: best PR-AUC={best:.6f} | tied configs={len(tied)} | "
            f"selected={chosen['params']} (PR-AUC {chosen['PR-AUC']:.6f}, "
            f"FP {chosen['FP']}, FN {chosen['FN']})"
        )


if __name__ == "__main__":
    main()