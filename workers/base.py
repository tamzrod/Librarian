"""
Abstract base class for all worker job handlers.

P5: Establishes the common interface that all extractor classes must implement,
replacing fragile per-class method-name conventions with a single .process(job)
entry point.

Operation Plugin Foundation: Added provenance support via get_provenance() method.
Every worker can now include identity (plugin_name, engine_name, plugin_version)
in its observations.
"""

from abc import ABC, abstractmethod
from typing import Protocol, Callable, Any, Optional
from datetime import datetime


class BaseWorker(ABC):
    """
    Abstract base class for worker job handlers.

    All extractor classes must inherit from BaseWorker and implement
    the process() method as their job-handler entry point.
    
    Operation Plugin Foundation: Added class-level identity fields and
    get_provenance() method for provenance tracking.
    """
    
    # Class-level identity (set by subclasses)
    # Operation Plugin Foundation: Required for provenance tracking
    PLUGIN_NAME: str = None      # e.g., "metadata.exif.pillow"
    ENGINE_NAME: str = None     # e.g., "pillow-exif"
    PLUGIN_VERSION: str = None # e.g., "1.0.0"
    
    def __init__(self, backend):
        """Initialize the worker with a backend."""
        self.backend = backend
    
    def get_provenance(self, document_id: int) -> dict:
        """
        Build provenance dictionary for an observation.
        
        Operation Plugin Foundation: Provides consistent provenance tracking
        across all workers.
        
        Args:
            document_id: ID of the document being processed
            
        Returns:
            Dict containing provenance information:
            {
                'plugin_name': str,     # e.g., "metadata.exif.pillow"
                'engine_name': str,     # e.g., "pillow-exif"
                'plugin_version': str,   # e.g., "1.0.0"
                'processed_at': str,    # ISO 8601 timestamp
                'artifact_hash': str,    # SHA256 of source artifact
            }
        """
        # Get artifact hash from document
        artifact_hash = None
        if self.backend and hasattr(self.backend, 'get_artifact_hash'):
            artifact_hash = self.backend.get_artifact_hash(document_id)
        
        return {
            'plugin_name': self.PLUGIN_NAME or 'unknown',
            'engine_name': self.ENGINE_NAME or 'unknown',
            'plugin_version': self.PLUGIN_VERSION or '1.0.0',
            'processed_at': datetime.utcnow().isoformat(),
            'artifact_hash': artifact_hash,
        }

    @abstractmethod
    def process(self, job: dict) -> dict:
        """
        Process a single job.

        Args:
            job: Job dict containing at least 'id', 'job_type', and 'document_id'.

        Returns:
            Dict with job processing results.
        """


class WorkerRuntime(Protocol):
    """
    Protocol defining the canonical worker runtime interface.
    
    P2: This protocol unifies the worker runtime implementations. All worker
    runtimes must implement these methods to ensure consistent job processing
    across the application.
    """
    
    def register_handler(self, job_type: str, handler: Callable[[dict], Any]) -> None:
        """Register a handler for a job type."""
        ...
    
    def start(self) -> None:
        """Start the worker runtime."""
        ...
    
    def stop(self) -> None:
        """Stop the worker runtime gracefully."""
        ...
    
    def get_stats(self) -> dict:
        """Get worker runtime statistics."""
        ...
