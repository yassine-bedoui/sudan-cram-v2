'use client'

import { getRiskCategory, getIndicatorColor } from '@/lib/bivariate-colors'

interface RegionData {
  name: string
  cp_score: number
  climate_risk: number
  combined_risk: number
  incidents: number
  fatalities?: number
  violence_severity?: number
  spatial_concentration?: number
  temporal_intensity?: number
  actor_diversity?: number
}

interface RegionDetailPanelProps {
  region: RegionData | null
  onClose: () => void
}

export function RegionDetailPanel({ region, onClose }: RegionDetailPanelProps) {
  if (!region) return null

  return (
    <div className="absolute top-4 right-4 w-96 bg-slate-800 rounded-lg border border-slate-700 shadow-2xl z-50 max-h-[90vh] overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-slate-800 p-4 border-b border-slate-700 flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">{region.name}</h2>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Primary Scores */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-900 p-3 rounded-lg">
            <div className="text-xs text-slate-400 mb-1">CP Score</div>
            <div
              className="text-2xl font-bold"
              style={{ color: getIndicatorColor(region.cp_score) }}
            >
              {region.cp_score.toFixed(2)}
            </div>
            <div className="text-xs text-slate-500">{getRiskCategory(region.cp_score)}</div>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg">
            <div className="text-xs text-slate-400 mb-1">Climate</div>
            <div
              className="text-2xl font-bold"
              style={{ color: getIndicatorColor(region.climate_risk) }}
            >
              {region.climate_risk.toFixed(2)}
            </div>
            <div className="text-xs text-slate-500">{getRiskCategory(region.climate_risk)}</div>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg">
            <div className="text-xs text-slate-400 mb-1">Combined</div>
            <div
              className="text-2xl font-bold"
              style={{ color: getIndicatorColor(region.combined_risk) }}
            >
              {region.combined_risk.toFixed(2)}
            </div>
            <div className="text-xs text-slate-500">{getRiskCategory(region.combined_risk)}</div>
          </div>
        </div>

        {/* Conflict Proneness Sub-indicators */}
        <div>
          <h3 className="text-sm font-semibold text-white mb-3">Conflict Proneness Components</h3>
          <div className="space-y-2">
            {region.violence_severity !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300">Violence Severity</span>
                <span className="text-sm font-bold text-red-400">{region.violence_severity.toFixed(2)}</span>
              </div>
            )}
            {region.spatial_concentration !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300">Spatial Concentration</span>
                <span className="text-sm font-bold text-orange-400">{region.spatial_concentration.toFixed(2)}</span>
              </div>
            )}
            {region.temporal_intensity !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300">Temporal Intensity</span>
                <span className="text-sm font-bold text-yellow-400">{region.temporal_intensity.toFixed(2)}</span>
              </div>
            )}
            {region.actor_diversity !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300">Actor Diversity</span>
                <span className="text-sm font-bold text-blue-400">{region.actor_diversity.toFixed(2)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Event Statistics */}
        <div>
          <h3 className="text-sm font-semibold text-white mb-3">Event Statistics</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Total Incidents</span>
              <span className="text-sm font-bold text-teal-400">{region.incidents}</span>
            </div>
            {region.fatalities !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300">Fatalities</span>
                <span className="text-sm font-bold text-red-400">{region.fatalities}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
