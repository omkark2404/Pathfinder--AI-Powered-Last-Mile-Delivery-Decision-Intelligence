'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import { fetchApi } from '@/lib/api';
import { Sliders, Play, CheckCircle2 } from 'lucide-react';

export default function ScenariosPage() {
  const [selectedRoute, setSelectedRoute] = useState('RT_DEMO_02');
  const [scenarioType, setScenarioType] = useState('RESEQUENCE');
  const [vehicleCount, setVehicleCount] = useState(2);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
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
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header title="What-If Dispatch Scenario Simulator" subtitle="Simulate Route Modifications & Quantify Operational Business Impact" />

      <div className="p-8 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
            <h2 className="text-sm font-bold text-slate-200 flex items-center">
              <Sliders className="w-4 h-4 text-indigo-400 mr-2" />
              <span>Scenario Selection</span>
            </h2>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Target Route</label>
              <select
                value={selectedRoute}
                onChange={(e) => setSelectedRoute(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
              >
                <option value="RT_DEMO_02">RT_DEMO_02</option>
                <option value="RT_DEMO_04">RT_DEMO_04</option>
                <option value="RT_DEMO_01">RT_DEMO_01</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">What-If Action</label>
              <select
                value={scenarioType}
                onChange={(e) => setScenarioType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
              >
                <option value="RESEQUENCE">Scenario A: Resequence Stops</option>
                <option value="MULTI_VEHICLE">Scenario B: Split to 2 Vehicles</option>
                <option value="TIME_OPTIMIZED">Scenario C: Minimize Duration</option>
                <option value="TIME_WINDOW_PRIORITY">Scenario D: Time Window Priority</option>
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
              </div>
            )}

            <button
              onClick={handleSimulate}
              disabled={loading}
              id="btn-run-scenario-sim"
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{loading ? 'Simulating...' : 'Simulate Scenario Impact'}</span>
            </button>
          </div>

          {/* Results Output */}
          <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-slate-800">
            <h2 className="text-sm font-bold text-slate-200 mb-4">Simulation Impact Report</h2>

            {result ? (
              <div className="space-y-6">
                <div className="p-4 rounded-lg bg-indigo-950/30 border border-indigo-500/30 text-xs font-mono text-indigo-300">
                  {result.description}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Distance Saved</span>
                    <span className="text-lg font-bold text-indigo-400 font-mono mt-1">-{result.distance_saved_km} km</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Duration Saved</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono mt-1">-{result.duration_saved_min} min</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Efficiency Gain</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono mt-1">+{result.efficiency_gain_pct}%</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                Choose a scenario and click 'Simulate Scenario Impact' to compute savings.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
