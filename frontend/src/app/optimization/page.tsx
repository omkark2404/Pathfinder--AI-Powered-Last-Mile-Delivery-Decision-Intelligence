'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import { fetchApi } from '@/lib/api';
import { Cpu, Play, CheckCircle2, Sliders } from 'lucide-react';

export default function OptimizationPage() {
  const [selectedRoute, setSelectedRoute] = useState('RT_DEMO_02');
  const [distWeight, setDistWeight] = useState(1.0);
  const [durWeight, setDurWeight] = useState(1.5);
  const [latePenalty, setLatePenalty] = useState(10.0);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleRunOptimization = async () => {
    setLoading(true);
    try {
      const res = await fetchApi<any>(`/routes/${selectedRoute}/optimize`, {
        method: 'POST',
        body: JSON.stringify({
          route_id: selectedRoute,
          objective_weights: {
            distance_weight: distWeight,
            duration_weight: durWeight,
            late_penalty_weight: latePenalty
          }
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
      <Header title="Google OR-Tools VRP Optimizer Engine" subtitle="Constraint-Aware Route Optimization & Objective Weight Configuration" />

      <div className="p-8 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Objective Configuration Controls */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6">
            <h2 className="text-sm font-bold text-slate-200 flex items-center">
              <Sliders className="w-4 h-4 text-indigo-400 mr-2" />
              <span>Optimization Parameters</span>
            </h2>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Target Route ID</label>
              <select
                value={selectedRoute}
                onChange={(e) => setSelectedRoute(e.target.value)}
                id="select-opt-route"
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
              >
                <option value="RT_DEMO_02">RT_DEMO_02 (8 Stops)</option>
                <option value="RT_DEMO_04">RT_DEMO_04 (8 Stops)</option>
                <option value="RT_DEMO_01">RT_DEMO_01 (8 Stops)</option>
              </select>
            </div>

            <div className="space-y-4 pt-2">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Distance Cost Weight</span>
                  <span className="font-mono text-indigo-400">{distWeight}</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="5.0"
                  step="0.1"
                  value={distWeight}
                  onChange={(e) => setDistWeight(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Duration Cost Weight</span>
                  <span className="font-mono text-indigo-400">{durWeight}</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="5.0"
                  step="0.1"
                  value={durWeight}
                  onChange={(e) => setDurWeight(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Late Penalty Weight</span>
                  <span className="font-mono text-indigo-400">{latePenalty}</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="50.0"
                  step="1.0"
                  value={latePenalty}
                  onChange={(e) => setLatePenalty(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>

            <button
              onClick={handleRunOptimization}
              disabled={loading}
              id="btn-trigger-vrp-solver"
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center space-x-2"
            >
              <Cpu className="w-4 h-4" />
              <span>{loading ? 'Solving VRP Problem...' : 'Run OR-Tools Solver'}</span>
            </button>
          </div>

          {/* Results Output */}
          <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-slate-800">
            <h2 className="text-sm font-bold text-slate-200 mb-4">VRP Solution Output</h2>

            {result ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Baseline Distance</span>
                    <span className="text-lg font-bold text-slate-200 font-mono mt-1">{result.baseline_distance_km} km</span>
                  </div>
                  <div className="p-4 rounded-lg bg-indigo-950/40 border border-indigo-500/30">
                    <span className="text-xs text-indigo-300 font-semibold block">Optimized Distance</span>
                    <span className="text-lg font-bold text-indigo-400 font-mono mt-1">{result.optimized_distance_km} km</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Distance Saved</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono mt-1">-{result.distance_savings_pct}%</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                    <span className="text-xs text-slate-400 block">Solver Time</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono mt-1">{result.solver_time_ms} ms</span>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
                  <h3 className="text-xs font-bold text-slate-300 mb-3">Optimal TSP Node Order</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.optimized_sequence?.map((s: any, i: number) => (
                      <span key={i} className="px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-mono">
                        #{s.optimized_sequence}: {s.address}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                Select parameters and click 'Run OR-Tools Solver' to execute exact VRP routing.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
