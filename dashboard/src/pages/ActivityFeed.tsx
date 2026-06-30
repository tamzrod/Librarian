import { useActivityFeed } from '../hooks/useActivityFeed'
import './ActivityFeed.css'

function ActivityFeed() {
  const { events, loading, error, clearEvents } = useActivityFeed(100, true, 3000)

  if (loading && events.length === 0) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <span>Loading activity feed...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page-error">
        <span className="error-icon">⚠️</span>
        <span>{error.message}</span>
      </div>
    )
  }

  return (
    <div className="activity-feed">
      <header className="page-header">
        <h1>Activity Feed</h1>
        <div className="header-actions">
          <span className="event-count">{events.length} events</span>
          <button className="clear-btn" onClick={clearEvents}>Clear</button>
        </div>
      </header>

      <div className="feed-container">
        <div className="feed-header">
          <span className="feed-col-timestamp">Timestamp</span>
          <span className="feed-col-level">Level</span>
          <span className="feed-col-message">Message</span>
        </div>
        <div className="feed-body">
          {events.length === 0 ? (
            <div className="feed-empty">
              <span>No activity yet</span>
              <span className="feed-empty-hint">Events will appear here as they occur</span>
            </div>
          ) : (
            events.map((event, index) => (
              <div
                key={`${event.timestamp}-${index}`}
                className={`feed-row level-${event.level}`}
              >
                <span className="feed-col-timestamp">
                  <code>{formatTimestamp(event.timestamp)}</code>
                </span>
                <span className="feed-col-level">
                  <span className={`level-badge level-${event.level}`}>
                    {event.level.toUpperCase()}
                  </span>
                </span>
                <span className="feed-col-message">
                  <span className="message-text">{event.message}</span>
                  {event.details && (
                    <span className="message-details" title={JSON.stringify(event.details, null, 2)}>
                      ℹ️
                    </span>
                  )}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="feed-legend">
        <span className="legend-item">
          <span className="level-badge level-info">INFO</span>
          Normal operations
        </span>
        <span className="legend-item">
          <span className="level-badge level-warning">WARN</span>
          Attention needed
        </span>
        <span className="legend-item">
          <span className="level-badge level-error">ERROR</span>
          Action required
        </span>
      </div>
    </div>
  )
}

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }) + '.' + String(date.getMilliseconds()).padStart(3, '0')
}

export default ActivityFeed
