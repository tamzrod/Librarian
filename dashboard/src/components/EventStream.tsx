import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { TraceEventItem } from '../types/api'
import type { FilterState } from './FilterPalette'
import './EventStream.css'

interface EventStreamProps {
  filters: FilterState
  onEventSelect?: (event: TraceEventItem) => void
  selectedEventId?: number
}

export default function EventStream({ filters, onEventSelect, selectedEventId }: EventStreamProps) {
  const [events, setEvents] = useState<TraceEventItem[]>([])
  const [loading, setLoading] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    loadEvents()
  }, [filters])

  const loadEvents = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()

      if (filters.cameras.length > 0) {
        params.append('cameras', filters.cameras.join(','))
      }
      if (filters.collections.length > 0) {
        params.append('collections', filters.collections.join(','))
      }
      if (filters.years.length > 0) {
        params.append('years', filters.years.join(','))
      }
      if (filters.sources.length > 0) {
        params.append('sources', filters.sources.join(','))
      }
      if (filters.startDate) {
        params.append('start_date', filters.startDate)
      }
      if (filters.endDate) {
        params.append('end_date', filters.endDate)
      }
      if (filters.includeUnknownDevice) {
        params.append('include_unknown_device', 'true')
      }

      const response = await api.getTraceData({
        cameras: params.get('cameras') || undefined,
        collections: params.get('collections') || undefined,
        years: params.get('years') || undefined,
        sources: params.get('sources') || undefined,
        startDate: params.get('start_date') || undefined,
        endDate: params.get('end_date') || undefined,
        includeUnknownDevice: params.get('include_unknown_device') === 'true',
        limit: 50
      })

      setEvents(response.events)
    } catch (error) {
      console.error('Failed to load events:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return 'Unknown'
    try {
      const date = new Date(timestamp)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Unknown'
    }
  }

  const getThumbnailUrl = (event: TraceEventItem): string | null => {
    return api.getTraceThumbnailUrl(event.thumbnail_path)
  }

  if (collapsed) {
    return (
      <div className="event-stream">
        <div className="event-stream-header">
          <div className="event-stream-title">
            <span>📷</span> Event Stream
          </div>
          <button
            className="event-stream-toggle"
            onClick={() => setCollapsed(false)}
          >
            ▲ Expand
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="event-stream">
      <div className="event-stream-header">
        <div className="event-stream-title">
          <span>📷</span> Event Stream
          <span className="event-stream-count">
            {events.length} items
          </span>
        </div>
        <button
          className="event-stream-toggle"
          onClick={() => setCollapsed(true)}
        >
          ▼ Collapse
        </button>
      </div>

      {loading ? (
        <div className="event-stream-loading">Loading events...</div>
      ) : events.length === 0 ? (
        <div className="event-empty">
          No events match the current filters
        </div>
      ) : (
        <div className="event-stream-content">
          {events.map(event => (
            <div
              key={event.document_id}
              className={`event-item ${selectedEventId === event.document_id ? 'selected' : ''}`}
              onClick={() => onEventSelect?.(event)}
            >
              <div className="event-thumbnail">
                {getThumbnailUrl(event) ? (
                  <img
                    src={getThumbnailUrl(event)!}
                    alt={event.filename}
                    loading="lazy"
                  />
                ) : (
                  <span className="event-thumbnail-placeholder">📷</span>
                )}
              </div>
              <div className="event-info">
                <div className="event-camera">
                  {event.camera || 'Unknown Camera'}
                </div>
                <div className="event-timestamp">
                  {formatTimestamp(event.timestamp)}
                </div>
                {event.location && (
                  <div className="event-location">
                    {event.location}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
