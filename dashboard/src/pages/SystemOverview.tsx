import { useSystemStats } from '../hooks/useSystemStats'
import StatsCard from '../components/StatsCard'
import StatusBadge from '../components/StatusBadge'
import ChartCard from '../components/ChartCard'
import QueueDepthChart from '../components/charts/QueueDepthChart'
import './SystemOverview.css'

function SystemOverview() {
  const { data, loading, error, refetch } = useSystemStats(5000)
  const { overview, stats, documentStatus } = data

  if (loading && !overview) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <span>Loading system overview...</span>
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

  const totalDocuments = documentStatus?.total || 0
  const documentStatusCounts = documentStatus?.status_counts || {}

  return (
    <div className="system-overview">
      <header className="page-header">
        <h1>System Overview</h1>
        <StatusBadge
          status={stats?.database.connected ? 'healthy' : 'degraded'}
          label={stats?.database.connected ? 'Database Connected' : 'Database Disconnected'}
        />
      </header>

      <section className="stats-grid">
        <StatsCard
          title="Files"
          value={overview?.files || 0}
          icon="📁"
          color="var(--accent-info)"
        />
        <StatsCard
          title="Documents"
          value={overview?.documents || 0}
          icon="📄"
          color="var(--accent-primary)"
        />
        <StatsCard
          title="Directories"
          value={overview?.directories || 0}
          icon="📂"
          color="var(--accent-secondary)"
        />
        <StatsCard
          title="Storage Used"
          value={overview?.storage_used_bytes || 0}
          icon="💾"
          color="var(--accent-warning)"
          format="bytes"
        />
        <StatsCard
          title="Entities"
          value={overview?.entities || 0}
          icon="🏷️"
          color="var(--accent-success)"
        />
        <StatsCard
          title="Relationships"
          value={overview?.relationships || 0}
          icon="🔗"
          color="var(--accent-info)"
        />
        <StatsCard
          title="Events"
          value={overview?.events || 0}
          icon="📅"
          color="var(--accent-secondary)"
        />
        <StatsCard
          title="Locations"
          value={overview?.locations || 0}
          icon="📍"
          color="var(--accent-warning)"
        />
        <StatsCard
          title="Embeddings"
          value={overview?.embeddings || 0}
          icon="🧮"
          color="var(--accent-primary)"
        />
      </section>

      <section className="pipeline-section">
        <h2>Pipeline Status</h2>
        <div className="pipeline-grid">
          <StatsCard
            title="Workers"
            value={overview?.workers || 0}
            icon="👷"
            color="var(--accent-success)"
          />
          <StatsCard
            title="Queue Depth"
            value={overview?.queued_jobs || 0}
            icon="📋"
            color="var(--accent-warning)"
            trend={overview?.queued_jobs && overview.queued_jobs > 10 ? 'up' : undefined}
          />
          <StatsCard
            title="Running Jobs"
            value={overview?.running_jobs || 0}
            icon="⚡"
            color="var(--accent-info)"
          />
          <StatsCard
            title="Failed Jobs"
            value={overview?.failed_jobs || 0}
            icon="❌"
            color="var(--accent-danger)"
          />
        </div>
      </section>

      <section className="document-status-section">
        <h2>Document Processing Status</h2>
        <div className="status-bars">
          {Object.entries(documentStatusCounts).map(([status, count]) => (
            <div key={status} className="status-bar-item">
              <div className="status-bar-label">
                <span>{status}</span>
                <span className="status-bar-count">{count as number}</span>
              </div>
              <div className="status-bar-track">
                <div
                  className="status-bar-fill"
                  style={{
                    width: `${totalDocuments > 0 ? ((count as number) / totalDocuments) * 100 : 0}%`,
                    backgroundColor: getStatusColor(status),
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="charts-section">
        <ChartCard title="Queue Depth History" className="chart-card-wide">
          <QueueDepthChart />
        </ChartCard>
      </section>

      <section className="services-section">
        <h2>Service Status</h2>
        <div className="services-grid">
          <div className="service-item">
            <span className="service-icon">🗄️</span>
            <span className="service-name">Database</span>
            <StatusBadge
              status={stats?.database.connected ? 'healthy' : 'degraded'}
              label={stats?.database.connected ? 'Connected' : 'Disconnected'}
            />
          </div>
          <div className="service-item">
            <span className="service-icon">👁️</span>
            <span className="service-name">Watcher</span>
            <StatusBadge
              status={stats?.watcher.active ? 'healthy' : 'inactive'}
              label={stats?.watcher.active ? 'Active' : 'Inactive'}
            />
          </div>
          <div className="service-item">
            <span className="service-icon">⚙️</span>
            <span className="service-name">Job Processor</span>
            <StatusBadge
              status={stats?.watcher.active ? 'healthy' : 'inactive'}
              label={stats?.watcher.active ? 'Active' : 'Inactive'}
            />
          </div>
          <div className="service-item">
            <span className="service-icon">🌐</span>
            <span className="service-name">API</span>
            <StatusBadge status="healthy" label="Operational" />
          </div>
        </div>
      </section>

      <section className="meta-section">
        <h2>System Information</h2>
        <dl className="meta-list">
          <div className="meta-item">
            <dt>Library Root</dt>
            <dd><code>{stats?.library_root || '/library'}</code></dd>
          </div>
          <div className="meta-item">
            <dt>Initial Scan</dt>
            <dd>{stats?.initial_scan_complete ? 'Complete' : 'In Progress'}</dd>
          </div>
          <div className="meta-item">
            <dt>Last Scan</dt>
            <dd>{stats?.watcher.last_scan || 'Never'}</dd>
          </div>
          <div className="meta-item">
            <dt>Supported Parssers</dt>
            <dd>{stats?.parsers.count || 0} ({stats?.parsers.types?.join(', ')})</dd>
          </div>
        </dl>
      </section>
    </div>
  )
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    DISCOVERED: '#6366f1',
    METADATA_INDEXED: '#8b5cf6',
    CONTENT_EXTRACTED: '#a855f7',
    ENTITY_EXTRACTED: '#d946ef',
    RELATIONSHIPS_BUILT: '#ec4899',
    EMBEDDED: '#f43f5e',
    COMPLETE: '#22c55e',
    FAILED: '#ef4444',
  }
  return colors[status] || '#64748b'
}

export default SystemOverview
