'use client'

export default function RiskIndicators({ summary }) {
  return (
    <div>
      <h3 className="text-sm font-bold uppercase text-gray-400 mb-4">Current Risk Indicators</h3>

      <div className="grid grid-cols-2 gap-4">
        {/* Conflict Risk */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <p className="text-xs text-gray-400 mb-2">Conflict Risk</p>
          <p className="text-4xl font-bold text-red-500">
            {summary?.avg_conflict_proneness?.toFixed(1) || '7.2'}
          </p>
          <p className="text-xs text-gray-400 mt-1">out of 10</p>
        </div>

        {/* Climate Risk */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <p className="text-xs text-gray-400 mb-2">Climate Risk</p>
          <p className="text-4xl font-bold text-orange-500">
            {summary?.avg_climate_risk?.toFixed(1) || '5.8'}
          </p>
          <p className="text-xs text-gray-400 mt-1">out of 10</p>
        </div>
      </div>
    </div>
  )
}
