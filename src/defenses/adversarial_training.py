"""Adversarial-training hardening, validation only (specification v1).

Follows docs/hardening_specification.md, committed before this script was
written. For each selected detector (logistic regression C = 0.1, random
forest 100 trees / min_samples_leaf 20, XGBoost depth 3 / 100 trees) the
script builds one feasible padded-and-delayed copy of every effective attack
flow of the TRAIN segment, retrains the detector from scratch on train plus
copies, and evaluates four states on the validation segment: original and
hardened, each clean and under attack. Evaluation attacks: random search with
a new seed (1234) at the amplitudes of the earlier attack, and the 31 x 31
grid over [1, 3] x [1, 3]. The test segment, Thursday and Friday are never
loaded.

Details not fixed by the specification: the draws used to build the training
copies use seed 42 and are processed in chunks of 5000 flows.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.attacks.grid_check import grid_search
from src.attacks.multi_target_attack import DETECTORS
from src.attacks.perturbation import perturb, rejection_reasons
from src.attacks.random_search_attack import (
    AMPLITUDES,
    CHUNK_FLOWS,
    DATA_DIR,
    MAX_FLOWS_PER_FAMILY,
    MTU,
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

ATTACK_SEED = 1234
TRAIN_AMPLITUDE = 1.0
TRAIN_DRAWS = 20
TRAIN_CHUNK = 5000
GRID_AMPLITUDE = 2.0
GRID_POINTS = 31
STATES = ("original", "hardened")


def stack(top, bottom):
    """Vertically stack two feature matrices, dense or sparse."""
    if sparse.issparse(top) or sparse.issparse(bottom):
        return sparse.vstack([top, bottom]).tocsr()
    return np.vstack([top, bottom])


def adversarial_examples(flows, lower, upper, rng):
    """One feasible padded-and-delayed copy per flow: first feasible of TRAIN_DRAWS draws."""
    kept = []
    skipped = 0
    for start in range(0, len(flows), TRAIN_CHUNK):
        chunk = flows.iloc[start : start + TRAIN_CHUNK].reset_index(drop=True)
        n = len(chunk)
        repeated = chunk.loc[chunk.index.repeat(TRAIN_DRAWS)].reset_index(drop=True)
        size = n * TRAIN_DRAWS
        s = 1.0 + TRAIN_AMPLITUDE * rng.random(size)
        t = 1.0 + TRAIN_AMPLITUDE * rng.random(size)
        candidate = perturb(repeated, s, t)
        reasons = rejection_reasons(repeated, candidate, lower, upper)
        infeasible = reasons.any(axis=1).to_numpy() | (
            candidate["Fwd Packet Length Max"].to_numpy() > MTU
        )
        feasible = (~infeasible).reshape(n, TRAIN_DRAWS)
        has_candidate = feasible.any(axis=1)
        first = feasible.argmax(axis=1)
        rows = np.arange(n)[has_candidate] * TRAIN_DRAWS + first[has_candidate]
        kept.append(candidate.iloc[rows])
        skipped += int((~has_candidate).sum())
    return pd.concat(kept, ignore_index=True), skipped


def clean_metrics(scores, y_val):
    flagged = (scores >= THRESHOLD).astype(int)
    _, fp, fn, _ = confusion_matrix(y_val, flagged).ravel()
    return {
        "precision": precision_score(y_val, flagged, zero_division=0),
        "recall": recall_score(y_val, flagged, zero_division=0),
        "F1": f1_score(y_val, flagged, zero_division=0),
        "PR-AUC": average_precision_score(y_val, scores),
        "FP": int(fp),
        "FN": int(fn),
    }


def evasion_population(labels, y_val, base):
    """Detected attack flows, at most MAX_FLOWS_PER_FAMILY per family, seed 42."""
    rng = np.random.default_rng(SEED)
    detected = (y_val == 1) & (base >= THRESHOLD)
    selected = {}
    for family in sorted(set(labels[y_val == 1])):
        pool = np.flatnonzero((labels == family) & detected)
        if len(pool) == 0:
            continue
        take = min(len(pool), MAX_FLOWS_PER_FAMILY)
        selected[family] = np.sort(rng.choice(pool, size=take, replace=False))
    return selected


def common_population(labels, y_val):
    """Same flows for every model: all effective attacks, at most 300 per family, seed 42."""
    rng = np.random.default_rng(SEED)
    selected = {}
    for family in sorted(set(labels[y_val == 1])):
        pool = np.flatnonzero((labels == family) & (y_val == 1))
        take = min(len(pool), MAX_FLOWS_PER_FAMILY)
        selected[family] = np.sort(rng.choice(pool, size=take, replace=False))
    return selected


def attack_random(model, fitted, features, selected, lower, upper, rng):
    rows = []
    for family, idx in selected.items():
        family_features = features.iloc[idx].reset_index(drop=True)
        for amplitude in AMPLITUDES:
            parts = [
                attack_chunk(
                    family_features.iloc[start : start + CHUNK_FLOWS].reset_index(drop=True),
                    amplitude,
                    rng,
                    model,
                    fitted,
                    lower,
                    upper,
                )
                for start in range(0, len(idx), CHUNK_FLOWS)
            ]
            result = pd.concat(parts, ignore_index=True)
            rows.append(
                {
                    "family": family,
                    "attack": f"random A={amplitude}",
                    "attacked": len(result),
                    "evaded": int(result["evaded"].sum()),
                }
            )
    return rows


def attack_grid(model, fitted, features, selected, lower, upper):
    axis = 1.0 + GRID_AMPLITUDE * np.linspace(0.0, 1.0, GRID_POINTS)
    s_grid, t_grid = np.meshgrid(axis, axis, indexing="ij")
    rows = []
    for family, idx in selected.items():
        family_features = features.iloc[idx].reset_index(drop=True)
        parts = [
            grid_search(
                family_features.iloc[start : start + CHUNK_FLOWS].reset_index(drop=True),
                s_grid.ravel(),
                t_grid.ravel(),
                model,
                fitted,
                lower,
                upper,
            )
            for start in range(0, len(idx), CHUNK_FLOWS)
        ]
        result = pd.concat(parts, ignore_index=True)
        rows.append(
            {
                "family": family,
                "attack": f"grid A={GRID_AMPLITUDE}",
                "attacked": len(result),
                "evaded": int(result["evaded"].sum()),
            }
        )
    return rows


def common_recall_rows(name, state, common, attackable, attack_rows, attack_names):
    """Recall on the common population: a missed or evaded flow counts as missed."""
    evaded = {(row["family"], row["attack"]): row["evaded"] for row in attack_rows}
    rows = []
    for family, idx in common.items():
        detected = len(attackable.get(family, []))
        for attack in ("none", *attack_names):
            lost = evaded.get((family, attack), 0)
            rows.append(
                {
                    "detector": name,
                    "state": state,
                    "family": family,
                    "attack": attack,
                    "n_common": len(idx),
                    "kept": detected - lost,
                }
            )
    return rows


def evasion_comparison(rows):
    frame = pd.DataFrame(rows)
    frame["rate"] = frame["evaded"] / frame["attacked"]
    bounds = [
        wilson(int(k), int(n))
        for k, n in zip(frame["evaded"], frame["attacked"], strict=True)
    ]
    frame["ci_low"] = [low for low, _ in bounds]
    frame["ci_high"] = [high for _, high in bounds]
    keys = ["detector", "family", "attack"]
    columns = ["attacked", "evaded", "rate", "ci_low", "ci_high"]
    original = frame[frame["state"] == "original"].set_index(keys)[columns]
    hardened = frame[frame["state"] == "hardened"].set_index(keys)[columns]
    comparison = original.add_suffix("_o").join(hardened.add_suffix("_h"), how="outer")

    def verdict(row) -> str:
        if pd.isna(row["ci_high_o"]) or pd.isna(row["ci_high_h"]):
            return "missing in one state"
        if row["ci_high_h"] < row["ci_low_o"]:
            return "improved"
        if row["ci_low_h"] > row["ci_high_o"]:
            return "worse"
        return "not separated"

    comparison["verdict"] = comparison.apply(verdict, axis=1)
    return comparison.sort_index()


def main() -> None:
    clock = time.perf_counter()
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    validation = raw[segments == "validation"]
    del raw

    # preprocessing fitted on the original train segment only
    plain = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=False)
    scaled = fit_preprocessor(train, header_strategy=STRATEGY, scale_numeric=True)
    columns = list(plain.feature_columns)
    assert list(scaled.feature_columns) == columns

    train_features = prepare_working_frame(train, STRATEGY)[columns].reset_index(drop=True)
    y_train = target_from_labels(train["Label"]).to_numpy()
    lower, upper = train_features.min(), train_features.max()

    attack_flows = train_features[y_train == 1].reset_index(drop=True)
    adversarial, skipped = adversarial_examples(
        attack_flows, lower, upper, np.random.default_rng(SEED)
    )
    y_aug = np.concatenate([y_train, np.ones(len(adversarial), dtype=y_train.dtype)])
    print(f"train rows: {len(y_train)} | attack flows in train: {len(attack_flows)}")
    print(
        f"adversarial copies built: {len(adversarial)} | flows without a feasible "
        f"candidate: {skipped} ({skipped / len(attack_flows):.4f})"
    )
    print(f"attack share in training: before {y_train.mean():.4f} | after {y_aug.mean():.4f}")
    del train_features, attack_flows

    validation_work = prepare_working_frame(validation, STRATEGY)
    features = validation_work[columns].reset_index(drop=True)
    labels = validation_work["Label"].to_numpy()
    y_val = target_from_labels(validation["Label"]).to_numpy()
    common = common_population(labels, y_val)

    matrices = {
        key: (
            transform_frame(train, fitted),
            transform_frame(adversarial, fitted),
            transform_frame(features, fitted),
        )
        for key, fitted in (("scaled", scaled), ("plain", plain))
    }

    attack_names = [*[f"random A={a}" for a in AMPLITUDES], f"grid A={GRID_AMPLITUDE}"]
    clean_rows, evasion_rows, recall_rows = [], [], []

    for name, (needs_scaling, make) in DETECTORS.items():
        fitted = scaled if needs_scaling else plain
        x_train, x_adv, x_val = matrices["scaled" if needs_scaling else "plain"]
        for state in STATES:
            model = make()
            started = time.perf_counter()
            if state == "original":
                model.fit(x_train, y_train)
            else:
                model.fit(stack(x_train, x_adv), y_aug)
            fit_seconds = time.perf_counter() - started
            base = model.predict_proba(x_val)[:, 1]
            clean_rows.append(
                {
                    "detector": name,
                    "state": state,
                    "fit_s": round(fit_seconds, 1),
                    **clean_metrics(base, y_val),
                }
            )

            selected = evasion_population(labels, y_val, base)
            population = np.concatenate(list(selected.values()))
            identity = perturb(features.iloc[population].reset_index(drop=True), 1.0, 1.0)
            identity_scores = model.predict_proba(transform_frame(identity, fitted))[:, 1]
            gap = np.abs(identity_scores - base[population])
            flips = int(
                ((identity_scores < THRESHOLD) & (base[population] >= THRESHOLD)).sum()
            )
            print(
                f"\n[{name} {state}] attacked flows {len(population)} | identity control: "
                f"max |score diff| {gap.max():.3g}, flips below {THRESHOLD}: {flips}"
            )

            attackable = {}
            for family, idx in common.items():
                kept_idx = idx[base[idx] >= THRESHOLD]
                if len(kept_idx):
                    attackable[family] = kept_idx

            for population_name, attacked in (("evasion", selected), ("common", attackable)):
                rows = attack_random(
                    model, fitted, features, attacked, lower, upper,
                    np.random.default_rng(ATTACK_SEED),
                )
                rows += attack_grid(model, fitted, features, attacked, lower, upper)
                if population_name == "evasion":
                    for row in rows:
                        row.update(detector=name, state=state)
                    evasion_rows.extend(rows)
                else:
                    recall_rows.extend(
                        common_recall_rows(name, state, common, attackable, rows, attack_names)
                    )
            print(f"done: {name} {state} ({time.perf_counter() - clock:.0f}s)")

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_rows", 500)

    print("\n=== Clean performance on validation (threshold 0.5; fit_s is noisy) ===")
    print(pd.DataFrame(clean_rows).round(6).to_string(index=False))

    comparison = evasion_comparison(evasion_rows)
    informative = comparison[
        (comparison["evaded_o"].fillna(0) > 0) | (comparison["evaded_h"].fillna(0) > 0)
    ]
    print("\n=== Evasion rate, original (_o) vs hardened (_h), combinations with any evasion ===")
    print(informative.round(4).to_string())
    print("\nVerdicts on those combinations (Wilson 95 % intervals separated or not):")
    print(informative["verdict"].value_counts().to_string())
    print(
        f"combinations with no evasion in either state: "
        f"{len(comparison) - len(informative)} of {len(comparison)}"
    )

    recall = pd.DataFrame(recall_rows)
    recall["recall"] = recall["kept"] / recall["n_common"]
    print("\n=== Recall on the common population per family (none = clean) ===")
    table = recall.pivot_table(
        index=["detector", "family", "state"], columns="attack", values="recall"
    )
    print(table.round(4).to_string())
    pooled = recall.groupby(["detector", "state", "attack"])[["kept", "n_common"]].sum()
    pooled["recall"] = pooled["kept"] / pooled["n_common"]
    print("\n=== Recall on the common population, pooled over families ===")
    print(pooled["recall"].unstack("attack").round(4).to_string())


if __name__ == "__main__":
    main()