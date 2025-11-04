import { StateRiskData } from '../hooks/useMapData'

interface StateStatsProps {
  states: StateRiskData[]
}

export function StateStats({ states }: StateStatsProps) {
  const highRiskStates = states.filter(s => s.cp_score >= 7).length
  const totalIncidents = states.reduce((sum, s) => sum + s.incidents, 0)
  const avgRisk = (states.reduce((sum, s) => sum + s.cp_score, 0) / states.length).toFixed(1)

  const topRiskStates = [...states]
    .sort((a, b) => b.cp_score - a.cp_score)
    .slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-slate-400 text-sm mb-1">High Risk States</p>
          <p className="text-3xl font-bold text-red-400">{highRiskStates}</p>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-slate-400 text-sm mb-1">Total Incidents</p>
          <p className="text-3xl font-bold text-orange-400">{totalIncidents}</p>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-slate-400 text-sm mb-1">Avg Risk Score</p>
          <p className="text-3xl font-bold text-yellow-400">{avgRisk}</p>
        </div>
      </div>

      {/* Top Risk States */}
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <h3 className="text-white font-semibold mb-3">Highest Risk States</h3>
        <div className="space-y-2">
          {topRiskStates.map((state, idx) => (
            <div key={state.name} className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white text-sm font-bold">
                {idx + 1}
              </div>
              <div className="flex-1">
                <p className="text-white font-medium">{state.name}</p>
                <p className="text-slate-400 text-xs">{state.incidents} incidents</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-red-400">{state.cp_score}</p>
                <p className="text-xs text-slate-400">{state.cp_category}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
