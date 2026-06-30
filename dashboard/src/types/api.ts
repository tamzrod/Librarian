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
