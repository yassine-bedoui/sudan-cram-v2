'use client'

import React, { useState, useEffect } from 'react'
import { Layout } from '@/components/layout/Layout'
import dynamic from 'next/dynamic'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

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
    EVENTS: number
    FATALITIES: number
    avg_risk: number
  }>
  regional_data: Array<{
    ADMIN1: string
    EVENTS: number
    FATALITIES: number
    risk_score: number
    risk_category: string
  }>
  risk_distribution: Record<string, number>
  top_regions: Array<{
    ADMIN1: string
    EVENTS: number
    FATALITIES: number
    risk_score: number
    risk_category: string
  }>
}

const RISK_COLORS = {
  LOW: '#91cf60',
  MEDIUM: '#fee08b',
  HIGH: '#fc8d59',
  SEVERE: '#d73027',
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/analytics/`)
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

  // Transform risk_distribution for pie chart
  const riskChartData = Object.entries(data.risk_distribution).map(([name, value]) => ({
    name,
    value
  }))

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">📊 Analytics Dashboard</h1>
          <p className="text-slate-400">Comprehensive conflict data analysis and trends</p>
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
            <div className="text-slate-400 text-sm mb-2">Avg Risk Score</div>
            <div className="text-3xl font-bold text-yellow-400">{data.summary.avg_risk_score.toFixed(1)}</div>
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

        {/* Monthly Conflict Trend */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">📈 Monthly Conflict Trend</h2>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data.monthly_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend />
              <Line type="monotone" dataKey="EVENTS" stroke="#06b6d4" strokeWidth={2} name="Events" />
              <Line type="monotone" dataKey="FATALITIES" stroke="#ef4444" strokeWidth={2} name="Fatalities" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Regional Comparison and Risk Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Risk Level Distribution */}
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">📊 Risk Level Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie 
                  data={riskChartData} 
                  cx="50%" 
                  cy="50%" 
                  innerRadius={60} 
                  outerRadius={100} 
                  paddingAngle={2} 
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {riskChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.name as keyof typeof RISK_COLORS] || '#6b7280'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {riskChartData.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: RISK_COLORS[item.name as keyof typeof RISK_COLORS] }}
                    />
                    <span className="text-slate-300">{item.name}</span>
                  </div>
                  <span className="font-bold text-white">{item.value}</span>
                </div>
              ))}
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
                    <th className="p-2 text-center text-slate-300">Events</th>
                    <th className="p-2 text-center text-slate-300">Deaths</th>
                    <th className="p-2 text-center text-slate-300">Risk</th>
                    <th className="p-2 text-center text-slate-300">Category</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_regions.map((region, index) => (
                    <tr key={index} className="border-t border-slate-700 hover:bg-slate-750">
                      <td className="p-2 text-slate-400">{index + 1}</td>
                      <td className="p-2 text-white font-medium">{region.ADMIN1}</td>
                      <td className="p-2 text-center text-teal-400">{region.EVENTS}</td>
                      <td className="p-2 text-center text-red-400">{region.FATALITIES}</td>
                      <td className="p-2 text-center font-bold text-white">{region.risk_score.toFixed(2)}</td>
                      <td className="p-2 text-center">
                        <span 
                          className="px-2 py-1 rounded-full text-xs font-bold"
                          style={{
                            backgroundColor: RISK_COLORS[region.risk_category as keyof typeof RISK_COLORS] + '33',
                            color: RISK_COLORS[region.risk_category as keyof typeof RISK_COLORS]
                          }}
                        >
                          {region.risk_category}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Regional Comparison Bar Chart */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">🗺️ Regional Comparison</h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.regional_data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="ADMIN1" 
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
              <Bar dataKey="EVENTS" fill="#06b6d4" name="Events" />
              <Bar dataKey="FATALITIES" fill="#ef4444" name="Fatalities" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Layout>
  )
}
