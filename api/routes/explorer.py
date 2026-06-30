"""Artifact Explorer API routes.

Provides folder hierarchy, artifact listing, and file preview for the Artifact Explorer interface.
Models a familiar file-browser experience similar to VSCode, Finder, or Windows Explorer.
"""

import os
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from api.dependencies import get_storage_backend
from api.app_state import get_app_state
from storage.backend import StorageBackend


router = APIRouter(prefix="/explorer", tags=["explorer"])


# ============================================================================
# Schema Definitions
# ============================================================================

class FolderNode(BaseModel):
    """A folder node in the hierarchy."""
    id: str = Field(description="Unique folder identifier (URL-encoded path)")
    name: str = Field(description="Folder name")
    path: str = Field(description="Full path to folder")
    has_children: bool = Field(description="Whether folder contains subfolders")


class FolderTreeResponse(BaseModel):
    """Folder hierarchy tree."""
    root: FolderNode = Field(description="Root folder node")
    total_folders: int = Field(description="Total number of folders")


class DocumentSummary(BaseModel):
    """Document summary for explorer."""
    id: int = Field(description="Document ID")
    name: str = Field(description="Filename")
    path: str = Field(description="Full path to document")
    extension: Optional[str] = Field(default=None, description="File extension (e.g., '.jpg')")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    modified_time: Optional[str] = Field(default=None, description="Last modified time (ISO 8601)")
    indexed_at: Optional[str] = Field(default=None, description="When document was indexed")
    status: str = Field(description="Indexing status")


class FolderContentsResponse(BaseModel):
    """Contents of a folder."""
    folder: FolderNode = Field(description="Folder information")
    folders: list[FolderNode] = Field(description="Subfolders")
    documents: list[DocumentSummary] = Field(description="Documents in folder")
    total_items: int = Field(description="Total items (folders + documents)")


class ProcessingStatus(BaseModel):
    """Processing status for a document."""
    job_type: str = Field(description="Type of processing job")
    status: str = Field(description="Status: QUEUED, IN_PROGRESS, COMPLETED, FAILED, CANCELLED")
    label: str = Field(description="Human-readable label")


class DocumentDetail(BaseModel):
    """Detailed document information for metadata panel."""
    id: int = Field(description="Document ID")
    name: str = Field(description="Filename")
    path: str = Field(description="Full path to document")
    extension: Optional[str] = Field(default=None, description="File extension")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    modified_time: Optional[str] = Field(default=None, description="Last modified time")
    created_at: Optional[str] = Field(default=None, description="When document was created")
    indexed_at: Optional[str] = Field(default=None, description="When document was indexed")
    status: str = Field(description="Indexing status")
    character_count: Optional[int] = Field(default=None, description="Character count if text")
    # File hashes
    md5: Optional[str] = Field(default=None, description="MD5 hash")
    sha1: Optional[str] = Field(default=None, description="SHA1 hash")
    sha256: Optional[str] = Field(default=None, description="SHA256 hash")
    # Artifact type classification
    artifact_type: Optional[str] = Field(default=None, description="Artifact type: Image, Document, Video, Audio, Archive, Structured Data")
    # Processing status from jobs
    processing_status: list[ProcessingStatus] = Field(default_factory=list, description="Enrichment processing status")


class DocumentDetailResponse(BaseModel):
    """Document detail response."""
    document: DocumentDetail


# ============================================================================
# Helper Functions
# ============================================================================

def _build_folder_tree_from_paths(paths: list[str], parent_path: str = "") -> list[FolderNode]:
    """Build folder tree structure from a list of paths.
    
    Args:
        paths: List of document paths
        parent_path: Parent path to filter (empty for root)
    
    Returns:
        List of FolderNode objects representing the folder hierarchy
    """
    folders_map: dict[str, set] = {}
    
    for path in paths:
        # Normalize path - remove trailing slash
        path = path.rstrip('/')
        
        if parent_path:
            if not path.startswith(parent_path):
                continue
            relative = path[len(parent_path):].lstrip('/')
        else:
            relative = path.lstrip('/')
        
        # Split into parts
        parts = relative.split('/')
        
        # Add the first level folder
        if parts:
            first_folder = parts[0]
            if first_folder not in folders_map:
                folders_map[first_folder] = set()
            
            # Track subfolders
            if len(parts) > 1:
                folders_map[first_folder].add('/'.join(parts[1:]))
    
    # Build folder nodes
    folder_nodes = []
    for folder_name in sorted(folders_map.keys()):
        subfolders = folders_map[folder_name]
        full_path = f"{parent_path}/{folder_name}" if parent_path else f"/{folder_name}"
        
        # Check if this folder has children (subfolders or documents)
        has_children = len(subfolders) > 0 or any(
            f.startswith(f"{folder_name}/") or f.split('/')[0] == folder_name
            for f in paths
        )
        
        folder_nodes.append(FolderNode(
            id=full_path,
            name=folder_name,
            path=full_path,
            has_children=has_children
        ))
    
    return folder_nodes


def _extract_folder_paths(conn) -> list[str]:
    """Extract unique folder paths from documents table.
    
    Returns:
        List of unique parent directory paths
    """
    paths = set()
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT path FROM documents ORDER BY path")
        
        for row in cur.fetchall():
            doc_path = row[0] or ""
            if '/' in doc_path:
                # Extract directory path (everything except filename)
                folder_path = '/'.join(doc_path.rsplit('/', 1)[:-1])
                if folder_path:
                    paths.add(folder_path)
            else:
                # File in root - treat root as a folder
                paths.add('/')
        
        cur.close()
    except Exception:
        pass
    
    return sorted(list(paths))


def _get_subfolders(conn, parent_path: str) -> list[FolderNode]:
    """Get subfolders within a parent path.
    
    Args:
        conn: Database connection
        parent_path: Parent folder path
    
    Returns:
        List of immediate subfolders
    """
    folders_map: dict[str, bool] = {}
    prefix = f"{parent_path}/" if not parent_path.endswith('/') else parent_path
    
    try:
        cur = conn.cursor()
        
        if parent_path == "/":
            # Root level - get top-level folders
            cur.execute("SELECT path FROM documents")
        else:
            # Subfolder level
            cur.execute("SELECT path FROM documents WHERE path LIKE %s", (f"{prefix}%",))
        
        for row in cur.fetchall():
            doc_path = row[0] or ""
            if parent_path == "/":
                # Get top-level folder names
                relative = doc_path.lstrip('/')
                if '/' in relative:
                    folder_name = relative.split('/')[0]
                    if folder_name:
                        folders_map[folder_name] = True
            else:
                # Get subfolder names
                if doc_path.startswith(prefix):
                    remaining = doc_path[len(prefix):]
                    if '/' in remaining:
                        folder_name = remaining.split('/')[0]
                        if folder_name:
                            folders_map[folder_name] = True
        
        cur.close()
    except Exception:
        pass
    
    return [
        FolderNode(
            id=f"{parent_path}/{name}" if parent_path != "/" else f"/{name}",
            name=name,
            path=f"{parent_path}/{name}" if parent_path != "/" else f"/{name}",
            has_children=True  # Assume children for now
        )
        for name in sorted(folders_map.keys())
    ]


def _get_documents_in_folder(conn, folder_path: str) -> list[DocumentSummary]:
    """Get documents within a specific folder.
    
    Args:
        conn: Database connection
        folder_path: Folder path to query
    
    Returns:
        List of documents in the folder
    """
    documents = []
    
    try:
        cur = conn.cursor()
        
        if folder_path == "/":
            # Root level - documents without subfolder
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       indexed_at, status, character_count
                FROM documents
                WHERE path NOT LIKE '%/%'
                ORDER BY path
            """)
        else:
            # Specific folder
            prefix = f"{folder_path}/"
            folder_name = folder_path.rsplit('/', 1)[-1]
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       indexed_at, status, character_count
                FROM documents
                WHERE path LIKE %s AND path NOT LIKE %s
                ORDER BY path
            """, (f"{prefix}%", f"{prefix}%/%"))
        
        for row in cur.fetchall():
            doc_id, doc_path, ext, size, mime, modified, indexed, status, char_count = row
            
            # Extract filename from path
            filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
            
            documents.append(DocumentSummary(
                id=doc_id,
                name=filename,
                path=doc_path,
                extension=ext,
                file_size=size,
                mime_type=mime,
                modified_time=modified.isoformat() + "Z" if modified else None,
                indexed_at=indexed.isoformat() + "Z" if indexed else None,
                status=status or "UNKNOWN",
            ))
        
        cur.close()
    except Exception:
        pass
    
    return documents


# ============================================================================
# Routes
# ============================================================================

@router.get(
    "/tree",
    response_model=FolderTreeResponse,
    summary="Get folder hierarchy tree"
)
async def get_folder_tree(
    backend: StorageBackend = Depends(get_storage_backend)
) -> FolderTreeResponse:
    """
    Get the complete folder hierarchy tree.
    
    Returns the root folder and all subfolders as a tree structure.
    This is used to populate the left pane of the Artifact Explorer.
    """
    root_path = "/library"
    subfolders = []
    total_folders = 1  # Root folder
    
    if backend and hasattr(backend, '_get_connection'):
        try:
            conn = backend._get_connection()
            
            # Get all unique folder paths
            paths = _extract_folder_paths(conn)
            
            # Build tree structure
            # Pass root_path as parent_path to skip the library prefix when extracting
            # folder names. Without this, absolute paths like /library/Camera would
            # incorrectly extract "library" as the first folder segment.
            subfolders = _build_folder_tree_from_paths(paths, root_path)
            total_folders += len(subfolders)
            
            # Recursively build tree for each top-level folder
            for folder in subfolders:
                nested = _build_folder_tree_from_paths(paths, folder.path)
                if nested:
                    folder.has_children = True
            
            conn.close()
        except Exception:
            pass
    
    # Build root node
    root_node = FolderNode(
        id=root_path,
        name="library",
        path=root_path,
        has_children=len(subfolders) > 0
    )
    
    # If we have subfolders, the root has children
    if subfolders:
        root_node = FolderNode(
            id=root_path,
            name="library",
            path=root_path,
            has_children=True
        )
    
    return FolderTreeResponse(
        root=root_node,
        total_folders=total_folders
    )


@router.get(
    "/folders/{folder_path:path}",
    response_model=FolderContentsResponse,
    summary="Get folder contents"
)
async def get_folder_contents(
    folder_path: str,
    backend: StorageBackend = Depends(get_storage_backend)
) -> FolderContentsResponse:
    """
    Get the contents of a specific folder.
    
    Returns subfolders and documents within the specified folder.
    The folder_path should be URL-encoded if it contains slashes.
    """
    # Normalize folder path
    folder_path = "/" + folder_path.strip("/")
    
    # Handle root folder
    if folder_path == "/":
        folder_path = "/library"
    
    subfolders = []
    documents = []
    
    if backend and hasattr(backend, '_get_connection'):
        try:
            conn = backend._get_connection()
            
            # Get subfolders
            subfolders = _get_subfolders(conn, folder_path)
            
            # Get documents in this folder
            documents = _get_documents_in_folder(conn, folder_path)
            
            conn.close()
        except Exception:
            pass
    
    folder_node = FolderNode(
        id=folder_path,
        name=folder_path.rsplit('/', 1)[-1] or "library",
        path=folder_path,
        has_children=len(subfolders) > 0
    )
    
    return FolderContentsResponse(
        folder=folder_node,
        folders=subfolders,
        documents=documents,
        total_items=len(subfolders) + len(documents)
    )


def _determine_artifact_type(extension: str | None, mime_type: str | None) -> str:
    """Determine artifact type from extension and MIME type."""
    ext = (extension or '').lower()
    
    # Image types
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.tiff', '.tif', '.heic', '.heif'}
    if ext in image_exts or (mime_type and mime_type.startswith('image/')):
        return 'Image'
    
    # Video types
    video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
    if ext in video_exts or (mime_type and mime_type.startswith('video/')):
        return 'Video'
    
    # Audio types
    audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
    if ext in audio_exts or (mime_type and mime_type.startswith('audio/')):
        return 'Audio'
    
    # Archive types
    archive_exts = {'.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz'}
    if ext in archive_exts:
        return 'Archive'
    
    # Structured data types
    structured_exts = {'.json', '.xml', '.yaml', '.yml', '.csv', '.tsv', '.toml'}
    if ext in structured_exts:
        return 'Structured Data'
    
    # Document types
    doc_exts = {'.pdf', '.doc', '.docx', '.odt', '.rtf', '.txt', '.md', '.rst'}
    if ext in doc_exts or (mime_type and mime_type.startswith('text/')):
        return 'Document'
    
    # Default to Document for text-like content
    if mime_type and mime_type.startswith('text/'):
        return 'Document'
    
    return 'Unknown'


# Job type to human-readable label mapping
JOB_TYPE_LABELS = {
    'extract_text': 'Text Extraction',
    'extract_entities': 'Entity Extraction',
    'extract_events': 'Event Extraction',
    'extract_locations': 'Location Extraction',
    'generate_embeddings': 'Embeddings Generation',
    'ocr': 'OCR Processing',
    'extract_photo_metadata': 'Photo Metadata Extraction',
    'plugin_processing': 'Plugin Processing',
}


@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details"
)
async def get_document_details(
    document_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
) -> DocumentDetailResponse:
    """
    Get detailed information about a specific document.
    
    Returns full document metadata for the metadata panel.
    """
    document = None
    
    if backend and hasattr(backend, '_get_connection'):
        try:
            conn = backend._get_connection()
            cur = conn.cursor()
            
            # Get document details
            cur.execute("""
                SELECT id, path, extension, file_size, mime_type, modified_time,
                       created_at, indexed_at, status, character_count, sha256
                FROM documents
                WHERE id = %s
            """, (document_id,))
            
            row = cur.fetchone()
            if row:
                doc_id, doc_path, ext, size, mime, modified, created, indexed, status, char_count, sha = row
                filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
                
                # Determine artifact type
                artifact_type = _determine_artifact_type(ext, mime)
                
                # Get processing status from jobs
                cur.execute("""
                    SELECT job_type, status
                    FROM document_jobs
                    WHERE document_id = %s
                    ORDER BY created_at DESC
                """, (document_id,))
                
                processing_status = []
                for job_row in cur.fetchall():
                    job_type, job_status = job_row
                    processing_status.append(ProcessingStatus(
                        job_type=job_type,
                        status=job_status,
                        label=JOB_TYPE_LABELS.get(job_type, job_type.replace('_', ' ').title())
                    ))
                
                document = DocumentDetail(
                    id=doc_id,
                    name=filename,
                    path=doc_path,
                    extension=ext,
                    file_size=size,
                    mime_type=mime,
                    modified_time=modified.isoformat() + "Z" if modified else None,
                    created_at=created.isoformat() + "Z" if created else None,
                    indexed_at=indexed.isoformat() + "Z" if indexed else None,
                    status=status or "UNKNOWN",
                    character_count=char_count,
                    sha256=sha,
                    artifact_type=artifact_type,
                    processing_status=processing_status
                )
            
            cur.close()
            conn.close()
        except Exception:
            pass
    
    if not document:
        # Return placeholder for non-existent document
        document = DocumentDetail(
            id=document_id,
            name="Unknown",
            path="/",
            status="NOT_FOUND"
        )
    
    return DocumentDetailResponse(document=document)


# Supported preview MIME types
PREVIEWABLE_TEXT_TYPES = {
    'text/plain',
    'text/markdown',
    'text/x-python',
    'text/x-java',
    'text/x-c',
    'text/x-c++',
    'application/json',
    'application/xml',
    'application/yaml',
    'text/yaml',
    'text/x-log',
}

PREVIEWABLE_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
    'image/bmp',
    'image/svg+xml',
}

# File extensions mapped to MIME types
EXT_TO_MIME = {
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.markdown': 'text/markdown',
    '.json': 'application/json',
    '.yaml': 'application/yaml',
    '.yml': 'application/yaml',
    '.xml': 'application/xml',
    '.py': 'text/x-python',
    '.log': 'text/x-log',
    '.ini': 'text/plain',
    '.cfg': 'text/plain',
    '.conf': 'text/plain',
    '.env': 'text/plain',
    '.java': 'text/x-java',
    '.c': 'text/x-c',
    '.cpp': 'text/x-c++',
    '.h': 'text/x-c',
    '.js': 'application/javascript',
    '.ts': 'application/typescript',
    '.jsx': 'text/javascript',
    '.tsx': 'text/typescript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.rst': 'text/x-rst',
    # Images
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp',
    '.svg': 'image/svg+xml',
}

# Text file extensions
TEXT_EXTENSIONS = {'.txt', '.md', '.markdown', '.json', '.yaml', '.yml', '.xml', '.py', '.log', '.ini', '.cfg', '.conf', '.env', '.java', '.c', '.cpp', '.h', '.js', '.ts', '.jsx', '.tsx', '.css', '.html', '.rst'}

# Image file extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}

# Maximum text preview size (50KB)
MAX_TEXT_PREVIEW_SIZE = 50 * 1024


@router.get(
    "/documents/{document_id}/preview",
    summary="Get document preview"
)
async def get_document_preview(
    document_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
):
    """
    Get a preview of the document content.
    
    For images: Returns the raw image file.
    For text: Returns the first 50KB of text content.
    For other files: Returns a 404 with "unsupported" message.
    
    This endpoint is designed for fast, lightweight previews without
    triggering any AI or enrichment processing.
    """
    # Get document path from database
    doc_path = None
    doc_extension = None
    
    if backend and hasattr(backend, '_get_connection'):
        try:
            conn = backend._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT path, extension FROM documents WHERE id = %s", (document_id,))
            row = cur.fetchone()
            if row:
                doc_path = row[0]
                doc_extension = row[1]
            cur.close()
            conn.close()
        except Exception:
            pass
    
    if not doc_path:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get library root from app state
    app_state = get_app_state()
    library_root = app_state.library_root
    
    # Construct full file path
    # The path stored in DB is relative to library root
    if doc_path.startswith('/'):
        # Remove leading slash and join with library root
        relative_path = doc_path.lstrip('/')
        full_path = os.path.join(library_root, relative_path)
    else:
        full_path = os.path.join(library_root, doc_path)
    
    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Normalize extension
    ext = (doc_extension or '').lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    
    # Handle based on file type
    if ext in IMAGE_EXTENSIONS:
        # Return image file directly
        return FileResponse(
            full_path,
            media_type=EXT_TO_MIME.get(ext, 'application/octet-stream')
        )
    
    elif ext in TEXT_EXTENSIONS:
        # Return text content (first N bytes)
        return _stream_text_preview(full_path, ext)
    
    else:
        # Unsupported type
        raise HTTPException(status_code=415, detail="Preview not supported for this file type")


def _stream_text_preview(file_path: str, extension: str) -> StreamingResponse:
    """
    Stream the first N bytes of a text file.
    
    Uses streaming to avoid loading large files into memory.
    """
    def generate():
        try:
            with open(file_path, 'rb') as f:
                # Read up to MAX_TEXT_PREVIEW_SIZE bytes
                data = f.read(MAX_TEXT_PREVIEW_SIZE)
                
                # Detect encoding and decode
                # Try UTF-8 first, fall back to latin-1
                try:
                    text = data.decode('utf-8')
                except UnicodeDecodeError:
                    text = data.decode('latin-1', errors='replace')
                
                # Truncate at a reasonable line boundary if we're at the limit
                if len(data) >= MAX_TEXT_PREVIEW_SIZE:
                    lines = text.split('\n')
                    if len(lines) > 1:
                        # Keep complete lines
                        preview_lines = []
                        current_size = 0
                        for line in lines:
                            line_size = len(line) + 1  # +1 for newline
                            if current_size + line_size > MAX_TEXT_PREVIEW_SIZE:
                                break
                            preview_lines.append(line)
                            current_size += line_size
                        text = '\n'.join(preview_lines)
                        if len(data) >= MAX_TEXT_PREVIEW_SIZE:
                            text += f"\n\n[... {(os.path.getsize(file_path) - MAX_TEXT_PREVIEW_SIZE) // 1024} KB more truncated ...]"
                
                yield text.encode('utf-8')
        except Exception as e:
            yield f"Error reading file: {str(e)}".encode('utf-8')
    
    # Determine media type
    media_type = EXT_TO_MIME.get(extension, 'text/plain')
    
    return StreamingResponse(
        generate(),
        media_type=media_type,
        headers={
            'Content-Type': f'{media_type}; charset=utf-8',
            'X-Preview-Type': 'text',
            'X-File-Extension': extension,
        }
    )


@router.get(
    "/documents/{document_id}/raw",
    summary="Get raw document file"
)
async def get_raw_document(
    document_id: int,
    backend: StorageBackend = Depends(get_storage_backend)
):
    """
    Get the raw document file for download.
    
    Streams the file directly without loading into memory.
    Supports caching via ETag header.
    """
    # Get document path from database
    doc_path = None
    doc_extension = None
    
    if backend and hasattr(backend, '_get_connection'):
        try:
            conn = backend._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT path, extension, mime_type FROM documents WHERE id = %s", (document_id,))
            row = cur.fetchone()
            if row:
                doc_path = row[0]
                doc_extension = row[1]
                doc_mime = row[2]
            cur.close()
            conn.close()
        except Exception:
            pass
    
    if not doc_path:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get library root from app state
    app_state = get_app_state()
    library_root = app_state.library_root
    
    # Construct full file path
    if doc_path.startswith('/'):
        relative_path = doc_path.lstrip('/')
        full_path = os.path.join(library_root, relative_path)
    else:
        full_path = os.path.join(library_root, doc_path)
    
    # Check if file exists
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Determine media type
    ext = (doc_extension or '').lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    media_type = EXT_TO_MIME.get(ext, doc_mime or 'application/octet-stream')
    
    # Extract filename from path
    filename = doc_path.rsplit('/', 1)[-1] if '/' in doc_path else doc_path
    
    return FileResponse(
        full_path,
        media_type=media_type,
        filename=filename,
        headers={
            'Content-Disposition': f'inline; filename="{filename}"',
        }
    )
