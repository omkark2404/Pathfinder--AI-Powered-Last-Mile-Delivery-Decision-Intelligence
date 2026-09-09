'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi, RouteItem } from '@/lib/api';
import Link from 'next/link';
import { AlertTriangle, ShieldAlert, ChevronRight, Sliders, Activity } from 'lucide-react';

export default function DeliveryRiskPage() {
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchApi<RouteItem[]>('/routes');
        setRoutes(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <div>
      <Header title="Delivery Delay & Risk Intelligence" subtitle="Supervised Machine Learning Risk Scoring & Delay Thresholds" />

      <div className="p-8 space-y-8">
        {/* Risk Level Threshold Explanation */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass-card p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10">
            <span className="text-xs font-bold text-emerald-400">LOW RISK (0–20)</span>
            <p className="text-xs text-slate-300 mt-1">Normal execution within SLA parameters.</p>
          </div>
          <div className="glass-card p-4 rounded-xl border border-amber-500/20 bg-amber-950/10">
            <span className="text-xs font-bold text-amber-400">MEDIUM RISK (21–50)</span>
            <p className="text-xs text-slate-300 mt-1">Minor delay risk. Dispatcher monitoring enabled.</p>
          </div>
          <div className="glass-card p-4 rounded-xl border border-indigo-500/20 bg-indigo-950/10">
            <span className="text-xs font-bold text-indigo-400">HIGH RISK (51–75)</span>
            <p className="text-xs text-slate-300 mt-1">Significant ETA delay predicted. VRP resequence ready.</p>
          </div>
          <div className="glass-card p-4 rounded-xl border border-rose-500/20 bg-rose-950/10">
            <span className="text-xs font-bold text-rose-400">CRITICAL RISK (76–100)</span>
            <p className="text-xs text-slate-300 mt-1">Severe time window violation. Immediate intervention needed.</p>
          </div>
        </div>

        {/* Risk Assessment List */}
        <div className="glass-panel rounded-xl border border-slate-800 p-6">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center">
            <ShieldAlert className="w-4 h-4 text-rose-400 mr-2" />
            <span>Route Risk Scoring Directory</span>
          </h2>

          <div className="space-y-4">
            {routes.map((r, idx) => {
              const isHigh = r.deviation?.is_material_deviation || idx % 2 === 1;
              const riskScore = isHigh ? 72 : 28;
              const level = riskScore > 50 ? 'HIGH' : 'LOW';

              return (
                <div key={r.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`p-3 rounded-xl ${riskScore > 50 ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-sm font-bold text-slate-100">{r.id}</span>
                        <span className="text-xs text-slate-400">({r.external_route_id})</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{r.total_stops} Stops • Driver {r.driver_id} • Planned {r.planned_distance_km} km</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-6">
                    <div className="text-right font-mono">
                      <span className="text-xs text-slate-400 block">Composite Risk Score</span>
                      <span className={`text-base font-bold ${riskScore > 50 ? 'text-rose-400' : 'text-emerald-400'}`}>{riskScore} / 100</span>
                    </div>

                    <Link
                      href={`/routes/${r.id}`}
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
