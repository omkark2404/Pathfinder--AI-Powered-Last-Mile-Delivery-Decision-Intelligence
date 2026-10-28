const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE}/api/v1`;

export interface HealthInfo {
  data_mode: 'synthetic_demo' | 'bundled_samples' | 'public_datasets';
  data_mode_note: string;
  data_sources: Record<string, string>;
}

export const DATA_MODE_LABELS: Record<HealthInfo['data_mode'], string> = {
  synthetic_demo: 'Synthetic demo data',
  bundled_samples: 'Bundled samples · partly synthetic',
  public_datasets: 'Public datasets',
};

let healthRequest: Promise<HealthInfo> | null = null;

/** /health lives outside /api/v1; one shared request per page load. */
export function fetchHealth(): Promise<HealthInfo> {
  if (!healthRequest) {
    healthRequest = fetchApi<HealthInfo>(`${API_BASE}/health`).catch((e) => {
      healthRequest = null;
      throw e;
    });
  }
  return healthRequest;
}

/** Show a measured value, or "n/a" when the source data does not have it. */
export function fmt(value: number | null | undefined, suffix = ''): string {
  return value === null || value === undefined ? 'n/a' : `${value}${suffix}`;
}

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
  avg_delay_minutes: number | null;
  p90_delay_minutes: number | null;
  p95_delay_minutes: number | null;
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
  route_date: string | null;
  planned_distance_km: number | null;
  actual_distance_km: number | null;
  planned_duration_min: number | null;
  actual_duration_min: number | null;
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

export interface RiskScoreItem {
  route_id: string;
  external_route_id: string;
  total_stops: number;
  planned_distance_km: number | null;
  data_complete: boolean;
  composite_risk_score: number | null;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | null;
  predicted_delay_min: number | null;
  deviation_probability: number | null;
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
