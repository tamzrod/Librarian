"""
Abstract base class for all worker job handlers.

P5: Establishes the common interface that all extractor classes must implement,
replacing fragile per-class method-name conventions with a single .process(job)
entry point.
"""

from abc import ABC, abstractmethod


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
