const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE}/api/v1`;

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_V1}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API Error ${res.status}: ${res.statusText}`);
  }

  return res.json();
}

export interface OverviewMetrics {
  total_routes: number;
  total_deliveries: number;
  on_time_delivery_rate: number;
  late_delivery_rate: number;
  avg_delay_minutes: number;
  p90_delay_minutes: number;
  p95_delay_minutes: number;
  avg_route_efficiency_pct: number;
  route_deviation_rate: number;
  high_risk_routes_count: number;
  optimization_opportunities_count: number;
}

export interface RouteItem {
  id: string;
  external_route_id: string;
  driver_id: string;
  vehicle_id: string;
  route_date: string;
  planned_distance_km: number;
  actual_distance_km: number;
  planned_duration_min: number;
  actual_duration_min: number;
  total_stops: number;
  status: string;
  metrics?: {
    distance_variance_km: number;
    duration_variance_min: number;
    on_time_delivery_rate: number;
    late_delivery_count: number;
    route_efficiency_score: number;
  };
  deviation?: {
    sequence_similarity_index: number;
    stop_reorder_count: number;
    additional_distance_km: number;
    additional_duration_min: number;
    deviation_percentage: number;
    is_material_deviation: boolean;
    explanation: string;
  };
}

export interface RecommendationItem {
  id: string;
  route_id: string;
  risk_score: number;
  action_type: string;
  title: string;
  explanation: string;
  expected_impact: {
    saved_minutes: number;
    saved_km: number;
    reduced_late_risk_pct: number;
  };
  evidence: any;
  status: string;
}
