'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi } from '@/lib/api';
import { Users, Award, ShieldCheck } from 'lucide-react';

export default function DriversPage() {
  const [drivers, setDrivers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDrivers = async () => {
      try {
        const data = await fetchApi<any[]>('/drivers');
        setDrivers(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadDrivers();
  }, []);

  return (
    <div>
      <Header title="Driver Utilization & Adherence Analytics" subtitle="Context-Aware Performance Analysis & Difficulty-Adjusted Metrics" />

      <div className="p-8 space-y-6">
        <div className="glass-panel p-6 rounded-xl border border-slate-800">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center">
            <Users className="w-4 h-4 text-indigo-400 mr-2" />
            <span>Driver Adherence Directory</span>
          </h2>

          <div className="space-y-4">
            {drivers.map((d) => (
              <div key={d.driver_id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="font-mono text-sm font-bold text-slate-100">{d.name}</span>
                  <span className="text-xs text-slate-400 ml-2">({d.external_driver_id})</span>
                  <p className="text-xs text-slate-400 mt-1">{d.performance_context}</p>
                </div>

                <div className="flex items-center space-x-6 font-mono text-xs">
                  <div>
                    <span className="text-slate-500 block">Adherence Rate</span>
                    <span className="text-emerald-400 font-bold">{(d.adherence_rate * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Avg Delay</span>
                    <span className="text-slate-300">{d.avg_delay_min} min</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Difficulty Index</span>
                    <span className="text-indigo-400 font-bold">{d.route_difficulty_index}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
