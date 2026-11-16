"""Share of the selected detector's gain reachable by the perturbation (train only).

Fits the selected XGBoost on the train segment and splits its gain importance
between columns the perturbation changes or recomputes and columns it freezes.
Also measures how many flows sit near the maximum duration seen in train.
Validation, test, Thursday and Friday are never loaded.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from xgboost import XGBClassifier

from src.attacks.perturbation import CHANGED_COLUMNS
from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    fit_preprocessor,
    prepare_working_frame,
    target_from_labels,
    transform_frame,
)
from src.data.temporal_split import assign_temporal_segments

DATA_DIR = Path("data/raw/CICIDS2017_improved")
SEED = 42
STRATEGY = "exclude"
PARAMS = {"max_depth": 3, "n_estimators": 100}


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    del raw
    y_train = target_from_labels(train["Label"])

    # fit only on the train segment
    fitted = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    x_train = transform_frame(train, fitted)
    model = XGBClassifier(
        learning_rate=0.1,
        tree_method="hist",
        n_jobs=-1,
        random_state=SEED,
        importance_type="gain",
        **PARAMS,
    )
    model.fit(x_train, y_train)

    names = fitted.transformer.get_feature_names_out()
    importance = pd.Series(model.feature_importances_, index=names)
    reachable = importance.index.isin(list(CHANGED_COLUMNS))

    pd.set_option("display.width", 220)
    print(f"total gain: {importance.sum():.4f}")
    print(f"gain on columns changed or recomputed: {importance[reachable].sum():.4f}")
    print(f"gain on frozen columns:                {importance[~reachable].sum():.4f}")
    print("\n=== Top 10 changed or recomputed columns ===")
    print(importance[reachable].sort_values(ascending=False).head(10).round(4).to_string())
    print("\n=== Top 10 frozen columns ===")
    print(importance[~reachable].sort_values(ascending=False).head(10).round(4).to_string())

    working = prepare_working_frame(train, STRATEGY)
    labels = working["Label"]
    effective = target_from_labels(labels).to_numpy() == 1
    cap_duration = working["Flow Duration"].max()
    cap_fwd = working["Fwd IAT Total"].max()
    print(f"\nmax Flow Duration (train): {cap_duration:.6g} | max Fwd IAT Total: {cap_fwd:.6g}")

    frame = pd.DataFrame(
        {
            "label": labels.to_numpy(),
            "duration_gt_80pct_max": (working["Flow Duration"] > 0.8 * cap_duration).to_numpy(),
            "duration_ge_99pct_max": (working["Flow Duration"] >= 0.99 * cap_duration).to_numpy(),
            "fwd_iat_gt_80pct_max": (working["Fwd IAT Total"] > 0.8 * cap_fwd).to_numpy(),
        }
    )[effective]
    print("\n=== Share of attack flows near the maximum duration, per family ===")
    print(frame.groupby("label").mean().round(4).to_string())


if __name__ == "__main__":
    main()