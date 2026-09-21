# Benchmark Data Directory

This directory contains offline benchmark and sample dataset files packaged with the repository to enable immediate evaluation, automated testing, and development without requiring external downloads.

---

## 1. Amazon Last Mile Routing Challenge Sample
- **Filename**: `amazon_last_mile_sample.json`
- **Source**: [AWS Open Data Registry — Amazon Last Mile Routing Research Challenge](https://registry.opendata.aws/amazon-last-mile-challenges/)
- **Nature**: Real benchmark sample (13 complete historical driver routes, 200+ stops, package dimensions, service times).
- **License**: AWS Open Data
- **Production Setup**: To run the full dataset (9,184 historical driver routes), download from AWS Open Data Registry and place at `./data/amazon_last_mile.json`.

---

## 2. Planned vs Actual Last-Mile Routes Benchmark Fixture
- **Filename**: `mendeley_planned_vs_actual.csv`
- **Reference Schema**: [Mendeley Data — Planned vs Actual Last-Mile Routes](https://data.mendeley.com/datasets/kkwgfvmtxn) (DOI: `10.17632/kkwgfvmtxn.1`)
- **Nature**: **Synthetic benchmark fixture** (30 routes, 603 stops) created strictly conforming to the Mendeley dataset schema and distributions. Bundled for offline unit testing, CI runs, and developer verification.
- **Production Setup**: For training on the authentic proprietary dataset, download from Mendeley Data (DOI: `10.17632/kkwgfvmtxn.1`) and place at `./data/mendeley_planned_vs_actual.csv`.
