'use client'

import React, { useEffect, useState } from 'react'
import { getIndicatorColor, getRiskCategory } from '@/lib/bivariate-colors'

interface ComparisonData {
  ADM1_NAME: string
  cp_score: number
  climate_risk: number
  combined_risk: number
  incidents: number
}

export default function ComparisonPage() {
  const [data, setData] = useState<ComparisonData[]>([])
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState<'cp_score' | 'climate_risk' | 'combined_risk'>('combined_risk')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/indicators/comparison')
        const result = await response.json()
        setData(result.data || [])
      } catch (error) {
        console.error('Failed to fetch comparison data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const sortedData = [...data].sort((a, b) => b[sortBy] - a[sortBy])

  const summary = {
    avgCP: (data.reduce((sum, d) => sum + d.cp_score, 0) / data.length).toFixed(2),
    avgClimate: (data.reduce((sum, d) => sum + d.climate_risk, 0) / data.length).toFixed(2),
    avgCombined: (data.reduce((sum, d) => sum + d.combined_risk, 0) / data.length).toFixed(2),
    totalIncidents: data.reduce((sum, d) => sum + d.incidents, 0),
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
        Loading comparison data...
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">📊 Indicator Comparison Dashboard</h1>
          <p className="text-lg text-slate-400">Side-by-side comparison of all risk metrics</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="text-sm text-slate-400 mb-2">Avg Conflict Proneness</div>
            <div className="text-3xl font-bold text-red-400">{summary.avgCP}</div>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="text-sm text-slate-400 mb-2">Avg Climate Risk</div>
            <div className="text-3xl font-bold text-orange-400">{summary.avgClimate}</div>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="text-sm text-slate-400 mb-2">Avg Combined Risk</div>
            <div className="text-3xl font-bold text-yellow-400">{summary.avgCombined}</div>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="text-sm text-slate-400 mb-2">Total Incidents</div>
            <div className="text-3xl font-bold text-teal-400">{summary.totalIncidents}</div>
          </div>
        </div>

        {/* Sort Controls */}
        <div className="mb-4 flex items-center gap-4">
          <span className="text-white font-medium">Sort by:</span>
          <button
            onClick={() => setSortBy('combined_risk')}
            className={`px-4 py-2 rounded-lg ${
              sortBy === 'combined_risk' ? 'bg-teal-500 text-white' : 'bg-slate-700 text-slate-300'
            }`}
          >
            Combined Risk
          </button>
          <button
            onClick={() => setSortBy('cp_score')}
            className={`px-4 py-2 rounded-lg ${
              sortBy === 'cp_score' ? 'bg-teal-500 text-white' : 'bg-slate-700 text-slate-300'
            }`}
          >
            Conflict Proneness
          </button>
          <button
            onClick={() => setSortBy('climate_risk')}
            className={`px-4 py-2 rounded-lg ${
              sortBy === 'climate_risk' ? 'bg-teal-500 text-white' : 'bg-slate-700 text-slate-300'
            }`}
          >
            Climate Risk
          </button>
        </div>

        {/* Comparison Table */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-900">
              <tr>
                <th className="text-left p-4 text-slate-300 font-semibold">#</th>
                <th className="text-left p-4 text-slate-300 font-semibold">Region</th>
                <th className="text-center p-4 text-slate-300 font-semibold">CP Score</th>
                <th className="text-center p-4 text-slate-300 font-semibold">Climate Risk</th>
                <th className="text-center p-4 text-slate-300 font-semibold">Combined Risk</th>
                <th className="text-center p-4 text-slate-300 font-semibold">Incidents</th>
              </tr>
            </thead>
            <tbody>
              {sortedData.map((region, index) => (
                <tr key={region.ADM1_NAME} className="border-t border-slate-700 hover:bg-slate-750">
                  <td className="p-4 text-slate-400">{index + 1}</td>
                  <td className="p-4 text-white font-medium">{region.ADM1_NAME}</td>
                  <td className="p-4 text-center">
                    <div className="inline-flex flex-col items-center">
                      <span className="font-bold text-lg" style={{ color: getIndicatorColor(region.cp_score) }}>
                        {region.cp_score.toFixed(2)}
                      </span>
                      <span className="text-xs text-slate-500">{getRiskCategory(region.cp_score)}</span>
                    </div>
                  </td>
                  <td className="p-4 text-center">
                    <div className="inline-flex flex-col items-center">
                      <span className="font-bold text-lg" style={{ color: getIndicatorColor(region.climate_risk) }}>
                        {region.climate_risk.toFixed(2)}
                      </span>
                      <span className="text-xs text-slate-500">{getRiskCategory(region.climate_risk)}</span>
                    </div>
                  </td>
                  <td className="p-4 text-center">
                    <div className="inline-flex flex-col items-center">
                      <span className="font-bold text-lg" style={{ color: getIndicatorColor(region.combined_risk) }}>
                        {region.combined_risk.toFixed(2)}
                      </span>
                      <span className="text-xs text-slate-500">{getRiskCategory(region.combined_risk)}</span>
                    </div>
                  </td>
                  <td className="p-4 text-center text-teal-400 font-bold">{region.incidents}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
