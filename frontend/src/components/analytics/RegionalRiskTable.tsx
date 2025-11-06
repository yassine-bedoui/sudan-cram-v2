// src/components/analytics/RegionalRiskTable.tsx
'use client';

import React, { useState } from 'react';
import type { Region } from '@/lib/api';

interface RegionalRiskTableProps {
  regions: Region[];
}

export default function RegionalRiskTable({ regions }: RegionalRiskTableProps) {
  const [sortBy, setSortBy] = useState<'climate' | 'conflict' | 'conflict-risk'>('conflict');

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
      'NORMAL': 'bg-gray-400'
    };
    return colors[level] || 'bg-gray-400';
  };

  // ✅ FIXED: Added conflict-risk sorting option
  const sortedRegions = [...regions].sort((a, b) => {
    if (sortBy === 'climate') {
      return b.climate_risk_score - a.climate_risk_score;
    }
    if (sortBy === 'conflict-risk') {
      return b.conflict_risk_score - a.conflict_risk_score;
    }
    // Default: CP (conflict proneness / political_risk_score)
    return b.political_risk_score - a.political_risk_score;
  });

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
          Regional Risk Assessment
        </h2>
        {/* ✅ FIXED: Added Conflict Risk button */}
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setSortBy('conflict')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              sortBy === 'conflict'
                ? 'bg-red-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            Sort by Proneness
          </button>
          <button
            onClick={() => setSortBy('conflict-risk')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              sortBy === 'conflict-risk'
                ? 'bg-orange-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            Sort by Conflict Risk
          </button>
          <button
            onClick={() => setSortBy('climate')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              sortBy === 'climate'
                ? 'bg-amber-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            Sort by Climate
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Region
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Climate Risk
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Conflict Risk
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Proneness
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Events (6mo)
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Fatalities
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {sortedRegions.map((region) => (
              <tr key={region.region} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="font-medium text-gray-900 dark:text-white">
                    {region.region}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {region.bivariate_category.replace(/_/g, ' ')}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-amber-600">
                      {region.climate_risk_score.toFixed(2)}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full text-white ${getBadgeColor(region.cdi_category)}`}>
                      {region.cdi_category}
                    </span>
                  </div>
                </td>
                {/* ✅ NEW: Conflict Risk column */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-orange-600">
                      {region.conflict_risk_score.toFixed(2)}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full text-white ${getBadgeColor(region.conflict_risk_level)}`}>
                      {region.conflict_risk_level}
                    </span>
                  </div>
                </td>
                {/* ✅ RENAMED: Conflict Proneness column */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-red-600">
                      {region.political_risk_score.toFixed(2)}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded-full text-white ${getBadgeColor(region.risk_category)}`}>
                      {region.risk_category}
                    </span>
                  </div>
                </td>
                {/* ✅ FIXED: Remove fallback to .events (doesn't exist) */}
                <td className="px-6 py-4 whitespace-nowrap text-gray-900 dark:text-white">
                  {region.events_6m || 0}
                </td>
                {/* ✅ FIXED: Remove fallback to .fatalities (doesn't exist) */}
                <td className="px-6 py-4 whitespace-nowrap text-gray-900 dark:text-white">
                  {region.fatalities_6m || 0}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
