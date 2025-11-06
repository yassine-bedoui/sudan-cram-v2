'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useEffect, useState } from 'react'

export default function RiskTrendChart() {
  const [data, setData] = useState([])

  useEffect(() => {
    // Fetch monthly trend data
    const fetchTrends = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/monthly-trend`)
        const response = await res.json()
        setData(response.data || [])
      } catch (err) {
        console.error('Failed to fetch trends:', err)
      }
    }

    fetchTrends()
  }, [])

  return (
    <div>
      <h3 className="text-sm font-bold uppercase text-gray-400 mb-4">Risk Trend Analysis</h3>

      {data.length > 0 && (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
            <XAxis dataKey="month" stroke="#999" />
            <YAxis stroke="#999" />
            <Tooltip contentStyle={{ backgroundColor: '#222', border: '1px solid #444' }} />
            <Legend />
            <Line type="monotone" dataKey="events" stroke="#ef4444" name="Conflict Events" />
            <Line type="monotone" dataKey="fatalities" stroke="#f97316" name="Fatalities Trend" />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
