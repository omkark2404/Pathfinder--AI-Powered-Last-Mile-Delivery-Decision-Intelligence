# Data Provenance & Ingestion Specification — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Primary Real-World Datasets

The platform is designed around two real public logistics research datasets:

### 1. Amazon Last Mile Routing Research Challenge
- **Source**: [AWS Open Data Registry](https://registry.opendata.aws/amazon-last-mile-challenges/)
- **Scope**: 9,184 historical driver routes performed in 2018 across 5 U.S. metropolitan areas.
- **Attributes Used**: Route sequences, stop locations, service times, package dimensions, depot coordinates.
- **Committed Sample**: A 13-route benchmark sample is provided in `./data/amazon_last_mile_sample.json` for immediate testing.
- **Full Dataset Setup**: Download the complete 9,184-route `amazon_last_mile.json` from the official AWS Open Data Registry and place it in `./data/amazon_last_mile.json`.

### 2. Planned vs Actual Last-Mile Routes
- **Source**: [Mendeley Data](https://data.mendeley.com/datasets/kkwgfvmtxn)
- **DOI**: [`10.17632/kkwgfvmtxn.1`](https://doi.org/10.17632/kkwgfvmtxn.1)
- **License**: CC BY 4.0
- **Attributes Used**: Planned route sequences vs actual driver sequences, travel distance, duration, time-window data.
- **Usage**: Benchmark for sequence deviation prediction, driver adherence analytics, and Kendall Tau similarity index.
- **Committed Dataset**: A schema-compliant synthetic benchmark fixture (30 routes, 603 stops) is bundled at `./data/mendeley_planned_vs_actual.csv` for offline verification and local testing. The actual Mendeley dataset can be downloaded from the DOI link above for production model training.

## Synthetic Data Policy

> **IMPORTANT**: Synthetic data is used ONLY as a fallback for schema validation and local UI demonstration when the raw dataset files are absent from `./data/`.

When dataset files are missing:
- Ingested datasets are explicitly tagged with `is_synthetic = True`.
- API endpoints report `data_mode = "synthetic_demo"`.
- ML models report `evaluation_status = "insufficient_data"` and `metrics = null`.
- Synthetic fixtures are **NEVER** used for model training, final evaluation, reported accuracy metrics, or business impact calculations.

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
