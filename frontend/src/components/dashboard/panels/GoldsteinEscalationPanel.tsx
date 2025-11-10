// frontend/src/components/dashboard/panels/GoldsteinEscalationPanel.tsx
'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface EscalationData {
  location: string
  escalation_risk: number  // CHANGED: was risk_score
  risk_level: string
  avg_goldstein: number
  goldstein_trend: number  // CHANGED: added this
  event_count: number
}

export default function GoldsteinEscalationPanel() {
  const [topRisks, setTopRisks] = useState<EscalationData[]>([])
  const [timeline, setTimeline] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const risksRes = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/goldstein/top-risks?limit=5`)
        
        if (!risksRes.ok) {
          throw new Error(`API Error: ${risksRes.status}`)
        }
        
        const risksData = await risksRes.json()
        
        if (risksData && risksData.top_risks && Array.isArray(risksData.top_risks)) {
          setTopRisks(risksData.top_risks)
        } else {
          throw new Error('Invalid data format')
        }

        const timelineRes = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/goldstein/timeline?hours=24`)
        
        if (timelineRes.ok) {
          const timelineData = await timelineRes.json()
          
          if (timelineData && Array.isArray(timelineData.timestamps)) {
            const chartData = timelineData.timestamps.map((ts: string, i: number) => ({
              time: new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
              goldstein: timelineData.goldstein_scores[i],
              events: timelineData.event_counts[i]
            }))
            setTimeline(chartData)
          }
        }
        
        setLoading(false)
      } catch (err: any) {
        console.error('Goldstein fetch error:', err)
        setError(err.message)
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 300000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="border border-gray-300 p-4 bg-white">
        <p className="text-xs text-gray-600">Loading escalation data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="border border-gray-300 p-4 bg-gray-50">
        <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-2 font-bold">
          Goldstein Data Unavailable
        </h3>
        <p className="text-xs text-gray-600 mb-2">{error}</p>
        <p className="text-xs text-gray-500 mt-2">
          Run: <code className="bg-gray-200 px-1">python scripts/gdelt/fetch_sudan_events.py</code>
        </p>
      </div>
    )
  }

  if (!topRisks || topRisks.length === 0) {
    return (
      <div className="border border-gray-300 p-4 bg-white">
        <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-2 font-bold">
          No Escalation Data
        </h3>
        <p className="text-xs text-gray-600">
          Run GDELT scripts to populate data.
        </p>
      </div>
    )
  }

  const getRiskColor = (level: string) => {
    const colors: Record<string, string> = {
      'CRITICAL': 'border-red-600',
      'HIGH': 'border-orange-600',
      'MODERATE': 'border-yellow-500'
    }
    return colors[level] || 'border-green-500'
  }

  const getRiskBgColor = (level: string) => {
    const colors: Record<string, string> = {
      'CRITICAL': 'bg-red-50',
      'HIGH': 'bg-orange-50',
      'MODERATE': 'bg-yellow-50'
    }
    return colors[level] || 'bg-green-50'
  }

  return (
    <div className="space-y-4">
      <div className="border border-gray-300 p-4 bg-white">
        <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-4 font-bold">
          Top Escalation Risks (GDELT)
        </h3>

        <div className="space-y-3">
          {topRisks.map((risk, i) => (
            <div
              key={i}
              className={`border-l-4 ${getRiskColor(risk.risk_level)} ${getRiskBgColor(risk.risk_level)} pl-3 py-2`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-xs font-bold text-gray-900">
                    {risk.location}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    Goldstein: {risk.avg_goldstein?.toFixed(1) ?? 'N/A'} | {risk.event_count ?? 0} events
                    {risk.goldstein_trend && (
                      <span> | {risk.goldstein_trend < 0 ? '⬇️ Escalating' : '⬆️ Stable'}</span>
                    )}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-mono font-bold text-orange-600">
                    {risk.escalation_risk?.toFixed(1) ?? 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500">{risk.risk_level ?? 'UNKNOWN'}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <p className="text-xs text-gray-500 mt-3">
          Real-time data from GDELT
        </p>
      </div>

      {timeline && timeline.length > 0 && (
        <div className="border border-gray-300 p-4 bg-white">
          <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-4 font-bold">
            Goldstein Trend (24h)
          </h3>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10 }}
                  stroke="#9ca3af"
                />
                <YAxis
                  domain={[-10, 10]}
                  tick={{ fontSize: 10 }}
                  stroke="#9ca3af"
                />
                <Tooltip />
                <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
                <ReferenceLine y={-5} stroke="#dc2626" strokeDasharray="2 2" />
                <Line
                  type="monotone"
                  dataKey="goldstein"
                  stroke="#F37420"
                  strokeWidth={2.5}
                  dot={{ fill: '#F37420', r: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-3 text-xs text-gray-600">
            <p>+10 (cooperation) to -10 (extreme violence)</p>
          </div>
        </div>
      )}
    </div>
  )
}
