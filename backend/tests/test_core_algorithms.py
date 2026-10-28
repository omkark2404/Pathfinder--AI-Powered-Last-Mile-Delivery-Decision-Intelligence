"""
Tests for the core algorithms and data adapters:
  - Kendall-tau sequence similarity and the material-deviation label
  - OR-Tools re-sequencing on a tiny instance with a known optimum
  - Scenario simulator baselines
  - Amazon / Mendeley adapters on the committed sample files
  - Dataset file resolution (synthetic labeling, no arbitrary paths)
  - Route risk scoring refusing to score routes without planning data
"""

import os
from types import SimpleNamespace

import pytest

from app.analytics.deviation import (
    RouteDeviationAnalyzer,
    distance_increase_pct,
    is_material_deviation,
)
from app.core.config import settings
from app.ingestion.amazon_adapter import AmazonLastMileAdapter
from app.ingestion.mendeley_adapter import MendeleyPlannedVsActualAdapter
from app.ingestion.pipeline import IngestionPipeline, resolve_dataset_file
from app.ml.registry import score_route
from app.models.models import Dataset, Route, RouteDeviation, RouteMetric
from app.optimization.vrp import VRPOptimizer
from app.schemas.schemas import IngestRequestSchema
from app.simulation.simulator import ScenarioSimulator


# ---------------------------------------------------------------------------
# Sequence similarity & deviation label
# ---------------------------------------------------------------------------

class TestKendallTau:
    def test_identical_order_is_one(self):
        assert RouteDeviationAnalyzer.calculate_kendall_tau_distance([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0

    def test_reversed_order_is_zero(self):
        assert RouteDeviationAnalyzer.calculate_kendall_tau_distance([1, 2, 3, 4], [4, 3, 2, 1]) == 0.0

    def test_one_adjacent_swap(self):
        # 6 pairs, 1 discordant: tau = 4/6, normalized (tau + 1) / 2 = 5/6
        sim = RouteDeviationAnalyzer.calculate_kendall_tau_distance([1, 2, 3, 4], [1, 3, 2, 4])
        assert sim == pytest.approx(5 / 6)

    def test_sequence_similarity_from_positions(self):
        # Stops planned 1..4, visited with stops 2 and 3 swapped
        sim = RouteDeviationAnalyzer.sequence_similarity([1, 2, 3, 4], [1, 3, 2, 4])
        assert sim == pytest.approx(5 / 6)


class TestDeviationLabel:
    def test_distance_over_threshold_is_material(self):
        assert is_material_deviation(10.5, 0.99) is True

    def test_low_similarity_is_material(self):
        assert is_material_deviation(2.0, 0.80) is True

    def test_within_thresholds_is_not_material(self):
        assert is_material_deviation(10.0, 0.85) is False

    def test_unknown_values_are_not_material(self):
        assert is_material_deviation(None, None) is False

    def test_distance_increase_pct(self):
        assert distance_increase_pct(50.0, 55.0) == 10.0
        assert distance_increase_pct(None, 55.0) is None
        assert distance_increase_pct(0.0, 5.0) is None


# ---------------------------------------------------------------------------
# OR-Tools optimizer and simulator
# ---------------------------------------------------------------------------

def _stop(seq, lng, lat=0.0):
    return SimpleNamespace(
        id=f"S{seq}", external_stop_id=f"S{seq}", address=f"Stop {seq}",
        planned_sequence=seq, lat=lat, lng=lng,
    )


def _zigzag_route(planned_distance_km=10.0, depot=(0.0, 0.0)):
    """Three stops on the equator, planned in a zigzag order: far, near, middle."""
    stops = [_stop(1, 0.03), _stop(2, 0.01), _stop(3, 0.02)]
    route = SimpleNamespace(
        depot_location={"lat": depot[0], "lng": depot[1]} if depot else None,
        planned_distance_km=planned_distance_km,
        planned_duration_min=60.0,
    )
    return route, stops


class TestVRPOptimizer:
    def test_finds_known_optimum_and_beats_planned_order(self):
        route, stops = _zigzag_route()
        res = VRPOptimizer.optimize_route(route, stops)
        # Optimal tour: depot -> 0.01 -> 0.02 -> 0.03 -> depot = 0.06 degrees of longitude
        optimal_km = 2 * VRPOptimizer._haversine_distance_km(0, 0, 0, 0.03)
        assert res["is_feasible"] is True
        assert res["optimized_distance_km"] == pytest.approx(optimal_km, abs=0.01)
        assert res["baseline_distance_km"] > res["optimized_distance_km"]
        assert res["distance_savings_pct"] > 0
        assert sorted(s["original_sequence"] for s in res["optimized_sequence"]) == [1, 2, 3]

    def test_duration_is_flagged_as_estimate(self):
        route, stops = _zigzag_route()
        res = VRPOptimizer.optimize_route(route, stops)
        assert res["duration_is_estimate"] is True
        assert res["optimized_duration_min"] < res["baseline_duration_min"]

    def test_no_dispatch_plan_means_no_baseline(self):
        route, stops = _zigzag_route(planned_distance_km=None)
        res = VRPOptimizer.optimize_route(route, stops)
        assert res["baseline_distance_km"] is None
        assert res["distance_savings_pct"] is None
        assert res["optimized_distance_km"] > 0

    def test_missing_depot_starts_at_first_planned_stop(self):
        route, stops = _zigzag_route(depot=None)
        res = VRPOptimizer.optimize_route(route, stops)
        # Tour from stop 1 (lng 0.03) through 0.01 and 0.02 and back: 0.02 degrees out and back
        expected_km = 2 * VRPOptimizer._haversine_distance_km(0, 0.01, 0, 0.03)
        assert res["optimized_distance_km"] == pytest.approx(expected_km, abs=0.01)

    def test_empty_route_raises(self):
        route, _ = _zigzag_route()
        with pytest.raises(ValueError):
            VRPOptimizer.optimize_route(route, [])


class TestScenarioSimulator:
    def test_remove_stop_drops_exactly_one_stop(self):
        route, stops = _zigzag_route()
        res = ScenarioSimulator.run_scenario(route, stops, "REMOVE_STOP", {"removed_stop_id": "S1"})
        assert "Remaining stops: 2" in res["description"]

    def test_resequence_baseline_matches_optimizer_baseline(self):
        route, stops = _zigzag_route()
        sim = ScenarioSimulator.run_scenario(route, stops, "RESEQUENCE", {})
        opt = VRPOptimizer.optimize_route(route, stops)
        assert sim["baseline_distance_km"] == opt["baseline_distance_km"]
        assert sim["distance_saved_km"] >= 0

    def test_no_plan_means_no_savings(self):
        route, stops = _zigzag_route(planned_distance_km=None)
        sim = ScenarioSimulator.run_scenario(route, stops, "RESEQUENCE", {})
        assert sim["distance_saved_km"] is None
        assert sim["duration_saved_min"] is None


# ---------------------------------------------------------------------------
# Adapters on the committed sample files
# ---------------------------------------------------------------------------

AMAZON_SAMPLE = os.path.join(settings.DATA_DIR, "amazon_last_mile_sample.json")
MENDELEY_FIXTURE = os.path.join(settings.DATA_DIR, "mendeley_synthetic_fixture.csv")


@pytest.mark.skipif(not os.path.exists(AMAZON_SAMPLE), reason="Amazon sample not present")
class TestAmazonAdapter:
    @pytest.fixture(scope="class")
    def routes(self):
        return AmazonLastMileAdapter.parse_data(AMAZON_SAMPLE)

    def test_route_count_and_station_excluded(self, routes):
        assert len(routes) == 13
        # 2,051 stop records in the file, one of them per route is the station (depot)
        assert sum(len(r.stops) for r in routes) == 2051 - 13

    def test_depot_and_date_come_from_the_file(self, routes):
        for r in routes:
            assert r.depot_location["station_code"]
            assert r.route_date.startswith("2018-")

    def test_fields_absent_from_the_file_stay_unknown(self, routes):
        for r in routes:
            assert r.planned_distance_km is None and r.actual_duration_min is None
            assert r.driver_id is None
            assert all(s.actual_sequence is None for s in r.stops)

    def test_service_time_and_volume_parsed(self, routes):
        stop = routes[0].stops[0]
        assert stop.service_time_min > 0
        assert stop.packages and stop.packages[0].volume_m3 > 0


@pytest.mark.skipif(not os.path.exists(MENDELEY_FIXTURE), reason="Mendeley fixture not present")
def test_mendeley_fixture_adapter():
    routes = MendeleyPlannedVsActualAdapter.parse_data(MENDELEY_FIXTURE)
    assert len(routes) == 30
    assert sum(len(r.stops) for r in routes) == 603
    assert all(s.actual_sequence is not None for r in routes for s in r.stops)
    assert all(r.route_date is None for r in routes)  # the fixture has no dates; none are invented


# ---------------------------------------------------------------------------
# File resolution and ingestion labeling
# ---------------------------------------------------------------------------

def test_bundled_mendeley_file_resolves_as_synthetic():
    path, is_synthetic = resolve_dataset_file("MENDELEY_PLANNED_VS_ACTUAL")
    if path is None:
        pytest.skip("no Mendeley file present")
    assert is_synthetic is (os.path.basename(path) == "mendeley_synthetic_fixture.csv")


def test_requested_file_path_cannot_escape_data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DATA_DIR", str(tmp_path))
    outside = tmp_path.parent / "outside.csv"
    outside.write_text("route_id\n1\n")
    path, _ = resolve_dataset_file("MENDELEY_PLANNED_VS_ACTUAL", requested=str(outside))
    assert path is None


@pytest.mark.asyncio
@pytest.mark.skipif(not os.path.exists(AMAZON_SAMPLE), reason="Amazon sample not present")
async def test_amazon_ingestion_creates_no_fabricated_outcomes(mem_session):
    from sqlalchemy import func, select
    dataset, _, _ = await IngestionPipeline(mem_session).run_ingestion(
        IngestRequestSchema(dataset_name="AMAZON_LAST_MILE")
    )
    assert dataset.license == "CC BY-NC 4.0"
    assert dataset.is_synthetic is False
    metrics = (await mem_session.execute(select(func.count()).select_from(RouteMetric))).scalar_one()
    deviations = (await mem_session.execute(select(func.count()).select_from(RouteDeviation))).scalar_one()
    assert metrics == 0 and deviations == 0


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

def test_score_route_refuses_routes_without_planning_data():
    route = SimpleNamespace(planned_distance_km=None, planned_duration_min=None)
    assert score_route(route, None, []) is None


def test_score_route_returns_bounded_score():
    route = SimpleNamespace(planned_distance_km=40.0, planned_duration_min=240.0)
    stops = [SimpleNamespace(time_window_start=None, time_window_end=None) for _ in range(12)]
    scored = score_route(route, None, stops)
    assert 0.0 <= scored["composite_risk_score"] <= 100.0
    assert scored["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
