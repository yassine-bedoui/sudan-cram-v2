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

  const getColor = (value: number) => {
    if (value === undefined || value === null || value === 0) return '#f3f4f6'
    if (value >= 8) return '#ED4447'
    if (value >= 6) return '#F37420'
    if (value >= 4) return '#E7B412'
    if (value >= 2) return '#11182A'
    if (value >= 1) return '#394153'
    return '#4A5464'
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

    // ONLY Tooltip (shows on hover)
    layer.bindTooltip(
      `<div style="font-family: Inter, sans-serif; padding: 4px; text-align: center;">
        <strong style="font-size: 11px; text-transform: uppercase; display: block; margin-bottom: 4px;">${normalizedName}</strong>
        <span style="font-size: 16px; font-weight: 700; color: #F37420;">${riskValue}</span>
        <span style="font-size: 10px; color: #9ca3af;"> / 10</span>
      </div>`,
      {
        permanent: false,
        direction: 'top',
        className: 'custom-tooltip',
        opacity: 0.95
      }
    )

    // REMOVED: bindPopup() - No click popup anymore

    // Hover effects
    layer.on({
      mouseover: (e: any) => {
        e.target.setStyle({ 
          weight: 3, 
          color: '#F37420',
          fillOpacity: 1
        })
      },
      mouseout: (e: any) => {
        e.target.setStyle({ 
          weight: 2, 
          color: '#ffffff',
          fillOpacity: 0.8
        })
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
