import { useState } from 'react'
import { useQueueMonitor } from '../hooks/useQueueMonitor'
import StatsCard from '../components/StatsCard'
import StatusBadge from '../components/StatusBadge'
import ChartCard from '../components/ChartCard'
import QueueDepthChart from '../components/charts/QueueDepthChart'
import FailureTrendsChart from '../components/charts/FailureTrendsChart'
import { JOB_STATUS_COLORS } from '../types/api'
import './QueueMonitor.css'

const JOB_TYPES = [
  'extract_text',
  'extract_entities',
  'extract_events',
  'extract_locations',
  'generate_embeddings',
]

function QueueMonitor() {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [jobTypeFilter, setJobTypeFilter] = useState<string>('')
  
  const { jobs, counts, loading, error, refetch } = useQueueMonitor({
    status: statusFilter || undefined,
    job_type: jobTypeFilter || undefined,
  })

  const filteredJobs = jobs.filter(job => {
    if (statusFilter && job.status !== statusFilter) return false
    if (jobTypeFilter && job.job_type !== jobTypeFilter) return false
    return true
  })

  if (loading && jobs.length === 0) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <span>Loading queue data...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page-error">
        <span className="error-icon">⚠️</span>
        <span>{error.message}</span>
        <button onClick={refetch}>Retry</button>
      </div>
    )
  }

  return (
    <div className="queue-monitor">
      <header className="page-header">
        <h1>Queue Monitor</h1>
        <button className="refresh-btn" onClick={refetch}>Refresh</button>
      </header>

      <section className="queue-stats">
        <StatsCard
          title="Queued"
          value={counts.queued}
          icon="⏳"
          color={JOB_STATUS_COLORS.QUEUED}
        />
        <StatsCard
          title="Running"
          value={counts.in_progress}
          icon="⚡"
          color={JOB_STATUS_COLORS.IN_PROGRESS}
        />
        <StatsCard
          title="Completed"
          value={counts.completed}
          icon="✅"
          color={JOB_STATUS_COLORS.COMPLETED}
        />
        <StatsCard
          title="Failed"
          value={counts.failed}
          icon="❌"
          color={JOB_STATUS_COLORS.FAILED}
        />
      </section>

      <section className="queue-charts">
        <ChartCard title="Queue Depth History">
          <QueueDepthChart />
        </ChartCard>
        <ChartCard title="Failure Trends">
          <FailureTrendsChart />
        </ChartCard>
      </section>

      <section className="job-filters">
        <div className="filter-group">
          <label htmlFor="status-filter">Status</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="QUEUED">Queued</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="job-type-filter">Job Type</label>
          <select
            id="job-type-filter"
            value={jobTypeFilter}
            onChange={(e) => setJobTypeFilter(e.target.value)}
          >
            <option value="">All</option>
            {JOB_TYPES.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
        <span className="job-count">{filteredJobs.length} jobs</span>
      </section>

      <section className="job-list">
        <div className="job-table">
          <div className="job-table-header">
            <span className="col-id">ID</span>
            <span className="col-doc">Document</span>
            <span className="col-type">Type</span>
            <span className="col-status">Status</span>
            <span className="col-worker">Worker</span>
            <span className="col-attempts">Attempts</span>
            <span className="col-age">Age</span>
          </div>
          <div className="job-table-body">
            {filteredJobs.length === 0 ? (
              <div className="job-table-empty">
                No jobs found matching the current filters.
              </div>
            ) : (
              filteredJobs.map(job => (
                <div key={job.id} className="job-row">
                  <span className="col-id">#{job.id}</span>
                  <span className="col-doc" title={job.document_path}>
                    {job.document_path ? truncatePath(job.document_path) : `#${job.document_id}`}
                  </span>
                  <span className="col-type">
                    <span className="job-type-badge">{job.job_type}</span>
                  </span>
                  <span className="col-status">
                    <StatusBadge
                      status={getStatusFromJobStatus(job.status)}
                      label={job.status}
                      size="small"
                    />
                  </span>
                  <span className="col-worker">
                    {job.worker_id || '-'}
                  </span>
                  <span className="col-attempts">
                    {job.attempt_count}
                  </span>
                  <span className="col-age">
                    {job.age_seconds !== undefined ? formatAge(job.age_seconds) : '-'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      {filteredJobs.some(j => j.status === 'FAILED' && j.error_message) && (
        <section className="failed-jobs-errors">
          <h2>Failed Job Errors</h2>
          <div className="error-list">
            {filteredJobs
              .filter(j => j.status === 'FAILED' && j.error_message)
              .slice(0, 5)
              .map(job => (
                <div key={job.id} className="error-item">
                  <span className="error-job-id">Job #{job.id}</span>
                  <span className="error-job-type">{job.job_type}</span>
                  <span className="error-message">{job.error_message}</span>
                </div>
              ))}
          </div>
        </section>
      )}
    </div>
  )
}

function truncatePath(path: string, maxLength: number = 40): string {
  if (path.length <= maxLength) return path
  const parts = path.split('/')
  if (parts.length <= 2) return '...' + path.slice(-maxLength)
  return parts[0] + '/.../' + parts.slice(-2).join('/')
}

function formatAge(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  return `${Math.floor(seconds / 3600)}h`
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

export default QueueMonitor
