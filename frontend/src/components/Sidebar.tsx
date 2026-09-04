'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  MapPin,
  AlertTriangle,
  GitFork,
  Cpu,
  Sliders,
  Users,
  BrainCircuit,
  ShieldCheck,
  FileText,
  Settings,
  Truck
} from 'lucide-react';

const navItems = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Routes', href: '/routes', icon: MapPin },
  { name: 'Delivery Risk', href: '/risk', icon: AlertTriangle },
  { name: 'Route Deviations', href: '/deviations', icon: GitFork },
  { name: 'Optimization', href: '/optimization', icon: Cpu },
  { name: 'Scenarios', href: '/scenarios', icon: Sliders },
  { name: 'Drivers', href: '/drivers', icon: Users },
  { name: 'Models', href: '/models', icon: BrainCircuit },
  { name: 'Data Quality', href: '/data-quality', icon: ShieldCheck },
  { name: 'Audit', href: '/audit', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 glass-panel border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-30">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <Truck className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-slate-100 text-sm tracking-wide leading-tight">LastMile</h1>
          <p className="text-xs text-indigo-400 font-medium">Delivery Intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              id={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
              className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-inner'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-[11px] text-slate-400 font-mono">Engine: Operational</span>
        </div>
        <div className="text-[10px] text-slate-500 mt-1 font-mono">Public Real-World Data Mode</div>
      </div>
    </aside>
  );
}
