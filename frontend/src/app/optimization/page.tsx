'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi, fmt, RouteItem } from '@/lib/api';
import { Cpu, Sliders } from 'lucide-react';

export default function OptimizationPage() {
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [selectedRoute, setSelectedRoute] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi<RouteItem[]>('/routes')
      .then((data) => {
        setRoutes(data);
        // Default to a route that has a dispatch plan, so savings can be shown.
        const first = data.find((r) => r.planned_distance_km != null) ?? data[0];
        if (first) setSelectedRoute(first.id);
      })
      .catch(() => setError('Could not load routes from the API.'));
  }, []);

  const handleRunOptimization = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchApi<any>(`/routes/${selectedRoute}/optimize`, {
        method: 'POST',
        body: JSON.stringify({ route_id: selectedRoute }),
      });
      setResult(res);
    } catch (e) {
      console.error(e);
      setError('The optimizer request failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header title="Google OR-Tools Route Optimizer" subtitle="Re-sequences a route's stops to minimize straight-line (Haversine) distance" />

      <div className="p-8 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
            <h2 className="text-sm font-bold text-slate-200 flex items-center">
              <Sliders className="w-4 h-4 text-indigo-400 mr-2" />
              <span>Optimization Setup</span>
            </h2>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Route</label>
              <select
                value={selectedRoute}
                onChange={(e) => setSelectedRoute(e.target.value)}
                id="select-opt-route"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
              >
                {routes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.external_route_id} ({r.total_stops} stops)
                  </option>
                ))}
              </select>
            </div>

            <div className="text-xs text-slate-400 space-y-1.5 leading-relaxed">
              <p><span className="text-slate-300 font-semibold">Objective:</span> minimize total straight-line distance, depot to depot.</p>
              <p><span className="text-slate-300 font-semibold">Not modeled yet:</span> road network, time windows, vehicle capacity.</p>
              <p><span className="text-slate-300 font-semibold">Search:</span> PATH_CHEAPEST_ARC first solution, 2 s time limit.</p>
            </div>

            <button
              onClick={handleRunOptimization}
              disabled={loading || !selectedRoute}
              id="btn-trigger-vrp-solver"
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2"
            >
              <Cpu className="w-4 h-4" />
              <span>{loading ? 'Solving…' : 'Run OR-Tools Solver'}</span>
            </button>
            {error && <p className="text-xs text-rose-300">{error}</p>}
          </div>

          <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-slate-800">
            <h2 className="text-sm font-bold text-slate-200 mb-4">Solver Output</h2>

            {result ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Planned order (straight-line)</span>
                    <span className="text-lg font-bold text-slate-200 font-mono mt-1">{fmt(result.baseline_distance_km, ' km')}</span>
                  </div>
                  <div className="p-4 rounded-lg bg-indigo-950/40 border border-indigo-500/30">
                    <span className="text-xs text-indigo-300 font-semibold block">Optimized order</span>
                    <span className="text-lg font-bold text-indigo-400 font-mono mt-1">{result.optimized_distance_km} km</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Distance saved</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono mt-1">
                      {result.distance_savings_pct != null ? `-${result.distance_savings_pct}%` : 'n/a'}
                    </span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Solver Time</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono mt-1">{result.solver_time_ms} ms</span>
                  </div>
                </div>
                {result.baseline_distance_km == null && (
                  <p className="text-xs text-slate-400">This route&apos;s source data has no dispatch plan, so there is no baseline to compare the optimized tour against.</p>
                )}

                <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                  <h3 className="text-xs font-bold text-slate-300 mb-3">Optimized stop order (best found within the time limit)</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.optimized_sequence?.map((s: any) => (
                      <span key={s.stop_id} className="px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-mono">
                        #{s.optimized_sequence} ← planned #{s.original_sequence}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                Pick a route and run the solver.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
