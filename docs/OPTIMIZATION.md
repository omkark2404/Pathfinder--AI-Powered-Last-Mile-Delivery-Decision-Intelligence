# Route Optimization Specification — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Vehicle Routing Problem (VRP) Formulation

The optimization engine formulates stop sequence determination as a constraint-aware Vehicle Routing Problem (VRP) solved via Google OR-Tools (`pywrapcp`).

## Mathematical Objective

```text
Minimize Objective =
  (W_dist * Total_Travel_Distance_km) +
  (W_dur * Total_Travel_Duration_min) +
  (W_late * Late_Delivery_Penalty) +
  (W_tw * Time_Window_Violation_Penalty)
```

Default Weights:
- `W_dist` = 1.0
- `W_dur` = 1.5
- `W_late` = 10.0
- `W_tw` = 20.0

## Solvers & Heuristics

- **First Solution Strategy**: `PATH_CHEAPEST_ARC`
- **Distance Matrix Computation**: Haversine distance matrix between depot and all stop coordinates.
- **Constraints**: Depot origin/destination, maximum route duration, vehicle capacity limits.
