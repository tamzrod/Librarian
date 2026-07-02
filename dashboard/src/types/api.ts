/**
 * Librarian API Types
 * Auto-generated from OpenAPI schema
 * Dashboard API version: v1.0
 */

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'starting'
  database: {
    connected: boolean
    schema_ready: boolean
  }
  queue: {
    queued: number
    running: number
    oldest_job_age_seconds: number | null
  }
  workers: number
  watcher_active: boolean
  job_processor_active: boolean
}

export interface SystemOverviewResponse {
  files: number
  documents: number
  directories: number
  watched_paths: number
  storage_used_bytes: number | null
  entities: number
  relationships: number
  events: number
  locations: number
  embeddings: number
  queued_jobs: number
  running_jobs: number
  completed_jobs: number
  failed_jobs: number
  workers: number
  oldest_job_age_seconds: number | null
  database_status: string
  watcher_status: string
  job_processor_status: string
  api_status: string
}

export interface StatsResponse {
  library_root: string
  database: {
    connected: boolean
    schema_ready: boolean
    persistence_available: boolean
  }
  documents: {
    total: number
    indexed: number
  }
  entities: {
    total: number
  }
  events: {
    total: number
  }
  locations: {
    total: number
  }
  parsers: {
    count: number
    types: string[]
  }
  watcher: {
    active: boolean
    last_scan: string | null
  }
  initial_scan_complete: boolean
  timestamp: string
}

export interface DocumentStatusResponse {
  status_counts: Record<string, number>
  total: number
  timestamp: string
}

export interface JobStatusResponse {
  status_counts: Record<string, number>
  total: number
  queued: number
  timestamp: string
}

export interface JobRecord {
  id: number
  document_id: number
  document_path?: string
  job_type: string
  status: 'QUEUED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  worker_id?: string
  attempt_count: number
  created_at?: string
  started_at?: string
  completed_at?: string
  age_seconds?: number
  error_message?: string
}

export interface JobsResponse {
  data: JobRecord[]
  filters: {
    document_id?: number
    status?: string
    job_type?: string
  }
  pagination: {
    total: number
    limit: number
    returned: number
  }
  timestamp: string
}

export interface JobQueueResponse {
  jobs: JobRecord[]
  total: number
  filters: Record<string, string | number | undefined>
  counts: {
    queued: number
    in_progress: number
    completed: number
    failed: number
  }
}

export interface ActivityEvent {
  timestamp: string
  level: 'info' | 'warning' | 'error'
  message: string
  details?: Record<string, unknown>
}

export interface ActivityFeedResponse {
  events: ActivityEvent[]
  count: number
  since?: string
}

export interface DocumentJourneyResponse {
  document_id: number
  path: string
  extension?: string
  file_size?: number
  status: string
  created_at?: string
  indexed_at?: string
  jobs: JobRecord[]
  lifecycle_states: string[]
}

export interface DocumentListResponse {
  documents: DocumentSummary[]
  total: number
}

export interface DocumentSummary {
  id: number
  path: string
  extension?: string
  file_size?: number
  status: string
  character_count?: number
  parser?: string
  created_at?: string
}

export interface ExtractionResultsResponse {
  document_id: number
  path: string
  entities: Entity[]
  events: Event[]
  locations: Location[]
  content_preview?: string
}

export interface Entity {
  id: number
  type: string
  value: string
  normalized?: string
}

export interface Event {
  id: number
  timestamp: string
  type: string
  description?: string
}

export interface Location {
  id: number
  name: string
  type?: string
  city?: string
  state?: string
  country?: string
  latitude?: number
  longitude?: number
}

export interface TimelineEvent {
  id: number
  timestamp: string
  event_type: string
  description: string
  document_count: number
}

export interface TimelineResponse {
  data: TimelineEvent[]
  filters: {
    start?: string
    end?: string
    entity?: string
    event_type?: string
  }
  pagination: {
    total: number
    limit: number
    returned: number
  }
}

export interface RootResponse {
  name: string
  version: string
  docs: string
  library_root: string
}

export interface ErrorResponse {
  error: {
    code: string
    message: string
    details?: Array<{
      field: string
      message: string
    }>
    request_id?: string
  }
}

export type DocumentLifecycleState =
  | 'DISCOVERED'
  | 'METADATA_INDEXED'
  | 'CONTENT_EXTRACTED'
  | 'ENTITY_EXTRACTED'
  | 'RELATIONSHIPS_BUILT'
  | 'EMBEDDED'
  | 'COMPLETE'
  | 'FAILED'

export type JobStatus = 'QUEUED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED'

export type JobType =
  | 'extract_text'
  | 'extract_entities'
  | 'extract_events'
  | 'extract_locations'
  | 'generate_embeddings'
  | 'ocr'
  | 'plugin_processing'

export const DOCUMENT_LIFECYCLE_STATES: DocumentLifecycleState[] = [
  'DISCOVERED',
  'METADATA_INDEXED',
  'CONTENT_EXTRACTED',
  'ENTITY_EXTRACTED',
  'RELATIONSHIPS_BUILT',
  'EMBEDDED',
  'COMPLETE',
]

export const JOB_STATUS_COLORS: Record<JobStatus, string> = {
  QUEUED: '#f59e0b',
  IN_PROGRESS: '#0ea5e9',
  COMPLETED: '#22c55e',
  FAILED: '#ef4444',
  CANCELLED: '#64748b',
}

export const LIFECYCLE_STATE_COLORS: Record<string, string> = {
  DISCOVERED: '#6366f1',
  METADATA_INDEXED: '#8b5cf6',
  CONTENT_EXTRACTED: '#a855f7',
  ENTITY_EXTRACTED: '#d946ef',
  RELATIONSHIPS_BUILT: '#ec4899',
  EMBEDDED: '#f43f5e',
  COMPLETE: '#22c55e',
  FAILED: '#ef4444',
}

// Evidence Timeline API Types (Phase 1B)

export interface TimelineStats {
  photos_total: number
  gps_tagged: number
  unique_cameras: number
  first_photo_timestamp: string | null
  last_photo_timestamp: string | null
}

export interface PhotoSummary {
  document_id: number
  filename: string
  timestamp: string | null
  camera_make: string | null
  camera_model: string | null
  gps_latitude: number | null
  gps_longitude: number | null
}

export interface PhotoMapMarker {
  document_id: number
  latitude: number
  longitude: number
  timestamp: string | null
  camera: string | null
  filename: string
}

export interface PhotoDetail {
  document_id: number
  filename: string
  timestamp: string | null
  timestamp_digitized: string | null
  gps_latitude: number | null
  gps_longitude: number | null
  gps_altitude: number | null
  camera_make: string | null
  camera_model: string | null
  lens_model: string | null
  width: number
  height: number
  orientation: number | null
  file_format: string
  extracted_at: string | null
}

export interface TimelinePhotosResponse {
  data: PhotoSummary[]
  pagination: {
    total: number
    limit: number
    offset: number
    returned: number
  }
  filters: {
    camera: string | null
    gps_only: boolean
    start_date: string | null
    end_date: string | null
  }
}

export interface TimelineMapResponse {
  markers: PhotoMapMarker[]
  count: number
}

// Artifact Explorer Types (Phase 2)

export interface FolderNode {
  id: string
  name: string
  path: string
  has_children: boolean
}

export interface FolderTreeResponse {
  root: FolderNode
  total_folders: number
}

export interface ExplorerDocument {
  id: number
  name: string
  path: string
  extension: string | null
  file_size: number | null
  mime_type: string | null
  modified_time: string | null
  indexed_at: string | null
  status: string
}

export interface FolderContentsResponse {
  folder: FolderNode
  folders: FolderNode[]
  documents: ExplorerDocument[]
  total_items: number
}

export interface ProcessingStatus {
  job_type: string
  status: 'QUEUED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  label: string
}

export interface DocumentDetail {
  id: number
  name: string
  path: string
  extension: string | null
  file_size: number | null
  mime_type: string | null
  modified_time: string | null
  created_at: string | null
  indexed_at: string | null
  status: string
  character_count: number | null
  // File hashes
  md5: string | null
  sha1: string | null
  sha256: string | null
  // Artifact type classification
  artifact_type: string | null
  // E5: Thumbnail path
  thumbnail_path: string | null
  // Processing status from jobs
  processing_status: ProcessingStatus[]
}

export interface DocumentDetailResponse {
  document: DocumentDetail
}

// Trace View API Types (Operation TRACE v2)

export interface TraceFilterOption {
  id: string
  label: string
  count: number
  checked: boolean
}

export interface TraceFilterGroup {
  id: string
  label: string
  expanded: boolean
  options: TraceFilterOption[]
}

export interface TraceFiltersResponse {
  groups: TraceFilterGroup[]
  total_items: number
}

export interface TraceMapMarker {
  document_id: number
  latitude: number
  longitude: number
  timestamp: string | null
  camera: string | null
  camera_make: string | null
  camera_model: string | null
  filename: string
  thumbnail_path: string | null
  altitude: number | null
  collection_id: string | null
  collection_name: string | null
  year: number | null
}

export interface TraceEventItem {
  document_id: number
  timestamp: string | null
  camera: string | null
  location: string | null
  latitude: number | null
  longitude: number | null
  filename: string
  thumbnail_path: string | null
  collection_name: string | null
  year: number | null
}

export interface TraceDataResponse {
  markers: TraceMapMarker[]
  events: TraceEventItem[]
  stats: {
    total: number
    with_gps: number
    unique_cameras: number
    year_range: { min: number | null; max: number | null }
  }
  pagination: {
    total: number
    limit: number
    offset: number
    returned: number
  }
}

export interface TracePhotoDetail {
  document_id: number
  filename: string
  path: string
  timestamp: string | null
  timestamp_digitized: string | null
  gps_latitude: number | null
  gps_longitude: number | null
  gps_altitude: number | null
  camera_make: string | null
  camera_model: string | null
  lens_model: string | null
  width: number
  height: number
  orientation: number | null
  file_format: string
  thumbnail_path: string | null
  collection_name: string | null
  extracted_at: string | null
}

export interface TracePhotoDetailResponse {
  photo: TracePhotoDetail
}
