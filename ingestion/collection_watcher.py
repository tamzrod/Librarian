import os
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
    """Monitor a collection directory for file changes."""
    
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
        """Process a new or modified file."""
        full_path = self.path / filepath
        
        # Detect parser
        parser = self.parser_registry.get_parser(full_path)
        if not parser:
            print(f"[CollectionWatcher] No parser for {filepath}")
            return
        
        try:
            # Parse file
            parsed = parser.parse(full_path)
            if not parsed:
                print(f"[CollectionWatcher] Parser returned None for {filepath}")
                return
            
            print(f"[CollectionWatcher] Parsed {filepath}: {parsed.get('character_count', 0)} chars")
            
            # Build document metadata
            document = {
                'path': str(filepath),
                'extension': full_path.suffix,
                'modified_time': datetime.fromtimestamp(os.path.getmtime(full_path)),
                'file_size': os.path.getsize(full_path),
                'character_count': parsed.get('character_count'),
                'parser': parsed.get('parser', full_path.suffix[1:] if full_path.suffix else 'text')
            }
            
            # Save to backend immediately (fast operation)
            if hasattr(self.backend, 'save_document'):
                doc_id = self.backend.save_document(document)
                print(f"[CollectionWatcher] Saved document {filepath} -> id:{doc_id}")
                
                # Create processing jobs (fast operation)
                if hasattr(self.backend, 'create_jobs_for_document'):
                    job_ids = self.backend.create_jobs_for_document(doc_id)
                    print(f"[CollectionWatcher] Created {len(job_ids)} jobs for document {doc_id}")
            else:
                print(f"[CollectionWatcher] Backend has no save_document method: {type(self.backend)}")
                    
        except Exception as e:
            print(f"[CollectionWatcher] Error processing {filepath}: {e}")
    
    def _mark_deleted(self, filepath):
        """Mark a deleted file in the database."""
        if hasattr(self.backend, 'mark_deleted'):
            self.backend.mark_deleted(filepath)
    
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