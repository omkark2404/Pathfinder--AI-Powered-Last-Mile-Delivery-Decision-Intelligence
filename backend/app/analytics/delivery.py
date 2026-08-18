import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import Route, RouteMetric, Delivery, Stop, Driver
from app.schemas.schemas import OverviewAnalyticsSchema

class DeliveryAnalytics:
    @staticmethod
    async def compute_overview_kpis(db: AsyncSession) -> OverviewAnalyticsSchema:
        """Computes system-wide delivery performance indicators."""
        # Query total routes & total stops
        route_stmt = select(Route)
        routes_res = await db.execute(route_stmt)
        routes = routes_res.scalars().all()
        
        total_routes = len(routes)
        if total_routes == 0:
            return OverviewAnalyticsSchema(
                total_routes=0,
                total_deliveries=0,
                on_time_delivery_rate=1.0,
                late_delivery_rate=0.0,
                avg_delay_minutes=0.0,
                p90_delay_minutes=0.0,
                p95_delay_minutes=0.0,
                avg_route_efficiency_pct=100.0,
                route_deviation_rate=0.0,
                high_risk_routes_count=0,
                optimization_opportunities_count=0
            )

        # Query metrics
        metrics_stmt = select(RouteMetric)
        metrics_res = await db.execute(metrics_stmt)
        metrics = metrics_res.scalars().all()

        deliv_stmt = select(Delivery)
        deliv_res = await db.execute(deliv_stmt)
        deliveries = deliv_res.scalars().all()
        total_deliveries = len(deliveries)

        delays = [d.delay_minutes for d in deliveries if d.delay_minutes > 0]
        avg_delay = float(np.mean(delays)) if delays else 0.0
        p90_delay = float(np.percentile(delays, 90)) if delays else 0.0
        p95_delay = float(np.percentile(delays, 95)) if delays else 0.0

        on_time_rates = [m.on_time_delivery_rate for m in metrics] if metrics else [1.0]
        avg_on_time = float(np.mean(on_time_rates))
        late_rate = round(1.0 - avg_on_time, 3)

        efficiencies = [m.route_efficiency_score for m in metrics] if metrics else [100.0]
        avg_efficiency = float(np.mean(efficiencies))

        # Deviations count
        deviations_count = sum(1 for r in routes if r.actual_distance_km and r.planned_distance_km and r.actual_distance_km > r.planned_distance_km * 1.1)
        deviation_rate = round(deviations_count / max(1, total_routes), 3)

        high_risk_count = sum(1 for m in metrics if m.on_time_delivery_rate < 0.85)

        return OverviewAnalyticsSchema(
            total_routes=total_routes,
            total_deliveries=total_deliveries,
            on_time_delivery_rate=round(avg_on_time, 3),
            late_delivery_rate=late_rate,
            avg_delay_minutes=round(avg_delay, 1),
            p90_delay_minutes=round(p90_delay, 1),
            p95_delay_minutes=round(p95_delay, 1),
            avg_route_efficiency_pct=round(avg_efficiency, 1),
            route_deviation_rate=deviation_rate,
            high_risk_routes_count=high_risk_count,
            optimization_opportunities_count=deviations_count + high_risk_count
        )

    @staticmethod
    async def get_driver_analytics(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Computes driver performance taking route difficulty into account.
        Avoids simplistic rankings per specification requirements.
        """
        drivers_stmt = select(Driver)
        res = await db.execute(drivers_stmt)
        drivers = res.scalars().all()
        
        result = []
        for d in drivers:
            # Fetch routes for driver
            routes_stmt = select(Route).where(Route.driver_id == d.id)
            r_res = await db.execute(routes_stmt)
            routes = r_res.scalars().all()
            
            route_count = len(routes)
            if route_count == 0:
                continue

            avg_stops = float(np.mean([r.total_stops for r in routes]))
            avg_distance = float(np.mean([r.planned_distance_km or 30.0 for r in routes]))
            
            # Difficulty score based on stop density and route length
            difficulty_index = round((avg_stops * 0.4) + (avg_distance * 0.6), 1)

            result.append({
                "driver_id": d.id,
                "external_driver_id": d.external_driver_id,
                "name": d.name,
                "routes_completed": route_count,
                "avg_stops_per_route": round(avg_stops, 1),
                "avg_distance_km": round(avg_distance, 1),
                "route_difficulty_index": difficulty_index,
                "adherence_rate": d.historical_adherence_rate,
                "avg_delay_min": d.historical_avg_delay_min,
                "performance_context": f"Completed {route_count} routes with avg difficulty score {difficulty_index}."
            })

        return result
