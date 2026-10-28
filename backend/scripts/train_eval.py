"""
Offline cross-validated evaluation of the ETA and deviation models on the data in DATA_DIR.

    cd backend && python scripts/train_eval.py

Only routes with outcome data (planned and actual distance/duration plus an actual visit
order) can be evaluated. The bundled Amazon sample has none, so with the bundled files this
evaluates on the 30-route SYNTHETIC Mendeley-schema fixture only: the numbers check that the
pipeline runs end to end and are not evidence of real-world accuracy.

Writes docs/eval_results.json.
"""

import asyncio
import json
import os
import sys

import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault("DATABASE_URL", "")

import sklearn  # noqa: E402
from sklearn.base import clone  # noqa: E402
from sklearn.dummy import DummyRegressor  # noqa: E402
from sklearn.linear_model import LinearRegression  # noqa: E402
from sklearn.metrics import average_precision_score, f1_score, mean_absolute_error, precision_score, recall_score  # noqa: E402
from sklearn.model_selection import KFold, StratifiedKFold  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.ingestion.pipeline import IngestionPipeline  # noqa: E402
from app.ml.deviation_model import RouteDeviationClassifier  # noqa: E402
from app.ml.eta_model import ETAPredictionModel  # noqa: E402
from app.ml.features import FEATURE_NAMES, FeatureEngineer  # noqa: E402
from app.models.models import Dataset, Route  # noqa: E402
from app.schemas.schemas import IngestRequestSchema  # noqa: E402

SEED = 42
N_SPLITS = 5
MIN_ROUTES = 10
OUT_PATH = os.path.join(os.path.dirname(BACKEND_DIR), "docs", "eval_results.json")


async def load_routes():
    """Ingest DATA_DIR into a throwaway in-memory database and return (routes, dataset rows)."""
    IngestionPipeline._export_to_duckdb = lambda *args, **kwargs: None  # no side files
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        for name in ("AMAZON_LAST_MILE", "MENDELEY_PLANNED_VS_ACTUAL"):
            await IngestionPipeline(session).run_ingestion(IngestRequestSchema(dataset_name=name))
        routes = (await session.execute(
            select(Route).options(selectinload(Route.stops), selectinload(Route.driver), selectinload(Route.deviation))
        )).scalars().all()
        datasets = (await session.execute(select(Dataset))).scalars().all()
    return routes, datasets


def mean_std(values):
    return {"mean": round(float(np.mean(values)), 3), "std": round(float(np.std(values)), 3)}


def evaluate(X, y_delay, y_dev):
    eta = clone(ETAPredictionModel().candidate_model)
    dev = clone(RouteDeviationClassifier().model)

    mae = {"gradient_boosting": [], "linear_regression": [], "mean_baseline": []}
    for train, test in KFold(N_SPLITS, shuffle=True, random_state=SEED).split(X):
        for key, model in (("gradient_boosting", clone(eta)), ("linear_regression", LinearRegression()),
                           ("mean_baseline", DummyRegressor(strategy="mean"))):
            model.fit(X[train], y_delay[train])
            mae[key].append(mean_absolute_error(y_delay[test], model.predict(X[test])))

    minority = int(min(y_dev.sum(), len(y_dev) - y_dev.sum()))
    classification = {"status": "insufficient_class_variety", "positives": int(y_dev.sum())}
    if minority >= 2:
        folds = min(N_SPLITS, minority)
        scores = {"pr_auc": [], "pr_auc_baseline_prevalence": [], "precision": [], "recall": [], "f1": []}
        for train, test in StratifiedKFold(folds, shuffle=True, random_state=SEED).split(X, y_dev):
            model = clone(dev).fit(X[train], y_dev[train])
            proba = model.predict_proba(X[test])[:, 1]
            pred = (proba >= 0.5).astype(int)
            scores["pr_auc"].append(average_precision_score(y_dev[test], proba))
            scores["pr_auc_baseline_prevalence"].append(float(y_dev[test].mean()))
            scores["precision"].append(precision_score(y_dev[test], pred, zero_division=0))
            scores["recall"].append(recall_score(y_dev[test], pred, zero_division=0))
            scores["f1"].append(f1_score(y_dev[test], pred, zero_division=0))
        classification = {
            "status": "evaluated",
            "cv": f"StratifiedKFold(n_splits={folds}, shuffle=True, random_state={SEED})",
            "positives": int(y_dev.sum()),
            "metrics": {k: mean_std(v) for k, v in scores.items()},
        }

    return {
        "eta_delay_minutes": {
            "target": "actual_duration_min - planned_duration_min (route level)",
            "cv": f"KFold(n_splits={N_SPLITS}, shuffle=True, random_state={SEED})",
            "mae": {k: mean_std(v) for k, v in mae.items()},
        },
        "route_deviation": {
            "target": "is_material_deviation: distance > 10% over plan or Kendall-tau similarity < 0.85",
            **classification,
        },
    }


def main():
    routes, datasets = asyncio.run(load_routes())
    names = {d.id: d for d in datasets}
    evaluable = [r for r in routes if r.deviation is not None]
    evaluated_sets = {names[r.dataset_id].name for r in evaluable}

    result = {
        "generated_by": "python backend/scripts/train_eval.py",
        "data_dir": os.path.relpath(settings.DATA_DIR, os.path.dirname(BACKEND_DIR)),
        "sklearn_version": sklearn.__version__,
        "datasets": [
            {"name": d.name, "is_synthetic": d.is_synthetic, "routes": d.route_count,
             "routes_with_outcomes": sum(1 for r in evaluable if r.dataset_id == d.id)}
            for d in datasets
        ],
        "evaluated_routes": len(evaluable),
        "evaluated_on_synthetic_data": any(d.is_synthetic for d in datasets if d.name in evaluated_sets),
    }

    if len(evaluable) < MIN_ROUTES:
        result["status"] = "insufficient_data"
    else:
        X = np.array([[FeatureEngineer.extract_route_features(r, r.driver, r.stops)[k] for k in FEATURE_NAMES]
                      for r in evaluable])
        y_delay = np.array([r.actual_duration_min - r.planned_duration_min for r in evaluable])
        y_dev = np.array([int(r.deviation.is_material_deviation) for r in evaluable])
        result["status"] = "evaluated"
        result["constant_features"] = [FEATURE_NAMES[i] for i in range(X.shape[1]) if np.ptp(X[:, i]) == 0]
        result.update(evaluate(X, y_delay, y_dev))

    if result["evaluated_on_synthetic_data"]:
        result["warning"] = ("Evaluated on a synthetic fixture. These numbers verify the pipeline; "
                             "they are not real-world model performance.")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
