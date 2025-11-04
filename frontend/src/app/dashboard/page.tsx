'use client'

import React from 'react'
import { Layout } from '@/components/layout/Layout'
import { MetricsCard } from './components/MetricsCard'
import { useData } from './hooks/useData'

export default function DashboardPage() {
  const { summary, loading } = useData()

  return (
    <Layout>
      <div className="space-y-8">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Dashboard Overview</h1>
          <p className="text-slate-400">Real-time Sudan conflict risk assessment</p>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricsCard
            title="Conflict Events"
            value={summary?.summary?.conflict_events || 0}
            change="+12.5%"
            color="red"
            icon="⚡"
          />
          <MetricsCard
            title="States Analyzed"
            value={summary?.summary?.states_analyzed || 0}
            change="+8%"
            color="orange"
            icon="📍"
          />
          <MetricsCard
            title="Risk Assessments"
            value={summary?.summary?.risk_assessments || 0}
            change="+15%"
            color="yellow"
            icon="📊"
          />
          <MetricsCard
            title="Data Confidence"
            value="94.8%"
            change="+2.3%"
            color="green"
            icon="✓"
          />
        </div>

        {/* Quick Insights */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold text-white mb-4">Quick Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-slate-400 mb-1">Highest Risk State</p>
              <p className="text-2xl font-bold text-red-400">Khartoum</p>
            </div>
            <div>
              <p className="text-sm text-slate-400 mb-1">Active Alerts</p>
              <p className="text-2xl font-bold text-orange-400">8</p>
            </div>
            <div>
              <p className="text-sm text-slate-400 mb-1">Trend Direction</p>
              <p className="text-2xl font-bold text-yellow-400">↗ Rising</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
