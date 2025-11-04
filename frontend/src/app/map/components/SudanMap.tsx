'use client'

import React, { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { StateRiskData } from '../hooks/useMapData'

// Dynamically import Leaflet components (client-side only)
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
)
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
)
const GeoJSON = dynamic(
  () => import('react-leaflet').then((mod) => mod.GeoJSON),
  { ssr: false }
)
const Marker = dynamic(
  () => import('react-leaflet').then((mod) => mod.Marker),
  { ssr: false }
)
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
)

interface SudanMapProps {
  states: StateRiskData[]
}

// Sudan state coordinates (capitals)
const stateCoordinates: Record<string, [number, number]> = {
  'Khartoum': [15.5007, 32.5599],
  'North Darfur': [13.3162, 24.8802],
  'South Darfur': [11.3512, 24.9323],
  'West Darfur': [12.8533, 22.9217],
  'Central Darfur': [12.8533, 24.4700],
  'East Darfur': [11.7833, 27.0167],
  'Blue Nile': [11.4500, 34.3667],
  'White Nile': [13.1833, 32.7333],
  'North Kordofan': [13.1833, 30.2167],
  'South Kordofan': [11.2000, 29.4167],
  'West Kordofan': [11.1500, 27.9667],
  'Kassala': [15.4500, 36.4000],
  'Gedaref': [14.0333, 35.3833],
  'Sennar': [13.5667, 33.6000],
  'Red Sea': [18.4333, 38.2000],
  'River Nile': [17.7000, 33.9667],
  'Northern': [19.5667, 30.4167],
  'Gezira': [14.4000, 33.5000],
  'Abyei PCA': [9.6000, 28.4000]
}

// Get color based on risk score
const getRiskColor = (score: number): string => {
  if (score >= 9) return '#dc2626' // red-600
  if (score >= 7) return '#ea580c' // orange-600
  if (score >= 5) return '#ca8a04' // yellow-600
  if (score >= 3) return '#16a34a' // green-600
  return '#64748b' // slate-500
}

export function SudanMap({ states }: SudanMapProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="w-full h-[600px] bg-slate-800 rounded-lg flex items-center justify-center">
        <p className="text-slate-400">Loading map...</p>
      </div>
    )
  }

  return (
    <div className="w-full h-[600px] rounded-lg overflow-hidden border border-slate-700">
      <MapContainer
        center={[15.0, 30.0]}
        zoom={6}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        {/* State Markers */}
        {states.map((state) => {
          const coords = stateCoordinates[state.name]
          if (!coords) return null

          const color = getRiskColor(state.cp_score)

          // Create custom icon
          const iconHtml = `
            <div style="
              background-color: ${color};
              width: 30px;
              height: 30px;
              border-radius: 50%;
              border: 3px solid white;
              box-shadow: 0 2px 8px rgba(0,0,0,0.3);
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-weight: bold;
              font-size: 12px;
            ">
              ${state.cp_score}
            </div>
          `

          return (
            <Marker
              key={state.name}
              position={coords}
              icon={
                typeof window !== 'undefined' && window.L
                  ? new window.L.DivIcon({
                      html: iconHtml,
                      className: 'custom-marker',
                      iconSize: [30, 30],
                      iconAnchor: [15, 15]
                    })
                  : undefined
              }
            >
              <Popup>
                <div className="p-2 min-w-[200px]">
                  <h3 className="font-bold text-lg mb-2">{state.name}</h3>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Risk Score:</span>
                      <span className="font-semibold" style={{ color }}>
                        {state.cp_score} ({state.cp_category})
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Incidents:</span>
                      <span className="font-semibold">{state.incidents}</span>
                    </div>
                    {state.political_risk !== null && (
                      <div className="flex justify-between">
                        <span className="text-slate-600">Political Risk:</span>
                        <span className="font-semibold">{state.political_risk.toFixed(2)}</span>
                      </div>
                    )}
                    {state.climate_risk !== null && (
                      <div className="flex justify-between">
                        <span className="text-slate-600">Climate Risk:</span>
                        <span className="font-semibold">{state.climate_risk.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
    </div>
  )
}
