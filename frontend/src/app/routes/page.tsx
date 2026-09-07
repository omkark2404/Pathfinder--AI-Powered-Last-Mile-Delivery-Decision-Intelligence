'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi, RouteItem } from '@/lib/api';
import Link from 'next/link';
import { MapPin, Search, ChevronRight, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function RoutesPage() {
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadRoutes = async () => {
      try {
        const data = await fetchApi<RouteItem[]>('/routes');
        setRoutes(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadRoutes();
  }, []);

  const filteredRoutes = routes.filter(
    (r) =>
      r.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.external_route_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.driver_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <Header title="Delivery Routes Intelligence" subtitle="Planned vs Actual Performance & Sequence Tracking" />

      <div className="p-8 space-y-6">
        {/* Search Bar */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              id="input-route-search"
              placeholder="Search route ID, external ref, or driver..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="text-xs text-slate-400 font-mono">
            Showing {filteredRoutes.length} of {routes.length} routes
          </div>
        </div>

        {/* Routes Table */}
        <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-medium">
                <tr>
                  <th className="p-4">Route ID</th>
                  <th className="p-4">Driver & Vehicle</th>
                  <th className="p-4">Stops</th>
                  <th className="p-4">Planned vs Actual (km)</th>
                  <th className="p-4">Planned vs Actual (min)</th>
                  <th className="p-4">Sequence Similarity</th>
                  <th className="p-4">Deviation Status</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredRoutes.map((r) => {
                  const similarity = r.deviation?.sequence_similarity_index || 1.0;
                  const isMaterial = r.deviation?.is_material_deviation || false;
                  return (
                    <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-4 font-mono font-semibold text-indigo-400">
                        {r.id}
                        <span className="block text-[10px] text-slate-500 font-normal">{r.external_route_id}</span>
                      </td>
                      <td className="p-4 text-slate-200">
                        {r.driver_id}
                        <span className="block text-[10px] text-slate-400">{r.vehicle_id}</span>
                      </td>
                      <td className="p-4 text-slate-300 font-medium">{r.total_stops}</td>
                      <td className="p-4 font-mono">
                        <span className="text-slate-300">{r.planned_distance_km}</span>
                        <span className="text-slate-500 mx-1">→</span>
                        <span className={r.actual_distance_km > r.planned_distance_km ? 'text-amber-400 font-semibold' : 'text-slate-300'}>
                          {r.actual_distance_km} km
                        </span>
                      </td>
                      <td className="p-4 font-mono">
                        <span className="text-slate-300">{r.planned_duration_min}</span>
                        <span className="text-slate-500 mx-1">→</span>
                        <span className={r.actual_duration_min > r.planned_duration_min ? 'text-rose-400 font-semibold' : 'text-slate-300'}>
                          {r.actual_duration_min} min
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-full ${similarity < 0.8 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                              style={{ width: `${similarity * 100}%` }}
                            ></div>
                          </div>
                          <span className="font-mono text-[11px] text-slate-300">{(similarity * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className={`px-2.5 py-1 rounded text-[10px] font-bold ${
                          isMaterial
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        }`}>
                          {isMaterial ? 'DEVIATED' : 'ADHERENT'}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <Link
                          href={`/routes/${r.id}`}
                          className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium inline-flex items-center transition-all"
                        >
                          <span>Investigate</span>
                          <ChevronRight className="w-3.5 h-3.5 ml-1" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
