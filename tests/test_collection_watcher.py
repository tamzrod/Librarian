"""
Test collection watcher functionality.
"""
import os
import sys
import time
import tempfile
import threading
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.collection_watcher import CollectionWatcher, watch_collection


class MockBackend:
    """Mock backend for testing."""
    
    def __init__(self):
        self.documents = {}
        self.events = []
    
    def save_document(self, document):
        doc_id = len(self.documents) + 1
        self.documents[document['path']] = {'id': doc_id, **document}
        print(f"  [Backend] Saved document: {document['path']}")
        return doc_id
    
    def save_entities(self, doc_id, entities):
        print(f"  [Backend] Saved {len(entities)} entities for doc {doc_id}")
    
    def save_events(self, doc_id, events):
        print(f"  [Backend] Saved {len(events)} events for doc {doc_id}")
    
    def save_locations(self, doc_id, locations):
        print(f"  [Backend] Saved {len(locations)} locations for doc {doc_id}")
    
    def mark_deleted(self, filepath):
        if filepath in self.documents:
            del self.documents[filepath]
            print(f"  [Backend] Marked as deleted: {filepath}")


class MockParserRegistry:
    """Mock parser registry for testing."""
    
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
        return {'text': text}


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
        
        # Test 4: Delete file
        print("\n--- STEP 5: Delete file ---")
        test_file.unlink()
        time.sleep(1)
        
        # Stop watcher
        print("\n--- STEP 6: Stop watching ---")
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
    test_collection_watcher()
    test_polling_fallback()
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)