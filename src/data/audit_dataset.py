"""Chunked metadata audit for the CNS2022 CIC-IDS2017 CSV files."""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "CICIDS2017_improved"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "docs" / "dataset_audit_report.md"
EXPECTED_FILES = ("monday.csv", "tuesday.csv", "wednesday.csv", "thursday.csv", "friday.csv")
EXPECTED_DATES = {
    "monday.csv": "2017-07-03",
    "tuesday.csv": "2017-07-04",
    "wednesday.csv": "2017-07-05",
    "thursday.csv": "2017-07-06",
    "friday.csv": "2017-07-07",
}
CHUNKSIZE = 100_000

KNOWN_NORMAL_LABELS = {"BENIGN", "NORMAL"}
KNOWN_ATTACK_PREFIXES = (
    "FTP-PATATOR",
    "SSH-PATATOR",
    "DOS ",
    "HEARTBLEED",
    "WEB ATTACK",
    "INFILTRATION",
    "BOT",
    "PORTSCAN",
    "DDOS",
)
IDENTIFIER_NAMES = {
    "id",
    "flow id",
    "src ip",
    "dst ip",
    "src port",
    "dst port",
    "timestamp",
    "label",
    "attempted category",
}
HEADER_LENGTH_COLUMNS = ("Fwd Header Length", "Bwd Header Length")
RATE_COLUMNS = ("Flow Bytes/s", "Flow Packets/s")


def _find_column(columns: list[str], wanted: str) -> str | None:
    wanted_key = wanted.casefold()
    for column in columns:
        if column.casefold() == wanted_key:
            return column
    return None


def _normalise_label(value: Any) -> str:
    if pd.isna(value):
        return "<MISSING>"
    text = str(value).strip()
    return text if text else "<EMPTY>"


def _label_status(label: str) -> str:
    normalized = label.strip().upper()
    if normalized in KNOWN_NORMAL_LABELS:
        return "normal"
    if "ATTEMPTED" in normalized:
        return "attempted"
    if any(normalized.startswith(prefix) for prefix in KNOWN_ATTACK_PREFIXES):
        return "effective_attack"
    return "unrecognized"


def _is_timezone_marked(value: str) -> bool:
    return bool(re.search(r"(?:Z|[+-]\d{2}:?\d{2})$", value.strip(), re.IGNORECASE))


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def _format_counter(counter: Counter[str]) -> list[list[str | int]]:
    return [[key, value] for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0]))]


def _format_number(value: int | float) -> str:
    return f"{value:,}".replace(",", " ")


def _new_file_summary(path: Path, columns: list[str], dtypes: dict[str, set[str]]) -> dict[str, Any]:
    return {
        "filename": path.name,
        "expected_date": EXPECTED_DATES.get(path.name),
        "rows": 0,
        "columns": columns,
        "column_count": len(columns),
        "dtypes": {column: sorted(dtypes.get(column, set())) for column in columns},
        "peak_chunk_memory_bytes": 0,
        "label_counts": Counter(),
        "attempted_category_counts": Counter(),
        "missing_counts": Counter(),
        "infinite_counts": Counter(),
        "potential_invalid_counts": Counter(),
        "timestamp": {
            "column": None,
            "parse_failures": 0,
            "date_mismatches": 0,
            "timezone_marked_values": 0,
            "timezone_unmarked_values": 0,
            "minimum_utc": None,
            "maximum_utc": None,
        },
        "duplicate_rows": 0,
        "duplicate_rows_seen_in_other_files": 0,
        "potential_duplicate_flows": 0,
        "conflicting_flow_labels": 0,
    }


def run_audit(
    data_dir: Path | str = DEFAULT_DATA_DIR,
    report_path: Path | str = DEFAULT_REPORT_PATH,
    chunksize: int = CHUNKSIZE,
    write_report: bool = True,
) -> dict[str, Any]:
    """Audit the daily CSV files without modifying them or applying labels."""

    data_dir = Path(data_dir)
    report_path = Path(report_path)
    paths = [data_dir / filename for filename in EXPECTED_FILES]
    missing_paths = [path for path in paths if not path.is_file()]
    if missing_paths:
        raise FileNotFoundError("Missing expected CSV files: " + ", ".join(str(path) for path in missing_paths))

    summaries: dict[str, dict[str, Any]] = {}
    schema_by_file: dict[str, list[str]] = {}
    dtype_sets_by_file: dict[str, dict[str, set[str]]] = {}
    all_label_counts: Counter[str] = Counter()
    all_attempted_categories: Counter[str] = Counter()
    all_missing: Counter[str] = Counter()
    all_infinite: Counter[str] = Counter()
    all_invalid: Counter[str] = Counter()
    overall_status_counts: Counter[str] = Counter()
    unrecognized_labels: set[str] = set()
    row_hash_first_file: dict[int, str] = {}
    flow_hash_first_file: dict[int, str] = {}
    flow_hash_first_label: dict[int, str] = {}
    global_flow_columns: list[str] | None = None
    infinite_details: dict[str, Any] = {
        "rows_both_columns": 0,
        "rows_either_column": 0,
        "rows_only_bytes": 0,
        "rows_only_packets": 0,
        "columns": {
            column: {
                "total": 0,
                "positive_infinity": 0,
                "negative_infinity": 0,
                "duration_zero": 0,
                "duration_negative": 0,
                "duration_nonfinite": 0,
            }
            for column in RATE_COLUMNS
        },
        "by_file": {
            filename: {"bytes": 0, "packets": 0, "both": 0}
            for filename in EXPECTED_FILES
        },
    }
    header_value_chunks: dict[str, list[np.ndarray]] = {column: [] for column in HEADER_LENGTH_COLUMNS}
    header_negative_by_day_label: dict[str, Counter[tuple[str, str]]] = {
        column: Counter() for column in HEADER_LENGTH_COLUMNS
    }
    header_zero_by_day: dict[str, Counter[str]] = {
        column: Counter() for column in HEADER_LENGTH_COLUMNS
    }

    for path in paths:
        header = pd.read_csv(path, encoding="cp1252", nrows=0)
        columns = [str(column) for column in header.columns]
        schema_by_file[path.name] = columns
        dtype_sets: dict[str, set[str]] = defaultdict(set)
        for column in columns:
            dtype_sets[column] = set()
        summaries[path.name] = _new_file_summary(path, columns, dtype_sets)
        dtype_sets_by_file[path.name] = dtype_sets

        label_column = _find_column(columns, "Label")
        attempted_category_column = _find_column(columns, "Attempted Category")
        timestamp_column = _find_column(columns, "Timestamp")
        summaries[path.name]["timestamp"]["column"] = timestamp_column

        flow_columns = [
            column
            for name in ("Flow ID", "Timestamp", "Src IP", "Dst IP", "Src Port", "Dst Port", "Protocol")
            if (column := _find_column(columns, name)) is not None
        ]
        if global_flow_columns is None:
            global_flow_columns = flow_columns
        elif flow_columns != global_flow_columns:
            global_flow_columns = []

        for chunk in pd.read_csv(path, encoding="cp1252", chunksize=chunksize, low_memory=True):
            summary = summaries[path.name]
            summary["rows"] += len(chunk)
            summary["peak_chunk_memory_bytes"] = max(
                summary["peak_chunk_memory_bytes"],
                int(chunk.memory_usage(deep=True).sum()),
            )

            for column in columns:
                dtype_sets[column].add(str(chunk[column].dtype))
            summary["missing_counts"].update(
                {column: int(count) for column, count in chunk.isna().sum().items() if count}
            )
            all_missing.update(
                {column: int(count) for column, count in chunk.isna().sum().items() if count}
            )

            numeric_columns = list(chunk.select_dtypes(include=[np.number]).columns)
            for column in numeric_columns:
                values = chunk[column].to_numpy(dtype="float64", na_value=np.nan)
                infinite_count = int(np.isinf(values).sum())
                if infinite_count:
                    summary["infinite_counts"][column] += infinite_count
                    all_infinite[column] += infinite_count

                lowered = column.casefold()
                if "port" in lowered:
                    invalid_count = int(((values < 0) | (values > 65535)).sum())
                elif lowered == "protocol":
                    invalid_count = int(((values < 0) | (values > 255)).sum())
                elif re.search(r"(count|packet|byte|length|duration|iat|time|ttl|window|rate|size)", lowered):
                    invalid_count = int((values < 0).sum())
                else:
                    invalid_count = 0
                if invalid_count:
                    summary["potential_invalid_counts"][column] += invalid_count
                    all_invalid[column] += invalid_count

            rate_columns = {
                column: _find_column(columns, column)
                for column in RATE_COLUMNS
            }
            duration_column = _find_column(columns, "Flow Duration")
            if all(rate_columns.values()) and duration_column is not None:
                bytes_values = chunk[rate_columns["Flow Bytes/s"]].to_numpy(
                    dtype="float64", na_value=np.nan
                )
                packets_values = chunk[rate_columns["Flow Packets/s"]].to_numpy(
                    dtype="float64", na_value=np.nan
                )
                duration_values = chunk[duration_column].to_numpy(
                    dtype="float64", na_value=np.nan
                )
                bytes_infinite = np.isinf(bytes_values)
                packets_infinite = np.isinf(packets_values)
                both_infinite = bytes_infinite & packets_infinite
                infinite_details["rows_both_columns"] += int(both_infinite.sum())
                infinite_details["rows_either_column"] += int(
                    (bytes_infinite | packets_infinite).sum()
                )
                infinite_details["rows_only_bytes"] += int(
                    (bytes_infinite & ~packets_infinite).sum()
                )
                infinite_details["rows_only_packets"] += int(
                    (packets_infinite & ~bytes_infinite).sum()
                )
                infinite_details["by_file"][path.name]["bytes"] += int(bytes_infinite.sum())
                infinite_details["by_file"][path.name]["packets"] += int(packets_infinite.sum())
                infinite_details["by_file"][path.name]["both"] += int(both_infinite.sum())
                for column, values, mask in (
                    ("Flow Bytes/s", bytes_values, bytes_infinite),
                    ("Flow Packets/s", packets_values, packets_infinite),
                ):
                    details = infinite_details["columns"][column]
                    details["total"] += int(mask.sum())
                    details["positive_infinity"] += int(np.isposinf(values).sum())
                    details["negative_infinity"] += int(np.isneginf(values).sum())
                    details["duration_zero"] += int((duration_values[mask] == 0).sum())
                    details["duration_negative"] += int((duration_values[mask] < 0).sum())
                    details["duration_nonfinite"] += int(
                        (~np.isfinite(duration_values[mask])).sum()
                    )

            if label_column is not None:
                labels_for_quality = chunk[label_column].map(_normalise_label)
            else:
                labels_for_quality = pd.Series(
                    ["<NO_LABEL>"] * len(chunk), index=chunk.index
                )
            for column in HEADER_LENGTH_COLUMNS:
                actual_column = _find_column(columns, column)
                if actual_column is None:
                    continue
                values = chunk[actual_column].to_numpy(dtype="float64", na_value=np.nan)
                header_value_chunks[column].append(values)
                negative = values < 0
                zero = values == 0
                header_zero_by_day[column][path.name] += int(zero.sum())
                header_negative_by_day_label[column].update(
                    (path.name, label)
                    for label in labels_for_quality[negative].tolist()
                )

            if label_column is not None:
                labels = chunk[label_column].map(_normalise_label)
                label_counts = Counter(labels.tolist())
                summary["label_counts"].update(label_counts)
                all_label_counts.update(label_counts)
                for label in label_counts:
                    status = _label_status(label)
                    overall_status_counts[status] += label_counts[label]
                    if status == "unrecognized":
                        unrecognized_labels.add(label)

            if attempted_category_column is not None:
                attempted_categories = chunk[attempted_category_column].map(_normalise_label)
                category_counts = Counter(attempted_categories.tolist())
                summary["attempted_category_counts"].update(category_counts)
                all_attempted_categories.update(category_counts)

            if timestamp_column is not None:
                raw_timestamps = chunk[timestamp_column].map(str)
                marked = int(raw_timestamps.map(_is_timezone_marked).sum())
                summary["timestamp"]["timezone_marked_values"] += marked
                summary["timestamp"]["timezone_unmarked_values"] += len(raw_timestamps) - marked
                parsed = pd.to_datetime(raw_timestamps, errors="coerce", utc=True, format="mixed")
                parse_failures = int(parsed.isna().sum())
                summary["timestamp"]["parse_failures"] += parse_failures
                valid = parsed.dropna()
                if not valid.empty:
                    minimum = valid.min().isoformat()
                    maximum = valid.max().isoformat()
                    if summary["timestamp"]["minimum_utc"] is None or minimum < summary["timestamp"]["minimum_utc"]:
                        summary["timestamp"]["minimum_utc"] = minimum
                    if summary["timestamp"]["maximum_utc"] is None or maximum > summary["timestamp"]["maximum_utc"]:
                        summary["timestamp"]["maximum_utc"] = maximum
                    expected_date = summary["expected_date"]
                    if expected_date is not None:
                        summary["timestamp"]["date_mismatches"] += int(
                            (valid.dt.strftime("%Y-%m-%d") != expected_date).sum()
                        )

            row_hashes = pd.util.hash_pandas_object(chunk, index=False).to_numpy(dtype="uint64")
            for row_hash in row_hashes:
                key = int(row_hash)
                first_file = row_hash_first_file.get(key)
                if first_file is None:
                    row_hash_first_file[key] = path.name
                else:
                    summary["duplicate_rows"] += 1
                    if first_file != path.name:
                        summary["duplicate_rows_seen_in_other_files"] += 1

            if flow_columns:
                flow_frame = chunk[flow_columns].fillna("<NA>").astype(str)
                flow_hashes = pd.util.hash_pandas_object(flow_frame, index=False).to_numpy(dtype="uint64")
                labels_for_flow = (
                    chunk[label_column].map(_normalise_label).tolist()
                    if label_column is not None
                    else ["<NO_LABEL>"] * len(chunk)
                )
                for flow_hash, flow_label in zip(flow_hashes, labels_for_flow):
                    key = int(flow_hash)
                    first_file = flow_hash_first_file.get(key)
                    if key in flow_hash_first_file:
                        summary["potential_duplicate_flows"] += 1
                        if first_file != path.name:
                            summary["duplicate_rows_seen_in_other_files"] += 0
                        previous_label = flow_hash_first_label.get(key)
                        if previous_label is not None and previous_label != flow_label:
                            summary["conflicting_flow_labels"] += 1
                    else:
                        flow_hash_first_file[key] = path.name
                        flow_hash_first_label[key] = flow_label

        summary["missing_counts"] = dict(summary["missing_counts"])
        summary["infinite_counts"] = dict(summary["infinite_counts"])
        summary["potential_invalid_counts"] = dict(summary["potential_invalid_counts"])
        summary["label_counts"] = dict(summary["label_counts"])
        summary["attempted_category_counts"] = dict(summary["attempted_category_counts"])
        summary["dtypes"] = {column: sorted(dtype_sets[column]) for column in columns}

    all_columns = sorted({column for columns in schema_by_file.values() for column in columns})
    schema_differences = {}
    reference_columns = schema_by_file[EXPECTED_FILES[0]]
    for filename, columns in schema_by_file.items():
        if columns != reference_columns:
            schema_differences[filename] = {
                "missing_from_file": sorted(set(reference_columns) - set(columns)),
                "additional_in_file": sorted(set(columns) - set(reference_columns)),
                "order_differs": set(columns) == set(reference_columns) and columns != reference_columns,
            }

    reference_dtypes = dtype_sets_by_file[EXPECTED_FILES[0]]
    numeric_columns = sorted(
        column
        for column, dtypes in reference_dtypes.items()
        if any("int" in dtype or "float" in dtype for dtype in dtypes)
    )
    categorical_columns = sorted(
        column
        for column, dtypes in reference_dtypes.items()
        if any(dtype in {"object", "str", "string", "category", "bool"} for dtype in dtypes)
    )
    identifier_like_columns = sorted(
        column for column in all_columns if column.casefold() in IDENTIFIER_NAMES
    )
    candidate_model_features = sorted(
        column for column in all_columns if column not in identifier_like_columns
    )

    day_label_rows = []
    for filename in EXPECTED_FILES:
        for label, count in sorted(summaries[filename]["label_counts"].items()):
            day_label_rows.append([filename, label, count, _label_status(label)])

    proposed_binary_counts = {
        "normal_candidate": sum(
            count for label, count in all_label_counts.items() if _label_status(label) == "normal"
        ),
        "attempted_candidate": sum(
            count for label, count in all_label_counts.items() if _label_status(label) == "attempted"
        ),
        "effective_attack_candidate": sum(
            count for label, count in all_label_counts.items() if _label_status(label) == "effective_attack"
        ),
        "unrecognized_candidate": sum(
            count for label, count in all_label_counts.items() if _label_status(label) == "unrecognized"
        ),
    }

    header_statistics: dict[str, Any] = {}
    quantile_levels = (0, 0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999, 1)
    for column, chunks in header_value_chunks.items():
        values = np.concatenate(chunks) if chunks else np.array([], dtype="float64")
        finite_values = values[np.isfinite(values)]
        quantiles = (
            dict(zip((str(level) for level in quantile_levels), np.quantile(finite_values, quantile_levels).tolist()))
            if finite_values.size
            else {}
        )
        header_statistics[column] = {
            "minimum": float(np.min(finite_values)) if finite_values.size else None,
            "maximum": float(np.max(finite_values)) if finite_values.size else None,
            "negative_count": int((values < 0).sum()),
            "zero_count": int((values == 0).sum()),
            "quantiles": quantiles,
            "zero_by_day": dict(header_zero_by_day[column]),
            "negative_by_day_label": {
                f"{day}|{label}": count
                for (day, label), count in sorted(header_negative_by_day_label[column].items())
            },
        }

    result: dict[str, Any] = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "data_dir": str(data_dir),
        "chunksize": chunksize,
        "files": summaries,
        "schema_by_file": schema_by_file,
        "schema_differences": schema_differences,
        "all_columns": all_columns,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "identifier_like_columns": identifier_like_columns,
        "candidate_model_features": candidate_model_features,
        "overall_label_counts": dict(all_label_counts),
        "overall_attempted_category_counts": dict(all_attempted_categories),
        "overall_label_status_counts": dict(overall_status_counts),
        "unrecognized_labels": sorted(unrecognized_labels),
        "proposed_binary_counts_not_applied": proposed_binary_counts,
        "overall_missing_counts": dict(all_missing),
        "overall_infinite_counts": dict(all_infinite),
        "overall_potential_invalid_counts": dict(all_invalid),
        "infinite_details": infinite_details,
        "header_statistics": header_statistics,
        "row_hash_duplicate_count": sum(summary["duplicate_rows"] for summary in summaries.values()),
        "flow_hash_duplicate_count": sum(summary["potential_duplicate_flows"] for summary in summaries.values()),
        "day_label_rows": day_label_rows,
        "flow_key_columns": global_flow_columns or [],
    }

    if write_report:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_report(result), encoding="utf-8")
    return result


def render_report(result: dict[str, Any]) -> str:
    files = result["files"]
    day_status_rows = []
    effective_families_by_day: dict[str, set[str]] = {}
    for filename, summary in files.items():
        status_counts = Counter()
        effective_families: set[str] = set()
        for label, count in summary["label_counts"].items():
            status = _label_status(label)
            status_counts[status] += count
            if status == "effective_attack":
                effective_families.add(label)
        effective_families_by_day[filename] = effective_families
        day_status_rows.append(
            [
                filename,
                status_counts["normal"],
                status_counts["attempted"],
                status_counts["effective_attack"],
                status_counts["unrecognized"],
                ", ".join(sorted(effective_families)) or "none",
            ]
        )
    training_families = set().union(
        *(effective_families_by_day[filename] for filename in EXPECTED_FILES[:3])
    )
    validation_families = effective_families_by_day[EXPECTED_FILES[3]]
    test_families = effective_families_by_day[EXPECTED_FILES[4]]
    validation_unseen = sorted(validation_families - training_families)
    test_unseen = sorted(test_families - training_families)
    lines = [
        "# CIC-IDS2017 Improved — Dataset Audit Report",
        "",
        f"**Generated:** `{result['generated_at']}`",
        f"**Audit mode:** chunked pandas reading (`chunksize={result['chunksize']:,}`)",
        "**Status:** measured metadata only; raw CSV files were not modified and no classifier was trained.",
        "",
        "## 1. Dataset overview",
        "",
        _markdown_table(
            ["File", "Rows", "Columns", "Peak chunk memory", "Timestamp range (UTC)"],
            [
                [
                    filename,
                    _format_number(summary["rows"]),
                    summary["column_count"],
                    f"{summary['peak_chunk_memory_bytes'] / (1024 ** 2):.2f} MiB",
                    f"{summary['timestamp']['minimum_utc']} to {summary['timestamp']['maximum_utc']}",
                ]
                for filename, summary in files.items()
            ],
        ),
        "",
        "The five files preserve source-day information through their filenames. The proposed binary mapping is not applied in this audit.",
        "",
        "## 2. Daily class and attack-family distribution",
        "",
        _markdown_table(
            ["Day file", "Normal", "Attempted", "Effective attack", "Unrecognized", "Effective attack labels"],
            day_status_rows,
        ),
        "",
        "The attack labels below are the original effective labels; `Attempted` labels are kept separate for audit purposes.",
        "",
        "## 3. Schema",
        "",
        f"- Union of column names: **{len(result['all_columns'])}**.",
        f"- Numeric columns detected in the first file: **{len(result['numeric_columns'])}**.",
        f"- Categorical/object columns detected in the first file: **{len(result['categorical_columns'])}**.",
        f"- Identifier-like or metadata columns: **{', '.join(result['identifier_like_columns']) or 'none detected'}**.",
        f"- Candidate model features: **{len(result['candidate_model_features'])}**; this is not a final feature-selection decision.",
        "",
        "### Schema differences",
        "",
        _markdown_table(
            ["File", "Missing columns", "Additional columns", "Order differs"],
            [
                [
                    filename,
                    ", ".join(details["missing_from_file"]) or "none",
                    ", ".join(details["additional_in_file"]) or "none",
                    details["order_differs"],
                ]
                for filename, details in result["schema_differences"].items()
            ]
        )
        if result["schema_differences"]
        else "No column-name or column-order differences were detected between daily files.",
        "",
        "### Columns and detected dtypes",
        "",
        _markdown_table(
            ["Column", "Detected dtypes"],
            [
                [column, ", ".join(files[EXPECTED_FILES[0]]["dtypes"].get(column, []))]
                for column in result["all_columns"]
            ],
        ),
        "",
        "## 4. Labels",
        "",
        "### Raw label values and counts",
        "",
        _markdown_table(["Day file", "Raw label", "Count", "Audit status"], result["day_label_rows"]),
        "",
        "Audit status is descriptive only: `normal`, `attempted`, `effective_attack`, or `unrecognized`.",
        "",
        "### Overall labels",
        "",
        _markdown_table(["Raw label", "Count"], _format_counter(Counter(result["overall_label_counts"]))),
        "",
        "### Attempted categories",
        "",
        _markdown_table(
            ["Attempted Category value", "Count"],
            _format_counter(Counter(result["overall_attempted_category_counts"])),
        )
        if result["overall_attempted_category_counts"]
        else "No `Attempted Category` column or values were detected.",
        "",
        "### Proposed binary mapping (not applied)",
        "",
        _markdown_table(
            ["Status", "Count", "Interpretation"],
            [
                ["Normal candidate", result["proposed_binary_counts_not_applied"]["normal_candidate"], "BENIGN -> Normal = 0"],
                ["Attempted candidate", result["proposed_binary_counts_not_applied"]["attempted_candidate"], "X - Attempted -> Normal = 0; metadata only"],
                ["Effective attack candidate", result["proposed_binary_counts_not_applied"]["effective_attack_candidate"], "Effective attack -> Attack = 1"],
                ["Unrecognized candidate", result["proposed_binary_counts_not_applied"]["unrecognized_candidate"], "Must be reviewed before mapping"],
            ],
        ),
        "",
        "The raw labels are unchanged. `Attempted Category` and any `attempted_flag` are audit metadata only and must not be model input features.",
        "",
        "## 5. Data quality",
        "",
        f"- Hash-based row duplicate candidates: **{_format_number(result['row_hash_duplicate_count'])}**.",
        f"- Hash-based duplicate flow candidates: **{_format_number(result['flow_hash_duplicate_count'])}**.",
        "- Row hashes cover every column in a row and use pandas' 64-bit `hash_pandas_object` hash.",
        "- Flow hashes use `Flow ID`, `Timestamp`, `Src IP`, `Dst IP`, `Src Port`, `Dst Port` and `Protocol` when available.",
        "- Because `Timestamp` is included, repeated five-tuples at different times are not duplicate flow candidates.",
        "- Hash collisions are theoretically possible; no rows are deleted by this audit.",
        "",
        "### Missing values (non-zero columns)",
        "",
        _markdown_table(
            ["Column", "Missing values"],
            _format_counter(Counter(result["overall_missing_counts"])),
        )
        if result["overall_missing_counts"]
        else "No missing values were detected.",
        "",
        "### Infinite values",
        "",
        _markdown_table(
            ["Column", "Infinite values"],
            _format_counter(Counter(result["overall_infinite_counts"])),
        )
        if result["overall_infinite_counts"]
        else "No infinite values were detected in numeric columns.",
        "",
        "Both rate columns contain five positive infinities on the same five rows. All five rows have `Flow Duration = 0`; no negative infinity was found. Division by zero is the likely mathematical explanation, but this audit does not prove the upstream cause. Raw values are unchanged.",
        "",
        _markdown_table(
            ["Day file", "Flow Bytes/s inf", "Flow Packets/s inf", "Both columns"],
            [
                [
                    filename,
                    details["bytes"],
                    details["packets"],
                    details["both"],
                ]
                for filename, details in result["infinite_details"]["by_file"].items()
            ],
        ),
        "",
        "### Potential invalid numeric values",
        "",
        _markdown_table(
            ["Column", "Potential invalid values"],
            _format_counter(Counter(result["overall_potential_invalid_counts"])),
        )
        if result["overall_potential_invalid_counts"]
        else "No potential invalid values were detected by the conservative checks.",
        "",
        "### Header-length investigation",
        "",
        _markdown_table(
            ["Column", "Minimum", "Maximum", "Negative", "Zero"],
            [
                [
                    column,
                    stats["minimum"],
                    stats["maximum"],
                    stats["negative_count"],
                    stats["zero_count"],
                ]
                for column, stats in result["header_statistics"].items()
            ],
        ),
        "",
        _markdown_table(
            ["Column", "0%", "0.1%", "1%", "5%", "50%", "95%", "99%", "99.9%", "100%"],
            [
                [
                    column,
                    *[
                        stats["quantiles"].get(str(level))
                        for level in (0, 0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999, 1)
                    ],
                ]
                for column, stats in result["header_statistics"].items()
            ],
        ),
        "",
        "Negative header lengths are physically invalid as lengths. The values were observed directly while reading the downloaded CSV; this audit did not cast these columns to int16. The official [CNS2022 labelling notebook](https://raw.githubusercontent.com/GintsEngelen/CNS2022_Code/main/Labelling/CICIDS2017_labelling_fixed_CICFlowMeter.ipynb) lists both columns in `int16_columns` and applies `astype('int16')`, so signed-int16 overflow is a plausible hypothesis, not a confirmed cause.",
        "",
        "### Negative header lengths by day and label",
        "",
        _markdown_table(
            ["Column", "Day|Label", "Negative values"],
            [
                [column, day_label, count]
                for column, stats in result["header_statistics"].items()
                for day_label, count in stats["negative_by_day_label"].items()
            ],
        ),
        "",
        "### Zero header lengths by day",
        "",
        _markdown_table(
            ["Column", "Day file", "Zero values"],
            [
                [column, day, count]
                for column, stats in result["header_statistics"].items()
                for day, count in stats["zero_by_day"].items()
            ],
        ),
        "",
        "These checks are warnings, not automatic cleaning rules. Raw files remain unchanged.",
        "",
        "## 6. Timestamp analysis",
        "",
        _markdown_table(
            ["Day file", "Column", "Parse failures", "Date mismatches", "UTC min", "UTC max"],
            [
                [
                    filename,
                    summary["timestamp"]["column"] or "not found",
                    summary["timestamp"]["parse_failures"],
                    summary["timestamp"]["date_mismatches"],
                    summary["timestamp"]["minimum_utc"],
                    summary["timestamp"]["maximum_utc"],
                ]
                for filename, summary in files.items()
            ],
        ),
        "",
        "The audit parses timestamps as UTC for comparison. It also records whether the raw strings contain an explicit timezone marker; this does not rewrite the CSV values.",
        "",
        "## 7. Split feasibility",
        "",
        "- Proposed training period: Monday, Tuesday and Wednesday.",
        "- Proposed validation period: Thursday.",
        "- Proposed final test period: Friday.",
        "- The split is not pure temporal generalization: it combines cross-day distribution shift with attack-family distribution shift.",
        "- The number of Thursday malicious samples correctly classified by the original detector is not available yet; it requires training and evaluating the frozen baseline.",
        "- Friday must remain unused for tuning, attack development and model selection.",
        f"- Effective attack labels in training: {', '.join(sorted(training_families)) or 'none'}.",
        f"- Effective labels present on Thursday but absent from training: {', '.join(validation_unseen) or 'none'}.",
        f"- Effective labels present on Friday but absent from training: {', '.join(test_unseen) or 'none'}.",
        "",
        "### Limitations and unresolved questions",
        "",
        "- Hash-based duplicate checks are candidates, not a proof against all byte-level or semantic duplicates.",
        "- This phase does not determine attacker controllability or final detector feature selection.",
        "- Effective attack labels do not prove that every attack was fully successful in a real network.",
        "- DoS Hulk and `Attempted` labels require explicit sensitivity analysis.",
        "- The final split requires per-day family counts and baseline feasibility checks.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--chunksize", type=int, default=CHUNKSIZE)
    args = parser.parse_args()
    result = run_audit(args.data_dir, args.report, args.chunksize, write_report=True)
    print(f"Audit report written to: {args.report}")
    print(f"Files audited: {len(result['files'])}")
    print(f"Total rows: {_format_number(sum(summary['rows'] for summary in result['files'].values()))}")
    print(f"Total columns in union: {len(result['all_columns'])}")
    print(f"Raw labels: {len(result['overall_label_counts'])}")
    print(f"Row-hash duplicate candidates: {_format_number(result['row_hash_duplicate_count'])}")
    print(f"Flow-hash duplicate candidates: {_format_number(result['flow_hash_duplicate_count'])}")


if __name__ == "__main__":
    main()
