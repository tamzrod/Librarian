"""Data Explorer API routes.

Provides descriptor-driven inspection of the Librarian catalog backend.
This is an operational inspection tool for validating ingestion, debugging issues,
and troubleshooting without exposing database internals.

Architecture:
    Dashboard → Data Explorer → Explorer Service → Backend Adapter → Catalog Backend

Navigation supports:
- Collections (user-defined artifact groupings)
- Folders (filesystem-derived hierarchy)
- Virtual Collections (dynamic groupings based on queries)
- Saved Views (persistent filtered views)

The UI is driven entirely by descriptors from the backend - no hardcoded
artifact type handling in the frontend.
"""

from typing import Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import get_storage_backend
from api.app_state import get_app_state
from storage.backend import StorageBackend


router = APIRouter(prefix="/data-explorer", tags=["data-explorer"])


# ============================================================================
# In-Memory Collections Store (Phase 1)
# ============================================================================
# In production, this would be backed by a database table.
# Format: collection_id -> { id, name, description, document_ids, created_at, updated_at }

_collections_store: dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Photos",
        "description": "Image files from various sources",
        "document_ids": [],  # Will be populated dynamically based on extension
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
    },
    2: {
        "id": 2,
        "name": "Documents",
        "description": "Text documents and PDFs",
        "document_ids": [],
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
    },
    3: {
        "id": 3,
        "name": "Code",
        "description": "Source code files",
        "document_ids": [],
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
    },
}

# Define collection rules (extension patterns)
_COLLECTION_RULES: dict[int, list[str]] = {
    1: [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic"],  # Photos
    2: [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],  # Documents
    3: [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".rb", ".php"],  # Code
}


# ============================================================================
# In-Memory Saved Views Store (Phase 1)
# ============================================================================
# Saved views are persistent filter configurations.
# Format: saved_view_id -> { id, name, description, filters, created_at, updated_at }

_saved_views_store: dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Large Photos",
        "description": "Photos larger than 1MB",
        "filters": {
            "type": "jpg",
            "min_size": 1048576,  # 1MB
        },
        "created_at": "2026-06-15T00:00:00Z",
        "updated_at": "2026-06-15T00:00:00Z",
    },
    2: {
        "id": 2,
        "name": "Recent Documents",
        "description": "Documents modified in the last week",
        "filters": {
            "type": "pdf",
        },
        "created_at": "2026-06-10T00:00:00Z",
        "updated_at": "2026-06-10T00:00:00Z",
    },
}

_next_saved_view_id = 3


# ============================================================================
# Schema Definitions - Descriptor-Driven Types
# ============================================================================

class NavigationItemType(str):
    """Navigation item types supported by the explorer."""
    COLLECTION = "collection"
    FOLDER = "folder"
    VIRTUAL_COLLECTION = "virtual_collection"
    SAVED_VIEW = "saved_view"


class InspectorFieldDescriptor(BaseModel):
    """A field descriptor for the inspector."""
    label: str = Field(description="Human-readable field label")
    value: Any = Field(default=None, description="Field value")
    type: str = Field(default="text", description="Field type: text, number, date, url, hash, status, list")
    truncate: bool = Field(default=False, description="Whether to truncate long values")
    copyable: bool = Field(default=False, description="Whether value can be copied")
    formatter: Optional[str] = Field(default=None, description="Optional formatter name")


class InspectorSectionDescriptor(BaseModel):
    """A section descriptor for the inspector."""
    title: str = Field(description="Section title")
    icon: Optional[str] = Field(default=None, description="Section icon emoji")
    fields: list[InspectorFieldDescriptor] = Field(default_factory=list, description="Fields in this section")
    collapsible: bool = Field(default=False, description="Whether section can be collapsed")
    collapsed: bool = Field(default=False, description="Initial collapsed state")


class ArtifactDescriptor(BaseModel):
    """The artifact descriptor that drives inspector rendering."""
    artifact_id: int = Field(description="Artifact document ID")
    artifact_type: str = Field(description="Artifact type category")
    sections: list[InspectorSectionDescriptor] = Field(default_factory=list, description="Inspector sections")


class DataExplorerNavigationItem(BaseModel):
    """A navigation item in the left pane."""
    id: str = Field(description="Unique item identifier")
    name: str = Field(description="Display name")
    type: str = Field(description="Item type: collection, folder, virtual_collection, saved_view")
    parent_id: Optional[str] = Field(default=None, description="Parent item ID for hierarchy")
    has_children: bool = Field(default=False, description="Whether item has child items")
    expanded: bool = Field(default=False, description="Whether item is expanded")
    children: list["DataExplorerNavigationItem"] = Field(default_factory=list, description="Child items")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DataExplorerNavigationResponse(BaseModel):
    """Response from navigation API endpoint."""
    items: list[DataExplorerNavigationItem] = Field(description="Navigation items")
    total: int = Field(description="Total number of items")


class DataExplorerArtifact(BaseModel):
    """An artifact in the explorer view."""
    id: int = Field(description="Document ID")
    name: str = Field(description="Filename")
    path: str = Field(description="Full path to document")
    type: Optional[str] = Field(default=None, description="Artifact type")
    size: Optional[int] = Field(default=None, description="File size in bytes")
    modified: Optional[str] = Field(default=None, description="Last modified time (ISO 8601)")
    thumbnail: Optional[str] = Field(default=None, description="Thumbnail URL")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DataExplorerArtifactsResponse(BaseModel):
    """Response from artifacts API endpoint."""
    artifacts: list[DataExplorerArtifact] = Field(description="Artifacts in the navigation item")
    total: int = Field(description="Total artifact count")
    navigation_id: str = Field(description="Source navigation item ID")
    navigation_type: str = Field(description="Source navigation item type")


class DataExplorerArtifactDetail(BaseModel):
    """Detailed artifact information for the inspector."""
    id: int = Field(description="Document ID")
    name: str = Field(description="Filename")
    path: str = Field(description="Full path")
    descriptor: ArtifactDescriptor = Field(description="Descriptor-driven inspector data")


class DataExplorerArtifactDetailResponse(BaseModel):
    """Response from artifact detail API endpoint."""
    artifact: DataExplorerArtifactDetail


class DataExplorerStatistics(BaseModel):
    """System statistics for Data Explorer."""
    total_documents: int = Field(description="Total number of documents")
    total_collections: int = Field(description="Total number of collections")
    total_virtual_collections: int = Field(description="Total number of virtual collections")
    total_saved_views: int = Field(description="Total number of saved views")
    by_type: dict[str, int] = Field(default_factory=dict, description="Document count by type")
    by_status: dict[str, int] = Field(default_factory=dict, description="Document count by status")


class DataExplorerStatisticsResponse(BaseModel):
    """Response from statistics API endpoint."""
    statistics: DataExplorerStatistics
    timestamp: str


class DataExplorerSearchResponse(BaseModel):
    """Response from search API endpoint."""
    artifacts: list[DataExplorerArtifact]
    total: int
    query: str
    filters_applied: dict[str, Any]


class SavedViewFilters(BaseModel):
    """Filters for a saved view."""
    type: Optional[str] = Field(default=None, description="File extension filter")
    min_size: Optional[int] = Field(default=None, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(default=None, description="Maximum file size in bytes")
    query: Optional[str] = Field(default=None, description="Text search query")


class SavedViewCreate(BaseModel):
    """Request schema for creating a saved view."""
    name: str = Field(..., min_length=1, max_length=255, description="View name")
    description: Optional[str] = Field(default=None, description="View description")
    filters: SavedViewFilters = Field(default_factory=SavedViewFilters, description="View filters")


class SavedViewUpdate(BaseModel):
    """Request schema for updating a saved view."""
    name: Optional[str] = Field(default=None, description="View name")
    description: Optional[str] = Field(default=None, description="View description")
    filters: Optional[SavedViewFilters] = Field(default=None, description="View filters")


class SavedViewResponse(BaseModel):
    """Response schema for a saved view."""
    id: int
    name: str
    description: Optional[str]
    filters: SavedViewFilters
    created_at: str
    updated_at: str


class SavedViewListResponse(BaseModel):
    """Response schema for listing saved views."""
    views: list[SavedViewResponse]
    total: int


# ============================================================================
# Helper Functions
# ============================================================================

def _build_artifact_descriptor(
    doc_id: int,
    doc_name: str,
    doc_path: str,
    doc_extension: Optional[str],
    doc_size: Optional[int],
    doc_mime: Optional[str],
    doc_modified: Optional[datetime],
    doc_created: Optional[datetime],
    doc_indexed: Optional[datetime],
    doc_status: str,
    doc_thumbnail: Optional[str],
    doc_md5: Optional[str],
    doc_sha256: Optional[str],
    doc_artifact_type: Optional[str],
    processing_status: list[dict],
    photo_metadata: Optional[dict] = None,
    detected_objects: Optional[list] = None,
) -> ArtifactDescriptor:
    """
    Build a descriptor-driven artifact representation for the inspector.
    
    This function constructs inspector sections dynamically based on available
    artifact metadata. New enrichment types automatically add sections without
    requiring frontend changes.
    """
    sections = []
    
    # Section 1: Core Information
    core_fields = [
        InspectorFieldDescriptor(label="Filename", value=doc_name, type="text", copyable=True),
        InspectorFieldDescriptor(label="Path", value=doc_path, type="text", truncate=True, copyable=True),
        InspectorFieldDescriptor(label="Extension", value=doc_extension.upper() if doc_extension else None, type="text"),
        InspectorFieldDescriptor(label="MIME Type", value=doc_mime, type="text"),
        InspectorFieldDescriptor(label="File Size", value=doc_size, type="number", formatter="file_size"),
        InspectorFieldDescriptor(label="Created", value=doc_created.isoformat() + "Z" if doc_created else None, type="date"),
        InspectorFieldDescriptor(label="Modified", value=doc_modified.isoformat() + "Z" if doc_modified else None, type="date"),
        InspectorFieldDescriptor(label="Indexed", value=doc_indexed.isoformat() + "Z" if doc_indexed else None, type="date"),
        InspectorFieldDescriptor(label="Status", value=doc_status, type="status"),
    ]
    sections.append(InspectorSectionDescriptor(
        title="Core Information",
        icon="📄",
        fields=core_fields,
    ))
    
    # Section 2: File Integrity
    hash_fields = []
    if doc_md5:
        hash_fields.append(InspectorFieldDescriptor(label="MD5", value=doc_md5, type="hash", copyable=True))
    if doc_sha256:
        hash_fields.append(InspectorFieldDescriptor(label="SHA256", value=doc_sha256, type="hash", copyable=True))
    
    if hash_fields:
        sections.append(InspectorSectionDescriptor(
            title="File Integrity",
            icon="🔐",
            fields=hash_fields,
        ))
    
    # Section 3: Processing Status
    if processing_status:
        status_fields = [
            InspectorFieldDescriptor(
                label=job.get("label", job.get("job_type", "Unknown")),
                value=job.get("status", "UNKNOWN"),
                type="status",
            )
            for job in processing_status
        ]
        sections.append(InspectorSectionDescriptor(
            title="Processing Status",
            icon="⚙️",
            fields=status_fields,
        ))
    
    # Section 4: Photo Metadata (if available)
    if photo_metadata:
        photo_fields = []
        if photo_metadata.get("camera_make"):
            photo_fields.append(InspectorFieldDescriptor(
                label="Camera",
                value=f"{photo_metadata['camera_make']} {photo_metadata.get('camera_model', '')}".strip(),
                type="text",
            ))
        if photo_metadata.get("date_taken"):
            photo_fields.append(InspectorFieldDescriptor(
                label="Date Taken",
                value=photo_metadata["date_taken"],
                type="date",
            ))
        if photo_metadata.get("gps_latitude") and photo_metadata.get("gps_longitude"):
            photo_fields.append(InspectorFieldDescriptor(
                label="GPS",
                value=f"{photo_metadata['gps_latitude']}, {photo_metadata['gps_longitude']}",
                type="text",
            ))
        if photo_metadata.get("gps_altitude"):
            photo_fields.append(InspectorFieldDescriptor(
                label="Altitude",
                value=f"{photo_metadata['gps_altitude']}m",
                type="number",
            ))
        
        if photo_fields:
            sections.append(InspectorSectionDescriptor(
                title="Photo Metadata",
                icon="📷",
                fields=photo_fields,
            ))
    
    # Section 5: Object Detection (if available)
    if detected_objects:
        object_fields = [
            InspectorFieldDescriptor(
                label=f"{obj.get('label', 'Unknown')} ({obj.get('confidence', 0):.0%})",
                value=f"Confidence: {obj.get('confidence', 0):.2%}",
                type="text",
            )
            for obj in detected_objects[:10]  # Limit to top 10
        ]
        sections.append(InspectorSectionDescriptor(
            title=f"Detected Objects ({len(detected_objects)})",
            icon="🔍",
            fields=object_fields,
            collapsible=True,
        ))
    
    # Section 6: Artifact Classification
    if doc_artifact_type:
        sections.append(InspectorSectionDescriptor(
            title="Classification",
            icon="🏷️",
            fields=[
                InspectorFieldDescriptor(label="Type", value=doc_artifact_type, type="text"),
            ],
        ))
    
    return ArtifactDescriptor(
        artifact_id=doc_id,
        artifact_type=doc_artifact_type or "document",
        sections=sections,
    )


# ============================================================================
# Routes
# ============================================================================

@router.get(
    "/navigation",
    response_model=DataExplorerNavigationResponse,
    summary="Get Data Explorer navigation"
)
async def get_navigation(
    backend: StorageBackend = Depends(get_storage_backend),
    parent_id: Optional[str] = Query(None, description="Parent navigation item ID to load children for"),
) -> DataExplorerNavigationResponse:
    """
    Get navigation structure for the Data Explorer.
    
    Returns descriptors for Collections, Folders, Virtual Collections, and Saved Views.
    Navigation is descriptor-driven - frontend renders generically based on type.
    
    If parent_id is provided, returns children of that item only (lazy loading).
    If parent_id is None, returns root-level items.
    
    The navigation hierarchy reflects investigation concepts:
    - Collections: User-defined groupings of artifacts
    - Folders: Filesystem-derived hierarchy
    - Virtual Collections: Dynamic groupings based on queries
    - Saved Views: Persistent filtered views
    """
    app_state = get_app_state()
    collection_root = app_state.library_root or "/library"
    
    # If parent_id is provided, load children for that item
    if parent_id:
        items = _get_navigation_children(backend, collection_root, parent_id)
        return DataExplorerNavigationResponse(
            items=items,
            total=len(items),
        )
    
    # Otherwise, return root-level items
    items = []
    
    # 1. Add Folders section with top-level folders
    folders = _get_folder_navigation(backend, collection_root)
    items.extend(folders)
    
    # 2. Add Collections section
    # Collections are user-defined groupings based on rules
    items.append(DataExplorerNavigationItem(
        id="collections",
        name="Collections",
        type=NavigationItemType.COLLECTION,
        parent_id=None,
        has_children=len(_collections_store) > 0,
        expanded=False,
        metadata={"description": "User-defined artifact groupings"},
    ))
    
    # 3. Add Virtual Collections section
    # Virtual collections are dynamic groupings based on queries
    items.append(DataExplorerNavigationItem(
        id="virtual_collections",
        name="Virtual Collections",
        type=NavigationItemType.VIRTUAL_COLLECTION,
        parent_id=None,
        has_children=True,  # Always has predefined virtual collections
        expanded=False,
        metadata={"description": "Dynamic groupings based on queries"},
    ))
    
    # 4. Add Saved Views section
    # Saved views are user-defined filter configurations
    items.append(DataExplorerNavigationItem(
        id="saved_views",
        name="Saved Views",
        type=NavigationItemType.SAVED_VIEW,
        parent_id=None,
        has_children=len(_saved_views_store) > 0,
        expanded=False,
        metadata={"description": "Persistent filtered views"},
    ))
    
    return DataExplorerNavigationResponse(
        items=items,
        total=len(items),
    )


def _get_navigation_children(
    backend: StorageBackend,
    collection_root: str,
    parent_id: str
) -> list[DataExplorerNavigationItem]:
    """
    Get child items for a navigation parent.
    
    Handles lazy loading of folder children when users expand folders.
    """
    items = []
    
    # Parse parent_id to determine type and path
    if parent_id.startswith("folder:"):
        folder_path = parent_id.replace("folder:", "")
        if not folder_path.startswith('/'):
            folder_path = f"/{folder_path}"
        
        items = _get_subfolders(backend, folder_path)
    
    elif parent_id == "collections":
        # Load user-defined collections as children
        items = _get_collections()
    
    elif parent_id == "virtual_collections":
        # Load virtual collections as children
        items = _get_virtual_collections(backend)
    
    elif parent_id == "saved_views":
        # Load saved views as children
        items = _get_saved_views()
    
    elif parent_id.startswith("collection:"):
        # Collection detail - no children
        pass
    
    return items


def _get_collections() -> list[DataExplorerNavigationItem]:
    """Get collection items for navigation."""
    items = []
    
    for collection_id, collection in _collections_store.items():
        items.append(DataExplorerNavigationItem(
            id=f"collection:{collection_id}",
            name=collection["name"],
            type=NavigationItemType.COLLECTION,
            parent_id="collections",
            has_children=False,
            expanded=False,
            metadata={
                "description": collection.get("description", ""),
                "document_count": _get_collection_document_count(collection_id),
            },
        ))
    
    return items


def _get_collection_document_count(collection_id: int) -> int:
    """Get document count for a collection based on rules."""
    if collection_id not in _COLLECTION_RULES:
        return 0
    
    # This would be replaced with a database query in production
    return 0  # Placeholder - actual count computed when loading artifacts


def _get_virtual_collections(backend: StorageBackend) -> list[DataExplorerNavigationItem]:
    """Get predefined virtual collections based on queries."""
    virtual_collections = [
        {
            "id": "vc:all",
            "name": "All Artifacts",
            "description": "View all artifacts in the library",
        },
        {
            "id": "vc:images",
            "name": "Images",
            "description": "All image files",
        },
        {
            "id": "vc:documents",
            "name": "Documents",
            "description": "All document files",
        },
        {
            "id": "vc:code",
            "name": "Code",
            "description": "All source code files",
        },
        {
            "id": "vc:recent",
            "name": "Recently Added",
            "description": "Artifacts added in the last 30 days",
        },
        {
            "id": "vc:large",
            "name": "Large Files",
            "description": "Files larger than 10MB",
        },
    ]
    
    return [
        DataExplorerNavigationItem(
            id=vc["id"],
            name=vc["name"],
            type=NavigationItemType.VIRTUAL_COLLECTION,
            parent_id="virtual_collections",
            has_children=False,
            expanded=False,
            metadata={"description": vc["description"]},
        )
        for vc in virtual_collections
    ]


def _get_saved_views() -> list[DataExplorerNavigationItem]:
    """Get saved view items for navigation."""
    return [
        DataExplorerNavigationItem(
            id=f"saved_view:{view['id']}",
            name=view["name"],
            type=NavigationItemType.SAVED_VIEW,
            parent_id="saved_views",
            has_children=False,
            expanded=False,
            metadata={
                "description": view.get("description", ""),
                "filters": view.get("filters", {}),
            },
        )
        for view in _saved_views_store.values()
    ]


def _get_subfolders(
    backend: StorageBackend,
    parent_path: str
) -> list[DataExplorerNavigationItem]:
    """Get subfolders within a parent path."""
    items = []
    folders_map: dict[str, bool] = {}
    
    if backend and hasattr(backend, '_get_connection'):
        try:
            conn = backend._get_connection()
            cur = conn.cursor()
            
            # Build prefix for matching - paths in DB are absolute
            prefix = f"{parent_path}/"
            
            # Query documents under this path
            cur.execute("""
                SELECT path FROM documents 
                WHERE path LIKE %s
            """, (f"{prefix}%",))
            
            for row in cur.fetchall():
                doc_path = row[0] or ""
                if doc_path.startswith(prefix):
                    # Get path relative to parent
                    remaining = doc_path[len(prefix):]
                    if '/' in remaining:
                        folder_name = remaining.split('/')[0]
                        if folder_name and folder_name not in folders_map:
                            folders_map[folder_name] = True
            
            cur.close()
            conn.close()
        except Exception:
            pass
    
    # Build navigation items for each unique subfolder
    for folder_name in sorted(folders_map.keys()):
        folder_path = f"{parent_path}/{folder_name}"
        folder_id = f"folder:{folder_path.lstrip('/')}"
        
        # Check if this folder has subfolders
        has_children = _has_subfolders(backend, folder_path)
        
        items.append(DataExplorerNavigationItem(
            id=folder_id,
            name=folder_name,
            type=NavigationItemType.FOLDER,
            parent_id=f"folder:{parent_path.lstrip('/')}",
            has_children=has_children,
            expanded=False,
        ))
    
    return items


def _has_subfolders(backend: StorageBackend, folder_path: str) -> bool:
    """Check if a folder has subfolders."""
    if not backend or not hasattr(backend, '_get_connection'):
        return False
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        prefix = f"{folder_path}/"
        
        cur.execute("""
            SELECT path FROM documents 
            WHERE path LIKE %s
            LIMIT 1
        """, (f"{prefix}%",))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            doc_path = row[0] or ""
            if doc_path.startswith(prefix):
                remaining = doc_path[len(prefix):]
                return '/' in remaining
        
        return False
    except Exception:
        return False


def _get_folder_navigation(
    backend: StorageBackend,
    collection_root: str
) -> list[DataExplorerNavigationItem]:
    """Build folder navigation from document paths."""
    folders_map: dict[str, dict] = {}
    
    if backend and hasattr(backend, '_get_connection'):
        try:
            conn = backend._get_connection()
            cur = conn.cursor()
            
            # Get all document paths
            cur.execute("SELECT path FROM documents ORDER BY path")
            
            for row in cur.fetchall():
                doc_path = row[0] or ""
                if not doc_path:
                    continue
                
                # Normalize path
                if doc_path.startswith('/'):
                    relative_path = doc_path[1:]
                else:
                    relative_path = doc_path
                
                parts = relative_path.split('/')
                if len(parts) <= 1:
                    continue
                
                # Build folder hierarchy
                current_path = ""
                for i, part in enumerate(parts[:-1]):  # Exclude filename
                    if current_path:
                        current_path = f"{current_path}/{part}"
                    else:
                        current_path = part
                    
                    if current_path not in folders_map:
                        folders_map[current_path] = {
                            "name": part,
                            "has_children": False,
                        }
                    
                    # Mark parent as having children if this isn't the immediate parent
                    if i > 0:
                        parent_parts = parts[:i]
                        parent_path = "/".join(parent_parts)
                        if parent_path in folders_map:
                            folders_map[parent_path]["has_children"] = True
            
            cur.close()
            conn.close()
        except Exception:
            pass
    
    # Build navigation items
    items = []
    root_folder_id = f"folder:{collection_root.lstrip('/')}"
    
    # Get top-level folders
    top_level_folders = {
        path: info for path, info in folders_map.items()
        if '/' not in path
    }
    
    for folder_path in sorted(top_level_folders.keys()):
        info = top_level_folders[folder_path]
        folder_id = f"folder:{folder_path}"
        
        # Check for children
        has_children = any(
            p.startswith(f"{folder_path}/") and '/' not in p[len(folder_path):]
            for p in folders_map.keys()
        )
        
        # Add child navigation items
        children = []
        child_folders = {
            p: folders_map[p] for p in folders_map.keys()
            if p.startswith(f"{folder_path}/") and '/' not in p[len(folder_path):]
        }
        
        for child_path in sorted(child_folders.keys()):
            child_info = child_folders[child_path]
            child_id = f"folder:{child_path}"
            child_has_children = any(
                p.startswith(f"{child_path}/") and '/' not in p[len(child_path):]
                for p in folders_map.keys()
            )
            children.append(DataExplorerNavigationItem(
                id=child_id,
                name=child_info["name"],
                type=NavigationItemType.FOLDER,
                parent_id=folder_id,
                has_children=child_has_children,
                expanded=False,
            ))
        
        items.append(DataExplorerNavigationItem(
            id=folder_id,
            name=info["name"],
            type=NavigationItemType.FOLDER,
            parent_id=None,
            has_children=has_children,
            expanded=False,
            children=children,
        ))
    
    return items


@router.get(
    "/artifacts",
    response_model=DataExplorerArtifactsResponse,
    summary="Get artifacts for navigation item"
)
async def get_artifacts(
    backend: StorageBackend = Depends(get_storage_backend),
    navigation_id: str = Query(..., description="Navigation item ID"),
    navigation_type: str = Query(..., description="Navigation item type"),
) -> DataExplorerArtifactsResponse:
    """
    Get artifacts for a navigation item.
    
    The behavior depends on the navigation type:
    - folder: Returns documents in the folder path
    - collection: Returns documents matching the collection rules
    - virtual_collection: Returns documents matching the virtual query
    - saved_view: Returns documents matching the saved view filter
    """
    artifacts = []
    app_state = get_app_state()
    collection_root = app_state.library_root or "/library"
    
    if navigation_type == NavigationItemType.FOLDER:
        # Extract folder path from navigation_id (format: folder:{path})
        folder_path = navigation_id.replace("folder:", "")
        if not folder_path.startswith('/'):
            folder_path = f"/{folder_path}"
        
        artifacts = _get_documents_in_folder(backend, collection_root, folder_path)
    
    elif navigation_type == NavigationItemType.COLLECTION:
        # Extract collection ID from navigation_id (format: collection:{id})
        collection_id_str = navigation_id.replace("collection:", "")
        try:
            collection_id = int(collection_id_str)
            artifacts = _get_documents_by_collection(backend, collection_id)
        except ValueError:
            pass
    
    elif navigation_type == NavigationItemType.VIRTUAL_COLLECTION:
        # Virtual collections use predefined queries
        artifacts = _get_documents_by_virtual_collection(backend, navigation_id)
    
    elif navigation_type == NavigationItemType.SAVED_VIEW:
        # Saved views use saved filter configurations
        artifacts = _get_documents_by_saved_view(backend, navigation_id)
    
    return DataExplorerArtifactsResponse(
        artifacts=artifacts,
        total=len(artifacts),
        navigation_id=navigation_id,
        navigation_type=navigation_type,
    )


def _get_documents_in_folder(
    backend: StorageBackend,
    collection_root: str,
    folder_path: str
) -> list[DataExplorerArtifact]:
    """Get documents in a specific folder."""
    artifacts = []
    
    if not backend or not hasattr(backend, '_get_connection'):
        return artifacts
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Build path prefix for matching
        prefix = f"{folder_path}/"
        
        # Get documents directly in this folder (not in subfolders)
        cur.execute("""
            SELECT id, path, extension, file_size, mime_type, modified_time,
                   indexed_at, status, thumbnail_path
            FROM documents
            WHERE path LIKE %s AND path NOT LIKE %s
            ORDER BY path
        """, (f"{prefix}%", f"{prefix}%/%"))
        
        for row in cur.fetchall():
            doc_id, doc_path, ext, size, mime, modified, indexed, status, thumbnail = row
            
            # Extract filename from path
            filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
            
            # Build thumbnail URL
            thumbnail_url = None
            if thumbnail:
                thumbnail_url = f"/thumbnails/{thumbnail}"
            
            artifacts.append(DataExplorerArtifact(
                id=doc_id,
                name=filename,
                path=doc_path,
                type=ext.lstrip('.') if ext else None,
                size=size,
                modified=modified.isoformat() + "Z" if modified else None,
                thumbnail=thumbnail_url,
            ))
        
        cur.close()
        conn.close()
    except Exception:
        pass
    
    return artifacts


def _get_documents_by_collection(
    backend: StorageBackend,
    collection_id: int
) -> list[DataExplorerArtifact]:
    """Get documents matching a collection's rules (based on extensions)."""
    artifacts = []
    
    if collection_id not in _COLLECTION_RULES:
        return artifacts
    
    extensions = _COLLECTION_RULES[collection_id]
    
    if not backend or not hasattr(backend, '_get_connection'):
        return artifacts
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Build query for matching extensions
        placeholders = ', '.join(['%s'] * len(extensions))
        query = f"""
            SELECT id, path, extension, file_size, mime_type, modified_time,
                   indexed_at, status, thumbnail_path
            FROM documents
            WHERE extension IN ({placeholders})
            ORDER BY path
        """
        
        cur.execute(query, extensions)
        
        for row in cur.fetchall():
            doc_id, doc_path, ext, size, mime, modified, indexed, status, thumbnail = row
            
            # Extract filename from path
            filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
            
            # Build thumbnail URL
            thumbnail_url = None
            if thumbnail:
                thumbnail_url = f"/thumbnails/{thumbnail}"
            
            artifacts.append(DataExplorerArtifact(
                id=doc_id,
                name=filename,
                path=doc_path,
                type=ext.lstrip('.') if ext else None,
                size=size,
                modified=modified.isoformat() + "Z" if modified else None,
                thumbnail=thumbnail_url,
            ))
        
        cur.close()
        conn.close()
    except Exception:
        pass
    
    return artifacts


def _get_documents_by_virtual_collection(
    backend: StorageBackend,
    virtual_collection_id: str
) -> list[DataExplorerArtifact]:
    """Get documents matching a virtual collection's query."""
    artifacts = []
    
    if not backend or not hasattr(backend, '_get_connection'):
        return artifacts
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        if virtual_collection_id == "vc:all":
            # All artifacts
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       indexed_at, status, thumbnail_path
                FROM documents
                ORDER BY indexed_at DESC
                LIMIT 500
            """)
        
        elif virtual_collection_id == "vc:images":
            # Images only
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       indexed_at, status, thumbnail_path
                FROM documents
                WHERE extension IN ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.heic')
                ORDER BY path
                LIMIT 500
            """)
        
        elif virtual_collection_id == "vc:documents":
            # Documents only
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       indexed_at, status, thumbnail_path
                FROM documents
                WHERE extension IN ('.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt')
                ORDER BY path
                LIMIT 500
            """)
        
        elif virtual_collection_id == "vc:code":
            # Code files
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       indexed_at, status, thumbnail_path
                FROM documents
                WHERE extension IN ('.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php')
                ORDER BY path
                LIMIT 500
            """)
        
        elif virtual_collection_id == "vc:recent":
            # Recently added (last 30 days)
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       indexed_at, status, thumbnail_path
                FROM documents
                WHERE indexed_at >= NOW() - INTERVAL '30 days'
                ORDER BY indexed_at DESC
                LIMIT 500
            """)
        
        elif virtual_collection_id == "vc:large":
            # Large files (>10MB)
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       indexed_at, status, thumbnail_path
                FROM documents
                WHERE file_size > 10485760  -- 10MB
                ORDER BY file_size DESC
                LIMIT 500
            """)
        
        else:
            cur.close()
            conn.close()
            return artifacts
        
        for row in cur.fetchall():
            doc_id, doc_path, ext, size, mime, modified, indexed, status, thumbnail = row
            
            # Extract filename from path
            filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
            
            # Build thumbnail URL
            thumbnail_url = None
            if thumbnail:
                thumbnail_url = f"/thumbnails/{thumbnail}"
            
            artifacts.append(DataExplorerArtifact(
                id=doc_id,
                name=filename,
                path=doc_path,
                type=ext.lstrip('.') if ext else None,
                size=size,
                modified=modified.isoformat() + "Z" if modified else None,
                thumbnail=thumbnail_url,
            ))
        
        cur.close()
        conn.close()
    except Exception:
        pass
    
    return artifacts


def _get_documents_by_saved_view(
    backend: StorageBackend,
    saved_view_id: str
) -> list[DataExplorerArtifact]:
    """Get documents matching a saved view's filters."""
    artifacts = []
    
    # Extract saved view ID from navigation_id (format: saved_view:{id})
    view_id_str = saved_view_id.replace("saved_view:", "")
    try:
        view_id = int(view_id_str)
    except ValueError:
        return artifacts
    
    # Get saved view
    if view_id not in _saved_views_store:
        return artifacts
    
    saved_view = _saved_views_store[view_id]
    filters = saved_view.get("filters", {})
    
    if not backend or not hasattr(backend, '_get_connection'):
        return artifacts
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Build query conditions based on filters
        conditions = []
        params = []
        
        # Type filter
        if filters.get("type"):
            ext = filters["type"]
            if not ext.startswith('.'):
                ext = f".{ext}"
            conditions.append("extension = %s")
            params.append(ext.lower())
        
        # Min size filter
        if filters.get("min_size"):
            conditions.append("file_size >= %s")
            params.append(filters["min_size"])
        
        # Max size filter
        if filters.get("max_size"):
            conditions.append("file_size <= %s")
            params.append(filters["max_size"])
        
        # Query filter
        if filters.get("query"):
            conditions.append("(path LIKE %s OR path LIKE %s)")
            params.append(f"%{filters['query']}%")
            params.append(f"%{filters['query']}%")
        
        # Build final query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        search_query = f"""
            SELECT id, path, extension, file_size, mime_type, modified_time,
                   indexed_at, status, thumbnail_path
            FROM documents
            WHERE {where_clause}
            ORDER BY path
            LIMIT 500
        """
        
        cur.execute(search_query, params)
        
        for row in cur.fetchall():
            doc_id, doc_path, ext, size, mime, modified, indexed, status, thumbnail = row
            
            # Extract filename from path
            filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
            
            # Build thumbnail URL
            thumbnail_url = None
            if thumbnail:
                thumbnail_url = f"/thumbnails/{thumbnail}"
            
            artifacts.append(DataExplorerArtifact(
                id=doc_id,
                name=filename,
                path=doc_path,
                type=ext.lstrip('.') if ext else None,
                size=size,
                modified=modified.isoformat() + "Z" if modified else None,
                thumbnail=thumbnail_url,
            ))
        
        cur.close()
        conn.close()
    except Exception:
        pass
    
    return artifacts


@router.get(
    "/artifacts/{artifact_id}",
    response_model=DataExplorerArtifactDetailResponse,
    summary="Get artifact detail for inspector"
)
async def get_artifact_detail(
    artifact_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
) -> DataExplorerArtifactDetailResponse:
    """
    Get detailed artifact information for the inspector.
    
    Returns a descriptor-driven representation that the frontend renders generically.
    New enrichment types automatically add inspector sections without frontend changes.
    """
    app_state = get_app_state()
    collection_root = app_state.library_root or "/library"
    
    # Default response
    detail = DataExplorerArtifactDetail(
        id=artifact_id,
        name="Unknown",
        path="/",
        descriptor=ArtifactDescriptor(
            artifact_id=artifact_id,
            artifact_type="unknown",
            sections=[
                InspectorSectionDescriptor(
                    title="Error",
                    icon="⚠️",
                    fields=[
                        InspectorFieldDescriptor(
                            label="Message",
                            value="Artifact not found",
                            type="text",
                        ),
                    ],
                ),
            ],
        ),
    )
    
    if not backend or not hasattr(backend, '_get_connection'):
        return DataExplorerArtifactDetailResponse(artifact=detail)
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Get document info
        cur.execute("""
            SELECT id, path, extension, file_size, mime_type, modified_time,
                   created_at, indexed_at, status, thumbnail_path,
                   md5_hash, sha256_hash, artifact_type
            FROM documents
            WHERE id = %s
        """, (artifact_id,))
        
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return DataExplorerArtifactDetailResponse(artifact=detail)
        
        doc_id, doc_path, ext, size, mime, modified, created, indexed, status, thumbnail, md5, sha256, artifact_type = row
        
        # Extract filename
        filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
        
        # Get processing status
        processing_status = []
        if hasattr(backend, 'get_document_jobs'):
            try:
                jobs = backend.get_document_jobs(doc_id)
                for job in jobs:
                    job_type = job.get('job_type', 'unknown')
                    processing_status.append({
                        "job_type": job_type,
                        "status": job.get('status', 'UNKNOWN'),
                        "label": _format_job_label(job_type),
                    })
            except Exception:
                pass
        
        # Get photo metadata if available
        photo_metadata = None
        if hasattr(backend, 'get_photo_metadata'):
            try:
                photo_meta = backend.get_photo_metadata(doc_id)
                if photo_meta:
                    photo_metadata = {
                        "camera_make": photo_meta.get('camera_make'),
                        "camera_model": photo_meta.get('camera_model'),
                        "date_taken": photo_meta.get('timestamp_original'),
                        "gps_latitude": photo_meta.get('gps_latitude'),
                        "gps_longitude": photo_meta.get('gps_longitude'),
                        "gps_altitude": photo_meta.get('gps_altitude'),
                    }
            except Exception:
                pass
        
        # Get object detections if available
        detected_objects = None
        if hasattr(backend, 'get_detections'):
            try:
                detections = backend.get_detections(doc_id)
                if detections:
                    detected_objects = [
                        {
                            "label": d.get('label', 'unknown'),
                            "confidence": d.get('confidence', 0),
                        }
                        for d in detections
                    ]
            except Exception:
                pass
        
        # Build descriptor
        descriptor = _build_artifact_descriptor(
            doc_id=doc_id,
            doc_name=filename,
            doc_path=doc_path,
            doc_extension=ext,
            doc_size=size,
            doc_mime=mime,
            doc_modified=modified,
            doc_created=created,
            doc_indexed=indexed,
            doc_status=status or "UNKNOWN",
            doc_thumbnail=thumbnail,
            doc_md5=md5,
            doc_sha256=sha256,
            doc_artifact_type=artifact_type,
            processing_status=processing_status,
            photo_metadata=photo_metadata,
            detected_objects=detected_objects,
        )
        
        detail = DataExplorerArtifactDetail(
            id=doc_id,
            name=filename,
            path=doc_path,
            descriptor=descriptor,
        )
        
        cur.close()
        conn.close()
    except Exception:
        pass
    
    return DataExplorerArtifactDetailResponse(artifact=detail)


def _format_job_label(job_type: str) -> str:
    """Format job type into human-readable label."""
    labels = {
        "extract_text": "Text Extraction",
        "extract_entities": "Entity Extraction",
        "extract_events": "Event Extraction",
        "extract_locations": "Location Extraction",
        "generate_embeddings": "Embeddings",
        "generate_thumbnail": "Thumbnail",
        "ocr": "OCR",
        "plugin_processing": "Plugin Processing",
    }
    return labels.get(job_type, job_type.replace('_', ' ').title())


@router.get(
    "/statistics",
    response_model=DataExplorerStatisticsResponse,
    summary="Get Data Explorer statistics"
)
async def get_statistics(
    backend: StorageBackend = Depends(get_storage_backend)
) -> DataExplorerStatisticsResponse:
    """
    Get system statistics for the Data Explorer.
    
    Returns counts grouped by type and status for the explorer overview.
    """
    stats = DataExplorerStatistics(
        total_documents=0,
        total_collections=0,
        total_virtual_collections=0,
        total_saved_views=0,
        by_type={},
        by_status={},
    )
    
    if backend and hasattr(backend, '_get_connection'):
        try:
            conn = backend._get_connection()
            cur = conn.cursor()
            
            # Count total documents
            cur.execute("SELECT COUNT(*) FROM documents")
            row = cur.fetchone()
            if row:
                stats.total_documents = row[0]
            
            # Count by extension (type)
            cur.execute("""
                SELECT extension, COUNT(*) 
                FROM documents 
                WHERE extension IS NOT NULL 
                GROUP BY extension
                ORDER BY COUNT(*) DESC
                LIMIT 20
            """)
            for row in cur.fetchall():
                ext = row[0].lstrip('.') if row[0] else 'unknown'
                stats.by_type[ext] = row[1]
            
            # Count by status
            cur.execute("""
                SELECT status, COUNT(*) 
                FROM documents 
                WHERE status IS NOT NULL 
                GROUP BY status
            """)
            for row in cur.fetchall():
                if row[0]:
                    stats.by_status[row[0]] = row[1]
            
            cur.close()
            conn.close()
        except Exception:
            pass
    
    return DataExplorerStatisticsResponse(
        statistics=stats,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get(
    "/search",
    response_model=DataExplorerSearchResponse,
    summary="Search artifacts"
)
async def search_artifacts(
    backend: StorageBackend = Depends(get_storage_backend),
    q: str = Query(..., description="Search query"),
    type_filter: Optional[str] = Query(None, description="Filter by file extension (e.g., 'jpg', 'pdf')"),
    min_size: Optional[int] = Query(None, description="Minimum file size in bytes"),
    max_size: Optional[int] = Query(None, description="Maximum file size in bytes"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
) -> DataExplorerSearchResponse:
    """
    Search artifacts across the entire library.
    
    Supports:
    - Full-text search on filename and path
    - File type filtering by extension
    - File size filtering
    - Pagination via limit
    
    Results are returned as DataExplorerArtifact items.
    """
    artifacts = []
    filters_applied = {}
    
    if not backend or not hasattr(backend, '_get_connection'):
        return DataExplorerSearchResponse(
            artifacts=artifacts,
            total=0,
            query=q,
            filters_applied=filters_applied,
        )
    
    try:
        conn = backend._get_connection()
        cur = conn.cursor()
        
        # Build query conditions
        conditions = []
        params = []
        
        # Search query (filename or path contains query)
        if q:
            conditions.append("(path LIKE %s OR path LIKE %s)")
            params.append(f"%{q}%")
            params.append(f"%{q}%")
        
        # File type filter
        if type_filter:
            ext = type_filter if type_filter.startswith('.') else f".{type_filter}"
            conditions.append("extension = %s")
            params.append(ext.lower())
            filters_applied["type"] = type_filter
        
        # File size filters
        if min_size is not None:
            conditions.append("file_size >= %s")
            params.append(min_size)
            filters_applied["min_size"] = min_size
        
        if max_size is not None:
            conditions.append("file_size <= %s")
            params.append(max_size)
            filters_applied["max_size"] = max_size
        
        # Build final query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM documents WHERE {where_clause}"
        cur.execute(count_query, params)
        total = cur.fetchone()[0]
        
        # Get results with limit
        search_query = f"""
            SELECT id, path, extension, file_size, mime_type, modified_time,
                   indexed_at, status, thumbnail_path
            FROM documents
            WHERE {where_clause}
            ORDER BY indexed_at DESC
            LIMIT %s
        """
        params.append(limit)
        
        cur.execute(search_query, params)
        
        for row in cur.fetchall():
            doc_id, doc_path, ext, size, mime, modified, indexed, status, thumbnail = row
            
            # Extract filename from path
            filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
            
            # Build thumbnail URL
            thumbnail_url = None
            if thumbnail:
                thumbnail_url = f"/thumbnails/{thumbnail}"
            
            artifacts.append(DataExplorerArtifact(
                id=doc_id,
                name=filename,
                path=doc_path,
                type=ext.lstrip('.') if ext else None,
                size=size,
                modified=modified.isoformat() + "Z" if modified else None,
                thumbnail=thumbnail_url,
            ))
        
        cur.close()
        conn.close()
    except Exception:
        pass
    
    return DataExplorerSearchResponse(
        artifacts=artifacts,
        total=total,
        query=q,
        filters_applied=filters_applied,
    )


# Update forward references
DataExplorerNavigationItem.model_rebuild()
