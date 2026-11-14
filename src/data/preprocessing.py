"""Label generation and leakage-safe preprocessing for supervised models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HeaderStrategy = Literal["impute", "exclude"]

HEADER_LENGTH_COLUMNS = ("Fwd Header Length", "Bwd Header Length")
BASE_METADATA_COLUMNS = {
    "id",
    "Flow ID",
    "Src IP",
    "Dst IP",
    "Timestamp",
    "Label",
    "Attempted Category",
    "attempted_flag",
    "source_day",
}
PORT_COLUMNS = {"Src Port", "Dst Port"}
NORMAL_LABELS = {"BENIGN", "NORMAL"}
EFFECTIVE_ATTACK_LABELS = {
    "FTP-Patator",
    "SSH-Patator",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowhttptest",
    "DoS Slowloris",
    "Heartbleed",
    "Web Attack - Brute Force",
    "Web Attack - XSS",
    "Web Attack - SQL Injection",
    "Infiltration",
    "Infiltration - Portscan",
    "Botnet",
    "Portscan",
    "DDoS",
}


def _normalise_label(value: object) -> str:
    if pd.isna(value):
        return "<MISSING>"
    text = str(value).strip()
    return text if text else "<EMPTY>"


ATTEMPTED_LABELS = {
    "SSH-PATATOR - ATTEMPTED",
    "FTP-PATATOR - ATTEMPTED",
    "DOS SLOWHTTPTEST - ATTEMPTED",
    "DOS SLOWLORIS - ATTEMPTED",
    "DOS HULK - ATTEMPTED",
    "DOS GOLDENEYE - ATTEMPTED",
    "WEB ATTACK - BRUTE FORCE - ATTEMPTED",
    "WEB ATTACK - XSS - ATTEMPTED",
    "INFILTRATION - ATTEMPTED",
    "WEB ATTACK - SQL INJECTION - ATTEMPTED",
}


def _is_attempted_label(label: str) -> bool:
    return label.upper() in ATTEMPTED_LABELS


def target_from_labels(labels: pd.Series) -> pd.Series:
    """Generate a binary target without changing the original label series."""

    targets: list[int] = []
    unknown: set[str] = set()
    effective_by_upper = {label.upper(): label for label in EFFECTIVE_ATTACK_LABELS}

    for raw_value in labels.tolist():
        label = _normalise_label(raw_value)
        upper = label.upper()
        if upper in NORMAL_LABELS or _is_attempted_label(label):
            targets.append(0)
        elif upper in effective_by_upper:
            targets.append(1)
        else:
            unknown.add(label)

    if unknown:
        values = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown labels cannot be mapped silently: {values}")

    return pd.Series(targets, index=labels.index, name="target", dtype="int8")


def replace_infinities(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a working copy with positive and negative infinity as NaN."""

    working = frame.copy(deep=True)
    return working.replace([np.inf, -np.inf], np.nan)


def prepare_working_frame(frame: pd.DataFrame, header_strategy: HeaderStrategy) -> pd.DataFrame:
    """Apply non-destructive cleaning rules to a working copy."""

    if header_strategy not in {"impute", "exclude"}:
        raise ValueError("header_strategy must be 'impute' or 'exclude'")

    working = replace_infinities(frame)
    if header_strategy == "impute":
        for column in HEADER_LENGTH_COLUMNS:
            if column in working.columns:
                working.loc[working[column] < 0, column] = np.nan
    return working


def select_feature_columns(
    frame: pd.DataFrame,
    *,
    header_strategy: HeaderStrategy,
    include_ports: bool = False,
) -> list[str]:
    """Select model candidates while preserving metadata outside X."""

    excluded = set(BASE_METADATA_COLUMNS)
    if not include_ports:
        excluded.update(PORT_COLUMNS)
    if header_strategy == "exclude":
        excluded.update(HEADER_LENGTH_COLUMNS)
    return [column for column in frame.columns if column not in excluded]


def _is_categorical_column(frame: pd.DataFrame, column: str) -> bool:
    if column.casefold() == "protocol":
        return True
    dtype = frame[column].dtype
    return (
        pd.api.types.is_object_dtype(dtype)
        or pd.api.types.is_string_dtype(dtype)
        or isinstance(dtype, pd.CategoricalDtype)
        or pd.api.types.is_bool_dtype(dtype)
    )


@dataclass(frozen=True)
class FittedPreprocessor:
    """Fitted transformer plus the exact feature contract used to fit it."""

    transformer: ColumnTransformer
    feature_columns: tuple[str, ...]
    numeric_columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]
    header_strategy: HeaderStrategy
    include_ports: bool


def build_preprocessor(
    frame: pd.DataFrame,
    *,
    header_strategy: HeaderStrategy,
    include_ports: bool = False,
    scale_numeric: bool = True,
) -> tuple[ColumnTransformer, list[str], list[str], list[str]]:
    """Build a ColumnTransformer without fitting it."""

    feature_columns = select_feature_columns(
        frame,
        header_strategy=header_strategy,
        include_ports=include_ports,
    )
    categorical_columns = [
        column for column in feature_columns if _is_categorical_column(frame, column)
    ]
    numeric_columns = [
        column for column in feature_columns if column not in categorical_columns
    ]

    numeric_steps: list[tuple[str, object]] = [
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True))
    ]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    transformers: list[tuple[str, Pipeline, list[str]]] = [
        (
            "numeric",
            Pipeline(numeric_steps),
            numeric_columns,
        ),
        (
            "categorical",
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    (
                        "onehot",
                        OneHotEncoder(handle_unknown="ignore", sparse_output=True),
                    ),
                ]
            ),
            categorical_columns,
        ),
    ]
    transformer = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return transformer, feature_columns, numeric_columns, categorical_columns


def fit_preprocessor(
    training_frame: pd.DataFrame,
    *,
    header_strategy: HeaderStrategy,
    include_ports: bool = False,
    scale_numeric: bool = True,
) -> FittedPreprocessor:
    """Fit preprocessing statistics on training data only."""

    working = prepare_working_frame(training_frame, header_strategy)
    transformer, features, numeric, categorical = build_preprocessor(
        working,
        header_strategy=header_strategy,
        include_ports=include_ports,
        scale_numeric=scale_numeric,
    )
    transformer.fit(working[features])
    return FittedPreprocessor(
        transformer=transformer,
        feature_columns=tuple(features),
        numeric_columns=tuple(numeric),
        categorical_columns=tuple(categorical),
        header_strategy=header_strategy,
        include_ports=include_ports,
    )


def transform_frame(frame: pd.DataFrame, fitted: FittedPreprocessor):
    """Transform validation or test data with training-fitted statistics."""

    working = prepare_working_frame(frame, fitted.header_strategy)
    return fitted.transformer.transform(working[list(fitted.feature_columns)])
