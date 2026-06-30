import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../services/api'
import type { ActivityFeedResponse, ActivityEvent } from '../types/api'

interface UseActivityFeedResult {
  data: ActivityFeedResponse | null
  loading: boolean
  error: Error | null
  events: ActivityEvent[]
  appendEvent: (event: ActivityEvent) => void
  clearEvents: () => void
}

export function useActivityFeed(
  limit: number = 50,
  autoRefresh: boolean = true,
  refreshInterval: number = 5000
): UseActivityFeedResult {
  const [data, setData] = useState<ActivityFeedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const previousTimestamp = useRef<string | null>(null)

  const fetchActivity = useCallback(async () => {
    try {
      const result = await api.getActivityFeed(limit)
      
      // Only update if there are new events
      const latestTimestamp = result.events[0]?.timestamp
      if (!previousTimestamp.current || latestTimestamp !== previousTimestamp.current) {
        setData(result)
        setEvents(result.events)
        previousTimestamp.current = latestTimestamp || null
      }
      
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch activity'))
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetchActivity()
    
    if (autoRefresh) {
      const interval = setInterval(fetchActivity, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [fetchActivity, autoRefresh, refreshInterval])

  const appendEvent = useCallback((event: ActivityEvent) => {
    setEvents((prev) => [event, ...prev].slice(0, limit))
  }, [limit])

  const clearEvents = useCallback(() => {
    setEvents([])
  }, [])

  return {
    data,
    loading,
    error,
    events,
    appendEvent,
    clearEvents,
  }
}
