import os
import pandas as pd
from typing import List
from datetime import datetime, timezone
from app.ingestion.canonical import CanonicalRoute, CanonicalStop, CanonicalPackage

class MendeleyPlannedVsActualAdapter:
    """
    Adapter for Planned vs Actual Last-Mile Routes dataset.
    DOI: https://doi.org/10.17632/kkwgfvmtxn.1
    """
    @staticmethod
    def parse_data(file_path: str) -> List[CanonicalRoute]:
        canonical_routes: List[CanonicalRoute] = []

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Mendeley dataset file not found at {file_path}")

        df = pd.read_excel(file_path) if file_path.endswith(".xlsx") else pd.read_csv(file_path)

        # Standardize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        route_col = [c for c in df.columns if "route" in c][0] if any("route" in c for c in df.columns) else "route_id"

        grouped = df.groupby(route_col)

        for route_id, group in grouped:
            stops = []
            seq = 0
            for _, row in group.iterrows():
                seq += 1
                stop_id = str(row.get("stop_id", f"STOP_{route_id}_{seq}"))
                planned_seq = int(row.get("planned_sequence", seq))
                actual_seq = int(row.get("actual_sequence", seq))
                
                lat = float(row["lat"]) if "lat" in row and pd.notnull(row["lat"]) else None
                lng = float(row["lng"]) if "lng" in row and pd.notnull(row["lng"]) else None

                stops.append(CanonicalStop(
                    stop_id=stop_id,
                    route_id=str(route_id),
                    planned_sequence=planned_seq,
                    actual_sequence=actual_seq,
                    lat=lat,
                    lng=lng,
                    service_time_min=float(row.get("service_time_min", 5.0)),
                    packages=[CanonicalPackage(package_id=f"PKG_{stop_id}", stop_id=stop_id)]
                ))

            driver_id = str(group["driver_id"].iloc[0]) if "driver_id" in group.columns else f"DRV_{route_id}"
            p_dist = float(group["planned_distance"].iloc[0]) if "planned_distance" in group.columns else 28.4
            a_dist = float(group["actual_distance"].iloc[0]) if "actual_distance" in group.columns else 32.1
            p_dur = float(group["planned_duration"].iloc[0]) if "planned_duration" in group.columns else 180.0
            a_dur = float(group["actual_duration"].iloc[0]) if "actual_duration" in group.columns else 210.0

            canonical_routes.append(CanonicalRoute(
                route_id=f"MEND_{route_id}",
                dataset_name="Planned vs Actual Last-Mile Routes (Mendeley)",
                external_route_id=str(route_id),
                driver_id=driver_id,
                route_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                planned_distance_km=p_dist,
                actual_distance_km=a_dist,
                planned_duration_min=p_dur,
                actual_duration_min=a_dur,
                stops=stops
            ))

        return canonical_routes
