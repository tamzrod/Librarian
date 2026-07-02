"""Trace API routes.

Operation TRACE v2: Spatial-temporal visualization layer for Librarian.
Provides unified access to photo metadata for map, timeline, and filter views.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from api.dependencies import get_storage_backend
from storage.backend import StorageBackend


router = APIRouter(prefix="/trace", tags=["trace"])


# =============================================================================
# Response Models
# =============================================================================

class TraceFilterOption(BaseModel):
    """Single filter option with selection state."""
    id: str = Field(description="Unique identifier for the filter")
    label: str = Field(description="Human-readable label")
    count: int = Field(description="Number of items matching this filter")
    checked: bool = Field(description="Whether this filter is currently selected")


class TraceFilterGroup(BaseModel):
    """Group of related filter options (collapsible)."""
    id: str = Field(description="Unique identifier for the group")
    label: str = Field(description="Human-readable label")
    expanded: bool = Field(description="Whether the group is currently expanded")
    options: list[TraceFilterOption] = Field(description="Available filter options")


class TraceFiltersResponse(BaseModel):
    """Available filters for the Trace view."""
    groups: list[TraceFilterGroup] = Field(description="Filter groups")
    total_items: int = Field(description="Total number of items across all filters")


class TraceMapMarker(BaseModel):
    """Photo marker for map display."""
    document_id: int = Field(description="Document ID")
    latitude: float = Field(description="GPS latitude")
    longitude: float = Field(description="GPS longitude")
    timestamp: Optional[str] = Field(default=None, description="Capture timestamp")
    camera: Optional[str] = Field(default=None, description="Camera make and model")
    camera_make: Optional[str] = Field(default=None, description="Camera manufacturer")
    camera_model: Optional[str] = Field(default=None, description="Camera model")
    filename: str = Field(description="Original filename")
    thumbnail_path: Optional[str] = Field(default=None, description="Thumbnail path")
    altitude: Optional[float] = Field(default=None, description="GPS altitude")
    collection_id: Optional[str] = Field(default=None, description="Collection ID")
    collection_name: Optional[str] = Field(default=None, description="Collection name")
    year: Optional[int] = Field(default=None, description="Capture year")


class TraceEventItem(BaseModel):
    """Event item for the event stream."""
    document_id: int = Field(description="Document ID")
    timestamp: Optional[str] = Field(default=None, description="Capture timestamp")
    camera: Optional[str] = Field(default=None, description="Camera make and model")
    location: Optional[str] = Field(default=None, description="Location name")
    latitude: Optional[float] = Field(default=None, description="GPS latitude")
    longitude: Optional[float] = Field(default=None, description="GPS longitude")
    filename: str = Field(description="Original filename")
    thumbnail_path: Optional[str] = Field(default=None, description="Thumbnail path")
    collection_name: Optional[str] = Field(default=None, description="Collection name")
    year: Optional[int] = Field(default=None, description="Capture year")


class TraceStats(BaseModel):
    """Statistics for the current trace data."""
    total: int = Field(description="Total number of photos")
    with_gps: int = Field(description="Photos with GPS coordinates")
    unique_cameras: int = Field(description="Unique camera make/model combinations")
    year_range: dict = Field(description="Year range")


class TraceDataResponse(BaseModel):
    """Unified response for trace data."""
    markers: list[TraceMapMarker] = Field(description="Map markers")
    events: list[TraceEventItem] = Field(description="Event stream items")
    stats: TraceStats
    pagination: dict


class TracePhotoDetail(BaseModel):
    """Full photo metadata for detail view."""
    document_id: int
    filename: str
    path: str
    timestamp: Optional[str] = None
    timestamp_digitized: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    width: int = 0
    height: int = 0
    orientation: Optional[int] = None
    file_format: str = "UNKNOWN"
    thumbnail_path: Optional[str] = None
    collection_name: Optional[str] = None
    extracted_at: Optional[str] = None


class TracePhotoDetailResponse(BaseModel):
    """Response for single photo detail."""
    photo: TracePhotoDetail


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/filters",
    response_model=TraceFiltersResponse,
    summary="Get available Trace filters"
)
async def get_trace_filters(
    backend: StorageBackend = Depends(get_storage_backend)
) -> TraceFiltersResponse:
    """
    Get available filters for the Trace view.
    
    Returns collapsible filter groups for:
    - Devices (cameras)
    - Collections
    - Years
    - Sources (GPS, OCR, AI, Manual)
    """
    if hasattr(backend, 'get_trace_filters'):
        result = backend.get_trace_filters()
        return TraceFiltersResponse(**result)
    
    # Fallback with empty filters
    return TraceFiltersResponse(
        groups=[],
        total_items=0
    )


@router.get(
    "/data",
    response_model=TraceDataResponse,
    summary="Get Trace data with filters"
)
async def get_trace_data(
    backend: StorageBackend = Depends(get_storage_backend),
    cameras: Optional[str] = Query(
        None,
        description="Comma-separated list of camera IDs to filter"
    ),
    collections: Optional[str] = Query(
        None,
        description="Comma-separated list of collection IDs to filter"
    ),
    years: Optional[str] = Query(
        None,
        description="Comma-separated list of years to filter"
    ),
    sources: Optional[str] = Query(
        None,
        description="Comma-separated list of sources (gps, ocr, ai, manual)"
    ),
    start_date: Optional[str] = Query(
        None,
        description="Start date filter (ISO format)"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date filter (ISO format)"
    ),
    include_unknown_device: bool = Query(
        False,
        description="Include photos with unknown device"
    ),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
) -> TraceDataResponse:
    """
    Get unified trace data with filters applied.
    
    Returns map markers and event stream items for the filtered photos.
    """
    # Parse comma-separated filters
    camera_list = [c.strip() for c in cameras.split(',')] if cameras else None
    collection_list = [c.strip() for c in collections.split(',')] if collections else None
    year_list = [int(y.strip()) for y in years.split(',')] if years else None
    source_list = [s.strip() for s in sources.split(',')] if sources else None
    
    if hasattr(backend, 'get_trace_data'):
        result = backend.get_trace_data(
            cameras=camera_list,
            collections=collection_list,
            years=year_list,
            sources=source_list,
            start_date=start_date,
            end_date=end_date,
            include_unknown_device=include_unknown_device,
            limit=limit,
            offset=offset
        )
        return TraceDataResponse(**result)
    
    # Fallback with empty data
    return TraceDataResponse(
        markers=[],
        events=[],
        stats=TraceStats(
            total=0,
            with_gps=0,
            unique_cameras=0,
            year_range={'min': None, 'max': None}
        ),
        pagination={
            'total': 0,
            'limit': limit,
            'offset': offset,
            'returned': 0
        }
    )


@router.get(
    "/photo/{document_id}",
    response_model=TracePhotoDetailResponse,
    summary="Get full photo metadata for Trace"
)
async def get_trace_photo(
    document_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
) -> TracePhotoDetailResponse:
    """
    Get full metadata for a single photo in Trace view.
    
    Returns all extracted EXIF metadata plus document info.
    """
    if hasattr(backend, 'get_trace_photo_detail'):
        photo = backend.get_trace_photo_detail(document_id)
    else:
        photo = None
    
    if not photo:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Photo not found")
    
    return TracePhotoDetailResponse(photo=TracePhotoDetail(**photo))
