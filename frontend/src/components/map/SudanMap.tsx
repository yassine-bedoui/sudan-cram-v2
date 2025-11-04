'use client'

import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

interface SudanMapProps {
  backendAvailable: boolean
  indicator: string
}

const SUDAN_CENTER: [number, number] = [15.5007, 32.5599]

const STATE_COORDINATES: Record<string, [number, number]> = {
  'North Darfur': [15.7500, 24.8667],
  'Khartoum': [15.5007, 32.5599],
  'South Darfur': [11.5000, 24.8833],
  'North Kordofan': [13.1667, 29.4167],
  'Al Jazirah': [14.4000, 33.5000],
  'West Kordofan': [11.5000, 27.5000],
  'South Kordofan': [11.2000, 29.4167],
  'White Nile': [13.3000, 32.7000],
  'Central Darfur': [12.8500, 24.5833],
  'Abyei': [10.2833, 28.9833],
  'Blue Nile': [11.9000, 34.4000],
  'East Darfur': [11.7833, 26.6500],
  'Sennar': [13.5500, 33.6000],
  'Northern': [19.5667, 30.4167],
  'River Nile': [17.7000, 33.9000],
  'West Darfur': [12.8167, 22.9167],
  'Kassala': [15.4667, 36.4000],
  'Gedaref': [14.0333, 35.4000],
  'Red Sea': [18.4333, 37.2167],
}

const getRiskColor = (category: string): string => {
  if (!category) return '#9ca3af'
  
  const normalized = category.toString().toUpperCase().trim()
  
  const colorMap: Record<string, string> = {
    'VERY HIGH': '#dc2626',  // red-600
    'HIGH': '#f97316',        // orange-500
    'MODERATE': '#eab308',    // yellow-500
    'LOW': '#22c55e',         // green-500
  }
  
  return colorMap[normalized] || '#9ca3af'
}

const getRiskRadius = (incidents: number): number => {
  return Math.max(Math.sqrt(incidents) * 2.5, 10)
}

export default function SudanMap({ backendAvailable, indicator }: SudanMapProps) {
  const [stateData, setStateData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Record<string, number>>({})

  useEffect(() => {
    const fetchData = async () => {
      if (!backendAvailable) {
        setLoading(false)
        return
      }

      try {
        const response = await fetch('http://localhost:8000/api/conflict-proneness')
        const data = await response.json()
        
        if (data && data.data) {
          // Count risk categories for debugging
          const categoryCount: Record<string, number> = {}
          
          const transformedData = data.data
            .map((state: any) => {
              const stateName = state.state || state.ADM1_NAME || 'Unknown'
              const coords = STATE_COORDINATES[stateName]
              
              if (!coords) return null
              
              const riskCategory = state.cp_category || 'UNKNOWN'
              const incidents = parseInt(state.incidents || 0)
              
              // Count categories
              categoryCount[riskCategory] = (categoryCount[riskCategory] || 0) + 1
              
              return {
                name: stateName,
                position: coords,
                risk: riskCategory,
                incidents: incidents,
                score: parseFloat(state.cp_score || state.conflict_proneness_score || 0)
              }
            })
            .filter((item: any) => item !== null)
          
          console.log('Risk category breakdown:', categoryCount)
          setStats(categoryCount)
          setStateData(transformedData)
        }
      } catch (error) {
        console.error('Failed to fetch map data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [backendAvailable, indicator])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-900">
        <div className="text-white text-center">
          <div className="text-4xl mb-4">🗺️</div>
          <div className="text-xl font-semibold">Loading map...</div>
        </div>
      </div>
    )
  }

  if (!stateData.length) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-900">
        <div className="text-white text-center">
          <div className="text-4xl mb-4">📍</div>
          <div className="text-xl font-semibold">No data available</div>
          <p className="text-slate-400 mt-2">Check backend connection</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full w-full relative">
      {/* State count badge */}
      <div className="absolute top-4 right-4 z-[1000] bg-slate-900/95 text-white px-4 py-2 rounded-lg shadow-lg border border-slate-700">
        <div className="font-semibold">{stateData.length} states loaded</div>
        {Object.keys(stats).length > 0 && (
          <div className="text-xs text-slate-400 mt-1">
            {Object.entries(stats).map(([cat, count]) => (
              <div key={cat}>{cat}: {count}</div>
            ))}
          </div>
        )}
      </div>

      <MapContainer
        center={SUDAN_CENTER}
        zoom={6}
        style={{ height: '100%', width: '100%', background: '#1e293b' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {stateData.map((state, index) => {
          const color = getRiskColor(state.risk)
          
          return (
            <CircleMarker
              key={`${state.name}-${index}`}
              center={state.position as [number, number]}
              radius={getRiskRadius(state.incidents)}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.65,
                weight: 2,
                opacity: 0.85,
              }}
            >
              {/* Enhanced Tooltip with Risk Level */}
              <Tooltip 
                direction="top" 
                offset={[0, -10]} 
                opacity={0.95}
                className="custom-tooltip"
              >
                <div className="font-bold text-base mb-1">{state.name}</div>
                <div 
                  className="text-xs font-semibold px-2 py-0.5 rounded inline-block text-white"
                  style={{ backgroundColor: color }}
                >
                  {state.risk}
                </div>
                <div className="text-xs text-slate-700 mt-1">
                  {state.incidents} incidents
                </div>
              </Tooltip>
              
              {/* Detailed Popup */}
              <Popup maxWidth={300}>
                <div className="py-2 px-1">
                  <h3 className="font-bold text-lg mb-3 text-slate-900 border-b pb-2">{state.name}</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-slate-700">Risk Level:</span>
                      <span 
                        className="px-3 py-1 rounded-full text-white font-bold text-xs"
                        style={{ backgroundColor: color }}
                      >
                        {state.risk}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-semibold text-slate-700">Conflict Events:</span>
                      <span className="text-slate-900 font-medium">{state.incidents}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-semibold text-slate-700">Risk Score:</span>
                      <span className="text-slate-900 font-medium">{state.score.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
      </MapContainer>

      {/* Legend with actual distribution */}
      <div className="absolute bottom-6 right-6 z-[1000] bg-slate-900/95 text-white p-4 rounded-lg shadow-xl border border-slate-700">
        <h4 className="font-bold mb-3">Risk Levels</h4>
        <div className="space-y-2.5">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full flex-shrink-0" style={{ backgroundColor: '#dc2626' }}></div>
            <span className="text-sm font-medium">Very High {stats['VERY HIGH'] ? `(${stats['VERY HIGH']})` : ''}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full flex-shrink-0" style={{ backgroundColor: '#f97316' }}></div>
            <span className="text-sm font-medium">High {stats['HIGH'] ? `(${stats['HIGH']})` : ''}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full flex-shrink-0" style={{ backgroundColor: '#eab308' }}></div>
            <span className="text-sm font-medium">Moderate {stats['MODERATE'] ? `(${stats['MODERATE']})` : ''}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full flex-shrink-0" style={{ backgroundColor: '#22c55e' }}></div>
            <span className="text-sm font-medium">Low {stats['LOW'] ? `(${stats['LOW']})` : ''}</span>
          </div>
        </div>
        <div className="mt-4 pt-3 border-t border-slate-700 text-xs text-slate-400">
          Circle size = event count
        </div>
      </div>

      {/* Custom tooltip styles */}
      <style jsx global>{`
        .custom-tooltip {
          background: white !important;
          border: 2px solid #334155 !important;
          border-radius: 8px !important;
          padding: 8px 12px !important;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        .custom-tooltip::before {
          border-top-color: white !important;
        }
      `}</style>
    </div>
  )
}
