# System Limitations & Boundary Conditions — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Known Limitations

### 1. Prototype models, synthetic outcome data

The API models are fitted on 5 hand-written rows and report `insufficient_data`. The only bundled outcome data is the synthetic Mendeley-schema fixture (`data/mendeley_synthetic_fixture.csv`). Offline cross-validation (`backend/scripts/train_eval.py`) runs on that fixture and verifies the pipeline only. See `docs/EVALUATION.md`.

### 2. The Amazon sample has no outcomes

`data/amazon_last_mile_sample.json` (13 real routes, CC BY-NC 4.0) has stop locations, packages and service times, but no actual visit order, distances or durations. Those routes are used for optimization only: they are not compared against a plan, risk-scored, or used for training. The official actual-sequence file is not parsed yet.

### 3. No lateness data

Neither bundled dataset has planned vs actual arrival timestamps. `Delivery.is_late` is stored as unknown, delay statistics are reported as unavailable, and the overview's "Stops in Planned Order" measures sequence adherence, not punctuality.

### 4. Optimizer assumptions

The solver minimizes straight-line (Haversine) distance. Road networks, time windows, vehicle capacity and duration limits are not modeled, and duration savings are scaled estimates. The 2-second time limit is enough for tens of stops; the ~190-stop Amazon routes hit it, so their tours are the best found, not proven optimal. The multi-vehicle scenario is a rough approximation.

### 5. Geographic scope

The Amazon sample covers U.S. metropolitan stations; the fixture's coordinates are around Oslo. Behaviour on other geographies is untested.

### 6. No live dispatch integration

The platform is a decision-support overlay with human-in-the-loop audit logging. It does not control vehicles or dispatch systems.

### 7. DuckDB export is write-only

Each ingestion replaces the DuckDB `routes_olap` table (`CREATE OR REPLACE`), so it only holds the most recently ingested dataset, and nothing queries it yet.

### 8. No authentication

All endpoints, including ingestion, predictions and dispatcher decisions, are unauthenticated, and the audit `user_id` is supplied by the client. Put the service behind an authenticating gateway before exposing it beyond a demo.

### 9. Default SECRET_KEY

The default development SECRET_KEY is intended for local sandbox execution. It should be replaced with a cryptographically strong random key in production environments. The application logs a warning at startup when the default development key is detected.
