'use client';

import React from 'react';
import { RefreshCw, Database } from 'lucide-react';
import { DATA_MODE_LABELS } from '@/lib/api';
import { useHealth } from '@/lib/useHealth';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
}

export default function Header({ title, subtitle, onRefresh }: HeaderProps) {
  const { health, error } = useHealth();
  const isRealData = health?.data_mode === 'public_datasets';
  const badgeText = health ? DATA_MODE_LABELS[health.data_mode] : error ? 'API unreachable' : 'Checking data…';

  return (
    <header className="h-16 glass-panel border-b border-slate-800 flex items-center justify-between px-8 sticky top-0 z-20">
      <div>
        <h1 className="text-lg font-bold text-slate-100">{title}</h1>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-4">
        {onRefresh && (
          <button
            onClick={onRefresh}
            id="btn-header-refresh"
            className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 transition-colors border border-slate-700/50 flex items-center space-x-1.5 text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
            <span>Refresh</span>
          </button>
        )}

        <div
          title={health?.data_mode_note}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs border ${
            isRealData
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
              : 'bg-amber-500/10 border-amber-500/20 text-amber-300'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span className="font-medium">{badgeText}</span>
        </div>
      </div>
    </header>
  );
}
