"""Librarian REST API - FastAPI Application.

Single-library architecture: operates on configured library root.
See ADR 0005 for details.
"""

import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Query, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uuid

from api.routes import questions, collections, pipeline, operations, timeline, explorer, trace, settings
from api.dependencies import get_storage_backend, MockBackend
from storage.backend import StorageBackend
from api.app_state import initialize_app, shutdown_app, get_app_state
from environment import get_library_root, get_librarian_data_root


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Library root from environment (user files - read-only)
LIBRARY_ROOT = get_library_root()

# Librarian data root from environment (derived artifacts - writable)
LIBRARIAN_DATA_ROOT = get_librarian_data_root()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Initializing Librarian API...")
    logger.info("Library root: %s", LIBRARY_ROOT)
    initialize_app()
    logger.info("Librarian API initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down Librarian API...")
    shutdown_app()
    logger.info("Librarian API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Librarian API",
    description="Evidence retrieval engine for bounded file collections. Single-library architecture.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Include routers with versioned prefix
app.include_router(questions.router, prefix="/api/v1")
app.include_router(collections.router, prefix="/api/v1")
app.include_router(pipeline.router, prefix="/api/v1")
app.include_router(operations.router, prefix="/api/v1")
app.include_router(timeline.router, prefix="/api/v1")
app.include_router(explorer.router, prefix="/api/v1")
app.include_router(trace.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")


# E5: Thumbnail serving endpoint
@app.get("/thumbnails/{path:path}")
async def get_thumbnail(path: str):
    """
    Serve thumbnail files from librarian-managed storage.

    E5: Thumbnail endpoint for serving generated thumbnails.
    Thumbnails are stored in librarian-data/thumbnails directory.

    API CONTRACT - Cache Miss Handling:
    ================================
    Thumbnails are DISPOSABLE CACHE, not evidence.
    A missing thumbnail is a CACHE MISS, NOT corruption.

    If file exists:
        - Return thumbnail
    If file missing:
        - Return placeholder image (1x1 pixel JPEG)
        - Optionally queue regeneration job (if document_id can be extracted)

    The database thumbnail_path is ADVISORY ONLY.
    Filesystem existence is AUTHORITATIVE.

    Browser request: /thumbnails/<filename>
    Filesystem path: /librarian-data/thumbnails/<filename>

    Note: nginx proxy_pass strips the /thumbnails/ prefix, so 'path' already
    contains the full relative path including 'thumbnails/' if stored with it.
    We strip any leading 'thumbnails/' to avoid double path segments.
    """
    # Validate LIBRARIAN_DATA_ROOT is set
    if not LIBRARIAN_DATA_ROOT:
        logger.error("LIBRARIAN_DATA_ROOT not configured")
        return JSONResponse({"error": "Thumbnail service misconfigured"}, status_code=500)

    # Ensure path is a safe string (prevent path traversal)
    safe_path = str(path).replace("..", "")

    # Strip leading 'thumbnails/' to avoid double path segments
    # nginx proxy_pass with trailing slash strips /thumbnails/ from the URL
    # If database stored 'thumbnails/xxx.jpg' and frontend calls /thumbnails/thumbnails/xxx.jpg,
    # nginx sends 'thumbnails/xxx.jpg' which would create /librarian-data/thumbnails/thumbnails/xxx.jpg
    if safe_path.startswith("thumbnails/"):
        safe_path = safe_path[len("thumbnails/"):]

    # Serve from librarian-data/thumbnails directory
    thumbnail_full_path = Path(LIBRARIAN_DATA_ROOT) / "thumbnails" / safe_path

    if not thumbnail_full_path.is_absolute():
        logger.error(f"Invalid thumbnail path construction: {thumbnail_full_path}")
        return JSONResponse({"error": "Invalid thumbnail path"}, status_code=500)

    # CACHE MISS HANDLING: Check filesystem existence
    # This is the authoritative check - database thumbnail_path is advisory only
    if thumbnail_full_path.exists() and thumbnail_full_path.is_file():
        # Cache hit - return the thumbnail
        return FileResponse(
            str(thumbnail_full_path),
            media_type="image/jpeg",
            filename=thumbnail_full_path.name
        )

    # Cache miss - thumbnail file does not exist on filesystem
    # This is NOT corruption - thumbnails are disposable cache
    logger.info(f"Thumbnail cache miss: {thumbnail_full_path}")

    # Try to extract document_id from filename (format: {doc_id}_{original_name}_thumb.jpg)
    document_id = _extract_document_id_from_thumbnail_filename(safe_path)

    # Attempt to queue regeneration job
    if document_id:
        queue_regeneration = os.environ.get("THUMBNAIL_AUTO_REGENERATE", "true").lower() == "true"
        if queue_regeneration:
            try:
                _queue_thumbnail_regeneration(document_id)
                logger.info(f"Queued thumbnail regeneration for document {document_id}")
            except Exception as e:
                logger.warning(f"Failed to queue thumbnail regeneration: {e}")

    # Return placeholder image
    return _get_thumbnail_placeholder()


def _extract_document_id_from_thumbnail_filename(filename: str) -> Optional[int]:
    """
    Extract document ID from thumbnail filename.

    Thumbnail filename format: {document_id}_{original_name}_thumb.jpg
    Example: 1017_IMG_001_thumb.jpg -> document_id = 1017

    Returns:
        Document ID as integer, or None if extraction fails
    """
    try:
        # Get just the filename (not path)
        name = filename.rsplit("/", 1)[-1] if "/" in filename else filename
        # Remove extension
        name = name.rsplit(".", 1)[0]
        # Remove _thumb suffix
        if name.endswith("_thumb"):
            name = name[:-6]
        # Split by underscore and get first part (document ID)
        parts = name.split("_")
        if parts:
            return int(parts[0])
    except (ValueError, IndexError):
        pass
    return None


def _queue_thumbnail_regeneration(document_id: int):
    """
    Queue a thumbnail regeneration job for a document.

    This is called when a cache miss is detected.
    """
    from api.app_state import get_app_state

    state = get_app_state()
    if state.backend and hasattr(state.backend, 'create_jobs_for_document'):
        # Create generate_thumbnail job with high priority
        job_ids = state.backend.create_jobs_for_document(document_id, ['generate_thumbnail'])
        if job_ids:
            logger.info(f"Created thumbnail regeneration job {job_ids[0]} for document {document_id}")


def _get_thumbnail_placeholder() -> FileResponse:
    """
    Return a 1x1 pixel placeholder JPEG image.

    This is returned when a thumbnail is not found (cache miss).
    The placeholder is embedded as bytes to avoid external dependencies.
    """
    # 1x1 pixel gray JPEG (valid JPEG format)
    # This is a minimal valid JPEG file
    import io
    PLACEHOLDER_JPEG = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n'
        b'\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d'
        b'\x1a\x1c\x1c\x20\x1c#\x1c ,#\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        b'\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00'
        b'\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00'
        b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf '
        b'\xff\xd9'
    )
    return FileResponse(
        io.BytesIO(PLACEHOLDER_JPEG),
        media_type="image/jpeg",
        filename="placeholder.jpg"
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Librarian API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "library_root": LIBRARY_ROOT
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with detailed status.
    
    Returns database connectivity, worker count, queue depth,
    and oldest queued job age.
    """
    from api.app_state import get_app_state
    state = get_app_state()
    
    # Database status
    db_connected = state.database_connected
    db_schema_ready = state._schema_ready
    
    # Job counts
    queued_jobs = 0
    running_jobs = 0
    oldest_job_age = None
    
    try:
        if state.backend and hasattr(state.backend, 'get_job_status_counts'):
            job_counts = state.backend.get_job_status_counts()
            queued_jobs = job_counts.get('queued', 0)
            running_jobs = job_counts.get('in_progress', 0)
        
        if state.backend and hasattr(state.backend, '_get_connection'):
            conn = state.backend._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT EXTRACT(EPOCH FROM (NOW() - created_at)) as age_seconds
                FROM document_jobs
                WHERE status = 'QUEUED'
                ORDER BY created_at ASC
                LIMIT 1
            """)
            row = cur.fetchone()
            if row and row[0]:
                oldest_job_age = round(float(row[0]), 1)
            cur.close()
            conn.close()
    except Exception:
        pass
    
    # Worker count
    worker_count = 1 if state.job_processor_active else 0
    
    # Overall health
    healthy = db_connected and db_schema_ready
    status = "healthy" if healthy else "degraded"
    
    return {
        "status": status,
        "database": {
            "connected": db_connected,
            "schema_ready": db_schema_ready
        },
        "queue": {
            "queued": queued_jobs,
            "running": running_jobs,
            "oldest_job_age_seconds": oldest_job_age
        },
        "workers": worker_count,
        "watcher_active": state.watcher_active,
        "job_processor_active": state.job_processor_active
    }


@app.get("/api/v1/status")
async def get_status():
    """
    Get API status with library statistics.
    
    Returns counts for documents, entities, events, locations,
    as well as watcher status, last scan time, and database health.
    """
    state = get_app_state()
    
    # Determine database status
    db_connected = state.database_connected
    db_schema_ready = state._schema_ready
    db_persistence_available = state._persistence_available
    
    # Get document counts, tracking any errors
    try:
        doc_count = len(state.backend.search_documents()) if state.backend else 0
        entity_count = len(state.backend.search_entities()) if state.backend else 0
        event_count = len(state.backend.search_events()) if state.backend else 0
        location_count = len(state.backend.search_locations()) if state.backend else 0
        db_error = None
    except Exception as e:
        doc_count = entity_count = event_count = location_count = 0
        db_error = str(e)
        state.record_persistence_error(db_error, "status_query")
    
    # Determine overall status
    if db_persistence_available and db_schema_ready and not db_error:
        overall_status = "healthy"
    elif db_persistence_available and not db_error:
        overall_status = "degraded"  # Connected but schema issues
    elif db_persistence_available and db_error:
        overall_status = "degraded"  # Connected but query failed
    else:
        overall_status = "degraded"  # Persistence unavailable
    
    return {
        "status": overall_status,
        "library_root": state.library_root,
        "database": {
            "connected": db_connected,
            "schema_ready": db_schema_ready,
            "persistence_available": db_persistence_available,
            "error": db_error
        },
        "documents": {
            "total": doc_count,
            "indexed": doc_count
        },
        "entities": {
            "total": entity_count
        },
        "events": {
            "total": event_count
        },
        "locations": {
            "total": location_count
        },
        "watcher_active": state.watcher_active,
        "initial_scan_complete": state._initial_scan_complete,
        "last_scan": state._last_scan.isoformat() + "Z" if state._last_scan else None,
        "persistence_errors": state._persistence_errors[-5:] if state._persistence_errors else [],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/v1/stats")
async def get_stats(
    backend: StorageBackend = Depends(get_storage_backend)
):
    """
    Get library statistics.
    
    Returns counts for documents, entities, events, locations,
    parser information, and watcher status.
    """
    state = get_app_state()
    
    try:
        doc_count = len(state.backend.search_documents()) if state.backend else 0
        entity_count = len(state.backend.search_entities()) if state.backend else 0
        event_count = len(state.backend.search_events()) if state.backend else 0
        location_count = len(state.backend.search_locations()) if state.backend else 0
    except Exception:
        doc_count = entity_count = event_count = location_count = 0
    
    return {
        "library_root": state.library_root,
        "database": {
            "connected": state.database_connected,
            "schema_ready": state._schema_ready,
            "persistence_available": state._persistence_available
        },
        "documents": {
            "total": doc_count,
            "indexed": doc_count
        },
        "entities": {
            "total": entity_count
        },
        "events": {
            "total": event_count
        },
        "locations": {
            "total": location_count
        },
        "parsers": {
            "count": 9,
            "types": ["json", "yaml", "csv", "xml", "ini", "toml", "python", "image", "text"]
        },
        "watcher": {
            "active": state.watcher_active,
            "last_scan": state._last_scan.isoformat() + "Z" if state._last_scan else None
        },
        "initial_scan_complete": state._initial_scan_complete,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/v1/documents/status")
async def get_document_status_counts():
    """
    Get count of documents grouped by processing status.
    
    Document Lifecycle States:
    - DISCOVERED: File detected, metadata not yet indexed
    - METADATA_INDEXED: Metadata extracted, content not yet processed
    - CONTENT_EXTRACTED: Text content extracted (future phase)
    - ENTITY_EXTRACTED: Entities identified (future phase)
    - RELATIONSHIPS_BUILT: Relationships mapped (future phase)
    - EMBEDDED: Vector embeddings generated (future phase)
    - COMPLETE: All processing stages complete
    - FAILED: Processing failed after max retries
    """
    state = get_app_state()
    
    try:
        if state.backend and hasattr(state.backend, 'get_document_status_counts'):
            status_counts = state.backend.get_document_status_counts()
        else:
            status_counts = {}
    except Exception:
        status_counts = {}
    
    return {
        "status_counts": status_counts,
        "total": sum(status_counts.values()),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/v1/jobs/status")
async def get_job_status_counts():
    """
    Get count of jobs grouped by status.
    
    Job Status States:
    - QUEUED: Job created, waiting for worker
    - IN_PROGRESS: Worker has claimed the job
    - COMPLETED: Job finished successfully
    - FAILED: Job failed after all retries
    - CANCELLED: Job cancelled by user
    """
    state = get_app_state()
    
    try:
        if state.backend and hasattr(state.backend, 'get_job_status_counts'):
            status_counts = state.backend.get_job_status_counts()
        else:
            status_counts = {}
    except Exception:
        status_counts = {}
    
    return {
        "status_counts": status_counts,
        "total": sum(status_counts.values()),
        "queued": status_counts.get('QUEUED', 0),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/v1/jobs")
async def get_jobs(
    state = Depends(get_app_state),
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    status: Optional[str] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(50, ge=1, le=100, description="Max results")
):
    """
    Get jobs with optional filtering.
    
    If document_id is provided, returns jobs for that document.
    Otherwise, returns recent jobs across all documents.
    """
    try:
        if document_id and state.backend and hasattr(state.backend, 'get_document_jobs'):
            jobs = state.backend.get_document_jobs(document_id)
        else:
            # Get jobs from search or default to empty list
            jobs = []
    except Exception:
        jobs = []
    
    # Apply filters
    if status:
        jobs = [j for j in jobs if j.get('status') == status]
    if job_type:
        jobs = [j for j in jobs if j.get('job_type') == job_type]
    
    # Apply limit
    jobs = jobs[:limit]
    
    return {
        "data": jobs,
        "filters": {
            "document_id": document_id,
            "status": status,
            "job_type": job_type
        },
        "pagination": {
            "total": len(jobs),
            "limit": limit,
            "returned": len(jobs)
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/api/v1/documents/{document_id}/jobs")
async def create_document_jobs(
    document_id: int,
    job_types: Optional[list] = Body(None, description="List of job types to create"),
    state = Depends(get_app_state)
):
    """
    Create jobs for a document.
    
    Job types (if not specified, creates default set):
    - extract_text: Extract text content
    - extract_entities: Identify entities in text
    - extract_events: Extract date/time references
    - extract_locations: Extract location references
    """
    try:
        if state.backend and hasattr(state.backend, 'create_jobs_for_document'):
            job_ids = state.backend.create_jobs_for_document(document_id, job_types)
            return {
                "created": len(job_ids),
                "job_ids": job_ids,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            return {"error": "Job queue not available"}, 503
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/v1/timeline")
async def get_timeline(
    backend: StorageBackend = Depends(get_storage_backend),
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    entity: Optional[str] = Query(None, description="Filter by entity"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=100, description="Max results")
):
    """
    Get timeline of events.
    
    Returns chronologically ordered events with optional filtering
    by date range, entity, or event type.
    """
    try:
        # Search for events with filters
        events = backend.search_events(
            date=start,
            month=end[:7] if end and len(end) >= 7 else None,  # Convert YYYY-MM-DD to YYYY-MM
            entity=entity,
            event_type=event_type
        )
        
        # Filter by date range if both start and end provided
        if start and end:
            filtered = []
            for event in events:
                ts = event.get("timestamp", "")
                if ts >= start and ts <= end:
                    filtered.append(event)
            events = filtered
        
        # Limit results
        events = events[:limit]
        
        return {
            "data": events,
            "filters": {
                "start": start,
                "end": end,
                "entity": entity,
                "event_type": event_type
            },
            "pagination": {
                "total": len(events),
                "limit": limit,
                "returned": len(events)
            }
        }
        
    except Exception as e:
        return {
            "data": [],
            "filters": {
                "start": start,
                "end": end,
                "entity": entity,
                "event_type": event_type
            },
            "pagination": {
                "total": 0,
                "limit": limit,
                "returned": 0
            },
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)