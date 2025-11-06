// src/components/analytics/RiskSummaryCards.tsx
import React from 'react';
import type { AnalyticsResponse } from '@/lib/api';

interface RiskSummaryCardsProps {
  analytics: AnalyticsResponse;
}

export default function RiskSummaryCards({ analytics }: RiskSummaryCardsProps) {
  const { summary } = analytics;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Total Regions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Regions</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {summary.total_regions}
            </p>
          </div>
          <div className="text-blue-500">
            <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 20a10 10 0 110-20 10 10 0 010 20zm0-18a8 8 0 100 16 8 8 0 000-16z"/>
            </svg>
          </div>
        </div>
      </div>

      {/* Average Climate Risk */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Avg Climate Risk</p>
            <p className="text-3xl font-bold text-amber-600">
              {summary.avg_climate_risk.toFixed(2)}
            </p>
          </div>
          <div className="text-amber-500">
            <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2a6 6 0 00-6 6c0 4.5 6 10 6 10s6-5.5 6-10a6 6 0 00-6-6z"/>
            </svg>
          </div>
        </div>
      </div>

      {/* ✅ FIXED: Average Conflict Proneness (not avg_conflict_risk) */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Avg Conflict Proneness</p>
            <p className="text-3xl font-bold text-red-600">
              {summary.avg_conflict_proneness.toFixed(2)}
            </p>
          </div>
          <div className="text-red-500">
            <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 2L2 10l8 8 8-8-8-8z"/>
            </svg>
          </div>
        </div>
      </div>

      {/* Total Events */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Events (6mo)</p>
            <p className="text-3xl font-bold text-purple-600">
              {summary.total_events.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {summary.total_fatalities.toLocaleString()} fatalities
            </p>
          </div>
          <div className="text-purple-500">
            <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v12a1 1 0 01-1 1H4a1 1 0 01-1-1V4z"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
