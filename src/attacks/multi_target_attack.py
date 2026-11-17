"""Random-search evasion against the three selected detectors (validation only).

Same attack code as random_search_attack.py (attack_chunk), applied to the
configurations selected by the pre-declared tuning rule: logistic regression
(C = 0.1), random forest (100 trees, min_samples_leaf 20) and XGBoost
(max_depth 3, 100 trees). Each detector is fitted on the train segment and
attacked on its own detected validation flows (at most 300 per family, seed
42), so the populations differ between detectors. The XGBoost rows must
reproduce the earlier results exactly. The test segment, Thursday and Friday
are never loaded.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from src.attacks.perturbation import perturb
from src.attacks.random_search_attack import (
    AMPLITUDES,
    CHUNK_FLOWS,
    DATA_DIR,
    MAX_FLOWS_PER_FAMILY,
    SEED,
    STRATEGY,
    THRESHOLD,
    attack_chunk,
    wilson,
)
from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    fit_preprocessor,
    prepare_working_frame,
    target_from_labels,
    transform_frame,
)
from src.data.temporal_split import assign_temporal_segments

# name -> (needs scaled inputs, constructor)
DETECTORS = {
    "LogReg": (
        True,
        lambda: LogisticRegression(C=0.1, max_iter=500, random_state=SEED),
    ),
    "RandomForest": (
        False,
        lambda: RandomForestClassifier(
            n_estimators=100, min_samples_leaf=20, n_jobs=-1, random_state=SEED
        ),
    ),
    "XGBoost": (
        False,
        lambda: XGBClassifier(
            max_depth=3,
            n_estimators=100,
            learning_rate=0.1,
            tree_method="hist",
            n_jobs=-1,
            random_state=SEED,
        ),
    ),
}


def main() -> None:
    clock = time.perf_counter()
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    validation = raw[segments == "validation"]
    del raw
    y_train = target_from_labels(train["Label"])
    y_val = target_from_labels(validation["Label"]).to_numpy()

    probe = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    columns = list(probe.feature_columns)
    train_features = prepare_working_frame(train, STRATEGY)[columns]
    lower, upper = train_features.min(), train_features.max()
    del train_features

    work = prepare_working_frame(validation, STRATEGY)
    features = work[columns].reset_index(drop=True)
    labels = work["Label"].to_numpy()

    rows = []
    for name, (scaled, make) in DETECTORS.items():
        # fit only on the train segment
        fitted = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=scaled)
        assert list(fitted.feature_columns) == columns
        model = make()
        model.fit(transform_frame(train, fitted), y_train)
        base = model.predict_proba(transform_frame(features, fitted))[:, 1]
        flagged = base >= THRESHOLD
        print(
            f"\n--- {name}: validation recall {flagged[y_val == 1].mean():.4f} | "
            f"false positives {int((flagged & (y_val == 0)).sum())}"
        )

        detected = (y_val == 1) & flagged
        rng = np.random.default_rng(SEED)
        selected: dict[str, np.ndarray] = {}
        totals: dict[str, tuple[int, int]] = {}
        for family in sorted(set(labels[y_val == 1])):
            in_family = labels == family
            totals[family] = (
                int((in_family & (y_val == 1)).sum()),
                int((in_family & detected).sum()),
            )
            pool = np.flatnonzero(in_family & detected)
            if len(pool) == 0:
                print(f"{family}: no detected flow, excluded")
                continue
            take = min(len(pool), MAX_FLOWS_PER_FAMILY)
            selected[family] = np.sort(rng.choice(pool, size=take, replace=False))
        sizes = {family: len(idx) for family, idx in selected.items()}
        print(f"attacked flows: {sum(sizes.values())} | per family: {sizes}")

        population = np.concatenate(list(selected.values()))
        identity = perturb(features.iloc[population].reset_index(drop=True), 1.0, 1.0)
        identity_scores = model.predict_proba(transform_frame(identity, fitted))[:, 1]
        diff = np.abs(identity_scores - base[population])
        flips = int(((identity_scores < THRESHOLD) & (base[population] >= THRESHOLD)).sum())
        print(
            f"identity control: max |score diff| = {diff.max():.3g} | "
            f"rows with diff > 1e-6: {int((diff > 1e-6).sum())} | flips below {THRESHOLD}: {flips}"
        )

        for family, idx in selected.items():
            family_features = features.iloc[idx].reset_index(drop=True)
            for amplitude in AMPLITUDES:
                parts = []
                for start in range(0, len(idx), CHUNK_FLOWS):
                    chunk = family_features.iloc[start : start + CHUNK_FLOWS]
                    parts.append(
                        attack_chunk(
                            chunk.reset_index(drop=True),
                            amplitude,
                            rng,
                            model,
                            fitted,
                            lower,
                            upper,
                        )
                    )
                result = pd.concat(parts, ignore_index=True)
                n, k = len(result), int(result["evaded"].sum())
                evaders = result[result["evaded"]]
                rows.append(
                    {
                        "model": name,
                        "family": family,
                        "A": amplitude,
                        "flows": n,
                        "evaded": k,
                        "evasion_rate": k / n,
                        "ci_high": wilson(k, n)[1],
                        "median_queries_evaders": evaders["queries"].median() if k else np.nan,
                        "median_base": float(np.median(base[idx])),
                        "median_min_score": float(np.nanmedian(result["min_score"])),
                        "recall_before": totals[family][1] / totals[family][0],
                    }
                )
            print(f"done: {name} {family} ({time.perf_counter() - clock:.0f}s)")

    summary = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    for column, title in (
        ("evasion_rate", "Evasion rate per model, family and amplitude"),
        ("median_min_score", "Median of the lowest score reached"),
    ):
        print(f"\n=== {title} ===")
        table = summary.pivot_table(index=["model", "family"], columns="A", values=column)
        print(table.round(4).to_string())
    print("\n=== Full summary ===")
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    main()