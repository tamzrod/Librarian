import { useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import { useTimelineStats, useTimelinePhotos, useTimelineMap } from '../hooks/useTimeline'
import StatsCard from '../components/StatsCard'
import type { PhotoSummary, PhotoMapMarker } from '../types/api'
import 'leaflet/dist/leaflet.css'
import './EvidenceTimeline.css'

// Fix Leaflet default marker icon issue
delete (L.Icon.Default.prototype as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

function EvidenceTimeline() {
  // Fetch data
  const { data: stats } = useTimelineStats()
  const { data: photos, loading: photosLoading } = useTimelinePhotos({
    camera: undefined,
    gps_only: false,
  })
  const { data: mapData, loading: mapLoading } = useTimelineMap()

  // Filters state
  const [cameraFilter, setCameraFilter] = useState('')
  const [gpsOnly, setGpsOnly] = useState(false)

  // Calculate filtered photos
  const filteredPhotos = photos?.data.filter((photo) => {
    const matchesCamera = !cameraFilter ||
      (photo.camera_make?.toLowerCase().includes(cameraFilter.toLowerCase()) ?? false) ||
      (photo.camera_model?.toLowerCase().includes(cameraFilter.toLowerCase()) ?? false)
    const matchesGps = !gpsOnly || (photo.gps_latitude !== null && photo.gps_longitude !== null)
    return matchesCamera && matchesGps
  }) ?? []

  // Default map center (Philippines)
  const defaultCenter: [number, number] = [14.5995, 120.9842]
  const mapCenter: [number, number] = mapData?.markers?.[0]
    ? [mapData.markers[0].latitude, mapData.markers[0].longitude]
    : defaultCenter

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return 'N/A'
    }
  }

  const formatTimestamp = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return 'N/A'
    }
  }

  return (
    <div className="evidence-timeline">
      <header className="page-header">
        <h1>Evidence Timeline</h1>
        <span className="page-description">Photo metadata visualization</span>
      </header>

      {/* Statistics Section */}
      <section className="stats-section">
        <h2>Timeline Statistics</h2>
        <div className="stats-grid">
          <StatsCard
            title="Total Photos"
            value={stats?.photos_total ?? 0}
            icon="📷"
            color="var(--accent-primary)"
          />
          <StatsCard
            title="GPS Tagged"
            value={stats?.gps_tagged ?? 0}
            icon="📍"
            color="var(--accent-success)"
          />
          <StatsCard
            title="Unique Cameras"
            value={stats?.unique_cameras ?? 0}
            icon="📷"
            color="var(--accent-secondary)"
          />
          <StatsCard
            title="First Photo"
            value={formatDate(stats?.first_photo_timestamp ?? null)}
            icon="🗓️"
            color="var(--accent-info)"
          />
          <StatsCard
            title="Last Photo"
            value={formatDate(stats?.last_photo_timestamp ?? null)}
            icon="🗓️"
            color="var(--accent-warning)"
          />
        </div>
      </section>

      {/* Map Section */}
      <section className="map-section">
        <h2>Map View</h2>
        <div className="map-container">
          {mapLoading ? (
            <div className="map-loading">
              <div className="spinner" />
              <span>Loading map...</span>
            </div>
          ) : mapData?.markers && mapData.markers.length > 0 ? (
            <MapContainer
              center={mapCenter}
              zoom={10}
              className="leaflet-map"
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {mapData.markers.map((marker: PhotoMapMarker) => (
                <Marker key={marker.document_id} position={[marker.latitude, marker.longitude]}>
                  <Popup>
                    <div className="map-popup">
                      <strong>{marker.filename}</strong>
                      <br />
                      <span>📅 {formatTimestamp(marker.timestamp)}</span>
                      <br />
                      {marker.camera && <span>📷 {marker.camera}</span>}
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          ) : (
            <div className="map-empty">
              <span className="empty-icon">🗺️</span>
              <span>No GPS-tagged photos yet</span>
              <span className="empty-hint">
                Drop geotagged images into the library to see them on the map
              </span>
            </div>
          )}
        </div>
        {mapData && (
          <div className="map-legend">
            <span>{mapData.count} marker{mapData.count !== 1 ? 's' : ''} on map</span>
          </div>
        )}
      </section>

      {/* Photo Table Section */}
      <section className="table-section">
        <h2>Photo Table</h2>
        <div className="table-filters">
          <div className="filter-group">
            <label htmlFor="camera-filter">Camera:</label>
            <input
              id="camera-filter"
              type="text"
              placeholder="Filter by camera..."
              value={cameraFilter}
              onChange={(e) => setCameraFilter(e.target.value)}
              className="filter-input"
            />
          </div>
          <div className="filter-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={gpsOnly}
                onChange={(e) => setGpsOnly(e.target.checked)}
              />
              GPS Only
            </label>
          </div>
        </div>
        <div className="table-container">
          {photosLoading ? (
            <div className="table-loading">
              <div className="spinner" />
              <span>Loading photos...</span>
            </div>
          ) : filteredPhotos.length > 0 ? (
            <table className="photo-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Camera</th>
                  <th>GPS Available</th>
                  <th>Filename</th>
                </tr>
              </thead>
              <tbody>
                {filteredPhotos.map((photo: PhotoSummary) => (
                  <tr key={photo.document_id}>
                    <td>{formatTimestamp(photo.timestamp)}</td>
                    <td>
                      {photo.camera_make || photo.camera_model
                        ? `${photo.camera_make || ''} ${photo.camera_model || ''}`.trim()
                        : 'Unknown'}
                    </td>
                    <td>
                      {photo.gps_latitude !== null && photo.gps_longitude !== null ? (
                        <span className="gps-badge gps-available">✓ Yes</span>
                      ) : (
                        <span className="gps-badge gps-unavailable">✗ No</span>
                      )}
                    </td>
                    <td className="filename-cell">{photo.filename}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="table-empty">
              <span className="empty-icon">📷</span>
              <span>No photos match your filters</span>
            </div>
          )}
        </div>
        {photos?.pagination && (
          <div className="table-pagination">
            <span>
              Showing {filteredPhotos.length} of {photos.pagination.total} photos
            </span>
          </div>
        )}
      </section>
    </div>
  )
}

export default EvidenceTimeline
