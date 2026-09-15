# System Limitations & Boundary Conditions — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Known Limitations

### 1. Benchmark Sample Included vs. Full Production Ingestion

The repository includes a 13-route benchmark sample (`amazon_last_mile_sample.json`) and a 30-route planned-vs-actual dataset (`mendeley_planned_vs_actual.csv`) to enable immediate out-of-the-box operation and automated testing.
The full 9,184-route Amazon Last Mile dataset is not bundled due to GitHub repository size limits and must be downloaded from AWS Open Data Registry for large-scale training.

When dataset files are absent, the application gracefully operates in **synthetic_demo** mode using an in-memory test fixture clearly labeled (`is_synthetic=True` on Dataset records, `data_mode="synthetic_demo"` in the ML model API).

### 2. ML Models: Limited Test Sample Size

Models evaluated on the 13-route benchmark sample return `evaluation_status: "low_sample_size"` with metrics rounded to 1 decimal place. When operated in synthetic_demo mode, no evaluation metrics are calculated and `/api/v1/metrics` returns `evaluation_status: "insufficient_data"` and `metrics: null` — never fabricated values.

### 3. Static Traffic Representation

The dataset does not include live GPS telemetry. Traffic factors are modeled
via service time variance and historical travel durations only.

### 4. Geographic Scope

Public datasets originate from U.S. metropolitan regions (Amazon) and specific
European urban courier networks (Mendeley). Model behavior in other geographies
is untested.

### 5. No Live Production Dispatch Integration

The platform is a decision-intelligence overlay with human-in-the-loop audit
logging. It does not directly control vehicle hardware or dispatch systems.

### 6. OR-Tools VRP Solver Assumptions

The optimization solver uses Haversine straight-line distance as a proxy for
actual road distance. Real road networks will produce different results. The
solver uses a 2-second time limit per route; complex routes may find only
heuristic (not globally optimal) solutions.

### 7. DuckDB OLAP Table is Append-Only on Re-Ingestion

`CREATE TABLE IF NOT EXISTS ... AS SELECT * FROM df` creates the DuckDB
`routes_olap` table only on first ingestion. User-triggered re-ingestion via
the API does not update the DuckDB table. This is a known limitation; a
full OLAP refresh on re-ingestion is a planned improvement.

### 8. Microservice Scope & Authentication Boundary

The current service is architected as an internal operational microservice designed to run inside a private VPC behind an API Gateway or Reverse Proxy (e.g. Envoy, Kong, or Traefik). Token authentication and RBAC are intended to be terminated at the edge gateway layer before traffic reaches internal decision endpoints.

### 9. Default SECRET_KEY

The default development SECRET_KEY is intended for local sandbox execution. It should be replaced with a cryptographically strong random key in production environments. The application logs a warning at startup when the default development key is detected.
