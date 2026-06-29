"""Operations Dashboard API routes.

Provides read-only observability into the Librarian system for operators.
All endpoints are read-only - no write operations are performed.
"""

from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from api.dependencies import get_storage_backend
from storage.backend import StorageBackend


router = APIRouter(prefix="/operations", tags=["operations"])


# ============================================================================
# Schema Definitions
# ============================================================================

class SystemOverviewResponse(BaseModel):
    """System overview statistics."""
    # Filesystem
    files: int = Field(description="Total physical files")
    documents: int = Field(description="Total documents in database")
    directories: int = Field(description="Total directories watched")
    watched_paths: int = Field(description="Number of watched path patterns")
    storage_used_bytes: Optional[int] = Field(default=None, description="Storage used in bytes")
    
    # Knowledge
    entities: int = Field(description="Total entities extracted")
    relationships: int = Field(description="Total relationships")
    events: int = Field(description="Total events extracted")
    locations: int = Field(description="Total locations extracted")
    embeddings: int = Field(description="Total embeddings generated")
    
    # Pipeline
    queued_jobs: int = Field(description="Jobs waiting to be processed")
    running_jobs: int = Field(description="Jobs currently being processed")
    completed_jobs: int = Field(description="Jobs completed successfully")
    failed_jobs: int = Field(description="Jobs that failed")
    workers: int = Field(description="Number of active workers")
    oldest_job_age_seconds: Optional[float] = Field(default=None, description="Age of oldest queued job")
    
    # System
    database_status: str = Field(description="Database connection status")
    watcher_status: str = Field(description="File watcher status")
    job_processor_status: str = Field(description="Job processor status")
    api_status: str = Field(description="API status")


class ActivityEvent(BaseModel):
    """A single activity event."""
    timestamp: str = Field(description="ISO timestamp of event")
    level: str = Field(description="Event level (info, warning, error)")
    message: str = Field(description="Event message")
    details: Optional[dict] = Field(default=None, description="Additional event details")


class ActivityFeedResponse(BaseModel):
    """Activity feed response."""
    events: list[ActivityEvent] = Field(description="Recent events")
    count: int = Field(description="Total events returned")
    since: Optional[str] = Field(default=None, description="Oldest event timestamp")


class JobRecord(BaseModel):
    """A job record."""
    id: int
    document_id: int
    document_path: Optional[str] = None
    job_type: str
    status: str
    worker_id: Optional[str] = None
    attempt_count: int
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    age_seconds: Optional[float] = None
    error_message: Optional[str] = None


class JobQueueResponse(BaseModel):
    """Job queue response."""
    jobs: list[JobRecord]
    total: int
    filters: dict
    counts: dict


class DocumentJourneyResponse(BaseModel):
    """Document processing journey."""
    document_id: int
    path: str
    extension: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    created_at: Optional[str] = None
    indexed_at: Optional[str] = None
    jobs: list[JobRecord]
    lifecycle_states: list[str]


class ExtractionResultsResponse(BaseModel):
    """Extraction results for a document."""
    document_id: int
    path: str
    entities: list[dict]
    events: list[dict]
    locations: list[dict]
    content_preview: Optional[str] = None


class DocumentListResponse(BaseModel):
    """List of documents."""
    documents: list[dict]
    total: int


# ============================================================================
# Helper Functions
# ============================================================================

def _get_db_counts(backend: StorageBackend) -> dict:
    """Get all database counts in a single query."""
    counts = {
        'documents': 0,
        'entities': 0,
        'events': 0,
        'locations': 0,
        'relationships': 0,
        'embeddings': 0,
    }
    
    if not backend or not hasattr(backend, '_get_connection'):
        return counts
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Count documents
        cur.execute("SELECT COUNT(*) FROM documents")
        counts['documents'] = cur.fetchone()[0] or 0
        
        # Count entities
        cur.execute("SELECT COUNT(*) FROM entities")
        counts['entities'] = cur.fetchone()[0] or 0
        
        # Count events
        cur.execute("SELECT COUNT(*) FROM events")
        counts['events'] = cur.fetchone()[0] or 0
        
        # Count locations
        cur.execute("SELECT COUNT(*) FROM locations")
        counts['locations'] = cur.fetchone()[0] or 0
        
        # Count relationships
        cur.execute("SELECT COUNT(*) FROM relationships")
        counts['relationships'] = cur.fetchone()[0] or 0
        
        # Count embeddings (if table exists)
        try:
            cur.execute("SELECT COUNT(*) FROM document_embeddings")
            counts['embeddings'] = cur.fetchone()[0] or 0
        except Exception:
            counts['embeddings'] = 0
        
        cur.close()
        conn.close()
    except Exception as e:
        pass
    
    return counts


def _get_job_counts(backend: StorageBackend) -> dict:
    """Get job queue counts."""
    counts = {
        'queued': 0,
        'in_progress': 0,
        'completed': 0,
        'failed': 0,
    }
    
    if not backend or not hasattr(backend, '_get_connection'):
        return counts
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT status, COUNT(*) as count 
            FROM document_jobs 
            GROUP BY status
        """)
        
        for row in cur.fetchall():
            status = row[0]
            count = row[1]
            if status == 'QUEUED':
                counts['queued'] = count
            elif status == 'IN_PROGRESS':
                counts['in_progress'] = count
            elif status == 'COMPLETED':
                counts['completed'] = count
            elif status in ('FAILED', 'FAILED_PERMANENT'):
                counts['failed'] += count
        
        cur.close()
        conn.close()
    except Exception:
        pass
    
    return counts


def _get_oldest_job_age(backend: StorageBackend) -> Optional[float]:
    """Get age of oldest queued job in seconds."""
    if not backend or not hasattr(backend, '_get_connection'):
        return None
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT EXTRACT(EPOCH FROM (NOW() - created_at)) as age_seconds
            FROM document_jobs
            WHERE status = 'QUEUED'
            ORDER BY created_at ASC
            LIMIT 1
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row and row[0]:
            return round(float(row[0]), 1)
    except Exception:
        pass
    
    return None


def _format_job_record(row: tuple, conn) -> JobRecord:
    """Format a job row into a JobRecord."""
    job_id, doc_id, job_type, status, worker_id, attempt_count, created_at, started_at, completed_at, error_msg, doc_path = row
    
    # Calculate age
    age_seconds = None
    if created_at:
        try:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if created_at.tzinfo:
                age_seconds = (now - created_at).total_seconds()
            else:
                age_seconds = (now - created_at.replace(tzinfo=None)).total_seconds()
            age_seconds = round(age_seconds, 1)
        except Exception:
            pass
    
    return JobRecord(
        id=job_id,
        document_id=doc_id,
        document_path=doc_path,
        job_type=job_type,
        status=status,
        worker_id=worker_id,
        attempt_count=attempt_count,
        created_at=created_at.isoformat() + "Z" if created_at else None,
        started_at=started_at.isoformat() + "Z" if started_at else None,
        completed_at=completed_at.isoformat() + "Z" if completed_at else None,
        age_seconds=age_seconds,
        error_message=error_msg
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/overview",
    response_model=SystemOverviewResponse,
    summary="Get system overview"
)
async def get_system_overview(
    backend: StorageBackend = Depends(get_storage_backend)
) -> SystemOverviewResponse:
    """
    Get complete system overview for the operations dashboard.
    
    Returns statistics for:
    - Filesystem: files, documents, directories, watched paths, storage
    - Knowledge: entities, relationships, events, locations, embeddings
    - Pipeline: job queue statistics and workers
    - System: status of all components
    """
    from api.app_state import get_app_state
    state = get_app_state()
    
    # Get database counts
    db_counts = _get_db_counts(backend)
    
    # Get job counts
    job_counts = _get_job_counts(backend)
    
    # Get oldest job age
    oldest_job_age = _get_oldest_job_age(backend)
    
    # Determine statuses
    db_status = "CONNECTED" if state.database_connected else "DISCONNECTED"
    if state._persistence_available and state._schema_ready:
        db_status = "CONNECTED"
    elif state._persistence_available and not state._schema_ready:
        db_status = "SCHEMA_ERROR"
    
    watcher_status = "RUNNING" if state.watcher_active else "STOPPED"
    
    # Count workers
    worker_count = 0
    if state.job_processor_active:
        worker_count = 1
    
    job_processor_status = "ACTIVE" if state.job_processor_active else "STOPPED"
    
    return SystemOverviewResponse(
        files=db_counts['documents'],  # For now, files = documents
        documents=db_counts['documents'],
        directories=1,  # Single library root for now
        watched_paths=1,
        storage_used_bytes=None,
        entities=db_counts['entities'],
        relationships=db_counts['relationships'],
        events=db_counts['events'],
        locations=db_counts['locations'],
        embeddings=db_counts['embeddings'],
        queued_jobs=job_counts['queued'],
        running_jobs=job_counts['in_progress'],
        completed_jobs=job_counts['completed'],
        failed_jobs=job_counts['failed'],
        workers=worker_count,
        oldest_job_age_seconds=oldest_job_age,
        database_status=db_status,
        watcher_status=watcher_status,
        job_processor_status=job_processor_status,
        api_status="HEALTHY"
    )


@router.get(
    "/activity",
    response_model=ActivityFeedResponse,
    summary="Get activity feed"
)
async def get_activity_feed(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum events to return"),
    since: Optional[str] = Query(default=None, description="Return events after this ISO timestamp"),
    backend: StorageBackend = Depends(get_storage_backend)
) -> ActivityFeedResponse:
    """
    Get recent activity events in reverse chronological order.
    
    This provides a live feed of what's happening in the system,
    similar to a tail -f of the system logs.
    """
    events = []
    oldest_timestamp = None
    
    if not backend or not hasattr(backend, '_get_connection'):
        return ActivityFeedResponse(events=[], count=0)
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Build query for job events
        query = """
            SELECT 
                j.created_at as timestamp,
                'info' as level,
                CASE 
                    WHEN j.status = 'QUEUED' THEN 'queued: ' || j.job_type || ' for doc ' || COALESCE(d.path, j.document_id::text)
                    WHEN j.status = 'IN_PROGRESS' THEN 'started: ' || j.job_type
                    WHEN j.status = 'COMPLETED' THEN 'completed: ' || j.job_type
                    WHEN j.status = 'FAILED' THEN 'failed: ' || j.job_type
                    ELSE j.status || ': ' || j.job_type
                END as message,
                jsonb_build_object(
                    'job_id', j.id,
                    'document_id', j.document_id,
                    'job_type', j.job_type,
                    'worker_id', j.worker_id,
                    'error_message', j.error_message
                ) as details
            FROM document_jobs j
            LEFT JOIN documents d ON j.document_id = d.id
        """
        
        params = []
        if since:
            query += " WHERE j.created_at > %s"
            params.append(since)
        
        query += " ORDER BY j.created_at DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        
        for row in cur.fetchall():
            timestamp, level, message, details = row
            if timestamp and oldest_timestamp is None:
                oldest_timestamp = timestamp.isoformat() + "Z"
            
            events.append(ActivityEvent(
                timestamp=timestamp.isoformat() + "Z" if timestamp else datetime.utcnow().isoformat() + "Z",
                level=level,
                message=message,
                details=details
            ))
        
        # Also add document discovery events
        if len(events) < limit:
            query2 = """
                SELECT 
                    created_at as timestamp,
                    'info' as level,
                    'discovered: ' || path as message,
                    jsonb_build_object(
                        'document_id', id,
                        'status', status
                    ) as details
                FROM documents
            """
            
            params2 = []
            if since:
                query2 += " WHERE created_at > %s"
                params2.append(since)
            
            query2 += " ORDER BY created_at DESC LIMIT %s"
            params2.append(limit - len(events))
            
            cur.execute(query2, params2)
            
            for row in cur.fetchall():
                timestamp, level, message, details = row
                events.append(ActivityEvent(
                    timestamp=timestamp.isoformat() + "Z" if timestamp else datetime.utcnow().isoformat() + "Z",
                    level=level,
                    message=message,
                    details=details
                ))
        
        # Sort by timestamp descending
        events.sort(key=lambda x: x.timestamp, reverse=True)
        events = events[:limit]
        
        cur.close()
        conn.close()
        
    except Exception as e:
        events.append(ActivityEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level="error",
            message=f"Error fetching activity: {str(e)}",
            details=None
        ))
    
    return ActivityFeedResponse(
        events=events,
        count=len(events),
        since=oldest_timestamp
    )


@router.get(
    "/jobs",
    response_model=JobQueueResponse,
    summary="Get job queue"
)
async def get_job_queue(
    status: Optional[str] = Query(default=None, description="Filter by status (QUEUED, IN_PROGRESS, COMPLETED, FAILED)"),
    job_type: Optional[str] = Query(default=None, description="Filter by job type"),
    document_id: Optional[int] = Query(default=None, description="Filter by document ID"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    backend: StorageBackend = Depends(get_storage_backend)
) -> JobQueueResponse:
    """
    Get job queue with optional filtering.
    
    Supports filtering by:
    - status: QUEUED, IN_PROGRESS, COMPLETED, FAILED, FAILED_PERMANENT
    - job_type: extract_text, extract_entities, extract_events, extract_locations, generate_embeddings
    - document_id: specific document
    """
    jobs = []
    total = 0
    counts = {'queued': 0, 'in_progress': 0, 'completed': 0, 'failed': 0}
    
    if not backend or not hasattr(backend, '_get_connection'):
        return JobQueueResponse(jobs=[], total=0, filters={}, counts=counts)
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Build WHERE clause
        conditions = []
        params = []
        
        if status:
            conditions.append("j.status = %s")
            params.append(status.upper())
        
        if job_type:
            conditions.append("j.job_type = %s")
            params.append(job_type)
        
        if document_id is not None:
            conditions.append("j.document_id = %s")
            params.append(document_id)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get counts
        cur.execute(f"""
            SELECT status, COUNT(*) 
            FROM document_jobs 
            GROUP BY status
        """)
        
        for row in cur.fetchall():
            if row[0] == 'QUEUED':
                counts['queued'] = row[1]
            elif row[0] == 'IN_PROGRESS':
                counts['in_progress'] = row[1]
            elif row[0] == 'COMPLETED':
                counts['completed'] = row[1]
            elif row[0] in ('FAILED', 'FAILED_PERMANENT'):
                counts['failed'] += row[1]
        
        # Get total
        cur.execute(f"SELECT COUNT(*) FROM document_jobs WHERE {where_clause}", params)
        total = cur.fetchone()[0] or 0
        
        # Get jobs
        query = f"""
            SELECT 
                j.id, j.document_id, j.job_type, j.status, j.worker_id,
                j.attempt_count, j.created_at, j.started_at, j.completed_at,
                j.error_message, d.path
            FROM document_jobs j
            LEFT JOIN documents d ON j.document_id = d.id
            WHERE {where_clause}
            ORDER BY j.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        cur.execute(query, params)
        
        for row in cur.fetchall():
            jobs.append(_format_job_record(row, conn))
        
        cur.close()
        conn.close()
        
    except Exception as e:
        pass
    
    return JobQueueResponse(
        jobs=jobs,
        total=total,
        filters={'status': status, 'job_type': job_type, 'document_id': document_id},
        counts=counts
    )


@router.get(
    "/documents/{document_id}/journey",
    response_model=DocumentJourneyResponse,
    summary="Get document journey"
)
async def get_document_journey(
    document_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
) -> DocumentJourneyResponse:
    """
    Get the complete processing journey for a document.
    
    Shows all lifecycle states and associated jobs.
    """
    path = None
    extension = None
    file_size = None
    status = None
    created_at = None
    indexed_at = None
    jobs = []
    
    # Define lifecycle states in order
    LIFECYCLE_STATES = [
        'DISCOVERED',
        'METADATA_INDEXED',
        'CONTENT_EXTRACTED',
        'ENTITY_EXTRACTED',
        'EVENT_EXTRACTED',
        'LOCATION_EXTRACTED',
        'RELATIONSHIPS_BUILT',
        'EMBEDDED',
        'COMPLETE'
    ]
    
    if not backend or not hasattr(backend, '_get_connection'):
        return DocumentJourneyResponse(
            document_id=document_id,
            path="NOT FOUND",
            status="UNKNOWN",
            jobs=[],
            lifecycle_states=LIFECYCLE_STATES
        )
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Get document info
        cur.execute("""
            SELECT path, extension, file_size, status, created_at, indexed_at
            FROM documents WHERE id = %s
        """, (document_id,))
        
        row = cur.fetchone()
        if row:
            path = row[0]
            extension = row[1]
            file_size = row[2]
            status = row[3]
            created_at = row[4].isoformat() + "Z" if row[4] else None
            indexed_at = row[5].isoformat() + "Z" if row[5] else None
        
        # Get jobs for document
        cur.execute("""
            SELECT 
                j.id, j.document_id, j.job_type, j.status, j.worker_id,
                j.attempt_count, j.created_at, j.started_at, j.completed_at,
                j.error_message, d.path
            FROM document_jobs j
            LEFT JOIN documents d ON j.document_id = d.id
            WHERE j.document_id = %s
            ORDER BY j.created_at ASC
        """, (document_id,))
        
        for row in cur.fetchall():
            jobs.append(_format_job_record(row, conn))
        
        cur.close()
        conn.close()
        
    except Exception as e:
        pass
    
    return DocumentJourneyResponse(
        document_id=document_id,
        path=path or "NOT FOUND",
        extension=extension,
        file_size=file_size,
        status=status or "UNKNOWN",
        created_at=created_at,
        indexed_at=indexed_at,
        jobs=jobs,
        lifecycle_states=LIFECYCLE_STATES
    )


@router.get(
    "/documents/{document_id}/extractions",
    response_model=ExtractionResultsResponse,
    summary="Get document extraction results"
)
async def get_document_extractions(
    document_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
) -> ExtractionResultsResponse:
    """
    Get all extraction results for a document.
    
    Returns entities, events, locations, and content preview.
    """
    path = None
    entities = []
    events = []
    locations = []
    content_preview = None
    
    if not backend or not hasattr(backend, '_get_connection'):
        return ExtractionResultsResponse(
            document_id=document_id,
            path="NOT FOUND",
            entities=[],
            events=[],
            locations=[]
        )
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Get document path
        cur.execute("SELECT path FROM documents WHERE id = %s", (document_id,))
        row = cur.fetchone()
        if row:
            path = row[0]
        
        # Get entities
        cur.execute("""
            SELECT e.id, e.type, e.value, e.normalized_value
            FROM entities e
            JOIN document_entities de ON e.id = de.entity_id
            WHERE de.document_id = %s
        """, (document_id,))
        
        for row in cur.fetchall():
            entities.append({
                'id': row[0],
                'type': row[1],
                'value': row[2],
                'normalized': row[3]
            })
        
        # Get events
        cur.execute("""
            SELECT e.id, e.timestamp, e.event_type, e.description
            FROM events e
            JOIN document_events de ON e.id = de.event_id
            WHERE de.document_id = %s
        """, (document_id,))
        
        for row in cur.fetchall():
            events.append({
                'id': row[0],
                'timestamp': row[1],
                'type': row[2],
                'description': row[3]
            })
        
        # Get locations
        cur.execute("""
            SELECT l.id, l.name, l.type, l.city, l.state, l.country
            FROM locations l
            JOIN document_locations dl ON l.id = dl.location_id
            WHERE dl.document_id = %s
        """, (document_id,))
        
        for row in cur.fetchall():
            locations.append({
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'city': row[3],
                'state': row[4],
                'country': row[5]
            })
        
        # Get content preview
        cur.execute("""
            SELECT content FROM document_content 
            WHERE document_id = %s
            LIMIT 1
        """, (document_id,))
        
        row = cur.fetchone()
        if row and row[0]:
            content_preview = row[0][:500] + "..." if len(row[0]) > 500 else row[0]
        
        cur.close()
        conn.close()
        
    except Exception as e:
        pass
    
    return ExtractionResultsResponse(
        document_id=document_id,
        path=path or "NOT FOUND",
        entities=entities,
        events=events,
        locations=locations,
        content_preview=content_preview
    )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List documents"
)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    backend: StorageBackend = Depends(get_storage_backend)
) -> DocumentListResponse:
    """
    List documents with optional filtering.
    """
    documents = []
    total = 0
    
    if not backend or not hasattr(backend, '_get_connection'):
        return DocumentListResponse(documents=[], total=0)
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Count total
        if status:
            cur.execute("SELECT COUNT(*) FROM documents WHERE status = %s", (status,))
        else:
            cur.execute("SELECT COUNT(*) FROM documents")
        total = cur.fetchone()[0] or 0
        
        # Get documents
        if status:
            cur.execute("""
                SELECT id, path, extension, file_size, status, character_count, parser, created_at
                FROM documents 
                WHERE status = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (status, limit, offset))
        else:
            cur.execute("""
                SELECT id, path, extension, file_size, status, character_count, parser, created_at
                FROM documents 
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
        
        for row in cur.fetchall():
            documents.append({
                'id': row[0],
                'path': row[1],
                'extension': row[2],
                'file_size': row[3],
                'status': row[4],
                'character_count': row[5],
                'parser': row[6],
                'created_at': row[7].isoformat() + "Z" if row[7] else None
            })
        
        cur.close()
        conn.close()
        
    except Exception:
        pass
    
    return DocumentListResponse(documents=documents, total=total)
