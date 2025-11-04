'use client'

import React, { useState, useEffect } from 'react'
import { TrendChart } from '@/components/analytics/TrendChart'
import { RegionalChart } from '@/components/analytics/RegionalChart'
import { RiskDistributionChart } from '@/components/analytics/RiskDistributionChart'

interface AnalyticsData {
  summary: {
    total_events: number
    total_fatalities: number
    avg_risk_score: number
    highest_risk_region: string
    regions_monitored: number
  }
  monthly_trend: Array<{
    month: string
    events: number
    fatalities: number
    avg_risk: number
  }>
  regional_data: Array<{
    region: string
    events: number
    fatalities: number
    risk_score: number
  }>
  risk_distribution: Record<string, number>
  top_regions: Array<{
    region: string
    risk_score: number
    events: number
    fatalities: number
  }>
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/analytics')
        if (!response.ok) throw new Error('Failed to fetch analytics')
        const result = await response.json()
        setData(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-white text-xl">Loading analytics...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-red-500 text-xl">Error: {error || 'No data available'}</div>
      </div>
    )
  }

  // Transform risk_distribution for pie chart
  const riskChartData = Object.entries(data.risk_distribution).map(([name, value]) => ({
    name,
    value
  }))

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">📊 Analytics Dashboard</h1>
        <p className="text-slate-400">Comprehensive conflict data analysis and trends</p>
      </div>

      {/* Summary Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Total Events</div>
          <div className="text-3xl font-bold text-teal-400">{data.summary.total_events.toLocaleString()}</div>
        </div>
        
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Total Fatalities</div>
          <div className="text-3xl font-bold text-red-400">{data.summary.total_fatalities.toLocaleString()}</div>
        </div>
        
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Avg Risk Score</div>
          <div className="text-3xl font-bold text-yellow-400">{data.summary.avg_risk_score}</div>
        </div>
        
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Highest Risk</div>
          <div className="text-xl font-bold text-orange-400">{data.summary.highest_risk_region}</div>
        </div>
        
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-slate-400 text-sm mb-2">Regions Monitored</div>
          <div className="text-3xl font-bold text-blue-400">{data.summary.regions_monitored}</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Monthly Trend */}
        <TrendChart data={data.monthly_trend} />

        {/* Regional Comparison and Risk Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RiskDistributionChart data={riskChartData} />
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">🎯 Top 10 High-Risk Regions</h2>
            <div className="space-y-3">
              {data.top_regions.map((region, index) => (
                <div key={index} className="flex items-center justify-between bg-slate-900 p-3 rounded">
                  <div className="flex items-center gap-3">
                    <span className="text-slate-400 font-mono text-sm w-6">{index + 1}.</span>
                    <span className="text-white font-medium">{region.region}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-teal-400 text-sm">{region.events} events</span>
                    <span className="text-red-400 text-sm">{region.fatalities} deaths</span>
                    <span 
                      className={`px-3 py-1 rounded text-sm font-bold ${
                        region.risk_score >= 7.5 ? 'bg-red-500/20 text-red-400' :
                        region.risk_score >= 5.0 ? 'bg-orange-500/20 text-orange-400' :
                        region.risk_score >= 2.5 ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}
                    >
                      {region.risk_score}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Regional Comparison Bar Chart */}
        <RegionalChart data={data.regional_data} />
      </div>
    </div>
  )
}
