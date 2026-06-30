import { useState } from 'react'
import './ArtifactExplorer.css'

interface TreeNode {
  id: string
  name: string
  type: 'folder' | 'file'
  children?: TreeNode[]
  expanded?: boolean
}

interface Artifact {
  id: number
  name: string
  path: string
  type: string
  size?: number
  modified?: string
}

const mockFolders: TreeNode[] = [
  {
    id: 'root',
    name: '/library',
    type: 'folder',
    expanded: true,
    children: [
      {
        id: 'samples',
        name: 'samples',
        type: 'folder',
        expanded: true,
        children: [
          { id: 'docs', name: 'documents', type: 'folder' },
          { id: 'structured', name: 'structured', type: 'folder' },
        ],
      },
      { id: 'storage', name: 'storage', type: 'folder' },
      { id: 'ingestion', name: 'ingestion', type: 'folder' },
    ],
  },
]

const mockArtifacts: Artifact[] = [
  { id: 1, name: 'config.yaml', path: '/library/config.yaml', type: 'yaml', size: 2048, modified: '2026-06-15' },
  { id: 2, name: 'main.py', path: '/library/ingestion/main.py', type: 'python', size: 8192, modified: '2026-06-20' },
  { id: 3, name: 'schema.json', path: '/library/storage/schema.json', type: 'json', size: 4096, modified: '2026-06-18' },
  { id: 4, name: 'README.md', path: '/library/README.md', type: 'markdown', size: 1536, modified: '2026-06-25' },
  { id: 5, name: 'photo.jpg', path: '/library/samples/photo.jpg', type: 'image', size: 102400, modified: '2026-06-10' },
]

function ArtifactExplorer() {
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null)
  const [folders, setFolders] = useState<TreeNode[]>(mockFolders)

  const toggleFolder = (nodeId: string) => {
    const toggleNode = (nodes: TreeNode[]): TreeNode[] => {
      return nodes.map(node => {
        if (node.id === nodeId) {
          return { ...node, expanded: !node.expanded }
        }
        if (node.children) {
          return { ...node, children: toggleNode(node.children) }
        }
        return node
      })
    }
    setFolders(toggleNode(folders))
  }

  const getFileIcon = (type: string) => {
    const icons: Record<string, string> = {
      yaml: '📝',
      python: '🐍',
      json: '📋',
      markdown: '📄',
      image: '🖼️',
      folder: '📁',
    }
    return icons[type] || '📄'
  }

  const renderTreeNode = (node: TreeNode, level = 0) => {
    const isFolder = node.type === 'folder'
    return (
      <div key={node.id}>
        <div
          className="tree-node"
          style={{ paddingLeft: `${1 + level * 1}rem` }}
          onClick={() => isFolder && toggleFolder(node.id)}
        >
          <span className="tree-expand">
            {isFolder && (node.expanded ? '▼' : '▶')}
          </span>
          <span className="tree-icon">{getFileIcon(node.type)}</span>
          <span className="tree-label">{node.name}</span>
        </div>
        {isFolder && node.expanded && node.children && (
          <div className="tree-children">
            {node.children.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="artifact-explorer">
      <div className="explorer-container">
        {/* Left Pane - Explorer Panel */}
        <div className="explorer-left-pane">
          <div className="explorer-panel-header">
            <h2>Explorer</h2>
            <div className="explorer-panel-actions">
              <button className="icon-btn" title="Refresh">↻</button>
            </div>
          </div>

          {/* Folder Tree */}
          <div className="folder-tree">
            {folders.map(node => renderTreeNode(node))}
          </div>

          {/* Artifact List */}
          <div className="explorer-panel-header" style={{ borderTop: '1px solid var(--border-color)' }}>
            <h2>Artifacts</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {mockArtifacts.length} items
            </span>
          </div>
          <div className="artifact-list">
            {mockArtifacts.map(artifact => (
              <div
                key={artifact.id}
                className={`artifact-item ${selectedArtifact?.id === artifact.id ? 'selected' : ''}`}
                onClick={() => setSelectedArtifact(artifact)}
              >
                <span className="artifact-icon">{getFileIcon(artifact.type)}</span>
                <div className="artifact-info">
                  <div className="artifact-name">{artifact.name}</div>
                  <div className="artifact-meta">
                    {artifact.type} • {artifact.modified}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Center Pane - Preview */}
        <div className="explorer-center-pane">
          <div className="preview-header">
            <div className="preview-breadcrumb">
              <span>library</span>
              <span>›</span>
              <span>{selectedArtifact?.path.split('/').slice(2, -1).join(' › ') || '...'}</span>
            </div>
            <span className="preview-title">
              {selectedArtifact?.name || 'No artifact selected'}
            </span>
          </div>
          <div className="preview-content">
            <div className="placeholder-preview">
              <span className="placeholder-icon">👁️</span>
              <span className="placeholder-text">
                {selectedArtifact
                  ? `Preview for "${selectedArtifact.name}"`
                  : 'Select an artifact to preview'}
              </span>
              <span className="placeholder-hint">
                Preview functionality coming soon
              </span>
            </div>
          </div>
        </div>

        {/* Right Pane - Metadata */}
        <div className="explorer-right-pane">
          <div className="explorer-panel-header">
            <h2>Metadata</h2>
          </div>
          <div className="metadata-content">
            {selectedArtifact ? (
              <>
                <div className="metadata-section">
                  <div className="metadata-section-title">File Information</div>
                  <div className="metadata-field">
                    <span className="metadata-label">Name</span>
                    <span className="metadata-value">{selectedArtifact.name}</span>
                  </div>
                  <div className="metadata-field">
                    <span className="metadata-label">Type</span>
                    <span className="metadata-value">{selectedArtifact.type.toUpperCase()}</span>
                  </div>
                  <div className="metadata-field">
                    <span className="metadata-label">Size</span>
                    <span className="metadata-value">
                      {selectedArtifact.size ? `${(selectedArtifact.size / 1024).toFixed(1)} KB` : 'Unknown'}
                    </span>
                  </div>
                  <div className="metadata-field">
                    <span className="metadata-label">Modified</span>
                    <span className="metadata-value">{selectedArtifact.modified}</span>
                  </div>
                </div>
                <div className="metadata-section">
                  <div className="metadata-section-title">Path</div>
                  <div className="metadata-field" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '0.25rem' }}>
                    <code style={{ fontSize: '0.75rem', wordBreak: 'break-all' }}>
                      {selectedArtifact.path}
                    </code>
                  </div>
                </div>
              </>
            ) : (
              <div className="metadata-empty">
                <span className="metadata-empty-icon">📋</span>
                <span>No artifact selected</span>
                <span style={{ fontSize: '0.75rem' }}>
                  Select an artifact to view metadata
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ArtifactExplorer
