// src/components/analytics/BivariateCards.tsx
'use client';

import React from 'react';
import type { AnalyticsResponse } from '@/lib/api';

interface BivariateCardsProps {
  analytics: AnalyticsResponse;
}

export default function BivariateCards({ analytics }: BivariateCardsProps) {
  const { summary } = analytics;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {/* Total Regions */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
        <div className="flex items-center justify-between mb-4">
          <span className="text-slate-400 text-sm font-medium">Total Regions</span>
          <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
            <span className="text-2xl">🗺️</span>
          </div>
        </div>
        <div className="text-4xl font-bold text-blue-400 mb-2">
          {summary.total_regions ?? 0}
        </div>
        <div className="text-xs text-slate-500">States monitored</div>
      </div>

      {/* Average Climate Risk */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
        <div className="flex items-center justify-between mb-4">
          <span className="text-slate-400 text-sm font-medium">Avg Climate Risk</span>
          <div className="w-12 h-12 rounded-lg bg-amber-500/20 flex items-center justify-center">
            <span className="text-2xl">🌡️</span>
          </div>
        </div>
        <div className="text-4xl font-bold text-amber-400 mb-2">
          {(summary.avg_climate_risk ?? 0).toFixed(1)}
        </div>
        <div className="text-xs text-slate-500">Climate vulnerability</div>
      </div>

      {/* Average Conflict Risk */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
        <div className="flex items-center justify-between mb-4">
          <span className="text-slate-400 text-sm font-medium">Avg Conflict Risk</span>
          <div className="w-12 h-12 rounded-lg bg-red-500/20 flex items-center justify-center">
            <span className="text-2xl">⚔️</span>
          </div>
        </div>
        <div className="text-4xl font-bold text-red-400 mb-2">
          {(summary.avg_conflict_proneness ?? 0).toFixed(1)}
        </div>
        <div className="text-xs text-slate-500">Political violence index</div>
      </div>

      {/* Total Fatalities */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
        <div className="flex items-center justify-between mb-4">
          <span className="text-slate-400 text-sm font-medium">Total Fatalities</span>
          <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
            <span className="text-2xl">📊</span>
          </div>
        </div>
        <div className="text-4xl font-bold text-purple-400 mb-2">
          {(summary.total_fatalities ?? 0).toLocaleString()}
        </div>
        <div className="text-xs text-slate-500">Conflict impact</div>
      </div>
    </div>
  );
}
