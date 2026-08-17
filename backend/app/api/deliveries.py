import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.models import Route, Delivery, Driver, Stop, Prediction
from app.schemas.schemas import RiskPredictionRequestSchema, OverviewAnalyticsSchema
from app.ml.features import FeatureEngineer
from app.ml.eta_model import ETAPredictionModel
from app.ml.deviation_model import RouteDeviationClassifier
from app.risk.scorer import DeliveryRiskScorer
from app.analytics.delivery import DeliveryAnalytics

router = APIRouter(tags=["Deliveries & Risk"])

eta_model = ETAPredictionModel()
dev_classifier = RouteDeviationClassifier()


@router.get("/overview", response_model=OverviewAnalyticsSchema)
async def get_overview_analytics(db: AsyncSession = Depends(get_db)):
    """Fleet-level KPI analytics computed from ingested route data."""
    return await DeliveryAnalytics.compute_overview_kpis(db)


@router.get("/deliveries")
async def list_deliveries(db: AsyncSession = Depends(get_db)):
    """List deliveries (limit 100)."""
    res = await db.execute(select(Delivery).limit(100))
    return res.scalars().all()


@router.get("/deliveries/{delivery_id}")
async def get_delivery(delivery_id: str, db: AsyncSession = Depends(get_db)):
    """
    Single delivery detail by ID.
    """
    stmt = select(Delivery).where(Delivery.id == delivery_id)
    res = await db.execute(stmt)
    delivery = res.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail=f"Delivery '{delivery_id}' not found")
    return delivery


@router.post("/routes/predict-risk")
async def predict_route_risk(req: RiskPredictionRequestSchema, db: AsyncSession = Depends(get_db)):
    """
    Predicts ETA delay and composite risk score for a route.
    Persists a Prediction record to the database for audit traceability.
    """
    stmt = select(Route).where(Route.id == req.route_id).options(
        selectinload(Route.stops)
    )
    res = await db.execute(stmt)
    route = res.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Load driver separately (lazy="raise" on the relationship)
    driver = None
    if route.driver_id:
        d_res = await db.execute(select(Driver).where(Driver.id == route.driver_id))
        driver = d_res.scalar_one_or_none()

    stops = route.stops
    features = FeatureEngineer.extract_route_features(route, driver, stops)
    pred_delay, late_prob = eta_model.predict_delay(features)
    dev_prob = dev_classifier.predict_deviation_probability(features)

    risk_score, risk_level = DeliveryRiskScorer.calculate_risk(
        pred_delay, late_prob, dev_prob,
        features["time_window_pressure"],
        features["route_complexity_score"],
    )

    # Persist Prediction record for audit traceability
    prediction_record = Prediction(
        id=str(uuid.uuid4()),
        route_id=route.id,
        predicted_delay_min=round(float(pred_delay), 2),
        late_probability=round(float(late_prob), 4),
        deviation_probability=round(float(dev_prob), 4),
        composite_risk_score=round(float(risk_score), 2),
        risk_level=risk_level,
        feature_snapshot=features,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(prediction_record)
    await db.commit()

    return {
        "prediction_id": prediction_record.id,
        "route_id": route.id,
        "external_route_id": route.external_route_id,
        "predicted_delay_min": prediction_record.predicted_delay_min,
        "late_probability": prediction_record.late_probability,
        "deviation_probability": prediction_record.deviation_probability,
        "composite_risk_score": prediction_record.composite_risk_score,
        "risk_level": risk_level,
        "data_mode": eta_model.get_metadata()["data_mode"],
        "features": features,
    }
