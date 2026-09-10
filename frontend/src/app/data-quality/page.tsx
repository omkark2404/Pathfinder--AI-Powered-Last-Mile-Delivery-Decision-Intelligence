'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi } from '@/lib/api';
import { ShieldCheck, Database, CheckCircle2, AlertTriangle, FileText } from 'lucide-react';

export default function DataQualityPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadReports = async () => {
      try {
        const data = await fetchApi<any[]>('/datasets/quality');
        setReports(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadReports();
  }, []);

  return (
    <div>
      <Header title="Data Quality & Dataset Provenance" subtitle="Ingestion Validation Reports, Null Checks & SHA-256 Hashes" />

      <div className="p-8 space-y-6">
        {reports.length > 0 ? (
          reports.map((rep, idx) => (
            <div key={idx} className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
              <div className="flex justify-between items-start">
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">{rep.dataset_name}</h3>
                    <p className="text-xs text-slate-400 font-mono">Provenance Hash: {rep.provenance_hash}</p>
                  </div>
                </div>

                <span className={`px-3 py-1 rounded text-xs font-bold ${
                  rep.validation_status === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                }`}>
                  STATUS: {rep.validation_status}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs pt-2">
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Total Records</span>
                  <span className="text-slate-200 font-bold">{rep.total_rows}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Routes Analyzed</span>
                  <span className="text-indigo-400 font-bold">{rep.route_count}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Stops Validated</span>
                  <span className="text-indigo-400 font-bold">{rep.stop_count}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <span className="text-slate-500 block">Duplicate Rows</span>
                  <span className="text-emerald-400 font-bold">{rep.duplicate_records}</span>
                </div>
              </div>

              {rep.issues && rep.issues.length > 0 && (
                <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 space-y-1">
                  {rep.issues.map((iss: string, i: number) => (
                    <div key={i} className="flex items-center space-x-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                      <span>{iss}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="glass-panel p-8 rounded-xl border border-slate-800 text-center text-slate-400 text-xs">
            Ingestion Data Quality Reports loaded for Amazon and Mendeley datasets.
          </div>
        )}
      </div>
    </div>
  );
}
