import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import SystemOverview from './pages/SystemOverview'
import QueueMonitor from './pages/QueueMonitor'
import ActivityFeed from './pages/ActivityFeed'
import ExtractionViewer from './pages/ExtractionViewer'
import ArtifactExplorer from './pages/ArtifactExplorer'
import TimelineView from './pages/TimelineView'
import MapView from './pages/MapView'
import EntitiesView from './pages/EntitiesView'
import RelationshipsView from './pages/RelationshipsView'
import TraceView from './pages/TraceView'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/explorer" replace />} />
        <Route path="explorer" element={<ArtifactExplorer />} />
        <Route path="trace" element={<TraceView />} />
        <Route path="timeline" element={<TimelineView />} />
        <Route path="map" element={<MapView />} />
        <Route path="entities" element={<EntitiesView />} />
        <Route path="relationships" element={<RelationshipsView />} />
        <Route path="overview" element={<SystemOverview />} />
        <Route path="queue" element={<QueueMonitor />} />
        <Route path="activity" element={<ActivityFeed />} />
        <Route path="extractions" element={<ExtractionViewer />} />
        <Route path="extractions/:id" element={<ExtractionViewer />} />
      </Route>
    </Routes>
  )
}

export default App
