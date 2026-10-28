# Data Directory

Sample files bundled so the app runs without downloads, plus the destination for the full public datasets. `GET /health` reports which of these files the backend found and whether each is real or synthetic.

---

## 1. Amazon Last Mile Routing Research Challenge — real subset
- **Filename**: `amazon_last_mile_sample.json`
- **Source**: [Registry of Open Data on AWS — Amazon Last Mile Routing Research Challenge](https://registry.opendata.aws/amazon-last-mile-challenges/) (Merchán et al., 2022, *Transportation Science*)
- **License**: CC BY-NC 4.0 — non-commercial use, attribution required
- **Contents**: 13 routes from July–August 2018 (stations DCH4, DLA7, DLA8, DLA9, DBO2, DSE4, DSE5), 2,051 stop records including one station per route, with package dimensions and planned service times. Package data is nested under each stop in this sample.
- **Not included**: actual visit order, route distances, durations, driver IDs. The app treats these as unknown.
- **Full dataset**: 9,184 routes. Place it at `./data/amazon_last_mile.json`; it is used in preference to the sample.

---

## 2. Planned vs Actual Last-Mile Routes — synthetic fixture
- **Filename**: `mendeley_synthetic_fixture.csv`
- **Nature**: **Synthetic.** 30 routes / 603 stops generated for this project in the column layout the adapter reads (`route_id, driver_id, stop_id, planned_sequence, actual_sequence, lat, lng, service_time_min, planned_distance, actual_distance, planned_duration, actual_duration`). Not real delivery data; ingested with `is_synthetic=True`.
- **Reference dataset**: [Mendeley Data — Last-mile delivery route deviations dataset: planned vs. actual routes](https://data.mendeley.com/datasets/kkwgfvmtxn) (DOI `10.17632/kkwgfvmtxn.1`), CC BY 4.0.
- **Using the real dataset**: download it and place it at `./data/mendeley_planned_vs_actual.csv`; it is used in preference to the fixture. Check the adapter's column mapping against the real files first.
