'use client'

import { useState, useEffect } from 'react'
import AIAlertFeed from './AIAlertFeed'
import RiskIndicators from './RiskIndicators'
import RiskTrendChart from './RiskTrendChart'

export default function RightPanel() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch analytics data
    const fetchData = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/analytics`)
        const data = await res.json()
        setAnalytics(data)
      } catch (err) {
        console.error('Failed to fetch analytics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) return <div className="w-96 bg-gray-900 p-4">Loading...</div>

  return (
    <aside className="w-96 bg-gray-900 border-l border-gray-800 p-6 overflow-y-auto space-y-6">
      {/* AI Alert Feed */}
      <AIAlertFeed />

      {/* Country Overview */}
      <div className="border-b border-gray-800 pb-4">
        <h2 className="text-xl font-bold">Sudan</h2>
        <p className="text-xs text-gray-400">Climate & Conflict Risk | October 2025</p>
      </div>

      {/* Risk Indicators */}
      {analytics && <RiskIndicators summary={analytics.summary} />}

      {/* Trend Chart */}
      <RiskTrendChart />
    </aside>
  )
}
