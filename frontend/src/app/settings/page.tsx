'use client';

import React from 'react';
import Header from '@/components/Header';
import { Settings, Download, ExternalLink, ShieldCheck, Database, Info } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div>
      <Header title="System Configuration & Dataset Setup" subtitle="What ships with the repo, and where to place the full public datasets" />

      <div className="p-8 space-y-8">
        <div className="glass-panel p-6 rounded-xl border border-indigo-500/30 bg-indigo-950/20 space-y-4">
          <div className="flex items-center space-x-3">
            <Info className="w-5 h-5 text-indigo-400" />
            <h2 className="text-sm font-bold text-slate-100">Data Provenance</h2>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The repository bundles a 13-route real subset of the Amazon Last Mile dataset (stop locations, packages, service
            times; no actual visit order or distances) and a <span className="text-amber-300 font-semibold">synthetic</span> 30-route
            fixture in the Mendeley planned-vs-actual schema (<span className="font-mono">data/mendeley_synthetic_fixture.csv</span>).
            Anything computed from the fixture is a demonstration, not a real-world result. The header badge shows which data is loaded.
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
              <div className="text-slate-400">Source: <a href="https://registry.opendata.aws/amazon-last-mile-challenges/" target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">AWS Registry (CC BY-NC 4.0)</a></div>
              <div className="text-slate-400">Target File Path: <span className="text-amber-300">./data/amazon_last_mile.json</span></div>
            </div>

            <a
              href="https://registry.opendata.aws/amazon-last-mile-challenges/"
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium inline-flex items-center space-x-1.5 transition-all border border-slate-700"
            >
              <span>Registry of Open Data on AWS</span>
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
              Real dataset: planned vs actual stop sequences, time windows and arrival timing from a logistics company. Not bundled; the repo ships a synthetic fixture in its place.
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
