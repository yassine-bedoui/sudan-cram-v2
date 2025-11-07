'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'

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

export default function InteractiveMap({ indicator }: { indicator: string }) {
  const [geoData, setGeoData] = useState(null)
  const [riskData, setRiskData] = useState<any>(null)

  // Sudan center coordinates
  const center = [15.5007, 32.5599]
  const zoom = 6

  useEffect(() => {
    // Fetch Sudan GeoJSON boundaries
    const fetchGeoData = async () => {
      try {
        const res = await fetch('/data/sudan-states.geojson') // FIXED: Changed filename
        const data = await res.json()
        setGeoData(data)
      } catch (err) {
        console.error('Failed to load GeoJSON:', err)
      }
    }

    fetchGeoData()
  }, [])

  useEffect(() => {
    // Fetch risk data based on selected indicator
    const fetchRiskData = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/map-data?indicator=${indicator}`
        )
        const data = await res.json()
        setRiskData(data)
      } catch (err) {
        console.error('Failed to fetch risk data:', err)
      }
    }

    fetchRiskData()
  }, [indicator])

  const getColor = (value: number) => {
    if (!value) return '#cccccc'
    if (value > 7) return '#dc2626' // Severe - Red
    if (value > 5) return '#f97316' // High - Orange
    if (value > 3) return '#fbbf24' // Medium - Yellow
    return '#6b7280' // Low - Gray
  }

  const style = (feature: any) => {
    // Try multiple property names (GeoJSON files vary)
    const regionName = feature.properties.shapeName || feature.properties.name || feature.properties.NAME_1
    const riskValue = riskData?.[regionName] || 0

    return {
      fillColor: getColor(riskValue),
      weight: 2,
      opacity: 1,
      color: '#ffffff',
      fillOpacity: 0.7,
    }
  }

  const onEachFeature = (feature: any, layer: any) => {
    const regionName = feature.properties.shapeName || feature.properties.name || feature.properties.NAME_1
    const riskValue = riskData?.[regionName] || 'N/A'

    layer.bindPopup(`
      <div style="font-family: monospace;">
        <strong>${regionName}</strong><br/>
        Risk Score: <strong>${riskValue}</strong>
      </div>
    `)
  }

  return (
    <section className="flex-1 h-full">
      {typeof window !== 'undefined' && geoData && (
        <MapContainer
          center={center as [number, number]}
          zoom={zoom}
          style={{ height: '100%', width: '100%' }}
          className="border border-gray-300"
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />

          {geoData && (
            <GeoJSON
              key={indicator}
              data={geoData}
              style={style}
              onEachFeature={onEachFeature}
            />
          )}
        </MapContainer>
      )}
    </section>
  )
}
