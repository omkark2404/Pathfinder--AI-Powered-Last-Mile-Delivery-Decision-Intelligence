from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.models import Route, Stop, Driver
from app.schemas.schemas import RouteSchema, RouteDetailSchema
from app.analytics.deviation import RouteDeviationAnalyzer

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.get("", response_model=List[RouteSchema])
async def list_routes(db: AsyncSession = Depends(get_db)):
    stmt = select(Route).options(
        selectinload(Route.metrics),
        selectinload(Route.deviation)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{route_id}", response_model=RouteDetailSchema)
async def get_route(route_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Route).where(Route.id == route_id).options(
        selectinload(Route.stops).selectinload(Stop.deliveries),
        selectinload(Route.metrics),
        selectinload(Route.deviation)
    )
    res = await db.execute(stmt)
    route = res.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.get("/{route_id}/performance")
async def get_route_performance(route_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Route).where(Route.id == route_id).options(
        selectinload(Route.metrics),
        selectinload(Route.stops)
    )
    res = await db.execute(stmt)
    route = res.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    m = route.metrics
    return {
        "route_id": route.id,
        "external_route_id": route.external_route_id,
        "planned_distance_km": route.planned_distance_km,
        "actual_distance_km": route.actual_distance_km,
        "planned_duration_min": route.planned_duration_min,
        "actual_duration_min": route.actual_duration_min,
        "distance_variance_km": m.distance_variance_km if m else 0.0,
        "duration_variance_min": m.duration_variance_min if m else 0.0,
        "on_time_delivery_rate": m.on_time_delivery_rate if m else 1.0,
        "late_delivery_count": m.late_delivery_count if m else 0,
        "route_efficiency_score": m.route_efficiency_score if m else 100.0
    }

@router.get("/{route_id}/deviation")
async def get_route_deviation(route_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Route).where(Route.id == route_id).options(selectinload(Route.stops))
    res = await db.execute(stmt)
    route = res.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    return RouteDeviationAnalyzer.analyze_route_deviation(route, route.stops)
