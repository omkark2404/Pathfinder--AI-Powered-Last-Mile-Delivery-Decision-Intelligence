# Model & Optimization Evaluation — Pathfinder Last-Mile Decision Intelligence

> [!CAUTION]
> No real-world model performance is claimed. The only outcome data in the repository is a **synthetic** fixture, so the numbers below check that the evaluation pipeline runs end to end.

## 1. What is deployed

Both API models (`ETAPredictionModel`, `RouteDeviationClassifier`) are fitted at startup on 5 hand-written rows. `GET /api/v1/metrics` therefore returns `metrics: null` and `evaluation_status: "insufficient_data"`.

## 2. Offline evaluation

```bash
cd backend
python scripts/train_eval.py   # writes docs/eval_results.json
```

The script:
1. Ingests `data/` into a throwaway in-memory database with the normal pipeline.
2. Keeps only routes with outcome data: planned and actual distance/duration plus the actual visit order. With the bundled files that is the 30-route synthetic Mendeley-schema fixture; the 13 Amazon sample routes have no outcomes.
3. Builds the 9 dispatch-time features (`backend/app/ml/features.py`) and two targets:
   - **Delay**: actual − planned route duration (minutes)
   - **Material deviation**: distance more than 10% over plan, or Kendall-tau sequence similarity below 0.85 (`backend/app/analytics/deviation.py`)
4. Runs 5-fold cross-validation (seed 42) with the same hyperparameters as the API models, alongside baselines.
5. Records dataset provenance, constant features, folds, seed and sklearn version in `docs/eval_results.json`.

The bundled fixture has no dates or driver history, so the folds are random rather than temporal. With real data, split by date or by driver instead.

## 3. Current output (synthetic fixture, n = 30)

| Task | Metric (mean ± std over folds) | Model | Baselines |
|---|---|---|---|
| Route delay | MAE (min) | Gradient boosting 30.3 ± 16.9 | Predict the mean 33.2 ± 4.9 · Linear regression 35.2 ± 8.1 |
| Material deviation | PR-AUC | Random forest 0.73 ± 0.06 | Prevalence 0.37 ± 0.07 |
| Material deviation | Precision / Recall / F1 at 0.5 | 0.60 / 0.37 / 0.43 | — |

Three of the nine features (driver adherence, driver historical delay, time-window pressure) are constant on this data. Gradient boosting is not clearly better than predicting the mean. These numbers describe a generated fixture and should not be quoted as model accuracy.

## 4. Route optimization

- **Solver**: OR-Tools routing library (`pywrapcp`), `PATH_CHEAPEST_ARC` first solution, 2 s time limit
- **Objective**: minimize straight-line (Haversine) distance only
- **Baseline**: the planned stop order measured with the same distance matrix. Routes whose source data has no dispatch plan (the Amazon sample) get no baseline and no savings figure.
- **Duration**: estimated by scaling planned duration with the distance saved; flagged `duration_is_estimate` in the API
- **Tests**: `backend/tests/test_core_algorithms.py` checks the solver against a 3-stop instance with a known optimum
