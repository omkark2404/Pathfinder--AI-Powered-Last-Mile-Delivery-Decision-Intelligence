import os
import pandas as pd
from typing import List
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
                actual_seq = int(row["actual_sequence"]) if pd.notnull(row.get("actual_sequence")) else None
                
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

            def first(col):
                """Route-level value repeated on every stop row; None when the column is absent."""
                if col in group.columns and pd.notnull(group[col].iloc[0]):
                    return group[col].iloc[0]
                return None

            driver_id = str(first("driver_id")) if first("driver_id") is not None else f"DRV_{route_id}"
            p_dist, a_dist = first("planned_distance"), first("actual_distance")
            p_dur, a_dur = first("planned_duration"), first("actual_duration")
            route_date = first("route_date")

            canonical_routes.append(CanonicalRoute(
                route_id=f"MEND_{route_id}",
                dataset_name="Planned vs Actual Last-Mile Routes (Mendeley)",
                external_route_id=str(route_id),
                driver_id=driver_id,
                route_date=str(route_date) if route_date is not None else None,
                planned_distance_km=float(p_dist) if p_dist is not None else None,
                actual_distance_km=float(a_dist) if a_dist is not None else None,
                planned_duration_min=float(p_dur) if p_dur is not None else None,
                actual_duration_min=float(a_dur) if a_dur is not None else None,
                stops=stops
            ))

        return canonical_routes
