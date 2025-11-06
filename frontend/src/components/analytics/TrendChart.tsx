'use client'

import React, { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface TrendData {
  month: string
  events: number
  fatalities: number
}

interface ApiResponse {
  data: TrendData[]
  summary: {
    total_months: number
    avg_monthly_events: number
    avg_monthly_fatalities: number
    trend: string
  }
}

export function TrendChart() {
  const [data, setData] = useState<TrendData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMonthlyTrend = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/monthly-trend`)
        if (!response.ok) throw new Error(`API error: ${response.status}`)
        
        const result: ApiResponse = await response.json()
        console.log('✅ Monthly trend data loaded:', result)
        setData(result.data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        console.error('❌ Failed to fetch monthly trend:', message)
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    fetchMonthlyTrend()
  }, [])

  if (loading) {
    return (
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h2 className="text-xl font-bold text-white mb-4">📈 Monthly Conflict Trend</h2>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500 mx-auto" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-slate-800 p-6 rounded-lg border border-red-700 bg-red-900/20">
        <h2 className="text-xl font-bold text-red-400 mb-4">📈 Monthly Conflict Trend</h2>
        <p className="text-red-400">Failed to load chart: {error}</p>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h2 className="text-xl font-bold text-white mb-4">📈 Monthly Conflict Trend</h2>
        <p className="text-slate-400">No data available</p>
      </div>
    )
  }

  return (
    <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
      <h2 className="text-xl font-bold text-white mb-4">📈 Monthly Conflict Trend</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
          <XAxis dataKey="month" stroke="#94a3b8" style={{ fontSize: '12px' }} />
          <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
            labelStyle={{ color: '#94a3b8' }}
            cursor={{ stroke: '#0891b2' }}
          />
          <Legend />
          <Line type="monotone" dataKey="events" stroke="#14b8a6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
          <Line type="monotone" dataKey="fatalities" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
