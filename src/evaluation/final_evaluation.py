"""Final evaluation, run once per segment (docs/final_evaluation_specification.md).

Follows the specification committed before this script was written (6e1241f).
Six frozen models (logistic regression, random forest, XGBoost; original and
hardened) are rebuilt on the train segment with the same seeds as the
hardening run. Their clean FP / FN on validation are first compared with the
values already measured; on a mismatch the script stops before any score is
computed on the evaluated segment. Then, on that segment only: clean metrics,
the same random-search and grid attacks as on validation, recall on a common
population per amplitude, and the perturbed-BENIGN control. Aggregates only
are written to results/final/. Each segment is evaluated once: the script
refuses to overwrite existing results.

Usage (from the project root):
    python -m src.evaluation.final_evaluation --segment test
    python -m src.evaluation.final_evaluation --segment friday
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, precision_recall_curve

from src.attacks.multi_target_attack import DETECTORS
from src.attacks.perturbation import perturb, rejection_reasons
from src.attacks.random_search_attack import (
    AMPLITUDES,
    CHUNK_FLOWS,
    DATA_DIR,
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
from src.defenses.adversarial_training import (
    ATTACK_SEED,
    GRID_AMPLITUDE,
    STATES,
    adversarial_examples,
    attack_grid,
    clean_metrics,
    common_population,
    common_recall_rows,
    evasion_comparison,
    evasion_population,
    stack,
)
from src.defenses.benign_perturbation_check import AMPLITUDES as BENIGN_AMPLITUDES
from src.defenses.benign_perturbation_check import BENIGN_SAMPLE, PERTURB_SEED

OUT_DIR = Path("results/final")
PR_POINTS = 400
# clean FP / FN on validation already measured (docs/hardening_report.md)
EXPECTED_VALIDATION = {
    ("LogReg", "original"): (509, 274),
    ("LogReg", "hardened"): (444, 227),
    ("RandomForest", "original"): (11, 40),
    ("RandomForest", "hardened"): (12, 26),
    ("XGBoost", "original"): (7, 36),
    ("XGBoost", "hardened"): (5, 10),
}


def attack_random_detailed(model, fitted, features, selected, lower, upper, rng):
    """Same search and same draw order as the hardening run, plus query counts."""
    rows = []
    for family, idx in selected.items():
        family_features = features.iloc[idx].reset_index(drop=True)
        for amplitude in AMPLITUDES:
            result = pd.concat(
                [
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
                ],
                ignore_index=True,
            )
            evaders = result[result["evaded"]]
            rows.append(
                {
                    "family": family,
                    "attack": f"random A={amplitude}",
                    "attacked": len(result),
                    "evaded": int(result["evaded"].sum()),
                    "median_queries_evaders": (
                        float(evaders["queries"].median()) if len(evaders) else np.nan
                    ),
                    "max_queries_evaders": (
                        float(evaders["queries"].max()) if len(evaders) else np.nan
                    ),
                }
            )
    return rows


def amplitude_of(attack: str) -> float:
    if attack == "none":
        return 0.0
    return float(attack.split("=")[1])


def perturbed_benign(features, labels, lower, upper):
    benign_idx = np.flatnonzero(labels == "BENIGN")
    size = min(BENIGN_SAMPLE, len(benign_idx))
    sample = np.sort(
        np.random.default_rng(PERTURB_SEED).choice(benign_idx, size=size, replace=False)
    )
    benign = features.iloc[sample].reset_index(drop=True)
    perturbed = {}
    for amplitude in BENIGN_AMPLITUDES:
        draw = np.random.default_rng(PERTURB_SEED + round(amplitude * 100))
        s = 1.0 + amplitude * draw.random(len(benign))
        t = 1.0 + amplitude * draw.random(len(benign))
        candidate = perturb(benign, s, t)
        reasons = rejection_reasons(benign, candidate, lower, upper)
        infeasible = reasons.any(axis=1).to_numpy() | (
            candidate["Fwd Packet Length Max"].to_numpy() > MTU
        )
        feasible = ~infeasible
        perturbed[amplitude] = (feasible, candidate[feasible].reset_index(drop=True))
    return sample, perturbed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segment", choices=("test", "friday"), required=True)
    args = parser.parse_args()
    segment = args.segment
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    marker = OUT_DIR / f"{segment}_clean.csv"
    if marker.exists():
        raise SystemExit(f"{marker} exists: this segment was already evaluated (one run only).")

    clock = time.perf_counter()
    raw = load_split(DATA_DIR, "train")
    assert set(raw["source_day"]) == {"monday", "tuesday", "wednesday"}
    segments = assign_temporal_segments(raw, gap_fraction=0.01)
    train = raw[segments == "train"]
    validation = raw[segments == "validation"]
    held_out = raw[segments == "test"].copy() if segment == "test" else None
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
    print(f"adversarial copies rebuilt: {len(adversarial)} | without candidate: {skipped}")
    del train_features, attack_flows

    val_features = prepare_working_frame(validation, STRATEGY)[columns].reset_index(drop=True)
    y_val = target_from_labels(validation["Label"]).to_numpy()
    fitted_by_flag = {True: scaled, False: plain}
    matrices = {
        flag: (transform_frame(train, fitted), transform_frame(adversarial, fitted))
        for flag, fitted in fitted_by_flag.items()
    }

    # 1. rebuild the six models and check them on validation, before the segment is read
    models, check_rows = {}, []
    for name, (needs_scaling, make) in DETECTORS.items():
        fitted = fitted_by_flag[needs_scaling]
        x_train, x_adv = matrices[needs_scaling]
        x_val = transform_frame(val_features, fitted)
        for state in STATES:
            model = make()
            started = time.perf_counter()
            if state == "original":
                model.fit(x_train, y_train)
            else:
                model.fit(stack(x_train, x_adv), y_aug)
            fit_seconds = time.perf_counter() - started
            metrics = clean_metrics(model.predict_proba(x_val)[:, 1], y_val)
            expected = EXPECTED_VALIDATION.get((name, state))
            observed = (metrics["FP"], metrics["FN"])
            check_rows.append(
                {
                    "detector": name,
                    "state": state,
                    "FP": observed[0],
                    "FN": observed[1],
                    "expected": str(expected),
                    "match": observed == expected,
                    "fit_s": round(fit_seconds, 1),
                }
            )
            models[(name, state)] = (model, fitted)
            print(f"rebuilt: {name} {state} ({time.perf_counter() - clock:.0f}s)")
    del matrices, train, adversarial, val_features, validation

    check = pd.DataFrame(check_rows)
    print("\n=== Validation check (FP / FN must match the earlier run) ===")
    print(check.to_string(index=False))
    check.to_csv(OUT_DIR / f"{segment}_validation_check.csv", index=False)
    if not check["match"].all():
        raise SystemExit("Validation mismatch: stopped before reading the evaluated segment.")

    # 2. the evaluated segment, read once
    if segment == "friday":
        held_out = load_split(DATA_DIR, "test")
        assert set(held_out["source_day"]) == {"friday"}, set(held_out["source_day"])
    work = prepare_working_frame(held_out, STRATEGY)
    features = work[columns].reset_index(drop=True)
    labels = work["Label"].to_numpy()
    y = target_from_labels(held_out["Label"]).to_numpy()
    assert len(labels) == len(y) == len(features)
    del work, held_out
    print(f"\n{segment}: rows {len(y)} | attacks {int(y.sum())} | attack share {y.mean():.4f}")

    common = common_population(labels, y)
    sample, perturbed = perturbed_benign(features, labels, lower, upper)
    families = sorted(set(labels[y == 1]))
    attack_names = [*[f"random A={a}" for a in AMPLITUDES], f"grid A={GRID_AMPLITUDE}"]

    clean_rows, class_rows, family_rows, pr_rows = [], [], [], []
    evasion_rows, recall_rows, benign_rows = [], [], []
    for (name, state), (model, fitted) in models.items():
        started = time.perf_counter()
        base = model.predict_proba(transform_frame(features, fitted))[:, 1]
        inference_seconds = time.perf_counter() - started
        flagged = base >= THRESHOLD
        metrics = clean_metrics(base, y)
        tp = int((flagged & (y == 1)).sum())
        tn = int((~flagged & (y == 0)).sum())
        clean_rows.append(
            {
                "detector": name,
                "state": state,
                **metrics,
                "TP": tp,
                "TN": tn,
                "inference_s": round(inference_seconds, 2),
            }
        )
        report = classification_report(
            y, flagged.astype(int), output_dict=True, zero_division=0
        )
        for cls in ("0", "1"):
            class_rows.append({"detector": name, "state": state, "class": cls, **report[cls]})
        for family in families:
            mask = (labels == family) & (y == 1)
            family_rows.append(
                {
                    "detector": name,
                    "state": state,
                    "family": family,
                    "n": int(mask.sum()),
                    "recall": float(flagged[mask].mean()),
                }
            )
        precision, recall, _ = precision_recall_curve(y, base)
        keep = np.unique(np.linspace(0, len(precision) - 1, PR_POINTS).astype(int))
        pr_rows.extend(
            {"detector": name, "state": state, "precision": p, "recall": r}
            for p, r in zip(precision[keep], recall[keep], strict=True)
        )

        selected = evasion_population(labels, y, base)
        population = np.concatenate(list(selected.values()))
        identity = perturb(features.iloc[population].reset_index(drop=True), 1.0, 1.0)
        identity_scores = model.predict_proba(transform_frame(identity, fitted))[:, 1]
        gap = np.abs(identity_scores - base[population])
        print(
            f"[{name} {state}] attacked {len(population)} | identity max |diff| {gap.max():.3g}"
        )

        attackable = {}
        for family, idx in common.items():
            kept_idx = idx[base[idx] >= THRESHOLD]
            if len(kept_idx):
                attackable[family] = kept_idx

        for population_name, attacked in (("evasion", selected), ("common", attackable)):
            rows = attack_random_detailed(
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

        before_all = flagged[sample]
        for amplitude, (feasible, candidate) in perturbed.items():
            after = model.predict_proba(transform_frame(candidate, fitted))[:, 1] >= THRESHOLD
            before = before_all[feasible]
            benign_rows.append(
                {
                    "detector": name,
                    "state": state,
                    "A": amplitude,
                    "feasible_share": float(feasible.mean()),
                    "flagged_before": float(before.mean()),
                    "flagged_after": float(after.mean()),
                }
            )
        print(f"done: {name} {state} ({time.perf_counter() - clock:.0f}s)")

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_rows", 500)

    evasion = pd.DataFrame(evasion_rows)
    evasion["rate"] = evasion["evaded"] / evasion["attacked"]
    bounds = [wilson(int(k), int(n)) for k, n in zip(evasion["evaded"], evasion["attacked"],
                                                       strict=True)]
    evasion["ci_low"] = [low for low, _ in bounds]
    evasion["ci_high"] = [high for _, high in bounds]
    comparison = evasion_comparison(evasion_rows)

    recall = pd.DataFrame(recall_rows)
    recall["recall"] = recall["kept"] / recall["n_common"]
    pooled = (
        recall.groupby(["detector", "state", "attack"])[["kept", "n_common"]].sum().reset_index()
    )
    pooled["recall"] = pooled["kept"] / pooled["n_common"]
    pooled["A"] = pooled["attack"].map(amplitude_of)
    pooled["search"] = np.where(pooled["attack"].str.startswith("grid"), "grid", "random")
    pooled.loc[pooled["attack"] == "none", "search"] = "clean"

    outputs = {
        "clean": pd.DataFrame(clean_rows),
        "per_class": pd.DataFrame(class_rows),
        "per_family_clean": pd.DataFrame(family_rows),
        "pr_curve": pd.DataFrame(pr_rows),
        "evasion": evasion,
        "evasion_comparison": comparison.reset_index(),
        "recall_common_family": recall,
        "recall_common_pooled": pooled,
        "benign_perturbed": pd.DataFrame(benign_rows),
    }
    for key, frame in outputs.items():
        frame.to_csv(OUT_DIR / f"{segment}_{key}.csv", index=False)

    print(f"\n=== Clean performance on {segment} (threshold {THRESHOLD}) ===")
    print(outputs["clean"].round(6).to_string(index=False))
    print("\n=== Precision / recall / F1 per class ===")
    print(outputs["per_class"].round(4).to_string(index=False))
    print("\n=== Clean recall per family ===")
    print(
        outputs["per_family_clean"]
        .pivot_table(index=["family", "n"], columns=["detector", "state"], values="recall")
        .round(4)
        .to_string()
    )
    informative = comparison[
        (comparison["evaded_o"].fillna(0) > 0) | (comparison["evaded_h"].fillna(0) > 0)
    ]
    print("\n=== Evasion, original (_o) vs hardened (_h), combinations with any evasion ===")
    print(informative.round(4).to_string())
    print(informative["verdict"].value_counts().to_string())
    print("\n=== Recall on the common population, pooled over families ===")
    print(
        pooled.pivot_table(index=["detector", "state"], columns="attack", values="recall")
        .round(4)
        .to_string()
    )
    print("\n=== Perturbed BENIGN flows ===")
    print(outputs["benign_perturbed"].round(6).to_string(index=False))
    print(f"\ntotal time: {time.perf_counter() - clock:.0f}s | results in {OUT_DIR}")


if __name__ == "__main__":
    main()