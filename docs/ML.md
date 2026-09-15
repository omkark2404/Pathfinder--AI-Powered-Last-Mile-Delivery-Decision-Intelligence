# Machine Learning Architecture — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Data Modes

| Mode | Description |
|---|---|
| `synthetic_demo` | Default. 5-sample benchmark fixture. No real evaluation metrics available. |
| `real` | Set after training on real Amazon/Mendeley data. Real metrics exposed. |

The current API always returns `data_mode: "synthetic_demo"` and
`evaluation_status: "insufficient_data"` until real data is provided.

## Temporal Leakage Prevention

All features must be information available at dispatch time T₀ (route start):

**Forbidden inputs** (actual outcomes — never used as features):
- `actual_distance_km`
- `actual_duration_min`
- `actual_arrival` times
- Any stop-level outcome measured after departure

**The `features.py` module is the canonical feature contract** shared by both
models. The `FEATURE_NAMES` list defines the feature order and must be kept in
sync with model training and inference.

## Feature Vector (9 features, in order)

| # | Feature | Description |
|---|---|---|
| 1 | `stop_count` | Total stops on route |
| 2 | `planned_distance_km` | Planned route distance |
| 3 | `planned_duration_min` | Planned total duration |
| 4 | `avg_stop_distance_km` | Mean inter-stop distance estimate |
| 5 | `avg_stop_duration_min` | Mean per-stop planned duration |
| 6 | `driver_adherence_rate` | Driver historical adherence [0..1] |
| 7 | `driver_historical_delay_min` | Driver historical mean delay (min) |
| 8 | `time_window_pressure` | Mean time-window tightness score |
| 9 | `route_complexity_score` | Composite complexity heuristic |

## Model 1: ETA Delay Predictor (`ETAPredictionModel`)

- **Task**: Predict `delay_minutes` (continuous)
- **Algorithm**: `GradientBoostingRegressor` (sklearn, n_estimators=50, max_depth=3, random_state=42)
- **Baseline**: `LinearRegression` (sklearn)
- **Version**: v1.3.0
- **Evaluation metrics** (real-data mode): MAE, RMSE, Median AE, P90 error, Bias
- **Late probability**: sigmoid(delay − 15 min / 5 min) — not a calibrated probability

## Model 2: Route Deviation Classifier (`RouteDeviationClassifier`)

- **Task**: Binary prediction of `is_material_deviation` (0 / 1)
- **Algorithm**: `RandomForestClassifier` (sklearn, n_estimators=30, max_depth=4, random_state=42)
- **Version**: v1.2.0
- **Evaluation metrics** (real-data mode): Precision, Recall, F1, PR-AUC
- **PR-AUC** is computed with `sklearn.metrics.average_precision_score` using actual probabilities — never hard-coded

## Composite Risk Scoring Formula

```text
Risk Score (0..100) =
  (late_probability × 35) +
  (min(1.0, delay_min / 60) × 25) +
  (deviation_probability × 20) +
  (min(1.0, tw_pressure / 50) × 10) +
  (min(1.0, complexity / 50) × 10)
```

### Risk Level Thresholds

| Score | Level |
|---|---|
| 0–20 | LOW |
| 21–50 | MEDIUM |
| 51–75 | HIGH |
| 76–100 | CRITICAL |

## Enabling Real-Data Mode

1. Verify or place dataset files:
   - `./data/amazon_last_mile_sample.json` (or full `./data/amazon_last_mile.json`)
   - `./data/mendeley_planned_vs_actual.csv`

2. Trigger ingestion: `POST /api/v1/datasets/ingest`

3. Train models on ingested data using `ETAPredictionModel.train(X, y, data_mode="real")`

4. Evaluate: `ETAPredictionModel.evaluate(X_test, y_test)`

5. Real metrics will appear at `GET /api/v1/metrics`
