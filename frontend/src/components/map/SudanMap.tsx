'use client'

import React, { useEffect, useState, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

interface SudanMapProps {
  backendAvailable: boolean
  indicator: string
}

interface RegionData {
  name: string
  riskLevel: string
  riskScore: number
  incidents: number
  fatalities: number
}

const SUDAN_CENTER: [number, number] = [15.5007, 32.5599]

// Helper functions
const getRegionName = (properties: any): string => {
  return properties.shapeName || properties.ADM1_EN || properties.name || 'Unknown'
}

const getRiskColor = (level: string): string => {
  const normalized = level.toString().toUpperCase().trim()
  const colorMap: Record<string, string> = {
    'SEVERE': '#dc2626',
    'HIGH': '#f97316',
    'MEDIUM': '#eab308',
    'LOW': '#22c55e',
  }
  return colorMap[normalized] || '#6b7280'
}

// Normalize region names for backend matching
const normalizeRegionName = (name: string): string => {
  const nameMap: Record<string, string> = {
    'Abyei PCA': 'Abyei',
    'Gezira': 'Al Jazirah'
  }
  return nameMap[name] || name
}

export default function SudanMap({ backendAvailable, indicator }: SudanMapProps) {
  const mapRef = useRef<L.Map | null>(null)
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const geoJsonLayerRef = useRef<L.GeoJSON | null>(null)
  
  const [regionData, setRegionData] = useState<Record<string, RegionData>>({})
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Record<string, number>>({})
  const [error, setError] = useState<string | null>(null)
  const [mapReady, setMapReady] = useState(false)

  // Fetch backend data
  useEffect(() => {
    const fetchData = async () => {
      console.log('🔵 [DATA FETCH] Starting...')
      console.log('🔵 Backend available:', backendAvailable)
      
      if (!backendAvailable) {
        console.log('⚠️ [DATA FETCH] Backend unavailable, skipping')
        setLoading(false)
        return
      }

      try {
        console.log('🔵 [DATA FETCH] Fetching from http://localhost:8000/api/conflict-proneness')
        const response = await fetch('http://localhost:8000/api/conflict-proneness')
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const data = await response.json()
        console.log('✅ [DATA FETCH] Success! Received data:', data)

        if (data && data.regions) {
          const categoryCount: Record<string, number> = {}
          const regionMap: Record<string, RegionData> = {}

          data.regions.forEach((region: any) => {
            const stateName = region.region
            const riskLevel = (region.level || 'UNKNOWN').toString().toUpperCase().trim()
            const events = parseInt(region.events || 0)
            const fatalities = parseInt(region.fatalities || 0)
            const riskScore = parseFloat(region.risk_score || 0)

            categoryCount[riskLevel] = (categoryCount[riskLevel] || 0) + 1
            regionMap[stateName] = {
              name: stateName,
              riskLevel,
              riskScore,
              incidents: events,
              fatalities
            }
          })

          console.log('✅ [DATA FETCH] Processed regions:', Object.keys(regionMap))
          console.log('✅ [DATA FETCH] Stats:', categoryCount)
          
          setRegionData(regionMap)
          setStats(categoryCount)
        } else {
          console.error('❌ [DATA FETCH] Invalid data structure:', data)
          setError('Invalid backend response')
        }
      } catch (err: any) {
        console.error('❌ [DATA FETCH] Error:', err)
        setError(`Backend error: ${err.message}`)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [backendAvailable, indicator])

  // Initialize map
  useEffect(() => {
    const timer = setTimeout(() => {
      console.log('🗺️ [MAP INIT] Starting...')
      
      if (!mapContainerRef.current) {
        console.error('❌ [MAP INIT] Container ref is null')
        setError('Map container failed to load')
        return
      }
      
      if (mapRef.current) {
        console.log('⚠️ [MAP INIT] Map already exists')
        return
      }

      console.log('🗺️ [MAP INIT] Creating Leaflet map...')
      const map = L.map(mapContainerRef.current, {
        center: SUDAN_CENTER,
        zoom: 6,
        zoomControl: true,
        scrollWheelZoom: true,
      })

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CARTO',
        subdomains: 'abcd',
        maxZoom: 19
      }).addTo(map)

      mapRef.current = map
      setMapReady(true)
      console.log('✅ [MAP INIT] Map created successfully')
    }, 100)

    return () => {
      clearTimeout(timer)
      if (mapRef.current) {
        console.log('🗺️ [MAP CLEANUP] Removing map')
        mapRef.current.remove()
        mapRef.current = null
        setMapReady(false)
      }
    }
  }, [])

  // Load GeoJSON (always, even without backend data)
  useEffect(() => {
    console.log('📍 [GEOJSON] Loading trigger...')
    console.log('📍 Map ready:', mapReady)
    console.log('📍 GeoJSON layer exists:', !!geoJsonLayerRef.current)
    
    if (!mapReady || geoJsonLayerRef.current) {
      console.log('⚠️ [GEOJSON] Skipping: map not ready or layer already exists')
      return
    }

    console.log('📍 [GEOJSON] Fetching /data/sudan-states.geojson...')
    
    fetch('/data/sudan-states.geojson')
      .then(res => {
        console.log('📍 [GEOJSON] Response status:', res.status, res.statusText)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(geojsonData => {
        console.log('✅ [GEOJSON] Loaded successfully')
        console.log('📍 [GEOJSON] Features count:', geojsonData.features?.length)
        console.log('📍 [GEOJSON] Backend data keys:', Object.keys(regionData))
        
        const geoJsonLayer = L.geoJSON(geojsonData, {
          style: (feature) => {
            const geoJsonName = getRegionName(feature.properties)
            const normalizedName = normalizeRegionName(geoJsonName)
            const regionInfo = regionData[normalizedName]
            const riskLevel = regionInfo?.riskLevel || 'UNKNOWN'

            const style = {
              fillColor: getRiskColor(riskLevel),
              weight: 2,
              opacity: 1,
              color: '#000000',
              fillOpacity: regionInfo ? 0.8 : 0.3
            }

            console.log(`🎨 [STYLE] ${geoJsonName} → ${normalizedName} → ${riskLevel} → ${style.fillColor}`)
            return style
          },
          onEachFeature: (feature, layer) => {
            const geoJsonName = getRegionName(feature.properties)
            const normalizedName = normalizeRegionName(geoJsonName)
            const regionInfo = regionData[normalizedName]

            const popupContent = `
              <div style="font-family: 'Courier New', monospace; min-width: 220px;">
                <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 700; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 6px;">
                  ${geoJsonName}
                </h3>
                ${regionInfo ? `
                  <div style="font-size: 12px;">
                    <div style="margin: 6px 0; padding: 4px; background: ${getRiskColor(regionInfo.riskLevel)}22;">
                      <strong>RISK:</strong> <span style="color: ${getRiskColor(regionInfo.riskLevel)};">${regionInfo.riskLevel}</span>
                    </div>
                    <div style="margin: 6px 0; padding: 4px;">
                      <strong>SCORE:</strong> ${regionInfo.riskScore.toFixed(1)}/10
                    </div>
                    <div style="margin: 6px 0; padding: 4px;">
                      <strong>EVENTS:</strong> ${regionInfo.incidents}
                    </div>
                    <div style="margin: 6px 0; padding: 4px;">
                      <strong>DEATHS:</strong> ${regionInfo.fatalities}
                    </div>
                  </div>
                ` : '<div style="color: #999; font-size: 12px;">NO DATA - Check backend</div>'}
              </div>
            `

            ;(layer as L.Path).bindPopup(popupContent, { className: 'brutalist-popup' })

            ;(layer as L.Path).on({
              mouseover: (e) => {
                const target = e.target as L.Path
                target.setStyle({ weight: 3, fillOpacity: 1 })
                target.bringToFront()
              },
              mouseout: (e) => {
                const target = e.target as L.Path
                const regionInfo = regionData[normalizedName]
                target.setStyle({
                  fillColor: getRiskColor(regionInfo?.riskLevel || 'UNKNOWN'),
                  weight: 2,
                  fillOpacity: regionInfo ? 0.8 : 0.3
                })
              },
              click: () => (layer as L.Path).openPopup()
            })
          }
        }).addTo(mapRef.current!)

        geoJsonLayerRef.current = geoJsonLayer
        console.log('✅ [GEOJSON] Layer added to map successfully')
      })
      .catch(err => {
        console.error('❌ [GEOJSON] Error:', err)
        setError(`GeoJSON failed: ${err.message}`)
      })
  }, [mapReady])

  // Update colors when backend data arrives
  useEffect(() => {
    console.log('🎨 [COLOR UPDATE] Trigger...')
    console.log('🎨 GeoJSON layer exists:', !!geoJsonLayerRef.current)
    console.log('🎨 Backend data count:', Object.keys(regionData).length)
    
    if (!geoJsonLayerRef.current || Object.keys(regionData).length === 0) {
      console.log('⚠️ [COLOR UPDATE] Skipping: no layer or no data')
      return
    }

    console.log('🎨 [COLOR UPDATE] Updating region colors...')
    let matchedCount = 0
    let unmatchedRegions: string[] = []

    geoJsonLayerRef.current.eachLayer((layer: any) => {
      if (layer.feature) {
        const geoJsonName = getRegionName(layer.feature.properties)
        const normalizedName = normalizeRegionName(geoJsonName)
        const regionInfo = regionData[normalizedName]
        
        if (regionInfo) {
          matchedCount++
          console.log(`✅ [COLOR UPDATE] ${geoJsonName} → ${normalizedName} → ${regionInfo.riskLevel}`)
        } else {
          unmatchedRegions.push(geoJsonName)
          console.log(`❌ [COLOR UPDATE] No data for: ${geoJsonName} (normalized: ${normalizedName})`)
        }
        
        layer.setStyle({
          fillColor: getRiskColor(regionInfo?.riskLevel || 'UNKNOWN'),
          weight: 2,
          opacity: 1,
          color: '#000000',
          fillOpacity: regionInfo ? 0.8 : 0.3
        })
      }
    })

    console.log(`✅ [COLOR UPDATE] Complete! Matched: ${matchedCount}, Unmatched: ${unmatchedRegions.length}`)
    if (unmatchedRegions.length > 0) {
      console.log('❌ [COLOR UPDATE] Unmatched regions:', unmatchedRegions)
    }
  }, [regionData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-900">
        <div className="text-white font-mono">
          <div className="text-4xl mb-4">🗺️</div>
          <div className="text-xl font-bold">LOADING...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-900">
        <div className="text-red-400 font-mono max-w-md text-center">
          <div className="text-xl font-bold mb-2">ERROR</div>
          <div className="text-sm mb-4">{error}</div>
          <div className="text-xs text-gray-400">Check browser console (F12) for details</div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-full">
      <div ref={mapContainerRef} className="absolute inset-0" />

      <div className="absolute top-4 left-4 z-[1000] bg-white border-2 border-black px-4 py-2 shadow-[4px_4px_0_0_#000] font-mono">
        <div className="font-bold text-sm">{Object.keys(regionData).length} REGIONS</div>
        {Object.keys(stats).length > 0 && (
          <div className="text-xs mt-2 space-y-1">
            {Object.entries(stats).map(([cat, count]) => (
              <div key={cat} className="flex items-center gap-2">
                <div className="w-3 h-3 border border-black" style={{ backgroundColor: getRiskColor(cat) }} />
                <span>{cat}: {count}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="absolute bottom-6 right-6 z-[1000] bg-white border-2 border-black p-4 shadow-[4px_4px_0_0_#000] font-mono">
        <h4 className="font-bold text-sm mb-3 uppercase border-b-2 border-black pb-2">RISK LEVELS</h4>
        <div className="space-y-2.5">
          {['SEVERE', 'HIGH', 'MEDIUM', 'LOW'].map(level => (
            <div key={level} className="flex items-center gap-3">
              <div className="w-6 h-6 border-2 border-black" style={{ backgroundColor: getRiskColor(level) }}></div>
              <span className="text-xs font-bold uppercase">{level} {stats[level] ? `(${stats[level]})` : ''}</span>
            </div>
          ))}
        </div>
      </div>

      {!backendAvailable && (
        <div className="absolute top-4 right-4 z-[1000] bg-yellow-400 border-2 border-black p-3 font-mono text-xs max-w-xs shadow-[4px_4px_0_0_#000]">
          <div className="font-bold mb-1">⚠ BACKEND OFFLINE</div>
          <div>Start backend on port 8000</div>
        </div>
      )}
    </div>
  )
}
