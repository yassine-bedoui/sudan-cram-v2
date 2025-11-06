// src/components/analytics/BivariateTable.tsx
'use client';

import React, { useState } from 'react';
import type { Region } from '@/lib/api';

interface BivariateTableProps {
  regions: Region[];
}

export default function BivariateTable({ regions }: BivariateTableProps) {
  const [sortBy, setSortBy] = useState<'climate' | 'conflict'>('conflict');

  const getBadgeColor = (level: string): string => {
    const colors: Record<string, string> = {
      'EXTREME': 'bg-red-600',
      'VERY HIGH': 'bg-red-500',
      'HIGH': 'bg-orange-500',
      'MODERATE': 'bg-yellow-500',
      'LOW': 'bg-green-500',
      'ALERT': 'bg-red-600',
      'WARNING': 'bg-orange-500',
      'WATCH': 'bg-yellow-500',
      'NORMAL': 'bg-gray-500'
    };
    return colors[level] || 'bg-gray-500';
  };

  const sortedRegions = [...regions].sort((a, b) => {
    if (sortBy === 'climate') {
      return b.climate_risk_score - a.climate_risk_score;
    }
    return b.conflict_risk_score - a.conflict_risk_score;
  });

  return (
    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl border border-slate-700 shadow-xl overflow-hidden">
      <div className="px-8 py-6 border-b border-slate-700">
        <h2 className="text-2xl font-bold text-white mb-4">Bivariate Risk Assessment</h2>
        <p className="text-slate-400 text-sm mb-4">
          Climate drought risk (CDI) × Conflict intensity (ACLED) analysis
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => setSortBy('conflict')}
            className={`px-4 py-2 rounded-lg transition-all font-medium ${
              sortBy === 'conflict'
                ? 'bg-red-600 text-white shadow-lg'
                : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
            }`}
          >
            ⚔️ Sort by Conflict
          </button>
          <button
            onClick={() => setSortBy('climate')}
            className={`px-4 py-2 rounded-lg transition-all font-medium ${
              sortBy === 'climate'
                ? 'bg-amber-600 text-white shadow-lg'
                : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
            }`}
          >
            🌡️ Sort by Climate
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-700">
          <thead className="bg-slate-900/50">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Region
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Climate Risk
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Conflict Risk
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Events (6mo)
              </th>
              <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Fatalities
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {sortedRegions.map((region, idx) => (
              <tr key={region.region} className="hover:bg-slate-800/50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="font-medium text-white">{region.region}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    {region.bivariate_category.replace(/_/g, ' ')}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-amber-400">
                      {region.climate_risk_score.toFixed(2)}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full text-white ${getBadgeColor(region.climate_risk_level)}`}>
                      {region.climate_risk_level}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-red-400">
                      {region.conflict_risk_score.toFixed(2)}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full text-white ${getBadgeColor(region.conflict_risk_level)}`}>
                      {region.conflict_risk_level}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-white font-medium">{region.events}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-white font-medium">{region.fatalities}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
