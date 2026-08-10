import os
import json
import pandas as pd
from typing import List, Tuple
from datetime import datetime, timedelta, timezone
from app.ingestion.canonical import CanonicalRoute, CanonicalStop, CanonicalPackage

class AmazonLastMileAdapter:
    """
    Adapter for the Amazon Last Mile Routing Research Challenge dataset.
    Source: https://registry.opendata.aws/amazon-last-mile-challenges/
    """
    @staticmethod
    def parse_data(file_path: str) -> List[CanonicalRoute]:
        canonical_routes: List[CanonicalRoute] = []

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Amazon dataset file not found at {file_path}")

        # Check if json or csv/parquet
        if file_path.endswith(".json"):
            with open(file_path, "r") as f:
                raw_data = json.load(f)
                
            for route_id, route_info in raw_data.items():
                stops = []
                stops_dict = route_info.get("stops", {})
                planned_seq = 0
                for stop_id, stop_info in stops_dict.items():
                    planned_seq += 1
                    lat = stop_info.get("lat")
                    lng = stop_info.get("lng")
                    
                    pkg_list = []
                    pkgs = stop_info.get("packages", {})
                    for pkg_id, pkg_info in pkgs.items():
                        pkg_list.append(CanonicalPackage(
                            package_id=pkg_id,
                            stop_id=stop_id,
                            weight_kg=pkg_info.get("weight"),
                            volume_m3=pkg_info.get("volume")
                        ))

                    stops.append(CanonicalStop(
                        stop_id=stop_id,
                        route_id=route_id,
                        planned_sequence=planned_seq,
                        actual_sequence=stop_info.get("actual_sequence", planned_seq),
                        lat=lat,
                        lng=lng,
                        service_time_min=stop_info.get("service_time", 5.0),
                        packages=pkg_list
                    ))

                route = CanonicalRoute(
                    route_id=f"AMZN_{route_id}",
                    dataset_name="Amazon Last Mile Routing Research Challenge",
                    external_route_id=route_id,
                    driver_id=route_info.get("driver_id", f"DRV_{route_id[:5]}"),
                    depot_location={"lat": route_info.get("depot_lat", 37.7749), "lng": route_info.get("depot_lng", -122.4194)},
                    route_date=route_info.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                    planned_distance_km=route_info.get("planned_distance_km", 45.2),
                    actual_distance_km=route_info.get("actual_distance_km", 48.7),
                    planned_duration_min=route_info.get("planned_duration_min", 240.0),
                    actual_duration_min=route_info.get("actual_duration_min", 265.0),
                    stops=stops
                )
                canonical_routes.append(route)
                
        elif file_path.endswith(".csv") or file_path.endswith(".parquet"):
            df = pd.read_parquet(file_path) if file_path.endswith(".parquet") else pd.read_csv(file_path)
            grouped = df.groupby("route_id")
            
            for route_id, group in grouped:
                stops = []
                for _, row in group.iterrows():
                    stop_id = str(row.get("stop_id", f"STOP_{row.name}"))
                    stops.append(CanonicalStop(
                        stop_id=stop_id,
                        route_id=str(route_id),
                        planned_sequence=int(row.get("planned_sequence", len(stops)+1)),
                        actual_sequence=int(row.get("actual_sequence", len(stops)+1)),
                        lat=float(row["lat"]) if "lat" in row and pd.notnull(row["lat"]) else None,
                        lng=float(row["lng"]) if "lng" in row and pd.notnull(row["lng"]) else None,
                        service_time_min=float(row.get("service_time_min", 5.0))
                    ))
                
                canonical_routes.append(CanonicalRoute(
                    route_id=f"AMZN_{route_id}",
                    dataset_name="Amazon Last Mile Routing Research Challenge",
                    external_route_id=str(route_id),
                    driver_id=str(group["driver_id"].iloc[0]) if "driver_id" in group.columns else f"DRV_{route_id}",
                    route_date=str(group["route_date"].iloc[0]) if "route_date" in group.columns else "2018-09-01",
                    planned_distance_km=float(group["planned_distance_km"].iloc[0]) if "planned_distance_km" in group.columns else 35.0,
                    actual_distance_km=float(group["actual_distance_km"].iloc[0]) if "actual_distance_km" in group.columns else 38.5,
                    stops=stops
                ))

        return canonical_routes
