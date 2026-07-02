import { useState, useEffect } from 'react'
import FilterPalette, { FilterState } from '../components/FilterPalette'
import MapCanvas from '../components/MapCanvas'
import EventStream from '../components/EventStream'
import PhotoPopup from '../components/PhotoPopup'
import { api } from '../services/api'
import type { TraceMapMarker, TraceEventItem } from '../types/api'
import './TraceView.css'

type ViewMode = 'map' | 'timeline' | 'grid'

export default function TraceView() {
  const [filters, setFilters] = useState<FilterState>({
    cameras: [],
    collections: [],
    years: [],
    sources: []
  })
  const [viewMode, setViewMode] = useState<ViewMode>('map')
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null)
  const [stats, setStats] = useState({
    total: 0,
    withGps: 0,
    uniqueCameras: 0
  })

  useEffect(() => {
    loadStats()
  }, [filters])

  const loadStats = async () => {
    try {
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

      const response = await api.getTraceData({
        cameras: params.get('cameras') || undefined,
        collections: params.get('collections') || undefined,
        years: params.get('years') || undefined,
        sources: params.get('sources') || undefined,
        limit: 1
      })

      setStats({
        total: response.stats.total,
        withGps: response.stats.with_gps,
        uniqueCameras: response.stats.unique_cameras
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters)
  }

  const handleMarkerClick = (marker: TraceMapMarker) => {
    setSelectedDocumentId(marker.document_id)
  }

  const handleEventSelect = (event: TraceEventItem) => {
    setSelectedDocumentId(event.document_id)
  }

  const handlePopupClose = () => {
    setSelectedDocumentId(null)
  }

  return (
    <div className="trace-view">
      {/* View mode tabs */}
      <div className="trace-views">
        <button
          className={`trace-view-tab ${viewMode === 'map' ? 'active' : ''}`}
          onClick={() => setViewMode('map')}
        >
          🗺️ Map
        </button>
        <button
          className={`trace-view-tab ${viewMode === 'timeline' ? 'active' : ''}`}
          onClick={() => setViewMode('timeline')}
        >
          📅 Timeline
        </button>
        <button
          className={`trace-view-tab ${viewMode === 'grid' ? 'active' : ''}`}
          onClick={() => setViewMode('grid')}
        >
          📰 Grid
        </button>

        <div className="trace-stats">
          <div className="trace-stat">
            <span className="trace-stat-value">{stats.total}</span>
            <span>photos</span>
          </div>
          <div className="trace-stat">
            <span className="trace-stat-value">{stats.withGps}</span>
            <span>with GPS</span>
          </div>
          <div className="trace-stat">
            <span className="trace-stat-value">{stats.uniqueCameras}</span>
            <span>cameras</span>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="trace-main">
        {/* Filter palette */}
        <FilterPalette onFiltersChange={handleFiltersChange} />

        {/* Content area */}
        <div className="trace-content">
          <div className="trace-canvas">
            {viewMode === 'map' && (
              <MapCanvas
                filters={filters}
                onMarkerClick={handleMarkerClick}
                selectedMarkerId={selectedDocumentId || undefined}
              />
            )}
            {viewMode === 'timeline' && (
              <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-muted, #666)',
                fontSize: '14px'
              }}>
                Timeline view coming soon...
              </div>
            )}
            {viewMode === 'grid' && (
              <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-muted, #666)',
                fontSize: '14px'
              }}>
                Grid view coming soon...
              </div>
            )}
          </div>

          {/* Event stream */}
          <EventStream
            filters={filters}
            onEventSelect={handleEventSelect}
            selectedEventId={selectedDocumentId || undefined}
          />
        </div>
      </div>

      {/* Photo popup */}
      {selectedDocumentId && (
        <PhotoPopup
          documentId={selectedDocumentId}
          onClose={handlePopupClose}
        />
      )}
    </div>
  )
}
