# Route Optimization Specification — Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence

## Formulation

Single-vehicle stop re-sequencing (TSP-style), depot to depot, solved with the Google OR-Tools routing library (`pywrapcp`). Implementation: `backend/app/optimization/vrp.py`.

## Objective

```text
Minimize  total straight-line (Haversine) distance of the tour, in integer meters
```

The `objective_weights` request field is accepted for compatibility, but scaling every arc by the same distance weight does not change the optimal tour, and there is no duration, lateness or time-window term yet.

## Solver settings

- **First solution strategy**: `PATH_CHEAPEST_ARC`
- **Time limit**: 2 seconds per route
- **Distance matrix**: Haversine distance between the depot and every stop
- **Depot**: the route's station when the data has one (Amazon sample), otherwise the first planned stop

## Reported figures

- **Baseline**: the planned stop order measured with the same distance matrix (like-for-like). Only reported when the source data includes a dispatch plan.
- **Distance savings**: baseline vs optimized tour
- **Duration**: estimate = planned duration × (1 − 0.8 × distance-savings fraction), flagged `duration_is_estimate`
- **`reported_planned_distance_km`**: the planned distance stated in the source data, shown for reference

## Not modeled yet

Time windows, vehicle capacity, maximum route duration, road-network distances, and multi-vehicle routing. The simulator's multi-vehicle scenario is a rough approximation.
