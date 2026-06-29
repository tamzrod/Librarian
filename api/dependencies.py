"""FastAPI dependencies for Librarian API."""

from typing import Generator

# Import storage backend
try:
    from storage.backend import StorageBackend
except ImportError:
    StorageBackend = None


def get_storage_backend() -> Generator[StorageBackend, None, None]:
    """
    Dependency that provides the storage backend.
    
    For Phase 1, returns a mock backend.
    In production, this would connect to PostgreSQL.
    """
    # For Phase 1, return a simple mock backend
    # This will be replaced with actual backend in later phases
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