# Data Provenance & Ingestion Specification — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Datasets

The platform is designed around two public logistics research datasets. The repository bundles a real subset of the first and a synthetic stand-in for the second (see `data/README.md`).

### 1. Amazon Last Mile Routing Research Challenge
- **Source**: [Registry of Open Data on AWS](https://registry.opendata.aws/amazon-last-mile-challenges/)
- **License**: CC BY-NC 4.0
- **Scope**: 9,184 historical driver routes performed in 2018 across 5 U.S. metropolitan areas.
- **Attributes used**: stop locations, the station (used as depot), route date, package dimensions, planned service times.
- **Committed sample**: 13 routes in `./data/amazon_last_mile_sample.json`. It has no actual visit order, distances or durations, which are stored as unknown.
- **Full dataset setup**: place it at `./data/amazon_last_mile.json`; it is used in preference to the sample.

### 2. Planned vs Actual Last-Mile Routes
- **Source**: [Mendeley Data](https://data.mendeley.com/datasets/kkwgfvmtxn), DOI [`10.17632/kkwgfvmtxn.1`](https://doi.org/10.17632/kkwgfvmtxn.1), CC BY 4.0
- **Attributes used**: planned vs actual stop sequences, planned vs actual distance and duration.
- **Committed file**: `./data/mendeley_synthetic_fixture.csv` — a **synthetic** 30-route / 603-stop fixture, ingested with `is_synthetic = True`.
- **Real dataset setup**: place it at `./data/mendeley_planned_vs_actual.csv`; it is used in preference to the fixture.

## Synthetic Data Policy

- The bundled Mendeley-schema fixture and the in-code fallback (used when no files are present) are tagged `is_synthetic = True`.
- `GET /health` reports `data_mode` (`synthetic_demo`, `bundled_samples` or `public_datasets`) and, per dataset, whether the file is real, synthetic or missing.
- The offline evaluation (`backend/scripts/train_eval.py`) runs on whatever outcome data exists, which with the bundled files is the synthetic fixture; its output is labeled `evaluated_on_synthetic_data: true` and is a pipeline check only.
- Values missing from the source (distances, durations, actual order, lateness) are stored as unknown, never replaced with defaults.

## Ingestion & Quality Validation Pipeline

```text
RAW DATA (CSV / Parquet / JSON)
        ↓
DataValidator (Missing values, duplicate check, duration/distance & coordinate bounds)
        ↓
DataQualityReport & SHA-256 Provenance Hash
        ↓
Canonical Delivery Model Normalization (Route, Stop, Package, Driver)
        ↓
PostgreSQL Persistence + DuckDB Parquet Analytics (routes_olap)
```

## Provenance Tracking Schema
For every dataset record stored in `datasets`:
- `id`, `name`, `source_url`, `doi`, `license`, `version`
- `download_timestamp`, `file_hash` (SHA-256)
- `row_count`, `route_count`, `stop_count`, `driver_count`
- `validation_status`, `is_synthetic`
