"""
ML model registry and metadata API.

Endpoints expose honest model information including:
  - data_mode (synthetic_demo vs real)
  - evaluation_status
  - actual computed metrics (or null with explanation)
  - feature names and architecture details

No fabricated metrics are exposed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.database import get_db
from app.ml.eta_model import ETAPredictionModel
from app.ml.deviation_model import RouteDeviationClassifier

router = APIRouter(tags=["ML Models & Evaluation"])

# Module-level singletons — initialized once per process.
eta_model = ETAPredictionModel()
dev_classifier = RouteDeviationClassifier()


@router.get("/models", response_model=List[Dict[str, Any]])
async def list_models(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns metadata for each active ML model.

    data_mode distinguishes synthetic_demo (default when real datasets are
    absent) from real (when trained on actual Amazon/Mendeley data).
    evaluation_status indicates whether evaluation metrics are available.
    """
    eta_meta = eta_model.get_metadata()
    dev_meta = dev_classifier.get_metadata()

    return [
        {
            "id": "MOD_ETA_01",
            "model_name": eta_meta["model_name"],
            "version": eta_meta["model_version"],
            "algorithm": eta_meta["algorithm"],
            "target": eta_meta["target_name"],
            "feature_names": eta_meta["feature_names"],
            "feature_count": eta_meta["feature_count"],
            "data_mode": eta_meta["data_mode"],
            "is_trained": eta_meta["is_trained"],
            "training_sample_count": eta_meta["training_sample_count"],
            "evaluation_status": eta_meta["evaluation_status"],
            "sample_size_warning": eta_meta.get("sample_size_warning"),
            "limitations": eta_meta["limitations"],
            "is_active": True,
        },
        {
            "id": "MOD_DEV_01",
            "model_name": dev_meta["model_name"],
            "version": dev_meta["model_version"],
            "algorithm": dev_meta["algorithm"],
            "target": dev_meta["target_name"],
            "feature_names": dev_meta["feature_names"],
            "feature_count": dev_meta["feature_count"],
            "data_mode": dev_meta["data_mode"],
            "is_trained": dev_meta["is_trained"],
            "training_sample_count": dev_meta["training_sample_count"],
            "evaluation_status": dev_meta["evaluation_status"],
            "sample_size_warning": dev_meta.get("sample_size_warning"),
            "limitations": dev_meta["limitations"],
            "is_active": True,
        },
    ]


@router.get("/metrics", response_model=Dict[str, Any])
async def get_model_metrics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns actual evaluation metrics for each model.

    When evaluation_status is "insufficient_data" or "not_evaluated",
    the metrics field is null and a clear explanation is provided.
    Fabricated/hard-coded metrics are never returned.
    """
    eta_meta = eta_model.get_metadata()
    dev_meta = dev_classifier.get_metadata()

    return {
        "eta_model": {
            "model_name": eta_meta["model_name"],
            "algorithm": eta_meta["algorithm"],
            "data_mode": eta_meta["data_mode"],
            "training_sample_count": eta_meta["training_sample_count"],
            "evaluation_sample_count": eta_meta["evaluation_sample_count"],
            "evaluation_status": eta_meta["evaluation_status"],
            "metrics": eta_meta["metrics"],
            "sample_size_warning": eta_meta.get("sample_size_warning"),
            "limitations": eta_meta["limitations"],
        },
        "deviation_model": {
            "model_name": dev_meta["model_name"],
            "algorithm": dev_meta["algorithm"],
            "data_mode": dev_meta["data_mode"],
            "training_sample_count": dev_meta["training_sample_count"],
            "evaluation_sample_count": dev_meta["evaluation_sample_count"],
            "evaluation_status": dev_meta["evaluation_status"],
            "metrics": dev_meta["metrics"],
            "sample_size_warning": dev_meta.get("sample_size_warning"),
            "limitations": dev_meta["limitations"],
        },
    }
