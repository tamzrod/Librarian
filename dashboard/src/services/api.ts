/**
 * Librarian API Client
 * REST API consumer for the Librarian backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  HealthResponse,
  SystemOverviewResponse,
  StatsResponse,
  DocumentStatusResponse,
  JobStatusResponse,
  JobsResponse,
  JobQueueResponse,
  ActivityFeedResponse,
  DocumentJourneyResponse,
  DocumentListResponse,
  ExtractionResultsResponse,
  TimelineResponse,
  RootResponse,
  ActivityEvent,
  JobRecord,
  FolderTreeResponse,
  FolderContentsResponse,
  DocumentDetailResponse,
  TraceFiltersResponse,
  TraceDataResponse,
  TracePhotoDetailResponse,
  PluginListResponse,
  PluginUpdateResponse,
} from '../types/api'
import type {
  DataExplorerNavigationResponse,
  DataExplorerArtifactsResponse,
  DataExplorerArtifactDetailResponse,
  DataExplorerStatisticsResponse,
  DataExplorerArtifact,
} from '../types/dataExplorer'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function handleApiError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ error?: { message?: string; code?: string } }>
    const message = axiosError.response?.data?.error?.message || axiosError.message
    const statusCode = axiosError.response?.status
    const code = axiosError.response?.data?.error?.code
    throw new ApiError(message, statusCode, code)
  }
  throw error
}

class LibrarianApiClient {
  private client: AxiosInstance

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL: baseURL || '/',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    })

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error)
        return Promise.reject(error)
      }
    )
  }

  private async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    try {
      const response = await this.client.get<T>(url, { params })
      return response.data
    } catch (error) {
      handleApiError(error)
    }
  }

  // Root endpoint
  async getRoot(): Promise<RootResponse> {
    return this.get<RootResponse>('/')
  }

  // Health check
  async getHealth(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health')
  }

  // System status
  async getStatus(): Promise<SystemOverviewResponse> {
    return this.get<SystemOverviewResponse>('/api/v1/status')
  }

  // Statistics
  async getStats(): Promise<StatsResponse> {
    return this.get<StatsResponse>('/api/v1/stats')
  }

  // Document status counts
  async getDocumentStatusCounts(): Promise<DocumentStatusResponse> {
    return this.get<DocumentStatusResponse>('/api/v1/documents/status')
  }

  // Job status counts
  async getJobStatusCounts(): Promise<JobStatusResponse> {
    return this.get<JobStatusResponse>('/api/v1/jobs/status')
  }

  // Get jobs with filters
  async getJobs(params: {
    document_id?: number
    status?: string
    job_type?: string
    limit?: number
  } = {}): Promise<JobsResponse> {
    return this.get<JobsResponse>('/api/v1/jobs', params)
  }

  // Get all operations data (combined endpoint for dashboard)
  async getOperationsOverview(): Promise<{
    health: HealthResponse
    stats: StatsResponse
    documentStatus: DocumentStatusResponse
    jobStatus: JobStatusResponse
  }> {
    const [health, stats, documentStatus, jobStatus] = await Promise.all([
      this.getHealth().catch(() => null),
      this.getStats().catch(() => null),
      this.getDocumentStatusCounts().catch(() => null),
      this.getJobStatusCounts().catch(() => null),
    ])

    return {
      health: health || this.getDefaultHealth(),
      stats: stats || this.getDefaultStats(),
      documentStatus: documentStatus || { status_counts: {}, total: 0, timestamp: new Date().toISOString() },
      jobStatus: jobStatus || { status_counts: {}, total: 0, queued: 0, timestamp: new Date().toISOString() },
    }
  }

  private getDefaultHealth(): HealthResponse {
    return {
      status: 'starting',
      database: { connected: false, schema_ready: false },
      queue: { queued: 0, running: 0, oldest_job_age_seconds: null },
      workers: 0,
      watcher_active: false,
      job_processor_active: false,
    }
  }

  private getDefaultStats(): StatsResponse {
    return {
      library_root: '/library',
      database: { connected: false, schema_ready: false, persistence_available: false },
      documents: { total: 0, indexed: 0 },
      entities: { total: 0 },
      events: { total: 0 },
      locations: { total: 0 },
      parsers: { count: 0, types: [] },
      watcher: { active: false, last_scan: null },
      initial_scan_complete: false,
      timestamp: new Date().toISOString(),
    }
  }

  // Queue operations
  async getQueueJobs(params: {
    status?: string
    job_type?: string
    limit?: number
  } = {}): Promise<JobQueueResponse> {
    try {
      const jobsResponse = await this.getJobs({
        status: params.status,
        job_type: params.job_type,
        limit: params.limit || 100,
      })

      const jobStatus = await this.getJobStatusCounts().catch(() => ({
        status_counts: {},
        total: 0,
        queued: 0,
        timestamp: new Date().toISOString(),
      }))

      const statusCounts = jobStatus.status_counts as Record<string, number>

      return {
        jobs: jobsResponse.data,
        total: jobsResponse.pagination.total,
        filters: params,
        counts: {
          queued: statusCounts['QUEUED'] || 0,
          in_progress: statusCounts['IN_PROGRESS'] || 0,
          completed: statusCounts['COMPLETED'] || 0,
          failed: (statusCounts['FAILED'] || 0) + (statusCounts['FAILED_PERMANENT'] || 0),
        },
      }
    } catch {
      return {
        jobs: [],
        total: 0,
        filters: params,
        counts: { queued: 0, in_progress: 0, completed: 0, failed: 0 },
      }
    }
  }

  // Activity feed
  async getActivityFeed(limit: number = 50): Promise<ActivityFeedResponse> {
    try {
      const [timeline, jobs] = await Promise.all([
        this.getTimeline({ limit }).catch(() => ({ data: [], filters: {}, pagination: { total: 0, limit: 0, returned: 0 } })),
        this.getJobs({ limit }).catch(() => ({ data: [], filters: {}, pagination: { total: 0, limit: 0, returned: 0 }, timestamp: '' })),
      ])

      const events: ActivityEvent[] = []

      // Add timeline events
      for (const event of timeline.data) {
        events.push({
          timestamp: event.timestamp,
          level: 'info',
          message: `${event.event_type}: ${event.description}`,
          details: { event_type: event.event_type, document_count: event.document_count },
        })
      }

      // Add job events
      for (const job of jobs.data) {
        let level: 'info' | 'warning' | 'error' = 'info'
        let message = `Job ${job.id}: ${job.job_type} - ${job.status}`

        if (job.status === 'FAILED') {
          level = 'error'
          message += job.error_message ? ` (${job.error_message})` : ''
        } else if (job.status === 'IN_PROGRESS') {
          level = 'info'
        } else if (job.status === 'COMPLETED') {
          level = 'info'
        }

        events.push({
          timestamp: job.completed_at || job.started_at || job.created_at || new Date().toISOString(),
          level,
          message,
          details: {
            job_id: job.id,
            job_type: job.job_type,
            worker_id: job.worker_id,
            attempt_count: job.attempt_count,
          },
        })
      }

      // Sort by timestamp descending
      events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

      return {
        events: events.slice(0, limit),
        count: Math.min(events.length, limit),
        since: events.length > 0 ? events[events.length - 1].timestamp : undefined,
      }
    } catch {
      return {
        events: [],
        count: 0,
      }
    }
  }

  // Timeline
  async getTimeline(params: {
    start?: string
    end?: string
    entity?: string
    event_type?: string
    limit?: number
  } = {}): Promise<TimelineResponse> {
    return this.get<TimelineResponse>('/api/v1/timeline', params)
  }

  // Document operations
  async getDocuments(params: {
    limit?: number
    offset?: number
    status?: string
  } = {}): Promise<DocumentListResponse> {
    return this.get<DocumentListResponse>('/api/v1/operations/documents', {
      limit: params.limit || 50,
      offset: params.offset || 0,
      status: params.status,
    })
  }

  async getDocumentJourney(documentId: number): Promise<DocumentJourneyResponse> {
    return this.get<DocumentJourneyResponse>(`/api/v1/operations/documents/${documentId}/journey`)
  }

  async getDocumentExtractions(documentId: number): Promise<ExtractionResultsResponse> {
    return this.get<ExtractionResultsResponse>(`/api/v1/operations/documents/${documentId}/extractions`)
  }

  // Utility: format bytes
  formatBytes(bytes: number | null | undefined): string {
    if (bytes == null || bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
  }

  // Utility: format relative time
  formatRelativeTime(isoString: string | null | undefined): string {
    if (!isoString) return 'N/A'
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHour = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHour / 24)

    if (diffSec < 60) return `${diffSec}s ago`
    if (diffMin < 60) return `${diffMin}m ago`
    if (diffHour < 24) return `${diffHour}h ago`
    if (diffDay < 7) return `${diffDay}d ago`
    return date.toLocaleDateString()
  }

  // =========================================================================
  // Artifact Explorer API
  // =========================================================================

  /**
   * Get the folder hierarchy tree.
   * Used to populate the left pane of Artifact Explorer.
   */
  async getFolderTree(): Promise<FolderTreeResponse> {
    return this.get<FolderTreeResponse>('/api/v1/explorer/tree')
  }

  /**
   * Get subfolders and documents within a folder.
   * @param folderPath - The folder path (e.g., "/library/photos")
   */
  async getFolderContents(folderPath: string): Promise<FolderContentsResponse> {
    // URL-encode the path for safety
    const encodedPath = encodeURIComponent(folderPath)
    return this.get<FolderContentsResponse>(`/api/v1/explorer/folders/${encodedPath}`)
  }

  /**
   * Get detailed information about a specific document.
   * Used to populate the metadata panel.
   * @param documentId - The document ID
   */
  async getDocumentDetails(documentId: number): Promise<DocumentDetailResponse> {
    return this.get<DocumentDetailResponse>(`/api/v1/explorer/documents/${documentId}`)
  }

  /**
   * Get a preview URL for a document.
   * @param documentId - The document ID
   * @returns URL to fetch the preview
   */
  getPreviewUrl(documentId: number): string {
    return `${this.client.defaults.baseURL}/api/v1/explorer/documents/${documentId}/preview`
  }

  /**
   * Get the raw file URL for a document.
   * @param documentId - The document ID
   * @returns URL to fetch the raw file
   */
  getRawFileUrl(documentId: number): string {
    return `${this.client.defaults.baseURL}/api/v1/explorer/documents/${documentId}/raw`
  }

  /**
   * Get the thumbnail URL for a document.
   * @param thumbnailPath - The relative thumbnail path (e.g., "thumbnails/1017_IMG_001_thumb.jpg")
   * @returns URL to fetch the thumbnail image
   */
  getThumbnailUrl(thumbnailPath: string | null | undefined): string | null {
    if (!thumbnailPath) return null
    // thumbnailPath is like "thumbnails/docId_filename_thumb.jpg" (from database)
    // Nginx proxy handles /thumbnails/ -> http://api:8001/thumbnails/
    // If path already starts with thumbnails/, use as-is
    const cleanPath = thumbnailPath.replace(/^thumbnails\//, '')
    // Handle base URL (which may be "/" or empty for relative URLs)
    const base = this.client.defaults.baseURL || '/'
    // Ensure no double slashes when base is "/"
    if (base === '/') {
      return `/thumbnails/${cleanPath}`
    }
    return `${base}/thumbnails/${cleanPath}`
  }

  /**
   * Check if a file extension is previewable as text.
   */
  isTextPreviewable(extension: string | null | undefined): boolean {
    if (!extension) return false
    const ext = extension.toLowerCase()
    const textExtensions = [
      '.txt', '.md', '.markdown', '.json', '.yaml', '.yml', '.xml',
      '.py', '.log', '.ini', '.cfg', '.conf', '.env', '.java',
      '.c', '.cpp', '.h', '.js', '.ts', '.jsx', '.tsx', '.css',
      '.html', '.rst'
    ]
    return textExtensions.includes(ext)
  }

  /**
   * Check if a file extension is previewable as an image.
   */
  isImagePreviewable(extension: string | null | undefined): boolean {
    if (!extension) return false
    const ext = extension.toLowerCase()
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
    return imageExtensions.includes(ext)
  }

  // =========================================================================
  // Trace View API (Operation TRACE v2)
  // =========================================================================

  /**
   * Get available filters for the Trace view.
   * Returns collapsible filter groups for devices, collections, years, and sources.
   */
  async getTraceFilters(): Promise<TraceFiltersResponse> {
    return this.get<TraceFiltersResponse>('/api/v1/trace/filters')
  }

  /**
   * Get Trace data with filters applied.
   * @param cameras - Comma-separated list of camera IDs to filter
   * @param collections - Comma-separated list of collection IDs to filter
   * @param years - Comma-separated list of years to filter
   * @param sources - Comma-separated list of sources to filter
   * @param startDate - Start date filter (ISO format)
   * @param endDate - End date filter (ISO format)
   * @param includeUnknownDevice - Include photos with unknown device
   * @param limit - Maximum results
   * @param offset - Offset for pagination
   */
  async getTraceData(params: {
    cameras?: string
    collections?: string
    years?: string
    sources?: string
    startDate?: string
    endDate?: string
    includeUnknownDevice?: boolean
    limit?: number
    offset?: number
  } = {}): Promise<TraceDataResponse> {
    return this.get<TraceDataResponse>('/api/v1/trace/data', {
      cameras: params.cameras,
      collections: params.collections,
      years: params.years,
      sources: params.sources,
      start_date: params.startDate,
      end_date: params.endDate,
      include_unknown_device: params.includeUnknownDevice,
      limit: params.limit || 100,
      offset: params.offset || 0,
    })
  }

  /**
   * Get full photo metadata for Trace view.
   * @param documentId - The document ID
   */
  async getTracePhoto(documentId: number): Promise<TracePhotoDetailResponse> {
    return this.get<TracePhotoDetailResponse>(`/api/v1/trace/photo/${documentId}`)
  }

  /**
   * Get the thumbnail URL for a trace photo.
   * Note: thumbnailPath is like "thumbnails/docId_filename_thumb.jpg" (from database).
   */
  getTraceThumbnailUrl(thumbnailPath: string | null | undefined): string | null {
    if (!thumbnailPath) return null
    // thumbnailPath is like "thumbnails/docId_filename_thumb.jpg" (from database)
    // Nginx proxy handles /thumbnails/ -> http://api:8001/thumbnails/
    // If path already starts with thumbnails/, strip the prefix
    const cleanPath = thumbnailPath.replace(/^thumbnails\//, '')
    // Handle base URL (which may be "/" or empty for relative URLs)
    const base = this.client.defaults.baseURL || '/'
    // Ensure no double slashes when base is "/"
    if (base === '/') {
      return `/thumbnails/${cleanPath}`
    }
    return `${base}/thumbnails/${cleanPath}`
  }

  // =========================================================================
  // Thumbnail Priority API
  // =========================================================================

  /**
   * Report visible documents to prioritize their thumbnail generation.
   * @param viewportDocumentIds - Document IDs currently visible in viewport
   * @param currentFolderDocumentIds - Document IDs in the currently open folder
   */
  async prioritizeThumbnails(
    viewportDocumentIds: number[],
    currentFolderDocumentIds?: number[]
  ): Promise<{
    viewport_prioritized: number
    folder_prioritized: number
    viewport_created: number
    folder_created: number
    timestamp: string
  }> {
    try {
      const response = await this.client.post<{
        viewport_prioritized: number
        folder_prioritized: number
        viewport_created: number
        folder_created: number
        timestamp: string
      }>('/api/v1/operations/thumbnails/prioritize', {
        viewport_document_ids: viewportDocumentIds,
        current_folder_document_ids: currentFolderDocumentIds
      })
      return response.data
    } catch (error) {
      handleApiError(error)
    }
  }

  // =========================================================================
  // Settings API (Plugin Configuration)
  // =========================================================================

  /**
   * Get all installed plugins with their configuration.
   */
  async getPlugins(): Promise<PluginListResponse> {
    return this.get<PluginListResponse>('/api/v1/settings/plugins')
  }

  /**
   * Update plugin enabled state.
   * @param pluginName - Name of the plugin
   * @param enabled - Whether the plugin should be enabled
   */
  async updatePlugin(pluginName: string, enabled: boolean): Promise<PluginUpdateResponse> {
    try {
      const response = await this.client.put<PluginUpdateResponse>(
        `/api/v1/settings/plugins/${pluginName}`,
        { enabled }
      )
      return response.data
    } catch (error) {
      handleApiError(error)
    }
  }

  // =========================================================================
  // Data Explorer API (Operational Inspection Tool)
  // =========================================================================

  /**
   * Get navigation structure for the Data Explorer.
   * Returns descriptors for Collections, Folders, Virtual Collections, and Saved Views.
   * Navigation is descriptor-driven - frontend renders generically.
   * 
   * @param parentId - If provided, returns children of that item (lazy loading)
   */
  async getDataExplorerNavigation(parentId?: string): Promise<DataExplorerNavigationResponse> {
    const params: Record<string, unknown> = {}
    if (parentId) {
      params.parent_id = parentId
    }
    return this.get<DataExplorerNavigationResponse>('/api/v1/data-explorer/navigation', params)
  }

  /**
   * Get artifacts for a navigation item.
   * @param navigationId - The navigation item ID
   * @param navigationType - The navigation item type (collection, folder, virtual_collection, saved_view)
   */
  async getDataExplorerArtifacts(
    navigationId: string,
    navigationType: string
  ): Promise<DataExplorerArtifactsResponse> {
    return this.get<DataExplorerArtifactsResponse>('/api/v1/data-explorer/artifacts', {
      navigation_id: navigationId,
      navigation_type: navigationType,
    })
  }

  /**
   * Get detailed artifact information for the inspector.
   * Descriptor-driven - returns sections/fields defined by backend.
   * @param artifactId - The artifact ID
   */
  async getDataExplorerArtifactDetail(artifactId: number): Promise<DataExplorerArtifactDetailResponse> {
    return this.get<DataExplorerArtifactDetailResponse>(`/api/v1/data-explorer/artifacts/${artifactId}`)
  }

  /**
   * Get system statistics for Data Explorer.
   */
  async getDataExplorerStatistics(): Promise<DataExplorerStatisticsResponse> {
    return this.get<DataExplorerStatisticsResponse>('/api/v1/data-explorer/statistics')
  }

  /**
   * Search artifacts across the library.
   * @param query - Search query string
   * @param options - Search options (type filter, size range, limit)
   */
  async searchDataExplorerArtifacts(
    query: string,
    options: {
      type?: string
      minSize?: number
      maxSize?: number
      limit?: number
    } = {}
  ): Promise<{
    artifacts: DataExplorerArtifact[]
    total: number
    query: string
    filters_applied: Record<string, unknown>
  }> {
    const params: Record<string, unknown> = { q: query }
    if (options.type) params.type_filter = options.type
    if (options.minSize !== undefined) params.min_size = options.minSize
    if (options.maxSize !== undefined) params.max_size = options.maxSize
    if (options.limit !== undefined) params.limit = options.limit
    
    return this.get('/api/v1/data-explorer/search', params)
  }
}

export const api = new LibrarianApiClient()
export { ApiError }
export type { JobRecord, ActivityEvent }
