'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi } from '@/lib/api';
import { useParams } from 'next/navigation';
import {
  MapPin,
  Cpu,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  TrendingDown,
  ShieldAlert,
  Play,
  RotateCcw,
  Check,
  X
} from 'lucide-react';

export default function RouteInvestigationPage() {
  const params = useParams();
  const routeId = params.id as string;

  const [route, setRoute] = useState<any>(null);
  const [riskData, setRiskData] = useState<any>(null);
  const [optResult, setOptResult] = useState<any>(null);
  const [simResult, setSimResult] = useState<any>(null);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [simulating, setSimulating] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const rData = await fetchApi<any>(`/routes/${routeId}`);
      setRoute(rData);

      // Fetch risk prediction
      const risk = await fetchApi<any>(`/routes/predict-risk`, {
        method: 'POST',
        body: JSON.stringify({ route_id: routeId })
      });
      setRiskData(risk);

      // Fetch recommendations list and find for this route
      const recs = await fetchApi<any[]>(`/recommendations`);
      const rec = recs.find((item: any) => item.route_id === routeId) || recs[0];
      setRecommendation(rec);

    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (routeId) loadData();
  }, [routeId]);

  const handleRunOptimizer = async () => {
    setOptimizing(true);
    try {
      const res = await fetchApi<any>(`/routes/${routeId}/optimize`, {
        method: 'POST',
        body: JSON.stringify({
          route_id: routeId,
          objective_weights: {
            distance_weight: 1.0,
            duration_weight: 1.5,
            late_penalty_weight: 10.0
          }
        })
      });
      setOptResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setOptimizing(false);
    }
  };

  const handleRunScenario = async (scenarioType: string) => {
    setSimulating(true);
    try {
      const res = await fetchApi<any>(`/routes/${routeId}/simulate`, {
        method: 'POST',
        body: JSON.stringify({
          route_id: routeId,
          scenario_type: scenarioType,
          vehicle_count: scenarioType === 'MULTI_VEHICLE' ? 2 : 1
        })
      });
      setSimResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setSimulating(false);
    }
  };

  const handleDecision = async (action: string) => {
    if (!recommendation) return;
    try {
      await fetchApi('/recommendations/decision', {
        method: 'POST',
        body: JSON.stringify({
          recommendation_id: recommendation.id,
          action: action,
          reason: `Dispatcher manually ${action.toLowerCase()}ed recommendation.`
        })
      });
      setRecommendation((prev: any) => ({ ...prev, status: action === 'ACCEPT' ? 'ACCEPTED' : 'REJECTED' }));
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div>
        <Header title="Route Investigation Workspace" />
        <div className="p-8 text-center text-slate-400 text-sm">Loading route telemetry...</div>
      </div>
    );
  }

  return (
    <div>
      <Header
        title={`Route Investigation Workspace: ${routeId}`}
        subtitle={`Driver: ${route?.driver_id || 'DRV_01'} • Depot: San Francisco Hub`}
      />

      <div className="p-8 space-y-8">
        {/* Top Metric Comparison: Planned vs Optimized vs Actual */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center">
            <Cpu className="w-4 h-4 text-indigo-400 mr-2" />
            <span>Planned vs Optimized vs Actual Telemetry</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400">PLANNED</span>
              <div className="text-xl font-bold text-slate-200 mt-1">{route?.planned_distance_km} km</div>
              <div className="text-xs text-slate-400 mt-0.5">{route?.planned_duration_min} min</div>
            </div>

            <div className="p-4 rounded-lg bg-indigo-950/40 border border-indigo-500/30">
              <span className="text-xs text-indigo-300 font-semibold">OPTIMIZED (OR-Tools)</span>
              <div className="text-xl font-bold text-indigo-400 mt-1">
                {optResult ? `${optResult.optimized_distance_km} km` : 'Run Solver'}
              </div>
              <div className="text-xs text-indigo-300 mt-0.5">
                {optResult ? `${optResult.optimized_duration_min} min (-${optResult.duration_savings_pct}%)` : 'Ready to run'}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400">ACTUAL DRIVEN</span>
              <div className="text-xl font-bold text-rose-400 mt-1">{route?.actual_distance_km} km</div>
              <div className="text-xs text-slate-400 mt-0.5">{route?.actual_duration_min} min</div>
            </div>

            <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400">SEQUENCE DEVIATION</span>
              <div className="text-xl font-bold text-amber-400 mt-1">
                {((route?.deviation?.sequence_similarity_index || 0.75) * 100).toFixed(0)}% Adherence
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                {route?.deviation?.stop_reorder_count || 2} stops reordered
              </div>
            </div>
          </div>
        </div>

        {/* Risk Prediction & Decision Engine Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Risk Scoring */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-sm font-bold text-slate-200">ML Delivery Risk Diagnosis</h3>
                  <p className="text-xs text-slate-400">Supervised ETA & Deviation Predictor</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                  riskData?.risk_level === 'CRITICAL' || riskData?.risk_level === 'HIGH'
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                }`}>
                  {riskData?.risk_level || 'HIGH'} RISK ({riskData?.composite_risk_score || 68}/100)
                </span>
              </div>

              <div className="mt-6 space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Predicted Delay</span>
                    <span className="text-slate-200 font-mono font-semibold">+{riskData?.predicted_delay_min || 18.5} min</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-amber-500 h-full" style={{ width: `${Math.min(100, ((riskData?.predicted_delay_min || 18.5)/30)*100)}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Late Delivery Probability</span>
                    <span className="text-slate-200 font-mono font-semibold">{((riskData?.late_probability || 0.62) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-rose-500 h-full" style={{ width: `${(riskData?.late_probability || 0.62) * 100}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Route Deviation Probability</span>
                    <span className="text-slate-200 font-mono font-semibold">{((riskData?.deviation_probability || 0.45) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full" style={{ width: `${(riskData?.deviation_probability || 0.45) * 100}%` }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Operational Dispatcher Recommendation */}
          <div className="glass-panel p-6 rounded-xl border border-indigo-500/30 bg-indigo-950/20 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">AI Operational Recommendation</span>
              <h3 className="text-base font-bold text-slate-100 mt-1">{recommendation?.title || 'Resequence Stop Order'}</h3>
              <p className="text-xs text-slate-300 mt-2 leading-relaxed">{recommendation?.explanation || 'Resequencing stops cuts duration variance.'}</p>

              <div className="mt-4 p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs space-y-1 font-mono">
                <div className="text-emerald-400">Est. Duration Saved: -{recommendation?.expected_impact?.saved_minutes || 24} min</div>
                <div className="text-indigo-300">Est. Distance Saved: -{recommendation?.expected_impact?.saved_km || 4.5} km</div>
              </div>
            </div>

            <div className="mt-6 flex items-center space-x-3 pt-4 border-t border-slate-800">
              {recommendation?.status === 'ACCEPTED' ? (
                <span className="px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center">
                  <Check className="w-4 h-4 mr-1.5" /> Recommendation Accepted & Executed
                </span>
              ) : recommendation?.status === 'REJECTED' ? (
                <span className="px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center">
                  <X className="w-4 h-4 mr-1.5" /> Recommendation Rejected
                </span>
              ) : (
                <>
                  <button
                    onClick={() => handleDecision('ACCEPT')}
                    id="btn-accept-recommendation"
                    className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md shadow-indigo-600/30 flex items-center justify-center space-x-1.5"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Accept & Dispatch</span>
                  </button>
                  <button
                    onClick={() => handleDecision('REJECT')}
                    id="btn-reject-recommendation"
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all border border-slate-700"
                  >
                    Reject
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* OR-Tools Optimizer & What-If Simulator Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* OR-Tools Engine Panel */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-200">Google OR-Tools VRP Solver</h3>
                <p className="text-xs text-slate-400">Constraint-Aware TSP / VRP Sequence Optimizer</p>
              </div>
              <button
                onClick={handleRunOptimizer}
                disabled={optimizing}
                id="btn-run-ortools-optimizer"
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all flex items-center space-x-1.5"
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>{optimizing ? 'Solving VRP...' : 'Execute Optimizer'}</span>
              </button>
            </div>

            {optResult ? (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex justify-between">
                  <span className="text-slate-400">Solver Compute Time:</span>
                  <span className="text-emerald-400 font-bold">{optResult.solver_time_ms} ms</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex justify-between">
                  <span className="text-slate-400">Distance Reduction:</span>
                  <span className="text-indigo-300">{optResult.baseline_distance_km} km → {optResult.optimized_distance_km} km (-{optResult.distance_savings_pct}%)</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex justify-between">
                  <span className="text-slate-400">Duration Reduction:</span>
                  <span className="text-indigo-300">{optResult.baseline_duration_min} min → {optResult.optimized_duration_min} min (-{optResult.duration_savings_pct}%)</span>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                Click 'Execute Optimizer' to run OR-Tools VRP solver on this stop sequence.
              </div>
            )}
          </div>

          {/* What-If Scenario Simulator Panel */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800">
            <h3 className="text-sm font-bold text-slate-200 mb-1">What-If Dispatch Scenario Simulator</h3>
            <p className="text-xs text-slate-400 mb-4">Simulate operational modifications before committing dispatch</p>

            <div className="flex flex-wrap gap-2 mb-4">
              <button
                onClick={() => handleRunScenario('RESEQUENCE')}
                disabled={simulating}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700"
              >
                Scenario A: Resequence Stops
              </button>
              <button
                onClick={() => handleRunScenario('MULTI_VEHICLE')}
                disabled={simulating}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700"
              >
                Scenario B: 2 Vehicles
              </button>
              <button
                onClick={() => handleRunScenario('TIME_OPTIMIZED')}
                disabled={simulating}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700"
              >
                Scenario C: Time Optimized
              </button>
            </div>

            {simResult ? (
              <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2 text-xs font-mono">
                <div className="text-slate-300 font-bold">{simResult.description}</div>
                <div className="text-emerald-400">Time Saved: {simResult.duration_saved_min} min</div>
                <div className="text-indigo-300">Distance Saved: {simResult.distance_saved_km} km</div>
                <div className="text-slate-400">Efficiency Gain: +{simResult.efficiency_gain_pct}%</div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                Select a What-If scenario above to calculate predicted impact.
              </div>
            )}
          </div>
        </div>

        {/* Stops Sequence Table */}
        <div className="glass-panel rounded-xl border border-slate-800 p-6">
          <h3 className="text-sm font-bold text-slate-200 mb-4">Route Stop Timeline & Adherence</h3>
          <div className="space-y-2">
            {route?.stops?.map((s: any, idx: number) => (
              <div key={s.id} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3">
                  <span className="w-6 h-6 rounded-full bg-slate-800 text-indigo-400 font-bold flex items-center justify-center font-mono">
                    {s.planned_sequence}
                  </span>
                  <div>
                    <span className="text-slate-200 font-medium">{s.address || `Stop #${s.planned_sequence}`}</span>
                    <span className="block text-[10px] text-slate-500 font-mono">{s.external_stop_id || s.id}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-slate-400">Service: {s.service_time_min} min</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    s.actual_sequence && s.actual_sequence !== s.planned_sequence
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-emerald-500/20 text-emerald-300'
                  }`}>
                    {s.actual_sequence && s.actual_sequence !== s.planned_sequence ? `Moved to #${s.actual_sequence}` : 'On Sequence'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
