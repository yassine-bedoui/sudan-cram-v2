'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { normalizeRegionName } from '@/utils/regionNameMapping'

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

  const center = [15.5007, 32.5599]
  const zoom = 6

  useEffect(() => {
    const fetchGeoData = async () => {
      try {
        const res = await fetch('/data/sudan-states.geojson')
        const data = await res.json()
        setGeoData(data)
      } catch (err) {
        console.error('Failed to load GeoJSON:', err)
      }
    }

    fetchGeoData()
  }, [])

  useEffect(() => {
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

  // UPDATED: New color palette
  const getColor = (value: number) => {
    if (value === undefined || value === null || value === 0) return '#f3f4f6' // No data - light gray
    if (value >= 8) return '#ED4447'  // Critical (8-10)
    if (value >= 6) return '#F37420'  // Very High (6-8)
    if (value >= 4) return '#E7B412'  // High (4-6)
    if (value >= 2) return '#11182A'  // Medium (2-4)
    if (value >= 1) return '#394153'  // Low (1-2)
    return '#4A5464'                   // Very Low (0-1)
  }

  const style = (feature: any) => {
    const geoName = feature.properties.shapeName
    const normalizedName = normalizeRegionName(geoName)
    const riskValue = riskData?.[normalizedName] || 0

    return {
      fillColor: getColor(riskValue),
      weight: 2,
      opacity: 1,
      color: '#ffffff',
      fillOpacity: 0.8,
    }
  }

  const onEachFeature = (feature: any, layer: any) => {
    const geoName = feature.properties.shapeName
    const normalizedName = normalizeRegionName(geoName)
    const riskValue = riskData?.[normalizedName]?.toFixed(1) || 'N/A'

    layer.bindPopup(`
      <div style="font-family: Inter, sans-serif; padding: 8px;">
        <strong style="font-size: 12px; text-transform: uppercase;">${normalizedName}</strong><br/>
        <span style="color: #6b7280; font-size: 11px;">Risk Score:</span> 
        <strong style="color: #F37420; font-size: 14px;">${riskValue}</strong> 
        <span style="color: #9ca3af; font-size: 11px;">/ 10</span>
      </div>
    `)

    layer.on({
      mouseover: (e: any) => {
        e.target.setStyle({ weight: 3, color: '#F37420' })
      },
      mouseout: (e: any) => {
        e.target.setStyle({ weight: 2, color: '#ffffff' })
      },
    })
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
