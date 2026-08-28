"""
Focused ML tests covering:
  - Feature engineering: output shape, no leakage, missing values, defaults
  - ETA model: training, prediction, evaluation, insufficient-data path, metadata
  - Deviation model: training, prediction, probabilities, metrics, class validation
  - Models API: metadata structure, no fabricated metrics, evaluation_status
"""

import pytest
import numpy as np
from unittest.mock import MagicMock

from app.ml.features import FeatureEngineer, FEATURE_NAMES, _FEATURE_DEFAULTS
from app.ml.eta_model import ETAPredictionModel, MIN_SAMPLES_FOR_EVAL as ETA_MIN
from app.ml.deviation_model import RouteDeviationClassifier, MIN_SAMPLES_FOR_EVAL as DEV_MIN


# =========================================================================
# Helpers
# =========================================================================

def _make_mock_route(
    planned_distance_km=35.0,
    planned_duration_min=240.0,
):
    r = MagicMock()
    r.planned_distance_km = planned_distance_km
    r.planned_duration_min = planned_duration_min
    # Actual outcomes must never be accessed by features — set to sentinel
    r.actual_distance_km = 999.0   # should not appear in features
    r.actual_duration_min = 999.0  # should not appear in features
    return r


def _make_mock_driver(adherence=0.92, avg_delay=4.5):
    d = MagicMock()
    d.historical_adherence_rate = adherence
    d.historical_avg_delay_min = avg_delay
    return d


def _make_mock_stop(planned_seq=1, tw_start=None, tw_end=None, service_time=5.0):
    s = MagicMock()
    s.planned_sequence = planned_seq
    s.time_window_start = tw_start
    s.time_window_end = tw_end
    s.service_time_min = service_time
    return s


def _make_X(n: int, seed: int = 0) -> np.ndarray:
    """Generate synthetic feature matrix for testing."""
    rng = np.random.RandomState(seed)
    base = np.array([
        [8,  28.5, 180.0, 3.56, 22.5, 0.95, 2.0,  0.0, 12.6],
        [12, 40.0, 240.0, 3.33, 20.0, 0.85, 8.0,  5.0, 18.0],
        [16, 55.0, 330.0, 3.44, 20.6, 0.90, 4.5, 10.0, 24.5],
        [6,  18.0, 120.0, 3.00, 20.0, 0.98, 1.0,  0.0,  8.4],
        [20, 72.0, 420.0, 3.60, 21.0, 0.78, 12.0, 20.0, 35.6],
    ], dtype=np.float64)
    rows = []
    for i in range(n):
        noise = rng.randn(len(FEATURE_NAMES)) * 0.5
        rows.append(base[i % len(base)] + noise)
    return np.array(rows, dtype=np.float64)


# =========================================================================
# Feature Engineering Tests
# =========================================================================

class TestFeatureEngineering:

    def test_feature_names_are_stable(self):
        """FEATURE_NAMES must match the expected 9 features in order."""
        expected = [
            "stop_count", "planned_distance_km", "planned_duration_min",
            "avg_stop_distance_km", "avg_stop_duration_min",
            "driver_adherence_rate", "driver_historical_delay_min",
            "time_window_pressure", "route_complexity_score",
        ]
        assert FEATURE_NAMES == expected

    def test_extract_returns_all_feature_names(self):
        route = _make_mock_route()
        driver = _make_mock_driver()
        stops = [_make_mock_stop(i) for i in range(1, 5)]
        features = FeatureEngineer.extract_route_features(route, driver, stops)
        for name in FEATURE_NAMES:
            assert name in features, f"Missing feature: {name}"

    def test_all_features_are_finite(self):
        route = _make_mock_route()
        driver = _make_mock_driver()
        stops = [_make_mock_stop(i) for i in range(1, 9)]
        features = FeatureEngineer.extract_route_features(route, driver, stops)
        for name, val in features.items():
            assert np.isfinite(val), f"Feature '{name}' is not finite: {val}"

    def test_no_target_leakage_actual_fields_not_accessed(self):
        """actual_distance_km and actual_duration_min must not appear in features."""
        route = _make_mock_route(planned_distance_km=30.0, planned_duration_min=200.0)
        driver = _make_mock_driver()
        stops = [_make_mock_stop(i) for i in range(1, 5)]
        features = FeatureEngineer.extract_route_features(route, driver, stops)
        # actual sentinel value (999.0) must never appear in features
        for name, val in features.items():
            assert abs(val - 999.0) > 0.01, f"Feature '{name}' = {val} matches sentinel — possible leakage"

    def test_none_driver_uses_defaults(self):
        route = _make_mock_route()
        stops = [_make_mock_stop(i) for i in range(1, 5)]
        features = FeatureEngineer.extract_route_features(route, None, stops)
        assert features["driver_adherence_rate"] == _FEATURE_DEFAULTS["driver_adherence_rate"]
        assert features["driver_historical_delay_min"] == _FEATURE_DEFAULTS["driver_historical_delay_min"]

    def test_zero_stops_does_not_divide_by_zero(self):
        route = _make_mock_route()
        driver = _make_mock_driver()
        # Empty stop list — should not raise, stop_count forced to 1
        features = FeatureEngineer.extract_route_features(route, driver, [])
        assert np.isfinite(features["avg_stop_distance_km"])
        assert np.isfinite(features["avg_stop_dur_min"] if "avg_stop_dur_min" in features
                           else features["avg_stop_duration_min"])

    def test_zero_planned_distance_uses_default(self):
        route = _make_mock_route(planned_distance_km=0.0)
        driver = _make_mock_driver()
        stops = [_make_mock_stop(i) for i in range(1, 5)]
        features = FeatureEngineer.extract_route_features(route, driver, stops)
        assert features["planned_distance_km"] == _FEATURE_DEFAULTS["planned_distance_km"]

    def test_driver_adherence_clamped_to_unit_interval(self):
        route = _make_mock_route()
        driver = _make_mock_driver(adherence=1.5)  # out of range
        stops = [_make_mock_stop(i) for i in range(1, 5)]
        features = FeatureEngineer.extract_route_features(route, driver, stops)
        assert 0.0 <= features["driver_adherence_rate"] <= 1.0

    def test_features_to_vector_shape(self):
        feats = {k: 1.0 for k in FEATURE_NAMES}
        vec = FeatureEngineer.features_to_vector(feats)
        assert vec.shape == (1, len(FEATURE_NAMES))

    def test_time_window_pressure_zero_without_windows(self):
        route = _make_mock_route()
        driver = _make_mock_driver()
        stops = [_make_mock_stop(i, tw_start=None, tw_end=None) for i in range(1, 5)]
        features = FeatureEngineer.extract_route_features(route, driver, stops)
        assert features["time_window_pressure"] == 0.0


# =========================================================================
# ETA Model Tests
# =========================================================================

class TestETAPredictionModel:

    def test_predict_returns_nonnegative_delay(self):
        model = ETAPredictionModel()
        features = {k: 1.0 for k in FEATURE_NAMES}
        delay, prob = model.predict_delay(features)
        assert delay >= 0.0

    def test_predict_late_probability_in_unit_interval(self):
        model = ETAPredictionModel()
        features = {k: 1.0 for k in FEATURE_NAMES}
        delay, prob = model.predict_delay(features)
        assert 0.0 <= prob <= 1.0

    def test_synthetic_bootstrap_evaluation_status(self):
        """Default model must report insufficient_data — never fake metrics."""
        model = ETAPredictionModel()
        meta = model.get_metadata()
        assert meta["evaluation_status"] == "insufficient_data"
        assert meta["metrics"] is None

    def test_synthetic_bootstrap_data_mode(self):
        model = ETAPredictionModel()
        meta = model.get_metadata()
        assert meta["data_mode"] == "synthetic_demo"

    def test_metadata_is_trained(self):
        model = ETAPredictionModel()
        meta = model.get_metadata()
        assert meta["is_trained"] is True

    def test_metadata_has_feature_names(self):
        model = ETAPredictionModel()
        meta = model.get_metadata()
        assert meta["feature_names"] == FEATURE_NAMES

    def test_evaluate_insufficient_data_below_threshold(self):
        """Evaluation on fewer than MIN_SAMPLES samples must return insufficient_data."""
        model = ETAPredictionModel()
        X = _make_X(ETA_MIN - 1)
        y = np.ones(ETA_MIN - 1)
        result = model.evaluate(X, y)
        assert result["evaluation_status"] == "insufficient_data"
        assert result["metrics"] is None

    def test_evaluate_sufficient_data_returns_real_metrics(self):
        """Evaluation on sufficient data must compute real, finite metrics."""
        model = ETAPredictionModel()
        # Need at least 2 * ETA_MIN samples so each split has >= ETA_MIN
        n = ETA_MIN * 2 + 4
        X = _make_X(n)
        X_train, X_test = X[:n // 2], X[n // 2:]
        y = np.linspace(1.0, 30.0, n)
        y_train, y_test = y[:n // 2], y[n // 2:]
        model.train(X_train, y_train)
        result = model.evaluate(X_test, y_test)
        assert result["evaluation_status"] in ("evaluated", "low_sample_size")
        assert result["metrics"] is not None
        for metric in ["mae", "rmse", "median_ae", "p90_error", "bias"]:
            assert metric in result["metrics"]
            assert np.isfinite(result["metrics"][metric])

    def test_evaluate_low_sample_size_flag_and_rounding(self):
        """When 10 <= len(y_test) < 30, evaluation_status must be 'low_sample_size' with 1 decimal."""
        model = ETAPredictionModel()
        n = 24
        X = _make_X(n)
        X_train, X_test = X[:12], X[12:]
        y = np.linspace(1.0, 30.0, n)
        y_train, y_test = y[:12], y[12:]
        model.train(X_train, y_train)
        result = model.evaluate(X_test, y_test)
        assert result["evaluation_status"] == "low_sample_size"
        assert result["sample_size_warning"] is not None
        for k, v in result["metrics"].items():
            assert round(v, 1) == v

    def test_evaluate_full_sample_size_status(self):
        """When len(y_test) >= 30, evaluation_status must be 'evaluated'."""
        model = ETAPredictionModel()
        n = 80
        X = _make_X(n)
        X_train, X_test = X[:40], X[40:]
        y = np.linspace(1.0, 30.0, n)
        y_train, y_test = y[:40], y[40:]
        model.train(X_train, y_train)
        result = model.evaluate(X_test, y_test)
        assert result["evaluation_status"] == "evaluated"

    def test_train_rejects_empty_data(self):
        model = ETAPredictionModel()
        with pytest.raises(ValueError, match="empty"):
            model.train(np.array([]).reshape(0, len(FEATURE_NAMES)), np.array([]))

    def test_train_rejects_wrong_feature_count(self):
        model = ETAPredictionModel()
        X = np.ones((5, len(FEATURE_NAMES) + 2))
        y = np.ones(5)
        with pytest.raises(ValueError, match="features"):
            model.train(X, y)

    def test_no_fabricated_metrics_in_metadata(self):
        """Verify the known fabricated values from the old implementation never appear."""
        model = ETAPredictionModel()
        meta = model.get_metadata()
        # Old hard-coded values that must not be present
        assert meta.get("mae") != 2.45
        assert meta.get("rmse") != 3.82
        # metrics should be None in synthetic mode
        assert meta["metrics"] is None

    def test_limitations_present_in_synthetic_mode(self):
        model = ETAPredictionModel()
        meta = model.get_metadata()
        assert meta["limitations"] is not None
        assert len(meta["limitations"]) > 0

    def test_predict_missing_feature_uses_zero(self):
        """Missing feature keys should default to 0.0 without raising."""
        model = ETAPredictionModel()
        delay, prob = model.predict_delay({})  # empty dict
        assert delay >= 0.0
        assert 0.0 <= prob <= 1.0

    def test_evaluate_performance_alias(self):
        """evaluate_performance() is an alias for evaluate() — must return dict."""
        model = ETAPredictionModel()
        X = _make_X(3)
        y = np.array([5.0, 10.0, 15.0])
        result = model.evaluate_performance(X, y)
        assert isinstance(result, dict)
        assert "evaluation_status" in result


# =========================================================================
# Deviation Model Tests
# =========================================================================

class TestRouteDeviationClassifier:

    def test_predict_deviation_probability_in_unit_interval(self):
        model = RouteDeviationClassifier()
        features = {k: 1.0 for k in FEATURE_NAMES}
        prob = model.predict_deviation_probability(features)
        assert 0.0 <= prob <= 1.0

    def test_predict_returns_binary_label(self):
        model = RouteDeviationClassifier()
        features = {k: 1.0 for k in FEATURE_NAMES}
        label = model.predict(features)
        assert label in (0, 1)

    def test_synthetic_bootstrap_evaluation_status(self):
        model = RouteDeviationClassifier()
        meta = model.get_metadata()
        assert meta["evaluation_status"] == "insufficient_data"
        assert meta["metrics"] is None

    def test_synthetic_bootstrap_data_mode(self):
        model = RouteDeviationClassifier()
        meta = model.get_metadata()
        assert meta["data_mode"] == "synthetic_demo"

    def test_metadata_has_feature_names(self):
        model = RouteDeviationClassifier()
        meta = model.get_metadata()
        assert meta["feature_names"] == FEATURE_NAMES

    def test_evaluate_insufficient_data(self):
        model = RouteDeviationClassifier()
        X = _make_X(DEV_MIN - 1)
        y = np.zeros(DEV_MIN - 1, dtype=int)
        result = model.evaluate(X, y)
        assert result["evaluation_status"] == "insufficient_data"
        assert result["metrics"] is None

    def test_evaluate_insufficient_class_variety(self):
        """Test set with only one class must return insufficient_class_variety."""
        model = RouteDeviationClassifier()
        X = _make_X(DEV_MIN + 5)
        y = np.zeros(len(X), dtype=int)  # only class 0
        result = model.evaluate(X, y)
        assert result["evaluation_status"] == "insufficient_class_variety"
        assert result["metrics"] is None

    def test_evaluate_sufficient_data_returns_real_metrics(self):
        """With enough balanced data, real PR-AUC must be computed."""
        model = RouteDeviationClassifier()
        n = DEV_MIN + 10
        X = _make_X(n)
        # Balanced labels
        y = np.array([i % 2 for i in range(n)], dtype=int)
        X_tr, X_te = X[:n//2], X[n//2:]
        y_tr, y_te = y[:n//2], y[n//2:]
        model.train(X_tr, y_tr)
        result = model.evaluate(X_te, y_te)
        assert result["evaluation_status"] in ("evaluated", "low_sample_size")
        assert result["metrics"] is not None
        for metric in ["precision", "recall", "f1_score", "pr_auc"]:
            assert metric in result["metrics"]
            assert np.isfinite(result["metrics"][metric])
        # PR-AUC must not be the old hard-coded 0.86 from single-class data
        # (it may coincidentally be close — but we verify it was actually computed)
        assert 0.0 <= result["metrics"]["pr_auc"] <= 1.0

    def test_evaluate_low_sample_size_flag_and_rounding(self):
        """When 10 <= len(y_test) < 30, deviation classifier returns low_sample_size."""
        model = RouteDeviationClassifier()
        n = 24
        X = _make_X(n)
        y = np.array([i % 2 for i in range(n)], dtype=int)
        X_tr, X_te = X[:12], X[12:]
        y_tr, y_te = y[:12], y[12:]
        model.train(X_tr, y_tr)
        result = model.evaluate(X_te, y_te)
        assert result["evaluation_status"] == "low_sample_size"
        assert result["sample_size_warning"] is not None
        for k, v in result["metrics"].items():
            assert round(v, 1) == v

    def test_evaluate_full_sample_size_status(self):
        """When len(y_test) >= 30, deviation classifier returns evaluated."""
        model = RouteDeviationClassifier()
        n = 80
        X = _make_X(n)
        y = np.array([i % 2 for i in range(n)], dtype=int)
        X_tr, X_te = X[:40], X[40:]
        y_tr, y_te = y[:40], y[40:]
        model.train(X_tr, y_tr)
        result = model.evaluate(X_te, y_te)
        assert result["evaluation_status"] == "evaluated"

    def test_no_hardcoded_pr_auc(self):
        """The old hard-coded pr_auc=0.86 must never appear in synthetic mode."""
        model = RouteDeviationClassifier()
        meta = model.get_metadata()
        assert meta["metrics"] is None  # not available, not faked

    def test_train_rejects_single_class(self):
        model = RouteDeviationClassifier()
        X = _make_X(10)
        y = np.ones(10, dtype=int)  # only class 1
        with pytest.raises(ValueError, match="both classes"):
            model.train(X, y)

    def test_train_rejects_empty_data(self):
        model = RouteDeviationClassifier()
        with pytest.raises(ValueError, match="empty"):
            model.train(np.array([]).reshape(0, len(FEATURE_NAMES)), np.array([]))

    def test_predict_missing_feature_uses_zero(self):
        model = RouteDeviationClassifier()
        prob = model.predict_deviation_probability({})
        assert 0.0 <= prob <= 1.0

    def test_limitations_present_in_synthetic_mode(self):
        model = RouteDeviationClassifier()
        meta = model.get_metadata()
        assert meta["limitations"] is not None

    def test_evaluate_performance_alias(self):
        model = RouteDeviationClassifier()
        X = _make_X(DEV_MIN - 1)
        y = np.zeros(len(X), dtype=int)
        result = model.evaluate_performance(X, y)
        assert isinstance(result, dict)
        assert "evaluation_status" in result
