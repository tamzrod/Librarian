"""
Shared pytest fixtures for Librarian tests.

Provides an InMemoryBackend and associated fixtures that let integration
tests exercise CollectionWatcher, EntityExtractor and EventExtractor
without requiring a live PostgreSQL database.
"""

import tempfile
import shutil
from pathlib import Path

import pytest

from ingestion.collection_watcher import CollectionWatcher


# ---------------------------------------------------------------------------
# In-memory backend
# ---------------------------------------------------------------------------

class InMemoryBackend:
    """
    Full in-memory storage backend used by pipeline E2E tests.

    Supports all methods called by CollectionWatcher, EntityExtractor and
    EventExtractor so that the complete watcher → extraction pipeline can be
    exercised without a database connection.
    """

    def __init__(self):
        self.documents = {}         # path  -> doc dict
        self.documents_by_id = {}   # id    -> doc dict
        self.content = {}           # doc_id -> {'content': str, 'source': str}
        self.entities = []          # [{'id', 'type', 'value', 'normalized_value'}]
        self.doc_entities = {}      # doc_id -> [entity_id]
        self.events = {}            # doc_id -> [event dict]
        self.locations = {}         # doc_id -> [location dict]
        self.jobs = []              # [job dict]
        self._next_id = 1
        self._next_entity_id = 1
        self._next_job_id = 1

    # -- Artifact / document lifecycle --------------------------------------

    def discover_artifact(self, path, extension=None, file_size=None, modified_time=None):
        doc_id = self._next_id
        self._next_id += 1
        doc = {
            'id': doc_id,
            'path': path,
            'extension': extension,
            'file_size': file_size,
            'modified_time': modified_time,
            'status': 'DISCOVERED',
            'exists_on_disk': True,
        }
        self.documents[path] = doc
        self.documents_by_id[doc_id] = doc
        return doc_id

    def save_document(self, document):
        path = document.get('path', '')
        if path in self.documents:
            self.documents[path].update(document)
            return self.documents[path]['id']
        doc_id = self._next_id
        self._next_id += 1
        doc = {'id': doc_id, **document}
        self.documents[path] = doc
        self.documents_by_id[doc_id] = doc
        return doc_id

    def mark_deleted(self, path):
        if path in self.documents:
            self.documents[path]['exists_on_disk'] = False
            return True
        return False

    def transition_document_status(self, doc_id, new_status):
        if doc_id not in self.documents_by_id:
            raise ValueError(f"Document {doc_id} not found")
        self.documents_by_id[doc_id]['status'] = new_status

    # -- Content -------------------------------------------------------------

    def save_content(self, doc_id, content, source):
        self.content[doc_id] = {'content': content, 'source': source}
        return True

    def get_content(self, doc_id):
        return self.content.get(doc_id)

    # -- Entities ------------------------------------------------------------

    def save_entity(self, entity_type, value, normalized=None):
        entity_id = self._next_entity_id
        self._next_entity_id += 1
        self.entities.append({
            'id': entity_id,
            'type': entity_type,
            'value': value,
            'normalized_value': normalized or value.lower(),
        })
        return entity_id

    def add_entity_to_document(self, doc_id, entity_id, weight=1):
        self.doc_entities.setdefault(doc_id, []).append(entity_id)

    def save_entities(self, doc_id, entities):
        for entity in entities:
            eid = self.save_entity(
                entity.get('type', 'UNKNOWN'),
                entity.get('value', ''),
            )
            self.add_entity_to_document(doc_id, eid)

    def get_entities_for_document(self, doc_id):
        ids = self.doc_entities.get(doc_id, [])
        return [e for e in self.entities if e['id'] in ids]

    # -- Events / locations --------------------------------------------------

    def save_event(self, timestamp, event_type, description=''):
        """Save a single event and return its ID (called by EventExtractor)."""
        event_id = len(self.events) + 1
        event = {'id': event_id, 'timestamp': timestamp, 'event_type': event_type, 'description': description}
        self.events.setdefault('_all', []).append(event)
        return event_id

    def add_event_to_document(self, doc_id, event_id):
        self.events.setdefault(doc_id, []).append(event_id)

    def save_events(self, doc_id, events):
        self.events[doc_id] = events

    def save_locations(self, doc_id, locations):
        self.locations[doc_id] = locations

    # -- Jobs ----------------------------------------------------------------

    def create_jobs_for_document(self, doc_id, **kwargs):
        job_ids = []
        for job_type in ('extract_text', 'extract_entities', 'extract_events'):
            job_id = self._next_job_id
            self._next_job_id += 1
            self.jobs.append({
                'id': job_id,
                'document_id': doc_id,
                'job_type': job_type,
                'status': 'QUEUED',
                'worker_id': None,
            })
            job_ids.append(job_id)
        return job_ids

    def claim_job(self, worker_id, job_type=None):
        for job in self.jobs:
            if job['status'] != 'QUEUED':
                continue
            if job_type is not None and job['job_type'] != job_type:
                continue
            job['status'] = 'IN_PROGRESS'
            job['worker_id'] = worker_id
            return job
        return None

    def complete_job(self, job_id, success=True):
        for job in self.jobs:
            if job['id'] == job_id:
                job['status'] = 'COMPLETED' if success else 'FAILED'
                return True
        return False

    # -- Optional extras used by evidence / record plumbing ------------------

    def record_evidence(self, **kwargs):
        pass


# ---------------------------------------------------------------------------
# Mock parser registry
# ---------------------------------------------------------------------------

class _MockParser:
    """Returns file text as parsed content."""

    def parse(self, filepath):
        try:
            text = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            text = ''
        return {'text': text, 'character_count': len(text), 'parser': 'text'}


class MockParserRegistry:
    """
    Minimal parser registry for testing.

    Recognises .txt, .md, .json, .yaml, .yml, and .csv files.
    All other extensions are treated as unparseable (no parser).
    """

    _SUPPORTED = {'.txt', '.md', '.json', '.yaml', '.yml', '.csv'}

    def get_parser(self, filepath):
        ext = Path(filepath).suffix.lower()
        return _MockParser() if ext in self._SUPPORTED else None

    def get_artifact_type(self, filepath):
        ext = Path(filepath).suffix.lower()
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        if ext in image_exts:
            return 'image'
        if ext in {'.zip', '.tar', '.gz', '.bz2', '.rar'}:
            return 'archive'
        if ext in {'.csv', '.json', '.xml', '.yaml', '.yml', '.db'}:
            return 'structured'
        if ext in self._SUPPORTED:
            return 'document'
        return 'unknown'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def backend():
    """Fresh InMemoryBackend for each test."""
    return InMemoryBackend()


@pytest.fixture()
def mock_parser_registry():
    """MockParserRegistry instance."""
    return MockParserRegistry()


@pytest.fixture()
def tmp_collection_dir():
    """
    Temporary directory pre-populated with sample files.

    Yields the Path; cleans up automatically after the test.
    """
    tmpdir = tempfile.mkdtemp(prefix='librarian_test_')
    collection = Path(tmpdir) / 'collection'
    collection.mkdir()

    # Plain-text document with named entities
    (collection / 'memo.txt').write_text(
        'John Smith visited Manila on January 1, 2025. '
        'He met with Jane Doe at Acme Corp.',
        encoding='utf-8',
    )

    # JSON structured file
    (collection / 'data.json').write_text(
        '{"author": "Alice Brown", "location": "Tokyo", "year": 2024}',
        encoding='utf-8',
    )

    # Binary-like file with no supported parser
    (collection / 'archive.xyz').write_bytes(b'\x00\x01\x02\x03')

    yield collection

    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture()
def watcher(tmp_collection_dir, backend, mock_parser_registry):
    """CollectionWatcher pointed at the temporary collection."""
    return CollectionWatcher(
        str(tmp_collection_dir),
        backend,
        mock_parser_registry,
    )
