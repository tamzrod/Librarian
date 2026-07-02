import { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'
import type { TraceEventItem } from '../types/api'
import type { FilterState } from './FilterPalette'
import './FilmStrip.css'

interface FilmStripProps {
  filters: FilterState
  onThumbnailClick?: (item: TraceEventItem) => void
  selectedThumbnailId?: number
  scrollToThumbnailId?: number
}

export default function FilmStrip({ 
  filters, 
  onThumbnailClick, 
  selectedThumbnailId,
  scrollToThumbnailId 
}: FilmStripProps) {
  const [thumbnails, setThumbnails] = useState<TraceEventItem[]>([])
  const [loading, setLoading] = useState(false)
  const [hoveredId, setHoveredId] = useState<number | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const thumbnailRefs = useRef<Map<number, HTMLDivElement>>(new Map())

  // Load thumbnails
  useEffect(() => {
    loadThumbnails()
  }, [filters])

  const loadThumbnails = async () => {
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
        limit: 200 // More thumbnails for film strip
      })

      // Sort chronologically (oldest first for film strip)
      const sorted = [...response.events].sort((a, b) => {
        if (!a.timestamp && !b.timestamp) return 0
        if (!a.timestamp) return 1
        if (!b.timestamp) return -1
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      })

      setThumbnails(sorted)
    } catch (error) {
      console.error('Failed to load thumbnails:', error)
    } finally {
      setLoading(false)
    }
  }

  // Scroll to selected thumbnail
  useEffect(() => {
    if (scrollToThumbnailId && thumbnailRefs.current.has(scrollToThumbnailId)) {
      const element = thumbnailRefs.current.get(scrollToThumbnailId)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
      }
    }
  }, [scrollToThumbnailId])

  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return '?'
    try {
      const date = new Date(timestamp)
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    } catch {
      return '?'
    }
  }

  const getThumbnailUrl = (item: TraceEventItem): string | null => {
    return api.getTraceThumbnailUrl(item.thumbnail_path)
  }

  const handleThumbnailClick = (item: TraceEventItem) => {
    onThumbnailClick?.(item)
  }

  return (
    <div className="film-strip">
      <div className="film-strip-header">
        <div className="film-strip-title">
          <span>🎞️</span> Film Strip
          <span className="film-strip-count">
            {thumbnails.length} frames
          </span>
        </div>
      </div>

      <div className="film-strip-track-wrapper">
        {loading ? (
          <div className="film-strip-loading">Loading...</div>
        ) : thumbnails.length === 0 ? (
          <div className="film-strip-empty">
            No photos match the current filters
          </div>
        ) : (
          <div ref={containerRef} className="film-strip-track">
            {thumbnails.map((item, index) => (
              <div
                key={item.document_id}
                ref={(el) => {
                  if (el) thumbnailRefs.current.set(item.document_id, el)
                }}
                className={`film-strip-frame ${
                  selectedThumbnailId === item.document_id ? 'selected' : ''
                } ${hoveredId === item.document_id ? 'hovered' : ''}`}
                onClick={() => handleThumbnailClick(item)}
                onMouseEnter={() => setHoveredId(item.document_id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <div className="film-strip-frame-inner">
                  {getThumbnailUrl(item) ? (
                    <img
                      src={getThumbnailUrl(item)!}
                      alt={item.filename}
                      loading="lazy"
                    />
                  ) : (
                    <div className="film-strip-placeholder">📷</div>
                  )}
                  <div className="film-strip-frame-overlay">
                    <div className="film-strip-frame-date">
                      {formatTimestamp(item.timestamp)}
                    </div>
                    {item.camera && (
                      <div className="film-strip-frame-camera">
                        {item.camera.split(' ')[0]}
                      </div>
                    )}
                  </div>
                </div>
                <div className="film-strip-frame-number">{index + 1}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
