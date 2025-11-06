// src/components/analytics/BivariateTable.tsx
'use client';

import React, { useState } from 'react';
import type { AnalyticsResponse } from '@/lib/api';

interface BivariateTableProps {
  regions: AnalyticsResponse['regional_data'];
}

export default function BivariateTable({ regions }: BivariateTableProps) {
  const [sortBy, setSortBy] = useState<'climate' | 'conflict'>('conflict');

  // Sort regions based on selected metric
  const sortedRegions = [...(regions || [])].sort((a, b) => {
    if (sortBy === 'climate') {
      return (b.climate_risk_score ?? 0) - (a.climate_risk_score ?? 0);
    }
    return (b.political_risk_score ?? 0) - (a.political_risk_score ?? 0);
  });

  const getClimateColor = (score: number | undefined): string => {
    if (!score) return 'text-slate-400';
    if (score >= 8) return 'text-red-500';
    if (score >= 6) return 'text-orange-400';
    if (score >= 4) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getConflictColor = (score: number | undefined): string => {
    if (!score) return 'text-slate-400';
    if (score >= 8) return 'text-red-500';
    if (score >= 6) return 'text-orange-400';
    if (score >= 4) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
      <div className="flex items-center justify-between p-6 bg-slate-900">
        <h2 className="text-2xl font-bold text-white">Regional Risk Comparison</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setSortBy('climate')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              sortBy === 'climate'
                ? 'bg-amber-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            🌡️ Sort by Climate
          </button>
          <button
            onClick={() => setSortBy('conflict')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              sortBy === 'conflict'
                ? 'bg-red-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            ⚔️ Sort by Conflict
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 border-t border-slate-700">
            <tr>
              <th className="px-6 py-4 text-left text-slate-300 font-semibold">Region</th>
              <th className="px-6 py-4 text-center text-slate-300 font-semibold">🌡️ Climate Risk</th>
              <th className="px-6 py-4 text-center text-slate-300 font-semibold">⚔️ Conflict Risk</th>
              <th className="px-6 py-4 text-center text-slate-300 font-semibold">Events (6mo)</th>
              <th className="px-6 py-4 text-center text-slate-300 font-semibold">Fatalities</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {sortedRegions.map((region, idx) => (
              <tr
                key={`${region.region}-${idx}`}
                className="hover:bg-slate-700/30 transition-colors"
              >
                {/* Region Name */}
                <td className="px-6 py-4 font-medium text-white">
                  {region.region || 'N/A'}
                </td>

                {/* Climate Risk Score */}
                <td className="px-6 py-4">
                  <div className="flex justify-center">
                    <span className={`font-semibold ${getClimateColor(region.climate_risk_score)}`}>
                      {(region.climate_risk_score ?? 0).toFixed(2)}
                    </span>
                  </div>
                </td>

                {/* Conflict Risk Score */}
                <td className="px-6 py-4">
                  <div className="flex justify-center">
                    <span className={`font-semibold ${getConflictColor(region.political_risk_score)}`}>
                      {(region.political_risk_score ?? 0).toFixed(2)}
                    </span>
                  </div>
                </td>

                {/* Events (6 months) */}
                <td className="px-6 py-4 text-center text-teal-400 font-medium">
                  {(region.events_6m ?? 0).toLocaleString()}
                </td>

                {/* Fatalities */}
                <td className="px-6 py-4 text-center text-red-400 font-medium">
                  {(region.fatalities_6m ?? 0).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sortedRegions.length === 0 && (
        <div className="text-center py-8 text-slate-400">
          No region data available
        </div>
      )}
    </div>
  );
}
