import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type { PluginInfo } from '../types/api'
import './Settings.css'

// Category display names
const CATEGORY_LABELS: Record<string, string> = {
  metadata: 'Metadata',
  vision: 'Vision',
  audio: 'Audio',
  embeddings: 'Embeddings',
  general: 'General',
}

// Category icons
const CATEGORY_ICONS: Record<string, string> = {
  metadata: '📷',
  vision: '👁️',
  audio: '🎧',
  embeddings: '🔢',
  general: '⚙️',
}

function Settings() {
  const [plugins, setPlugins] = useState<PluginInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState<string | null>(null)

  const fetchPlugins = useCallback(async () => {
    try {
      setError(null)
      const response = await api.getPlugins()
      setPlugins(response.plugins)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load plugins')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPlugins()
  }, [fetchPlugins])

  const handleToggle = async (pluginName: string, currentEnabled: boolean) => {
    setUpdating(pluginName)
    try {
      await api.updatePlugin(pluginName, !currentEnabled)
      // Update local state
      setPlugins(plugins.map(p =>
        p.name === pluginName ? { ...p, enabled: !currentEnabled } : p
      ))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update plugin')
    } finally {
      setUpdating(null)
    }
  }

  // Group plugins by category
  const pluginsByCategory = plugins.reduce((acc, plugin) => {
    const category = plugin.category || 'general'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(plugin)
    return acc
  }, {} as Record<string, PluginInfo[]>)

  // Sort categories
  const sortedCategories = Object.keys(pluginsByCategory).sort((a, b) => {
    // metadata first, then alphabetically
    if (a === 'metadata') return -1
    if (b === 'metadata') return 1
    return a.localeCompare(b)
  })

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <span>Loading settings...</span>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <header className="page-header">
        <h1>Settings</h1>
        <button className="refresh-btn" onClick={fetchPlugins}>Refresh</button>
      </header>

      {error && (
        <div className="settings-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
          <button onClick={fetchPlugins}>Retry</button>
        </div>
      )}

      <section className="settings-section">
        <h2>Plugins</h2>
        <p className="section-description">
          Configure which plugins are enabled for processing. Changes take effect immediately
          for new files. Restart may be required for existing jobs.
        </p>

        {plugins.length === 0 ? (
          <div className="no-plugins">
            No plugins installed.
          </div>
        ) : (
          <div className="plugin-categories">
            {sortedCategories.map(category => (
              <div key={category} className="plugin-category">
                <h3 className="category-header">
                  <span className="category-icon">{CATEGORY_ICONS[category] || '⚙️'}</span>
                  <span className="category-label">{CATEGORY_LABELS[category] || category}</span>
                </h3>
                <div className="plugin-list">
                  {pluginsByCategory[category].map(plugin => (
                    <div key={plugin.name} className="plugin-item">
                      <div className="plugin-info">
                        <div className="plugin-header">
                          <span className="plugin-name">
                            {formatPluginName(plugin.name)}
                          </span>
                          {plugin.enabled && (
                            <span className="plugin-badge enabled">Enabled</span>
                          )}
                          {!plugin.enabled && (
                            <span className="plugin-badge disabled">Disabled</span>
                          )}
                        </div>
                        <p className="plugin-description">{plugin.description}</p>
                        <span className="plugin-job-type">Job type: {plugin.job_type}</span>
                      </div>
                      <div className="plugin-controls">
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={plugin.enabled}
                            onChange={() => handleToggle(plugin.name, plugin.enabled)}
                            disabled={updating === plugin.name}
                          />
                          <span className="toggle-slider"></span>
                        </label>
                        {updating === plugin.name && (
                          <div className="spinner-small" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="settings-section">
        <h3>Plugin Information</h3>
        <div className="plugin-summary">
          <div className="summary-item">
            <span className="summary-value">{plugins.length}</span>
            <span className="summary-label">Total Plugins</span>
          </div>
          <div className="summary-item">
            <span className="summary-value">{plugins.filter(p => p.enabled).length}</span>
            <span className="summary-label">Enabled</span>
          </div>
          <div className="summary-item">
            <span className="summary-value">{plugins.filter(p => !p.enabled).length}</span>
            <span className="summary-label">Disabled</span>
          </div>
        </div>
      </section>
    </div>
  )
}

function formatPluginName(name: string): string {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export default Settings
