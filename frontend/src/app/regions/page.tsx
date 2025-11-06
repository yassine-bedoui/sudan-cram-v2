'use client'

import React, { useState, useEffect } from 'react'

interface Region {
  region: string
  climate_risk_score: number
  cdi_category: string
  political_risk_score: number
  risk_category: string
  bivariate_category: string
  events_6m?: number  
  fatalities_6m?: number  
  trend: string
}

interface RegionsData {
  regions: Region[]
  total_count: number
  risk_summary: {
    climate: Record<string, number>
    conflict: Record<string, number>
  }
}

const getClimateRiskColor = (category: string): string => {
  switch (category) {
    case 'EXTREME': return 'text-red-500'
    case 'ALERT': return 'text-orange-400'
    case 'WATCH': return 'text-yellow-400'
    case 'NORMAL': return 'text-green-400'
    default: return 'text-slate-400'
  }
}

const getConflictRiskColor = (category: string): string => {
  switch (category) {
    case 'EXTREME': return 'text-red-500'
    case 'VERY HIGH': return 'text-red-400'
    case 'HIGH': return 'text-orange-400'
    case 'MODERATE': return 'text-yellow-400'
    case 'LOW': return 'text-green-400'
    default: return 'text-slate-400'
  }
}

const getRiskBadgeColor = (category: string): string => {
  switch (category) {
    case 'EXTREME': return 'bg-red-500/20 border-red-500/50'
    case 'VERY HIGH': return 'bg-red-400/20 border-red-400/50'
    case 'ALERT': return 'bg-orange-400/20 border-orange-400/50'
    case 'HIGH': return 'bg-orange-400/20 border-orange-400/50'
    case 'WATCH': return 'bg-yellow-400/20 border-yellow-400/50'
    case 'MODERATE': return 'bg-yellow-400/20 border-yellow-400/50'
    case 'NORMAL': return 'bg-green-400/20 border-green-400/50'
    case 'LOW': return 'bg-green-400/20 border-green-400/50'
    default: return 'bg-slate-400/20 border-slate-400/50'
  }
}

const getTrendIcon = (trend: string): string => {
  switch (trend) {
    case 'rising': return '↑'
    case 'falling': return '↓'
    case 'stable': return '→'
    default: return '→'
  }
}

const getTrendColor = (trend: string): string => {
  switch (trend) {
    case 'rising': return 'text-red-400'
    case 'falling': return 'text-green-400'
    case 'stable': return 'text-slate-400'
    default: return 'text-slate-400'
  }
}

export default function RegionsPage() {
  const [data, setData] = useState<RegionsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterDimension, setFilterDimension] = useState<'climate' | 'conflict'>('conflict')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/regions`)
        const result = await response.json()
        setData(result)
      } catch (error) {
        console.error('Error fetching regions:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-white text-xl">Loading regions...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-red-400 text-xl">Failed to load data</div>
      </div>
    )
  }

  // Filter and sort regions
  const filteredRegions = data.regions
    .filter(region => region.region.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      if (filterDimension === 'climate') {
        return (b.climate_risk_score || 0) - (a.climate_risk_score || 0)
      }
      return (b.political_risk_score || 0) - (a.political_risk_score || 0)
    })

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
            🗺️ Bivariate Regions Overview
          </h1>
          <p className="text-slate-400">
            Monitoring {data.total_count} regions with climate + conflict analysis
          </p>
        </div>

        {/* Risk Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Climate Risk Summary */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-amber-400 font-bold mb-3">🌡️ Climate Risk Levels</h3>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(data.risk_summary.climate).map(([level, count]) => (
                <div key={level} className={`${getRiskBadgeColor(level)} rounded-lg p-3`}>
                  <div className={`text-sm font-medium mb-1 ${getClimateRiskColor(level)}`}>{level}</div>
                  <div className="text-2xl font-bold text-white">{count}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Conflict Risk Summary */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-red-400 font-bold mb-3">⚔️ Conflict Risk Levels</h3>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(data.risk_summary.conflict).map(([level, count]) => (
                <div key={level} className={`${getRiskBadgeColor(level)} rounded-lg p-3`}>
                  <div className={`text-sm font-medium mb-1 ${getConflictRiskColor(level)}`}>{level}</div>
                  <div className="text-2xl font-bold text-white">{count}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Search and Sort */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6 flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="🔍 Search regions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-teal-400"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setFilterDimension('climate')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                filterDimension === 'climate'
                  ? 'bg-amber-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              🌡️ Sort by Climate
            </button>
            <button
              onClick={() => setFilterDimension('conflict')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                filterDimension === 'conflict'
                  ? 'bg-red-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              ⚔️ Sort by Conflict
            </button>
          </div>
        </div>

        {/* Results Count */}
        <div className="text-slate-400 mb-4">
          Showing {filteredRegions.length} of {data.total_count} regions
        </div>

        {/* Regions Grid */}
        <div className="grid grid-cols-1 gap-4">
          {filteredRegions.map((region, index) => (
            <div
              key={index}
              className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-teal-400 transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-2">
                    {region.region}
                  </h3>
                  <div className="text-xs text-slate-400 mb-3">
                    {region.bivariate_category?.replace(/_/g, ' ') || 'N/A'}
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-teal-400">
                      {(region.events_6m ?? 0).toLocaleString()} events
                    </span>
                    <span className="text-red-400">
                      {(region.fatalities_6m ?? 0).toLocaleString()} fatalities
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <div className={`text-sm ${getTrendColor(region.trend)}`}>
                    {getTrendIcon(region.trend)} {region.trend}
                  </div>
                </div>
              </div>

              {/* Bivariate Risk Display */}
              <div className="grid grid-cols-2 gap-4 mb-3">
                {/* Climate Risk */}
                <div className={`p-3 rounded-lg border ${getRiskBadgeColor(region.cdi_category)}`}>
                  <div className="text-xs text-slate-400 mb-1">Climate Risk</div>
                  <div className={`text-lg font-bold ${getClimateRiskColor(region.cdi_category)}`}>
                    {(region.climate_risk_score || 0).toFixed(1)}
                  </div>
                  <div className="text-xs font-medium text-white mt-1">
                    {region.cdi_category || 'N/A'}
                  </div>
                </div>

                {/* Conflict Risk */}
                <div className={`p-3 rounded-lg border ${getRiskBadgeColor(region.risk_category)}`}>
                  <div className="text-xs text-slate-400 mb-1">Conflict Risk</div>
                  <div className={`text-lg font-bold ${getConflictRiskColor(region.risk_category)}`}>
                    {(region.political_risk_score || 0).toFixed(1)}
                  </div>
                  <div className="text-xs font-medium text-white mt-1">
                    {region.risk_category || 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* No Results */}
        {filteredRegions.length === 0 && (
          <div className="text-center py-12">
            <div className="text-slate-400 text-lg">No regions found matching your criteria</div>
          </div>
        )}
      </div>
    </div>
  )
}
