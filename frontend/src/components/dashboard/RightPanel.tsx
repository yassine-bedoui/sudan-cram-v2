'use client'

import { useState, useEffect } from 'react'
import AIAlertFeed from './panels/AIAlertFeed'
import RiskIndicators from './panels/RiskIndicators'
import RiskTrendChart from './panels/RiskChart'
import CountryHeader from './panels/CountryHeader'
import Description from './panels/Description'
import DownloadOptions from './panels/DownloadOptions'
import DataSources from './panels/DataSources'
import GoldsteinEscalationPanel from './panels/GoldsteinEscalationPanel'  // Updated path

export default function RightPanel() {
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalytics = async () => {
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

    fetchAnalytics()
  }, [])

  if (loading) {
    return <aside className="w-80">Loading...</aside>
  }

  return (
    <aside className="w-80 space-y-4 overflow-y-auto">
      <CountryHeader />
      {analytics && <RiskIndicators summary={analytics.summary} />}
      <RiskTrendChart />
      <GoldsteinEscalationPanel />
      <AIAlertFeed />
      <Description />
      <DownloadOptions />
      <DataSources />
    </aside>
  )
}