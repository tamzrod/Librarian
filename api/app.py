"""Librarian REST API - FastAPI Application.

Single-library architecture: operates on configured library root.
See ADR 0005 for details.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from api.routes import questions, collections
from api.dependencies import get_storage_backend, MockBackend
from api.app_state import initialize_app, shutdown_app, get_app_state


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Library root from environment
LIBRARY_ROOT = os.environ.get("LIBRARIAN_LIBRARY_ROOT", "/library")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Initializing Librarian API...")
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
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/v1/status")
async def get_status():
    """
    Get API status with library statistics.
    
    Returns counts for documents, entities, events, locations,
    as well as watcher status and last scan time.
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
        "status": "healthy",
        "library_root": state.library_root,
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
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/v1/stats")
async def get_stats(
    backend: MockBackend = Depends(get_storage_backend)
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


@app.get("/api/v1/timeline")
async def get_timeline(
    backend: MockBackend = Depends(get_storage_backend),
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