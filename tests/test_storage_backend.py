import pytest

from evidence.evidence_builder import EvidenceBuilder
from storage.backend import StorageBackend, validate_backend_instance


class ConcreteBackend(StorageBackend):
    def save_collection(self, collection):
        return 1

    def save_document(self, document):
        return 1

    def save_entities(self, document_id, entities):
        return None

    def save_events(self, document_id, events):
        return None

    def save_locations(self, document_id, locations):
        return None

    def load_collection(self, collection_id=None, name=None):
        return {"id": collection_id or 1, "name": name or "default"}

    def search_documents(self, query=None, collection_id=None):
        return [{"query": query, "collection_id": collection_id}]

    def search_entities(self, entity_type=None, value=None):
        return [{"type": entity_type, "value": value}]

    def search_events(self, timestamp=None, event_type=None):
        return [{"timestamp": timestamp, "event_type": event_type}]

    def search_locations(self, location_name=None):
        return [{"name": location_name}]

    def mark_deleted(self, path):
        return True

    def discover_artifact(self, path, extension=None, file_size=None, modified_time=None):
        return 1


class PartialBackend(StorageBackend):
    def save_collection(self, collection):
        return 1

    def save_document(self, document):
        return 1

    def save_entities(self, document_id, entities):
        return None

    def save_events(self, document_id, events):
        return None

    def save_locations(self, document_id, locations):
        return None

    def load_collection(self, collection_id=None, name=None):
        return None

    def search_documents(self, query=None, collection_id=None):
        return []

    def search_entities(self, entity_type=None, value=None):
        return []

    def search_events(self, timestamp=None, event_type=None):
        return []

    def mark_deleted(self, path):
        return True

    def discover_artifact(self, path, extension=None, file_size=None, modified_time=None):
        return 1


def test_partial_backend_instantiation_fails_immediately():
    with pytest.raises(TypeError):
        PartialBackend()


def test_validate_backend_instance_rejects_non_backend():
    with pytest.raises(TypeError):
        validate_backend_instance(object())


def test_evidence_builder_calls_backend_methods_directly():
    builder = EvidenceBuilder(ConcreteBackend())

    assert builder.get_documents("doc") == [{"query": "doc", "collection_id": None}]
    assert builder.get_entities("person", "Ada") == [{"type": "person", "value": "Ada"}]
    assert builder.get_events("2026-01-01", "meeting") == [
        {"timestamp": "2026-01-01", "event_type": "meeting"}
    ]
    assert builder.get_locations("Manila") == [{"name": "Manila"}]
