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
    """Mock backend for Phase 1 development."""
    
    def __init__(self):
        self.collections = {
            1: {"id": 1, "name": "Default Collection", "root_path": "/tmp"}
        }
    
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