import os
import json
import pandas as pd
from typing import List
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
                
            # The challenge's route file has no dispatch plan, driver ID, distances or
            # durations, so those stay None rather than being filled with constants.
            # planned_sequence is file order; actual visit order is only known when a
            # stop carries "actual_sequence" (the official data ships it separately).
            for route_id, route_info in raw_data.items():
                stops = []
                depot = None
                planned_seq = 0
                for stop_id, stop_info in route_info.get("stops", {}).items():
                    lat = stop_info.get("lat")
                    lng = stop_info.get("lng")
                    if stop_info.get("type") == "Station":
                        depot = {"lat": lat, "lng": lng, "station_code": route_info.get("station_code")}
                        continue
                    planned_seq += 1

                    pkg_list = []
                    service_seconds = []
                    for pkg_id, pkg_info in stop_info.get("packages", {}).items():
                        dims = pkg_info.get("dimensions") or {}
                        volume_cm3 = dims.get("depth_cm", 0) * dims.get("height_cm", 0) * dims.get("width_cm", 0)
                        pkg_list.append(CanonicalPackage(
                            package_id=pkg_id,
                            stop_id=stop_id,
                            weight_kg=pkg_info.get("weight"),
                            volume_m3=round(volume_cm3 / 1e6, 6) if volume_cm3 else None,
                        ))
                        if pkg_info.get("planned_service_time_seconds") is not None:
                            service_seconds.append(pkg_info["planned_service_time_seconds"])

                    stops.append(CanonicalStop(
                        stop_id=stop_id,
                        route_id=route_id,
                        planned_sequence=planned_seq,
                        actual_sequence=stop_info.get("actual_sequence"),
                        lat=lat,
                        lng=lng,
                        service_time_min=round(sum(service_seconds) / 60.0, 2) if service_seconds else 5.0,
                        packages=pkg_list
                    ))

                canonical_routes.append(CanonicalRoute(
                    route_id=f"AMZN_{route_id}",
                    dataset_name="Amazon Last Mile Routing Research Challenge",
                    external_route_id=route_id,
                    driver_id=route_info.get("driver_id"),
                    depot_location=depot,
                    route_date=route_info.get("date_YYYY_MM_DD") or route_info.get("date"),
                    stops=stops
                ))
                
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
                        actual_sequence=int(row["actual_sequence"]) if pd.notnull(row.get("actual_sequence")) else None,
                        lat=float(row["lat"]) if "lat" in row and pd.notnull(row["lat"]) else None,
                        lng=float(row["lng"]) if "lng" in row and pd.notnull(row["lng"]) else None,
                        service_time_min=float(row.get("service_time_min", 5.0))
                    ))
                
                canonical_routes.append(CanonicalRoute(
                    route_id=f"AMZN_{route_id}",
                    dataset_name="Amazon Last Mile Routing Research Challenge",
                    external_route_id=str(route_id),
                    driver_id=str(group["driver_id"].iloc[0]) if "driver_id" in group.columns else f"DRV_{route_id}",
                    route_date=str(group["route_date"].iloc[0]) if "route_date" in group.columns else None,
                    planned_distance_km=float(group["planned_distance_km"].iloc[0]) if "planned_distance_km" in group.columns else None,
                    actual_distance_km=float(group["actual_distance_km"].iloc[0]) if "actual_distance_km" in group.columns else None,
                    stops=stops
                ))

        return canonical_routes
