"""
Feature engineering for ETA delay prediction and route deviation classification.

Temporal leakage discipline:
    All features must be available at dispatch time T_0 (before the route begins).
    Actual outcomes (actual_distance, actual_duration, actual_arrival) must NEVER be used.

Feature contract:
    The ordered list FEATURE_NAMES is the canonical source of truth used by both
    ETAPredictionModel and RouteDeviationClassifier. Adding, removing, or reordering
    features requires updating both models and incrementing their versions.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from app.models.models import Route, Stop, Driver

# ------------------------------------------------------------------
# Canonical ordered feature list — shared by both ML models.
# Do NOT change order without updating model versions.
# ------------------------------------------------------------------
FEATURE_NAMES: List[str] = [
    "stop_count",                  # Number of stops on route
    "planned_distance_km",         # Planned route distance
    "planned_duration_min",        # Planned total duration
    "avg_stop_distance_km",        # Mean inter-stop distance estimate
    "avg_stop_duration_min",       # Mean per-stop planned duration
    "driver_adherence_rate",       # Historical adherence rate [0..1]
    "driver_historical_delay_min", # Historical mean delay in minutes
    "time_window_pressure",        # Mean time-window tightness (higher = tighter)
    "route_complexity_score",      # Composite complexity heuristic
]

# Safe fallback values when a feature cannot be computed from available data.
_FEATURE_DEFAULTS: Dict[str, float] = {
    "stop_count": 8.0,
    "planned_distance_km": 35.0,
    "planned_duration_min": 240.0,
    "avg_stop_distance_km": 4.375,
    "avg_stop_duration_min": 30.0,
    "driver_adherence_rate": 0.90,
    "driver_historical_delay_min": 5.0,
    "time_window_pressure": 0.0,
    "route_complexity_score": 15.0,
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, returning default on failure or NaN."""
    try:
        f = float(value)
        return f if np.isfinite(f) else default
    except (TypeError, ValueError):
        return default


class FeatureEngineer:
    """
    Constructs ML feature vectors for ETA prediction and route deviation prediction.

    All methods strictly enforce dispatch-time leakage rules:
    - Only information available at T_0 (route start) may be used.
    - actual_distance_km, actual_duration_min, actual_arrival are NEVER used.
    """

    @staticmethod
    def extract_route_features(
        route: Route,
        driver: Optional[Driver],
        stops: List[Stop],
    ) -> Dict[str, float]:
        """
        Extract the 9-feature vector used by both ML models.

        Parameters
        ----------
        route : Route
            The route ORM object (only planned fields are accessed).
        driver : Driver or None
            Driver ORM object; None triggers safe defaults.
        stops : list of Stop
            Stop ORM objects belonging to the route.

        Returns
        -------
        dict mapping FEATURE_NAMES → float values (always complete, never NaN).
        """
        stop_count = max(1, len(stops))

        planned_dist = _safe_float(
            route.planned_distance_km, _FEATURE_DEFAULTS["planned_distance_km"]
        )
        planned_dur = _safe_float(
            route.planned_duration_min, _FEATURE_DEFAULTS["planned_duration_min"]
        )

        # Guard against implausible zero-distance routes
        if planned_dist <= 0.0:
            planned_dist = _FEATURE_DEFAULTS["planned_distance_km"]
        if planned_dur <= 0.0:
            planned_dur = _FEATURE_DEFAULTS["planned_duration_min"]

        avg_stop_dist = planned_dist / stop_count
        avg_stop_dur = planned_dur / stop_count

        driver_adherence = _safe_float(
            driver.historical_adherence_rate if driver else None,
            _FEATURE_DEFAULTS["driver_adherence_rate"],
        )
        driver_avg_delay = _safe_float(
            driver.historical_avg_delay_min if driver else None,
            _FEATURE_DEFAULTS["driver_historical_delay_min"],
        )

        # Clamp adherence to valid probability range
        driver_adherence = max(0.0, min(1.0, driver_adherence))
        driver_avg_delay = max(0.0, driver_avg_delay)

        # Time-window pressure: higher value means tighter window
        # Uses 120 min as a reference "comfortable" window.
        tw_pressures: List[float] = []
        for s in stops:
            if s.time_window_start and s.time_window_end:
                window_mins = (
                    s.time_window_end - s.time_window_start
                ).total_seconds() / 60.0
                if window_mins > 0:
                    tw_pressures.append(max(0.0, 120.0 - window_mins))
        tw_pressure_avg = float(np.mean(tw_pressures)) if tw_pressures else 0.0

        # Route complexity: weighted combination of stop density, distance, and
        # time-window tightness. Coefficients are heuristic; not tuned on real data.
        route_complexity = round(
            (stop_count * 0.5) + (planned_dist * 0.3) + (tw_pressure_avg * 0.2),
            2,
        )

        features = {
            "stop_count": float(stop_count),
            "planned_distance_km": float(planned_dist),
            "planned_duration_min": float(planned_dur),
            "avg_stop_distance_km": float(avg_stop_dist),
            "avg_stop_duration_min": float(avg_stop_dur),
            "driver_adherence_rate": float(driver_adherence),
            "driver_historical_delay_min": float(driver_avg_delay),
            "time_window_pressure": float(tw_pressure_avg),
            "route_complexity_score": float(route_complexity),
        }

        # Final NaN guard — should not be reached, but be defensive
        for key in FEATURE_NAMES:
            if not np.isfinite(features[key]):
                features[key] = _FEATURE_DEFAULTS[key]

        return features

    @staticmethod
    def features_to_vector(features: Dict[str, float]) -> np.ndarray:
        """
        Convert a feature dict to a numpy row vector in FEATURE_NAMES order.
        Missing keys fall back to their defaults.
        """
        return np.array(
            [features.get(k, _FEATURE_DEFAULTS.get(k, 0.0)) for k in FEATURE_NAMES],
            dtype=np.float64,
        ).reshape(1, -1)

    @staticmethod
    def extract_stop_features(
        stop: Stop,
        route_features: Dict[str, float],
        current_sequence: int,
    ) -> Dict[str, float]:
        """
        Extend route-level features with stop-level progress context.
        Only information available at stop k (sequence position) is used.
        cumulative_distance_est_km is an estimate, never the actual distance.
        """
        stop_count = max(1.0, route_features.get("stop_count", 1.0))
        remaining_stops = max(0, int(stop_count) - current_sequence)
        pct_completed = float(current_sequence) / stop_count

        return {
            **route_features,
            "stop_sequence": float(current_sequence),
            "remaining_stops": float(remaining_stops),
            "route_completion_pct": float(pct_completed),
            "service_time_min": _safe_float(stop.service_time_min, 5.0),
            "cumulative_distance_est_km": float(
                route_features.get("avg_stop_distance_km", 0.0) * current_sequence
            ),
        }
