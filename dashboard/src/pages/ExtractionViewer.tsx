import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useDocuments } from '../hooks/useDocuments'
import { useExtractions } from '../hooks/useExtractions'
import ChartCard from '../components/ChartCard'
import ExtractionCountsChart from '../components/charts/ExtractionCountsChart'
import './ExtractionViewer.css'

function ExtractionViewer() {
  const { id } = useParams<{ id?: string }>()
  const documentId = id ? parseInt(id, 10) : null
  const navigate = useNavigate()
  
  const { documents, loading: docsLoading } = useDocuments({ limit: 100 })
  const { data: extractions } = useExtractions(documentId)
  
  const [searchQuery, setSearchQuery] = useState('')

  const handleDocumentClick = (docId: number) => {
    navigate(`/extractions/${docId}`)
  }

  const filteredDocuments = documents.filter(doc => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      doc.path.toLowerCase().includes(query) ||
      doc.extension?.toLowerCase().includes(query) ||
      doc.status.toLowerCase().includes(query)
    )
  })

  if (documentId && extractions) {
    return (
      <div className="extraction-viewer-detail">
        <header className="page-header">
          <button className="back-btn" onClick={() => navigate('/extractions')}>
            ← Back to List
          </button>
          <h1>Extraction Results</h1>
        </header>

        <section className="document-info">
          <div className="info-card">
            <h2>Document</h2>
            <dl>
              <div className="info-row">
                <dt>ID</dt>
                <dd><code>#{extractions.document_id}</code></dd>
              </div>
              <div className="info-row">
                <dt>Path</dt>
                <dd><code className="path-text">{extractions.path}</code></dd>
              </div>
            </dl>
          </div>
        </section>

        <section className="extraction-stats">
          <div className="stat-card">
            <span className="stat-icon">🏷️</span>
            <span className="stat-value">{extractions.entities.length}</span>
            <span className="stat-label">Entities</span>
          </div>
          <div className="stat-card">
            <span className="stat-icon">📅</span>
            <span className="stat-value">{extractions.events.length}</span>
            <span className="stat-label">Events</span>
          </div>
          <div className="stat-card">
            <span className="stat-icon">📍</span>
            <span className="stat-value">{extractions.locations.length}</span>
            <span className="stat-label">Locations</span>
          </div>
        </section>

        {extractions.content_preview && (
          <section className="content-preview">
            <h2>Content Preview</h2>
            <pre className="preview-text">{extractions.content_preview}</pre>
          </section>
        )}

        <section className="extraction-results">
          <div className="results-grid">
            <div className="results-section">
              <h2>Entities ({extractions.entities.length})</h2>
              {extractions.entities.length === 0 ? (
                <div className="empty-state">No entities extracted</div>
              ) : (
                <div className="entities-list">
                  {extractions.entities.map(entity => (
                    <div key={entity.id} className="entity-item">
                      <span className="entity-type">{entity.type}</span>
                      <span className="entity-value">{entity.value}</span>
                      {entity.normalized && (
                        <span className="entity-normalized">({entity.normalized})</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="results-section">
              <h2>Events ({extractions.events.length})</h2>
              {extractions.events.length === 0 ? (
                <div className="empty-state">No events extracted</div>
              ) : (
                <div className="events-list">
                  {extractions.events.map(event => (
                    <div key={event.id} className="event-item">
                      <span className="event-type">{event.type}</span>
                      <span className="event-timestamp">{formatDate(event.timestamp)}</span>
                      {event.description && (
                        <span className="event-description">{event.description}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="results-section">
              <h2>Locations ({extractions.locations.length})</h2>
              {extractions.locations.length === 0 ? (
                <div className="empty-state">No locations extracted</div>
              ) : (
                <div className="locations-list">
                  {extractions.locations.map(location => (
                    <div key={location.id} className="location-item">
                      <span className="location-name">{location.name}</span>
                      {location.city && <span className="location-detail">{location.city}</span>}
                      {location.country && <span className="location-detail">{location.country}</span>}
                      {(location.latitude && location.longitude) && (
                        <span className="location-coords">
                          ({location.latitude.toFixed(4)}, {location.longitude.toFixed(4)})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="extraction-viewer">
      <header className="page-header">
        <h1>Extraction Viewer</h1>
        <div className="header-actions">
          <span className="doc-count">{documents.length} documents</span>
        </div>
      </header>

      <section className="extraction-overview">
        <ChartCard title="Extraction Distribution">
          <ExtractionCountsChart />
        </ChartCard>
      </section>

      <section className="search-section">
        <input
          type="text"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </section>

      {docsLoading ? (
        <div className="page-loading">
          <div className="spinner" />
          <span>Loading documents...</span>
        </div>
      ) : (
        <div className="documents-list">
          <div className="list-header">
            <span>ID</span>
            <span>Path</span>
            <span>Entities</span>
            <span>Events</span>
            <span>Locations</span>
          </div>
          <div className="list-body">
            {filteredDocuments.length === 0 ? (
              <div className="list-empty">No documents found</div>
            ) : (
              filteredDocuments.map(doc => (
                <div
                  key={doc.id}
                  className="list-row"
                  onClick={() => handleDocumentClick(doc.id)}
                >
                  <span><code>#{doc.id}</code></span>
                  <span className="path-text" title={doc.path}>{doc.path}</span>
                  <span className="extraction-count">-</span>
                  <span className="extraction-count">-</span>
                  <span className="extraction-count">-</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function formatDate(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return timestamp
  }
}

export default ExtractionViewer
