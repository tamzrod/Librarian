/**
 * Evidence Timeline Hook
 * Fetches data from timeline API endpoints
 */

import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import type { TimelineStats, TimelinePhotosResponse, TimelineMapResponse } from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

interface UseTimelineStatsResult {
  data: TimelineStats | null
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useTimelineStats(pollInterval = 30000): UseTimelineStatsResult {
  const [data, setData] = useState<TimelineStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get<TimelineStats>(
        `${API_BASE_URL}/api/v1/timeline/stats`
      )
      setData(response.data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch timeline stats'))
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

interface UseTimelinePhotosResult {
  data: TimelinePhotosResponse | null
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useTimelinePhotos(
  filters: {
    camera?: string
    gps_only?: boolean
    start_date?: string
    end_date?: string
  } = {},
  pollInterval = 0
): UseTimelinePhotosResult {
  const [data, setData] = useState<TimelinePhotosResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchPhotos = useCallback(async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filters.camera) params.append('camera', filters.camera)
      if (filters.gps_only) params.append('gps_only', 'true')
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)
      params.append('limit', '100')

      const response = await axios.get<TimelinePhotosResponse>(
        `${API_BASE_URL}/api/v1/timeline/photos?${params.toString()}`
      )
      setData(response.data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch photos'))
    } finally {
      setLoading(false)
    }
  }, [filters.camera, filters.gps_only, filters.start_date, filters.end_date])

  useEffect(() => {
    fetchPhotos()
  }, [fetchPhotos])

  useEffect(() => {
    if (pollInterval > 0) {
      const interval = setInterval(fetchPhotos, pollInterval)
      return () => clearInterval(interval)
    }
  }, [fetchPhotos, pollInterval])

  return { data, loading, error, refetch: fetchPhotos }
}

interface UseTimelineMapResult {
  data: TimelineMapResponse | null
  loading: boolean
  error: Error | null
  refetch: () => void
}

export function useTimelineMap(pollInterval = 30000): UseTimelineMapResult {
  const [data, setData] = useState<TimelineMapResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchMapData = useCallback(async () => {
    try {
      const response = await axios.get<TimelineMapResponse>(
        `${API_BASE_URL}/api/v1/timeline/map`
      )
      setData(response.data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch map data'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMapData()
    const interval = setInterval(fetchMapData, pollInterval)
    return () => clearInterval(interval)
  }, [fetchMapData, pollInterval])

  return { data, loading, error, refetch: fetchMapData }
}
