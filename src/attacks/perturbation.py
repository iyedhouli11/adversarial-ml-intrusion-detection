"""Feature-space perturbation with recomputation of verified derived features.

Only Fwd-side primitives are perturbed: packet lengths by a factor s >= 1
(padding) and inter-arrival times by a factor t >= 1 (delay). Derived columns
are recomputed with relations measured on the train segment. Columns without a
verified formula stay unchanged. Nothing here queries a model or reads
validation, test, Thursday or Friday data.

Modelling hypothesis (not verifiable from the data): stretching the Fwd
intervals by t lengthens the flow by (t - 1) x Fwd IAT Total.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MICRO = 1e6  # durations are in microseconds (verified with the rate formulas)
RTOL = 1e-3
ATOL = 1e-6
BOUND_RTOL = 1e-6

SCALED_BY_S = (
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Fwd Segment Size Avg",
    "Total Length of Fwd Packet",
)
SCALED_BY_T = (
    "Fwd IAT Total",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",
)
RECOMPUTED = (
    "Flow Duration",
    "Flow IAT Mean",
    "Flow Packets/s",
    "Flow Bytes/s",
    "Fwd Packets/s",
    "Bwd Packets/s",
    "Packet Length Mean",
    "Average Packet Size",
    "Packet Length Max",
    "Packet Length Min",
    "Packet Length Variance",
    "Packet Length Std",
)
CHANGED_COLUMNS = SCALED_BY_S + SCALED_BY_T + RECOMPUTED


def _ratio(
    numerator: pd.Series,
    denominator: pd.Series,
    valid: pd.Series,
    fallback: pd.Series,
) -> pd.Series:
    """numerator / denominator where valid, the original value elsewhere."""
    safe = denominator.where(valid, 1.0)
    value = np.where(valid.to_numpy(), (numerator / safe).to_numpy(), fallback.to_numpy())
    return pd.Series(value, index=numerator.index)


def perturb(features: pd.DataFrame, s: float, t: float) -> pd.DataFrame:
    """Return a perturbed copy; the input frame is never modified."""
    if not (np.isfinite(s) and np.isfinite(t)) or s < 1.0 or t < 1.0:
        raise ValueError("s and t must be finite and >= 1 (padding and delay only)")

    out = features.copy(deep=True)

    def g(name: str) -> pd.Series:
        return features[name].astype("float64")

    n_f, n_b = g("Total Fwd Packet"), g("Total Bwd packets")
    total = n_f + n_b
    bwd_len = g("Total Length of Bwd Packet")

    new: dict[str, pd.Series] = {}
    for column in SCALED_BY_S:
        new[column] = g(column) * s
    for column in SCALED_BY_T:
        new[column] = g(column) * t

    duration = g("Flow Duration") + (t - 1.0) * g("Fwd IAT Total")
    new["Flow Duration"] = duration
    fwd_len = new["Total Length of Fwd Packet"]

    has_time = duration > 0
    has_packets = total > 0
    multi = total > 1

    new["Flow IAT Mean"] = _ratio(duration, total - 1.0, multi, g("Flow IAT Mean"))
    new["Flow Packets/s"] = _ratio(total * MICRO, duration, has_time, g("Flow Packets/s"))
    new["Flow Bytes/s"] = _ratio(
        (fwd_len + bwd_len) * MICRO, duration, has_time, g("Flow Bytes/s")
    )
    new["Fwd Packets/s"] = _ratio(n_f * MICRO, duration, has_time, g("Fwd Packets/s"))
    new["Bwd Packets/s"] = _ratio(n_b * MICRO, duration, has_time, g("Bwd Packets/s"))

    mean_all = _ratio(fwd_len + bwd_len, total, has_packets, g("Packet Length Mean"))
    new["Packet Length Mean"] = mean_all
    new["Average Packet Size"] = mean_all
    new["Packet Length Max"] = np.maximum(
        new["Fwd Packet Length Max"], g("Bwd Packet Length Max")
    )

    fwd_min = new["Fwd Packet Length Min"].where(n_f > 0, np.inf)
    bwd_min = g("Bwd Packet Length Min").where(n_b > 0, np.inf)
    pooled_min = np.minimum(fwd_min, bwd_min)
    new["Packet Length Min"] = pd.Series(
        np.where(has_packets.to_numpy(), pooled_min.to_numpy(), g("Packet Length Min").to_numpy()),
        index=features.index,
    )

    s_f, s_b = new["Fwd Packet Length Std"], g("Bwd Packet Length Std")
    m_f, m_b = new["Fwd Packet Length Mean"], g("Bwd Packet Length Mean")
    within = (n_f - 1.0).clip(lower=0.0) * s_f**2 + (n_b - 1.0).clip(lower=0.0) * s_b**2
    between = n_f * (m_f - mean_all) ** 2 + n_b * (m_b - mean_all) ** 2
    variance = _ratio(within + between, total - 1.0, multi, g("Packet Length Variance"))
    new["Packet Length Variance"] = variance
    std = np.sqrt(np.clip(variance.to_numpy(), 0.0, None))
    new["Packet Length Std"] = pd.Series(
        np.where(multi.to_numpy(), std, g("Packet Length Std").to_numpy()),
        index=features.index,
    )

    for column, series in new.items():
        out[column] = series.to_numpy(dtype="float64")
    return out


def _above(small: pd.Series, large: pd.Series) -> np.ndarray:
    return (small > large * (1.0 + RTOL) + ATOL).to_numpy()


def order_violations(candidate: pd.DataFrame) -> pd.DataFrame:
    """Boolean frame: orderings verified on the train segment that a candidate breaks."""
    c = candidate
    return pd.DataFrame(
        {
            "fwd_iat_total_above_duration": _above(c["Fwd IAT Total"], c["Flow Duration"]),
            "flow_iat_min_above_mean": _above(c["Flow IAT Min"], c["Flow IAT Mean"]),
            "flow_iat_mean_above_max": _above(c["Flow IAT Mean"], c["Flow IAT Max"]),
            "flow_iat_max_above_duration": _above(c["Flow IAT Max"], c["Flow Duration"]),
            "fwd_length_order": _above(c["Fwd Packet Length Min"], c["Fwd Packet Length Mean"])
            | _above(c["Fwd Packet Length Mean"], c["Fwd Packet Length Max"]),
        },
        index=candidate.index,
    )


def out_of_bounds(candidate: pd.DataFrame, lower: pd.Series, upper: pd.Series) -> np.ndarray:
    """True where a changed column leaves the [lower, upper] range seen on train."""
    columns = list(CHANGED_COLUMNS)
    values = candidate[columns]
    low, high = lower[columns], upper[columns]
    below = values.lt(low - low.abs() * BOUND_RTOL - 1e-9, axis=1)
    above = values.gt(high + high.abs() * BOUND_RTOL + 1e-9, axis=1)
    return (below | above).any(axis=1).to_numpy()


def rejection_reasons(
    original: pd.DataFrame,
    candidate: pd.DataFrame,
    lower: pd.Series,
    upper: pd.Series,
) -> pd.DataFrame:
    """All rejection reasons per row (True = the candidate must be rejected)."""
    reasons = order_violations(candidate)
    reasons["out_of_bounds"] = out_of_bounds(candidate, lower, upper)
    columns = list(CHANGED_COLUMNS)
    new_values = candidate[columns].to_numpy(dtype=float)
    old_values = original[columns].to_numpy(dtype=float)
    reasons["non_finite"] = (~np.isfinite(new_values) & np.isfinite(old_values)).any(axis=1)
    return reasons