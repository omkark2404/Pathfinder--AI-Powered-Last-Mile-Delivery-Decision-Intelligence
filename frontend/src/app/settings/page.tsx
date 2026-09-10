'use client';

import React from 'react';
import Header from '@/components/Header';
import { Settings, Download, ExternalLink, ShieldCheck, Database, Info } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div>
      <Header title="System Configuration & Real Datasets Setup" subtitle="Dataset Placement Instructions & System Environment Settings" />

      <div className="p-8 space-y-8">
        {/* Real Public Dataset Policy Info Box */}
        <div className="glass-panel p-6 rounded-xl border border-indigo-500/30 bg-indigo-950/20 space-y-4">
          <div className="flex items-center space-x-3">
            <Info className="w-5 h-5 text-indigo-400" />
            <h2 className="text-sm font-bold text-slate-100">Real Public Data Policy</h2>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Per project specification, primary operational workflows run on real public delivery/logistics datasets.
            Synthetic data is strictly prohibited for model evaluation, ETA accuracy reports, or optimization claims.
          </p>
        </div>

        {/* Dataset Placement Guide */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Dataset A */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Primary Dataset A</span>
                <h3 className="text-sm font-bold text-slate-100 mt-0.5">Amazon Last Mile Routing Research Challenge</h3>
              </div>
              <Download className="w-4 h-4 text-indigo-400" />
            </div>

            <p className="text-xs text-slate-400">
              Contains route-, stop-, and package-level features from 9,184 historical Amazon driver routes performed in 2018 across five U.S. metropolitan areas.
            </p>

            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono space-y-1">
              <div className="text-slate-400">Source: <a href="https://registry.opendata.aws/amazon-last-mile-challenges/" target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">AWS Registry</a></div>
              <div className="text-slate-400">Target File Path: <span className="text-amber-300">./data/amazon_last_mile.json</span></div>
            </div>

            <a
              href="https://registry.opendata.aws/amazon-last-mile-challenges/"
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium inline-flex items-center space-x-1.5 transition-all border border-slate-700"
            >
              <span>AWS Open Data Registry</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Dataset B */}
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Primary Dataset B</span>
                <h3 className="text-sm font-bold text-slate-100 mt-0.5">Planned vs Actual Last-Mile Routes</h3>
              </div>
              <Download className="w-4 h-4 text-indigo-400" />
            </div>

            <p className="text-xs text-slate-400">
              Contains planned routes and actual driven routes by delivery drivers, stop sequence changes, time windows, and exact timing.
            </p>

            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs font-mono space-y-1">
              <div className="text-slate-400">Source: <a href="https://data.mendeley.com/datasets/kkwgfvmtxn" target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">Mendeley Data (CC BY 4.0)</a></div>
              <div className="text-slate-400">Target File Path: <span className="text-amber-300">./data/mendeley_planned_vs_actual.csv</span></div>
            </div>

            <a
              href="https://data.mendeley.com/datasets/kkwgfvmtxn"
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium inline-flex items-center space-x-1.5 transition-all border border-slate-700"
            >
              <span>Mendeley Data Record (DOI)</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
