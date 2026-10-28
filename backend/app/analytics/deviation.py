from typing import List, Dict, Any, Optional
from app.models.models import Route, Stop

# Single definition of the deviation label, shared by ingestion, the API and evaluation.
SIMILARITY_THRESHOLD = 0.85
DISTANCE_INCREASE_THRESHOLD_PCT = 10.0


def is_material_deviation(distance_increase_pct: Optional[float], similarity: Optional[float]) -> bool:
    """Material = distance more than 10% over plan, or Kendall-tau sequence similarity below 0.85."""
    over_distance = distance_increase_pct is not None and distance_increase_pct > DISTANCE_INCREASE_THRESHOLD_PCT
    reordered = similarity is not None and similarity < SIMILARITY_THRESHOLD
    return over_distance or reordered


def distance_increase_pct(planned_km: Optional[float], actual_km: Optional[float]) -> Optional[float]:
    """Percent by which the driven distance exceeded the plan; None when either value is unknown."""
    if not planned_km or actual_km is None:
        return None
    return round((actual_km - planned_km) / planned_km * 100.0, 1)


class RouteDeviationAnalyzer:
    """
    Computes sequence similarity, stop reordering, distance/duration impact,
    and narrative explanation for planned vs actual route execution.
    """
    @staticmethod
    def calculate_kendall_tau_distance(seq_a: List[int], seq_b: List[int]) -> float:
        """
        Calculates normalized Kendall Tau similarity index [0..1] between two sequences.
        1.0 means identical order, 0.0 means reverse order.
        """
        if len(seq_a) <= 1 or len(seq_a) != len(seq_b):
            return 1.0

        n = len(seq_a)
        # Create map from element to actual position
        pos_b = {val: idx for idx, val in enumerate(seq_b)}
        
        concordant = 0
        discordant = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                val_i = seq_a[i]
                val_j = seq_a[j]
                
                if val_i in pos_b and val_j in pos_b:
                    dir_a = i - j
                    dir_b = pos_b[val_i] - pos_b[val_j]
                    
                    if (dir_a * dir_b) > 0:
                        concordant += 1
                    else:
                        discordant += 1
                        
        total_pairs = (n * (n - 1)) / 2.0
        if total_pairs == 0:
            return 1.0
            
        tau = (concordant - discordant) / total_pairs
        # Normalize to [0..1]
        return max(0.0, min(1.0, (tau + 1.0) / 2.0))

    @classmethod
    def sequence_similarity(cls, planned_positions: List[int], actual_positions: List[int]) -> float:
        """Kendall-tau similarity between the planned order and the order the stops were actually visited."""
        visit_order = sorted(range(len(planned_positions)), key=lambda i: actual_positions[i])
        visited_planned = [planned_positions[i] for i in visit_order]
        return cls.calculate_kendall_tau_distance(sorted(planned_positions), visited_planned)

    @classmethod
    def analyze_route_deviation(cls, route: Route, stops: List[Stop]) -> Dict[str, Any]:
        """
        Analyzes route deviation comparing planned stop order vs actual stop order.
        """
        sorted_planned = sorted(stops, key=lambda s: s.planned_sequence)
        if not stops or any(s.actual_sequence is None for s in stops):
            return {
                "route_id": route.id,
                "external_route_id": route.external_route_id,
                "sequence_similarity_index": None,
                "stop_reorder_count": None,
                "reordered_stops": [],
                "planned_sequence_display": None,
                "actual_sequence_display": None,
                "additional_distance_km": None,
                "additional_duration_min": None,
                "deviation_percentage": None,
                "is_material_deviation": None,
                "explanation": "The source data has no actual visit order for this route, so deviation cannot be measured.",
            }
        sorted_actual = sorted(stops, key=lambda s: s.actual_sequence)

        similarity_index = cls.sequence_similarity(
            [s.planned_sequence for s in stops], [s.actual_sequence for s in stops]
        )

        # Identify reordered stops
        reordered_stops = []
        for p_stop in sorted_planned:
            stop_id = p_stop.external_stop_id or p_stop.id
            actual_pos = next((i + 1 for i, s in enumerate(sorted_actual) if (s.external_stop_id or s.id) == stop_id), p_stop.planned_sequence)
            if actual_pos != p_stop.planned_sequence:
                reordered_stops.append({
                    "stop_id": stop_id,
                    "address": p_stop.address,
                    "planned_sequence": p_stop.planned_sequence,
                    "actual_sequence": actual_pos
                })

        p_dist, a_dist = route.planned_distance_km, route.actual_distance_km
        p_dur, a_dur = route.planned_duration_min, route.actual_duration_min
        add_dist = max(0.0, round(a_dist - p_dist, 2)) if p_dist is not None and a_dist is not None else None
        add_dur = max(0.0, round(a_dur - p_dur, 1)) if p_dur is not None and a_dur is not None else None
        dev_pct = distance_increase_pct(p_dist, a_dist)

        is_material = is_material_deviation(dev_pct, similarity_index)

        # Both strings list stops by their planned number, so a reordering is visible in the actual one.
        planned_seq_str = "Depot → " + " → ".join([f"Stop #{s.planned_sequence}" for s in sorted_planned[:5]]) + (" → ..." if len(sorted_planned) > 5 else " → Depot")
        actual_seq_str = "Depot → " + " → ".join([f"Stop #{s.planned_sequence}" for s in sorted_actual[:5]]) + (" → ..." if len(sorted_actual) > 5 else " → Depot")

        # Construct explanation
        distance_note = (
            f"Distance changed by {add_dist:+} km ({dev_pct:+}%) and duration by {add_dur:+} min."
            if add_dist is not None and add_dur is not None and dev_pct is not None
            else "Planned/actual distance or duration not available."
        )
        if len(reordered_stops) > 0:
            reorder_desc = ", ".join([f"Stop #{r['planned_sequence']} moved to #{r['actual_sequence']}" for r in reordered_stops[:3]])
            explanation = f"Driver deviated from planned sequence ({reorder_desc}). {distance_note}"
        else:
            explanation = f"Route followed the planned sequence. {distance_note}"

        return {
            "route_id": route.id,
            "external_route_id": route.external_route_id,
            "sequence_similarity_index": round(similarity_index, 3),
            "stop_reorder_count": len(reordered_stops),
            "reordered_stops": reordered_stops,
            "planned_sequence_display": planned_seq_str,
            "actual_sequence_display": actual_seq_str,
            "additional_distance_km": add_dist,
            "additional_duration_min": add_dur,
            "deviation_percentage": dev_pct,
            "is_material_deviation": is_material,
            "explanation": explanation
        }
