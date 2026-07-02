import { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'
import type { TraceMapMarker } from '../types/api'
import type { FilterState } from './FilterPalette'
import './MapCanvas.css'

interface MapCanvasProps {
  filters: FilterState
  onMarkerClick?: (marker: TraceMapMarker) => void
  selectedMarkerId?: number
  centerOnMarkerId?: number
}

declare global {
  interface Window {
    L: typeof import('leaflet')
  }
}

export default function MapCanvas({ filters, onMarkerClick, selectedMarkerId, centerOnMarkerId }: MapCanvasProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const leafletMapRef = useRef<any>(null)
  const markersRef = useRef<any[]>([])
  const markerDataRef = useRef<Map<number, TraceMapMarker>>(new Map())
  const resizeObserverRef = useRef<ResizeObserver | null>(null)
  const [markers, setMarkers] = useState<TraceMapMarker[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({ total: 0, withGps: 0 })
  const [leafletLoaded, setLeafletLoaded] = useState(false)

  // Load Leaflet dynamically
  useEffect(() => {
    const loadLeaflet = async () => {
      if (window.L) {
        setLeafletLoaded(true)
        return
      }

      // Load Leaflet CSS
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
      document.head.appendChild(link)

      // Load Leaflet JS
      const script = document.createElement('script')
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
      script.onload = () => setLeafletLoaded(true)
      document.head.appendChild(script)
    }

    loadLeaflet()
  }, [])

  // Initialize map
  useEffect(() => {
    if (!leafletLoaded || !mapRef.current || leafletMapRef.current) return

    const L = window.L
    if (!L) return

    // Initialize map centered on a default location (can be adjusted)
    const map = L.map(mapRef.current).setView([14.5995, 120.9842], 10) // Manila, Philippines

    // Add dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(map)

    leafletMapRef.current = map

    // CRITICAL: Invalidate size after initialization to fix flexbox container issue
    // Leaflet calculates dimensions at init time; if container has 0 height, map breaks
    setTimeout(() => {
      map.invalidateSize({ pan: true })
    }, 100)

    // Set up ResizeObserver to handle layout changes
    if (mapRef.current) {
      resizeObserverRef.current = new ResizeObserver(() => {
        map.invalidateSize({ pan: false })
      })
      resizeObserverRef.current.observe(mapRef.current)
    }

    return () => {
      if (resizeObserverRef.current && mapRef.current) {
        resizeObserverRef.current.unobserve(mapRef.current)
        resizeObserverRef.current.disconnect()
        resizeObserverRef.current = null
      }
      map.remove()
      leafletMapRef.current = null
    }
  }, [leafletLoaded])

  // Load markers
  useEffect(() => {
    loadMarkers()
  }, [filters])

  const loadMarkers = async () => {
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
        limit: 500
      })

      setMarkers(response.markers)
      setStats({
        total: response.stats.total,
        withGps: response.stats.with_gps
      })

      // Store marker data for later centering
      markerDataRef.current.clear()
      response.markers.forEach(marker => {
        markerDataRef.current.set(marker.document_id, marker)
      })
    } catch (error) {
      console.error('Failed to load markers:', error)
    } finally {
      setLoading(false)
    }
  }

  // Center map on a specific marker
  useEffect(() => {
    if (!centerOnMarkerId || !leafletMapRef.current) return

    const marker = markerDataRef.current.get(centerOnMarkerId)
    if (marker) {
      leafletMapRef.current.setView([marker.latitude, marker.longitude], 14, {
        animate: true,
        duration: 0.5
      })
    }
  }, [centerOnMarkerId, leafletLoaded])

  // Add markers to map
  useEffect(() => {
    if (!leafletMapRef.current || !leafletLoaded) return

    const L = window.L
    if (!L) return

    const map = leafletMapRef.current

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove())
    markersRef.current = []

    // Add new markers
    markers.forEach(marker => {
      const customIcon = L.divIcon({
        className: 'custom-marker',
        html: `
          <div class="photo-marker ${selectedMarkerId === marker.document_id ? 'selected' : ''}" 
               data-id="${marker.document_id}">
            📷
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      })

      const leafletMarker = L.marker([marker.latitude, marker.longitude], { icon: customIcon })
        .addTo(map)
        .on('click', () => onMarkerClick?.(marker))

      // Create popup content with thumbnail if available
      const thumbnailUrl = marker.thumbnail_path ? api.getTraceThumbnailUrl(marker.thumbnail_path) : null
      const thumbnailHtml = thumbnailUrl
        ? `<img src="${thumbnailUrl}" alt="${marker.filename}" class="map-popup-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" /><div class="map-popup-placeholder" style="display:none;">📷</div>`
        : `<div class="map-popup-placeholder">📷</div>`

      const popupContent = `
        <div class="map-popup">
          ${thumbnailHtml}
          <div class="map-popup-info">
            <div class="map-popup-camera">${marker.camera || 'Unknown Camera'}</div>
            <div class="map-popup-timestamp">${formatTimestamp(marker.timestamp)}</div>
            <div class="map-popup-location">${marker.filename}</div>
            <div class="map-popup-gps">${marker.latitude.toFixed(6)}, ${marker.longitude.toFixed(6)}</div>
          </div>
        </div>
      `

      leafletMarker.bindPopup(popupContent)
      markersRef.current.push(leafletMarker)
    })

    // Fit bounds if we have markers
    if (markers.length > 0) {
      const bounds = L.latLngBounds(markers.map(m => [m.latitude, m.longitude]))
      map.fitBounds(bounds, { padding: [50, 50] })
    }

    // Invalidate size after adding markers (fitBounds changes map dimensions)
    setTimeout(() => {
      map.invalidateSize({ pan: true })
    }, 100)
  }, [markers, selectedMarkerId, leafletLoaded, onMarkerClick])

  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return 'Unknown date'
    try {
      const date = new Date(timestamp)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return 'Unknown date'
    }
  }

  const zoomIn = () => {
    leafletMapRef.current?.zoomIn()
  }

  const zoomOut = () => {
    leafletMapRef.current?.zoomOut()
  }

  const resetView = () => {
    if (markers.length > 0 && window.L) {
      const L = window.L
      const bounds = L.latLngBounds(markers.map(m => [m.latitude, m.longitude]))
      leafletMapRef.current?.fitBounds(bounds, { padding: [50, 50] })
    }
  }

  return (
    <div className="map-canvas">
      <div ref={mapRef} className="map-container" />

      {loading && (
        <div className="map-loading">Loading markers...</div>
      )}

      {!loading && markers.length === 0 && (
        <div className="map-empty">
          <div className="map-empty-icon">🗺️</div>
          <div className="map-empty-text">
            No photos with GPS coordinates found.<br />
            Try adjusting your filters.
          </div>
        </div>
      )}

      {markers.length > 0 && (
        <div className="map-stats">
          <div className="map-stat">
            <span className="map-stat-value">{stats.total}</span>
            <span className="map-stat-label">Photos</span>
          </div>
          <div className="map-stat">
            <span className="map-stat-value">{stats.withGps}</span>
            <span className="map-stat-label">With GPS</span>
          </div>
          <div className="map-stat">
            <span className="map-stat-value">{markers.length}</span>
            <span className="map-stat-label">Markers</span>
          </div>
        </div>
      )}

      <div className="map-controls">
        <button className="map-control-btn" onClick={zoomIn} title="Zoom in">
          +
        </button>
        <button className="map-control-btn" onClick={zoomOut} title="Zoom out">
          −
        </button>
        <button className="map-control-btn" onClick={resetView} title="Reset view">
          ⌂
        </button>
      </div>
    </div>
  )
}
