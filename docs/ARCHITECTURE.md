# System Architecture — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Architectural Principles

1. **Modular Monolith**: Simple, clean monorepo architecture avoiding unnecessary microservice overhead.
2. **Optimization + ML Prediction**: ML estimates uncertain outcomes (delay, deviation probability); the OR-Tools routing solver searches for shorter stop sequences within a time limit.
3. **Explicit Data Provenance**: Every dataset is tagged real or synthetic (`is_synthetic`), `GET /health` reports what is loaded, and missing source values stay unknown instead of being filled with defaults.

## Component Flow Diagram

```mermaid
flowchart TB
    USER[Dispatcher / Operations Manager]
    USER --> FE[Frontend: Next.js 14 + React + TypeScript]
    FE -->|REST / JSON| API[FastAPI Backend]

    API --> DATA[Data Layer]
    API --> ETA[ETA / Delay ML Predictor]
    API --> DEV[Route Deviation Classifier]
    API --> OPT[Google OR-Tools VRP Optimizer]
    API --> SIM[Scenario Simulator]
    API --> DEC[Decision Engine]
    API --> AUDIT[Audit Trail Logger]

    DATA --> PG[(PostgreSQL App DB)]
    DATA --> DUCK[DuckDB OLAP Engine]

    RAW[Bundled samples / public datasets] --> ING[Ingestion Pipeline] --> VAL[Quality Validator] --> CAN[Canonical Model]
    CAN --> DATA
```

## Layer Breakdown

- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, Recharts.
- **Backend API**: FastAPI, Async SQLAlchemy ORM, Pydantic V2 schemas.
- **Data Stores**: PostgreSQL 15 (relational application state) + DuckDB (OLAP analytical queries).
- **Optimization**: Google OR-Tools Routing Library (`pywrapcp`).
- **Machine Learning**: scikit-learn, Gradient Boosting Regressor, Random Forest Classifier.
