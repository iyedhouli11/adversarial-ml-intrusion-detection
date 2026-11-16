"""Grid check of the evasion search (validation only).

Same target and same attacked population (seed 42) as the random-search
attack. Instead of random draws, evaluates a deterministic 31 x 31 grid over
[1, 3] x [1, 3] (A = 2, the largest amplitude, which contains the smaller
ones), plus a padding-only axis and a delay-only axis. At most 961 queries per
flow, within the 1000-query budget. No tuning. The test segment, Thursday and
Friday are never loaded.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from src.attacks.perturbation import perturb, rejection_reasons
from src.attacks.random_search_attack import (
    CHUNK_FLOWS,
    DATA_DIR,
    MAX_FLOWS_PER_FAMILY,
    MTU,
    PARAMS,
    SEED,
    STRATEGY,
    THRESHOLD,
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

AMPLITUDE = 2.0
GRID_POINTS = 31


def grid_search(
    flows: pd.DataFrame,
    s_values: np.ndarray,
    t_values: np.ndarray,
    model: XGBClassifier,
    fitted,
    lower: pd.Series,
    upper: pd.Series,
) -> pd.DataFrame:
    """Query every feasible grid point of every flow once."""
    n, g = len(flows), len(s_values)
    repeated = flows.loc[flows.index.repeat(g)].reset_index(drop=True)
    candidate = perturb(repeated, np.tile(s_values, n), np.tile(t_values, n))
    reasons = rejection_reasons(repeated, candidate, lower, upper)
    infeasible = reasons.any(axis=1).to_numpy() | (
        candidate["Fwd Packet Length Max"].to_numpy() > MTU
    )
    feasible = ~infeasible
    scores = np.full(n * g, np.nan)
    if feasible.any():
        queried = candidate[feasible].reset_index(drop=True)
        scores[feasible] = model.predict_proba(transform_frame(queried, fitted))[:, 1]
    scores = scores.reshape(n, g)
    feasible = feasible.reshape(n, g)
    lowest = np.where(feasible, scores, np.inf).min(axis=1)
    lowest = np.where(np.isinf(lowest), np.nan, lowest)
    return pd.DataFrame(
        {
            "evaded": (scores < THRESHOLD).any(axis=1),
            "feasible_share": feasible.mean(axis=1),
            "min_score": lowest,
        }
    )


def main() -> None:
    clock = time.perf_counter()
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    validation = raw[segments == "validation"]
    del raw

    # fit only on the train segment
    fitted = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    model = XGBClassifier(
        learning_rate=0.1, tree_method="hist", n_jobs=-1, random_state=SEED, **PARAMS
    )
    model.fit(transform_frame(train, fitted), target_from_labels(train["Label"]))
    columns = list(fitted.feature_columns)
    train_features = prepare_working_frame(train, STRATEGY)[columns]
    lower, upper = train_features.min(), train_features.max()
    del train_features, train

    validation_work = prepare_working_frame(validation, STRATEGY)
    features = validation_work[columns].reset_index(drop=True)
    labels = validation_work["Label"].to_numpy()
    y_val = target_from_labels(validation["Label"]).to_numpy()
    base = model.predict_proba(transform_frame(features, fitted))[:, 1]

    # same population as the random-search attack: same seed, same call order
    rng = np.random.default_rng(SEED)
    detected = (y_val == 1) & (base >= THRESHOLD)
    selected: dict[str, np.ndarray] = {}
    for family in sorted(set(labels[y_val == 1])):
        pool = np.flatnonzero((labels == family) & detected)
        if len(pool) == 0:
            continue
        take = min(len(pool), MAX_FLOWS_PER_FAMILY)
        selected[family] = np.sort(rng.choice(pool, size=take, replace=False))
    sizes = {family: len(idx) for family, idx in selected.items()}
    print(f"attacked flows: {sum(sizes.values())} | per family: {sizes}")

    axis = 1.0 + AMPLITUDE * np.linspace(0.0, 1.0, GRID_POINTS)
    s_grid, t_grid = np.meshgrid(axis, axis, indexing="ij")
    ones = np.ones(GRID_POINTS)
    modes = {
        "both": (s_grid.ravel(), t_grid.ravel()),
        "padding_only": (axis, ones),
        "delay_only": (ones, axis),
    }

    rows = []
    for mode, (s_values, t_values) in modes.items():
        for family, idx in selected.items():
            flows = features.iloc[idx].reset_index(drop=True)
            parts = [
                grid_search(
                    flows.iloc[start : start + CHUNK_FLOWS].reset_index(drop=True),
                    s_values,
                    t_values,
                    model,
                    fitted,
                    lower,
                    upper,
                )
                for start in range(0, len(idx), CHUNK_FLOWS)
            ]
            result = pd.concat(parts, ignore_index=True)
            n, k = len(result), int(result["evaded"].sum())
            rows.append(
                {
                    "mode": mode,
                    "family": family,
                    "flows": n,
                    "grid_points": len(s_values),
                    "feasible_grid_share": result["feasible_share"].mean(),
                    "evaded": k,
                    "evasion_rate": k / n,
                    "ci_high": wilson(k, n)[1],
                    "median_base": float(np.median(base[idx])),
                    "median_min_score": float(np.nanmedian(result["min_score"])),
                    "median_drop": float(
                        np.nanmedian(base[idx] - result["min_score"].to_numpy())
                    ),
                }
            )
            print(f"done: {mode} {family} ({time.perf_counter() - clock:.0f}s)")

    summary = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    for column, title in (
        ("evasion_rate", "Evasion rate"),
        ("feasible_grid_share", "Share of grid points that are feasible"),
        ("median_min_score", "Median of the lowest score reached"),
        ("median_drop", "Median score drop (initial score minus lowest score)"),
    ):
        print(f"\n=== {title} ===")
        print(summary.pivot(index="family", columns="mode", values=column).round(4).to_string())
    print("\n=== Full summary ===")
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    main()