/**
 * Data Explorer Types
 * 
 * Descriptor-driven types for the operational inspection tool.
 * These types define the contract between Dashboard and Explorer API.
 * 
 * Key architectural principles:
 * - Navigation is driven by descriptors from the backend
 * - Inspector renders dynamically based on artifact descriptors
 * - No hardcoded artifact type handling in the frontend
 */

/**
 * Navigation item types supported by the explorer.
 * These represent investigation concepts, not database structures.
 */
export type NavigationItemType = 'collection' | 'folder' | 'virtual_collection' | 'saved_view'

/**
 * A navigation item in the left pane.
 * Descriptors define the structure - frontend renders generically.
 */
export interface DataExplorerNavigationItem {
  id: string
  name: string
  type: NavigationItemType
  parent_id: string | null
  has_children: boolean
  expanded: boolean
  children?: DataExplorerNavigationItem[]
  metadata?: Record<string, unknown>
}

/**
 * Response from navigation API endpoint.
 */
export interface DataExplorerNavigationResponse {
  items: DataExplorerNavigationItem[]
  total: number
}

/**
 * An artifact in the explorer view.
 * Minimal information for list/grid display.
 */
export interface DataExplorerArtifact {
  id: number
  name: string
  path: string
  type: string | null
  size: number | null
  modified: string | null
  thumbnail: string | null
  metadata?: Record<string, unknown>
}

/**
 * Response from artifacts API endpoint.
 */
export interface DataExplorerArtifactsResponse {
  artifacts: DataExplorerArtifact[]
  total: number
  navigation_id: string
  navigation_type: NavigationItemType
}

/**
 * A field descriptor for the inspector.
 * Defines how a single field should be rendered.
 */
export interface InspectorFieldDescriptor {
  label: string
  value: unknown
  type: 'text' | 'number' | 'date' | 'url' | 'hash' | 'status' | 'list'
  truncate?: boolean
  copyable?: boolean
  formatter?: string
}

/**
 * A section descriptor for the inspector.
 * Groups related fields together.
 */
export interface InspectorSectionDescriptor {
  title: string
  icon?: string
  fields: InspectorFieldDescriptor[]
  collapsible?: boolean
  collapsed?: boolean
}

/**
 * The artifact descriptor that drives inspector rendering.
 * Backend provides this - frontend renders generically.
 */
export interface ArtifactDescriptor {
  artifact_id: number
  artifact_type: string
  sections: InspectorSectionDescriptor[]
}

/**
 * Detailed artifact information for the inspector.
 */
export interface DataExplorerArtifactDetail {
  id: number
  name: string
  path: string
  descriptor: ArtifactDescriptor
}

/**
 * Response from artifact detail API endpoint.
 */
export interface DataExplorerArtifactDetailResponse {
  artifact: DataExplorerArtifactDetail
}

/**
 * Statistics response for system overview.
 */
export interface DataExplorerStatistics {
  total_documents: number
  total_collections: number
  total_virtual_collections: number
  total_saved_views: number
  by_type: Record<string, number>
  by_status: Record<string, number>
}

/**
 * Response from statistics API endpoint.
 */
export interface DataExplorerStatisticsResponse {
  statistics: DataExplorerStatistics
  timestamp: string
}
