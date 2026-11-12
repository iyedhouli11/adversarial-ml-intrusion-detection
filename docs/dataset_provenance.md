# CIC-IDS2017 Improved — CNS2022 Provenance

## Dataset identity

- **Name:** CIC-IDS2017 Improved
- **Release:** CNS2022 improved release
- **Research source:** [CNS2022 CIC-IDS2017 documentation](https://intrusion-detection.distrinet-research.be/CNS2022/CICIDS2017.html)
- **Official archive:** [CICIDS2017_improved.zip](https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/CICIDS2017_improved.zip)
- **Download date:** 2026-11-12
- **Storage location:** `data/raw/CICIDS2017_improved.zip`

## Download verification

- **HTTP response:** `200 OK`
- **Expected archive size:** `343,549,013` bytes
- **Verified archive size:** `343,549,013` bytes
- **SHA-256:** `97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883`
- **ZIP CRC verification:** passed with Python's built-in `zipfile` module

## Archive contents

The archive contains five CSV files, one for each capture day:

```text
monday.csv
tuesday.csv
wednesday.csv
thursday.csv
friday.csv
```

The total uncompressed size reported by the ZIP central directory is
`1,152,270,765` bytes. The files were extracted to:

```text
data/raw/CICIDS2017_improved/
```

The five extracted file sizes were checked against the ZIP metadata. Raw CSV
files are not modified by the audit.

## Reproducible acquisition and extraction

1. Open the official CNS2022 archive URL above.
2. Save `CICIDS2017_improved.zip` under `data/raw/`.
3. Verify the expected byte size and SHA-256 before extraction.
4. Verify ZIP CRC integrity.
5. Extract only the five daily CSV files into `data/raw/CICIDS2017_improved/`.
6. Confirm the extracted sizes against the ZIP central directory.

The raw archive and raw CSV files are excluded from Git by `.gitignore`. They
must never be committed or pushed. The audit preserves the original labels and
does not apply the proposed binary mapping.

## Academic sources

- Liu, Engelen, Lynar, Essam and Joosen, *Error Prevalence in NIDS datasets:
  A Case Study on CIC-IDS-2017 and CSE-CIC-IDS-2018*, CNS 2022.
- [CNS2022 tools and documentation](https://intrusion-detection.distrinet-research.be/CNS2022/Tools_Documentation.html)
- [CNS2022 dataset download index](https://intrusion-detection.distrinet-research.be/CNS2022/Datasets/)
