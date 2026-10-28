"""
Process-wide model instances and the route scoring shared by every endpoint,
so /metrics, /routes/predict-risk, /risk-scores and recommendations all use the same models.
"""

from typing import Any, Dict, List, Optional

from app.ml.deviation_model import RouteDeviationClassifier
from app.ml.eta_model import ETAPredictionModel
from app.ml.features import FeatureEngineer
from app.models.models import Driver, Route, Stop
from app.risk.scorer import DeliveryRiskScorer

eta_model = ETAPredictionModel()
dev_classifier = RouteDeviationClassifier()


def has_planning_data(route: Route) -> bool:
    """Risk features need planned distance and duration; without them they would be filled with defaults."""
    return route.planned_distance_km is not None and route.planned_duration_min is not None


def score_route(route: Route, driver: Optional[Driver], stops: List[Stop]) -> Optional[Dict[str, Any]]:
    """Composite risk for a route, or None when the route lacks the planning data to score it."""
    if not has_planning_data(route):
        return None
    features = FeatureEngineer.extract_route_features(route, driver, stops)
    pred_delay, late_prob = eta_model.predict_delay(features)
    dev_prob = dev_classifier.predict_deviation_probability(features)
    risk_score, risk_level = DeliveryRiskScorer.calculate_risk(
        pred_delay, late_prob, dev_prob,
        features["time_window_pressure"],
        features["route_complexity_score"],
    )
    return {
        "features": features,
        "predicted_delay_min": pred_delay,
        "late_probability": late_prob,
        "deviation_probability": dev_prob,
        "composite_risk_score": risk_score,
        "risk_level": risk_level,
    }
