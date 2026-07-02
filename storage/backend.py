from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def save_collection(self, collection):
        """Persist a collection and return its ID."""
        raise NotImplementedError()

    @abstractmethod
    def save_document(self, document):
        raise NotImplementedError()

    @abstractmethod
    def save_entities(self, document_id, entities):
        raise NotImplementedError()

    @abstractmethod
    def save_events(self, document_id, events):
        raise NotImplementedError()

    @abstractmethod
    def save_locations(self, document_id, locations):
        raise NotImplementedError()

    @abstractmethod
    def load_collection(self, collection_id=None, name=None):
        raise NotImplementedError()

    @abstractmethod
    def search_documents(self, query=None, collection_id=None):
        raise NotImplementedError()

    @abstractmethod
    def search_entities(self, entity_type=None, value=None):
        raise NotImplementedError()

    @abstractmethod
    def search_events(self, timestamp=None, event_type=None):
        raise NotImplementedError()

    @abstractmethod
    def search_locations(self, location_name=None):
        raise NotImplementedError()

    @abstractmethod
    def mark_deleted(self, path):
        """Mark a document as deleted (soft delete).
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        Deleted files are marked, not deleted. Records are preserved for auditability.
        
        Args:
            path: Document path to mark as deleted
            
        Returns:
            True if marked, False otherwise
        """
        raise NotImplementedError()

    @abstractmethod
    def discover_artifact(self, path, extension=None, file_size=None, modified_time=None, mime_type=None):
        """Create an artifact record immediately upon discovery.
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        A file exists immediately upon discovery. Parser availability does not affect existence.
        
        This method creates a document record without requiring a parser.
        It is called by CollectionWatcher before any parsing is attempted.
        
        Args:
            path: Full path to the file
            extension: File extension (e.g., '.jpg')
            file_size: File size in bytes
            modified_time: Last modified timestamp
            mime_type: MIME type of the artifact (e.g., 'image/jpeg')
                       Determined from extension during discovery, persisted as
                       Discovery Metadata - no worker or parser dependency.
            
        Returns:
            Document ID if created, None on failure
        """
        raise NotImplementedError()

    @abstractmethod
    def get_trace_filters(self) -> dict:
        """Get available filters for the Trace view."""
        raise NotImplementedError()

    @abstractmethod
    def get_trace_data(
        self,
        cameras: list = None,
        collections: list = None,
        years: list = None,
        sources: list = None,
        limit: int = 100,
        offset: int = 0
    ) -> dict:
        """Get Trace data with filters applied."""
        raise NotImplementedError()

    @abstractmethod
    def get_trace_photo_detail(self, document_id: int) -> dict:
        """Get full photo metadata for Trace view."""
        raise NotImplementedError()


def validate_backend_instance(backend: StorageBackend) -> StorageBackend:
    """Validate that an initialized backend satisfies the StorageBackend ABC."""
    if not isinstance(backend, StorageBackend):
        raise TypeError(
            f"Configured backend must implement StorageBackend; got {type(backend).__name__}"
        )
    return backend