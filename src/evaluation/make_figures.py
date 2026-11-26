"""Figures from the saved aggregates in results/final/ (no model, no raw data).

Usage: python -m src.evaluation.make_figures --segment test
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT_DIR = Path("results/final")
COLORS = {"original": "#c0392b", "hardened": "#2471a3"}


def recall_vs_amplitude(segment: str) -> Path:
    pooled = pd.read_csv(OUT_DIR / f"{segment}_recall_common_pooled.csv")
    detectors = sorted(pooled["detector"].unique())
    fig, axes = plt.subplots(1, len(detectors), figsize=(5 * len(detectors), 4), sharey=True)
    for ax, detector in zip(axes, detectors, strict=True):
        for state, color in COLORS.items():
            part = pooled[(pooled["detector"] == detector) & (pooled["state"] == state)]
            curve = part[part["search"].isin(["clean", "random"])].sort_values("A")
            ax.plot(curve["A"], curve["recall"], marker="o", color=color, label=f"{state}")
            grid = part[part["search"] == "grid"]
            ax.scatter(grid["A"], grid["recall"], marker="x", s=70, color=color,
                       label=f"{state}, grid")
        ax.set_title(detector)
        ax.set_xlabel("amplitude A (s, t in [1, 1 + A])")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("recall under attack (common population)")
    axes[0].legend(loc="lower left", fontsize=8)
    fig.suptitle(f"Recall vs attack amplitude, before and after hardening ({segment})")
    fig.tight_layout()
    path = OUT_DIR / f"{segment}_recall_vs_amplitude.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def pr_curves(segment: str) -> Path:
    curves = pd.read_csv(OUT_DIR / f"{segment}_pr_curve.csv")
    clean = pd.read_csv(OUT_DIR / f"{segment}_clean.csv")
    detectors = sorted(curves["detector"].unique())
    fig, axes = plt.subplots(1, len(detectors), figsize=(5 * len(detectors), 4), sharey=True)
    for ax, detector in zip(axes, detectors, strict=True):
        for state, color in COLORS.items():
            part = curves[(curves["detector"] == detector) & (curves["state"] == state)]
            auc = clean[(clean["detector"] == detector) & (clean["state"] == state)]["PR-AUC"]
            ax.plot(part["recall"], part["precision"], color=color,
                    label=f"{state} (PR-AUC {auc.iloc[0]:.4f})")
        ax.set_title(detector)
        ax.set_xlabel("recall")
        ax.grid(alpha=0.3)
        ax.legend(loc="lower left", fontsize=8)
    axes[0].set_ylabel("precision")
    fig.suptitle(f"Precision-recall curves, clean ({segment})")
    fig.tight_layout()
    path = OUT_DIR / f"{segment}_pr_curves.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segment", choices=("test", "friday"), required=True)
    segment = parser.parse_args().segment
    for path in (recall_vs_amplitude(segment), pr_curves(segment)):
        print(f"written: {path}")


if __name__ == "__main__":
    main()