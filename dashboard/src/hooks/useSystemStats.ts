import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type {
  SystemOverviewResponse,
  StatsResponse,
  DocumentStatusResponse,
  JobStatusResponse,
} from '../types/api'

interface SystemStats {
  overview: SystemOverviewResponse | null
  stats: StatsResponse | null
  documentStatus: DocumentStatusResponse | null
  jobStatus: JobStatusResponse | null
}

interface UseSystemStatsResult {
  data: SystemStats
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useSystemStats(pollInterval: number = 5000): UseSystemStatsResult {
  const [data, setData] = useState<SystemStats>({
    overview: null,
    stats: null,
    documentStatus: null,
    jobStatus: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchStats = useCallback(async () => {
    try {
      const [stats, documentStatus, jobStatus] = await Promise.all([
        api.getStats().catch(() => null),
        api.getDocumentStatusCounts().catch(() => null),
        api.getJobStatusCounts().catch(() => null),
      ])

      const overview: SystemOverviewResponse = {
        files: stats?.documents.total || 0,
        documents: stats?.documents.total || 0,
        directories: 1,
        watched_paths: 1,
        storage_used_bytes: null,
        entities: stats?.entities.total || 0,
        relationships: 0,
        events: stats?.events.total || 0,
        locations: stats?.locations.total || 0,
        embeddings: 0,
        queued_jobs: jobStatus?.status_counts['QUEUED'] || 0,
        running_jobs: jobStatus?.status_counts['IN_PROGRESS'] || 0,
        completed_jobs: jobStatus?.status_counts['COMPLETED'] || 0,
        failed_jobs: (jobStatus?.status_counts['FAILED'] || 0) + (jobStatus?.status_counts['FAILED_PERMANENT'] || 0),
        workers: 1,
        oldest_job_age_seconds: null,
        database_status: stats?.database.connected ? 'connected' : 'disconnected',
        watcher_status: stats?.watcher.active ? 'active' : 'inactive',
        job_processor_status: stats?.watcher.active ? 'active' : 'inactive',
        api_status: 'operational',
      }

      setData({ overview, stats, documentStatus, jobStatus })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch system stats'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
    
    const interval = setInterval(fetchStats, pollInterval)
    return () => clearInterval(interval)
  }, [fetchStats, pollInterval])

  return { data, loading, error, refetch: fetchStats }
}
