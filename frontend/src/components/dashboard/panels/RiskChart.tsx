'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function RiskChart() {
  const [data, setData] = useState<any[]>([])

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
        <button className="text-orange-600 hover:text-orange-700 transition">−</button>
      </h3>
      {data.length > 0 ? (
        <div className="bg-gray-50 p-3">
          {/* UPDATED: Increased height from 150 to 220 for better visibility */}
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 5 }}>
              <CartesianGrid stroke="#E5E7EB" strokeDasharray="3 3" />
              <XAxis 
                dataKey="month" 
                tick={{ fontSize: 10 }} 
                stroke="#9CA3AF"
              />
              {/* UPDATED: Show Y-axis for better context */}
              <YAxis 
                tick={{ fontSize: 10 }} 
                stroke="#9CA3AF"
                width={30}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #d1d5db',
                  borderRadius: '0',
                  fontSize: '11px',
                  padding: '8px'
                }}
              />
              {/* Conflict Risk - Brand Orange #F37420 */}
              <Line
                type="monotone"
                dataKey="events"
                stroke="#F37420"
                strokeWidth={2.5}
                dot={{ fill: '#F37420', r: 3 }}
                activeDot={{ r: 5 }}
                name="Conflict Risk"
              />
              {/* Climate Risk - Brand Teal #049787 */}
              <Line
                type="monotone"
                dataKey="fatalities"
                stroke="#049787"
                strokeWidth={2.5}
                dot={{ fill: '#049787', r: 3 }}
                activeDot={{ r: 5 }}
                name="Climate Risk"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="text-xs text-gray-500 bg-gray-50 p-3">Loading chart...</p>
      )}
      <div className="flex gap-6 mt-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-sm" style={{ backgroundColor: '#F37420' }}></div>
          <span className="text-gray-700 font-medium">Conflict Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-sm" style={{ backgroundColor: '#049787' }}></div>
          <span className="text-gray-700 font-medium">Climate Risk</span>
        </div>
      </div>
    </div>
  )
}
