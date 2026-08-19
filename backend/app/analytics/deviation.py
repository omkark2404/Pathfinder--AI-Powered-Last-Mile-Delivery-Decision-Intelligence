import math
from typing import List, Dict, Any, Tuple
from app.models.models import Route, Stop, RouteDeviation

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
    def analyze_route_deviation(cls, route: Route, stops: List[Stop]) -> Dict[str, Any]:
        """
        Analyzes route deviation comparing planned stop order vs actual stop order.
        """
        sorted_planned = sorted(stops, key=lambda s: s.planned_sequence)
        sorted_actual = sorted(stops, key=lambda s: s.actual_sequence or s.planned_sequence)

        planned_ids = [s.external_stop_id or s.id for s in sorted_planned]
        actual_ids = [s.external_stop_id or s.id for s in sorted_actual]

        # Calculate similarity
        seq_a = list(range(len(planned_ids)))
        seq_b_map = {stop_id: idx for idx, stop_id in enumerate(planned_ids)}
        seq_b = [seq_b_map.get(sid, i) for i, sid in enumerate(actual_ids)]

        similarity_index = cls.calculate_kendall_tau_distance(seq_a, seq_b)

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

        p_dist = route.planned_distance_km or 1.0
        a_dist = route.actual_distance_km or p_dist
        p_dur = route.planned_duration_min or 1.0
        a_dur = route.actual_duration_min or p_dur

        add_dist = max(0.0, round(a_dist - p_dist, 2))
        add_dur = max(0.0, round(a_dur - p_dur, 1))
        dev_pct = round((add_dist / p_dist) * 100.0, 1)

        is_material = dev_pct > 10.0 or len(reordered_stops) > 0

        # Construct visual sequence string
        planned_seq_str = "Depot → " + " → ".join([f"Stop #{s.planned_sequence}" for s in sorted_planned[:5]]) + (" → ..." if len(sorted_planned) > 5 else " → Depot")
        actual_seq_str = "Depot → " + " → ".join([f"Stop #{s.actual_sequence or s.planned_sequence}" for s in sorted_actual[:5]]) + (" → ..." if len(sorted_actual) > 5 else " → Depot")

        # Construct explanation
        if len(reordered_stops) > 0:
            reorder_desc = ", ".join([f"Stop #{r['planned_sequence']} moved to #{r['actual_sequence']}" for r in reordered_stops[:3]])
            explanation = f"Driver deviated from planned sequence ({reorder_desc}). Distance increased by +{add_dist} km (+{dev_pct}%) and duration by +{add_dur} mins."
        else:
            explanation = f"Route followed planned sequence cleanly with minimal variance (+{add_dist} km, +{add_dur} mins)."

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
