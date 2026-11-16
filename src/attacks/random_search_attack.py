"""Random-search evasion attack in feature space (validation only).

Target: the selected XGBoost (max_depth 3, n_estimators 100) fitted on the
train segment. Population: validation attack flows already detected at 0.5
(at most 300 per family, seed 42). The attacker controls two Fwd-side factors,
padding s and delay t, both in [1, 1 + A]; verified derived features are
recomputed, the others stay frozen. Candidates that break a verified rule
(train bounds, verified orderings, 1500-byte MTU, non-finite values) are never
queried. Each flow gets at most MAX_QUERIES queries. The test segment,
Thursday and Friday are never loaded.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from src.attacks.perturbation import perturb, rejection_reasons
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
THRESHOLD = 0.5
PARAMS = {"max_depth": 3, "n_estimators": 100}
AMPLITUDES = (0.1, 0.25, 0.5, 1.0, 2.0)
MAX_FLOWS_PER_FAMILY = 300
MAX_QUERIES = 1000
MAX_DRAWS = 2000
MTU = 1500
CHUNK_FLOWS = 20


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95 % Wilson interval for a proportion."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    denom = 1.0 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return float(centre - half), float(centre + half)


def attack_chunk(flows, amplitude, rng, model, fitted, lower, upper) -> pd.DataFrame:
    """Sequential random search simulated on MAX_DRAWS pre-drawn candidates per flow."""
    n = len(flows)
    repeated = flows.loc[flows.index.repeat(MAX_DRAWS)].reset_index(drop=True)
    size = n * MAX_DRAWS
    s = 1.0 + amplitude * rng.random(size)
    t = 1.0 + amplitude * rng.random(size)
    candidate = perturb(repeated, s, t)

    reasons = rejection_reasons(repeated, candidate, lower, upper)
    infeasible = reasons.any(axis=1).to_numpy() | (
        candidate["Fwd Packet Length Max"].to_numpy() > MTU
    )
    feasible = (~infeasible).reshape(n, MAX_DRAWS)
    rank = np.cumsum(feasible, axis=1)  # 1-based rank among feasible candidates
    queried = feasible & (rank <= MAX_QUERIES)
    flat = queried.reshape(-1)

    scores = np.full(size, np.nan)
    if flat.any():
        queried_frame = candidate[flat].reset_index(drop=True)
        scores[flat] = model.predict_proba(transform_frame(queried_frame, fitted))[:, 1]
    scores = scores.reshape(n, MAX_DRAWS)

    success = queried & (scores < THRESHOLD)
    evaded = success.any(axis=1)
    first = success.argmax(axis=1)
    used = np.where(evaded, rank[np.arange(n), first], queried.sum(axis=1))
    lowest = np.where(queried, scores, np.inf).min(axis=1)
    lowest = np.where(np.isinf(lowest), np.nan, lowest)
    return pd.DataFrame(
        {
            "evaded": evaded,
            "queries": used,
            "any_feasible": feasible.any(axis=1),
            "feasible_draw_share": feasible.mean(axis=1),
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

    rng = np.random.default_rng(SEED)
    detected = (y_val == 1) & (base >= THRESHOLD)
    totals: dict[str, dict[str, int]] = {}
    selected: dict[str, np.ndarray] = {}
    for family in sorted(set(labels[y_val == 1])):
        in_family = labels == family
        totals[family] = {
            "all": int((in_family & (y_val == 1)).sum()),
            "detected": int((in_family & detected).sum()),
        }
        pool = np.flatnonzero(in_family & detected)
        if len(pool) == 0:
            print(f"{family}: no detected flow, excluded")
            continue
        take = min(len(pool), MAX_FLOWS_PER_FAMILY)
        selected[family] = np.sort(rng.choice(pool, size=take, replace=False))
    population = np.concatenate(list(selected.values()))
    print(f"attacked flows: {len(population)} | per family: "
          f"{ {k: len(v) for k, v in selected.items()} }")

    identity = perturb(features.iloc[population].reset_index(drop=True), 1.0, 1.0)
    identity_scores = model.predict_proba(transform_frame(identity, fitted))[:, 1]
    diff = np.abs(identity_scores - base[population])
    flips = int(((identity_scores < THRESHOLD) & (base[population] >= THRESHOLD)).sum())
    print(f"identity control: max |score diff| = {diff.max():.3g} | "
          f"rows with diff > 1e-6: {int((diff > 1e-6).sum())} | flips below {THRESHOLD}: {flips}")

    frames = []
    for family, idx in selected.items():
        family_features = features.iloc[idx].reset_index(drop=True)
        for amplitude in AMPLITUDES:
            for start in range(0, len(idx), CHUNK_FLOWS):
                chunk = family_features.iloc[start : start + CHUNK_FLOWS].reset_index(drop=True)
                result = attack_chunk(chunk, amplitude, rng, model, fitted, lower, upper)
                result["family"], result["amplitude"] = family, amplitude
                result["base_score"] = base[idx][start : start + CHUNK_FLOWS]
                frames.append(result)
            print(f"done: {family} A={amplitude} ({time.perf_counter() - clock:.0f}s)")
    table = pd.concat(frames, ignore_index=True)

    rows = []
    for (family, amplitude), part in table.groupby(["family", "amplitude"]):
        n, k = len(part), int(part["evaded"].sum())
        low, high = wilson(k, n)
        evaders = part[part["evaded"]]
        total = totals[family]
        rows.append(
            {
                "family": family,
                "A": amplitude,
                "flows": n,
                "feasible_share": part["any_feasible"].mean(),
                "evasion_rate": k / n,
                "ci_low": low,
                "ci_high": high,
                "median_queries_evaders": evaders["queries"].median() if k else np.nan,
                "max_queries_evaders": evaders["queries"].max() if k else np.nan,
                "median_base_score": part["base_score"].median(),
                "median_min_score": part["min_score"].median(),
                "recall_before": total["detected"] / total["all"],
                "recall_after_est": total["detected"] * (1 - k / n) / total["all"],
            }
        )
    summary = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print("\n=== Evasion rate per family and amplitude (validation) ===")
    print(summary.pivot(index="family", columns="A", values="evasion_rate").round(4).to_string())
    print("\n=== Share of flows with at least one feasible candidate ===")
    print(summary.pivot(index="family", columns="A", values="feasible_share").round(4).to_string())
    print("\n=== Full summary ===")
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    main()