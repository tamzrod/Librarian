"""Collections API routes - DEPRECATED.

These endpoints are deprecated in favor of single-library architecture.
See ADR 0005 for details.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_storage_backend, MockBackend


router = APIRouter(prefix="/collections", tags=["collections"])


# In-memory storage for Phase 1 (would be replaced by database)
_collection_store = {
    1: {
        "id": 1,
        "name": "Default Collection",
        "root_path": "/home/user/documents",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-06-28T10:00:00Z",
        "document_count": 42,
        "entity_count": 156,
        "event_count": 23,
        "location_count": 8
    }
}
_watcher_store = {}  # collection_id -> watcher


# Request/Response Schemas
class CollectionCreate(BaseModel):
    """Request schema for creating a collection."""
    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    root_path: str = Field(..., min_length=1, description="Root path to watch")


class CollectionResponse(BaseModel):
    """Response schema for a collection."""
    id: int
    name: str
    root_path: str
    document_count: int = 0
    entity_count: int = 0
    event_count: int = 0
    location_count: int = 0
    created_at: str
    updated_at: str


class CollectionListResponse(BaseModel):
    """Response schema for listing collections."""
    data: list[CollectionResponse]
    pagination: dict


class DeleteResponse(BaseModel):
    """Response schema for deletion."""
    message: str
    id: int


# Routes - DEPRECATED
@router.get(
    "",
    response_model=CollectionListResponse,
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="[DEPRECATED] List collections"
)
async def list_collections(
    limit: int = 20,
    offset: int = 0
) -> CollectionListResponse:
    """
    DEPRECATED: Librarian now uses single-library architecture.
    
    See ADR 0005 for details.
    
    This endpoint will be removed in a future version.
    """
    collections = list(_collection_store.values())
    total = len(collections)
    
    paginated = collections[offset:offset + limit]
    
    return CollectionListResponse(
        data=[CollectionResponse(**c) for c in paginated],
        pagination={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    )


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    deprecated=True,
    summary="[DEPRECATED] Create collection"
)
async def create_collection(
    request: CollectionCreate
) -> CollectionResponse:
    """
    DEPRECATED: Librarian now uses single-library architecture.
    
    See ADR 0005 for details.
    
    This endpoint will be removed in a future version.
    """
    collection_id = generate_collection_id()
    now = datetime.utcnow().isoformat() + "Z"
    
    collection = {
        "id": collection_id,
        "name": request.name,
        "root_path": request.root_path,
        "created_at": now,
        "updated_at": now,
        "document_count": 0,
        "entity_count": 0,
        "event_count": 0,
        "location_count": 0
    }
    
    _collection_store[collection_id] = collection
    return CollectionResponse(**collection)


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="[DEPRECATED] Get collection"
)
async def get_collection(
    collection_id: int
) -> CollectionResponse:
    """
    DEPRECATED: Librarian now uses single-library architecture.
    
    See ADR 0005 for details.
    
    This endpoint will be removed in a future version.
    """
    if collection_id not in _collection_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Collection {collection_id} not found",
                "details": []
            }
        )
    
    return CollectionResponse(**_collection_store[collection_id])


@router.delete(
    "/{collection_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="[DEPRECATED] Delete collection"
)
async def delete_collection(
    collection_id: int
) -> DeleteResponse:
    """
    DEPRECATED: Librarian now uses single-library architecture.
    
    See ADR 0005 for details.
    
    This endpoint will be removed in a future version.
    """
    if collection_id not in _collection_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Collection {collection_id} not found",
                "details": []
            }
        )
    
    del _collection_store[collection_id]
    
    return DeleteResponse(
        message="Collection deleted successfully",
        id=collection_id
    )


def generate_collection_id() -> int:
    """Generate a unique collection ID."""
    if not _collection_store:
        return 1
    return max(_collection_store.keys()) + 1