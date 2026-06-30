import { Outlet, NavLink } from 'react-router-dom'
import { useApiStatus } from '../hooks/useApiStatus'
import BuildInfo from './BuildInfo'
import './Layout.css'

const navItems = [
  { path: '/overview', label: 'System Overview', icon: '📊' },
  { path: '/queue', label: 'Queue Monitor', icon: '📋' },
  { path: '/activity', label: 'Activity Feed', icon: '📜' },
  { path: '/documents', label: 'Document Journey', icon: '📄' },
  { path: '/extractions', label: 'Extraction Viewer', icon: '🔍' },
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
          <span className="api-version">API v1.0</span>
        </div>
      </header>
      <div className="main-container">
        <nav className="sidebar">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
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
