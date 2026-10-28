'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi, fmt, RouteItem } from '@/lib/api';
import { Sliders, Play } from 'lucide-react';

export default function ScenariosPage() {
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [selectedRoute, setSelectedRoute] = useState('');
  const [scenarioType, setScenarioType] = useState('RESEQUENCE');
  const [vehicleCount, setVehicleCount] = useState(2);
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

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchApi<any>(`/routes/${selectedRoute}/simulate`, {
        method: 'POST',
        body: JSON.stringify({
          route_id: selectedRoute,
          scenario_type: scenarioType,
          vehicle_count: vehicleCount
        })
      });
      setResult(res);
    } catch (e) {
      console.error(e);
      setError('The scenario request failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header title="What-If Dispatch Scenario Simulator" subtitle="Compare a route's planned stop order with solver-based alternatives" />

      <div className="p-8 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
            <h2 className="text-sm font-bold text-slate-200 flex items-center">
              <Sliders className="w-4 h-4 text-indigo-400 mr-2" />
              <span>Scenario Selection</span>
            </h2>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Route</label>
              <select
                value={selectedRoute}
                onChange={(e) => setSelectedRoute(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
              >
                {routes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.external_route_id} ({r.total_stops} stops)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">What-If Action</label>
              <select
                value={scenarioType}
                onChange={(e) => setScenarioType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
              >
                <option value="RESEQUENCE">Resequence stops (OR-Tools)</option>
                <option value="MULTI_VEHICLE">Split across vehicles (rough estimate)</option>
              </select>
            </div>

            {scenarioType === 'MULTI_VEHICLE' && (
              <div>
                <label className="text-xs text-slate-400 block mb-1">Number of Vehicles</label>
                <input
                  type="number"
                  min="2"
                  max="4"
                  value={vehicleCount}
                  onChange={(e) => setVehicleCount(parseInt(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
                />
                <p className="text-[11px] text-slate-500 mt-1">Approximation: distance +10%, duration divided by vehicle count.</p>
              </div>
            )}

            <button
              onClick={handleSimulate}
              disabled={loading || !selectedRoute}
              id="btn-run-scenario-sim"
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{loading ? 'Simulating…' : 'Simulate Scenario'}</span>
            </button>
            {error && <p className="text-xs text-rose-300">{error}</p>}
          </div>

          <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-slate-800">
            <h2 className="text-sm font-bold text-slate-200 mb-4">Simulation Result</h2>

            {result ? (
              <div className="space-y-6">
                <div className="p-4 rounded-lg bg-indigo-950/30 border border-indigo-500/30 text-xs font-mono text-indigo-300">
                  {result.description}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Distance saved (straight-line)</span>
                    <span className="text-lg font-bold text-indigo-400 font-mono mt-1">{fmt(result.distance_saved_km, ' km')}</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Duration saved (estimate)</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono mt-1">{fmt(result.duration_saved_min, ' min')}</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Duration change (estimate)</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono mt-1">{fmt(result.efficiency_gain_pct, '%')}</span>
                  </div>
                </div>
                {result.distance_saved_km == null && (
                  <p className="text-xs text-slate-400">This route&apos;s source data has no dispatch plan, so savings cannot be computed.</p>
                )}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                Choose a route and scenario, then run the simulation.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
