'use client';

import React from 'react';
import { Bell, RefreshCw, Database } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
}

export default function Header({ title, subtitle, onRefresh }: HeaderProps) {
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

        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
          <Database className="w-3.5 h-3.5" />
          <span className="font-medium">Amazon & Mendeley Datasets</span>
        </div>
      </div>
    </header>
  );
}
