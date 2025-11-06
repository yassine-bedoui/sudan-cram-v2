'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function RiskChart() {
  const [data, setData] = useState([])

  useEffect(() => {
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
    <div className="border border-gray-300 p-4 bg-white">
      <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-4 flex justify-between items-center font-bold">
        Risk Trend Analysis
        <button className="text-orange-600"><i>−</i></button>
      </h3>

      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={data}>
            <CartesianGrid stroke="#E5E7EB" />
            <XAxis dataKey="month" tick={{ fontSize: 10 }} stroke="#9CA3AF" />
            <YAxis hide={true} />
            <Tooltip />
            <Line type="monotone" dataKey="events" stroke="#E63E11" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="fatalities" stroke="#F97316" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-xs text-gray-500">Loading chart...</p>
      )}

      <div className="flex gap-4 mt-3 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-orange-600"></div>
          <span className="text-gray-600">Conflict Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-orange-500"></div>
          <span className="text-gray-600">Climate Risk</span>
        </div>
      </div>
    </div>
  )
}
