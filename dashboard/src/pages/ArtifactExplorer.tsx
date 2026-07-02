import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import type { FolderNode, ExplorerDocument, DocumentDetail } from '../types/api'
import './ArtifactExplorer.css'

// View mode types
type ViewMode = 'grid' | 'list' | 'preview'

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
  // Default
  folder: '📁',
}

function getFileIcon(filename: string, isFolder = false): string {
  if (isFolder) return FILE_ICONS.folder
  const ext = filename.toLowerCase().match(/\.[^.]+$/)?.[0]
  return ext ? FILE_ICONS[ext] || '📄' : '📄'
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

// Tree node for folder tree
interface TreeNode {
  folder: FolderNode
  expanded: boolean
  loaded: boolean
  children: TreeNode[]
}

// E5: Grid item component that displays thumbnail when available
interface GridDocumentItemProps {
  doc: ExplorerDocument
  isSelected: boolean
  onClick: () => void
  documentDetail: DocumentDetail | null
}

function GridDocumentItem({ doc, isSelected, onClick, documentDetail }: GridDocumentItemProps) {
  const thumbnailUrl = documentDetail?.thumbnail_path 
    ? api.getThumbnailUrl(documentDetail.thumbnail_path) 
    : null
  
  const isImage = api.isImagePreviewable(doc.extension)

  return (
    <div
      className={`grid-item ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="grid-item-thumbnail">
        {thumbnailUrl && isImage ? (
          <img 
            src={thumbnailUrl} 
            alt={doc.name}
            className="grid-thumbnail-img"
            onError={(e) => {
              // Fall back to icon on error
              (e.target as HTMLImageElement).style.display = 'none'
              const parent = (e.target as HTMLImageElement).parentElement
              if (parent) parent.querySelector('.grid-item-icon')?.classList.remove('hidden')
            }}
          />
        ) : null}
        <div className={`grid-item-icon ${thumbnailUrl && isImage ? 'hidden' : ''}`}>
          {getFileIcon(doc.name)}
        </div>
      </div>
      <div className="grid-item-name">{doc.name}</div>
      {doc.extension && (
        <div className="grid-item-meta">{doc.extension.replace('.', '').toUpperCase()}</div>
      )}
    </div>
  )
}

function ArtifactExplorer() {
  // State
  const [tree, setTree] = useState<TreeNode[]>([])
  const [selectedFolder, setSelectedFolder] = useState<string>('/library')
  const [folderContents, setFolderContents] = useState<{ folders: FolderNode[], documents: ExplorerDocument[] }>({
    folders: [],
    documents: [],
  })
  const [selectedDocument, setSelectedDocument] = useState<ExplorerDocument | null>(null)
  const [documentDetail, setDocumentDetail] = useState<DocumentDetail | null>(null)
  const [documentThumbnailCache, setDocumentThumbnailCache] = useState<Record<number, DocumentDetail | null>>({})
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Preview state
  const [previewContent, setPreviewContent] = useState<{
    type: 'image' | 'text' | 'unsupported' | 'loading' | null
    data?: string
  } | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  // Load folder tree on mount
  useEffect(() => {
    loadFolderTree()
  }, [])

  // Load folder contents when selected folder changes
  useEffect(() => {
    if (selectedFolder) {
      loadFolderContents(selectedFolder)
    }
  }, [selectedFolder])

  // Load thumbnail cache when folder contents change (for grid view thumbnails)
  useEffect(() => {
    if (viewMode === 'grid' && folderContents.documents.length > 0) {
      loadDocumentThumbnailCache(folderContents.documents)
    }
  }, [folderContents.documents, viewMode])

  // Load document details when selected document changes
  useEffect(() => {
    if (selectedDocument) {
      loadDocumentDetails(selectedDocument.id)
    } else {
      setDocumentDetail(null)
    }
  }, [selectedDocument])

  // Load preview when document is selected and view mode is preview
  useEffect(() => {
    if (selectedDocument && viewMode === 'preview') {
      loadPreview(selectedDocument)
    } else {
      setPreviewContent(null)
    }
  }, [selectedDocument, viewMode])

  const loadFolderTree = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.getFolderTree()
      
      // Build tree structure from root
      const rootNode: TreeNode = {
        folder: response.root,
        expanded: false,
        loaded: false,
        children: [],
      }
      
      setTree([rootNode])
    } catch (err) {
      console.error('Failed to load folder tree:', err)
      setError('Failed to load folder tree')
      // Fallback to empty tree
      setTree([])
    } finally {
      setLoading(false)
    }
  }

  const loadFolderContents = async (folderPath: string) => {
    try {
      const response = await api.getFolderContents(folderPath)
      setFolderContents({
        folders: response.folders,
        documents: response.documents,
      })
    } catch (err) {
      console.error('Failed to load folder contents:', err)
      setFolderContents({ folders: [], documents: [] })
    }
  }

  const loadDocumentDetails = async (documentId: number) => {
    try {
      const response = await api.getDocumentDetails(documentId)
      setDocumentDetail(response.document)
    } catch (err) {
      console.error('Failed to load document details:', err)
      setDocumentDetail(null)
    }
  }

  // Load thumbnail details for all documents in grid view (for E5 thumbnails)
  const loadDocumentThumbnailCache = async (documents: ExplorerDocument[]) => {
    // Load thumbnails in parallel, but only if we don't have them cached
    const uncachedDocs = documents.filter(doc => documentThumbnailCache[doc.id] === undefined)
    if (uncachedDocs.length === 0) return

    try {
      const results = await Promise.allSettled(
        uncachedDocs.slice(0, 100).map(async (doc) => {
          const response = await api.getDocumentDetails(doc.id)
          return { id: doc.id, detail: response.document }
        })
      )

      setDocumentThumbnailCache(prev => {
        const updated = { ...prev }
        results.forEach(result => {
          if (result.status === 'fulfilled') {
            updated[result.value.id] = result.value.detail
          }
        })
        return updated
      })
    } catch (err) {
      console.error('Failed to load thumbnail cache:', err)
    }
  }

  // Load preview for a document
  const loadPreview = async (doc: ExplorerDocument) => {
    setPreviewLoading(true)
    setPreviewContent({ type: 'loading' })
    
    try {
      const ext = doc.extension?.toLowerCase()
      
      // Check if it's an image
      if (api.isImagePreviewable(ext)) {
        // For images, set the URL directly
        const previewUrl = api.getPreviewUrl(doc.id)
        setPreviewContent({ type: 'image', data: previewUrl })
      }
      // Check if it's text
      else if (api.isTextPreviewable(ext)) {
        // For text, fetch the content
        const previewUrl = api.getPreviewUrl(doc.id)
        const response = await fetch(previewUrl)
        if (response.ok) {
          const text = await response.text()
          setPreviewContent({ type: 'text', data: text })
        } else {
          setPreviewContent({ type: 'unsupported' })
        }
      }
      // Unsupported
      else {
        setPreviewContent({ type: 'unsupported' })
      }
    } catch (err) {
      console.error('Failed to load preview:', err)
      setPreviewContent({ type: 'unsupported' })
    } finally {
      setPreviewLoading(false)
    }
  }

  // Toggle folder expansion and load children
  const toggleFolder = useCallback(async (node: TreeNode) => {
    const toggleInTree = (nodes: TreeNode[]): TreeNode[] => {
      return nodes.map(n => {
        if (n.folder.id === node.folder.id) {
          const newExpanded = !n.expanded
          // Load children if expanding for the first time
          if (newExpanded && !n.loaded) {
            // Load children asynchronously
            api.getFolderContents(n.folder.path).then(response => {
              setTree(prev => updateNodeInTree(prev, n.folder.id, {
                children: response.folders.map(f => ({
                  folder: f,
                  expanded: false,
                  loaded: false,
                  children: [],
                })),
                loaded: true,
              }))
            }).catch(() => {})
          }
          return { ...n, expanded: newExpanded }
        }
        if (n.children.length > 0) {
          return { ...n, children: toggleInTree(n.children) }
        }
        return n
      })
    }
    setTree(prev => toggleInTree(prev))
  }, [])

  // Helper to update a node in tree
  const updateNodeInTree = (nodes: TreeNode[], id: string, update: Partial<TreeNode>): TreeNode[] => {
    return nodes.map(n => {
      if (n.folder.id === id) {
        return { ...n, ...update }
      }
      if (n.children.length > 0) {
        return { ...n, children: updateNodeInTree(n.children, id, update) }
      }
      return n
    })
  }

  // Select a folder in the tree
  const selectFolder = useCallback((folderPath: string) => {
    setSelectedFolder(folderPath)
    setSelectedDocument(null)
  }, [])

  // Select a document
  const selectDocument = useCallback((doc: ExplorerDocument) => {
    setSelectedDocument(doc)
  }, [])

  // Render folder tree node
  const renderTreeNode = (node: TreeNode, level = 0): JSX.Element => {
    const isSelected = selectedFolder === node.folder.path
    return (
      <div key={node.folder.id} className="tree-node-wrapper">
        <div
          className={`tree-node ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${0.75 + level * 1}rem` }}
          onClick={() => {
            toggleFolder(node)
            selectFolder(node.folder.path)
          }}
        >
          <span className="tree-expand">
            {node.folder.has_children ? (node.expanded ? '▼' : '▶') : ''}
          </span>
          <span className="tree-icon">{getFileIcon('', true)}</span>
          <span className="tree-label">{node.folder.name}</span>
        </div>
        {node.expanded && node.children.length > 0 && (
          <div className="tree-children">
            {node.children.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  // Render Grid View
  const renderGridView = () => (
    <div className="view-grid">
      {/* Folders first */}
      {folderContents.folders.map(folder => (
        <div
          key={folder.id}
          className={`grid-item folder-item ${selectedFolder === folder.path ? 'selected' : ''}`}
          onClick={() => selectFolder(folder.path)}
        >
          <div className="grid-item-icon">{getFileIcon('', true)}</div>
          <div className="grid-item-name">{folder.name}</div>
        </div>
      ))}
      {/* Documents */}
      {folderContents.documents.map(doc => (
        <GridDocumentItem
          key={doc.id}
          doc={doc}
          isSelected={selectedDocument?.id === doc.id}
          onClick={() => selectDocument(doc)}
          documentDetail={documentThumbnailCache[doc.id] ?? null}
        />
      ))}
      {folderContents.folders.length === 0 && folderContents.documents.length === 0 && (
        <div className="view-empty">
          <span className="view-empty-icon">📂</span>
          <span>This folder is empty</span>
        </div>
      )}
    </div>
  )

  // Render List View
  const renderListView = () => (
    <div className="view-list">
      <div className="list-header">
        <span className="list-col-icon"></span>
        <span className="list-col-name">Name</span>
        <span className="list-col-size">Size</span>
        <span className="list-col-modified">Modified</span>
      </div>
      <div className="list-body">
        {/* Folders */}
        {folderContents.folders.map(folder => (
          <div
            key={folder.id}
            className={`list-row folder-row ${selectedFolder === folder.path ? 'selected' : ''}`}
            onClick={() => selectFolder(folder.path)}
          >
            <span className="list-col-icon">{getFileIcon('', true)}</span>
            <span className="list-col-name">
              <span className="name-text">{folder.name}</span>
              <span className="folder-badge">Folder</span>
            </span>
            <span className="list-col-size">—</span>
            <span className="list-col-modified">—</span>
          </div>
        ))}
        {/* Documents */}
        {folderContents.documents.map(doc => (
          <div
            key={doc.id}
            className={`list-row ${selectedDocument?.id === doc.id ? 'selected' : ''}`}
            onClick={() => selectDocument(doc)}
          >
            <span className="list-col-icon">{getFileIcon(doc.name)}</span>
            <span className="list-col-name">
              <span className="name-text">{doc.name}</span>
            </span>
            <span className="list-col-size">{formatFileSize(doc.file_size)}</span>
            <span className="list-col-modified">{formatDate(doc.modified_time)}</span>
          </div>
        ))}
        {folderContents.folders.length === 0 && folderContents.documents.length === 0 && (
          <div className="list-empty">This folder is empty</div>
        )}
      </div>
    </div>
  )

  // Render Preview View
  const renderPreviewView = () => {
    if (!selectedDocument) {
      return (
        <div className="preview-placeholder">
          <span className="preview-placeholder-icon">👁️</span>
          <span className="preview-placeholder-text">Select an artifact to preview</span>
        </div>
      )
    }

    // Show loading state
    if (previewLoading) {
      return (
        <div className="preview-content-area">
          <div className="preview-type-badge">
            {getFileIcon(selectedDocument.name)} {selectedDocument.extension?.replace('.', '').toUpperCase() || 'FILE'}
          </div>
          <div className="preview-loading">
            <span className="preview-loading-spinner">⏳</span>
            <span>Loading preview...</span>
          </div>
        </div>
      )
    }

    // Show preview content
    if (previewContent?.type === 'image' && previewContent.data) {
      return (
        <div className="preview-content-area preview-image-container">
          <div className="preview-type-badge">
            {getFileIcon(selectedDocument.name)} {selectedDocument.extension?.replace('.', '').toUpperCase() || 'FILE'}
          </div>
          <div className="preview-image-wrapper">
            <img 
              src={previewContent.data} 
              alt={selectedDocument.name}
              className="preview-image"
            />
          </div>
        </div>
      )
    }

    if (previewContent?.type === 'text' && previewContent.data) {
      return (
        <div className="preview-content-area preview-text-container">
          <div className="preview-type-badge">
            {getFileIcon(selectedDocument.name)} {selectedDocument.extension?.replace('.', '').toUpperCase() || 'FILE'}
          </div>
          <pre className="preview-text">{previewContent.data}</pre>
        </div>
      )
    }

    // Unsupported or no preview
    const ext = selectedDocument.extension?.toLowerCase()
    const isPdf = ext === '.pdf'

    return (
      <div className="preview-content-area">
        <div className="preview-type-badge">
          {getFileIcon(selectedDocument.name)} {selectedDocument.extension?.replace('.', '').toUpperCase() || 'FILE'}
        </div>
        <div className="preview-placeholder">
          <span className="preview-placeholder-icon">👁️</span>
          <span className="preview-placeholder-text">
            {isPdf ? 'PDF preview coming soon' : 'No preview available'}
          </span>
          <span className="preview-placeholder-filename">{selectedDocument.name}</span>
        </div>
      </div>
    )
  }

  // Render processing status badge
  const renderProcessingBadge = (status: string) => {
    const statusClass = status.toLowerCase().replace('_', '-')
    let icon = '⚙️'
    let text = status
    
    switch (status) {
      case 'COMPLETED':
        icon = '✓'
        text = 'Done'
        break
      case 'IN_PROGRESS':
        icon = '⟳'
        text = 'Running'
        break
      case 'QUEUED':
        icon = '⏳'
        text = 'Pending'
        break
      case 'FAILED':
      case 'FAILED_PERMANENT':
        icon = '⚠'
        text = 'Failed'
        break
      case 'CANCELLED':
        icon = '✗'
        text = 'Cancelled'
        break
    }
    
    return (
      <span className={`processing-badge ${statusClass}`}>
        <span className="processing-badge-icon">{icon}</span>
        <span className="processing-badge-text">{text}</span>
      </span>
    )
  }

  // Render metadata panel
  const renderMetadataPanel = () => {
    if (!documentDetail) {
      return (
        <div className="metadata-empty">
          <span className="metadata-empty-icon">📋</span>
          <span>No artifact selected</span>
          <span className="metadata-empty-hint">Select an artifact to view its metadata</span>
        </div>
      )
    }

    return (
      <div className="metadata-details">
        {/* Section 1: Core Metadata */}
        <div className="metadata-section">
          <div className="metadata-section-title">
            <span className="section-icon">📄</span>
            Core Metadata
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Document ID</span>
            <span className="metadata-value metadata-id">#{documentDetail.id}</span>
          </div>
          <div className="metadata-row metadata-row-filename">
            <span className="metadata-label">Filename</span>
            <span className="metadata-value metadata-filename" title={documentDetail.name}>
              {documentDetail.name}
            </span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Path</span>
            <span className="metadata-value metadata-path-value" title={documentDetail.path}>
              {documentDetail.path}
            </span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Extension</span>
            <span className="metadata-value">
              {documentDetail.extension ? documentDetail.extension.toUpperCase() : '—'}
            </span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">MIME Type</span>
            <span className="metadata-value metadata-mime">
              {documentDetail.mime_type || '—'}
            </span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">File Size</span>
            <span className="metadata-value">{formatFileSize(documentDetail.file_size)}</span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Created</span>
            <span className="metadata-value">{formatDate(documentDetail.created_at)}</span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Modified</span>
            <span className="metadata-value">{formatDate(documentDetail.modified_time)}</span>
          </div>
          <div className="metadata-row">
            <span className="metadata-label">Indexed</span>
            <span className="metadata-value">{formatDate(documentDetail.indexed_at)}</span>
          </div>
        </div>

        {/* Section 2: Processing Status */}
        <div className="metadata-section">
          <div className="metadata-section-title">
            <span className="section-icon">⚙️</span>
            Processing Status
          </div>
          {documentDetail.processing_status.length === 0 ? (
            <div className="processing-empty">
              No processing jobs found
            </div>
          ) : (
            <div className="processing-list">
              {documentDetail.processing_status.map((job, index) => (
                <div key={index} className="processing-item">
                  <span className="processing-label">{job.label}</span>
                  {renderProcessingBadge(job.status)}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 3: File Hashes */}
        <div className="metadata-section">
          <div className="metadata-section-title">
            <span className="section-icon">🔐</span>
            File Hashes
          </div>
          {documentDetail.md5 && (
            <div className="hash-row">
              <span className="hash-label">MD5</span>
              <span className="hash-value" title={documentDetail.md5}>
                {documentDetail.md5.substring(0, 16)}...
              </span>
            </div>
          )}
          {documentDetail.sha1 && (
            <div className="hash-row">
              <span className="hash-label">SHA1</span>
              <span className="hash-value" title={documentDetail.sha1}>
                {documentDetail.sha1.substring(0, 16)}...
              </span>
            </div>
          )}
          {documentDetail.sha256 && (
            <div className="hash-row">
              <span className="hash-label">SHA256</span>
              <span className="hash-value" title={documentDetail.sha256}>
                {documentDetail.sha256.substring(0, 16)}...
              </span>
            </div>
          )}
          {!documentDetail.md5 && !documentDetail.sha1 && !documentDetail.sha256 && (
            <div className="hash-empty">No hashes available</div>
          )}
        </div>

        {/* Section 4: Artifact Type */}
        <div className="metadata-section">
          <div className="metadata-section-title">
            <span className="section-icon">🏷️</span>
            Artifact Type
          </div>
          <div className="artifact-type-row">
            <span className={`artifact-type-badge artifact-type-${(documentDetail.artifact_type || 'unknown').toLowerCase().replace(' ', '-')}`}>
              {documentDetail.artifact_type || 'Unknown'}
            </span>
          </div>
        </div>
      </div>
    )
  }

  // Build breadcrumb path
  const getBreadcrumbPath = () => {
    const parts = selectedFolder.split('/').filter(Boolean)
    return parts
  }

  return (
    <div className="artifact-explorer">
      <div className="explorer-container">
        {/* Left Pane - Explorer Tree */}
        <div className="explorer-left-pane">
          <div className="pane-header">
            <span className="pane-title">Explorer</span>
            <button className="pane-action" onClick={loadFolderTree} title="Refresh">
              ↻
            </button>
          </div>
          <div className="folder-tree">
            {loading && tree.length === 0 ? (
              <div className="tree-loading">Loading...</div>
            ) : error ? (
              <div className="tree-error">{error}</div>
            ) : (
              tree.map(node => renderTreeNode(node))
            )}
          </div>
        </div>

        {/* Center Pane - View */}
        <div className="explorer-center-pane">
          {/* View header with breadcrumb and view switcher */}
          <div className="view-header">
            <div className="breadcrumb">
              {getBreadcrumbPath().map((part, i) => (
                <span key={i}>
                  <span className="breadcrumb-sep">/</span>
                  <span className="breadcrumb-part">{part}</span>
                </span>
              ))}
            </div>
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
              <button
                className={`view-btn ${viewMode === 'preview' ? 'active' : ''}`}
                onClick={() => setViewMode('preview')}
                title="Preview view"
              >
                👁
              </button>
            </div>
          </div>

          {/* View content */}
          <div className="view-content">
            {viewMode === 'grid' && renderGridView()}
            {viewMode === 'list' && renderListView()}
            {viewMode === 'preview' && renderPreviewView()}
          </div>

          {/* View footer */}
          <div className="view-footer">
            <span className="item-count">
              {folderContents.folders.length + folderContents.documents.length} items
            </span>
            {selectedDocument && (
              <span className="selected-info">
                {getFileIcon(selectedDocument.name)} {selectedDocument.name}
              </span>
            )}
          </div>
        </div>

        {/* Right Pane - Metadata */}
        <div className="explorer-right-pane">
          <div className="pane-header">
            <span className="pane-title">Metadata</span>
          </div>
          <div className="pane-content">
            {renderMetadataPanel()}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ArtifactExplorer
