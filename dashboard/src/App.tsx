import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import SystemOverview from './pages/SystemOverview'
import QueueMonitor from './pages/QueueMonitor'
import ActivityFeed from './pages/ActivityFeed'
import DocumentJourney from './pages/DocumentJourney'
import ExtractionViewer from './pages/ExtractionViewer'
import EvidenceTimeline from './pages/EvidenceTimeline'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<SystemOverview />} />
        <Route path="queue" element={<QueueMonitor />} />
        <Route path="activity" element={<ActivityFeed />} />
        <Route path="documents" element={<DocumentJourney />} />
        <Route path="documents/:id" element={<DocumentJourney />} />
        <Route path="extractions" element={<ExtractionViewer />} />
        <Route path="extractions/:id" element={<ExtractionViewer />} />
        <Route path="timeline" element={<EvidenceTimeline />} />
      </Route>
    </Routes>
  )
}

export default App
