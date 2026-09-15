# System Architecture — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Architectural Principles

1. **Modular Monolith**: Simple, clean monorepo architecture avoiding unnecessary microservice overhead.
2. **Deterministic Optimization + ML Prediction**: ML predicts uncertain outcomes (delay, deviation probability); deterministic OR-Tools algorithms calculate exact optimal routes.
3. **No Synthetic Data in Production ML**: Models train and evaluate strictly on real-world historical delivery data.

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

    RAW[Real Public Delivery Datasets] --> ING[Ingestion Pipeline] --> VAL[Quality Validator] --> CAN[Canonical Model]
    CAN --> DATA
```

## Layer Breakdown

- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, Recharts.
- **Backend API**: FastAPI, Async SQLAlchemy ORM, Pydantic V2 schemas.
- **Data Stores**: PostgreSQL 15 (relational application state) + DuckDB (OLAP analytical queries).
- **Optimization**: Google OR-Tools Routing Library (`pywrapcp`).
- **Machine Learning**: scikit-learn, Gradient Boosting Regressor, Random Forest Classifier.
