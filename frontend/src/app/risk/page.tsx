'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi, RiskScoreItem } from '@/lib/api';
import Link from 'next/link';
import { AlertTriangle, ShieldAlert, ChevronRight } from 'lucide-react';

const LEVEL_STYLES: Record<string, { box: string; text: string }> = {
  LOW: { box: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20', text: 'text-emerald-400' },
  MEDIUM: { box: 'bg-amber-500/10 text-amber-400 border border-amber-500/20', text: 'text-amber-400' },
  HIGH: { box: 'bg-orange-500/10 text-orange-400 border border-orange-500/20', text: 'text-orange-400' },
  CRITICAL: { box: 'bg-rose-500/10 text-rose-400 border border-rose-500/20', text: 'text-rose-400' },
};
const UNSCORED = { box: 'bg-slate-800 text-slate-500 border border-slate-700', text: 'text-slate-500' };

export default function DeliveryRiskPage() {
  const [scores, setScores] = useState<RiskScoreItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchApi<RiskScoreItem[]>('/risk-scores');
        // Highest risk first; routes that cannot be scored go last.
        data.sort((a, b) => (b.composite_risk_score ?? -1) - (a.composite_risk_score ?? -1));
        setScores(data);
      } catch (e) {
        console.error(e);
        setError('Could not load risk scores from the API.');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <div>
      <Header title="Delivery Delay & Risk Intelligence" subtitle="Composite 0–100 score from the prototype models (training status on the Models page)" />

      <div className="p-8 space-y-8">
        {/* Risk bands and the action the decision rules attach to each */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass-card p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10">
            <span className="text-xs font-bold text-emerald-400">LOW RISK (0–20)</span>
            <p className="text-xs text-slate-300 mt-1">Rule: monitor.</p>
          </div>
          <div className="glass-card p-4 rounded-xl border border-amber-500/20 bg-amber-950/10">
            <span className="text-xs font-bold text-amber-400">MEDIUM RISK (21–50)</span>
            <p className="text-xs text-slate-300 mt-1">Rule: monitor, or resequence if deviation probability &gt; 0.4.</p>
          </div>
          <div className="glass-card p-4 rounded-xl border border-orange-500/20 bg-orange-950/10">
            <span className="text-xs font-bold text-orange-400">HIGH RISK (51–75)</span>
            <p className="text-xs text-slate-300 mt-1">Rule: reroute with the solver&apos;s stop sequence.</p>
          </div>
          <div className="glass-card p-4 rounded-xl border border-rose-500/20 bg-rose-950/10">
            <span className="text-xs font-bold text-rose-400">CRITICAL RISK (76–100)</span>
            <p className="text-xs text-slate-300 mt-1">Rule: escalate to a senior dispatcher.</p>
          </div>
        </div>

        <div className="glass-panel rounded-xl border border-slate-800 p-6">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center">
            <ShieldAlert className="w-4 h-4 text-rose-400 mr-2" />
            <span>Route Risk Scoring Directory</span>
          </h2>

          {error && <p className="text-xs text-rose-300 mb-4">{error}</p>}
          {loading && <p className="text-xs text-slate-400">Loading risk scores…</p>}

          <div className="space-y-4">
            {scores.map((s) => {
              const style = s.risk_level ? LEVEL_STYLES[s.risk_level] : UNSCORED;
              return (
                <div key={s.route_id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`p-3 rounded-xl ${style.box}`}>
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="font-mono text-sm font-bold text-slate-100">{s.external_route_id}</span>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {s.total_stops} Stops • Planned {s.planned_distance_km != null ? `${s.planned_distance_km} km` : 'distance n/a'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-6">
                    <div className="text-right font-mono">
                      <span className="text-xs text-slate-400 block">Composite Risk Score</span>
                      {s.data_complete ? (
                        <span className={`text-base font-bold ${style.text}`}>{s.composite_risk_score} / 100 · {s.risk_level}</span>
                      ) : (
                        <span className="text-xs text-slate-500">Not scored: no planned distance/duration</span>
                      )}
                    </div>

                    <Link
                      href={`/routes/${s.route_id}`}
                      className="px-3.5 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold flex items-center"
                    >
                      <span>Diagnose</span>
                      <ChevronRight className="w-3.5 h-3.5 ml-1" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
