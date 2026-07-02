/**
 * @deprecated Use TraceView with view="map" parameter instead.
 * Routes: /trace?view=map
 * 
 * Legacy placeholder retained for backwards compatibility with existing bookmarks.
 * Will be removed in a future version.
 */
import { Navigate } from 'react-router-dom'

function MapView() {
  return <Navigate to="/trace?view=map" replace />
}

export default MapView
