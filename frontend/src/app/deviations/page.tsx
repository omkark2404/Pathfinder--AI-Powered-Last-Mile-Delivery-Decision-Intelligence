'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi, RouteItem } from '@/lib/api';
import Link from 'next/link';
import { GitFork, ChevronRight, ArrowRight } from 'lucide-react';

export default function RouteDeviationsPage() {
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
      <Header title="Route Deviation Intelligence" subtitle="Planned vs Actual Driver Route Execution & Sequence Adherence" />

      <div className="p-8 space-y-6">
        <div className="glass-panel p-6 rounded-xl border border-slate-800">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center">
            <GitFork className="w-4 h-4 text-indigo-400 mr-2" />
            <span>Route Sequence Divergence Breakdown</span>
          </h2>

          <div className="space-y-4">
            {routes.map((r) => {
              const dev = r.deviation;
              const simPct = ((dev?.sequence_similarity_index || 0.8) * 100).toFixed(0);
              return (
                <div key={r.id} className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-mono text-sm font-bold text-indigo-400">{r.id}</span>
                      <span className="text-xs text-slate-400 ml-2">Driver {r.driver_id}</span>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                      dev?.is_material_deviation
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}>
                      {dev?.is_material_deviation ? 'MATERIAL DEVIATION' : 'ADHERENT'}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 font-medium leading-relaxed">{dev?.explanation || 'Driver executed route as planned.'}</p>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 border-t border-slate-800 text-xs font-mono">
                    <div>
                      <span className="text-slate-500 block">Sequence Similarity</span>
                      <span className="text-slate-200 font-bold">{simPct}% Adherence</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Extra Distance</span>
                      <span className="text-amber-400 font-bold">+{dev?.additional_distance_km || 0} km (+{dev?.deviation_percentage || 0}%)</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Extra Time</span>
                      <span className="text-rose-400 font-bold">+{dev?.additional_duration_min || 0} min</span>
                    </div>
                  </div>

                  <div className="pt-2 text-right">
                    <Link
                      href={`/routes/${r.id}`}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center"
                    >
                      <span>View Stop Sequence Matrix</span>
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
