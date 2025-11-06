// src/app/dashboard/page.tsx
'use client'

import React, { useEffect, useState } from 'react'
import { Layout } from '@/components/layout/Layout'
import { cramAPI } from '@/lib/api'
import type { DashboardStats, AnalyticsResponse } from '@/lib/api'
import BivariateCards from '@/components/analytics/BivariateCards'
import BivariateTable from '@/components/analytics/BivariateTable'

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch both dashboard stats and analytics
        const [dashboardData, analyticsData] = await Promise.all([
          cramAPI.getDashboardStats(),
          cramAPI.getAnalytics()
        ])

        setStats(dashboardData)
        setAnalytics(analyticsData)
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-white text-xl">Loading dashboard...</div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-red-400 text-lg">Error: {error}</div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Dashboard Overview</h1>
          <p className="text-lg text-slate-400">Real-time Sudan conflict risk assessment</p>
        </div>

        {/* Key Metrics Cards (existing) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">Conflict Events</span>
              <div className="w-12 h-12 rounded-lg bg-red-500/20 flex items-center justify-center">
                <span className="text-2xl">⚡</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-red-400 mb-2">
              {stats?.summary.conflict_events.toLocaleString() ?? 0}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 font-medium">
                +12.5%
              </span>
              <span className="text-xs text-slate-500">this month</span>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">States Analyzed</span>
              <div className="w-12 h-12 rounded-lg bg-orange-500/20 flex items-center justify-center">
                <span className="text-2xl">📍</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-orange-400 mb-2">
              {stats?.summary.states_analyzed ?? 0}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 font-medium">
                +8%
              </span>
              <span className="text-xs text-slate-500">this month</span>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">Risk Assessments</span>
              <div className="w-12 h-12 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                <span className="text-2xl">📊</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-yellow-400 mb-2">
              {stats?.summary.risk_assessments ?? 0}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 font-medium">
                +15%
              </span>
              <span className="text-xs text-slate-500">this month</span>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl hover:shadow-2xl transition-all">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm font-medium">Data Confidence</span>
              <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
                <span className="text-2xl">✓</span>
              </div>
            </div>
            <div className="text-4xl font-bold text-green-400 mb-2">
              {stats?.summary.data_confidence ?? 0}%
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 font-medium">
                +2.3%
              </span>
              <span className="text-xs text-slate-500">this month</span>
            </div>
          </div>
        </div>

        {/* Quick Insights */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-8 border border-slate-700 shadow-xl">
          <h2 className="text-2xl font-bold text-white mb-6">Quick Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-2">
              <p className="text-sm text-slate-400 font-medium">Highest Risk State</p>
              <p className="text-3xl font-bold text-red-400">{stats?.quick_insights.highest_risk_state ?? 'N/A'}</p>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div className="bg-red-500 h-2 rounded-full" style={{ width: '85%' }}></div>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-slate-400 font-medium">Active Alerts</p>
              <p className="text-3xl font-bold text-orange-400">{stats?.quick_insights.active_alerts ?? 0}</p>
              <div className="flex gap-2 mt-2">
                <span className="px-3 py-1 bg-orange-900/30 text-orange-400 rounded-full text-xs font-medium">
                  {stats?.quick_insights.alert_breakdown.high ?? 0} High
                </span>
                <span className="px-3 py-1 bg-yellow-900/30 text-yellow-400 rounded-full text-xs font-medium">
                  {stats?.quick_insights.alert_breakdown.very_high ?? 0} V.High
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-slate-400 font-medium">Trend Direction</p>
              <div className="flex items-center gap-3">
                <p className="text-3xl font-bold text-yellow-400">↗</p>
                <div>
                  <p className="text-xl font-bold text-yellow-400">{stats?.quick_insights.trend.direction ?? 'Unknown'}</p>
                  <p className="text-sm text-slate-500">+{stats?.quick_insights.trend.percentage ?? 0}% trend</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bivariate Analysis Section */}
        <div className="border-t-2 border-slate-700 pt-8">
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-white mb-2">Bivariate Risk Analysis</h2>
            <p className="text-slate-400">Climate + Conflict dual-dimension assessment</p>
          </div>

          {/* Bivariate Cards */}
          {analytics ? (
            <>
              <BivariateCards analytics={analytics} />
              <BivariateTable regions={analytics.regional_data} />
            </>
          ) : (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-6">
              <p className="text-red-400">Failed to load bivariate data</p>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-8 border border-slate-700 shadow-xl">
          <h2 className="text-2xl font-bold text-white mb-6">Recent Activity</h2>
          <div className="space-y-4">
            {[
              { type: 'alert', text: `New high-risk alert in ${stats?.quick_insights.highest_risk_state}`, time: '5 min ago', color: 'red' },
              { type: 'update', text: 'Risk assessment updated for North Darfur', time: '12 min ago', color: 'blue' },
              { type: 'event', text: `${stats?.summary.conflict_events} conflict events recorded`, time: '1 hour ago', color: 'orange' },
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
