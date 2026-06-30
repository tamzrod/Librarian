import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useDocuments } from '../hooks/useDocuments'
import { useDocumentJourney } from '../hooks/useExtractions'
import StatusBadge from '../components/StatusBadge'
import { DOCUMENT_LIFECYCLE_STATES, LIFECYCLE_STATE_COLORS } from '../types/api'
import './DocumentJourney.css'

function DocumentJourney() {
  const { id } = useParams<{ id?: string }>()
  const documentId = id ? parseInt(id, 10) : null
  const navigate = useNavigate()
  
  const { documents, loading, total } = useDocuments({ limit: 50 })
  const { data: journey } = useDocumentJourney(documentId)
  
  const [statusFilter, setStatusFilter] = useState<string>('')

  const handleDocumentClick = (docId: number) => {
    navigate(`/documents/${docId}`)
  }

  const filteredDocuments = documents.filter(doc => {
    if (statusFilter && doc.status !== statusFilter) return false
    return true
  })

  if (documentId && journey) {
    return (
      <div className="document-journey-detail">
        <header className="page-header">
          <button className="back-btn" onClick={() => navigate('/documents')}>
            ← Back to List
          </button>
          <h1>Document Journey</h1>
        </header>

        <section className="document-info">
          <div className="info-card">
            <h2>Document</h2>
            <dl>
              <div className="info-row">
                <dt>ID</dt>
                <dd><code>#{journey.document_id}</code></dd>
              </div>
              <div className="info-row">
                <dt>Path</dt>
                <dd><code className="path-text">{journey.path}</code></dd>
              </div>
              <div className="info-row">
                <dt>Extension</dt>
                <dd>{journey.extension || 'Unknown'}</dd>
              </div>
              <div className="info-row">
                <dt>File Size</dt>
                <dd>{journey.file_size ? formatBytes(journey.file_size) : 'Unknown'}</dd>
              </div>
              <div className="info-row">
                <dt>Status</dt>
                <dd>
                  <StatusBadge
                    status={getStatusFromString(journey.status)}
                    label={journey.status}
                  />
                </dd>
              </div>
              <div className="info-row">
                <dt>Created</dt>
                <dd>{journey.created_at ? new Date(journey.created_at).toLocaleString() : 'Unknown'}</dd>
              </div>
              <div className="info-row">
                <dt>Indexed</dt>
                <dd>{journey.indexed_at ? new Date(journey.indexed_at).toLocaleString() : 'Pending'}</dd>
              </div>
            </dl>
          </div>
        </section>

        <section className="lifecycle-timeline">
          <h2>Processing Lifecycle</h2>
          <div className="timeline">
            {DOCUMENT_LIFECYCLE_STATES.map((state, index) => {
              const isComplete = journey.status === 'COMPLETE' && index < DOCUMENT_LIFECYCLE_STATES.indexOf('COMPLETE')
              const isCurrent = journey.status === state || (journey.status === 'COMPLETE' && state === 'COMPLETE')
              const isPending = index > DOCUMENT_LIFECYCLE_STATES.indexOf(journey.status as typeof DOCUMENT_LIFECYCLE_STATES[number]) && journey.status !== 'COMPLETE'
              
              return (
                <div
                  key={state}
                  className={`timeline-item ${isComplete ? 'complete' : ''} ${isCurrent ? 'current' : ''} ${isPending ? 'pending' : ''}`}
                >
                  <div
                    className="timeline-dot"
                    style={{ backgroundColor: isPending ? 'var(--bg-tertiary)' : LIFECYCLE_STATE_COLORS[state] }}
                  />
                  <div className="timeline-content">
                    <span className="timeline-state">{formatStateName(state)}</span>
                    {isCurrent && <span className="timeline-badge">Current</span>}
                  </div>
                  {index < DOCUMENT_LIFECYCLE_STATES.length - 1 && (
                    <div className={`timeline-line ${isComplete ? 'complete' : ''}`} />
                  )}
                </div>
              )
            })}
          </div>
        </section>

        <section className="document-jobs">
          <h2>Processing Jobs ({journey.jobs.length})</h2>
          <div className="jobs-table">
            <div className="jobs-table-header">
              <span>ID</span>
              <span>Type</span>
              <span>Status</span>
              <span>Worker</span>
              <span>Attempts</span>
            </div>
            <div className="jobs-table-body">
              {journey.jobs.length === 0 ? (
                <div className="jobs-empty">No jobs processed yet</div>
              ) : (
                journey.jobs.map(job => (
                  <div key={job.id} className="job-item">
                    <span><code>#{job.id}</code></span>
                    <span className="job-type">{job.job_type}</span>
                    <span>
                      <StatusBadge
                        status={getStatusFromJobStatus(job.status)}
                        label={job.status}
                        size="small"
                      />
                    </span>
                    <span>{job.worker_id || '-'}</span>
                    <span>{job.attempt_count}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="document-journey">
      <header className="page-header">
        <h1>Document Journey</h1>
        <div className="header-actions">
          <span className="doc-count">{total} documents</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="DISCOVERED">Discovered</option>
            <option value="METADATA_INDEXED">Metadata Indexed</option>
            <option value="CONTENT_EXTRACTED">Content Extracted</option>
            <option value="ENTITY_EXTRACTED">Entity Extracted</option>
            <option value="COMPLETE">Complete</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </header>

      {loading ? (
        <div className="page-loading">
          <div className="spinner" />
          <span>Loading documents...</span>
        </div>
      ) : (
        <div className="documents-table">
          <div className="table-header">
            <span>ID</span>
            <span>Path</span>
            <span>Extension</span>
            <span>Status</span>
            <span>Size</span>
            <span>Created</span>
          </div>
          <div className="table-body">
            {filteredDocuments.length === 0 ? (
              <div className="table-empty">No documents found</div>
            ) : (
              filteredDocuments.map(doc => (
                <div
                  key={doc.id}
                  className="table-row"
                  onClick={() => handleDocumentClick(doc.id)}
                >
                  <span><code>#{doc.id}</code></span>
                  <span className="path-text" title={doc.path}>{doc.path}</span>
                  <span>{doc.extension || '-'}</span>
                  <span>
                    <StatusBadge
                      status={getStatusFromString(doc.status)}
                      label={doc.status}
                      size="small"
                    />
                  </span>
                  <span>{doc.file_size ? formatBytes(doc.file_size) : '-'}</span>
                  <span>{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '-'}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <section className="lifecycle-legend">
        <h2>Lifecycle States</h2>
        <div className="legend-items">
          {DOCUMENT_LIFECYCLE_STATES.map(state => (
            <div key={state} className="legend-item">
              <span
                className="legend-dot"
                style={{ backgroundColor: LIFECYCLE_STATE_COLORS[state] }}
              />
              <span className="legend-label">{formatStateName(state)}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

function formatStateName(state: string): string {
  return state.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function getStatusFromString(status: string): 'healthy' | 'degraded' | 'warning' | 'error' | 'inactive' {
  switch (status) {
    case 'COMPLETE':
    case 'METADATA_INDEXED':
    case 'CONTENT_EXTRACTED':
    case 'ENTITY_EXTRACTED':
      return 'healthy'
    case 'FAILED':
      return 'error'
    case 'DISCOVERED':
      return 'inactive'
    default:
      return 'warning'
  }
}

function getStatusFromJobStatus(status: string): 'healthy' | 'degraded' | 'warning' | 'error' | 'inactive' {
  switch (status) {
    case 'COMPLETED':
      return 'healthy'
    case 'IN_PROGRESS':
      return 'warning'
    case 'FAILED':
      return 'error'
    case 'QUEUED':
      return 'inactive'
    default:
      return 'inactive'
  }
}

export default DocumentJourney
