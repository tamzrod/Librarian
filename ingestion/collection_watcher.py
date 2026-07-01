import os
import hashlib
import time
import threading
from pathlib import Path
from datetime import datetime


try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class CollectionWatcher:
    """Monitor a collection directory for file changes.
    
    ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
    
    This watcher creates artifact records immediately upon file discovery,
    without requiring a parser. Parser availability does not affect existence.
    
    Flow:
        1. File detected
        2. Artifact record created immediately (discover_artifact)
        3. Parser lookup attempted
        4. If parser exists: create jobs for enrichment
        5. If parser doesn't exist: artifact remains in discovered state
    """
    
    def __init__(self, path, backend, parser_registry):
        self.path = Path(path)
        self.backend = backend
        self.parser_registry = parser_registry
        self._observer = None
        self._running = False
        self._polling_thread = None
        self._last_scan = {}
        self._events = []
    
    def start(self):
        """Start watching the collection."""
        if not self.path.exists():
            raise ValueError(f"Path does not exist: {self.path}")
        
        self._running = True
        
        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        else:
            self._start_polling()
    
    def stop(self):
        """Stop watching the collection."""
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join()
        if self._polling_thread:
            self._polling_thread.join()
    
    def _start_watchdog(self):
        """Use watchdog library for file monitoring."""
        handler = CollectionEventHandler(self)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.path), recursive=True)
        self._observer.start()
    
    def _start_polling(self):
        """Fallback: poll filesystem every 30 seconds."""
        def poll():
            while self._running:
                self._scan_and_detect_changes()
                time.sleep(30)
        
        self._polling_thread = threading.Thread(target=poll, daemon=True)
        self._polling_thread.start()
    
    def _scan_and_detect_changes(self):
        """Scan filesystem and detect changes (for polling fallback)."""
        current_files = {}
        
        for root, dirs, files in os.walk(self.path):
            for filename in files:
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(self.path)
                try:
                    stat = filepath.stat()
                    current_files[str(rel_path)] = {
                        'mtime': stat.st_mtime,
                        'size': stat.st_size
                    }
                except OSError:
                    pass
        
        # Detect new and modified files
        for path_str, info in current_files.items():
            if path_str not in self._last_scan:
                self._handle_event('created', path_str)
            elif self._last_scan[path_str]['mtime'] != info['mtime']:
                self._handle_event('modified', path_str)
        
        # Detect deleted files
        for path_str in self._last_scan:
            if path_str not in current_files:
                self._handle_event('deleted', path_str)
        
        self._last_scan = current_files
    
    def _handle_event(self, event_type, filepath):
        """Handle a file system event."""
        event = {
            'type': event_type,
            'path': filepath,
            'timestamp': datetime.now().isoformat()
        }
        self._events.append(event)
        print(f"[CollectionWatcher] {event_type}: {filepath}")
        
        if event_type in ('created', 'modified'):
            self._process_file(filepath)
        elif event_type == 'deleted':
            self._mark_deleted(filepath)
    
    def _process_file(self, filepath):
        """Process a new or modified file.
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        
        This method creates an artifact record immediately, without requiring a parser.
        Parser availability does not affect artifact existence.
        
        Flow:
        1. Create artifact record immediately (discover_artifact)
        2. Attempt parser lookup
        3. If parser exists: build full document and update, create jobs
        4. If parser doesn't exist: artifact remains in discovered state
        """
        full_path = self.path / filepath
        
        # Build the artifact path with library root prefix
        # self.path is the library root (e.g., /library)
        # filepath is relative to library root (e.g., documents/sample.txt)
        # artifact_path must be absolute (e.g., /library/documents/sample.txt)
        # This ensures paths match what Explorer expects
        artifact_path = str(full_path)
        
        # Step 1: Discover artifact immediately (no parser required)
        # ARTIFACT INVENTORY MODEL: Discovery precedes understanding
        try:
            stat = full_path.stat()
            doc_id = None
            
            if hasattr(self.backend, 'discover_artifact'):
                # Use new discover_artifact method for immediate creation
                doc_id = self.backend.discover_artifact(
                    path=artifact_path,
                    extension=full_path.suffix,
                    file_size=stat.st_size,
                    modified_time=datetime.fromtimestamp(stat.st_mtime)
                )
                print(f"[CollectionWatcher] Discovered artifact {artifact_path} -> id:{doc_id}")
            elif hasattr(self.backend, 'save_document'):
                # Fallback to save_document for backends without discover_artifact
                document = {
                    'path': artifact_path,
                    'extension': full_path.suffix,
                    'file_size': stat.st_size,
                    'modified_time': datetime.fromtimestamp(stat.st_mtime),
                    'status': 'DISCOVERED'
                }
                doc_id = self.backend.save_document(document)
                print(f"[CollectionWatcher] Discovered artifact (fallback) {artifact_path} -> id:{doc_id}")
            else:
                print(f"[CollectionWatcher] Backend has no discover_artifact or save_document method: {type(self.backend)}")
                return
            
        except Exception as e:
            print(f"[CollectionWatcher] Error discovering artifact {artifact_path}: {e}")
            return
        
        # Step 2: Attempt parser lookup (enrichment phase)
        # Parser availability does not affect existence
        parser = self.parser_registry.get_parser(full_path)
        
        if parser:
            # Parser exists - attempt enrichment
            try:
                parsed = parser.parse(full_path)
                if parsed:
                    print(f"[CollectionWatcher] Parsed {artifact_path}: {parsed.get('character_count', 0)} chars")
                    
                    # Build full document metadata
                    # Include artifact_type to ensure correct job scheduling
                    artifact_type = self.parser_registry.get_artifact_type(full_path)
                    document = {
                        'path': artifact_path,
                        'extension': full_path.suffix,
                        'modified_time': datetime.fromtimestamp(stat.st_mtime),
                        'file_size': stat.st_size,
                        'character_count': parsed.get('character_count'),
                        'parser': parsed.get('parser', full_path.suffix[1:] if full_path.suffix else 'text'),
                        'artifact_type': artifact_type,
                        'status': 'METADATA_INDEXED'
                    }
                    
                    # Update document with parsed data
                    if hasattr(self.backend, 'save_document'):
                        self.backend.save_document(document)
                        print(f"[CollectionWatcher] Updated document {artifact_path} with parsed data")
                    
                    # Create processing jobs for enrichment
                    if doc_id and hasattr(self.backend, 'create_jobs_for_document'):
                        job_ids = self.backend.create_jobs_for_document(doc_id)
                        print(f"[CollectionWatcher] Created {len(job_ids)} jobs for document {doc_id}")
                else:
                    print(f"[CollectionWatcher] Parser returned None for {artifact_path}")
                    
            except Exception as e:
                print(f"[CollectionWatcher] Error parsing {artifact_path}: {e}")
                # Parser failure does not remove artifact - it remains in discovered state
        else:
            # No parser exists - artifact remains in discovered state
            # This is expected behavior - understanding is optional
            print(f"[CollectionWatcher] No parser for {artifact_path} - artifact remains discovered")
    
    def _mark_deleted(self, filepath):
        """Mark a deleted file in the database.
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        Deleted files are marked, not deleted. Records are preserved for auditability.
        """
        full_path = self.path / filepath
        artifact_path = str(full_path)
        
        if hasattr(self.backend, 'mark_deleted'):
            self.backend.mark_deleted(artifact_path)
        elif hasattr(self.backend, 'save_document'):
            # Fallback: update exists_on_disk via save_document
            document = {
                'path': artifact_path,
                'exists_on_disk': False
            }
            try:
                self.backend.save_document(document)
            except Exception as e:
                print(f"[CollectionWatcher] Error marking deleted {artifact_path}: {e}")
    
    def scan_collection(self, collection_id=None, worker_version=None):
        """Perform an idempotent scan of the collection directory.
        
        This method scans the filesystem and creates jobs only for:
        - New artifacts not yet in the database
        - Artifacts with changed hashes
        - Artifacts requiring jobs due to worker version changes
        
        SCAN IDEMPOTENCY:
        - Uses scan_snapshots to track what has been processed
        - Same file with same hash = no duplicate jobs created
        - Worker version changes trigger reprocessing
        
        Args:
            collection_id: ID of the collection (for snapshot tracking)
            worker_version: Version of the workers (changes invalidate snapshots)
            
        Returns:
            Dict with scan statistics: {'new_jobs': int, 'skipped': int, 'errors': int}
        """
        stats = {'new_jobs': 0, 'skipped': 0, 'errors': 0}
        
        for root, dirs, files in os.walk(self.path):
            # Skip hidden and common non-library directories
            dirs[:] = [
                d for d in dirs
                if not d.startswith('.')
                and d not in {'__pycache__', '.venv', 'node_modules'}
            ]
            
            for filename in files:
                if filename.startswith('.'):
                    continue
                    
                full_path = Path(root) / filename
                artifact_path = str(full_path)
                
                try:
                    stat = full_path.stat()
                    file_hash = self._compute_file_hash(full_path)
                    
                    if not file_hash:
                        stats['errors'] += 1
                        continue
                    
                    # Check if we already have a current snapshot for this file
                    if hasattr(self.backend, 'check_scan_snapshot_exists'):
                        if self.backend.check_scan_snapshot_exists(artifact_path, file_hash, worker_version):
                            stats['skipped'] += 1
                            continue
                    
                    # Discover artifact
                    doc_id = None
                    if hasattr(self.backend, 'discover_artifact'):
                        doc_id = self.backend.discover_artifact(
                            path=artifact_path,
                            extension=full_path.suffix,
                            file_size=stat.st_size,
                            modified_time=datetime.fromtimestamp(stat.st_mtime)
                        )
                    
                    # Create scan snapshot for tracking
                    snapshot_id = None
                    if hasattr(self.backend, 'create_scan_snapshot') and collection_id:
                        artifact_type = self.parser_registry.get_artifact_type(full_path)
                        snapshot_id = self.backend.create_scan_snapshot(
                            collection_id=collection_id,
                            scan_path=artifact_path,
                            file_hash=file_hash,
                            artifact_type=artifact_type,
                            worker_version=worker_version
                        )
                    
                    # Create jobs for enrichment (only for new/processed files)
                    if doc_id and hasattr(self.backend, 'create_jobs_for_document'):
                        job_ids = self.backend.create_jobs_for_document(
                            doc_id,
                            worker_version=worker_version,
                            scan_snapshot_id=snapshot_id
                        )
                        stats['new_jobs'] += len(job_ids)
                        print(f"[CollectionWatcher] Scanned {artifact_path}: {len(job_ids)} jobs created")
                    
                except Exception as e:
                    print(f"[CollectionWatcher] Error scanning {artifact_path}: {e}")
                    stats['errors'] += 1
        
        print(f"[CollectionWatcher] Scan complete: {stats['new_jobs']} new jobs, {stats['skipped']} skipped, {stats['errors']} errors")
        return stats
    
    def _compute_file_hash(self, filepath):
        """Compute SHA256 hash of a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Hex string of SHA256 hash, or None on error
        """
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None
    
    def get_events(self):
        """Get recent events."""
        return self._events.copy()
    
    def clear_events(self):
        """Clear recorded events."""
        self._events = []


class CollectionEventHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Handle watchdog events."""
    
    def __init__(self, watcher):
        self.watcher = watcher
        super().__init__()
    
    def on_created(self, event):
        if not event.is_directory:
            rel_path = Path(event.src_path).relative_to(self.watcher.path)
            self.watcher._handle_event('created', str(rel_path))
    
    def on_modified(self, event):
        if not event.is_directory:
            rel_path = Path(event.src_path).relative_to(self.watcher.path)
            self.watcher._handle_event('modified', str(rel_path))
    
    def on_deleted(self, event):
        if not event.is_directory:
            rel_path = Path(event.src_path).relative_to(self.watcher.path)
            self.watcher._handle_event('deleted', str(rel_path))


def watch_collection(path, backend=None, parser_registry=None):
    """
    Convenience function to start watching a collection.
    
    Args:
        path: Path to the collection directory
        backend: Storage backend instance
        parser_registry: Parser registry instance
    
    Returns:
        CollectionWatcher instance
    """
    watcher = CollectionWatcher(path, backend or MockBackend(), parser_registry or MockParserRegistry())
    watcher.start()
    return watcher