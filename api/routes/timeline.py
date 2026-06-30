"""Evidence Timeline API routes.

Phase 1B: REST API Exposure for Evidence Timeline.

Provides read-only access to photo metadata extracted from images.
All timeline information is obtained through these REST APIs only.
No direct PostgreSQL access is allowed from consumers.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from api.dependencies import get_storage_backend
from storage.backend import StorageBackend


router = APIRouter(prefix="/timeline", tags=["timeline"])


# =============================================================================
# Response Models
# =============================================================================

class TimelineStats(BaseModel):
    """Statistics for the Evidence Timeline."""
    photos_total: int = Field(description="Total number of photos with metadata")
    gps_tagged: int = Field(description="Number of photos with GPS coordinates")
    unique_cameras: int = Field(description="Number of unique camera make/model combinations")
    first_photo_timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp of earliest photo"
    )
    last_photo_timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp of latest photo"
    )


class PhotoSummary(BaseModel):
    """Summary of a photo for list views."""
    document_id: int = Field(description="Document ID in the database")
    filename: str = Field(description="Original filename")
    timestamp: Optional[str] = Field(default=None, description="When photo was taken")
    camera_make: Optional[str] = Field(default=None, description="Camera manufacturer")
    camera_model: Optional[str] = Field(default=None, description="Camera model")
    gps_latitude: Optional[float] = Field(default=None, description="GPS latitude")
    gps_longitude: Optional[float] = Field(default=None, description="GPS longitude")


class PhotoMapMarker(BaseModel):
    """Photo marker for map display."""
    document_id: int = Field(description="Document ID in the database")
    latitude: float = Field(description="GPS latitude")
    longitude: float = Field(description="GPS longitude")
    timestamp: Optional[str] = Field(default=None, description="When photo was taken")
    camera: Optional[str] = Field(default=None, description="Camera make and model")
    filename: str = Field(description="Original filename")


class PhotoDetail(BaseModel):
    """Full photo metadata for detail view."""
    document_id: int
    filename: str
    timestamp: Optional[str] = None
    timestamp_digitized: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    width: int
    height: int
    orientation: Optional[int] = None
    file_format: str
    extracted_at: str


class PhotoListResponse(BaseModel):
    """Paginated response for photo list."""
    data: list[PhotoSummary]
    pagination: dict
    filters: dict


class MapResponse(BaseModel):
    """Response for map markers."""
    markers: list[PhotoMapMarker]
    count: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/stats",
    response_model=TimelineStats,
    summary="Get timeline statistics"
)
async def get_timeline_stats(
    backend: StorageBackend = Depends(get_storage_backend)
) -> TimelineStats:
    """
    Get statistics for the Evidence Timeline.
    
    Returns counts and date ranges for all photo metadata.
    """
    if hasattr(backend, 'get_timeline_stats'):
        stats = backend.get_timeline_stats()
    else:
        # Fallback for mock backend
        stats = {
            'photos_total': 0,
            'gps_tagged': 0,
            'unique_cameras': 0,
            'first_photo_timestamp': None,
            'last_photo_timestamp': None
        }
    
    return TimelineStats(**stats)


@router.get(
    "/photos",
    response_model=PhotoListResponse,
    summary="List photos with optional filters"
)
async def list_photos(
    backend: StorageBackend = Depends(get_storage_backend),
    camera: Optional[str] = Query(
        None,
        description="Filter by camera (matches make or model)"
    ),
    gps_only: bool = Query(
        False,
        description="Only return photos with GPS coordinates"
    ),
    start_date: Optional[str] = Query(
        None,
        description="Filter photos after this date (ISO 8601)"
    ),
    end_date: Optional[str] = Query(
        None,
        description="Filter photos before this date (ISO 8601)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
) -> PhotoListResponse:
    """
    List photos with optional filtering and pagination.
    
    Supports filtering by:
    - Camera make/model (partial match)
    - GPS coordinates present
    - Date range
    
    Results are sorted by timestamp descending (most recent first).
    """
    if hasattr(backend, 'search_photo_metadata'):
        results, total = backend.search_photo_metadata(
            camera_make=camera,
            camera_model=camera,  # Same param for both
            gps_only=gps_only,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
    else:
        # Mock backend
        results = []
        total = 0
    
    return PhotoListResponse(
        data=[PhotoSummary(**r) for r in results],
        pagination={
            'total': total,
            'limit': limit,
            'offset': offset,
            'returned': len(results)
        },
        filters={
            'camera': camera,
            'gps_only': gps_only,
            'start_date': start_date,
            'end_date': end_date
        }
    )


@router.get(
    "/map",
    response_model=MapResponse,
    summary="Get GPS markers for map display"
)
async def get_map_markers(
    backend: StorageBackend = Depends(get_storage_backend),
    limit: int = Query(1000, ge=1, le=5000, description="Maximum markers"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
) -> MapResponse:
    """
    Get all photos with GPS coordinates for map display.
    
    Returns markers with latitude, longitude, timestamp, camera, and filename.
    Only photos with valid GPS coordinates are returned.
    """
    if hasattr(backend, 'get_photos_with_gps'):
        markers = backend.get_photos_with_gps(limit=limit, offset=offset)
    else:
        markers = []
    
    return MapResponse(
        markers=[PhotoMapMarker(**m) for m in markers],
        count=len(markers)
    )


@router.get(
    "/photo/{document_id}",
    response_model=PhotoDetail,
    summary="Get full photo metadata"
)
async def get_photo(
    document_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
) -> PhotoDetail:
    """
    Get full timeline metadata for a single photo.
    
    Returns all extracted EXIF metadata plus document info.
    """
    if hasattr(backend, 'get_photo_metadata'):
        metadata = backend.get_photo_metadata(document_id)
    else:
        metadata = None
    
    if not metadata:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Photo metadata not found")
    
    # Get document info for filename
    if hasattr(backend, 'get_document_for_photo'):
        doc = backend.get_document_for_photo(document_id)
        filename = doc['filename'] if doc else f"unknown_{document_id}"
    else:
        filename = f"unknown_{document_id}"
    
    return PhotoDetail(
        document_id=metadata['document_id'],
        filename=filename,
        timestamp=metadata['timestamp_original'].isoformat() + 'Z' if metadata.get('timestamp_original') else None,
        timestamp_digitized=metadata['timestamp_digitized'].isoformat() + 'Z' if metadata.get('timestamp_digitized') else None,
        gps_latitude=metadata.get('gps_latitude'),
        gps_longitude=metadata.get('gps_longitude'),
        gps_altitude=metadata.get('gps_altitude'),
        camera_make=metadata.get('camera_make'),
        camera_model=metadata.get('camera_model'),
        lens_model=metadata.get('lens_model'),
        width=metadata.get('width', 0),
        height=metadata.get('height', 0),
        orientation=metadata.get('orientation'),
        file_format=metadata.get('file_format', 'UNKNOWN'),
        extracted_at=metadata['extracted_at'].isoformat() + 'Z' if metadata.get('extracted_at') else None
    )
