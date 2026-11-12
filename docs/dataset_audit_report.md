# CIC-IDS2017 Improved — Dataset Audit Report

**Generated:** `2026-11-12T21:39:33.760113+01:00`
**Audit mode:** chunked pandas reading (`chunksize=100,000`)
**Status:** measured metadata only; raw CSV files were not modified and no classifier was trained.

## 1. Dataset overview

| File | Rows | Columns | Peak chunk memory | Timestamp range (UTC) |
| --- | --- | --- | --- | --- |
| monday.csv | 371 624 | 91 | 101.87 MiB | 2017-07-03T11:55:58.598308+00:00 to 2017-07-03T20:01:34.352593+00:00 |
| tuesday.csv | 322 078 | 91 | 101.85 MiB | 2017-07-04T11:53:44.398274+00:00 to 2017-07-04T20:00:30.041663+00:00 |
| wednesday.csv | 496 641 | 91 | 101.85 MiB | 2017-07-05T11:42:42.084372+00:00 to 2017-07-05T20:10:14.557249+00:00 |
| thursday.csv | 362 076 | 91 | 102.27 MiB | 2017-07-06T11:59:00.490140+00:00 to 2017-07-06T20:04:36.513760+00:00 |
| friday.csv | 547 557 | 91 | 101.74 MiB | 2017-07-07T11:59:50.315195+00:00 to 2017-07-07T20:02:40.977798+00:00 |

The five files preserve source-day information through their filenames. The proposed binary mapping is not applied in this audit.

## 2. Daily class and attack-family distribution

| Day file | Normal | Attempted | Effective attack | Unrecognized | Effective attack labels |
| --- | --- | --- | --- | --- | --- |
| monday.csv | 371624 | 0 | 0 | 0 | none |
| tuesday.csv | 315106 | 39 | 6933 | 0 | FTP-Patator, SSH-Patator |
| wednesday.csv | 319120 | 5876 | 171645 | 0 | DoS GoldenEye, DoS Hulk, DoS Slowhttptest, DoS Slowloris, Heartbleed |
| thursday.csv | 288172 | 1997 | 71907 | 0 | Infiltration, Infiltration - Portscan, Web Attack - Brute Force, Web Attack - SQL Injection, Web Attack - XSS |
| friday.csv | 288544 | 4067 | 254946 | 0 | Botnet, DDoS, Portscan |

The attack labels below are the original effective labels; `Attempted` labels are kept separate for audit purposes.

## 3. Schema

- Union of column names: **91**.
- Numeric columns detected in the first file: **86**.
- Categorical/object columns detected in the first file: **5**.
- Identifier-like or metadata columns: **Attempted Category, Dst IP, Dst Port, Flow ID, Label, Src IP, Src Port, Timestamp, id**.
- Candidate model features: **82**; this is not a final feature-selection decision.

### Schema differences

No column-name or column-order differences were detected between daily files.

### Columns and detected dtypes

| Column | Detected dtypes |
| --- | --- |
| ACK Flag Count | int64 |
| Active Max | int64 |
| Active Mean | float64 |
| Active Min | int64 |
| Active Std | float64 |
| Attempted Category | int64 |
| Average Packet Size | float64 |
| Bwd Bulk Rate Avg | int64 |
| Bwd Bytes/Bulk Avg | int64 |
| Bwd Header Length | int64 |
| Bwd IAT Max | int64 |
| Bwd IAT Mean | float64 |
| Bwd IAT Min | int64 |
| Bwd IAT Std | float64 |
| Bwd IAT Total | int64 |
| Bwd Init Win Bytes | int64 |
| Bwd PSH Flags | int64 |
| Bwd Packet Length Max | int64 |
| Bwd Packet Length Mean | float64 |
| Bwd Packet Length Min | int64 |
| Bwd Packet Length Std | float64 |
| Bwd Packet/Bulk Avg | int64 |
| Bwd Packets/s | float64 |
| Bwd RST Flags | int64 |
| Bwd Segment Size Avg | float64 |
| Bwd URG Flags | int64 |
| CWR Flag Count | int64 |
| Down/Up Ratio | float64 |
| Dst IP | str |
| Dst Port | int64 |
| ECE Flag Count | int64 |
| FIN Flag Count | int64 |
| FWD Init Win Bytes | int64 |
| Flow Bytes/s | float64 |
| Flow Duration | int64 |
| Flow IAT Max | int64 |
| Flow IAT Mean | float64 |
| Flow IAT Min | int64 |
| Flow IAT Std | float64 |
| Flow ID | str |
| Flow Packets/s | float64 |
| Fwd Act Data Pkts | int64 |
| Fwd Bulk Rate Avg | int64 |
| Fwd Bytes/Bulk Avg | int64 |
| Fwd Header Length | int64 |
| Fwd IAT Max | int64 |
| Fwd IAT Mean | float64 |
| Fwd IAT Min | int64 |
| Fwd IAT Std | float64 |
| Fwd IAT Total | int64 |
| Fwd PSH Flags | int64 |
| Fwd Packet Length Max | int64 |
| Fwd Packet Length Mean | float64 |
| Fwd Packet Length Min | int64 |
| Fwd Packet Length Std | float64 |
| Fwd Packet/Bulk Avg | int64 |
| Fwd Packets/s | float64 |
| Fwd RST Flags | int64 |
| Fwd Seg Size Min | int64 |
| Fwd Segment Size Avg | float64 |
| Fwd URG Flags | int64 |
| ICMP Code | int64 |
| ICMP Type | int64 |
| Idle Max | int64 |
| Idle Mean | float64 |
| Idle Min | int64 |
| Idle Std | float64 |
| Label | str |
| PSH Flag Count | int64 |
| Packet Length Max | int64 |
| Packet Length Mean | float64 |
| Packet Length Min | int64 |
| Packet Length Std | float64 |
| Packet Length Variance | float64 |
| Protocol | int64 |
| RST Flag Count | int64 |
| SYN Flag Count | int64 |
| Src IP | str |
| Src Port | int64 |
| Subflow Bwd Bytes | int64 |
| Subflow Bwd Packets | int64 |
| Subflow Fwd Bytes | int64 |
| Subflow Fwd Packets | int64 |
| Timestamp | str |
| Total Bwd packets | int64 |
| Total Fwd Packet | int64 |
| Total Length of Bwd Packet | int64 |
| Total Length of Fwd Packet | int64 |
| Total TCP Flow Time | int64 |
| URG Flag Count | int64 |
| id | int64 |

## 4. Labels

### Raw label values and counts

| Day file | Raw label | Count | Audit status |
| --- | --- | --- | --- |
| monday.csv | BENIGN | 371624 | normal |
| tuesday.csv | BENIGN | 315106 | normal |
| tuesday.csv | FTP-Patator | 3972 | effective_attack |
| tuesday.csv | FTP-Patator - Attempted | 12 | attempted |
| tuesday.csv | SSH-Patator | 2961 | effective_attack |
| tuesday.csv | SSH-Patator - Attempted | 27 | attempted |
| wednesday.csv | BENIGN | 319120 | normal |
| wednesday.csv | DoS GoldenEye | 7567 | effective_attack |
| wednesday.csv | DoS GoldenEye - Attempted | 80 | attempted |
| wednesday.csv | DoS Hulk | 158468 | effective_attack |
| wednesday.csv | DoS Hulk - Attempted | 581 | attempted |
| wednesday.csv | DoS Slowhttptest | 1740 | effective_attack |
| wednesday.csv | DoS Slowhttptest - Attempted | 3368 | attempted |
| wednesday.csv | DoS Slowloris | 3859 | effective_attack |
| wednesday.csv | DoS Slowloris - Attempted | 1847 | attempted |
| wednesday.csv | Heartbleed | 11 | effective_attack |
| thursday.csv | BENIGN | 288172 | normal |
| thursday.csv | Infiltration | 36 | effective_attack |
| thursday.csv | Infiltration - Attempted | 45 | attempted |
| thursday.csv | Infiltration - Portscan | 71767 | effective_attack |
| thursday.csv | Web Attack - Brute Force | 73 | effective_attack |
| thursday.csv | Web Attack - Brute Force - Attempted | 1292 | attempted |
| thursday.csv | Web Attack - SQL Injection | 13 | effective_attack |
| thursday.csv | Web Attack - SQL Injection - Attempted | 5 | attempted |
| thursday.csv | Web Attack - XSS | 18 | effective_attack |
| thursday.csv | Web Attack - XSS - Attempted | 655 | attempted |
| friday.csv | BENIGN | 288544 | normal |
| friday.csv | Botnet | 736 | effective_attack |
| friday.csv | Botnet - Attempted | 4067 | attempted |
| friday.csv | DDoS | 95144 | effective_attack |
| friday.csv | Portscan | 159066 | effective_attack |

Audit status is descriptive only: `normal`, `attempted`, `effective_attack`, or `unrecognized`.

### Overall labels

| Raw label | Count |
| --- | --- |
| BENIGN | 1582566 |
| Portscan | 159066 |
| DoS Hulk | 158468 |
| DDoS | 95144 |
| Infiltration - Portscan | 71767 |
| DoS GoldenEye | 7567 |
| Botnet - Attempted | 4067 |
| FTP-Patator | 3972 |
| DoS Slowloris | 3859 |
| DoS Slowhttptest - Attempted | 3368 |
| SSH-Patator | 2961 |
| DoS Slowloris - Attempted | 1847 |
| DoS Slowhttptest | 1740 |
| Web Attack - Brute Force - Attempted | 1292 |
| Botnet | 736 |
| Web Attack - XSS - Attempted | 655 |
| DoS Hulk - Attempted | 581 |
| DoS GoldenEye - Attempted | 80 |
| Web Attack - Brute Force | 73 |
| Infiltration - Attempted | 45 |
| Infiltration | 36 |
| SSH-Patator - Attempted | 27 |
| Web Attack - XSS | 18 |
| Web Attack - SQL Injection | 13 |
| FTP-Patator - Attempted | 12 |
| Heartbleed | 11 |
| Web Attack - SQL Injection - Attempted | 5 |

### Attempted categories

| Attempted Category value | Count |
| --- | --- |
| -1 | 2087997 |
| 0 | 4845 |
| 1 | 4067 |
| 6 | 2804 |
| 5 | 138 |
| 4 | 75 |
| 3 | 27 |
| 2 | 23 |

### Proposed binary mapping (not applied)

| Status | Count | Interpretation |
| --- | --- | --- |
| Normal candidate | 1582566 | BENIGN -> Normal = 0 |
| Attempted candidate | 11979 | X - Attempted -> Normal = 0; metadata only |
| Effective attack candidate | 505431 | Effective attack -> Attack = 1 |
| Unrecognized candidate | 0 | Must be reviewed before mapping |

The raw labels are unchanged. `Attempted Category` and any `attempted_flag` are audit metadata only and must not be model input features.

## 5. Data quality

- Hash-based row duplicate candidates: **0**.
- Hash-based duplicate flow candidates: **0**.
- Row hashes cover every column in a row and use pandas' 64-bit `hash_pandas_object` hash.
- Flow hashes use `Flow ID`, `Timestamp`, `Src IP`, `Dst IP`, `Src Port`, `Dst Port` and `Protocol` when available.
- Because `Timestamp` is included, repeated five-tuples at different times are not duplicate flow candidates.
- Hash collisions are theoretically possible; no rows are deleted by this audit.

### Missing values (non-zero columns)

No missing values were detected.

### Infinite values

| Column | Infinite values |
| --- | --- |
| Flow Bytes/s | 5 |
| Flow Packets/s | 5 |

Both rate columns contain five positive infinities on the same five rows. All five rows have `Flow Duration = 0`; no negative infinity was found. Division by zero is the likely mathematical explanation, but this audit does not prove the upstream cause. Raw values are unchanged.

| Day file | Flow Bytes/s inf | Flow Packets/s inf | Both columns |
| --- | --- | --- | --- |
| monday.csv | 3 | 3 | 3 |
| tuesday.csv | 0 | 0 | 0 |
| wednesday.csv | 1 | 1 | 1 |
| thursday.csv | 1 | 1 | 1 |
| friday.csv | 0 | 0 | 0 |

### Potential invalid numeric values

| Column | Potential invalid values |
| --- | --- |
| Bwd Header Length | 472 |
| Fwd Header Length | 309 |

### Header-length investigation

| Column | Minimum | Maximum | Negative | Zero |
| --- | --- | --- | --- | --- |
| Fwd Header Length | -32708.0 | 32748.0 | 309 | 2146 |
| Bwd Header Length | -32764.0 | 32680.0 | 472 | 55174 |

| Column | 0% | 0.1% | 1% | 5% | 50% | 95% | 99% | 99.9% | 100% |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fwd Header Length | -32708.0 | 0.0 | 8.0 | 8.0 | 32.0 | 624.0 | 1576.0 | 7972.0 | 32748.0 |
| Bwd Header Length | -32764.0 | 0.0 | 0.0 | 8.0 | 20.0 | 616.0 | 1960.0 | 11208.0 | 32680.0 |

Negative header lengths are physically invalid as lengths. The values were observed directly while reading the downloaded CSV; this audit did not cast these columns to int16. The official [CNS2022 labelling notebook](https://raw.githubusercontent.com/GintsEngelen/CNS2022_Code/main/Labelling/CICIDS2017_labelling_fixed_CICFlowMeter.ipynb) lists both columns in `int16_columns` and applies `astype('int16')`, so signed-int16 overflow is a plausible hypothesis, not a confirmed cause.

### Negative header lengths by day and label

| Column | Day|Label | Negative values |
| --- | --- | --- |
| Fwd Header Length | friday.csv\|BENIGN | 40 |
| Fwd Header Length | monday.csv\|BENIGN | 46 |
| Fwd Header Length | thursday.csv\|BENIGN | 94 |
| Fwd Header Length | thursday.csv\|Infiltration | 5 |
| Fwd Header Length | tuesday.csv\|BENIGN | 60 |
| Fwd Header Length | wednesday.csv\|BENIGN | 64 |
| Bwd Header Length | friday.csv\|BENIGN | 89 |
| Bwd Header Length | monday.csv\|BENIGN | 85 |
| Bwd Header Length | thursday.csv\|BENIGN | 124 |
| Bwd Header Length | thursday.csv\|Infiltration | 4 |
| Bwd Header Length | tuesday.csv\|BENIGN | 82 |
| Bwd Header Length | wednesday.csv\|BENIGN | 85 |
| Bwd Header Length | wednesday.csv\|Heartbleed | 3 |

### Zero header lengths by day

| Column | Day file | Zero values |
| --- | --- | --- |
| Fwd Header Length | monday.csv | 405 |
| Fwd Header Length | tuesday.csv | 440 |
| Fwd Header Length | wednesday.csv | 356 |
| Fwd Header Length | thursday.csv | 474 |
| Fwd Header Length | friday.csv | 471 |
| Bwd Header Length | monday.csv | 5220 |
| Bwd Header Length | tuesday.csv | 4420 |
| Bwd Header Length | wednesday.csv | 7597 |
| Bwd Header Length | thursday.csv | 34674 |
| Bwd Header Length | friday.csv | 3263 |

These checks are warnings, not automatic cleaning rules. Raw files remain unchanged.

## 6. Timestamp analysis

| Day file | Column | Parse failures | Date mismatches | UTC min | UTC max |
| --- | --- | --- | --- | --- | --- |
| monday.csv | Timestamp | 0 | 0 | 2017-07-03T11:55:58.598308+00:00 | 2017-07-03T20:01:34.352593+00:00 |
| tuesday.csv | Timestamp | 0 | 0 | 2017-07-04T11:53:44.398274+00:00 | 2017-07-04T20:00:30.041663+00:00 |
| wednesday.csv | Timestamp | 0 | 0 | 2017-07-05T11:42:42.084372+00:00 | 2017-07-05T20:10:14.557249+00:00 |
| thursday.csv | Timestamp | 0 | 0 | 2017-07-06T11:59:00.490140+00:00 | 2017-07-06T20:04:36.513760+00:00 |
| friday.csv | Timestamp | 0 | 0 | 2017-07-07T11:59:50.315195+00:00 | 2017-07-07T20:02:40.977798+00:00 |

The audit parses timestamps as UTC for comparison. It also records whether the raw strings contain an explicit timezone marker; this does not rewrite the CSV values.

## 7. Split feasibility

- Proposed training period: Monday, Tuesday and Wednesday.
- Proposed validation period: Thursday.
- Proposed final test period: Friday.
- The split is not pure temporal generalization: it combines cross-day distribution shift with attack-family distribution shift.
- The number of Thursday malicious samples correctly classified by the original detector is not available yet; it requires training and evaluating the frozen baseline.
- Friday must remain unused for tuning, attack development and model selection.
- Effective attack labels in training: DoS GoldenEye, DoS Hulk, DoS Slowhttptest, DoS Slowloris, FTP-Patator, Heartbleed, SSH-Patator.
- Effective labels present on Thursday but absent from training: Infiltration, Infiltration - Portscan, Web Attack - Brute Force, Web Attack - SQL Injection, Web Attack - XSS.
- Effective labels present on Friday but absent from training: Botnet, DDoS, Portscan.

### Limitations and unresolved questions

- Hash-based duplicate checks are candidates, not a proof against all byte-level or semantic duplicates.
- This phase does not determine attacker controllability or final detector feature selection.
- Effective attack labels do not prove that every attack was fully successful in a real network.
- DoS Hulk and `Attempted` labels require explicit sensitivity analysis.
- The final split requires per-day family counts and baseline feasibility checks.
