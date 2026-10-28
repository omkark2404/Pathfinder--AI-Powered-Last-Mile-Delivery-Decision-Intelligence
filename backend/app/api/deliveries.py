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
from app.ml.registry import eta_model, score_route
from app.analytics.delivery import DeliveryAnalytics

router = APIRouter(tags=["Deliveries & Risk"])


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

    scored = score_route(route, driver, route.stops)
    if scored is None:
        # Nothing is persisted: a score built from default features would be made up.
        return {
            "route_id": route.id,
            "external_route_id": route.external_route_id,
            "data_complete": False,
            "detail": "Route has no planned distance/duration in the source data, so it cannot be risk-scored.",
            "data_mode": eta_model.get_metadata()["data_mode"],
        }

    # Persist Prediction record for audit traceability
    prediction_record = Prediction(
        id=str(uuid.uuid4()),
        route_id=route.id,
        predicted_delay_min=round(float(scored["predicted_delay_min"]), 2),
        late_probability=round(float(scored["late_probability"]), 4),
        deviation_probability=round(float(scored["deviation_probability"]), 4),
        composite_risk_score=round(float(scored["composite_risk_score"]), 2),
        risk_level=scored["risk_level"],
        feature_snapshot=scored["features"],
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
        "risk_level": prediction_record.risk_level,
        "data_complete": True,
        "data_mode": eta_model.get_metadata()["data_mode"],
        "features": scored["features"],
    }


@router.get("/risk-scores")
async def list_route_risk_scores(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Composite risk for every route, computed with the same models as /routes/predict-risk.
    Read-only: nothing is persisted. Routes without planning data are returned unscored.
    """
    stmt = select(Route).options(selectinload(Route.stops), selectinload(Route.driver))
    routes = (await db.execute(stmt)).scalars().all()
    results = []
    for r in routes:
        scored = score_route(r, r.driver, r.stops)
        results.append({
            "route_id": r.id,
            "external_route_id": r.external_route_id,
            "total_stops": r.total_stops,
            "planned_distance_km": r.planned_distance_km,
            "data_complete": scored is not None,
            "composite_risk_score": scored["composite_risk_score"] if scored else None,
            "risk_level": scored["risk_level"] if scored else None,
            "predicted_delay_min": scored["predicted_delay_min"] if scored else None,
            "deviation_probability": scored["deviation_probability"] if scored else None,
        })
    return results
