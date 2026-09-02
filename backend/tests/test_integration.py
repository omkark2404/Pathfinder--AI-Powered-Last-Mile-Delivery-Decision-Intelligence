"""
Integration and API tests covering:
  - Data ingestion pipeline (synthetic fixture path)
  - Idempotent ingestion (regression)
  - DataValidator correctness
  - Risk scorer unit tests
  - Decision engine correctness
  - Analytics (DeliveryAnalytics empty state)
  - API health and overview endpoints
  - Models API (no fabricated metrics)
"""

import pytest
import pytest_asyncio
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import ASGITransport, AsyncClient

from app.core.database import Base
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.validation import DataValidator
from app.models.models import Dataset, Route, RouteMetric, Delivery
from app.schemas.schemas import IngestRequestSchema
from app.risk.scorer import DeliveryRiskScorer
from app.decisions.engine import DispatchDecisionEngine
from app.analytics.delivery import DeliveryAnalytics


# =========================================================================
# Shared in-memory DB fixture
# =========================================================================

@pytest_asyncio.fixture
async def mem_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()


# =========================================================================
# DataValidator Tests
# =========================================================================

class TestDataValidator:

    def test_valid_dataframe_returns_success(self):
        df = pd.DataFrame([
            {"route_id": "R1", "driver_id": "D1", "planned_distance": 30.0, "actual_distance": 32.0,
             "planned_duration": 180.0, "actual_duration": 190.0, "stop_count": 8},
            {"route_id": "R2", "driver_id": "D2", "planned_distance": 25.0, "actual_distance": 26.5,
             "planned_duration": 150.0, "actual_duration": 160.0, "stop_count": 6},
        ])
        report = DataValidator.validate_dataset(df, "TEST", None)
        assert report.validation_status in ("SUCCESS", "WARNING")
        assert report.total_rows == 2
        assert report.duplicate_records == 0
        assert report.invalid_distances == 0
        assert report.invalid_durations == 0

    def test_duplicate_rows_detected(self):
        row = {"route_id": "R1", "driver_id": "D1", "planned_distance": 30.0}
        df = pd.DataFrame([row, row])
        report = DataValidator.validate_dataset(df, "TEST", None)
        assert report.duplicate_records == 1
        assert any("duplicate" in i.lower() for i in report.issues)

    def test_negative_distance_detected(self):
        df = pd.DataFrame([
            {"route_id": "R1", "planned_distance": -5.0, "actual_distance": 30.0}
        ])
        report = DataValidator.validate_dataset(df, "TEST", None)
        assert report.invalid_distances >= 1

    def test_negative_duration_detected(self):
        df = pd.DataFrame([
            {"route_id": "R1", "planned_duration": -10.0, "actual_duration": 180.0}
        ])
        report = DataValidator.validate_dataset(df, "TEST", None)
        assert report.invalid_durations >= 1

    def test_invalid_lat_lng_detected(self):
        df = pd.DataFrame([
            {"route_id": "R1", "lat": 999.0, "lng": -122.0},
            {"route_id": "R2", "lat": 37.0, "lng": 500.0},
            {"route_id": "R3", "lat": 37.0, "lng": -122.0},  # valid
        ])
        report = DataValidator.validate_dataset(df, "TEST", None)
        assert report.invalid_coordinates >= 2

    def test_empty_dataframe_does_not_raise(self):
        df = pd.DataFrame()
        report = DataValidator.validate_dataset(df, "TEST", None)
        assert report.total_rows == 0

    def test_missing_optional_columns_does_not_raise(self):
        """Validator must not raise KeyError on missing columns."""
        df = pd.DataFrame([{"some_col": "value"}])
        report = DataValidator.validate_dataset(df, "TEST", None)
        assert report is not None

    def test_provenance_hash_na_when_no_file(self):
        df = pd.DataFrame([{"route_id": "R1"}])
        report = DataValidator.validate_dataset(df, "TEST", "/nonexistent/path.csv")
        assert report.provenance_hash == "N/A"

    def test_missing_values_reported(self):
        df = pd.DataFrame([
            {"route_id": "R1", "driver_id": None},
            {"route_id": "R2", "driver_id": "D2"},
        ])
        report = DataValidator.validate_dataset(df, "TEST", None)
        assert report.missing_values.get("driver_id", 0) >= 1


# =========================================================================
# Risk Scorer Tests
# =========================================================================

class TestDeliveryRiskScorer:

    def test_low_risk_all_zeros(self):
        score, level = DeliveryRiskScorer.calculate_risk(0.0, 0.0, 0.0, 0.0, 0.0)
        assert score == 0.0
        assert level == "LOW"

    def test_score_in_valid_range(self):
        score, level = DeliveryRiskScorer.calculate_risk(5.0, 0.3, 0.2, 10.0, 20.0)
        assert 0.0 <= score <= 100.0
        assert level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_critical_risk_with_extreme_inputs(self):
        score, level = DeliveryRiskScorer.calculate_risk(120.0, 1.0, 1.0, 100.0, 100.0)
        assert level == "CRITICAL"
        assert score > 75.0

    def test_low_threshold(self):
        score, level = DeliveryRiskScorer.calculate_risk(1.0, 0.05, 0.05, 0.0, 0.0)
        assert level == "LOW"

    def test_medium_threshold(self):
        score, level = DeliveryRiskScorer.calculate_risk(10.0, 0.4, 0.3, 5.0, 10.0)
        assert level in ("MEDIUM", "HIGH")

    def test_score_capped_at_100(self):
        score, _ = DeliveryRiskScorer.calculate_risk(1000.0, 2.0, 2.0, 200.0, 200.0)
        assert score <= 100.0

    def test_score_floored_at_0(self):
        score, _ = DeliveryRiskScorer.calculate_risk(-10.0, -1.0, -1.0, -50.0, -50.0)
        assert score >= 0.0


# =========================================================================
# Decision Engine Tests
# =========================================================================

class TestDispatchDecisionEngine:

    def _make_route(self, route_id="R1"):
        r = MagicMock()
        r.id = route_id
        r.external_route_id = f"EXT_{route_id}"
        r.planned_distance_km = 35.0
        return r

    def _make_stops(self, n=4):
        return [MagicMock() for _ in range(n)]

    def test_low_risk_returns_monitor(self):
        rec = DispatchDecisionEngine.generate_recommendation(
            self._make_route(), self._make_stops(), 10.0, "LOW", 2.0, 0.1
        )
        assert rec.action_type == "MONITOR"

    def test_medium_low_deviation_returns_monitor(self):
        rec = DispatchDecisionEngine.generate_recommendation(
            self._make_route(), self._make_stops(), 35.0, "MEDIUM", 10.0, 0.2
        )
        assert rec.action_type == "MONITOR"

    def test_medium_high_deviation_returns_resequence(self):
        rec = DispatchDecisionEngine.generate_recommendation(
            self._make_route(), self._make_stops(), 35.0, "MEDIUM", 10.0, 0.6
        )
        assert rec.action_type == "RESEQUENCE"

    def test_high_risk_returns_reroute(self):
        rec = DispatchDecisionEngine.generate_recommendation(
            self._make_route(), self._make_stops(), 70.0, "HIGH", 25.0, 0.7
        )
        assert rec.action_type == "REROUTE"

    def test_critical_risk_returns_escalate(self):
        rec = DispatchDecisionEngine.generate_recommendation(
            self._make_route(), self._make_stops(), 90.0, "CRITICAL", 45.0, 0.9
        )
        assert rec.action_type == "ESCALATE"

    def test_action_type_is_valid_enum(self):
        valid = {"MONITOR", "RESEQUENCE", "REROUTE", "REASSIGN", "PRIORITIZE", "ESCALATE"}
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            for dev in (0.1, 0.6):
                rec = DispatchDecisionEngine.generate_recommendation(
                    self._make_route(), self._make_stops(), 50.0, level, 10.0, dev
                )
                assert rec.action_type in valid, f"Invalid action_type {rec.action_type} for level={level}"

    def test_recommendation_has_evidence(self):
        rec = DispatchDecisionEngine.generate_recommendation(
            self._make_route(), self._make_stops(), 40.0, "MEDIUM", 10.0, 0.3
        )
        assert isinstance(rec.evidence, dict)
        assert "risk_score" in rec.evidence
        assert "predicted_delay_min" in rec.evidence

    def test_impact_saved_minutes_is_nonnegative(self):
        for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            rec = DispatchDecisionEngine.generate_recommendation(
                self._make_route(), self._make_stops(), 50.0, level, 10.0, 0.5
            )
            assert rec.expected_impact["saved_minutes"] >= 0


# =========================================================================
# Ingestion Integration Tests
# =========================================================================

@pytest.mark.asyncio
async def test_synthetic_ingestion_creates_routes(mem_session):
    """Ingesting a synthetic fixture must create at least one Route and Dataset."""
    pipeline = IngestionPipeline(mem_session)
    dataset, run, report = await pipeline.run_ingestion(
        IngestRequestSchema(dataset_name="AMAZON_LAST_MILE")
    )
    assert dataset is not None
    assert dataset.is_synthetic is True
    assert run.status in ("SUCCESS", "WARNING")

    from sqlalchemy import select
    res = await mem_session.execute(select(Route))
    routes = res.scalars().all()
    assert len(routes) >= 1


@pytest.mark.asyncio
async def test_ingestion_dataset_is_synthetic_labeled(mem_session):
    """Synthetic fixture must set is_synthetic=True."""
    pipeline = IngestionPipeline(mem_session)
    dataset, _, _ = await pipeline.run_ingestion(
        IngestRequestSchema(dataset_name="MENDELEY_PLANNED_VS_ACTUAL")
    )
    assert dataset.is_synthetic is True


# =========================================================================
# Analytics: Empty State
# =========================================================================

@pytest.mark.asyncio
async def test_analytics_empty_db_returns_zero_counts(mem_session):
    """Analytics must not crash on an empty database."""
    result = await DeliveryAnalytics.compute_overview_kpis(mem_session)
    assert result.total_routes == 0
    assert result.total_deliveries == 0
    assert result.on_time_delivery_rate == 1.0


@pytest.mark.asyncio
async def test_driver_analytics_empty_db_returns_empty_list(mem_session):
    result = await DeliveryAnalytics.get_driver_analytics(mem_session)
    assert isinstance(result, list)
    assert len(result) == 0


# =========================================================================
# API Integration Tests (ASGI)
# =========================================================================

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health_endpoint():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"


@pytest.mark.asyncio
async def test_models_api_no_fabricated_metrics():
    """GET /api/v1/metrics must return null metrics in synthetic_demo mode."""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/metrics")
    assert resp.status_code == 200
    data = resp.json()
    # Verify evaluation_status and that metrics are null (not fabricated numbers)
    assert data["eta_model"]["evaluation_status"] == "insufficient_data"
    assert data["eta_model"]["metrics"] is None
    assert data["deviation_model"]["evaluation_status"] == "insufficient_data"
    assert data["deviation_model"]["metrics"] is None


@pytest.mark.asyncio
async def test_models_api_list_structure():
    """GET /api/v1/models must return list with model metadata including data_mode."""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    for model in data:
        assert model["data_mode"] == "synthetic_demo"
        assert "feature_names" in model
        assert "evaluation_status" in model


@pytest.mark.asyncio
async def test_overview_endpoint_returns_valid_schema():
    """GET /api/v1/overview must return a valid JSON with the expected keys."""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/overview")
    assert resp.status_code == 200
    data = resp.json()
    for key in [
        "total_routes", "total_deliveries", "on_time_delivery_rate",
        "late_delivery_rate", "avg_delay_minutes", "high_risk_routes_count",
    ]:
        assert key in data, f"Missing key: {key}"


@pytest.mark.asyncio
async def test_routes_endpoint_returns_list():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/routes")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_routes_404_for_unknown_id():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/routes/nonexistent-route-id-xyz")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health_endpoint_data_mode():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_mode" in data
    assert "data_mode_note" in data
    assert data["data_mode"] in ("real", "synthetic_demo")


@pytest.mark.asyncio
async def test_recommendations_endpoints():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/recommendations")
        assert resp.status_code == 200
        recs = resp.json()
        assert isinstance(recs, list)

        # 404 test
        resp_404 = await client.get("/api/v1/recommendations/nonexistent-rec-id")
        assert resp_404.status_code == 404


@pytest.mark.asyncio
async def test_deliveries_single_404():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/deliveries/nonexistent-deliv-id")
    assert resp.status_code == 404
