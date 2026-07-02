import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import FilterPalette, { FilterState } from '../components/FilterPalette'
import MapCanvas from '../components/MapCanvas'
import EventStream from '../components/EventStream'
import PhotoPopup from '../components/PhotoPopup'
import { api } from '../services/api'
import type { TraceMapMarker, TraceEventItem } from '../types/api'
import './TraceView.css'

type ViewMode = 'map' | 'timeline' | 'grid'

/**
 * TraceView - Unified view for map, timeline, and grid visualizations.
 * Supports query parameter for direct navigation: ?view=map|timeline|grid
 */
export default function TraceView() {
  const [searchParams] = useSearchParams()
  const [filters, setFilters] = useState<FilterState>({
    cameras: [],
    collections: [],
    years: [],
    sources: []
  })
  
  // Initialize view mode from URL parameter (for backwards compatibility with /map, /timeline)
  const urlViewParam = searchParams.get('view') as ViewMode | null
  const initialViewMode: ViewMode = urlViewParam && ['map', 'timeline', 'grid'].includes(urlViewParam) 
    ? urlViewParam 
    : 'map'
  const [viewMode, setViewMode] = useState<ViewMode>(initialViewMode)
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null)
  const [stats, setStats] = useState({
    total: 0,
    withGps: 0,
    uniqueCameras: 0
  })

  // Load stats on mount
  useEffect(() => {
    api.getTraceData({ limit: 1 })
      .then(response => {
        setStats({
          total: response.stats.total,
          withGps: response.stats.with_gps,
          uniqueCameras: response.stats.unique_cameras
        })
      })
      .catch(error => {
        console.error('Failed to load trace stats:', error)
      })
  }, [])

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

        {/* Workspace - contains map and event stream */}
        <div className="trace-workspace">
          {/* Map area */}
          <div className="map-area">
            {viewMode === 'map' && (
              <MapCanvas
                filters={filters}
                onMarkerClick={handleMarkerClick}
                selectedMarkerId={selectedDocumentId || undefined}
              />
            )}
            {viewMode === 'timeline' && (
              <div className="placeholder-view">
                Timeline view coming soon...
              </div>
            )}
            {viewMode === 'grid' && (
              <div className="placeholder-view">
                Grid view coming soon...
              </div>
            )}
          </div>

          {/* Event stream - docked at bottom */}
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
