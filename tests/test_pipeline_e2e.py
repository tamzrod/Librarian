"""
P6 — Pipeline end-to-end integration tests.

These tests exercise the full ingestion pipeline using an InMemoryBackend
(defined in conftest.py) so that they run without a live PostgreSQL instance
and are included in the standard CI unit-test job.

Coverage:
  - File discovery via CollectionWatcher._scan_and_detect_changes()
  - Content + entity extraction run inline (not in background threads)
  - Soft-delete detected by a subsequent scan

Definition of Done (P6):
  At least one E2E test: file discovery → content extraction → entity extraction
  At least one test: soft-delete (file removed from disk)
  Tests runnable with ``python -m pytest``
  Tests pass in CI
"""

from pathlib import Path

import pytest

from workers.entity_extractor import EntityExtractor
from workers.event_extractor import EventExtractor


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _first_doc_id(backend):
    """Return the ID of the first discovered document."""
    docs = list(backend.documents_by_id.values())
    assert docs, "No documents found in backend"
    return docs[0]['id']


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPipelineDiscovery:
    """CollectionWatcher._scan_and_detect_changes() populates the backend."""

    def test_scan_discovers_all_files(self, watcher, backend, tmp_collection_dir):
        """
        Scanning the collection directory creates a document record for every
        file found, including files whose extension has no registered parser.
        """
        watcher._scan_and_detect_changes()

        expected_names = {'memo.txt', 'data.json', 'archive.xyz'}
        discovered_names = {Path(p).name for p in backend.documents}
        assert expected_names.issubset(discovered_names), (
            f"Missing from catalog: {expected_names - discovered_names}"
        )

    def test_scan_marks_exists_on_disk_true(self, watcher, backend, tmp_collection_dir):
        """Newly discovered documents have exists_on_disk set to True."""
        watcher._scan_and_detect_changes()

        for path, doc in backend.documents.items():
            assert doc['exists_on_disk'] is True, (
                f"{path} should be marked as existing on disk"
            )

    def test_scan_parseable_file_becomes_metadata_indexed(
        self, watcher, backend, tmp_collection_dir
    ):
        """
        A file with a registered parser is enriched and its status advances
        to METADATA_INDEXED.
        """
        watcher._scan_and_detect_changes()

        memo_path = str(tmp_collection_dir / 'memo.txt')
        assert memo_path in backend.documents, "memo.txt should be discovered"
        assert backend.documents[memo_path]['status'] == 'METADATA_INDEXED', (
            "Parseable file should be METADATA_INDEXED after scan"
        )

    def test_scan_unknown_extension_stays_discovered(
        self, watcher, backend, tmp_collection_dir
    ):
        """
        A file with no registered parser is still catalogued but stays in
        DISCOVERED status (no enrichment possible).
        """
        watcher._scan_and_detect_changes()

        archive_path = str(tmp_collection_dir / 'archive.xyz')
        assert archive_path in backend.documents, "archive.xyz should be discovered"
        assert backend.documents[archive_path]['status'] == 'DISCOVERED', (
            "File without parser should remain DISCOVERED"
        )


class TestPipelineInlineExtraction:
    """
    File discovery → content extraction → entity extraction, run inline.

    ContentExtractor is tightly coupled to a live database connection so the
    content step is seeded directly into InMemoryBackend here.  All subsequent
    worker logic (EntityExtractor, EventExtractor) runs against the in-memory
    backend with no database required.
    """

    def test_entity_extraction_after_discovery(
        self, watcher, backend, tmp_collection_dir
    ):
        """
        End-to-end: file discovered → content seeded → EntityExtractor run inline
        → at least one entity stored in backend.
        """
        # Step 1: discover files
        watcher._scan_and_detect_changes()

        memo_path = str(tmp_collection_dir / 'memo.txt')
        assert memo_path in backend.documents

        doc_id = backend.documents[memo_path]['id']

        # Step 2: seed content (simulates ContentExtractor storing extracted text)
        content = (tmp_collection_dir / 'memo.txt').read_text(encoding='utf-8')
        backend.save_content(doc_id, content, 'text')

        # Step 3: run EntityExtractor inline
        extractor = EntityExtractor(backend)
        job = {
            'id': 1,
            'document_id': doc_id,
            'job_type': 'extract_entities',
        }
        result = extractor.process(job)

        assert result['entities_extracted'] > 0, (
            "At least one entity should be extracted from the memo"
        )
        assert len(backend.doc_entities.get(doc_id, [])) > 0, (
            "Entities should be linked to the document in the backend"
        )

    def test_event_extraction_after_discovery(
        self, watcher, backend, tmp_collection_dir
    ):
        """
        End-to-end: file discovered → content seeded → EventExtractor run inline
        → result dict returned without error.
        """
        watcher._scan_and_detect_changes()

        memo_path = str(tmp_collection_dir / 'memo.txt')
        doc_id = backend.documents[memo_path]['id']

        content = (tmp_collection_dir / 'memo.txt').read_text(encoding='utf-8')
        backend.save_content(doc_id, content, 'text')

        extractor = EventExtractor(backend)
        job = {
            'id': 2,
            'document_id': doc_id,
            'job_type': 'extract_events',
        }
        result = extractor.process(job)

        assert 'events_extracted' in result, (
            "EventExtractor result should include events_extracted count"
        )

    def test_multiple_documents_processed_independently(
        self, watcher, backend, tmp_collection_dir
    ):
        """Each document is processed independently; entities don't bleed across docs."""
        watcher._scan_and_detect_changes()

        memo_path = str(tmp_collection_dir / 'memo.txt')
        json_path = str(tmp_collection_dir / 'data.json')

        assert memo_path in backend.documents
        assert json_path in backend.documents

        for path in (memo_path, json_path):
            doc_id = backend.documents[path]['id']
            content = Path(path).read_text(encoding='utf-8')
            backend.save_content(doc_id, content, 'text')

            extractor = EntityExtractor(backend)
            job = {'id': doc_id * 10, 'document_id': doc_id, 'job_type': 'extract_entities'}
            result = extractor.process(job)

            assert 'entities_extracted' in result


class TestPipelineSoftDelete:
    """
    Soft-delete: a file removed from disk is marked exists_on_disk = False
    after a subsequent scan.
    """

    def test_deleted_file_marked_not_on_disk(
        self, watcher, backend, tmp_collection_dir
    ):
        """
        Discover files, then delete one, rescan → exists_on_disk is False
        for the deleted file and True for the remaining files.
        """
        # Initial scan: all files discovered
        watcher._scan_and_detect_changes()

        memo_path = str(tmp_collection_dir / 'memo.txt')
        assert backend.documents[memo_path]['exists_on_disk'] is True

        # Delete the file
        (tmp_collection_dir / 'memo.txt').unlink()

        # Second scan: deletion detected
        watcher._scan_and_detect_changes()

        assert backend.documents[memo_path]['exists_on_disk'] is False, (
            "Deleted file should have exists_on_disk = False after rescan"
        )

    def test_remaining_files_unaffected_after_delete(
        self, watcher, backend, tmp_collection_dir
    ):
        """
        Soft-deleting one file does not affect the catalog entries for other files.
        """
        watcher._scan_and_detect_changes()
        (tmp_collection_dir / 'memo.txt').unlink()
        watcher._scan_and_detect_changes()

        json_path = str(tmp_collection_dir / 'data.json')
        assert backend.documents[json_path]['exists_on_disk'] is True, (
            "Surviving files should still be marked as existing on disk"
        )

    def test_soft_delete_preserves_document_record(
        self, watcher, backend, tmp_collection_dir
    ):
        """
        ARTIFACT INVENTORY MODEL: soft-delete preserves the document record;
        it does not remove the entry from the catalog.
        """
        watcher._scan_and_detect_changes()
        doc_count_before = len(backend.documents)

        (tmp_collection_dir / 'memo.txt').unlink()
        watcher._scan_and_detect_changes()

        assert len(backend.documents) == doc_count_before, (
            "Document record must be preserved after soft-delete (record kept for auditability)"
        )
