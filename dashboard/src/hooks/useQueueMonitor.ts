import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type { JobQueueResponse, JobRecord } from '../types/api'

interface UseQueueMonitorResult {
  data: JobQueueResponse | null
  loading: boolean
  error: Error | null
  refetch: () => void
  jobs: JobRecord[]
  counts: {
    queued: number
    in_progress: number
    completed: number
    failed: number
  }
}

export function useQueueMonitor(
  filters: { status?: string; job_type?: string } = {},
  pollInterval: number = 3000
): UseQueueMonitorResult {
  const [data, setData] = useState<JobQueueResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchQueue = useCallback(async () => {
    try {
      const result = await api.getQueueJobs({
        status: filters.status,
        job_type: filters.job_type,
        limit: 100,
      })
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch queue'))
    } finally {
      setLoading(false)
    }
  }, [filters.status, filters.job_type])

  useEffect(() => {
    fetchQueue()
    
    const interval = setInterval(fetchQueue, pollInterval)
    return () => clearInterval(interval)
  }, [fetchQueue, pollInterval])

  return {
    data,
    loading,
    error,
    refetch: fetchQueue,
    jobs: data?.jobs || [],
    counts: data?.counts || { queued: 0, in_progress: 0, completed: 0, failed: 0 },
  }
}
