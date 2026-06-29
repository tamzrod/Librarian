"""Application state management for Librarian API.

Manages global state for storage backend, ingestion engine, and file watcher.
"""

import os
import logging
import threading
from datetime import datetime
from typing import Optional

from storage.postgres_backend import PostgresBackend
from ingestion.librarian import Librarian
from ingestion.collection_watcher import CollectionWatcher, WATCHDOG_AVAILABLE
from registry.parser_registry import ParserRegistry
from registry.register_parsers import registry

logger = logging.getLogger(__name__)


class AppState:
    """Global application state for the Librarian API."""
    
    def __init__(self):
        self.backend: Optional[PostgresBackend] = None
        self.watcher: Optional[CollectionWatcher] = None
        self.librarian: Optional[Librarian] = None
        self.parser_registry: Optional[ParserRegistry] = None
        self.library_root: str = "/library"
        self._initial_scan_complete: bool = False
        self._initial_scan_thread: Optional[threading.Thread] = None
        self._last_scan: Optional[datetime] = None
        # Persistence status tracking
        self._persistence_errors: list = []
        self._persistence_available: bool = False
        self._schema_ready: bool = False
    
    @property
    def watcher_active(self) -> bool:
        """Check if watcher is currently active."""
        return self.watcher is not None and self.watcher._running
    
    @property
    def documents_indexed(self) -> int:
        """Get count of indexed documents."""
        if self.backend is None:
            return 0
        try:
            return len(self.backend.search_documents())
        except Exception:
            return 0
    
    @property
    def database_connected(self) -> bool:
        """Check if database connection is established."""
        return self.backend is not None and hasattr(self.backend, '_get_connection')
    
    @property
    def persistence_healthy(self) -> bool:
        """Check if persistence layer is fully operational."""
        return self._persistence_available and self._schema_ready
    
    @property
    def overall_status(self) -> str:
        """Get overall system status."""
        if self.persistence_healthy:
            return "healthy"
        elif self._persistence_errors:
            return "degraded"
        else:
            return "starting"
    
    def record_persistence_error(self, error: str, operation: str = "unknown"):
        """Record a persistence error for observability."""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation": operation,
            "error": str(error)
        }
        self._persistence_errors.append(error_entry)
        # Keep only last 100 errors to prevent memory issues
        if len(self._persistence_errors) > 100:
            self._persistence_errors = self._persistence_errors[-100:]
        logger.error(f"PERSISTENCE ERROR [{operation}]: {error}")
    
    def clear_persistence_errors(self):
        """Clear recorded persistence errors after successful recovery."""
        self._persistence_errors = []
        logger.info("Persistence errors cleared after successful recovery")
    
    def initialize_backend(self) -> bool:
        """Initialize the PostgreSQL backend."""
        try:
            database_url = os.environ.get("DATABASE_URL")
            if database_url:
                # Parse DATABASE_URL: postgresql://user:pass@host:port/dbname
                import re
                match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
                if match:
                    user, password, host, port, dbname = match.groups()
                    self.backend = PostgresBackend(
                        host=host,
                        port=int(port),
                        dbname=dbname,
                        user=user,
                        password=password
                    )
                    # Test connection
                    self.backend._get_connection().close()
                    self._persistence_available = True
                    logger.info(f"PostgreSQL backend initialized (host={host})")
                    
                    # Ensure schema exists
                    if self.backend.ensure_schema():
                        self._schema_ready = True
                        logger.info("Database schema verified and ready")
                    else:
                        self._schema_ready = False
                        self.record_persistence_error(
                            "Schema initialization failed - tables may not exist",
                            "ensure_schema"
                        )
                        logger.error("Database schema could not be verified. Persistence may be degraded.")
                    
                    return True
                else:
                    logger.warning(f"Could not parse DATABASE_URL: {database_url}")
                    from api.dependencies import MockBackend
                    self.backend = MockBackend()
                    self._persistence_available = False
                    self._schema_ready = False
                    return True
            else:
                logger.warning("DATABASE_URL not set, using mock backend")
                from api.dependencies import MockBackend
                self.backend = MockBackend()
                self._persistence_available = False
                self._schema_ready = False
                return True
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL backend: {e}")
            self.record_persistence_error(str(e), "initialize_backend")
            from api.dependencies import MockBackend
            self.backend = MockBackend()
            self._persistence_available = False
            self._schema_ready = False
            return True
    
    def initialize_ingestion(self):
        """Initialize the Librarian ingestion engine and parser registry."""
        self.parser_registry = registry
        self.librarian = Librarian()
        logger.info("Librarian ingestion engine initialized")
    
    def start_watcher(self):
        """Start the collection watcher if not already running."""
        if self.watcher is not None and self.watcher._running:
            logger.info("Watcher already running")
            return
        
        if self.backend is None:
            logger.error("Cannot start watcher: backend not initialized")
            return
        
        library_path = os.environ.get("LIBRARIAN_LIBRARY_ROOT", self.library_root)
        self.library_root = library_path
        
        if not os.path.exists(library_path):
            logger.warning(f"Library path does not exist: {library_path}")
            return
        
        self.watcher = CollectionWatcher(
            path=library_path,
            backend=self.backend,
            parser_registry=self.parser_registry
        )
        
        try:
            self.watcher.start()
            logger.info(f"CollectionWatcher started for: {library_path}")
        except Exception as e:
            logger.error(f"Failed to start watcher: {e}")
            self.watcher = None
    
    def run_initial_scan(self):
        """Run initial scan of the library in a background thread."""
        if self._initial_scan_complete:
            logger.info("Initial scan already complete")
            return
        
        def scan():
            try:
                logger.info("Starting initial library scan...")
                library_path = os.environ.get("LIBRARIAN_LIBRARY_ROOT", self.library_root)
                
                if os.path.exists(library_path):
                    self.librarian.ingest(library_path)
                    self._last_scan = datetime.utcnow()
                    logger.info(f"Initial scan complete. Indexed {len(self.librarian.index)} documents.")
                    
                    # Index documents into backend
                    if self.backend and hasattr(self.backend, 'save_document'):
                        saved_count = 0
                        failed_count = 0
                        for doc in self.librarian.index:
                            try:
                                self.backend.save_document({
                                    'path': doc.get('path'),
                                    'extension': doc.get('extension'),
                                    'sha256': doc.get('sha256_hash'),
                                    'modified_time': doc.get('modified_time'),
                                    'file_size': doc.get('file_size'),
                                    'character_count': doc.get('character_count'),
                                    'parser': doc.get('parser')
                                })
                                saved_count += 1
                            except Exception as e:
                                failed_count += 1
                                self.record_persistence_error(
                                    f"Failed to save document {doc.get('path')}: {e}",
                                    "save_document"
                                )
                        if failed_count > 0:
                            logger.error(f"Initial scan: saved {saved_count} documents, {failed_count} failed to persist")
                        else:
                            logger.info(f"Initial scan: all {saved_count} documents persisted successfully")
                else:
                    logger.warning(f"Library path does not exist for initial scan: {library_path}")
                    
            except Exception as e:
                logger.error(f"Error during initial scan: {e}")
                self.record_persistence_error(str(e), "initial_scan")
            finally:
                self._initial_scan_complete = True
        
        self._initial_scan_thread = threading.Thread(target=scan, daemon=True)
        self._initial_scan_thread.start()
    
    def stop(self):
        """Stop all background services."""
        if self.watcher is not None:
            logger.info("Stopping CollectionWatcher...")
            self.watcher.stop()
            self.watcher = None


# Global application state instance
_state: Optional[AppState] = None


def get_app_state() -> AppState:
    """Get the global application state instance."""
    global _state
    if _state is None:
        _state = AppState()
    return _state


def initialize_app() -> AppState:
    """Initialize the application state."""
    state = get_app_state()
    state.initialize_backend()
    state.initialize_ingestion()
    state.start_watcher()
    state.run_initial_scan()
    return state


def shutdown_app():
    """Shutdown the application state."""
    global _state
    if _state is not None:
        _state.stop()
        _state = None
