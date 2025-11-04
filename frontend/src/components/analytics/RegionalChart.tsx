'use client'

import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface RegionalData {
  region: string
  events: number
  fatalities: number
  risk_score: number
}

export function RegionalChart({ data }: { data: RegionalData[] }) {
  return (
    <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
      <h2 className="text-xl font-bold text-white mb-4">🏘️ Regional Comparison</h2>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
          <XAxis dataKey="region" stroke="#94a3b8" angle={-45} textAnchor="end" height={100} style={{ fontSize: '11px' }} />
          <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
            labelStyle={{ color: '#94a3b8' }}
          />
          <Legend />
          <Bar dataKey="events" fill="#14b8a6" />
          <Bar dataKey="fatalities" fill="#ef4444" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
