from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class CanonicalPackage:
    package_id: str
    stop_id: str
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    priority: str = "NORMAL"
    is_late: bool = False
    delay_minutes: float = 0.0

@dataclass
class CanonicalStop:
    stop_id: str
    route_id: str
    planned_sequence: int
    actual_sequence: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    planned_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    service_time_min: float = 5.0
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    status: str = "PENDING"
    packages: List[CanonicalPackage] = field(default_factory=list)

@dataclass
class CanonicalRoute:
    route_id: str
    dataset_name: str
    external_route_id: str
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    depot_location: Optional[Dict[str, Any]] = None
    route_date: Optional[str] = None
    planned_distance_km: Optional[float] = None
    actual_distance_km: Optional[float] = None
    planned_duration_min: Optional[float] = None
    actual_duration_min: Optional[float] = None
    stops: List[CanonicalStop] = field(default_factory=list)
