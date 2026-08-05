from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Base Config ---
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# --- Data Quality & Dataset Schemas ---
class DataQualityReportSchema(BaseSchema):
    dataset_name: str
    total_rows: int
    route_count: int
    stop_count: int
    driver_count: int
    missing_values: Dict[str, int]
    duplicate_records: int
    invalid_durations: int
    invalid_distances: int
    invalid_coordinates: int
    validation_status: str # SUCCESS, WARNING, CRITICAL
    issues: List[str]
    provenance_hash: str

class DatasetSchema(BaseSchema):
    id: str
    name: str
    source_url: Optional[str] = None
    doi: Optional[str] = None
    license: Optional[str] = None
    version: str
    download_timestamp: datetime
    file_hash: Optional[str] = None
    row_count: int
    route_count: int
    stop_count: int
    driver_count: int
    date_range: Optional[str] = None
    geographic_scope: Optional[str] = None
    validation_status: str
    is_synthetic: bool

class IngestRequestSchema(BaseModel):
    dataset_name: str # "AMAZON_LAST_MILE" or "MENDELEY_PLANNED_VS_ACTUAL"
    file_path: Optional[str] = None # Path relative to data/ or absolute

# --- Route & Stop Schemas ---
class DeliverySchema(BaseSchema):
    id: str
    package_id: str
    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    priority: str
    is_late: bool
    delay_minutes: float

class StopSchema(BaseSchema):
    id: str
    route_id: str
    external_stop_id: Optional[str] = None
    planned_sequence: int
    actual_sequence: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    planned_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    service_time_min: float
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    status: str
    deliveries: List[DeliverySchema] = []

class RouteMetricSchema(BaseSchema):
    distance_variance_km: float
    duration_variance_min: float
    on_time_delivery_rate: float
    late_delivery_count: int
    route_efficiency_score: float

class RouteDeviationSchema(BaseSchema):
    sequence_similarity_index: float
    stop_reorder_count: int
    additional_distance_km: float
    additional_duration_min: float
    deviation_percentage: float
    is_material_deviation: bool
    explanation: Optional[str] = None

class RouteSchema(BaseSchema):
    id: str
    dataset_id: Optional[str] = None
    external_route_id: str
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    depot_location: Optional[Dict[str, Any]] = None
    route_date: Optional[str] = None
    planned_distance_km: Optional[float] = None
    actual_distance_km: Optional[float] = None
    planned_duration_min: Optional[float] = None
    actual_duration_min: Optional[float] = None
    total_stops: int
    status: str
    created_at: datetime
    metrics: Optional[RouteMetricSchema] = None
    deviation: Optional[RouteDeviationSchema] = None

class RouteDetailSchema(RouteSchema):
    stops: List[StopSchema] = []

# --- Driver Schemas ---
class DriverSchema(BaseSchema):
    id: str
    external_driver_id: str
    name: Optional[str] = None
    experience_level: Optional[str] = None
    historical_adherence_rate: float
    historical_avg_delay_min: float
    created_at: datetime

# --- ML & Risk Schemas ---
class RiskPredictionRequestSchema(BaseModel):
    route_id: str

class RiskPredictionSchema(BaseSchema):
    id: str
    route_id: Optional[str] = None
    stop_id: Optional[str] = None
    predicted_delay_min: float
    late_probability: float
    deviation_probability: float
    composite_risk_score: float # 0 - 100
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    feature_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime

class ModelVersionSchema(BaseSchema):
    id: str
    model_name: str
    version: str
    algorithm: str
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_names: Optional[List[str]] = None
    train_period: Optional[str] = None
    test_period: Optional[str] = None
    is_active: bool
    created_at: datetime

class ModelMetricSchema(BaseSchema):
    id: str
    model_version_id: str
    dataset_id: Optional[str] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    median_ae: Optional[float] = None
    p90_error: Optional[float] = None
    bias: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    pr_auc: Optional[float] = None
    evaluated_at: datetime

# --- Optimization & Scenario Schemas ---
class OptimizeRouteRequestSchema(BaseModel):
    route_id: str
    objective_weights: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {
            "distance_weight": 1.0,
            "duration_weight": 1.5,
            "late_penalty_weight": 10.0,
            "time_window_penalty_weight": 20.0
        }
    )

class OptimizationResultSchema(BaseSchema):
    id: str
    route_id: str
    algorithm: str
    solver_time_ms: float
    baseline_distance_km: float
    optimized_distance_km: float
    baseline_duration_min: float
    optimized_duration_min: float
    distance_savings_pct: float
    duration_savings_pct: float
    is_feasible: bool
    optimized_sequence: List[Dict[str, Any]]
    objective_value: float
    weights_used: Optional[Dict[str, float]] = None
    created_at: datetime

class ScenarioRequestSchema(BaseModel):
    route_id: str
    scenario_type: str # RESEQUENCE, REMOVE_STOP, MULTI_VEHICLE, TIME_WINDOW_PRIORITY, TIME_OPTIMIZED
    removed_stop_id: Optional[str] = None
    vehicle_count: Optional[int] = 1
    custom_sequence: Optional[List[str]] = None

class ScenarioResultSchema(BaseSchema):
    id: str
    route_id: str
    scenario_type: str
    scenario_params: Optional[Dict[str, Any]] = None
    result_metrics: Dict[str, Any]
    created_at: datetime

# --- Decision & Recommendation Schemas ---
class RecommendationSchema(BaseSchema):
    id: str
    route_id: str
    risk_score: float
    action_type: str
    title: str
    explanation: str
    expected_impact: Dict[str, Any]
    evidence: Dict[str, Any]
    status: str
    created_at: datetime

class RecommendationDecisionSchema(BaseModel):
    recommendation_id: str
    action: str # ACCEPT, REJECT, DISMISS
    reason: Optional[str] = None
    user_id: Optional[str] = "dispatcher_01"

# --- Operational Analytics Dashboard KPI Schemas ---
class OverviewAnalyticsSchema(BaseSchema):
    total_routes: int
    total_deliveries: int
    on_time_delivery_rate: float
    late_delivery_rate: float
    avg_delay_minutes: float
    p90_delay_minutes: float
    p95_delay_minutes: float
    avg_route_efficiency_pct: float
    route_deviation_rate: float
    high_risk_routes_count: int
    optimization_opportunities_count: int

# --- Audit Trail Schema ---
class AuditLogSchema(BaseSchema):
    id: str
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any]
    timestamp: datetime
