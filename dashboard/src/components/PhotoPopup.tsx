import { useState, useEffect } from 'react'
import { api } from '../services/api'
import type { TracePhotoDetail } from '../types/api'
import './PhotoPopup.css'

interface PhotoPopupProps {
  documentId: number | null
  onClose: () => void
}

export default function PhotoPopup({ documentId, onClose }: PhotoPopupProps) {
  const [photo, setPhoto] = useState<TracePhotoDetail | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (documentId) {
      loadPhoto(documentId)
    }
  }, [documentId])

  const loadPhoto = async (id: number) => {
    try {
      setLoading(true)
      const response = await api.getTracePhoto(id)
      setPhoto(response.photo)
    } catch (error) {
      console.error('Failed to load photo:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return 'Unknown'
    try {
      const date = new Date(timestamp)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch {
      return 'Unknown'
    }
  }

  const getThumbnailUrl = (): string | null => {
    if (!photo?.thumbnail_path) return null
    return api.getTraceThumbnailUrl(photo.thumbnail_path)
  }

  const openInExplorer = () => {
    if (photo) {
      window.open(`/explorer?document=${photo.document_id}`, '_blank')
    }
  }

  const copyGpsToClipboard = () => {
    if (photo?.gps_latitude && photo?.gps_longitude) {
      const gps = `${photo.gps_latitude}, ${photo.gps_longitude}`
      navigator.clipboard.writeText(gps)
    }
  }

  if (!documentId) return null

  return (
    <div className="photo-popup-overlay" onClick={handleOverlayClick}>
      <div className="photo-popup">
        <div className="photo-popup-header">
          <div className="photo-popup-title">
            <span>📷</span>
            {photo?.filename || 'Photo Details'}
          </div>
          <button className="photo-popup-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="photo-popup-image">
          {loading ? (
            <div className="photo-popup-image-placeholder">Loading...</div>
          ) : getThumbnailUrl() ? (
            <img src={getThumbnailUrl()!} alt={photo?.filename} />
          ) : (
            <div className="photo-popup-image-placeholder">📷</div>
          )}
        </div>

        <div className="photo-popup-content">
          {loading ? (
            <div className="photo-popup-loading">Loading metadata...</div>
          ) : photo ? (
            <>
              <div className="photo-popup-section">
                <div className="photo-popup-section-title">Camera</div>
                <div className="photo-popup-grid">
                  <div className="photo-popup-field">
                    <span className="photo-popup-field-label">Make</span>
                    <span className="photo-popup-field-value">
                      {photo.camera_make || <span className="empty">Unknown</span>}
                    </span>
                  </div>
                  <div className="photo-popup-field">
                    <span className="photo-popup-field-label">Model</span>
                    <span className="photo-popup-field-value">
                      {photo.camera_model || <span className="empty">Unknown</span>}
                    </span>
                  </div>
                  <div className="photo-popup-field">
                    <span className="photo-popup-field-label">Lens</span>
                    <span className="photo-popup-field-value">
                      {photo.lens_model || <span className="empty">Unknown</span>}
                    </span>
                  </div>
                  <div className="photo-popup-field">
                    <span className="photo-popup-field-label">Dimensions</span>
                    <span className="photo-popup-field-value">
                      {photo.width && photo.height ? `${photo.width} × ${photo.height}` : '-'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="photo-popup-section">
                <div className="photo-popup-section-title">Timestamp</div>
                <div className="photo-popup-grid">
                  <div className="photo-popup-field full-width">
                    <span className="photo-popup-field-label">Captured</span>
                    <span className="photo-popup-field-value">
                      {formatTimestamp(photo.timestamp)}
                    </span>
                  </div>
                  {photo.timestamp_digitized && (
                    <div className="photo-popup-field full-width">
                      <span className="photo-popup-field-label">Digitized</span>
                      <span className="photo-popup-field-value">
                        {formatTimestamp(photo.timestamp_digitized)}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="photo-popup-section">
                <div className="photo-popup-section-title">GPS Location</div>
                <div className="photo-popup-grid">
                  <div className="photo-popup-field full-width">
                    <span className="photo-popup-field-label">Coordinates</span>
                    <span className={`photo-popup-field-value photo-popup-gps ${!photo.gps_latitude && !photo.gps_longitude ? 'empty' : ''}`}>
                      {photo.gps_latitude && photo.gps_longitude
                        ? `${photo.gps_latitude.toFixed(6)}, ${photo.gps_longitude.toFixed(6)}`
                        : 'No GPS data'}
                    </span>
                  </div>
                  {photo.gps_altitude && (
                    <div className="photo-popup-field">
                      <span className="photo-popup-field-label">Altitude</span>
                      <span className="photo-popup-field-value">
                        {photo.gps_altitude.toFixed(1)} m
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="photo-popup-section">
                <div className="photo-popup-section-title">File</div>
                <div className="photo-popup-grid">
                  <div className="photo-popup-field">
                    <span className="photo-popup-field-label">Filename</span>
                    <span className="photo-popup-field-value">{photo.filename}</span>
                  </div>
                  <div className="photo-popup-field">
                    <span className="photo-popup-field-label">Format</span>
                    <span className="photo-popup-field-value">
                      {photo.file_format || 'Unknown'}
                    </span>
                  </div>
                  <div className="photo-popup-field full-width">
                    <span className="photo-popup-field-label">Path</span>
                    <span className="photo-popup-field-value" style={{ fontSize: '11px', wordBreak: 'break-all' }}>
                      {photo.path}
                    </span>
                  </div>
                  {photo.collection_name && (
                    <div className="photo-popup-field full-width">
                      <span className="photo-popup-field-label">Collection</span>
                      <span className="photo-popup-field-value">{photo.collection_name}</span>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : null}
        </div>

        <div className="photo-popup-actions">
          <button className="photo-popup-action btn-secondary" onClick={copyGpsToClipboard}>
            📋 Copy GPS
          </button>
          <button className="photo-popup-action btn-secondary" onClick={onClose}>
            Close
          </button>
          <button className="photo-popup-action btn-primary" onClick={openInExplorer}>
            🔍 Open in Explorer
          </button>
        </div>
      </div>
    </div>
  )
}
