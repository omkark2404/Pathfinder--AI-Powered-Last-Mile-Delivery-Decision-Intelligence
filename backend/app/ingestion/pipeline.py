import os
import uuid
import datetime
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Tuple, Dict, Any

from app.core.config import settings
from app.core.database import get_duckdb_connection
from app.ingestion.canonical import CanonicalRoute, CanonicalStop, CanonicalPackage
from app.ingestion.amazon_adapter import AmazonLastMileAdapter
from app.ingestion.mendeley_adapter import MendeleyPlannedVsActualAdapter
from app.ingestion.validation import DataValidator
from app.models.models import (
    Dataset, IngestionRun, Driver, Route, Stop, Delivery,
    RouteMetric, RouteDeviation
)
from app.schemas.schemas import DataQualityReportSchema, IngestRequestSchema

class IngestionPipeline:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def run_ingestion(self, request: IngestRequestSchema) -> Tuple[Dataset, IngestionRun, DataQualityReportSchema]:
        """
        Full ingestion pipeline:
        RAW DATA -> Validation -> Normalization -> Database Persistence & DuckDB
        """
        run_id = str(uuid.uuid4())
        dataset_id = str(uuid.uuid4())
        started_at = datetime.datetime.now(datetime.timezone.utc)

        file_path = request.file_path
        if not file_path:
            # Check default locations inside data directory
            if request.dataset_name == "AMAZON_LAST_MILE":
                sample_p = os.path.join(settings.DATA_DIR, "amazon_last_mile_sample.json")
                orig_p = os.path.join(settings.DATA_DIR, "amazon_last_mile.json")
                file_path = sample_p if os.path.exists(sample_p) else orig_p
            else:
                file_path = os.path.join(settings.DATA_DIR, "mendeley_planned_vs_actual.csv")

        # Validate file existence
        if not os.path.exists(file_path):
            # Create synthetic test fixture if file missing, clearly labeled per spec
            sample_df = self._generate_fixture_df(request.dataset_name)
            report = DataValidator.validate_dataset(sample_df, request.dataset_name, file_path)
            report.issues.append("DATASET FILE MISSING: Using synthetic test fixture for schema validation.")
            canonical_routes = self._generate_fixture_canonical_routes(request.dataset_name)
            is_synthetic = True
        else:
            # Parse real dataset
            if request.dataset_name == "AMAZON_LAST_MILE":
                canonical_routes = AmazonLastMileAdapter.parse_data(file_path)
            else:
                canonical_routes = MendeleyPlannedVsActualAdapter.parse_data(file_path)
            
            # Read into dataframe for quality validation
            sample_df = pd.DataFrame([
                {
                    "route_id": r.route_id,
                    "driver_id": r.driver_id,
                    "planned_distance": r.planned_distance_km,
                    "actual_distance": r.actual_distance_km,
                    "planned_duration": r.planned_duration_min,
                    "actual_duration": r.actual_duration_min,
                    "stop_count": len(r.stops)
                } for r in canonical_routes
            ])
            report = DataValidator.validate_dataset(sample_df, request.dataset_name, file_path)
            is_synthetic = False

        # Create Dataset record
        dataset_record = Dataset(
            id=dataset_id,
            name=request.dataset_name,
            source_url="https://registry.opendata.aws/amazon-last-mile-challenges/" if "AMAZON" in request.dataset_name else "https://data.mendeley.com/datasets/kkwgfvmtxn",
            doi="https://doi.org/10.17632/kkwgfvmtxn.1" if "MENDELEY" in request.dataset_name else None,
            license="CC BY 4.0",
            version="1.0",
            download_timestamp=started_at,
            file_hash=report.provenance_hash,
            row_count=report.total_rows,
            route_count=len(canonical_routes),
            stop_count=sum(len(r.stops) for r in canonical_routes),
            driver_count=len(set(r.driver_id for r in canonical_routes if r.driver_id)),
            validation_status=report.validation_status,
            is_synthetic=is_synthetic
        )
        self.db.add(dataset_record)

        # Persist Routes, Drivers, Stops, Deliveries
        drivers_map: Dict[str, Driver] = {}
        
        for c_route in canonical_routes:
            # Driver setup
            driver_id = c_route.driver_id or "DRV_UNKNOWN"
            if driver_id not in drivers_map:
                driver_obj = Driver(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset_id,
                    external_driver_id=driver_id,
                    name=f"Driver {driver_id}",
                    # Neutral defaults — will be updated once real historical data is available.
                    # Model schema defaults: adherence_rate=1.0, avg_delay_min=0.0
                    historical_adherence_rate=1.0,
                    historical_avg_delay_min=0.0
                )
                self.db.add(driver_obj)
                drivers_map[driver_id] = driver_obj

            db_driver = drivers_map[driver_id]

            # Route object
            route_db_id = str(uuid.uuid4())
            route_obj = Route(
                id=route_db_id,
                dataset_id=dataset_id,
                external_route_id=c_route.external_route_id,
                driver_id=db_driver.id,
                vehicle_id=c_route.vehicle_id or "VAN_01",
                depot_location=c_route.depot_location or {"lat": 37.7749, "lng": -122.4194},
                route_date=c_route.route_date or "2026-08-12",
                planned_distance_km=c_route.planned_distance_km or 35.0,
                actual_distance_km=c_route.actual_distance_km or 38.5,
                planned_duration_min=c_route.planned_duration_min or 240.0,
                actual_duration_min=c_route.actual_duration_min or 265.0,
                total_stops=len(c_route.stops),
                status="COMPLETED"
            )
            self.db.add(route_obj)

            # Stops & Deliveries
            late_stops_count = 0
            for c_stop in c_route.stops:
                stop_db_id = str(uuid.uuid4())
                
                # Check for stop delay / deviation
                is_reordered = c_stop.actual_sequence is not None and c_stop.actual_sequence != c_stop.planned_sequence
                if is_reordered:
                    late_stops_count += 1

                stop_obj = Stop(
                    id=stop_db_id,
                    route_id=route_db_id,
                    external_stop_id=c_stop.stop_id,
                    planned_sequence=c_stop.planned_sequence,
                    actual_sequence=c_stop.actual_sequence or c_stop.planned_sequence,
                    lat=c_stop.lat,
                    lng=c_stop.lng,
                    address=c_stop.address or f"Stop Location #{c_stop.planned_sequence}",
                    service_time_min=c_stop.service_time_min,
                    status="DELIVERED"
                )
                self.db.add(stop_obj)

                # Package deliveries.
                # delay_minutes is 0.0 when actual arrival times are unavailable.
                # is_late is inferred from stop sequence reordering as a proxy;
                # accurate lateness requires planned_arrival vs actual_arrival timestamps.
                for pkg in c_stop.packages:
                    deliv_obj = Delivery(
                        id=str(uuid.uuid4()),
                        stop_id=stop_db_id,
                        package_id=pkg.package_id,
                        weight_kg=pkg.weight_kg or 2.5,
                        volume_m3=pkg.volume_m3 or 0.015,
                        priority="NORMAL",
                        is_late=is_reordered,
                        delay_minutes=0.0  # Set to 0.0; actual delay requires arrival timestamps
                    )
                    self.db.add(deliv_obj)

            # Route Metrics
            dist_var = round((c_route.actual_distance_km or 0.0) - (c_route.planned_distance_km or 0.0), 2)
            dur_var = round((c_route.actual_duration_min or 0.0) - (c_route.planned_duration_min or 0.0), 2)
            on_time_rate = round(max(0.0, 1.0 - (late_stops_count / max(1, len(c_route.stops)))), 2)

            route_metric = RouteMetric(
                id=str(uuid.uuid4()),
                route_id=route_db_id,
                distance_variance_km=dist_var,
                duration_variance_min=dur_var,
                on_time_delivery_rate=on_time_rate,
                late_delivery_count=late_stops_count,
                route_efficiency_score=round(max(50.0, 100.0 - (dist_var * 2) - (dur_var * 0.5)), 1)
            )
            self.db.add(route_metric)

            # Route Deviation
            dev_pct = round((dist_var / max(1.0, c_route.planned_distance_km or 1.0)) * 100.0, 1)
            is_mat_dev = dev_pct > 10.0 or late_stops_count > 1
            
            route_deviation = RouteDeviation(
                id=str(uuid.uuid4()),
                route_id=route_db_id,
                sequence_similarity_index=round(1.0 - (late_stops_count / max(1, len(c_route.stops))), 2),
                stop_reorder_count=late_stops_count,
                additional_distance_km=max(0.0, dist_var),
                additional_duration_min=max(0.0, dur_var),
                deviation_percentage=dev_pct,
                is_material_deviation=is_mat_dev,
                explanation=f"{late_stops_count} stops reordered from planned sequence. Distance increased by {dist_var} km (+{dev_pct}%)."
            )
            self.db.add(route_deviation)

        # Record Ingestion Run
        ingest_run = IngestionRun(
            id=run_id,
            dataset_id=dataset_id,
            status="SUCCESS" if report.validation_status != "CRITICAL" else "WARNING",
            started_at=started_at,
            completed_at=datetime.datetime.now(datetime.timezone.utc),
            quality_report=report.model_dump(),
            error_message="; ".join(report.issues) if report.issues else None
        )
        self.db.add(ingest_run)

        await self.db.commit()

        # Update DuckDB analytical engine
        self._export_to_duckdb(dataset_id, canonical_routes)

        return dataset_record, ingest_run, report

    def _export_to_duckdb(self, dataset_id: str, canonical_routes: List[CanonicalRoute]):
        """Populates DuckDB parquet analytical tables for fast OLAP queries."""
        try:
            conn = get_duckdb_connection()
            rows = []
            for r in canonical_routes:
                rows.append({
                    "dataset_id": dataset_id,
                    "route_id": r.route_id,
                    "driver_id": r.driver_id,
                    "planned_distance_km": r.planned_distance_km,
                    "actual_distance_km": r.actual_distance_km,
                    "planned_duration_min": r.planned_duration_min,
                    "actual_duration_min": r.actual_duration_min,
                    "stop_count": len(r.stops)
                })
            df = pd.DataFrame(rows)
            # CREATE OR REPLACE ensures re-ingestion always reflects the latest data.
            conn.execute("CREATE OR REPLACE TABLE routes_olap AS SELECT * FROM df")
            conn.close()
        except Exception:
            pass

    def _generate_fixture_df(self, name: str) -> pd.DataFrame:
        """Generates synthetic test fixture dataframe clearly marked per specification."""
        return pd.DataFrame([
            {
                "route_id": f"FIX_{i}",
                "driver_id": f"DRV_{i%3}",
                "planned_distance": 30.0 + i,
                "actual_distance": 32.5 + i*1.2,
                "planned_duration": 180 + i*10,
                "actual_duration": 195 + i*12,
                "stop_count": 8 + i
            } for i in range(5)
        ])

    def _generate_fixture_canonical_routes(self, dataset_name: str) -> List[CanonicalRoute]:
        """Generates 5 realistic sample routes for demonstration when raw files are not placed."""
        routes = []
        depots = [
            {"lat": 37.7749, "lng": -122.4194, "address": "San Francisco Central Hub"},
            {"lat": 34.0522, "lng": -118.2437, "address": "Los Angeles Logistics Depot"},
            {"lat": 40.7128, "lng": -74.0060, "address": "New York Distribution Center"}
        ]
        
        for i in range(1, 6):
            depot = depots[(i-1) % len(depots)]
            stops = []
            # 8 stops per route
            base_lat, base_lng = depot["lat"], depot["lng"]
            for s in range(1, 9):
                # Introduce deliberate reordering in stop 3 and 4 for routes 2 and 4
                actual_seq = s
                if i in [2, 4] and s == 3:
                    actual_seq = 4
                elif i in [2, 4] and s == 4:
                    actual_seq = 3
                    
                stop_lat = base_lat + (s * 0.012)
                stop_lng = base_lng + (s * 0.015)
                
                stops.append(CanonicalStop(
                    stop_id=f"STOP_{i}_{s}",
                    route_id=f"RT_DEMO_0{i}",
                    planned_sequence=s,
                    actual_sequence=actual_seq,
                    lat=stop_lat,
                    lng=stop_lng,
                    address=f"{100 + s*10} Main St, Stop #{s}",
                    service_time_min=6.0,
                    packages=[
                        CanonicalPackage(package_id=f"PKG_{i}_{s}_A", stop_id=f"STOP_{i}_{s}", weight_kg=3.2, volume_m3=0.02)
                    ]
                ))
                
            p_dist = 28.5 + (i * 4.0)
            a_dist = p_dist * (1.15 if i in [2, 4] else 1.03)
            p_dur = 160.0 + (i * 20.0)
            a_dur = p_dur * (1.22 if i in [2, 4] else 1.05)

            routes.append(CanonicalRoute(
                route_id=f"RT_DEMO_0{i}",
                dataset_name=dataset_name,
                external_route_id=f"ROUTE_EXT_100{i}",
                driver_id=f"DRV_00{((i-1)%3)+1}",
                vehicle_id=f"VAN_0{((i-1)%3)+1}",
                depot_location=depot,
                route_date=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
                planned_distance_km=round(p_dist, 2),
                actual_distance_km=round(a_dist, 2),
                planned_duration_min=round(p_dur, 1),
                actual_duration_min=round(a_dur, 1),
                stops=stops
            ))
        return routes
