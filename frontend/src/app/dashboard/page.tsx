'use client'

import React, { useEffect, useState } from 'react'
import { Layout } from '@/components/layout/Layout'

interface DashboardStats {
  conflict_events: number
  states_analyzed: number
  risk_assessments: number
  data_confidence: number
  highest_risk_state: string
  active_alerts: number
  high_alerts: number
  medium_alerts: number
  trend_direction: string
  trend_percentage: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    conflict_events: 0,
    states_analyzed: 0,
    risk_assessments: 0,
    data_confidence: 94.8,
    highest_risk_state: '...',
    active_alerts: 0,
    high_alerts: 0,
    medium_alerts: 0,
    trend_direction: 'Rising',
    trend_percentage: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch dashboard stats from new endpoint
        const response = await fetch('http://localhost:8000/api/alerts/dashboard-stats')
        const data = await response.json()

        if (data && data.stats) {
          setStats(data.stats)
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return (
    <Layout>
      <div className="space-y-8">
        {/* Page Header */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Dashboard Overview</h1>
          <p className="text-lg text-slate-400">Real-time Sudan conflict risk assessment</p>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Conflict Events Card */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">Conflict Events</span>
              <div className="w-12 h-12 rounded-lg bg-red-500/20 flex items-center justify-center">
                <span className="text-2xl">⚡</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-red-400 mb-2">
              {loading ? '...' : stats.conflict_events.toLocaleString()}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 font-medium">
                +12.5%
              </span>
              <span className="text-xs text-slate-500">this month</span>
            </div>
          </div>

          {/* States Analyzed Card */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">States Analyzed</span>
              <div className="w-12 h-12 rounded-lg bg-orange-500/20 flex items-center justify-center">
                <span className="text-2xl">📍</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-orange-400 mb-2">
              {loading ? '...' : stats.states_analyzed}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 font-medium">
                +8%
              </span>
              <span className="text-xs text-slate-500">this month</span>
            </div>
          </div>

          {/* Risk Assessments Card */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">Risk Assessments</span>
              <div className="w-12 h-12 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <span className="text-2xl">📊</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-yellow-400 mb-2">
              {loading ? '...' : stats.risk_assessments}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 font-medium">
                +15%
              </span>
              <span className="text-xs text-slate-500">this month</span>
            </div>
          </div>

          {/* Data Confidence Card */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">Data Confidence</span>
              <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
                <span className="text-2xl">✓</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-green-400 mb-2">
              {loading ? '...' : stats.data_confidence}%
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 font-medium">
                +2.3%
              </span>
              <span className="text-xs text-slate-500">this month</span>
            </div>
          </div>
        </div>

        {/* Quick Insights Card */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-8 border border-slate-700 shadow-xl">
          <h2 className="text-2xl font-bold text-white mb-6">Quick Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-2">
              <p className="text-sm text-slate-400 font-medium">Highest Risk State</p>
              <p className="text-3xl font-bold text-red-400">{stats.highest_risk_state}</p>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div className="bg-red-500 h-2 rounded-full" style={{ width: '85%' }}></div>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-slate-400 font-medium">Active Alerts</p>
              <p className="text-3xl font-bold text-orange-400">{loading ? '...' : stats.active_alerts}</p>
              <div className="flex gap-2 mt-2">
                <span className="px-3 py-1 bg-orange-900/30 text-orange-400 rounded-full text-xs font-medium">
                  {stats.high_alerts} High
                </span>
                <span className="px-3 py-1 bg-yellow-900/30 text-yellow-400 rounded-full text-xs font-medium">
                  {stats.medium_alerts} Medium
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-slate-400 font-medium">Trend Direction</p>
              <div className="flex items-center gap-3">
                <p className="text-3xl font-bold text-yellow-400">↗</p>
                <div>
                  <p className="text-xl font-bold text-yellow-400">{stats.trend_direction}</p>
                  <p className="text-sm text-slate-500">+{stats.trend_percentage}% trend</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-8 border border-slate-700 shadow-xl">
          <h2 className="text-2xl font-bold text-white mb-6">Recent Activity</h2>
          <div className="space-y-4">
            {[
              { type: 'alert', text: `New high-risk alert in ${stats.highest_risk_state}`, time: '5 min ago', color: 'red' },
              { type: 'update', text: 'Risk assessment updated for North Darfur', time: '12 min ago', color: 'blue' },
              { type: 'event', text: `${stats.conflict_events} conflict events recorded`, time: '1 hour ago', color: 'orange' },
            ].map((activity, index) => (
              <div key={index} className="flex items-center gap-4 p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                <div className={`w-10 h-10 rounded-lg bg-${activity.color}-500/20 flex items-center justify-center flex-shrink-0`}>
                  <span className="text-xl">
                    {activity.type === 'alert' ? '⚠️' : activity.type === 'update' ? '🔄' : '📝'}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium">{activity.text}</p>
                  <p className="text-slate-500 text-sm">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
