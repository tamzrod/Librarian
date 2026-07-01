"""
Abstract base class for all worker job handlers.

P5: Establishes the common interface that all extractor classes must implement,
replacing fragile per-class method-name conventions with a single .process(job)
entry point.
"""

from abc import ABC, abstractmethod
from typing import Protocol, Callable, Any, Optional


class BaseWorker(ABC):
    """
    Abstract base class for worker job handlers.

    All extractor classes must inherit from BaseWorker and implement
    the process() method as their job-handler entry point.
    """

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
