"""Application state management for Librarian API.

Manages global state for storage backend, ingestion engine, file watcher, and job processor.
"""

import os
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Callable, Dict, Any

from storage.backend import validate_backend_instance
from storage.postgres_backend import PostgresBackend
from ingestion.librarian import Librarian
from ingestion.collection_watcher import CollectionWatcher, WATCHDOG_AVAILABLE
from registry.parser_registry import ParserRegistry
from registry.register_parsers import registry
from environment import DEFAULT_LIBRARY_ROOT, get_database_url, get_library_root

logger = logging.getLogger(__name__)


class BackgroundJobProcessor:
    """Background processor that polls and executes queued jobs.
    
    This enables automatic job processing within the API server,
    so the pipeline works without requiring a separate worker container.
    """

    def __init__(self, backend, poll_interval: float = 1.0):
        """Initialize the job processor.
        
        Args:
            backend: Storage backend instance
            poll_interval: Seconds between job polls
        """
        self.backend = backend
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._handlers: Dict[str, Callable] = {}
        self.worker_id = f"api-processor-{os.getpid()}"
        
        # Metrics
        self.jobs_processed = 0
        self.jobs_succeeded = 0
        self.jobs_failed = 0

    def register_handler(self, job_type: str, handler: Callable[[dict], Any]):
        """Register a handler for a job type."""
        self._handlers[job_type] = handler
        logger.info(f"Registered job handler: {job_type}")

    def start(self):
        """Start the background job processor."""
        if self._running:
            logger.warning("Job processor already running")
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="JobProcessor")
        self._thread.start()
        logger.info(f"Background job processor started (worker_id={self.worker_id})")

    def stop(self):
        """Stop the background job processor."""
        if not self._running:
            return
        
        logger.info("Stopping background job processor...")
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Background job processor stopped")

    def _run_loop(self):
        """Main processing loop."""
        while not self._stop_event.is_set():
            try:
                # Recover expired leases first
                recovered = self.backend.recover_expired_leases()
                if recovered > 0:
                    logger.debug(f"Recovered {recovered} expired jobs")

                # Claim a job
                job = self.backend.claim_job(self.worker_id)
                
                if job is None:
                    # No jobs available, wait
                    self._stop_event.wait(self.poll_interval)
                    continue

                # Execute the job
                self._execute_job(job)

            except Exception as e:
                logger.error(f"Error in job processor loop: {e}")
                self._stop_event.wait(5)  # Back off on error

        logger.info("Job processor loop ended")

    def _execute_job(self, job: dict):
        """Execute a single job."""
        job_id = job['id']
        job_type = job['job_type']
        document_id = job['document_id']

        logger.info(f"Processing job {job_id}: {job_type} for document {document_id}")

        handler = self._handlers.get(job_type)
        if not handler:
            logger.warning(f"No handler for job type: {job_type}")
            self.backend.complete_job(job_id, success=False, error_message=f"No handler for {job_type}")
            self.jobs_failed += 1
            self.jobs_processed += 1
            return

        try:
            result = handler(job)
            self.backend.complete_job(job_id, success=True)
            self.jobs_succeeded += 1
            self.jobs_processed += 1
            logger.info(f"Job {job_id} completed successfully")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Job {job_id} failed: {error_msg}")
            self.backend.complete_job(job_id, success=False, error_message=error_msg)
            self.jobs_failed += 1
            self.jobs_processed += 1

    def get_stats(self) -> dict:
        """Get processor statistics."""
        return {
            'running': self._running,
            'worker_id': self.worker_id,
            'jobs_processed': self.jobs_processed,
            'jobs_succeeded': self.jobs_succeeded,
            'jobs_failed': self.jobs_failed,
            'registered_handlers': list(self._handlers.keys())
        }


class AppState:
    """Global application state for the Librarian API."""
    
    def __init__(self):
        self.backend: Optional[PostgresBackend] = None
        self.watcher: Optional[CollectionWatcher] = None
        self.librarian: Optional[Librarian] = None
        self.parser_registry: Optional[ParserRegistry] = None
        self.job_processor: Optional[BackgroundJobProcessor] = None
        self.library_root: str = get_library_root(DEFAULT_LIBRARY_ROOT)
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
    def job_processor_active(self) -> bool:
        """Check if job processor is currently active."""
        return self.job_processor is not None and self.job_processor._running
    
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
        """Initialize the PostgreSQL backend with automatic schema migration.
        
        This method initializes the database connection and runs any pending
        schema migrations automatically. If migrations fail, startup is halted
        with a clear error message.
        
        Raises:
            RuntimeError: If schema migration fails (prevents startup)
        """
        try:
            database_url = get_database_url()
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
                    validate_backend_instance(self.backend)
                    # Test connection
                    self.backend._get_connection().close()
                    self._persistence_available = True
                    logger.info(f"PostgreSQL backend initialized (host={host})")

                    # Ensure schema exists and run migrations
                    logger.info("Starting schema migration check...")
                    if self.backend.ensure_schema():
                        self._schema_ready = True
                        logger.info("Database schema verified and ready")
                    else:
                        self._schema_ready = False
                        error_msg = (
                            "SCHEMA MIGRATION FAILED: Database schema could not be initialized. "
                            "The database may be in an inconsistent state or migrations failed to apply. "
                            "Check the logs above for details about the failed migration."
                        )
                        logger.error(error_msg)
                        self.record_persistence_error(
                            "Schema initialization failed - migrations could not be applied",
                            "ensure_schema"
                        )
                        # Raise error to halt startup
                        raise RuntimeError(error_msg)

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
        except RuntimeError:
            # Re-raise RuntimeError to halt startup
            raise
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
        
        library_path = get_library_root(self.library_root)
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
                library_path = get_library_root(self.library_root)
                
                if os.path.exists(library_path):
                    self.librarian.ingest(library_path)
                    self._last_scan = datetime.utcnow()
                    logger.info(f"Initial scan complete. Indexed {len(self.librarian.index)} documents.")
                    
                    # Index documents into backend and create jobs
                    if self.backend and hasattr(self.backend, 'save_document'):
                        saved_count = 0
                        failed_count = 0
                        jobs_created = 0
                        for doc in self.librarian.index:
                            try:
                                document_id = self.backend.save_document({
                                    'path': doc.get('path'),
                                    'extension': doc.get('extension'),
                                    'sha256': doc.get('sha256_hash'),
                                    'modified_time': doc.get('modified_time'),
                                    'file_size': doc.get('file_size'),
                                    'character_count': doc.get('character_count'),
                                    'parser': doc.get('parser')
                                })
                                saved_count += 1
                                
                                # Create processing jobs for this document
                                if self.backend and hasattr(self.backend, 'create_jobs_for_document'):
                                    job_ids = self.backend.create_jobs_for_document(document_id)
                                    jobs_created += len(job_ids)
                            except Exception as e:
                                import traceback
                                tb = traceback.format_exc()
                                failed_count += 1
                                self.record_persistence_error(
                                    f"Failed to save document {doc.get('path')}: {e}\n{tb}",
                                    "save_document"
                                )
                        
                        if failed_count > 0:
                            logger.error(f"Initial scan: saved {saved_count} documents, {jobs_created} jobs created, {failed_count} failed")
                        else:
                            logger.info(f"Initial scan: all {saved_count} documents persisted, {jobs_created} jobs queued")
                else:
                    logger.warning(f"Library path does not exist for initial scan: {library_path}")
                    
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                logger.error(f"Error during initial scan: {e}")
                logger.error(f"Full traceback:\n{tb}")
                self.record_persistence_error(str(e), "initial_scan")
            finally:
                self._initial_scan_complete = True
        
        self._initial_scan_thread = threading.Thread(target=scan, daemon=True)
        self._initial_scan_thread.start()

    def start_job_processor(self):
        """Start the background job processor if backend is available."""
        if self.job_processor is not None and self.job_processor._running:
            logger.info("Job processor already running")
            return
        
        if self.backend is None or not hasattr(self.backend, 'claim_job'):
            logger.error("Cannot start job processor: backend not available")
            return
        
        # Create job processor
        self.job_processor = BackgroundJobProcessor(self.backend)
        
        # Import and register handlers from workers module
        try:
            from workers.content_extractor import ContentExtractor
            from workers.entity_extractor import EntityExtractor
            from workers.event_extractor import EventExtractor
            from workers.location_extractor import LocationExtractor
            from workers.embedding_generator import EmbeddingGenerator
            
            library_root = get_library_root(self.library_root)
            
            self.job_processor.register_handler(
                'extract_text', 
                ContentExtractor(self.backend, library_root).extract_text
            )
            self.job_processor.register_handler(
                'extract_entities',
                EntityExtractor(self.backend).extract_entities
            )
            self.job_processor.register_handler(
                'extract_events',
                EventExtractor(self.backend).extract_events
            )
            self.job_processor.register_handler(
                'extract_locations',
                LocationExtractor(self.backend).extract_locations
            )
            self.job_processor.register_handler(
                'generate_embeddings',
                EmbeddingGenerator(self.backend).generate_embeddings
            )
            
            logger.info("Registered all job handlers")
        except Exception as e:
            logger.error(f"Failed to register job handlers: {e}")
            return
        
        # Start the processor
        self.job_processor.start()
        logger.info("Background job processor started")
    
    def stop(self):
        """Stop all background services."""
        if self.job_processor is not None:
            logger.info("Stopping BackgroundJobProcessor...")
            self.job_processor.stop()
            self.job_processor = None
        
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
    state.start_job_processor()  # Start job processor for automatic pipeline
    state.run_initial_scan()
    return state


def shutdown_app():
    """Shutdown the application state."""
    global _state
    if _state is not None:
        _state.stop()
        _state = None
