import uuid
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Route, Stop, Recommendation, AuditLog
from app.risk.scorer import DeliveryRiskScorer

class DispatchDecisionEngine:
    """
    Operational Decision Engine translating risk, predictions, and route metrics
    into concrete, audit-tracked dispatcher recommendations.
    """
    @staticmethod
    def generate_recommendation(
        route: Route,
        stops: List[Stop],
        risk_score: float,
        risk_level: str,
        predicted_delay_min: float,
        deviation_prob: float
    ) -> Recommendation:
        """
        Generates actionable dispatcher recommendation based on operational rules.
        """
        rec_id = str(uuid.uuid4())
        
        # Rule-based decision matrix
        # action_type must be one of: MONITOR, RESEQUENCE, REROUTE, REASSIGN, PRIORITIZE, ESCALATE
        if risk_level == "LOW":
            action_type = "MONITOR"
            title = "Route within Normal Bounds — Monitor Passively"
            explanation = "Route is performing within normal operating bounds. No intervention required; continue standard monitoring."
            impact = {"saved_minutes": 0, "saved_km": 0, "reduced_late_risk_pct": 0}

        elif risk_level == "MEDIUM":
            if deviation_prob > 0.4:
                action_type = "RESEQUENCE"
                title = "Resequence Route Stops"
                explanation = (
                    f"Moderate route deviation risk detected (probability={deviation_prob:.2f}). "
                    f"Predicted delay: {predicted_delay_min:.1f} min. "
                    "Resequencing stops to improve spatial efficiency is recommended."
                )
                # Estimated impact — proportional to predicted delay, not hard-coded
                est_saved_min = round(min(predicted_delay_min * 0.4, 20.0), 1)
                impact = {
                    "saved_minutes": est_saved_min,
                    "saved_km": round(est_saved_min * 0.2, 1),
                    "reduced_late_risk_pct": round(deviation_prob * 50.0, 1),
                }
            else:
                action_type = "MONITOR"
                title = "Active Dispatcher Monitoring"
                explanation = (
                    f"Predicted delay of {predicted_delay_min:.1f} min. "
                    "Monitor route progress and intervene if stop-level delays accumulate."
                )
                est_saved_min = round(min(predicted_delay_min * 0.2, 10.0), 1)
                impact = {
                    "saved_minutes": est_saved_min,
                    "saved_km": 0.0,
                    "reduced_late_risk_pct": 10.0,
                }

        elif risk_level == "HIGH":
            action_type = "REROUTE"
            title = "Apply VRP-Optimized Stop Sequence"
            explanation = (
                f"High delivery risk (score={risk_score:.1f}/100, predicted delay={predicted_delay_min:.1f} min). "
                "Reoptimizing the stop sequence using the VRP solver is recommended."
            )
            est_saved_min = round(min(predicted_delay_min * 0.5, 35.0), 1)
            impact = {
                "saved_minutes": est_saved_min,
                "saved_km": round(est_saved_min * 0.18, 1),
                "reduced_late_risk_pct": round(min(risk_score * 0.7, 65.0), 1),
            }

        else:  # CRITICAL
            action_type = "ESCALATE"
            title = "Escalate to Senior Dispatcher — Critical Risk"
            explanation = (
                f"Critical risk level (score={risk_score:.1f}/100, predicted delay={predicted_delay_min:.1f} min). "
                "Immediate dispatcher escalation required. Prioritize high-value stops and consider route reassignment."
            )
            est_saved_min = round(min(predicted_delay_min * 0.6, 50.0), 1)
            impact = {
                "saved_minutes": est_saved_min,
                "saved_km": round(est_saved_min * 0.18, 1),
                "reduced_late_risk_pct": round(min(risk_score * 0.8, 80.0), 1),
            }


        # Structured evidence audit object
        evidence = {
            "route_id": route.id,
            "external_route_id": route.external_route_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "predicted_delay_min": predicted_delay_min,
            "deviation_probability": deviation_prob,
            "total_stops": len(stops),
            "planned_distance_km": route.planned_distance_km,
            "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        return Recommendation(
            id=rec_id,
            route_id=route.id,
            risk_score=risk_score,
            action_type=action_type,
            title=title,
            explanation=explanation,
            expected_impact=impact,
            evidence=evidence,
            status="PENDING"
        )
