'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { fetchApi } from '@/lib/api';
import { FileText, CheckCircle2, XCircle } from 'lucide-react';

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAudit = async () => {
      try {
        const data = await fetchApi<any[]>('/audit');
        setLogs(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadAudit();
  }, []);

  return (
    <div>
      <Header title="Dispatcher Decision Audit Log" subtitle="Human-In-The-Loop Traceability, Evidence Log & Action History" />

      <div className="p-8 space-y-6">
        <div className="glass-panel rounded-xl border border-slate-800 p-6">
          <h2 className="text-sm font-bold text-slate-200 mb-4 flex items-center">
            <FileText className="w-4 h-4 text-indigo-400 mr-2" />
            <span>Audit Trail Records</span>
          </h2>

          <div className="space-y-3">
            {logs.length > 0 ? (
              logs.map((log) => (
                <div key={log.id} className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 text-xs font-mono flex items-center justify-between">
                  <div>
                    <span className="text-indigo-400 font-bold">{log.action}</span>
                    <span className="text-slate-400 ml-2">User: {log.user_id}</span>
                    <p className="text-slate-300 mt-1">{log.details?.recommendation_title || log.details?.reason || 'Decision recorded.'}</p>
                  </div>
                  <span className="text-slate-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs">
                Audit logs are recorded whenever a dispatcher accepts, rejects, or executes operational route recommendations.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
