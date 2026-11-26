"""Post hoc control for the hardening (NOT part of hardening specification v1).

Added after seeing the hardening results. For every detector and state it
(1) rebuilds the models with the same seeds and checks that the clean FP / FN
on validation are reproduced, (2) measures how many perturbed BENIGN flows
(feasible candidates only) are flagged, compared with the same flows before
perturbation, and (3) counts the prediction changes between the original and
the hardened model on the whole validation segment. The test segment,
Thursday and Friday are never loaded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.attacks.multi_target_attack import DETECTORS
from src.attacks.perturbation import perturb, rejection_reasons
from src.attacks.random_search_attack import DATA_DIR, MTU, SEED, STRATEGY, THRESHOLD
from src.data.dataset_loader import load_split
from src.data.preprocessing import (
    fit_preprocessor,
    prepare_working_frame,
    target_from_labels,
    transform_frame,
)
from src.data.temporal_split import assign_temporal_segments
from src.defenses.adversarial_training import adversarial_examples, clean_metrics, stack

BENIGN_SAMPLE = 20000
AMPLITUDES = (0.5, 1.0, 2.0)
PERTURB_SEED = 99


def main() -> None:
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
    train_features = prepare_working_frame(train, STRATEGY)[columns].reset_index(drop=True)
    y_train = target_from_labels(train["Label"]).to_numpy()
    lower, upper = train_features.min(), train_features.max()
    attack_flows = train_features[y_train == 1].reset_index(drop=True)
    adversarial, skipped = adversarial_examples(
        attack_flows, lower, upper, np.random.default_rng(SEED)
    )
    y_aug = np.concatenate([y_train, np.ones(len(adversarial), dtype=y_train.dtype)])
    print(f"adversarial copies rebuilt: {len(adversarial)} | without feasible candidate: {skipped}")
    del train_features, attack_flows

    work = prepare_working_frame(validation, STRATEGY)
    features = work[columns].reset_index(drop=True)
    labels = work["Label"].to_numpy()
    y_val = target_from_labels(validation["Label"]).to_numpy()
    benign_idx = np.flatnonzero(labels == "BENIGN")
    size = min(BENIGN_SAMPLE, len(benign_idx))
    sample = np.sort(np.random.default_rng(PERTURB_SEED).choice(benign_idx, size=size, replace=False))
    benign = features.iloc[sample].reset_index(drop=True)
    print(f"BENIGN validation flows sampled: {len(benign)} of {len(benign_idx)}")

    perturbed = {}
    for amplitude in AMPLITUDES:
        draw = np.random.default_rng(PERTURB_SEED + int(round(amplitude * 100)))
        s = 1.0 + amplitude * draw.random(len(benign))
        t = 1.0 + amplitude * draw.random(len(benign))
        candidate = perturb(benign, s, t)
        reasons = rejection_reasons(benign, candidate, lower, upper)
        infeasible = reasons.any(axis=1).to_numpy() | (
            candidate["Fwd Packet Length Max"].to_numpy() > MTU
        )
        feasible = ~infeasible
        perturbed[amplitude] = (feasible, candidate[feasible].reset_index(drop=True))

    fitted_by_flag = {True: scaled, False: plain}
    matrices = {
        flag: (
            transform_frame(train, fitted),
            transform_frame(adversarial, fitted),
            transform_frame(features, fitted),
        )
        for flag, fitted in fitted_by_flag.items()
    }

    reproduction, rows, paired = [], [], []
    for name, (needs_scaling, make) in DETECTORS.items():
        fitted = fitted_by_flag[needs_scaling]
        x_train, x_adv, x_val = matrices[needs_scaling]
        flags = {}
        for state in ("original", "hardened"):
            model = make()
            if state == "original":
                model.fit(x_train, y_train)
            else:
                model.fit(stack(x_train, x_adv), y_aug)
            base = model.predict_proba(x_val)[:, 1]
            metrics = clean_metrics(base, y_val)
            reproduction.append(
                {"detector": name, "state": state, "FP": metrics["FP"], "FN": metrics["FN"]}
            )
            flags[state] = base >= THRESHOLD
            before_all = flags[state][sample]
            for amplitude, (feasible, candidate) in perturbed.items():
                after = model.predict_proba(transform_frame(candidate, fitted))[:, 1] >= THRESHOLD
                before = before_all[feasible]
                rows.append(
                    {
                        "detector": name,
                        "state": state,
                        "A": amplitude,
                        "feasible_share": float(feasible.mean()),
                        "flagged_before": float(before.mean()),
                        "flagged_after": float(after.mean()),
                        "newly_flagged": int((after & ~before).sum()),
                        "cleared": int((before & ~after).sum()),
                    }
                )
            print(f"done: {name} {state}")

        original, hardened = flags["original"], flags["hardened"]
        attack = y_val == 1
        paired.append(
            {
                "detector": name,
                "attacks_gained": int((~original & hardened & attack).sum()),
                "attacks_lost": int((original & ~hardened & attack).sum()),
                "benign_newly_flagged": int((~original & hardened & ~attack).sum()),
                "benign_cleared": int((original & ~hardened & ~attack).sum()),
            }
        )

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print("\n=== Reproduction check: clean FP / FN on validation ===")
    print("earlier run: LogReg 509/274 -> 444/227 | RandomForest 11/40 -> 12/26 | XGBoost 7/36 -> 5/10")
    print(pd.DataFrame(reproduction).to_string(index=False))
    print("\n=== Perturbed BENIGN flows (feasible candidates only, same flows before and after) ===")
    print(pd.DataFrame(rows).round(6).to_string(index=False))
    print("\n=== Prediction changes, original -> hardened, whole validation segment ===")
    print(pd.DataFrame(paired).to_string(index=False))


if __name__ == "__main__":
    main()