/**
 * Data Explorer
 * 
 * Operational inspection tool for Librarian catalog backend.
 * Provides read-first access to inspect artifact state, validate ingestion,
 * and troubleshoot indexing without exposing database internals.
 * 
 * Architecture:
 * - Dashboard → Data Explorer → Explorer Service → Backend Adapter → Catalog Backend
 * 
 * Navigation supports:
 * - Collections (user-defined artifact groupings)
 * - Folders (filesystem-derived hierarchy)
 * - Virtual Collections (dynamic groupings based on queries)
 * - Saved Views (persistent filtered views)
 */

import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type {
  DataExplorerNavigationItem,
  DataExplorerArtifact,
  DataExplorerArtifactDetail,
} from '../types/dataExplorer'
import './DataExplorer.css'

// View mode types
type ViewMode = 'grid' | 'list'

// Sort options
type SortField = 'name' | 'size' | 'modified' | 'type'
type SortDirection = 'asc' | 'desc'

// File type icons mapping
const FILE_ICONS: Record<string, string> = {
  // Images
  '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.webp': '🖼️', '.bmp': '🖼️', '.svg': '🖼️',
  // Documents
  '.pdf': '📄', '.doc': '📄', '.docx': '📄', '.txt': '📝', '.rtf': '📝',
  // Code
  '.py': '🐍', '.js': '📜', '.ts': '📜', '.tsx': '📜', '.jsx': '📜',
  '.java': '☕', '.cpp': '⚙️', '.c': '⚙️', '.h': '⚙️', '.go': '🔧', '.rs': '🦀',
  // Data
  '.json': '📋', '.xml': '📋', '.yaml': '📝', '.yml': '📝', '.toml': '📝',
  '.csv': '📊', '.tsv': '📊',
  // Config
  '.ini': '⚙️', '.conf': '⚙️', '.cfg': '⚙️', '.env': '🔐',
  // Markup
  '.md': '📝', '.rst': '📝', '.html': '🌐', '.css': '🎨',
  // Archives
  '.zip': '📦', '.tar': '📦', '.gz': '📦', '.rar': '📦', '.7z': '📦',
  // Video
  '.mp4': '🎬', '.mov': '🎬', '.avi': '🎬', '.mkv': '🎬',
  // Audio
  '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.aac': '🎵',
  // Navigation
  collection: '📚',
  folder: '📁',
  virtual_collection: '🔮',
  saved_view: '💾',
  // Default
  default: '📄',
}

function getFileIcon(filename: string): string {
  const ext = filename.toLowerCase().match(/\.[^.]+$/)?.[0]
  return ext ? FILE_ICONS[ext] || FILE_ICONS.default : FILE_ICONS.default
}

function getNavigationIcon(type: string): string {
  return FILE_ICONS[type] || FILE_ICONS.default
}

// Format file size
function formatFileSize(bytes: number | null | undefined): string {
  if (bytes == null || bytes === 0) return '—'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// Format date
function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return '—'
  try {
    const date = new Date(isoString)
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return '—'
  }
}

// Sort artifacts
function sortArtifacts(
  artifacts: DataExplorerArtifact[],
  field: SortField,
  direction: SortDirection
): DataExplorerArtifact[] {
  return [...artifacts].sort((a, b) => {
    let comparison = 0
    switch (field) {
      case 'name':
        comparison = a.name.localeCompare(b.name)
        break
      case 'size':
        comparison = (a.size || 0) - (b.size || 0)
        break
      case 'modified':
        comparison = new Date(a.modified || 0).getTime() - new Date(b.modified || 0).getTime()
        break
      case 'type':
        comparison = (a.type || '').localeCompare(b.type || '')
        break
    }
    return direction === 'asc' ? comparison : -comparison
  })
}

function DataExplorer() {
  // Navigation state
  const [navigationItems, setNavigationItems] = useState<DataExplorerNavigationItem[]>([])
  const [selectedNavItem, setSelectedNavItem] = useState<DataExplorerNavigationItem | null>(null)
  const [navigationLoading, setNavigationLoading] = useState(true)
  const [navigationError, setNavigationError] = useState<string | null>(null)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<DataExplorerArtifact[] | null>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [isSearching, setIsSearching] = useState(false)

  // Artifacts state
  const [artifacts, setArtifacts] = useState<DataExplorerArtifact[]>([])
  const [artifactsLoading, setArtifactsLoading] = useState(false)

  // Selection state
  const [selectedArtifact, setSelectedArtifact] = useState<DataExplorerArtifact | null>(null)
  const [artifactDetail, setArtifactDetail] = useState<DataExplorerArtifactDetail | null>(null)

  // View state
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [sortField, setSortField] = useState<SortField>('name')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [filterText, setFilterText] = useState('')

  // Panel sizes for resizable panels
  const [leftPanelWidth, setLeftPanelWidth] = useState(280)
  const [rightPanelWidth, setRightPanelWidth] = useState(350)

  // Load navigation on mount
  useEffect(() => {
    loadNavigation()
  }, [])

  // Load artifacts when navigation selection changes
  useEffect(() => {
    if (selectedNavItem) {
      loadArtifacts(selectedNavItem)
    }
  }, [selectedNavItem])

  // Load artifact detail when selection changes
  useEffect(() => {
    if (selectedArtifact) {
      loadArtifactDetail(selectedArtifact.id)
    } else {
      setArtifactDetail(null)
    }
  }, [selectedArtifact])

  // Load navigation from API
  const loadNavigation = useCallback(async (parentId?: string) => {
    setNavigationLoading(true)
    setNavigationError(null)
    try {
      const data = await api.getDataExplorerNavigation(parentId)
      
      if (parentId) {
        // Loading children for an expanded folder
        return data.items
      } else {
        // Loading root navigation
        setNavigationItems(data.items)
        
        // Auto-select first item if none selected
        if (data.items.length > 0 && !selectedNavItem) {
          setSelectedNavItem(data.items[0])
        }
      }
    } catch (error) {
      console.error('Failed to load navigation:', error)
      setNavigationError('Failed to load navigation')
    } finally {
      setNavigationLoading(false)
    }
    return []
  }, [])

  // Handle folder expansion
  const handleFolderExpand = useCallback(async (item: DataExplorerNavigationItem) => {
    if (!item.has_children) return
    
    const newExpanded = new Set(expandedFolders)
    
    if (expandedFolders.has(item.id)) {
      // Collapse folder
      newExpanded.delete(item.id)
      setExpandedFolders(newExpanded)
      
      // Update item in navigationItems to mark as collapsed
      setNavigationItems(prev => updateItemInTree(prev, item.id, { expanded: false, children: [] }))
    } else {
      // Expand folder - load children
      newExpanded.add(item.id)
      setExpandedFolders(newExpanded)
      
      // Load children from API
      const children = await loadNavigation(item.id)
      
      // Update item in navigationItems with children
      setNavigationItems(prev => updateItemInTree(prev, item.id, { 
        expanded: true, 
        children: children as DataExplorerNavigationItem[] 
      }))
    }
  }, [expandedFolders, loadNavigation])

  // Helper to update item in tree
  const updateItemInTree = (
    items: DataExplorerNavigationItem[], 
    itemId: string, 
    updates: Partial<DataExplorerNavigationItem>
  ): DataExplorerNavigationItem[] => {
    return items.map(item => {
      if (item.id === itemId) {
        return { ...item, ...updates }
      }
      if (item.children && item.children.length > 0) {
        return { ...item, children: updateItemInTree(item.children, itemId, updates) }
      }
      return item
    })
  }

  // Load artifacts for selected navigation item
  const loadArtifacts = useCallback(async (navItem: DataExplorerNavigationItem) => {
    setArtifactsLoading(true)
    setArtifacts([])
    setSelectedArtifact(null)
    try {
      const data = await api.getDataExplorerArtifacts(navItem.id, navItem.type)
      setArtifacts(data.artifacts)
    } catch (error) {
      console.error('Failed to load artifacts:', error)
      setArtifacts([])
    } finally {
      setArtifactsLoading(false)
    }
  }, [])

  // Load artifact detail
  const loadArtifactDetail = useCallback(async (artifactId: number) => {
    try {
      const data = await api.getDataExplorerArtifactDetail(artifactId)
      setArtifactDetail(data.artifact)
    } catch (error) {
      console.error('Failed to load artifact detail:', error)
      setArtifactDetail(null)
    }
  }, [])

  // Handle search
  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query)
    
    if (!query.trim()) {
      setSearchResults(null)
      setIsSearching(false)
      return
    }
    
    setSearchLoading(true)
    setIsSearching(true)
    
    try {
      const results = await api.searchDataExplorerArtifacts(query)
      setSearchResults(results.artifacts)
    } catch (error) {
      console.error('Search failed:', error)
      setSearchResults([])
    } finally {
      setSearchLoading(false)
    }
  }, [])

  // Clear search
  const clearSearch = useCallback(() => {
    setSearchQuery('')
    setSearchResults(null)
    setIsSearching(false)
  }, [])

  // Get filtered and sorted artifacts
  const getDisplayArtifacts = useCallback(() => {
    // Use search results if searching, otherwise use navigation artifacts
    let sourceArtifacts = searchResults !== null ? searchResults : artifacts
    
    // Apply local filter if any
    let filtered = sourceArtifacts
    if (filterText && searchResults === null) {
      // Only apply local filter when not in search mode
      const search = filterText.toLowerCase()
      filtered = sourceArtifacts.filter(a => 
        a.name.toLowerCase().includes(search) ||
        (a.type && a.type.toLowerCase().includes(search))
      )
    }
    return sortArtifacts(filtered, sortField, sortDirection)
  }, [searchResults, artifacts, filterText, sortField, sortDirection])

  // Handle sort change
  const handleSortChange = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Render navigation item
  const renderNavigationItem = (item: DataExplorerNavigationItem, depth = 0) => {
    const isSelected = selectedNavItem?.id === item.id
    const hasChildren = item.has_children
    const isExpanded = expandedFolders.has(item.id)
    const isFolder = item.type === 'folder'
    
    return (
      <div key={item.id}>
        <div
          className={`nav-item ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${12 + depth * 16}px` }}
          onClick={() => {
            if (isFolder && hasChildren) {
              handleFolderExpand(item)
            }
            setSelectedNavItem(item)
          }}
        >
          {isFolder && hasChildren && (
            <span className={`nav-expand-icon ${isExpanded ? 'expanded' : ''}`}>
              ▶
            </span>
          )}
          {!isFolder && <span className="nav-expand-icon-spacer" />}
          <span className="nav-item-icon">{getNavigationIcon(item.type)}</span>
          <span className="nav-item-label">{item.name}</span>
        </div>
        {hasChildren && isExpanded && item.children && item.children.length > 0 && (
          <div className="nav-children">
            {item.children.map(child => renderNavigationItem(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  // Render grid view
  const renderGridView = () => {
    const displayArtifacts = getDisplayArtifacts()
    
    if (artifactsLoading) {
      return <div className="view-loading">Loading artifacts...</div>
    }
    
    if (displayArtifacts.length === 0) {
      return <div className="view-empty">No artifacts found</div>
    }

    return (
      <div className="grid-view">
        {displayArtifacts.map(artifact => (
          <div
            key={artifact.id}
            className={`grid-item ${selectedArtifact?.id === artifact.id ? 'selected' : ''}`}
            onClick={() => setSelectedArtifact(artifact)}
            data-document-id={artifact.id}
          >
            <div className="grid-item-thumbnail">
              {artifact.thumbnail ? (
                <img
                  src={artifact.thumbnail}
                  alt={artifact.name}
                  className="grid-thumbnail-img"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none'
                    const parent = (e.target as HTMLImageElement).parentElement
                    if (parent) parent.querySelector('.grid-item-icon')?.classList.remove('hidden')
                  }}
                />
              ) : null}
              <div className={`grid-item-icon ${artifact.thumbnail ? 'hidden' : ''}`}>
                {getFileIcon(artifact.name)}
              </div>
            </div>
            <div className="grid-item-name" title={artifact.name}>{artifact.name}</div>
            {artifact.type && (
              <div className="grid-item-meta">{artifact.type}</div>
            )}
          </div>
        ))}
      </div>
    )
  }

  // Render list view
  const renderListView = () => {
    const displayArtifacts = getDisplayArtifacts()
    
    if (artifactsLoading) {
      return <div className="view-loading">Loading artifacts...</div>
    }
    
    if (displayArtifacts.length === 0) {
      return <div className="view-empty">No artifacts found</div>
    }

    return (
      <div className="list-view">
        <div className="list-header">
          <div className="list-header-cell name" onClick={() => handleSortChange('name')}>
            Name {sortField === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
          </div>
          <div className="list-header-cell type" onClick={() => handleSortChange('type')}>
            Type {sortField === 'type' && (sortDirection === 'asc' ? '↑' : '↓')}
          </div>
          <div className="list-header-cell size" onClick={() => handleSortChange('size')}>
            Size {sortField === 'size' && (sortDirection === 'asc' ? '↑' : '↓')}
          </div>
          <div className="list-header-cell modified" onClick={() => handleSortChange('modified')}>
            Modified {sortField === 'modified' && (sortDirection === 'asc' ? '↑' : '↓')}
          </div>
        </div>
        <div className="list-body">
          {displayArtifacts.map(artifact => (
            <div
              key={artifact.id}
              className={`list-row ${selectedArtifact?.id === artifact.id ? 'selected' : ''}`}
              onClick={() => setSelectedArtifact(artifact)}
            >
              <div className="list-cell name">
                <span className="list-icon">{getFileIcon(artifact.name)}</span>
                <span className="list-name" title={artifact.name}>{artifact.name}</span>
              </div>
              <div className="list-cell type">{artifact.type || '—'}</div>
              <div className="list-cell size">{formatFileSize(artifact.size)}</div>
              <div className="list-cell modified">{formatDate(artifact.modified)}</div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Render descriptor-driven inspector
  const renderInspector = () => {
    if (!selectedArtifact) {
      return (
        <div className="inspector-empty">
          <span className="inspector-empty-icon">📋</span>
          <span className="inspector-empty-text">Select an artifact to inspect</span>
        </div>
      )
    }

    if (!artifactDetail) {
      return (
        <div className="inspector-loading">
          <span className="inspector-loading-text">Loading artifact details...</span>
        </div>
      )
    }

    return (
      <div className="inspector-content">
        {/* Render sections based on descriptor */}
        {artifactDetail.descriptor.sections.map((section, idx) => (
          <div key={idx} className="inspector-section">
            <div className="inspector-section-header">
              <span className="inspector-section-icon">{section.icon || '📄'}</span>
              <span className="inspector-section-title">{section.title}</span>
            </div>
            <div className="inspector-section-content">
              {section.fields.map((field, fieldIdx) => (
                <div key={fieldIdx} className="inspector-field">
                  <span className="inspector-field-label">{field.label}</span>
                  <span className="inspector-field-value" title={String(field.value || '—')}>
                    {field.value !== undefined ? String(field.value) : '—'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Build breadcrumb path
  const getBreadcrumbPath = () => {
    const parts: string[] = []
    if (selectedNavItem) {
      let current: DataExplorerNavigationItem | undefined = selectedNavItem
      while (current) {
        parts.unshift(current.name)
        current = navigationItems.find(i => i.id === current?.parent_id)
      }
    }
    return parts
  }

  return (
    <div className="data-explorer">
      <div className="explorer-container">
        {/* Left Panel - Navigation */}
        <div className="explorer-left-pane" style={{ width: leftPanelWidth }}>
          <div className="pane-header">
            <span className="pane-title">{isSearching ? 'Search Results' : 'Collections'}</span>
            <button className="pane-action" onClick={() => loadNavigation()} title="Refresh">
              ↻
            </button>
          </div>
          <div className="nav-search">
            <input
              type="text"
              className="nav-search-input"
              placeholder="Search artifacts..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  clearSearch()
                }
              }}
            />
            {searchQuery && (
              <button className="nav-search-clear" onClick={clearSearch} title="Clear search">
                ×
              </button>
            )}
          </div>
          {isSearching ? (
            <div className="navigation-tree">
              {searchLoading ? (
                <div className="nav-loading">Searching...</div>
              ) : searchResults && searchResults.length > 0 ? (
                <div className="nav-search-results">
                  <div className="nav-search-info">
                    Found {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
                  </div>
                  {searchResults.slice(0, 50).map((artifact) => (
                    <div
                      key={artifact.id}
                      className={`nav-item nav-search-item ${selectedArtifact?.id === artifact.id ? 'selected' : ''}`}
                      onClick={() => setSelectedArtifact(artifact)}
                    >
                      <span className="nav-item-icon">{getFileIcon(artifact.name)}</span>
                      <span className="nav-item-label">{artifact.name}</span>
                    </div>
                  ))}
                  {searchResults.length > 50 && (
                    <div className="nav-search-more">
                      Showing 50 of {searchResults.length} results
                    </div>
                  )}
                </div>
              ) : (
                <div className="nav-empty">No results found</div>
              )}
            </div>
          ) : (
            <div className="navigation-tree">
              {navigationLoading && navigationItems.length === 0 ? (
                <div className="nav-loading">Loading...</div>
              ) : navigationError ? (
                <div className="nav-error">{navigationError}</div>
              ) : (
                navigationItems.map(item => renderNavigationItem(item))
              )}
            </div>
          )}
        </div>

        {/* Left Resize Handle */}
        <div
          className="resize-handle resize-handle-left"
          onMouseDown={(e) => {
            const startX = e.clientX
            const startWidth = leftPanelWidth
            const onMouseMove = (e: MouseEvent) => {
              const delta = e.clientX - startX
              setLeftPanelWidth(Math.max(200, Math.min(500, startWidth + delta)))
            }
            const onMouseUp = () => {
              document.removeEventListener('mousemove', onMouseMove)
              document.removeEventListener('mouseup', onMouseUp)
            }
            document.addEventListener('mousemove', onMouseMove)
            document.addEventListener('mouseup', onMouseUp)
          }}
        />

        {/* Center Panel - Artifacts View */}
        <div className="explorer-center-pane">
          <div className="view-header">
            <div className="breadcrumb">
              {getBreadcrumbPath().map((part, i) => (
                <span key={i}>
                  <span className="breadcrumb-sep">/</span>
                  <span className="breadcrumb-part">{part}</span>
                </span>
              ))}
            </div>
            <div className="view-controls">
              <input
                type="text"
                className="filter-input"
                placeholder="Filter artifacts..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
              />
              <div className="view-switcher">
                <button
                  className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                  onClick={() => setViewMode('grid')}
                  title="Grid view"
                >
                  ☷
                </button>
                <button
                  className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
                  onClick={() => setViewMode('list')}
                  title="List view"
                >
                  ☰
                </button>
              </div>
            </div>
          </div>

          <div className="view-content">
            {viewMode === 'grid' && renderGridView()}
            {viewMode === 'list' && renderListView()}
          </div>

          <div className="view-footer">
            <span className="item-count">
              {getDisplayArtifacts().length} items
            </span>
            {selectedArtifact && (
              <span className="selected-info">
                {getFileIcon(selectedArtifact.name)} {selectedArtifact.name}
              </span>
            )}
          </div>
        </div>

        {/* Right Resize Handle */}
        <div
          className="resize-handle resize-handle-right"
          onMouseDown={(e) => {
            const startX = e.clientX
            const startWidth = rightPanelWidth
            const onMouseMove = (e: MouseEvent) => {
              const delta = startX - e.clientX
              setRightPanelWidth(Math.max(250, Math.min(600, startWidth + delta)))
            }
            const onMouseUp = () => {
              document.removeEventListener('mousemove', onMouseMove)
              document.removeEventListener('mouseup', onMouseUp)
            }
            document.addEventListener('mousemove', onMouseMove)
            document.addEventListener('mouseup', onMouseUp)
          }}
        />

        {/* Right Panel - Inspector */}
        <div className="explorer-right-pane" style={{ width: rightPanelWidth }}>
          <div className="pane-header">
            <span className="pane-title">Inspector</span>
          </div>
          <div className="pane-content inspector">
            {renderInspector()}
          </div>
        </div>
      </div>
    </div>
  )
}

export default DataExplorer
