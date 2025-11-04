import { useEffect, useState } from 'react'

interface DashboardData {
  summary: {
    conflict_events: number
    proneness_scores: number
    states_analyzed: number
    risk_assessments: number
  }
  files: Record<string, any>
  latest_update: string
}

export function useData() {
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/summary')
        if (!response.ok) throw new Error('Failed to fetch data')
        const data = await response.json()
        setSummary(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return { summary, loading, error }
}
