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
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">Interactive Risk Map</h1>
          <p className="text-lg text-slate-400">Geographic visualization of conflict risk across Sudan</p>
        </div>

        {/* Backend Status Warning */}
        {!isBackendAvailable && !checking && (
          <div className="mb-4 p-4 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <h3 className="text-yellow-400 font-semibold mb-1">Backend API Not Available</h3>
                <p className="text-yellow-200 text-sm mb-2">
                  The backend server is not running. Start it with:
                </p>
                <code className="bg-slate-900 px-3 py-1 rounded text-sm text-green-400 block">
                  cd ~/Desktop/projects/sudan-cram-v2/backend && uvicorn app.main:app --reload --port 8000
                </code>
                <p className="text-yellow-200 text-sm mt-2">
                  The map will show demo data until the backend is connected.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Map Container */}
        <div className="flex-1 bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <MapComponent backendAvailable={isBackendAvailable} />
        </div>
      </div>
    </Layout>
  )
}
