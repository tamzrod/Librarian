/**
 * @deprecated Use TraceView with view="timeline" parameter instead.
 * Routes: /trace?view=timeline
 * 
 * Legacy placeholder retained for backwards compatibility with existing bookmarks.
 * Will be removed in a future version.
 */
import { Navigate } from 'react-router-dom'

function TimelineView() {
  return <Navigate to="/trace?view=timeline" replace />
}

export default TimelineView
