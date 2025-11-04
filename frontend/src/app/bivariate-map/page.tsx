'use client'

import React, { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { IndicatorSelector, type IndicatorMode } from '@/components/map/IndicatorSelector'
import { BivariateLegend } from '@/components/map/BivariateLegend'
import { RegionDetailPanel } from '@/components/map/RegionDetailPanel'
import { getBivariateColor, getIndicatorColor } from '@/lib/bivariate-colors'

const MapContainer = dynamic(() => import('react-leaflet').then((mod) => mod.MapContainer), { ssr: false })
const TileLayer = dynamic(() => import('react-leaflet').then((mod) => mod.TileLayer), { ssr: false })
const CircleMarker = dynamic(() => import('react-leaflet').then((mod) => mod.CircleMarker), { ssr: false })
const Tooltip = dynamic(() => import('react-leaflet').then((mod) => mod.Tooltip), { ssr: false })

interface RegionData {
  name: string
  cp_score: number
  climate_risk: number
  combined_risk: number
  incidents: number
  coordinates: [number, number]
}

export default function BivariateMapPage() {
  const [mode, setMode] = useState<IndicatorMode>('bivariate')
  const [regions, setRegions] = useState<RegionData[]>([])
  const [selectedRegion, setSelectedRegion] = useState<RegionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const endpoint =
          mode === 'bivariate'
            ? 'http://localhost:8000/api/indicators/bivariate'
            : `http://localhost:8000/api/indicators/data?indicator=${mode}`

        const response = await fetch(endpoint)
        const data = await response.json()

        // Transform data
        const transformed = data.data.map((item: any) => ({
          name: item.ADM1_NAME,
          cp_score: item.cp_score || 0,
          climate_risk: item.climate_risk || 0,
          combined_risk: item.combined_risk || 0,
          incidents: item.incidents || 0,
          coordinates: getStateCoordinates(item.ADM1_NAME),
        }))

        setRegions(transformed)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [mode])

  const getColor = (region: RegionData): string => {
    if (mode === 'bivariate') {
      return getBivariateColor(region.cp_score, region.climate_risk)
    }
    const score =
      mode === 'conflict_proneness'
        ? region.cp_score
        : mode === 'climate_risk'
        ? region.climate_risk
        : region.combined_risk
    return getIndicatorColor(score)
  }

  if (!mounted) {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Loading map...</div>
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">🗺️ Interactive Bivariate Map</h1>
          <p className="text-lg text-slate-400">Explore conflict and climate risk across Sudan</p>
        </div>

        {/* Indicator Selector */}
        <div className="mb-4">
          <IndicatorSelector selected={mode} onChange={setMode} />
        </div>

        {/* Map Container */}
        <div className="relative">
          <div className="h-[700px] bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center h-full text-white">Loading data...</div>
            ) : (
              <MapContainer center={[15.0, 30.0]} zoom={6} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  attribution='&copy; OpenStreetMap contributors &copy; CARTO'
                />

                {regions.map((region) => (
                  <CircleMarker
                    key={region.name}
                    center={region.coordinates}
                    radius={12}
                    fillColor={getColor(region)}
                    color="#ffffff"
                    weight={2}
                    fillOpacity={0.8}
                    eventHandlers={{
                      click: () => setSelectedRegion(region),
                    }}
                  >
                    <Tooltip>
                      <div className="text-sm">
                        <div className="font-bold">{region.name}</div>
                        <div>CP: {region.cp_score.toFixed(2)}</div>
                        <div>Climate: {region.climate_risk.toFixed(2)}</div>
                      </div>
                    </Tooltip>
                  </CircleMarker>
                ))}
              </MapContainer>
            )}
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 z-10">
            {mode === 'bivariate' && <BivariateLegend />}
          </div>

          {/* Region Detail Panel */}
          <RegionDetailPanel region={selectedRegion} onClose={() => setSelectedRegion(null)} />
        </div>
      </div>
    </div>
  )
}

// State coordinates helper
function getStateCoordinates(name: string): [number, number] {
  const coords: Record<string, [number, number]> = {
    Khartoum: [15.5007, 32.5599],
    'North Darfur': [13.3162, 24.8802],
    'South Darfur': [11.3512, 24.9323],
    'West Darfur': [12.8533, 22.9217],
    'Central Darfur': [12.8533, 24.47],
    'East Darfur': [11.7833, 27.0167],
    'Blue Nile': [11.45, 34.3667],
    'White Nile': [13.1833, 32.7333],
    'North Kordofan': [13.1833, 30.2167],
    'South Kordofan': [11.2, 29.4167],
    'West Kordofan': [11.15, 27.9667],
    Kassala: [15.45, 36.4],
    Gedaref: [14.0333, 35.3833],
    Sennar: [13.5667, 33.6],
    'Red Sea': [18.4333, 38.2],
    'River Nile': [17.7, 33.9667],
    Northern: [19.5667, 30.4167],
    Gezira: [14.4, 33.5],
    'Abyei PCA': [9.6, 28.4],
  }
  return coords[name] || [15.0, 30.0]
}
