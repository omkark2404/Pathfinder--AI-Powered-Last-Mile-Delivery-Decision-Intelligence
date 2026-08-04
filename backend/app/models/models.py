import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"
    OPERATIONS_MANAGER = "OPERATIONS_MANAGER"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default=UserRole.DISPATCHER.value, nullable=False)
    created_at = Column(DateTime, default=utc_now)

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    doi = Column(String, nullable=True)
    license = Column(String, nullable=True)
    version = Column(String, nullable=False)
    download_timestamp = Column(DateTime, default=utc_now)
    file_hash = Column(String, nullable=True)
    row_count = Column(Integer, default=0)
    route_count = Column(Integer, default=0)
    stop_count = Column(Integer, default=0)
    driver_count = Column(Integer, default=0)
    date_range = Column(String, nullable=True)
    geographic_scope = Column(String, nullable=True)
    schema_info = Column(JSON, nullable=True)
    validation_status = Column(String, default="PENDING")
    is_synthetic = Column(Boolean, default=False)

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    status = Column(String, nullable=False) # SUCCESS, FAILED, WARNING
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    quality_report = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True)
    external_driver_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=True)
    experience_level = Column(String, nullable=True)
    historical_adherence_rate = Column(Float, default=1.0)
    historical_avg_delay_min = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now)

class Route(Base):
    __tablename__ = "routes"

    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True)
    external_route_id = Column(String, index=True, nullable=False)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=True)
    vehicle_id = Column(String, nullable=True)
    depot_location = Column(JSON, nullable=True) # {lat, lng, address}
    route_date = Column(String, nullable=True)
    
    planned_distance_km = Column(Float, nullable=True)
    actual_distance_km = Column(Float, nullable=True)
    planned_duration_min = Column(Float, nullable=True)
    actual_duration_min = Column(Float, nullable=True)
    
    total_stops = Column(Integer, default=0)
    status = Column(String, default="PLANNED") # PLANNED, IN_PROGRESS, COMPLETED, DELAYED
    
    created_at = Column(DateTime, default=utc_now)

    stops = relationship("Stop", back_populates="route", cascade="all, delete-orphan")
    metrics = relationship("RouteMetric", back_populates="route", uselist=False)
    deviation = relationship("RouteDeviation", back_populates="route", uselist=False)
    driver = relationship("Driver", foreign_keys=[driver_id], primaryjoin="Route.driver_id == Driver.id", lazy="raise")

class Stop(Base):
    __tablename__ = "stops"

    id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    external_stop_id = Column(String, nullable=True)
    planned_sequence = Column(Integer, nullable=False)
    actual_sequence = Column(Integer, nullable=True)
    
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    address = Column(String, nullable=True)
    
    planned_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    service_time_min = Column(Float, default=5.0)
    
    time_window_start = Column(DateTime, nullable=True)
    time_window_end = Column(DateTime, nullable=True)
    
    status = Column(String, default="PENDING") # PENDING, DELIVERED, LATE, SKIPPED
    
    route = relationship("Route", back_populates="stops")
    deliveries = relationship("Delivery", back_populates="stop", cascade="all, delete-orphan")

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(String, primary_key=True)
    stop_id = Column(String, ForeignKey("stops.id"), nullable=False)
    package_id = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=True)
    volume_m3 = Column(Float, nullable=True)
    priority = Column(String, default="NORMAL") # HIGH, NORMAL, LOW
    is_late = Column(Boolean, default=False)
    delay_minutes = Column(Float, default=0.0)

    stop = relationship("Stop", back_populates="deliveries")

class RouteMetric(Base):
    __tablename__ = "route_metrics"

    id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("routes.id"), unique=True, nullable=False)
    distance_variance_km = Column(Float, default=0.0)
    duration_variance_min = Column(Float, default=0.0)
    on_time_delivery_rate = Column(Float, default=1.0)
    late_delivery_count = Column(Integer, default=0)
    route_efficiency_score = Column(Float, default=100.0)
    calculated_at = Column(DateTime, default=utc_now)

    route = relationship("Route", back_populates="metrics")

class RouteDeviation(Base):
    __tablename__ = "deviations"

    id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("routes.id"), unique=True, nullable=False)
    sequence_similarity_index = Column(Float, default=1.0) # Kendall Tau / Levenshtein 0..1
    stop_reorder_count = Column(Integer, default=0)
    additional_distance_km = Column(Float, default=0.0)
    additional_duration_min = Column(Float, default=0.0)
    deviation_percentage = Column(Float, default=0.0)
    is_material_deviation = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)

    route = relationship("Route", back_populates="deviation")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("routes.id"), nullable=True)
    stop_id = Column(String, ForeignKey("stops.id"), nullable=True)
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=True)
    
    predicted_delay_min = Column(Float, default=0.0)
    late_probability = Column(Float, default=0.0)
    deviation_probability = Column(Float, default=0.0)
    composite_risk_score = Column(Float, default=0.0) # 0 to 100
    risk_level = Column(String, default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    
    feature_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String, primary_key=True)
    model_name = Column(String, nullable=False) # ETA_MODEL, DEVIATION_MODEL
    version = Column(String, nullable=False)
    algorithm = Column(String, nullable=False) # Baseline, XGBoost, LightGBM, Random Forest
    hyperparameters = Column(JSON, nullable=True)
    feature_names = Column(JSON, nullable=True)
    train_period = Column(String, nullable=True)
    test_period = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(String, primary_key=True)
    model_version_id = Column(String, ForeignKey("model_versions.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    median_ae = Column(Float, nullable=True)
    p90_error = Column(Float, nullable=True)
    bias = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    pr_auc = Column(Float, nullable=True)
    evaluated_at = Column(DateTime, default=utc_now)

class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    algorithm = Column(String, default="OR-Tools VRP")
    solver_time_ms = Column(Float, default=0.0)
    baseline_distance_km = Column(Float, nullable=False)
    optimized_distance_km = Column(Float, nullable=False)
    baseline_duration_min = Column(Float, nullable=False)
    optimized_duration_min = Column(Float, nullable=False)
    distance_savings_pct = Column(Float, default=0.0)
    duration_savings_pct = Column(Float, default=0.0)
    is_feasible = Column(Boolean, default=True)
    optimized_sequence = Column(JSON, nullable=False)
    objective_value = Column(Float, default=0.0)
    weights_used = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)

class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    scenario_type = Column(String, nullable=False) # RESEQUENCE, REMOVE_STOP, MULTI_VEHICLE, TIME_WINDOW_PRIORITY, TIME_OPTIMIZED
    scenario_params = Column(JSON, nullable=True)
    result_metrics = Column(JSON, nullable=False) # {distance, duration, late_stops, violations, savings}
    created_at = Column(DateTime, default=utc_now)

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    action_type = Column(String, nullable=False) # MONITOR, RESEQUENCE, REROUTE, REASSIGN, PRIORITIZE, ESCALATE
    title = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    expected_impact = Column(JSON, nullable=False) # {saved_minutes, saved_km, reduced_late_risk}
    evidence = Column(JSON, nullable=False) # Structured evidence record
    status = Column(String, default="PENDING") # PENDING, ACCEPTED, REJECTED, DISMISSED
    created_at = Column(DateTime, default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False) # RECOMMENDATION_DECISION, DATASET_INGEST, OPTIMIZATION_RUN, SCENARIO_RUN
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    details = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=utc_now)
