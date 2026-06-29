"""Pipeline status and job management API routes.

Provides observability into the document processing pipeline.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from api.dependencies import get_storage_backend
from storage.backend import StorageBackend


router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineStatusResponse(BaseModel):
    """Response schema for pipeline status."""
    documents: int = Field(description="Total documents indexed")
    queued_jobs: int = Field(description="Jobs waiting to be processed")
    running_jobs: int = Field(description="Jobs currently being processed")
    completed_jobs: int = Field(description="Jobs that completed successfully")
    failed_jobs: int = Field(description="Jobs that failed")
    workers: int = Field(description="Number of active workers")
    watcher_status: str = Field(description="File watcher status")
    database_status: str = Field(description="Database connection status")
    oldest_queued_job_age_seconds: Optional[float] = Field(
        default=None, 
        description="Age of oldest queued job in seconds"
    )
    job_processor_active: bool = Field(description="Whether job processor is running")


class JobSummary(BaseModel):
    """Summary of a job."""
    id: int
    document_id: int
    job_type: str
    status: str
    priority: int
    attempt_count: int
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None


class JobListResponse(BaseModel):
    """Response schema for listing jobs."""
    jobs: list[JobSummary]
    total: int
    filters: dict


class DocumentPipelineResponse(BaseModel):
    """Response schema for document pipeline status."""
    document_id: int
    path: str
    status: str
    jobs: list[JobSummary]


@router.get(
    "/status",
    response_model=PipelineStatusResponse,
    summary="Get pipeline status"
)
async def get_pipeline_status(
    backend: StorageBackend = Depends(get_storage_backend)
) -> PipelineStatusResponse:
    """
    Get the current status of the document processing pipeline.
    
    Returns counts for documents, jobs by status, worker information,
    and database connectivity.
    """
    from api.app_state import get_app_state
    state = get_app_state()
    
    # Get document count
    doc_count = 0
    try:
        if hasattr(backend, 'search_documents'):
            doc_count = len(backend.search_documents())
    except Exception:
        pass
    
    # Get job status counts
    job_counts = {
        'queued': 0,
        'in_progress': 0,
        'completed': 0,
        'failed': 0
    }
    oldest_queued_age = None
    
    try:
        if hasattr(backend, 'get_job_status_counts'):
            job_counts = backend.get_job_status_counts()
        
        # Calculate oldest queued job age
        if hasattr(backend, '_get_connection'):
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
            if row:
                oldest_queued_age = float(row[0]) if row[0] else None
            cur.close()
            conn.close()
    except Exception:
        pass
    
    # Determine statuses
    watcher_status = "RUNNING" if state.watcher_active else "STOPPED"
    db_status = "CONNECTED" if state.database_connected else "DISCONNECTED"
    
    # Count workers (job processors)
    worker_count = 0
    if state.job_processor_active:
        worker_count = 1
    # Could also query document_jobs for distinct worker_ids
    
    return PipelineStatusResponse(
        documents=doc_count,
        queued_jobs=job_counts.get('queued', 0),
        running_jobs=job_counts.get('in_progress', 0),
        completed_jobs=job_counts.get('completed', 0),
        failed_jobs=job_counts.get('failed', 0),
        workers=worker_count,
        watcher_status=watcher_status,
        database_status=db_status,
        oldest_queued_job_age_seconds=oldest_queued_age,
        job_processor_active=state.job_processor_active
    )


@router.get(
    "/jobs",
    response_model=JobListResponse,
    summary="List jobs with optional filters"
)
async def list_jobs(
    status: Optional[str] = Query(default=None, description="Filter by job status"),
    job_type: Optional[str] = Query(default=None, description="Filter by job type"),
    document_id: Optional[int] = Query(default=None, description="Filter by document ID"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    backend: StorageBackend = Depends(get_storage_backend)
) -> JobListResponse:
    """
    List jobs with optional filters.
    
    Supports filtering by status (QUEUED, IN_PROGRESS, COMPLETED, FAILED),
    job_type (extract_text, extract_entities, etc.), and document_id.
    """
    jobs = []
    total = 0
    
    try:
        if hasattr(backend, '_get_connection'):
            conn = backend._get_connection()
            cur = conn.cursor()
            
            # Build query
            where_clauses = []
            params = []
            
            if status:
                where_clauses.append("status = %s")
                params.append(status.upper())
            
            if job_type:
                where_clauses.append("job_type = %s")
                params.append(job_type)
            
            if document_id is not None:
                where_clauses.append("document_id = %s")
                params.append(document_id)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Count total
            count_sql = f"SELECT COUNT(*) FROM document_jobs WHERE {where_sql}"
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]
            
            # Fetch jobs
            query_sql = f"""
                SELECT id, document_id, job_type, status, priority, attempt_count,
                       created_at, started_at, completed_at, error_message, worker_id
                FROM document_jobs
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            cur.execute(query_sql, params)
            
            for row in cur.fetchall():
                jobs.append(JobSummary(
                    id=row[0],
                    document_id=row[1],
                    job_type=row[2],
                    status=row[3],
                    priority=row[4],
                    attempt_count=row[5],
                    created_at=row[6].isoformat() + "Z" if row[6] else None,
                    started_at=row[7].isoformat() + "Z" if row[7] else None,
                    completed_at=row[8].isoformat() + "Z" if row[8] else None,
                    error_message=row[9],
                    worker_id=row[10]
                ))
            
            cur.close()
            conn.close()
    except Exception as e:
        # Return empty results on error
        pass
    
    return JobListResponse(
        jobs=jobs,
        total=total,
        filters={
            "status": status,
            "job_type": job_type,
            "document_id": document_id,
            "limit": limit,
            "offset": offset
        }
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentPipelineResponse,
    summary="Get document pipeline status"
)
async def get_document_pipeline(
    document_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
) -> DocumentPipelineResponse:
    """
    Get the processing pipeline status for a specific document.
    
    Returns the document info and all associated jobs with their statuses.
    """
    doc_path = None
    doc_status = None
    jobs = []
    
    try:
        if hasattr(backend, '_get_connection'):
            conn = backend._get_connection()
            cur = conn.cursor()
            
            # Get document info
            cur.execute(
                "SELECT path, status FROM documents WHERE id = %s",
                (document_id,)
            )
            row = cur.fetchone()
            if row:
                doc_path = row[0]
                doc_status = row[1]
            
            # Get document jobs
            cur.execute("""
                SELECT id, document_id, job_type, status, priority, attempt_count,
                       created_at, started_at, completed_at, error_message, worker_id
                FROM document_jobs
                WHERE document_id = %s
                ORDER BY created_at ASC
            """, (document_id,))
            
            for row in cur.fetchall():
                jobs.append(JobSummary(
                    id=row[0],
                    document_id=row[1],
                    job_type=row[2],
                    status=row[3],
                    priority=row[4],
                    attempt_count=row[5],
                    created_at=row[6].isoformat() + "Z" if row[6] else None,
                    started_at=row[7].isoformat() + "Z" if row[7] else None,
                    completed_at=row[8].isoformat() + "Z" if row[8] else None,
                    error_message=row[9],
                    worker_id=row[10]
                ))
            
            cur.close()
            conn.close()
    except Exception as e:
        pass
    
    return DocumentPipelineResponse(
        document_id=document_id,
        path=doc_path or "unknown",
        status=doc_status or "UNKNOWN",
        jobs=jobs
    )
