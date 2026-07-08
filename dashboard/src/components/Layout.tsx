import { Outlet, NavLink } from 'react-router-dom'
import { useApiStatus } from '../hooks/useApiStatus'
import BuildInfo from './BuildInfo'
import './Layout.css'

const investigationItems = [
  { path: '/explorer', label: 'Explorer', icon: '🔍' },
  { path: '/data-explorer', label: 'Data Explorer', icon: '🗂️' },
  { path: '/trace', label: 'Trace', icon: '🧭' },
  // Legacy routes /timeline and /map are deprecated - use /trace with view parameter instead
  { path: '/entities', label: 'Entities', icon: '🏷️' },
  { path: '/relationships', label: 'Relationships', icon: '🔗' },
]

const operationsItems = [
  { path: '/overview', label: 'Overview', icon: '📊' },
  { path: '/queue', label: 'Queue', icon: '📋' },
  { path: '/activity', label: 'Activity', icon: '📜' },
  { path: '/extractions', label: 'Extraction', icon: '🔎' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
]

function Layout() {
  const { data: status } = useApiStatus()

  const getStatusColor = () => {
    if (!status) return 'var(--text-muted)'
    return status.status === 'healthy' ? 'var(--accent-success)' : 'var(--accent-warning)'
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">📚</span>
            <span className="logo-text">Librarian</span>
          </div>
          <span className="status-indicator" style={{ backgroundColor: getStatusColor() }} />
          <span className="status-text">{status ? status.status.charAt(0).toUpperCase() + status.status.slice(1) : 'Connecting...'}</span>
        </div>
        <div className="header-right">
          <span className="workspace-label">Investigation Workspace</span>
          <span className="api-version">API v1.0</span>
        </div>
      </header>
      <div className="main-container">
        <nav className="sidebar">
          <div className="nav-section">
            <span className="nav-section-label">Investigation</span>
            {investigationItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
              </NavLink>
            ))}
          </div>
          <div className="nav-section">
            <span className="nav-section-label">Operations</span>
            {operationsItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
        <main className="content">
          <Outlet />
        </main>
      </div>
      <BuildInfo />
    </div>
  )
}

export default Layout
