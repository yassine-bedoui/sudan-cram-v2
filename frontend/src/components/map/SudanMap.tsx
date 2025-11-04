'use client'

import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

interface SudanMapProps {
  backendAvailable: boolean
}

// Sudan center coordinates
const SUDAN_CENTER: [number, number] = [15.5007, 32.5599]

// Demo state data
const DEMO_STATES = [
  { name: 'Khartoum', position: [15.5007, 32.5599], risk: 'high', incidents: 245 },
  { name: 'North Darfur', position: [13.6167, 24.9], risk: 'high', incidents: 189 },
  { name: 'West Darfur', position: [12.8167, 22.9167], risk: 'high', incidents: 156 },
  { name: 'South Darfur', position: [11.5, 24.8833], risk: 'medium', incidents: 98 },
  { name: 'Gezira', position: [14.4, 33.5], risk: 'medium', incidents: 76 },
  { name: 'White Nile', position: [13.3, 32.7], risk: 'low', incidents: 32 },
  { name: 'Blue Nile', position: [11.9, 34.4], risk: 'low', incidents: 28 },
  { name: 'Kassala', position: [15.4667, 36.4], risk: 'medium', incidents: 54 },
  { name: 'Red Sea', position: [18.4333, 37.2167], risk: 'low', incidents: 19 },
  { name: 'River Nile', position: [17.7, 33.9], risk: 'low', incidents: 15 },
]

const getRiskColor = (risk: string) => {
  switch (risk) {
    case 'high': return '#ef4444'
    case 'medium': return '#f59e0b'
    case 'low': return '#10b981'
    default: return '#6b7280'
  }
}

const getRiskRadius = (incidents: number) => {
  return Math.sqrt(incidents) * 3
}

export default function SudanMap({ backendAvailable }: SudanMapProps) {
  const [stateData, setStateData] = useState(DEMO_STATES)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      if (!backendAvailable) {
        // Use demo data
        setStateData(DEMO_STATES)
        setLoading(false)
        return
      }

      try {
        const response = await fetch('http://localhost:8000/api/conflict-proneness')
        const data = await response.json()
        
        if (data && data.data) {
          // Transform API data to map format
          const transformedData = data.data.map((state: any) => ({
            name: state.state,
            position: [state.latitude || 15, state.longitude || 32], // Use actual coords
            risk: state.risk_level?.toLowerCase() || 'low',
            incidents: state.incidents || 0
          }))
          setStateData(transformedData)
        }
      } catch (error) {
        console.error('Failed to fetch map data:', error)
        setStateData(DEMO_STATES)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [backendAvailable])

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

  return (
    <div className="h-full w-full relative">
      {!backendAvailable && (
        <div className="absolute top-4 left-4 z-[1000] bg-blue-900/90 text-white px-4 py-2 rounded-lg shadow-lg">
          <span className="font-semibold">Demo Mode</span> - Using sample data
        </div>
      )}

      <MapContainer
        center={SUDAN_CENTER}
        zoom={6}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {stateData.map((state, index) => (
          <CircleMarker
            key={index}
            center={state.position as [number, number]}
            radius={getRiskRadius(state.incidents)}
            pathOptions={{
              color: getRiskColor(state.risk),
              fillColor: getRiskColor(state.risk),
              fillOpacity: 0.6,
              weight: 2,
            }}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-bold text-lg mb-1">{state.name}</h3>
                <div className="space-y-1 text-sm">
                  <p><span className="font-semibold">Risk Level:</span> 
                    <span className={`ml-2 px-2 py-0.5 rounded ${
                      state.risk === 'high' ? 'bg-red-100 text-red-800' :
                      state.risk === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {state.risk.toUpperCase()}
                    </span>
                  </p>
                  <p><span className="font-semibold">Incidents:</span> {state.incidents}</p>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Legend */}
      <div className="absolute bottom-6 right-6 z-[1000] bg-slate-900/95 text-white p-4 rounded-lg shadow-xl border border-slate-700">
        <h4 className="font-bold mb-3">Risk Levels</h4>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-sm">High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span className="text-sm">Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-sm">Low Risk</span>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-slate-700 text-xs text-slate-400">
          Circle size = incident count
        </div>
      </div>
    </div>
  )
}
