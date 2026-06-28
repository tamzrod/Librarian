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