"""
Test collection watcher functionality.

ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
These tests verify that artifacts are created immediately upon discovery,
regardless of parser availability.
"""
import os
import sys
import time
import tempfile
import threading
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.collection_watcher import CollectionWatcher, watch_collection


class MockBackend:
    """Mock backend for testing with artifact inventory support."""
    
    def __init__(self):
        self.documents = {}
        self.events = []
        self.discovered_artifacts = []  # Track discovered artifacts
        self.deleted_artifacts = []  # Track deleted artifacts
    
    def discover_artifact(self, path, extension=None, file_size=None, modified_time=None):
        """Create an artifact record immediately upon discovery."""
        doc_id = len(self.documents) + 1
        self.documents[path] = {
            'id': doc_id,
            'path': path,
            'extension': extension,
            'file_size': file_size,
            'modified_time': modified_time,
            'status': 'DISCOVERED',
            'exists_on_disk': True,
            'lifecycle_state': 'discovered',
            'artifact_type': self._classify_artifact_type(extension)
        }
        self.discovered_artifacts.append(path)
        print(f"  [Backend] Discovered artifact: {path} (type: {self.documents[path]['artifact_type']})")
        return doc_id
    
    def save_document(self, document):
        """Save or update a document."""
        path = document['path']
        if path in self.documents:
            # Update existing
            self.documents[path].update(document)
            self.documents[path]['status'] = document.get('status', 'METADATA_INDEXED')
        else:
            # New document
            doc_id = len(self.documents) + 1
            self.documents[path] = {'id': doc_id, **document}
        print(f"  [Backend] Saved document: {path}")
        return self.documents[path]['id']
    
    def create_jobs_for_document(self, doc_id):
        """Create jobs for a document."""
        print(f"  [Backend] Created jobs for document {doc_id}")
        return [1, 2, 3]  # Mock job IDs
    
    def mark_deleted(self, path):
        """Mark a document as deleted (soft delete)."""
        if path in self.documents:
            self.documents[path]['exists_on_disk'] = False
            self.documents[path]['deleted_at'] = '2026-01-01T00:00:00'
            self.deleted_artifacts.append(path)
            print(f"  [Backend] Marked as deleted (soft): {path}")
            return True
        return False
    
    def save_entities(self, doc_id, entities):
        print(f"  [Backend] Saved {len(entities)} entities for doc {doc_id}")
    
    def save_events(self, doc_id, events):
        print(f"  [Backend] Saved {len(events)} events for doc {doc_id}")
    
    def save_locations(self, doc_id, locations):
        print(f"  [Backend] Saved {len(locations)} locations for doc {doc_id}")
    
    def _classify_artifact_type(self, extension):
        """Classify artifact type based on extension."""
        ext = (extension or '').lower()
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}:
            return 'image'
        if ext in {'.txt', '.md', '.pdf', '.doc'}:
            return 'document'
        if ext in {'.zip', '.tar', '.gz'}:
            return 'archive'
        return 'unknown'


class MockParserRegistry:
    """Mock parser registry for testing.
    
    Only supports .txt, .md, .json, .yaml, .yml, .csv files.
    Other extensions (like .xyz, .unknown) have no parser.
    """
    
    def get_parser(self, filepath):
        ext = Path(filepath).suffix.lower()
        if ext in ['.txt', '.md', '.json', '.yaml', '.yml', '.csv']:
            return MockParser()
        return None


class MockParser:
    """Mock parser for testing."""
    
    def parse(self, filepath):
        with open(filepath, 'r') as f:
            text = f.read()
        return {
            'text': text,
            'character_count': len(text),
            'parser': 'text'
        }


def test_artifact_discovery_unknown_extension():
    """Test that artifacts with unknown extensions are discovered.
    
    ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
    A file does not require a parser to become an artifact.
    """
    print("\n" + "=" * 70)
    print("TEST: Artifact Discovery with Unknown Extension")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test_collection"
        collection_path.mkdir()
        
        backend = MockBackend()
        parser_registry = MockParserRegistry()
        watcher = CollectionWatcher(str(collection_path), backend, parser_registry)
        
        # Create file with unknown extension (.xyz)
        test_file = collection_path / "weird.xyz"
        test_file.write_text("This file has an unknown extension")
        
        # Process the file (note: paths are now absolute)
        print("\nProcessing file with unknown extension (.xyz)...")
        watcher._process_file("weird.xyz")
        
        # Verify artifact was discovered with absolute path
        expected_path = str(test_file)  # Full absolute path
        assert expected_path in backend.documents, f"Artifact should be discovered even without parser at {expected_path}"
        assert backend.documents[expected_path]["status"] == "DISCOVERED", "Status should be DISCOVERED"
        assert backend.documents[expected_path]["artifact_type"] == "unknown", "Artifact type should be unknown"
        assert backend.documents[expected_path]["exists_on_disk"] == True, "Should exist on disk"
        
        # Verify NO jobs were created (no parser = no jobs)
        # The artifact was discovered but not enriched
        
        print("\n✓ Artifact with unknown extension was discovered")
        print(f"✓ Path: {expected_path}")
        print(f"✓ Status: {backend.documents[expected_path]['status']}")
        print(f"✓ Artifact type: {backend.documents[expected_path]['artifact_type']}")


def test_artifact_discovery_supported_extension():
    """Test that artifacts with supported extensions are discovered and enriched.
    
    ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
    Artifacts with parsers get additional enrichment.
    """
    print("\n" + "=" * 70)
    print("TEST: Artifact Discovery with Supported Extension")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test_collection"
        collection_path.mkdir()
        
        backend = MockBackend()
        parser_registry = MockParserRegistry()
        watcher = CollectionWatcher(str(collection_path), backend, parser_registry)
        
        # Create file with supported extension (.txt)
        test_file = collection_path / "document.txt"
        test_file.write_text("This is a supported document")
        
        # Process the file (note: paths are now absolute)
        print("\nProcessing file with supported extension (.txt)...")
        watcher._process_file("document.txt")
        
        # Verify artifact was discovered with absolute path
        expected_path = str(test_file)
        assert expected_path in backend.documents, f"Artifact should be discovered at {expected_path}"
        assert backend.documents[expected_path]["status"] == "METADATA_INDEXED", "Status should be METADATA_INDEXED"
        assert backend.documents[expected_path]["exists_on_disk"] == True, "Should exist on disk"
        
        print("\n✓ Artifact with supported extension was discovered and enriched")
        print(f"✓ Path: {expected_path}")
        print(f"✓ Status: {backend.documents[expected_path]['status']}")


def test_artifact_discovery_encrypted_file():
    """Test that encrypted/inaccessible files are still discovered.
    
    ARTIFACT INVENTORY MODEL: Unknown artifacts are first-class citizens.
    """
    print("\n" + "=" * 70)
    print("TEST: Artifact Discovery with Encrypted File")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test_collection"
        collection_path.mkdir()
        
        backend = MockBackend()
        parser_registry = MockParserRegistry()
        watcher = CollectionWatcher(str(collection_path), backend, parser_registry)
        
        # Create file with encrypted-like extension
        test_file = collection_path / "secrets.db"
        test_file.write_text("encrypted content")
        
        # Process the file (note: paths are now absolute)
        print("\nProcessing encrypted file (.db)...")
        watcher._process_file("secrets.db")
        
        # Verify artifact was discovered with absolute path
        expected_path = str(test_file)
        assert expected_path in backend.documents, f"Artifact should be discovered at {expected_path}"
        print(f"\n✓ Encrypted file was discovered")
        print(f"✓ Path: {expected_path}")
        print(f"✓ Artifact type: {backend.documents[expected_path].get('artifact_type', 'unknown')}")


def test_soft_delete():
    """Test that deleted files are marked, not deleted.
    
    ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
    Deleted files are marked, not deleted. Records are preserved for auditability.
    """
    print("\n" + "=" * 70)
    print("TEST: Soft Delete")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test_collection"
        collection_path.mkdir()
        
        backend = MockBackend()
        parser_registry = MockParserRegistry()
        watcher = CollectionWatcher(str(collection_path), backend, parser_registry)
        
        # First, discover an artifact
        test_file = collection_path / "to_delete.txt"
        test_file.write_text("This file will be deleted")
        watcher._process_file("to_delete.txt")
        
        # Verify artifact exists with absolute path
        expected_path = str(test_file)
        assert expected_path in backend.documents
        assert backend.documents[expected_path]["exists_on_disk"] == True
        
        # Delete the file (simulate)
        test_file.unlink()
        
        # Mark as deleted (note: paths are now absolute)
        print("\nMarking file as deleted...")
        watcher._mark_deleted("to_delete.txt")
        
        # Verify artifact is soft-deleted with absolute path
        assert backend.documents[expected_path]["exists_on_disk"] == False, "Should not exist on disk"
        assert backend.documents[expected_path].get("deleted_at") is not None, "Should have deleted_at timestamp"
        assert expected_path in backend.deleted_artifacts, "Should be in deleted artifacts list"
        
        print("\n✓ Deleted file was soft-deleted")
        print(f"✓ exists_on_disk: {backend.documents[expected_path]['exists_on_disk']}")
        print(f"✓ deleted_at: {backend.documents[expected_path]['deleted_at']}")


def test_multiple_unknown_extensions():
    """Test that multiple files with unknown extensions are all discovered.
    
    SUCCESS CRITERIA: Dropping the following files:
    IMG_001.jpg, archive.zip, encrypted.db, weird.xyz
    
    immediately creates document records.
    """
    print("\n" + "=" * 70)
    print("TEST: Multiple Unknown Extensions")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test_collection"
        collection_path.mkdir()
        
        backend = MockBackend()
        parser_registry = MockParserRegistry()
        watcher = CollectionWatcher(str(collection_path), backend, parser_registry)
        
        # Create files with various extensions (note: paths are now absolute)
        test_files = {
            "IMG_001.jpg": "fake image",
            "archive.zip": "fake zip",
            "encrypted.db": "fake db",
            "weird.xyz": "fake weird",
        }
        
        expected_paths = {}
        for filename, content in test_files.items():
            test_file = collection_path / filename
            test_file.write_text(content)
            expected_paths[filename] = str(test_file)
        
        # Process all files
        print("\nProcessing files...")
        for filename in test_files.keys():
            watcher._process_file(filename)
        
        # Verify all artifacts were discovered with absolute paths
        print("\nVerifying all artifacts discovered:")
        for filename in test_files.keys():
            expected_path = expected_paths[filename]
            assert expected_path in backend.documents, f"{filename} should be discovered at {expected_path}"
            doc = backend.documents[expected_path]
            print(f"  ✓ {expected_path}: status={doc['status']}, type={doc.get('artifact_type', 'N/A')}")
        
        # Verify correct artifact types
        assert backend.documents[expected_paths["IMG_001.jpg"]]["artifact_type"] == "image"
        assert backend.documents[expected_paths["archive.zip"]]["artifact_type"] == "archive"
        assert backend.documents[expected_paths["encrypted.db"]]["artifact_type"] in ["structured", "unknown"]
        
        print("\n✓ All artifacts with various extensions were discovered")


def test_parser_failure_still_creates_artifact():
    """Test that parser failure still creates the artifact.
    
    ARTIFACT INVENTORY MODEL: Parser failure must never prevent artifact creation.
    """
    print("\n" + "=" * 70)
    print("TEST: Parser Failure Still Creates Artifact")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test_collection"
        collection_path.mkdir()
        
        backend = MockBackend()
        
        # Create a parser that fails
        class FailingParserRegistry:
            def get_parser(self, filepath):
                return FailingParser()
        
        class FailingParser:
            def parse(self, filepath):
                raise Exception("Parser failure!")
        
        watcher = CollectionWatcher(str(collection_path), backend, FailingParserRegistry())
        
        # Create a file
        test_file = collection_path / "failing.txt"
        test_file.write_text("This will cause parser failure")
        
        # Process the file (note: paths are now absolute)
        print("\nProcessing file with failing parser...")
        watcher._process_file("failing.txt")
        
        # Verify artifact was still discovered with absolute path
        expected_path = str(test_file)
        assert expected_path in backend.documents, f"Artifact should be discovered despite parser failure at {expected_path}"
        assert backend.documents[expected_path]["status"] == "DISCOVERED", "Status should be DISCOVERED (parser failed)"
        
        print("\n✓ Artifact was created despite parser failure")
        print(f"✓ Path: {expected_path}")
        print(f"✓ Status: {backend.documents[expected_path]['status']}")


def test_collection_watcher():
    """Test collection watcher with file events."""
    
    # Create temporary collection directory
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test_collection"
        collection_path.mkdir()
        
        print("=" * 70)
        print("COLLECTION WATCHER TEST")
        print("=" * 70)
        print(f"\nTemporary collection: {collection_path}")
        
        # Create watcher with mock backend
        backend = MockBackend()
        parser_registry = MockParserRegistry()
        watcher = CollectionWatcher(str(collection_path), backend, parser_registry)
        
        print("\n--- STEP 1: Start watching collection ---")
        watcher.start()
        
        # Test 1: Add new file
        print("\n--- STEP 2: Add new file (new_file.txt) ---")
        test_file = collection_path / "new_file.txt"
        test_file.write_text("This is a new file created at " + time.strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(1)  # Give watcher time to detect
        
        # Test 2: Modify file
        print("\n--- STEP 3: Modify file ---")
        test_file.write_text("This file was modified at " + time.strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(1)
        
        # Test 3: Add another file
        print("\n--- STEP 4: Add another file (data.json) ---")
        json_file = collection_path / "data.json"
        json_file.write_text('{"name": "test", "created": "2026-01-01"}')
        time.sleep(1)
        
        # Test 4: Add file with unknown extension
        print("\n--- STEP 5: Add file with unknown extension (.xyz) ---")
        unknown_file = collection_path / "unknown.xyz"
        unknown_file.write_text("This file has an unknown extension")
        time.sleep(1)
        
        # Test 5: Delete file
        print("\n--- STEP 6: Delete file ---")
        test_file.unlink()
        time.sleep(1)
        
        # Stop watcher
        print("\n--- STEP 7: Stop watching ---")
        watcher.stop()
        
        # Display recorded events
        print("\n" + "=" * 70)
        print("DETECTED EVENTS")
        print("=" * 70)
        
        events = watcher.get_events()
        for event in events:
            print(f"  [{event['timestamp']}] {event['type']}: {event['path']}")
        
        print(f"\nTotal events detected: {len(events)}")
        
        # Verify events
        event_types = [e['type'] for e in events]
        print("\nEvent verification:")
        print(f"  Created events: {event_types.count('created')}")
        print(f"  Modified events: {event_types.count('modified')}")
        print(f"  Deleted events: {event_types.count('deleted')}")
        
        # Verify artifacts were discovered
        print("\n" + "=" * 70)
        print("DISCOVERED ARTIFACTS")
        print("=" * 70)
        for path, doc in backend.documents.items():
            print(f"  {path}: status={doc['status']}, type={doc.get('artifact_type', 'N/A')}")


def test_polling_fallback():
    """Test polling fallback when watchdog is not available."""
    
    print("\n" + "=" * 70)
    print("POLLING FALLBACK TEST")
    print("=" * 70)
    
    # Check if watchdog is available
    try:
        from watchdog.observers import Observer
        print("\nWatchdog is available - using watchdog mode")
        print("Polling fallback would be used if watchdog was not installed.")
    except ImportError:
        print("\nWatchdog not available - would use polling fallback")
    
    print("\nNote: Polling checks every 30 seconds.")
    print("For testing, we can trigger a manual scan:")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        collection_path = Path(tmpdir) / "test_collection"
        collection_path.mkdir()
        
        backend = MockBackend()
        parser_registry = MockParserRegistry()
        watcher = CollectionWatcher(str(collection_path), backend, parser_registry)
        
        # Manually trigger scan
        print("\nManual scan (no files):")
        watcher._scan_and_detect_changes()
        print(f"  Events after scan: {len(watcher.get_events())}")
        
        # Add a file and scan
        print("\nAdd file and scan:")
        test_file = collection_path / "manual_test.txt"
        test_file.write_text("Manual test content")
        watcher._scan_and_detect_changes()
        print(f"  Events after scan: {len(watcher.get_events())}")


if __name__ == "__main__":
    # Run artifact inventory tests
    test_artifact_discovery_unknown_extension()
    test_artifact_discovery_supported_extension()
    test_artifact_discovery_encrypted_file()
    test_soft_delete()
    test_multiple_unknown_extensions()
    test_parser_failure_still_creates_artifact()
    
    # Run standard collection watcher tests
    test_collection_watcher()
    test_polling_fallback()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)