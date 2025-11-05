import { useEffect, useState } from 'react'

export interface StateRiskData {
  name: string
  cp_score: number
  cp_category: string
  incidents: number
  political_risk: number | null
  climate_risk: number | null
}

export function useMapData() {
  const [states, setStates] = useState<StateRiskData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch conflict proneness data
        const cpResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/conflict-proneness`)
        const cpData = await cpResponse.json()

        // Fetch combined risk data
        const riskResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"}/api/combined-risk`)
        const riskData = await riskResponse.json()

        // Merge data by state name
        const mergedData = cpData.data.map((cp: any) => {
          const risk = riskData.data.find((r: any) => r.ADM1_NAME === cp.ADM1_NAME)
          return {
            name: cp.ADM1_NAME,
            cp_score: cp.cp_score || 0,
            cp_category: cp.cp_category || 'UNKNOWN',
            incidents: cp.incidents || 0,
            political_risk: risk?.political_risk || null,
            climate_risk: risk?.climate_risk || null
          }
        })

        setStates(mergedData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch map data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return { states, loading, error }
}
