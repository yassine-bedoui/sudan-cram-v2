'use client'

import React, { useEffect, useState, useRef, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

interface SudanMapProps {
  backendAvailable: boolean
  indicator: string
}

interface RegionData {
  name: string
  proneness_level: string
  proneness_score: number
  incidents: number
  fatalities: number
  climate_risk_level: string
  climate_risk_score: number
}

type RiskIndicator = 'conflict-risk' | 'climate-risk' | 'conflict-proneness' | 'combined-risk'

const SUDAN_CENTER: [number, number] = [15.5007, 32.5599]
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

const getRegionName = (properties: any): string => {
  return properties.shapeName || properties.ADM1_EN || properties.name || 'Unknown'
}

// ✅ FIXED: Proper color mapping with type safety
const getRiskColor = (level: string | undefined, riskScore?: number): string => {
  if (!level && riskScore === undefined) return '#6b7280'

  // For combined risk, use score-based coloring
  if (riskScore !== undefined) {
    if (riskScore >= 7.5) return '#8B0000'
    if (riskScore >= 6) return '#DC143C'
    if (riskScore >= 4.5) return '#FF6347'
    if (riskScore >= 3) return '#FFA500'
    if (riskScore >= 1.5) return '#FFD700'
    return '#00A86B'
  }

  if (!level) return '#6b7280'

  const normalized = level.toString().toUpperCase().trim()

  const colorMap: Record<string, string> = {
    'EXTREME': '#8B0000',
    'VERY HIGH': '#DC143C',
    'VERY_HIGH': '#DC143C',
    'HIGH': '#FF6347',
    'SEVERE': '#FF4500',
    'ALERT': '#FFA500',
    'MODERATE': '#FFD700',
    'WARNING': '#FFFF00',
    'WATCH': '#90EE90',
    'LOW': '#00A86B',
    'NORMAL': '#90EE90',
  }
  return colorMap[normalized] || '#6b7280'
}

// ✅ FIXED: Corrected state name normalization
const normalizeRegionName = (name: string): string => {
  const nameMap: Record<string, string> = {
    'Abyei PCA': 'Abyei',
    'Gezira': 'Al Jazirah',
    'Al Jazirah': 'Al Jazirah',
  }
  return nameMap[name] || name
}

export default function SudanMap({ backendAvailable, indicator: initialIndicator }: SudanMapProps) {
  const mapRef = useRef<L.Map | null>(null)
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const geoJsonLayerRef = useRef<L.GeoJSON | null>(null)

  const [regionData, setRegionData] = useState<Record<string, RegionData>>({})
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Record<string, number>>({})
  const [error, setError] = useState<string | null>(null)
  const [mapReady, setMapReady] = useState(false)
  const [selectedIndicator, setSelectedIndicator] = useState<RiskIndicator>('conflict-proneness')

  // ✅ Fetch backend data
  useEffect(() => {
    const fetchData = async () => {
      console.log('🔵 [DATA FETCH] Starting...')
      console.log('🔵 Backend available:', backendAvailable)
      console.log('🔵 Backend URL:', BACKEND_URL)

      if (!backendAvailable) {
        console.log('⚠️ [DATA FETCH] Backend unavailable, skipping')
        setLoading(false)
        return
      }

      try {
        console.log(`🔵 [DATA FETCH] Fetching from ${BACKEND_URL}/api/conflict-proneness`)
        const response = await fetch(`${BACKEND_URL}/api/conflict-proneness`)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()
        console.log('✅ [DATA FETCH] Success! Received data:', data)

        // ✅ Handle dict format
        let regionsArray = Array.isArray(data) ? data : Object.values(data)

        if (!regionsArray || regionsArray.length === 0) {
          throw new Error('No region data received')
        }

        const regionMap: Record<string, RegionData> = {}

        regionsArray.forEach((region: any) => {
          const stateName = region.region || region.name

          regionMap[stateName] = {
            name: stateName,
            proneness_level: (region.proneness_level || 'UNKNOWN').toString().toUpperCase().trim(),
            proneness_score: parseFloat(region.conflict_proneness || region.proneness_score || 0),
            climate_risk_level: (region.climate_risk_level || region.cdi_category || 'UNKNOWN').toString().toUpperCase().trim(),
            climate_risk_score: parseFloat(region.climate_risk_score || 0),
            incidents: parseInt(region.high_risk_events || region.incidents || 0),
            fatalities: parseInt(region.fatalities || 0),
          }
        })

        console.log('✅ [DATA FETCH] Processed regions:', Object.keys(regionMap).length)
        setRegionData(regionMap)
      } catch (err: any) {
        console.error('❌ [DATA FETCH] Error:', err)
        setError(`Backend error: ${err.message}`)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [backendAvailable, initialIndicator])

  // ✅ Initialize map
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

  // ✅ Load GeoJSON
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
        console.log('📍 [GEOJSON] Backend data keys:', Object.keys(regionData).length)

        const geoJsonLayer = L.geoJSON(geojsonData, {
          style: (feature) => {
            if (!feature || !feature.properties) {
              return {
                fillColor: '#6b7280',
                weight: 2,
                opacity: 1,
                color: '#000000',
                fillOpacity: 0.3
              }
            }

            const geoJsonName = getRegionName(feature.properties)
            const normalizedName = normalizeRegionName(geoJsonName)
            const regionInfo = regionData[normalizedName]

            let fillColor = '#6b7280'
            if (regionInfo) {
              if (selectedIndicator === 'conflict-risk' || selectedIndicator === 'conflict-proneness') {
                fillColor = getRiskColor(regionInfo.proneness_level)
              } else if (selectedIndicator === 'climate-risk') {
                fillColor = getRiskColor(regionInfo.climate_risk_level)
              } else if (selectedIndicator === 'combined-risk') {
                const avgScore = (parseFloat(String(regionInfo.proneness_score)) + parseFloat(String(regionInfo.climate_risk_score))) / 2
                fillColor = getRiskColor(undefined, avgScore)
              }
            }

            const style = {
              fillColor,
              weight: 2,
              opacity: 1,
              color: '#000000',
              fillOpacity: regionInfo ? 0.8 : 0.3
            }

            console.log(`🎨 [STYLE] ${geoJsonName} → ${normalizedName} → ${fillColor}`)
            return style
          },
          onEachFeature: (feature, layer) => {
            const geoJsonName = getRegionName(feature.properties)
            const normalizedName = normalizeRegionName(geoJsonName)
            const regionInfo = regionData[normalizedName]

            const popupContent = getPopupContent(geoJsonName, regionInfo, selectedIndicator)

            ;(layer as L.Path).bindPopup(popupContent, { className: 'brutalist-popup' })

            ;(layer as L.Path).on({
              mouseover: (e) => {
                const target = e.target as L.Path
                target.setStyle({ weight: 3, fillOpacity: 1 })
                target.bringToFront()
              },
              mouseout: (e) => {
                const target = e.target as L.Path
                let fillColor = '#6b7280'
                if (regionInfo) {
                  if (selectedIndicator === 'conflict-risk' || selectedIndicator === 'conflict-proneness') {
                    fillColor = getRiskColor(regionInfo.proneness_level)
                  } else if (selectedIndicator === 'climate-risk') {
                    fillColor = getRiskColor(regionInfo.climate_risk_level)
                  } else if (selectedIndicator === 'combined-risk') {
                    const avgScore = (parseFloat(String(regionInfo.proneness_score)) + parseFloat(String(regionInfo.climate_risk_score))) / 2
                    fillColor = getRiskColor(undefined, avgScore)
                  }
                }
                target.setStyle({
                  fillColor,
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
  }, [mapReady, regionData, selectedIndicator])

  // ✅ Calculate stats based on indicator
  const calculateStats = useCallback(() => {
    const statsMap: Record<string, number> = {}
    Object.values(regionData).forEach(region => {
      let level = ''
      if (selectedIndicator === 'conflict-risk' || selectedIndicator === 'conflict-proneness') {
        level = region.proneness_level
      } else if (selectedIndicator === 'climate-risk') {
        level = region.climate_risk_level
      } else if (selectedIndicator === 'combined-risk') {
        const score = (parseFloat(String(region.proneness_score)) + parseFloat(String(region.climate_risk_score))) / 2
        if (score >= 7.5) level = 'EXTREME'
        else if (score >= 6) level = 'VERY HIGH'
        else if (score >= 4.5) level = 'HIGH'
        else if (score >= 3) level = 'MODERATE'
        else level = 'LOW'
      }
      statsMap[level] = (statsMap[level] || 0) + 1
    })
    return statsMap
  }, [selectedIndicator, regionData])

  // ✅ Update stats when indicator or data changes
  useEffect(() => {
    setStats(calculateStats())
  }, [calculateStats])

  // ✅ Update colors when indicator changes - COMPLETE VERSION
  useEffect(() => {
    console.log('🎨 [COLOR UPDATE] Trigger...')
    console.log('🎨 GeoJSON layer exists:', !!geoJsonLayerRef.current)
    console.log('🎨 Backend data count:', Object.keys(regionData).length)
    console.log('🎨 Selected indicator:', selectedIndicator)

    if (!geoJsonLayerRef.current || Object.keys(regionData).length === 0) {
      console.log('⚠️ [COLOR UPDATE] Skipping: no layer or no data')
      return
    }

    console.log(`🎨 [COLOR UPDATE] Switching to ${selectedIndicator}`)

    geoJsonLayerRef.current.eachLayer((layer: any) => {
      if (layer.feature) {
        const geoJsonName = getRegionName(layer.feature.properties)
        const normalizedName = normalizeRegionName(geoJsonName)
        const regionInfo = regionData[normalizedName]

        let fillColor = '#6b7280'

        // ✅ FIXED: Proper handling of all indicators including combined-risk
        if (regionInfo) {
          if (selectedIndicator === 'conflict-risk' || selectedIndicator === 'conflict-proneness') {
            fillColor = getRiskColor(regionInfo.proneness_level)
            console.log(`  📌 ${geoJsonName}: ${regionInfo.proneness_level} → ${fillColor}`)
          } else if (selectedIndicator === 'climate-risk') {
            fillColor = getRiskColor(regionInfo.climate_risk_level)
            console.log(`  📌 ${geoJsonName}: ${regionInfo.climate_risk_level} → ${fillColor}`)
          } else if (selectedIndicator === 'combined-risk') {
            // ✅ FIXED: Calculate average score and get color
            const avgScore = (parseFloat(String(regionInfo.proneness_score)) + parseFloat(String(regionInfo.climate_risk_score))) / 2
            fillColor = getRiskColor(undefined, avgScore)
            console.log(`  📌 ${geoJsonName}: combined(${regionInfo.proneness_score}+${regionInfo.climate_risk_score})/2 = ${avgScore} → ${fillColor}`)
          }
        }

        layer.setStyle({
          fillColor,
          weight: 2,
          opacity: 1,
          color: '#000000',
          fillOpacity: regionInfo ? 0.8 : 0.3
        })

        ;(layer as L.Path).setPopupContent(getPopupContent(geoJsonName, regionInfo, selectedIndicator))
      }
    })

    console.log(`✅ [COLOR UPDATE] Complete!`)
  }, [selectedIndicator, regionData])

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

      {/* ✅ REGION COUNT (Top-Left) */}
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

      {/* ✅ INDICATOR SELECTOR (Top-Right) */}
      <div className="absolute top-4 right-4 z-[1000] bg-white border-2 border-black p-4 shadow-[4px_4px_0_0_#000] font-mono">
        <div className="font-bold text-sm mb-3 uppercase border-b-2 border-black pb-2">SELECT INDICATOR</div>
        <select
          value={selectedIndicator}
          onChange={(e) => setSelectedIndicator(e.target.value as RiskIndicator)}
          className="w-full px-3 py-2 border-2 border-black rounded text-sm font-bold focus:outline-none"
        >
          <option value="conflict-proneness">⚠️ CONFLICT PRONENESS</option>
          <option value="conflict-risk">🔴 CONFLICT RISK</option>
          <option value="climate-risk">🟡 CLIMATE RISK</option>
          <option value="combined-risk">🟣 COMBINED RISK</option>
        </select>
      </div>

      {/* ✅ RISK LEVELS LEGEND (Bottom-Right) */}
      <div className="absolute bottom-6 right-6 z-[1000] bg-white border-2 border-black p-4 shadow-[4px_4px_0_0_#000] font-mono">
        <h4 className="font-bold text-sm mb-3 uppercase border-b-2 border-black pb-2">RISK LEVELS</h4>
        <div className="space-y-2.5">
          {['EXTREME', 'VERY HIGH', 'HIGH', 'MODERATE', 'LOW'].map(level => (
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

// ✅ Helper function: Generate popup content
function getPopupContent(
  regionName: string,
  regionInfo: RegionData | undefined,
  indicator: RiskIndicator
): string {
  if (!regionInfo) {
    return `<div style="font-family: 'Courier New', monospace; min-width: 220px;">
      <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 700; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 6px;">
        ${regionName}
      </h3>
      <div style="color: #999; font-size: 12px;">NO DATA - Check backend</div>
    </div>`
  }

  let content = `<div style="font-family: 'Courier New', monospace; min-width: 240px;">
    <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 700; text-transform: uppercase; border-bottom: 2px solid #000; padding-bottom: 6px;">
      ${regionName}
    </h3>
    <div style="font-size: 12px;">`

  if (indicator === 'conflict-proneness' || indicator === 'conflict-risk') {
    const color = getRiskColor(regionInfo.proneness_level)
    content += `
      <div style="margin: 6px 0; padding: 4px; background: ${color}22;">
        <strong>${indicator === 'conflict-proneness' ? 'CONFLICT PRONENESS' : 'CONFLICT RISK'}:</strong> <span style="color: ${color};">${regionInfo.proneness_level}</span>
      </div>
      <div style="margin: 6px 0; padding: 4px;">
        <strong>SCORE:</strong> ${regionInfo.proneness_score.toFixed(1)}/10
      </div>
      <div style="margin: 6px 0; padding: 4px;">
        <strong>EVENTS (6M):</strong> ${regionInfo.incidents}
      </div>
      <div style="margin: 6px 0; padding: 4px;">
        <strong>FATALITIES:</strong> ${regionInfo.fatalities}
      </div>
    `
  } else if (indicator === 'climate-risk') {
    const color = getRiskColor(regionInfo.climate_risk_level)
    content += `
      <div style="margin: 6px 0; padding: 4px; background: ${color}22;">
        <strong>CLIMATE RISK:</strong> <span style="color: ${color};">${regionInfo.climate_risk_level}</span>
      </div>
      <div style="margin: 6px 0; padding: 4px;">
        <strong>SCORE:</strong> ${regionInfo.climate_risk_score.toFixed(1)}/10
      </div>
      <div style="margin: 6px 0; padding: 4px;">
        <strong>CONFLICT PRONENESS:</strong> ${regionInfo.proneness_level}
      </div>
    `
  } else if (indicator === 'combined-risk') {
    const avgScore = (regionInfo.proneness_score + regionInfo.climate_risk_score) / 2
    const color = getRiskColor(undefined, avgScore)
    const level = avgScore >= 7.5 ? 'EXTREME'
      : avgScore >= 6 ? 'VERY HIGH'
      : avgScore >= 4.5 ? 'HIGH'
      : avgScore >= 3 ? 'MODERATE' : 'LOW'
    content += `
      <div style="margin: 6px 0; padding: 4px; background: ${color}22;">
        <strong>COMBINED RISK:</strong> <span style="color: ${color};">${level}</span>
      </div>
      <div style="margin: 6px 0; padding: 4px;">
        <strong>SCORE:</strong> ${avgScore.toFixed(1)}/10
      </div>
      <div style="margin: 6px 0; padding: 4px;">
        <strong>CONFLICT:</strong> ${regionInfo.proneness_score.toFixed(1)} | <strong>CLIMATE:</strong> ${regionInfo.climate_risk_score.toFixed(1)}
      </div>
    `
  }

  content += `
    </div>
  </div>`

  return content
}
