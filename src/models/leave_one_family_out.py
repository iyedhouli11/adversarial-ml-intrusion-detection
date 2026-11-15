"""Phase 4.5-b: leave-one-family-out on the per-stratum split.

Monday-Wednesday only. For each attack family, the family (and its
"- Attempted" variant) is removed from the train segment; preprocessing and
model are fitted without it. Evaluation: validation rows of that family
against validation BENIGN rows. The test segment, Thursday and Friday are
never used. Hyperparameters are the ones fixed in advance in earlier phases.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
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
FAMILIES = (
    "DoS Hulk",
    "DoS GoldenEye",
    "DoS Slowhttptest",
    "DoS Slowloris",
    "FTP-Patator",
    "SSH-Patator",
)


def main() -> None:
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw)
    train_all = raw[segments == "train"]
    validation = raw[segments == "validation"]
    del raw

    val_labels = validation["Label"].to_numpy()
    rows = []
    for family in FAMILIES:
        removed = {family, f"{family} - Attempted"}
        train = train_all[~train_all["Label"].isin(removed)]
        y_train = target_from_labels(train["Label"])

        mask = (val_labels == family) | (val_labels == "BENIGN")
        held_out = validation[mask]
        y_true = (held_out["Label"].to_numpy() == family).astype(int)
        print(
            f"\n--- held out: {family} | train rows={len(train)} | "
            f"validation family flows={int(y_true.sum())} | benign flows={int((1 - y_true).sum())}"
        )

        # fit only on the train segment without the held-out family
        scaled = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=True)
        plain = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
        xs_train, xs_val = transform_frame(train, scaled), transform_frame(held_out, scaled)
        xp_train, xp_val = transform_frame(train, plain), transform_frame(held_out, plain)

        models = (
            ("LogReg", LogisticRegression(max_iter=500, random_state=SEED), xs_train, xs_val),
            (
                "RandomForest",
                RandomForestClassifier(
                    n_estimators=100, min_samples_leaf=5, n_jobs=-1, random_state=SEED
                ),
                xp_train,
                xp_val,
            ),
            (
                "XGBoost",
                XGBClassifier(
                    n_estimators=200, max_depth=6, learning_rate=0.1,
                    tree_method="hist", n_jobs=-1, random_state=SEED,
                ),
                xp_train,
                xp_val,
            ),
        )
        for name, model, x_train, x_val in models:
            model.fit(x_train, y_train)
            scores = model.predict_proba(x_val)[:, 1]
            flagged = scores >= THRESHOLD
            rows.append(
                {
                    "held_out": family,
                    "model": name,
                    "family_flows": int(y_true.sum()),
                    "family_recall": float(flagged[y_true == 1].mean()),
                    "benign_flag_rate": float(flagged[y_true == 0].mean()),
                    "PR-AUC": average_precision_score(y_true, scores),
                    "random_ref": float(y_true.mean()),
                }
            )

    print("\n=== Leave-one-family-out (validation segment, threshold 0.5) ===")
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == "__main__":
    main()