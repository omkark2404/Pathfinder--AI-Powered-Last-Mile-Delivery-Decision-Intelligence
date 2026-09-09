'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi } from '@/lib/api';
import { BrainCircuit, CheckCircle2, ShieldCheck, Activity, AlertCircle, Database } from 'lucide-react';

export default function ModelsPage() {
  const [metricsData, setMetricsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const data = await fetchApi<any>('/metrics');
        setMetricsData(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadMetrics();
  }, []);

  const etaModel = metricsData?.eta_model;
  const devModel = metricsData?.deviation_model;
  const etaMetrics = etaModel?.metrics;
  const devMetrics = devModel?.metrics;
  const isDemoMode = etaModel?.data_mode === 'synthetic_demo';

  return (
    <div>
      <Header
        title="Machine Learning Models & Evaluation Metrics"
        subtitle="Supervised Models, Evaluation Benchmarks & Temporal Leakage Prevention"
      />

      <div className="p-8 space-y-8">
        {/* Data Mode Alert Banner */}
        {isDemoMode && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
            <div className="text-xs space-y-1">
              <div className="font-bold flex items-center space-x-2">
                <span>SYNTHETIC DEMO MODE — REAL DATASET FILES NOT FOUND</span>
                <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-200">synthetic_demo</span>
              </div>
              <p className="text-amber-300/80">
                Evaluation metrics report <code className="bg-slate-900/60 px-1 py-0.5 rounded font-mono">insufficient_data</code> because real Amazon Last Mile and Mendeley dataset files are not placed in <code className="bg-slate-900/60 px-1 py-0.5 rounded font-mono">./data/</code>. No fake numbers are displayed. Place raw dataset files in <code className="bg-slate-900/60 px-1 py-0.5 rounded font-mono">./data/</code> and run dataset ingestion to train and compute real metrics.
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* ETA Regressor Model Metrics */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Supervised Regression</span>
                <h3 className="text-base font-bold text-slate-100 mt-0.5">ETA / Delay Prediction Model</h3>
              </div>
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300">
                {etaModel?.algorithm || 'GradientBoostingRegressor'}
              </span>
            </div>

            {etaModel?.evaluation_status === 'insufficient_data' ? (
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 text-xs font-mono">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Evaluation Status:</span>
                  <span className="text-amber-400 font-bold">insufficient_data</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Sample Count:</span>
                  <span className="text-slate-200">{etaModel?.evaluation_sample_count || 5} (min 10 required)</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Data Mode:</span>
                  <span className="text-amber-300 font-bold">{etaModel?.data_mode || 'synthetic_demo'}</span>
                </div>
                <p className="text-[11px] text-slate-500 pt-2 border-t border-slate-800">
                  Metrics will be automatically calculated when trained on ≥10 samples from real datasets.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 font-mono text-xs pt-2">
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Mean Absolute Error (MAE)</span>
                  <span className="text-indigo-400 font-bold text-sm mt-0.5 block">
                    {etaMetrics?.mae != null ? `${etaMetrics.mae} min` : 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Root Mean Sq. Error (RMSE)</span>
                  <span className="text-indigo-400 font-bold text-sm mt-0.5 block">
                    {etaMetrics?.rmse != null ? `${etaMetrics.rmse} min` : 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Median Abs Error</span>
                  <span className="text-emerald-400 font-bold text-sm mt-0.5 block">
                    {etaMetrics?.median_ae != null ? `${etaMetrics.median_ae} min` : 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">P90 Absolute Error</span>
                  <span className="text-amber-400 font-bold text-sm mt-0.5 block">
                    {etaMetrics?.p90_error != null ? `${etaMetrics.p90_error} min` : 'N/A'}
                  </span>
                </div>
              </div>
            )}

            <div className="text-xs text-slate-400 font-mono space-y-1">
              <p>Canonical Features: 9 features (stop_count, planned_distance, planned_duration, driver_adherence, TW_pressure, complexity)</p>
              <p>Leakage Prevention: Strictly temporal data ≤ T₀ (no actual arrival times used as features)</p>
            </div>
          </div>

          {/* Route Deviation Classifier Metrics */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Binary Classifier</span>
                <h3 className="text-base font-bold text-slate-100 mt-0.5">Route Deviation Classifier</h3>
              </div>
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300">
                {devModel?.algorithm || 'RandomForestClassifier'}
              </span>
            </div>

            {devModel?.evaluation_status === 'insufficient_data' ? (
              <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 text-xs font-mono">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Evaluation Status:</span>
                  <span className="text-amber-400 font-bold">insufficient_data</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Sample Count:</span>
                  <span className="text-slate-200">{devModel?.evaluation_sample_count || 5} (min 10 required)</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Data Mode:</span>
                  <span className="text-amber-300 font-bold">{devModel?.data_mode || 'synthetic_demo'}</span>
                </div>
                <p className="text-[11px] text-slate-500 pt-2 border-t border-slate-800">
                  Metrics will be automatically calculated when trained on ≥10 samples from real datasets.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 font-mono text-xs pt-2">
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Precision</span>
                  <span className="text-indigo-400 font-bold text-sm mt-0.5 block">
                    {devMetrics?.precision != null ? devMetrics.precision : 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Recall</span>
                  <span className="text-indigo-400 font-bold text-sm mt-0.5 block">
                    {devMetrics?.recall != null ? devMetrics.recall : 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">F1 Score</span>
                  <span className="text-emerald-400 font-bold text-sm mt-0.5 block">
                    {devMetrics?.f1_score != null ? devMetrics.f1_score : 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">PR-AUC</span>
                  <span className="text-emerald-400 font-bold text-sm mt-0.5 block">
                    {devMetrics?.pr_auc != null ? devMetrics.pr_auc : 'N/A'}
                  </span>
                </div>
              </div>
            )}

            <div className="text-xs text-slate-400 font-mono space-y-1">
              <p>Target: Binary classification (is_material_deviation: sequence similarity &lt; 0.85 or distance variance &gt; 10%)</p>
              <p>Evaluation: Stratified split with sklearn average_precision_score (PR-AUC)</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
