"""
Background worker for processing document jobs.

Phase 3A: Implements the worker runtime that:
- Claims jobs from the queue
- Executes job handlers
- Handles lease management
- Supports retry with backoff
- Recovers from crashes via lease expiration
"""

import os
import time
import signal
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any
from environment import get_worker_id

logger = logging.getLogger(__name__)


class Worker:
    """
    Background worker that processes jobs from the queue.
    
    Worker loop:
    1. Recover any expired leases (Phase 3B)
    2. Claim a job (with lease)
    3. Execute the job handler
    4. Mark job complete or failed (with retry logic)
    5. Sleep and repeat
    
    Features:
    - Lease management: Jobs are automatically recovered after crash
    - Exponential backoff: Failed jobs retry with increasing delays
    - Graceful shutdown: Releases active leases on SIGTERM
    - Multiple job types: Pluggable job handlers
    """
    
    def __init__(
        self,
        backend,
        worker_id: str = None,
        poll_interval: float = 1.0,
        lease_seconds: int = 300,
        lease_renewal_interval: int = 60
    ):
        """
        Initialize the worker.
        
        Args:
            backend: Storage backend (PostgresBackend)
            worker_id: Unique worker ID (auto-generated if not provided)
            poll_interval: Seconds to wait when no jobs available
            lease_seconds: How long to hold a lease before it expires
            lease_renewal_interval: How often to renew leases
        """
        self.backend = backend
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.lease_seconds = lease_seconds
        self.lease_renewal_interval = lease_renewal_interval
        
        # Job handlers: job_type -> handler function
        self._handlers: Dict[str, Callable] = {}
        
        # State
        self._running = False
        self._current_job = None
        self._lease_renewal_thread = None
        self._stop_event = threading.Event()
        
        # Metrics
        self.jobs_processed = 0
        self.jobs_succeeded = 0
        self.jobs_failed = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def register_handler(self, job_type: str, handler: Callable[[dict], Any]):
        """
        Register a handler for a job type.
        
        Args:
            job_type: Type of job (e.g., 'extract_text')
            handler: Function that takes job dict and returns result
        """
        self._handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")
    
    def start(self):
        """Start the worker loop."""
        if self._running:
            logger.warning("Worker already running")
            return
        
        self._running = True
        self._stop_event.clear()
        logger.info(f"Worker {self.worker_id} starting...")
        
        while self._running:
            try:
                # Phase 3B: Recover expired leases
                recovered = self.backend.recover_expired_leases()
                if recovered > 0:
                    logger.info(f"Recovered {recovered} expired jobs")
                
                # Claim a job
                job = self.backend.claim_job(self.worker_id, self.lease_seconds)
                
                if job is None:
                    # No jobs available, wait
                    time.sleep(self.poll_interval)
                    continue
                
                # Got a job - start lease renewal thread
                self._current_job = job
                self._start_lease_renewal()
                
                # Execute job
                self._execute_job(job)
                
                # Stop lease renewal
                self._stop_lease_renewal()
                self._current_job = None
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(5)  # Back off on errors
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    def stop(self):
        """Stop the worker gracefully."""
        logger.info(f"Worker {self.worker_id} stopping...")
        self._running = False
        self._stop_event.set()
        
        # Release current job's lease
        if self._current_job:
            self.backend.release_lease(self._current_job['id'])
            logger.info(f"Released lease for job {self._current_job['id']}")
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    def _execute_job(self, job: dict):
        """Execute a single job."""
        job_id = job['id']
        job_type = job['job_type']
        document_id = job['document_id']
        
        logger.info(f"Executing job {job_id}: {job_type} for document {document_id}")
        
        handler = self._handlers.get(job_type)
        if not handler:
            error_msg = f"No handler registered for job type: {job_type}"
            logger.error(error_msg)
            self.backend.complete_job(job_id, success=False, error_message=error_msg)
            self.jobs_failed += 1
            self.jobs_processed += 1
            return
        
        try:
            # Execute the handler
            result = handler(job)
            
            # Mark job as completed
            self.backend.complete_job(job_id, success=True)
            self.jobs_succeeded += 1
            self.jobs_processed += 1
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Job {job_id} failed: {error_msg}")
            
            # Mark job as failed (will handle retry)
            self.backend.complete_job(job_id, success=False, error_message=error_msg)
            self.jobs_failed += 1
            self.jobs_processed += 1
    
    def _start_lease_renewal(self):
        """Start the lease renewal thread."""
        self._lease_renewal_thread = threading.Thread(
            target=self._lease_renewal_loop,
            daemon=True
        )
        self._lease_renewal_thread.start()
    
    def _stop_lease_renewal(self):
        """Stop the lease renewal thread."""
        self._stop_event.set()
        if self._lease_renewal_thread:
            self._lease_renewal_thread.join(timeout=5)
            self._lease_renewal_thread = None
        self._stop_event.clear()
    
    def _lease_renewal_loop(self):
        """Periodically renew the current job's lease."""
        while not self._stop_event.is_set():
            self._stop_event.wait(self.lease_renewal_interval)
            
            if self._stop_event.is_set():
                break
            
            if self._current_job:
                success = self.backend.renew_lease(
                    self._current_job['id'],
                    self.worker_id,
                    self.lease_seconds
                )
                if success:
                    logger.debug(f"Renewed lease for job {self._current_job['id']}")
                else:
                    logger.warning(f"Failed to renew lease for job {self._current_job['id']}")
                    # Job might have been completed or taken by another worker
                    break
    
    def get_stats(self) -> dict:
        """Get worker statistics."""
        return {
            'worker_id': self.worker_id,
            'running': self._running,
            'jobs_processed': self.jobs_processed,
            'jobs_succeeded': self.jobs_succeeded,
            'jobs_failed': self.jobs_failed,
            'current_job': self._current_job['id'] if self._current_job else None
        }


def run_worker(backend, worker_id: str = None):
    """
    Run a worker with the given backend.
    
    This is a convenience function that creates and runs a worker
    with all job handlers registered.
    """
    from .content_extractor import ContentExtractor
    from .entity_extractor import EntityExtractor
    from .event_extractor import EventExtractor
    from .location_extractor import LocationExtractor
    from .embedding_generator import EmbeddingGenerator
    from .photo_metadata_extractor import PhotoMetadataExtractor
    
    worker = Worker(backend, worker_id=worker_id)
    
    # Register all handlers
    worker.register_handler('extract_text', ContentExtractor(backend).extract_text)
    worker.register_handler('extract_entities', EntityExtractor(backend).extract_entities)
    worker.register_handler('extract_events', EventExtractor(backend).extract_events)
    worker.register_handler('extract_locations', LocationExtractor(backend).extract_locations)
    worker.register_handler('generate_embeddings', EmbeddingGenerator(backend).generate_embeddings)
    worker.register_handler('extract_photo_metadata', PhotoMetadataExtractor(backend).extract_photo_metadata)
    
    logger.info("Starting worker with all extraction handlers")
    worker.start()


if __name__ == '__main__':
    # Allow running worker directly for testing
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from storage.postgres_backend import PostgresBackend
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    backend = PostgresBackend()
    backend.ensure_schema()
    
    worker_id = get_worker_id()
    run_worker(backend, worker_id=worker_id)
