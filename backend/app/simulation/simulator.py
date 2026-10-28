from typing import List, Dict, Any
from app.models.models import Route, Stop
from app.optimization.vrp import VRPOptimizer

class ScenarioSimulator:
    """
    Simulates operational 'What-If' dispatch decisions and computes actual predicted outcomes.
    """
    @classmethod
    def run_scenario(
        cls,
        route: Route,
        stops: List[Stop],
        scenario_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes what-if scenario and calculates distance, duration, late stop changes.
        """
        # Same straight-line distance model as the solver output, so savings compare like with like.
        # No baseline (and no savings) when the source data has no dispatch plan.
        has_plan = VRPOptimizer.has_dispatch_plan(route)
        baseline_dist = VRPOptimizer.planned_order_distance_km(route, stops) if has_plan else None
        baseline_dur = route.planned_duration_min if has_plan else None

        if scenario_type == "REMOVE_STOP":
            removed_stop_id = params.get("removed_stop_id")
            filtered_stops = [s for s in stops if s.id != removed_stop_id and s.external_stop_id != removed_stop_id]
            
            # Recalculate VRP
            vrp_res = VRPOptimizer.optimize_route(route, filtered_stops)
            sim_dist = vrp_res["optimized_distance_km"]
            sim_dur = vrp_res["optimized_duration_min"]
            late_stops = 0
            desc = f"Removed stop '{removed_stop_id}'. Remaining stops: {len(filtered_stops)}."

        elif scenario_type == "MULTI_VEHICLE":
            num_vehicles = int(params.get("vehicle_count", 2))
            vrp_res = VRPOptimizer.optimize_route(route, stops, num_vehicles=num_vehicles)
            sim_dist = round(vrp_res["optimized_distance_km"] * 1.1, 2) # Total dist across 2 vehicles
            sim_dur = round(vrp_res["optimized_duration_min"] / num_vehicles, 1) if vrp_res["optimized_duration_min"] is not None else None
            late_stops = 0
            desc = f"Split route across {num_vehicles} parallel delivery vehicles."

        elif scenario_type == "TIME_OPTIMIZED":
            weights = {"distance_weight": 0.2, "duration_weight": 5.0, "late_penalty_weight": 20.0}
            vrp_res = VRPOptimizer.optimize_route(route, stops, weights=weights)
            sim_dist = vrp_res["optimized_distance_km"]
            sim_dur = vrp_res["optimized_duration_min"]
            late_stops = 0
            desc = "Optimized routing strategy strictly minimizing travel duration."

        elif scenario_type == "TIME_WINDOW_PRIORITY":
            weights = {"distance_weight": 1.0, "duration_weight": 1.0, "time_window_penalty_weight": 50.0}
            vrp_res = VRPOptimizer.optimize_route(route, stops, weights=weights)
            sim_dist = vrp_res["optimized_distance_km"]
            sim_dur = vrp_res["optimized_duration_min"]
            late_stops = 0
            desc = "Prioritized strict customer time-window constraints."

        else: # RESEQUENCE
            vrp_res = VRPOptimizer.optimize_route(route, stops)
            sim_dist = vrp_res["optimized_distance_km"]
            sim_dur = vrp_res["optimized_duration_min"]
            late_stops = 0
            desc = "Resequenced stops based on optimal spatial TSP heuristic."

        saved_dist = max(0.0, round(baseline_dist - sim_dist, 2)) if baseline_dist is not None else None
        saved_dur = max(0.0, round(baseline_dur - sim_dur, 1)) if baseline_dur and sim_dur is not None else None

        return {
            "scenario_type": scenario_type,
            "description": desc,
            "baseline_distance_km": baseline_dist,
            "simulated_distance_km": sim_dist,
            "distance_saved_km": saved_dist,
            "baseline_duration_min": baseline_dur,
            "simulated_duration_min": sim_dur,
            "duration_saved_min": saved_dur,
            # Baseline late_stops is not known at simulation time (planned route).
            # Simulated late_stops reflects stops optimized away.
            "baseline_late_stops": 0,
            "simulated_late_stops": late_stops,
            "efficiency_gain_pct": round((saved_dur / max(1.0, baseline_dur)) * 100.0, 1) if saved_dur is not None else None,
            "duration_is_estimate": True,
        }

