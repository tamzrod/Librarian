class StorageBackend:
    def save_collection(self, collection):
        raise NotImplementedError()

    def save_document(self, document):
        raise NotImplementedError()

    def save_entities(self, document_id, entities):
        raise NotImplementedError()

    def save_events(self, document_id, events):
        raise NotImplementedError()

    def save_locations(self, document_id, locations):
        raise NotImplementedError()

    def load_collection(self, collection_id=None, name=None):
        raise NotImplementedError()

    def search_documents(self, query, collection_id=None):
        raise NotImplementedError()

    def search_entities(self, entity_type=None, value=None):
        raise NotImplementedError()

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

    def discover_artifact(self, path, extension=None, file_size=None, modified_time=None):
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
            
        Returns:
            Document ID if created, None on failure
        """
        raise NotImplementedError()