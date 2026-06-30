import { useState, useEffect, useCallback } from 'react'
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
      // Use /api/v1/operations/overview for complete system overview
      const response = await fetch('/api/v1/operations/overview')
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`)
      }
      
      const overviewData = await response.json()
      
      // Create StatsResponse from overview for compatibility
      const stats: StatsResponse = {
        library_root: '/library',
        database: {
          connected: overviewData.database_status === 'CONNECTED',
          schema_ready: overviewData.database_status !== 'SCHEMA_ERROR',
          persistence_available: overviewData.database_status === 'CONNECTED',
        },
        documents: {
          total: overviewData.documents,
          indexed: overviewData.documents,
        },
        entities: {
          total: overviewData.entities,
        },
        events: {
          total: overviewData.events,
        },
        locations: {
          total: overviewData.locations,
        },
        parsers: {
          count: 9,
          types: ['json', 'yaml', 'csv', 'xml', 'ini', 'toml', 'python', 'image', 'text'],
        },
        watcher: {
          active: overviewData.watcher_status === 'RUNNING',
          last_scan: null,
        },
        initial_scan_complete: true,
        timestamp: new Date().toISOString(),
      }

      const overview: SystemOverviewResponse = {
        files: overviewData.files,
        documents: overviewData.documents,
        directories: overviewData.directories,
        watched_paths: overviewData.watched_paths,
        storage_used_bytes: overviewData.storage_used_bytes,
        entities: overviewData.entities,
        relationships: overviewData.relationships,
        events: overviewData.events,
        locations: overviewData.locations,
        embeddings: overviewData.embeddings,
        queued_jobs: overviewData.queued_jobs,
        running_jobs: overviewData.running_jobs,
        completed_jobs: overviewData.completed_jobs,
        failed_jobs: overviewData.failed_jobs,
        workers: overviewData.workers,
        oldest_job_age_seconds: overviewData.oldest_job_age_seconds,
        database_status: overviewData.database_status,
        watcher_status: overviewData.watcher_status,
        job_processor_status: overviewData.job_processor_status,
        api_status: overviewData.api_status,
      }

      setData({ overview, stats, documentStatus: null, jobStatus: null })
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
