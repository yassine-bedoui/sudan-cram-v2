'use client'

import React, { useState, useEffect } from 'react'
import { Layout } from '@/components/layout/Layout'

interface Alert {
  region: string
  week: string
  risk_score: number
  event_count: number
  alert_level: string
  explanation: string
}

interface AlertResponse {
  alerts: Alert[]
  total_alerts: number
  source: string
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedLevel, setSelectedLevel] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'risk' | 'date'>('risk')

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    setLoading(true)
    setError(null)
    
    try {
      console.log('Fetching alerts from backend...')
      
      const response = await fetch('${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/alerts')
      console.log('Response status:', response.status)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data: AlertResponse = await response.json()
      console.log('Response data:', data)
      
      if (data.alerts) {
        setAlerts(data.alerts || [])
        console.log(`Loaded ${data.alerts?.length || 0} alerts`)
      } else {
        throw new Error('No alerts in response')
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
      setError(error instanceof Error ? error.message : 'Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (level: string) => {
    const colors: Record<string, string> = {
      SEVERE: 'bg-red-600 text-white border-red-700',
      HIGH: 'bg-orange-500 text-white border-orange-600',
      MEDIUM: 'bg-yellow-500 text-slate-900 border-yellow-600',
      LOW: 'bg-green-500 text-white border-green-600'
    }
    return colors[level.toUpperCase()] || 'bg-gray-500'
  }

  const getSeverityIcon = (level: string) => {
    const icons: Record<string, string> = {
      SEVERE: '🚨',
      HIGH: '⚠️',
      MEDIUM: '⚡',
      LOW: 'ℹ️'
    }
    return icons[level.toUpperCase()] || '📋'
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      })
    } catch {
      return dateStr
    }
  }

  const exportToCSV = () => {
    const headers = ['Region', 'Week', 'Risk Score', 'Events', 'Severity', 'Explanation']
    const rows = filteredAlerts.map(alert => [
      alert.region,
      alert.week,
      alert.risk_score.toFixed(2),
      alert.event_count,
      alert.alert_level,
      alert.explanation.replace(/,/g, ';')
    ])

    const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `sudan-cram-alerts-${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  let filteredAlerts = alerts.filter(alert => 
    (selectedLevel === 'ALL' || alert.alert_level === selectedLevel) &&
    (searchQuery === '' || 
     alert.region.toLowerCase().includes(searchQuery.toLowerCase()) ||
     alert.explanation.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  // Sort alerts
  if (sortBy === 'risk') {
    filteredAlerts.sort((a, b) => b.risk_score - a.risk_score)
  } else {
    filteredAlerts.sort((a, b) => new Date(b.week).getTime() - new Date(a.week).getTime())
  }

  // Calculate summary
  const summary = {
    total: alerts.length,
    severe: alerts.filter(a => a.alert_level === 'SEVERE').length,
    high: alerts.filter(a => a.alert_level === 'HIGH').length,
    medium: alerts.filter(a => a.alert_level === 'MEDIUM').length,
    low: alerts.filter(a => a.alert_level === 'LOW').length,
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4 animate-spin">🔄</div>
            <div className="text-xl font-semibold text-white">Loading alerts...</div>
            <div className="text-sm text-slate-400 mt-2">Fetching from backend...</div>
          </div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-8 max-w-2xl">
            <div className="text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <div className="text-2xl font-semibold text-red-400 mb-4">Failed to Load Alerts</div>
              <div className="text-slate-300 mb-6">{error}</div>
              <button
                onClick={fetchAlerts}
                className="px-6 py-3 bg-teal-600 hover:bg-teal-700 text-white rounded-lg transition-colors font-medium"
              >
                🔄 Retry
              </button>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">Alert Management</h1>
          <p className="text-lg text-slate-400">Real-time conflict risk alerts across Sudan</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
            <div className="text-sm text-slate-400 mb-1">Total Alerts</div>
            <div className="text-3xl font-bold text-white">{summary.total}</div>
          </div>
          <div className="bg-red-900/20 border-red-700/50 p-4 rounded-lg border">
            <div className="text-sm text-red-400 mb-1">Severe</div>
            <div className="text-3xl font-bold text-red-500">{summary.severe}</div>
          </div>
          <div className="bg-orange-900/20 border-orange-700/50 p-4 rounded-lg border">
            <div className="text-sm text-orange-400 mb-1">High</div>
            <div className="text-3xl font-bold text-orange-500">{summary.high}</div>
          </div>
          <div className="bg-yellow-900/20 border-yellow-700/50 p-4 rounded-lg border">
            <div className="text-sm text-yellow-400 mb-1">Medium</div>
            <div className="text-3xl font-bold text-yellow-500">{summary.medium}</div>
          </div>
          <div className="bg-green-900/20 border-green-700/50 p-4 rounded-lg border">
            <div className="text-sm text-green-400 mb-1">Low</div>
            <div className="text-3xl font-bold text-green-500">{summary.low}</div>
          </div>
        </div>

        {/* Filters and Actions */}
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 mb-4 flex items-center gap-4 flex-wrap">
          <div className="flex-1 min-w-xs">
            <input
              type="text"
              placeholder="Search by region..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-slate-900 text-white border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-400">Level:</label>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="px-4 py-2 bg-slate-900 text-white border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="ALL">All Levels</option>
              <option value="SEVERE">Severe</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-400">Sort:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'risk' | 'date')}
              className="px-4 py-2 bg-slate-900 text-white border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="risk">By Risk Score</option>
              <option value="date">By Date</option>
            </select>
          </div>
          <button
            onClick={exportToCSV}
            disabled={filteredAlerts.length === 0}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            📥 Export CSV
          </button>
        </div>

        {/* Alerts List */}
        <div className="flex-1 overflow-y-auto space-y-3">
          {filteredAlerts.length === 0 ? (
            <div className="bg-slate-800 p-8 rounded-lg border border-slate-700 text-center">
              <div className="text-4xl mb-4">🔍</div>
              <div className="text-xl font-semibold text-white mb-2">No alerts found</div>
              <p className="text-slate-400">Try adjusting your filters or search query</p>
            </div>
          ) : (
            filteredAlerts.map((alert, idx) => (
              <div
                key={`${alert.region}-${alert.week}-${idx}`}
                className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden transition-all hover:border-slate-600 hover:shadow-lg hover:shadow-slate-900/50"
              >
                <div className="p-4">
                  <div className="flex items-start gap-4">
                    {/* Severity Badge */}
                    <div className="flex-shrink-0">
                      <div className={`px-3 py-1 rounded-lg text-sm font-bold border ${getSeverityColor(alert.alert_level)}`}>
                        {getSeverityIcon(alert.alert_level)} {alert.alert_level}
                      </div>
                    </div>

                    {/* Alert Content */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-bold text-white mb-1">{alert.region}</h3>
                          <div className="flex items-center gap-3 text-sm text-slate-400">
                            <span>📅 {formatDate(alert.week)}</span>
                            <span>•</span>
                            <span>📊 Risk: {alert.risk_score.toFixed(2)}</span>
                            <span>•</span>
                            <span>🔥 {alert.event_count} events</span>
                          </div>
                        </div>
                      </div>

                      <p className="text-slate-300 text-sm">{alert.explanation}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Layout>
  )
}
