'use client'

import React, { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { Layout } from '@/components/layout/Layout'

// Dynamically import map component (client-side only)
const MapComponent = dynamic(
  () => import('@/components/map/SudanMap'),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full">
        <div className="text-white">Loading map...</div>
      </div>
    )
  }
)

export default function MapPage() {
  const [isBackendAvailable, setIsBackendAvailable] = useState(false)
  const [checking, setChecking] = useState(true)
  const [selectedIndicator, setSelectedIndicator] = useState('conflict_proneness')

  useEffect(() => {
    // Check if backend is available
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/conflict-proneness')
        if (response.ok) {
          setIsBackendAvailable(true)
        }
      } catch (error) {
        console.log('Backend not available yet')
        setIsBackendAvailable(false)
      } finally {
        setChecking(false)
      }
    }

    checkBackend()
  }, [])

  return (
    <Layout>
      <div className="h-full flex flex-col">
        {/* Page Header */}
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Interactive Risk Map</h1>
            <p className="text-lg text-slate-400">Geographic visualization of conflict risk across Sudan</p>
          </div>
          
          {/* Indicator Selector */}
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-slate-300">Indicator:</label>
            <select 
              value={selectedIndicator}
              onChange={(e) => setSelectedIndicator(e.target.value)}
              className="px-4 py-2 bg-slate-800 text-white border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="conflict_proneness">Conflict Proneness</option>
              <option value="drought_severity" disabled>Drought Severity (Coming Soon)</option>
              <option value="food_insecurity" disabled>Food Insecurity (Coming Soon)</option>
            </select>
          </div>
        </div>

        {/* Backend Status Warning */}
        {!isBackendAvailable && !checking && (
          <div className="mb-4 p-4 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <h3 className="text-yellow-400 font-semibold mb-1">Backend API Not Available</h3>
                <p className="text-yellow-200 text-sm">
                  Start the backend with: <code className="bg-slate-900 px-2 py-1 rounded text-sm text-green-400">uvicorn app.main:app --reload --port 8000</code>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Map Container */}
        <div className="flex-1 bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <MapComponent 
            backendAvailable={isBackendAvailable} 
            indicator={selectedIndicator}
          />
        </div>
      </div>
    </Layout>
  )
}
