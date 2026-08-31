from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import Route, Stop
from app.schemas.schemas import OptimizeRouteRequestSchema, ScenarioRequestSchema
from app.optimization.vrp import VRPOptimizer
from app.simulation.simulator import ScenarioSimulator

router = APIRouter(prefix="/routes", tags=["Optimization & Simulation"])

@router.post("/{route_id}/optimize")
async def optimize_route(route_id: str, req: OptimizeRouteRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(Route).where(Route.id == route_id).options(selectinload(Route.stops))
    res = await db.execute(stmt)
    route = res.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    result = VRPOptimizer.optimize_route(route, route.stops, weights=req.objective_weights)
    return result

@router.post("/{route_id}/simulate")
async def simulate_scenario(route_id: str, req: ScenarioRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(Route).where(Route.id == route_id).options(selectinload(Route.stops))
    res = await db.execute(stmt)
    route = res.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    params = {
        "removed_stop_id": req.removed_stop_id,
        "vehicle_count": req.vehicle_count
    }
    result = ScenarioSimulator.run_scenario(route, route.stops, req.scenario_type, params)
    return result
