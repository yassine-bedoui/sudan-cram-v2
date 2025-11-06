export default function RiskIndicators({ summary }) {
  return (
    <div className="border border-gray-300 p-4 bg-white">
      <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-4 flex justify-between items-center font-bold">
        Current Risk Indicators
        <button className="text-orange-600"><i>−</i></button>
      </h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="border-l-4 border-orange-600 pl-3">
          <p className="text-2xl font-mono font-bold text-orange-600">
            {summary?.avg_conflict_proneness?.toFixed(1) || '7.2'}
          </p>
          <p className="text-xs text-gray-600 mt-1">Conflict Risk</p>
          <p className="text-xs text-gray-500">out of 10</p>
        </div>

        <div className="border-l-4 border-orange-500 pl-3">
          <p className="text-2xl font-mono font-bold text-orange-500">
            {summary?.avg_climate_risk?.toFixed(1) || '5.8'}
          </p>
          <p className="text-xs text-gray-600 mt-1">Climate Risk</p>
          <p className="text-xs text-gray-500">out of 10</p>
        </div>
      </div>
    </div>
  )
}
