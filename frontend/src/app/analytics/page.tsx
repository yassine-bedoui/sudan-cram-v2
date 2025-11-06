// src/app/analytics/page.tsx
'use client'

import React, { useState, useEffect } from 'react'
import { Layout } from '@/components/layout/Layout'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface AnalyticsData {
  summary: {
    total_events: number
    total_fatalities: number
    avg_climate_risk: number
    avg_conflict_proneness: number  // ✅ FIXED: Changed from avg_conflict_risk
    highest_risk_region: string
    total_regions: number
  }
  regional_data: Array<{
    region: string
    climate_risk_score: number
    political_risk_score: number
    events_6m: number
    fatalities_6m: number
  }>
  risk_distribution: {
    climate: Record<string, number>
    conflict: Record<string, number>
  }
  top_regions: Array<{
    region: string
    climate_risk_score: number
    political_risk_score: number
    cdi_category: string
    risk_category: string
    events_6m: number
    fatalities_6m: number
  }>
}

interface MonthlyTrendData {
  month: string
  events: number
  fatalities: number
}

const CLIMATE_COLORS = {
  NORMAL: '#91cf60',
  WATCH: '#fee08b',
  ALERT: '#fc8d59',
  EXTREME: '#d73027',
}

const CONFLICT_COLORS = {
  LOW: '#91cf60',
  MODERATE: '#fee08b',
  HIGH: '#fc8d59',
  'VERY HIGH': '#fc8d59',
  EXTREME: '#d73027',
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [monthlyTrend, setMonthlyTrend] = useState<MonthlyTrendData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAllData = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

        // ✅ Fetch analytics data
        const analyticsResponse = await fetch(`${backendUrl}/api/analytics`)
        if (!analyticsResponse.ok) throw new Error('Failed to fetch analytics')
        const analyticsData = await analyticsResponse.json()
        setData(analyticsData)

        // ✅ Fetch monthly trend data separately
        const trendResponse = await fetch(`${backendUrl}/api/monthly-trend`)
        if (!trendResponse.ok) throw new Error('Failed to fetch monthly trend')
        const trendData = await trendResponse.json()
        console.log('✅ Monthly trend data:', trendData)
        setMonthlyTrend(trendData.data)

      } catch (err) {
        console.error('❌ Fetch error:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchAllData()
  }, [])

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-white text-xl">Loading analytics...</div>
        </div>
      </Layout>
    )
  }

  if (error || !data) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-red-500 text-xl">Error: {error || 'No data available'}</div>
        </div>
      </Layout>
    )
  }

  // Transform risk distributions for pie charts
  const climateChartData = Object.entries(data.risk_distribution.climate).map(([name, value]) => ({
    name,
    value
  }))

  const conflictChartData = Object.entries(data.risk_distribution.conflict).map(([name, value]) => ({
    name,
    value
  }))

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">📊 Bivariate Analytics Dashboard</h1>
          <p className="text-slate-400">Comprehensive climate + conflict data analysis and trends</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="text-slate-400 text-sm mb-2">Total Events</div>
            <div className="text-3xl font-bold text-teal-400">{data.summary.total_events.toLocaleString()}</div>
          </div>

          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="text-slate-400 text-sm mb-2">Total Fatalities</div>
            <div className="text-3xl font-bold text-red-400">{data.summary.total_fatalities.toLocaleString()}</div>
          </div>

          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="text-slate-400 text-sm mb-2">Avg Climate Risk</div>
            <div className="text-3xl font-bold text-amber-400">{(data.summary.avg_climate_risk ?? 0).toFixed(1)}</div>
          </div>

          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="text-slate-400 text-sm mb-2">Avg Conflict Risk</div>
            <div className="text-3xl font-bold text-orange-400">{(data.summary.avg_conflict_proneness ?? 0).toFixed(1)}</div>
          </div>

          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="text-slate-400 text-sm mb-2">Regions Monitored</div>
            <div className="text-3xl font-bold text-blue-400">{data.summary.total_regions}</div>
          </div>
        </div>

        {/* ✅ FIXED: Monthly Conflict Trend - Using real data */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">📈 Monthly Conflict Trend</h2>
          {monthlyTrend.length === 0 ? (
            <div className="text-slate-400 text-center py-8">No monthly trend data available</div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Legend />
                <Line type="monotone" dataKey="events" stroke="#06b6d4" strokeWidth={2} name="Events" />
                <Line type="monotone" dataKey="fatalities" stroke="#ef4444" strokeWidth={2} name="Fatalities" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Risk Distribution - Climate vs Conflict */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Climate Risk Distribution */}
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">🌡️ Climate Risk Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={climateChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {climateChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CLIMATE_COLORS[entry.name as keyof typeof CLIMATE_COLORS] || '#6b7280'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {climateChartData.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: CLIMATE_COLORS[item.name as keyof typeof CLIMATE_COLORS] }}
                    />
                    <span className="text-slate-300">{item.name}</span>
                  </div>
                  <span className="font-bold text-white">{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Conflict Risk Distribution */}
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">⚔️ Conflict Risk Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={conflictChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {conflictChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CONFLICT_COLORS[entry.name as keyof typeof CONFLICT_COLORS] || '#6b7280'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {conflictChartData.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: CONFLICT_COLORS[item.name as keyof typeof CONFLICT_COLORS] }}
                    />
                    <span className="text-slate-300">{item.name}</span>
                  </div>
                  <span className="font-bold text-white">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top 10 High-Risk Regions */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">🎯 Top 10 High-Risk Regions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-900">
                <tr>
                  <th className="p-2 text-left text-slate-300">#</th>
                  <th className="p-2 text-left text-slate-300">Region</th>
                  <th className="p-2 text-center text-slate-300">Climate Risk</th>
                  <th className="p-2 text-center text-slate-300">Conflict Risk</th>
                  <th className="p-2 text-center text-slate-300">Events</th>
                  <th className="p-2 text-center text-slate-300">Deaths</th>
                </tr>
              </thead>
              <tbody>
                {data.top_regions.map((region, index) => (
                  <tr key={index} className="border-t border-slate-700 hover:bg-slate-750">
                    <td className="p-2 text-slate-400">{index + 1}</td>
                    <td className="p-2 text-white font-medium">{region.region || 'N/A'}</td>
                    <td className="p-2 text-center">
                      <span className="text-amber-400 font-bold">
                        {(region.climate_risk_score ?? 0).toFixed(2)}
                      </span>
                      <br />
                      <span
                        className="px-2 py-1 rounded-full text-xs font-bold"
                        style={{
                          backgroundColor: (CLIMATE_COLORS[region.cdi_category as keyof typeof CLIMATE_COLORS] || '#6b7280') + '33',
                          color: CLIMATE_COLORS[region.cdi_category as keyof typeof CLIMATE_COLORS] || '#6b7280'
                        }}
                      >
                        {region.cdi_category || 'N/A'}
                      </span>
                    </td>
                    <td className="p-2 text-center">
                      <span className="text-red-400 font-bold">
                        {(region.political_risk_score ?? 0).toFixed(2)}
                      </span>
                      <br />
                      <span
                        className="px-2 py-1 rounded-full text-xs font-bold"
                        style={{
                          backgroundColor: (CONFLICT_COLORS[region.risk_category as keyof typeof CONFLICT_COLORS] || '#6b7280') + '33',
                          color: CONFLICT_COLORS[region.risk_category as keyof typeof CONFLICT_COLORS] || '#6b7280'
                        }}
                      >
                        {region.risk_category || 'N/A'}
                      </span>
                    </td>
                    <td className="p-2 text-center text-teal-400">{region.events_6m ?? 0}</td>
                    <td className="p-2 text-center text-red-400">{region.fatalities_6m ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Regional Comparison Bar Chart */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">🗺️ Regional Climate vs Conflict Risk</h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.regional_data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="region"
                angle={-45}
                textAnchor="end"
                height={120}
                stroke="#9ca3af"
                interval={0}
              />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend />
              <Bar dataKey="climate_risk_score" fill="#f59e0b" name="Climate Risk" />
              <Bar dataKey="political_risk_score" fill="#ef4444" name="Conflict Risk" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Layout>
  )
}
