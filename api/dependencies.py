"""FastAPI dependencies for Librarian API."""

from typing import Generator

# Import storage backend
try:
    from storage.backend import StorageBackend
except ImportError:
    StorageBackend = None


def get_storage_backend() -> Generator:
    """
    Dependency that provides the storage backend.
    
    Returns the actual backend from app_state when available,
    falling back to MockBackend if not initialized or if DATABASE_URL is not set.
    """
    from api.app_state import get_app_state
    state = get_app_state()
    if state.backend is not None:
        yield state.backend
    else:
        yield MockBackend()


class MockBackend:
    """Mock backend for development and testing.
    
    ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
    This mock supports the artifact inventory architecture.
    """
    
    def __init__(self):
        self.collections = {
            1: {"id": 1, "name": "Default Collection", "root_path": "/tmp"}
        }
        self.documents = {}
        self._next_id = 1
    
    def collection_exists(self, collection_id: int) -> bool:
        """Check if collection exists."""
        return collection_id in self.collections
    
    def search_documents(self, query: str = None, entity: str = None, 
                         date: str = None, month: str = None, location: str = None):
        """Mock document search."""
        return []
    
    def search_entities(self, entity_type: str = None, value: str = None):
        """Mock entity search."""
        return []
    
    def search_events(self, date: str = None, month: str = None, 
                      entity: str = None, event_type: str = None):
        """Mock event search."""
        return []
    
    def search_locations(self, date: str = None, month: str = None,
                         entity: str = None, location_name: str = None):
        """Mock location search."""
        return []
    
    def search_relationships(self, entity: str = None, relationship_type: str = None):
        """Mock relationship search."""
        return []
    
    def discover_artifact(self, path: str, extension: str = None, 
                          file_size: int = None, modified_time = None, mime_type: str = None) -> int:
        """Create an artifact record immediately upon discovery.
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        E1: mime_type is Discovery Metadata - persisted immediately from extension.
        """
        doc_id = self._next_id
        self._next_id += 1
        self.documents[path] = {
            'id': doc_id,
            'path': path,
            'extension': extension,
            'file_size': file_size,
            'modified_time': modified_time,
            'status': 'DISCOVERED',
            'exists_on_disk': True,
            'lifecycle_state': 'discovered',
            'artifact_type': self._classify_artifact_type(extension),
            'mime_type': mime_type
        }
        return doc_id
    
    def save_document(self, document: dict) -> int:
        """Save a document."""
        path = document.get('path', '')
        if path in self.documents:
            self.documents[path].update(document)
            return self.documents[path]['id']
        else:
            doc_id = self._next_id
            self._next_id += 1
            self.documents[path] = {'id': doc_id, **document}
            return doc_id
    
    def mark_deleted(self, path: str) -> bool:
        """Mark a document as deleted (soft delete).
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        Deleted files are marked, not deleted. Records are preserved for auditability.
        """
        if path in self.documents:
            self.documents[path]['exists_on_disk'] = False
            return True
        return False
    
    def _classify_artifact_type(self, extension: str = None) -> str:
        """Classify artifact type based on extension."""
        ext = (extension or '').lower()
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
        audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        archive_exts = {'.zip', '.tar', '.gz', '.bz2', '.xz', '.rar', '.7z'}
        structured_exts = {'.csv', '.tsv', '.json', '.xml', '.yaml', '.yml', '.toml', '.db'}
        
        if ext in image_exts:
            return 'image'
        if ext in video_exts:
            return 'video'
        if ext in audio_exts:
            return 'audio'
        if ext in archive_exts:
            return 'archive'
        if ext in structured_exts:
            return 'structured'
        return 'unknown'