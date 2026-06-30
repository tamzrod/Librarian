import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type { HealthResponse } from '../types/api'

interface UseApiStatusResult {
  data: HealthResponse | null
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useApiStatus(pollInterval: number = 5000): UseApiStatusResult {
  const [data, setData] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchStatus = useCallback(async () => {
    try {
      const result = await api.getHealth()
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch API status'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    
    const interval = setInterval(fetchStatus, pollInterval)
    return () => clearInterval(interval)
  }, [fetchStatus, pollInterval])

  return { data, loading, error, refetch: fetchStatus }
}
