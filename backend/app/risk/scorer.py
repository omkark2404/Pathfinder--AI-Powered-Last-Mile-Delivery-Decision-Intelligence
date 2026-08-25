from typing import Dict, Any, Tuple
from app.schemas.schemas import RiskPredictionSchema

class DeliveryRiskScorer:
    """
    Computes reproducible composite delivery risk score (0 to 100).
    Categorizes routes into LOW, MEDIUM, HIGH, CRITICAL.
    """
    @staticmethod
    def calculate_risk(
        predicted_delay_min: float,
        late_probability: float,
        deviation_probability: float,
        time_window_pressure: float,
        route_complexity: float
    ) -> Tuple[float, str]:
        """
        Risk Score Formula:
        Score = (late_prob * 35) + (min(delay_min, 60)/60 * 25) + (dev_prob * 20) + (tw_pressure/50 * 10) + (complexity/50 * 10)
        """
        delay_component = min(1.0, predicted_delay_min / 60.0) * 25.0
        late_component = late_probability * 35.0
        deviation_component = deviation_probability * 20.0
        tw_component = min(1.0, time_window_pressure / 50.0) * 10.0
        complexity_component = min(1.0, route_complexity / 50.0) * 10.0

        raw_score = late_component + delay_component + deviation_component + tw_component + complexity_component
        risk_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Operational risk thresholds
        if risk_score <= 20.0:
            level = "LOW"
        elif risk_score <= 50.0:
            level = "MEDIUM"
        elif risk_score <= 75.0:
            level = "HIGH"
        else:
            level = "CRITICAL"

        return risk_score, level
