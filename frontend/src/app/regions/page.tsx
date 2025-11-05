'use client'

import React, { useState, useEffect } from 'react'

interface Region {
  region: string
  events: number
  fatalities: number
  risk_score: number
  risk_category: string
  trend: string
}

interface RegionsData {
  regions: Region[]
  total_count: number
  risk_summary: {
    SEVERE: number
    HIGH: number
    MEDIUM: number
    LOW: number
  }
}

const getRiskColor = (category: string): string => {
  switch (category) {
    case 'SEVERE': return 'text-red-500'
    case 'HIGH': return 'text-orange-400'
    case 'MEDIUM': return 'text-yellow-400'
    case 'LOW': return 'text-green-400'
    default: return 'text-slate-400'
  }
}

const getRiskBadgeColor = (category: string): string => {
  switch (category) {
    case 'SEVERE': return 'bg-red-500/20 border-red-500/50'
    case 'HIGH': return 'bg-orange-400/20 border-orange-400/50'
    case 'MEDIUM': return 'bg-yellow-400/20 border-yellow-400/50'
    case 'LOW': return 'bg-green-400/20 border-green-400/50'
    default: return 'bg-slate-400/20 border-slate-400/50'
  }
}

const getTrendIcon = (trend: string): string => {
  switch (trend) {
    case 'increasing': return '↑'
    case 'decreasing': return '↓'
    case 'stable': return '→'
    default: return '→'
  }
}

const getTrendColor = (trend: string): string => {
  switch (trend) {
    case 'increasing': return 'text-red-400'
    case 'decreasing': return 'text-green-400'
    case 'stable': return 'text-slate-400'
    default: return 'text-slate-400'
  }
}

export default function RegionsPage() {
  const [data, setData] = useState<RegionsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>('ALL')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/regions')
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

  // Filter regions
  const filteredRegions = data.regions.filter(region => {
    const matchesSearch = region.region.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterCategory === 'ALL' || region.risk_category === filterCategory
    return matchesSearch && matchesFilter
  })

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
            🗺️ Regions Overview
          </h1>
          <p className="text-slate-400">
            Monitoring {data.total_count} regions across Sudan
          </p>
        </div>

        {/* Risk Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
            <div className="text-red-400 text-sm font-medium mb-1">🔴 SEVERE</div>
            <div className="text-3xl font-bold text-white">{data.risk_summary.SEVERE}</div>
          </div>
          <div className="bg-orange-400/20 border border-orange-400/50 rounded-lg p-4">
            <div className="text-orange-400 text-sm font-medium mb-1">🟠 HIGH</div>
            <div className="text-3xl font-bold text-white">{data.risk_summary.HIGH}</div>
          </div>
          <div className="bg-yellow-400/20 border border-yellow-400/50 rounded-lg p-4">
            <div className="text-yellow-400 text-sm font-medium mb-1">🟡 MEDIUM</div>
            <div className="text-3xl font-bold text-white">{data.risk_summary.MEDIUM}</div>
          </div>
          <div className="bg-green-400/20 border border-green-400/50 rounded-lg p-4">
            <div className="text-green-400 text-sm font-medium mb-1">🟢 LOW</div>
            <div className="text-3xl font-bold text-white">{data.risk_summary.LOW}</div>
          </div>
        </div>

        {/* Search and Filter */}
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
          <div>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-teal-400"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="SEVERE">Severe</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
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
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-teal-400">
                      {region.events.toLocaleString()} events
                    </span>
                    <span className="text-red-400">
                      {region.fatalities.toLocaleString()} deaths
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskBadgeColor(region.risk_category)} ${getRiskColor(region.risk_category)}`}>
                    {region.risk_category} {region.risk_score.toFixed(1)}
                  </div>
                  <div className={`text-sm ${getTrendColor(region.trend)}`}>
                    {getTrendIcon(region.trend)} {region.trend}
                  </div>
                </div>
              </div>
              
              {/* Progress bar for risk score */}
              <div className="relative w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`absolute left-0 top-0 h-full ${
                    region.risk_category === 'SEVERE' ? 'bg-red-500' :
                    region.risk_category === 'HIGH' ? 'bg-orange-400' :
                    region.risk_category === 'MEDIUM' ? 'bg-yellow-400' :
                    'bg-green-400'
                  }`}
                  style={{ width: `${(region.risk_score / 10) * 100}%` }}
                />
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
