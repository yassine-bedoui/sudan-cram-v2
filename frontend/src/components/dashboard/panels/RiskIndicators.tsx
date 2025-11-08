'use client'

import { useState } from 'react'

export default function RiskIndicators({ summary }: { summary: any }) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <div className="border border-gray-300 p-4 bg-white rounded">
      <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-4 flex justify-between items-center font-bold">
        Current Risk Indicators
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-orange-600 hover:text-orange-700 transition text-lg font-bold"
          aria-label={isCollapsed ? "Expand" : "Collapse"}
        >
          {isCollapsed ? '+' : '−'}
        </button>
      </h3>

      {!isCollapsed && (
        <div className="grid grid-cols-2 gap-4">
          <div className="border-l-4 border-orange-600 pl-3 bg-gray-50 p-2 rounded">
            <p className="text-2xl font-mono font-bold text-orange-600">
              {summary?.avg_conflict_proneness?.toFixed(1) || '7.2'}
            </p>
            <p className="text-xs text-gray-600 mt-1">Conflict Risk</p>
            <p className="text-xs text-gray-500">out of 10</p>
          </div>

          <div className="border-l-4 border-orange-500 pl-3 bg-gray-50 p-2 rounded">
            <p className="text-2xl font-mono font-bold text-orange-500">
              {summary?.avg_climate_risk?.toFixed(1) || '5.8'}
            </p>
            <p className="text-xs text-gray-600 mt-1">Climate Risk</p>
            <p className="text-xs text-gray-500">out of 10</p>
          </div>
        </div>
      )}
    </div>
  )
}
