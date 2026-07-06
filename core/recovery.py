"""
Derived Artifact Recovery Framework for Librarian.

This module provides a generic framework for detecting and repairing missing
Tier 1A derived artifacts (embeddings, OCR, object detection, transcription).

TIER CLASSIFICATION:
- Tier 1A (Derived Artifacts): Expensive to generate, require recovery frameworks
  Examples: embeddings, OCR, object_detection, transcription, geolocation
- Tier 1B (Disposable Cache): Cheap to generate, no recovery needed
  Examples: thumbnails, previews - see workers/thumbnail_generator.py

ARCHITECTURE PRINCIPLES:
- Artifact is authoritative. The filesystem contains the ground truth.
- Tier 1A optional data is expensive to regenerate; recovery is a convenience.
- Metadata in the database is a cache that can be regenerated.
- Recovery never modifies healthy artifacts or creates unnecessary work.

The framework supports:
- Detection: Identifying missing, orphaned, and valid artifacts
- Recovery: Selectively repairing only affected artifacts
- Reporting: Providing detailed status of artifact health

USAGE:
    from core.recovery import get_recovery_handler

    handler = get_recovery_handler('embedding', backend)
    if handler:
        report = handler.detect()
        print(report.summary())
        if report.missing:
            handler.repair(report.missing)

NOTE: Thumbnails (Tier 1B) are NOT supported by this framework.
Use workers/thumbnail_generator.py for thumbnail handling.
"""

import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set, List, Dict, Any
from datetime import datetime
from enum import Enum

from environment import get_librarian_data_root

logger = logging.getLogger(__name__)


class ArtifactState(Enum):
    """Possible states for derived artifacts."""
    VALID = "valid"           # Metadata exists, file exists
    MISSING = "missing"        # Metadata exists, file missing (orphaned metadata)
    ORPHAN = "orphan"          # File exists, no metadata reference
    PENDING = "pending"        # Neither metadata nor file exists (expected state)
    UNSUPPORTED = "unsupported"  # Artifact type not supported for this artifact


@dataclass
class ArtifactRecord:
    """A single artifact record with its state."""
    document_id: int
    artifact_path: Optional[str] = None  # Relative path in metadata
    full_path: Optional[Path] = None     # Absolute filesystem path
    state: ArtifactState = ArtifactState.PENDING
    reason: Optional[str] = None


@dataclass
class RecoveryReport:
    """Report from artifact detection/recovery operation."""
    artifact_type: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    # Categorized artifacts
    valid: List[ArtifactRecord] = field(default_factory=list)
    missing: List[ArtifactRecord] = field(default_factory=list)
    orphans: List[ArtifactRecord] = field(default_factory=list)
    
    # Statistics
    total_documents: int = 0
    total_files: int = 0
    
    # Recovery stats
    repaired: int = 0
    failed: int = 0
    skipped: int = 0
    
    # Errors
    errors: List[str] = field(default_factory=list)

    def summary(self) -> dict:
        """Get a summary of the detection results."""
        return {
            'artifact_type': self.artifact_type,
            'total_documents': self.total_documents,
            'total_files': self.total_files,
            'valid': len(self.valid),
            'missing': len(self.missing),
            'orphans': len(self.orphans),
            'repaired': self.repaired,
            'failed': self.failed,
            'skipped': self.skipped,
            'health_percentage': self._health_percentage()
        }

    def _health_percentage(self) -> float:
        """Calculate artifact health percentage."""
        expected = self.total_documents
        if expected == 0:
            return 100.0
        return round((len(self.valid) / expected) * 100, 2)

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        logger.error(f"Recovery error: {error}")


class BaseArtifactRecovery(ABC):
    """
    Base class for artifact recovery operations.

    This abstract class defines the interface that all artifact-specific
    recovery implementations must follow.

    ARCHITECTURE:
    1. Detection compares database metadata against filesystem state
    2. Recovery only repairs MISSING artifacts (never regenerates valid ones)
    3. Orphan files are logged but not automatically deleted
    """

    # Artifact type identifier (e.g., 'thumbnail', 'embedding', 'ocr')
    ARTIFACT_TYPE: str = "artifact"

    # Subdirectory within librarian-data where artifacts are stored
    ARTIFACT_SUBDIR: str = ""

    def __init__(self, backend, librarian_data_root: str = None):
        """
        Initialize the recovery handler.

        Args:
            backend: Storage backend instance
            librarian_data_root: Override for librarian data root path
        """
        self.backend = backend
        self.librarian_data_root = librarian_data_root or get_librarian_data_root()
        self.artifact_dir = Path(self.librarian_data_root) / self.ARTIFACT_SUBDIR

    @abstractmethod
    def get_artifact_metadata(self) -> List[Dict[str, Any]]:
        """
        Get all artifact metadata from the database.

        Returns:
            List of dicts containing document_id and artifact_path for each record
        """
        pass

    @abstractmethod
    def get_artifact_path_field(self) -> str:
        """
        Get the database field name that stores the artifact path.

        Returns:
            Field name string (e.g., 'thumbnail_path', 'embedding_path')
        """
        pass

    @abstractmethod
    def is_supported_artifact(self, document_id: int) -> bool:
        """
        Check if a document supports this artifact type.

        Args:
            document_id: Document ID to check

        Returns:
            True if this document type supports artifact generation
        """
        pass

    def get_existing_files(self) -> Set[str]:
        """
        Get all existing artifact files in the storage directory.

        Returns:
            Set of artifact filenames (just filenames, not full paths)
        """
        files = set()
        if not self.artifact_dir.exists():
            logger.warning(f"Artifact directory does not exist: {self.artifact_dir}")
            return files

        try:
            for entry in self.artifact_dir.iterdir():
                if entry.is_file():
                    files.add(entry.name)
        except Exception as e:
            logger.error(f"Error listing artifact directory: {e}")

        return files

    def resolve_artifact_path(self, relative_path: str) -> Optional[Path]:
        """
        Resolve a relative artifact path to an absolute path.

        Args:
            relative_path: Relative path from librarian data root

        Returns:
            Absolute Path object, or None if path is invalid
        """
        if not relative_path:
            return None
        
        full_path = self.artifact_dir / relative_path
        return full_path if full_path.exists() else None

    def detect(self) -> RecoveryReport:
        """
        Detect artifact state across all documents.

        This method:
        1. Gets all artifact metadata from database
        2. Gets all existing artifact files from filesystem
        3. Classifies each artifact as VALID, MISSING, ORPHAN, or PENDING

        Returns:
            RecoveryReport with categorized artifacts
        """
        report = RecoveryReport(artifact_type=self.ARTIFACT_TYPE)

        # Get all existing files
        existing_files = self.get_existing_files()
        report.total_files = len(existing_files)

        # Get all metadata records
        metadata_records = self.get_artifact_metadata()
        report.total_documents = len(metadata_records)

        # Track which files are referenced
        referenced_files: Set[str] = set()

        for record in metadata_records:
            doc_id = record['document_id']
            artifact_path = record.get(self.get_artifact_path_field())

            # Check if document supports this artifact type
            if not self.is_supported_artifact(doc_id):
                continue

            artifact_record = ArtifactRecord(
                document_id=doc_id,
                artifact_path=artifact_path,
                state=ArtifactState.PENDING
            )

            if artifact_path:
                # Metadata exists - check if file exists
                filename = os.path.basename(artifact_path)
                referenced_files.add(filename)
                full_path = self.resolve_artifact_path(artifact_path)

                if full_path and full_path.exists():
                    # Both metadata and file exist - VALID
                    artifact_record.full_path = full_path
                    artifact_record.state = ArtifactState.VALID
                    report.valid.append(artifact_record)
                else:
                    # Metadata exists but file missing - MISSING
                    artifact_record.state = ArtifactState.MISSING
                    artifact_record.reason = f"File not found: {artifact_path}"
                    report.missing.append(artifact_record)
            else:
                # No metadata - PENDING (expected state)
                report.valid.append(artifact_record)

        # Find orphan files (exist on disk but not referenced in metadata)
        for filename in existing_files:
            if filename not in referenced_files:
                orphan_record = ArtifactRecord(
                    document_id=0,  # Unknown document
                    artifact_path=filename,
                    full_path=self.artifact_dir / filename,
                    state=ArtifactState.ORPHAN,
                    reason="File exists but not referenced in any document metadata"
                )
                report.orphans.append(orphan_record)

        logger.info(
            f"Detection complete: {len(report.valid)} valid, "
            f"{len(report.missing)} missing, {len(report.orphans)} orphans "
            f"for {self.ARTIFACT_TYPE}"
        )

        return report

    @abstractmethod
    def clear_artifact_metadata(self, document_id: int) -> bool:
        """
        Clear the artifact metadata for a document.

        Args:
            document_id: Document ID to clear

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def requeue_artifact_job(self, document_id: int) -> Optional[int]:
        """
        Requeue the artifact generation job.

        Args:
            document_id: Document ID to requeue

        Returns:
            Job ID if created, None if failed or duplicate
        """
        pass

    def repair(self, missing_records: List[ArtifactRecord], 
               dry_run: bool = True) -> RecoveryReport:
        """
        Repair missing artifacts.

        For each missing artifact:
        1. Clear the stale metadata
        2. Requeue the generation job

        Args:
            missing_records: List of ArtifactRecords with MISSING state
            dry_run: If True, only report what would be done (default True)

        Returns:
            RecoveryReport with repair statistics
        """
        report = RecoveryReport(artifact_type=self.ARTIFACT_TYPE)
        report.total_documents = len(missing_records)

        for record in missing_records:
            doc_id = record.document_id

            if dry_run:
                logger.info(f"[DRY RUN] Would repair document {doc_id}: {record.reason}")
                report.skipped += 1
                continue

            try:
                # Step 1: Clear stale metadata
                if self.clear_artifact_metadata(doc_id):
                    logger.info(f"Cleared metadata for document {doc_id}")
                else:
                    report.add_error(f"Failed to clear metadata for document {doc_id}")
                    report.failed += 1
                    continue

                # Step 2: Requeue generation job
                job_id = self.requeue_artifact_job(doc_id)
                if job_id:
                    logger.info(f"Requeued job {job_id} for document {doc_id}")
                    report.repaired += 1
                else:
                    report.add_error(f"Failed to requeue job for document {doc_id}")
                    report.failed += 1

            except Exception as e:
                report.add_error(f"Error repairing document {doc_id}: {e}")
                report.failed += 1

        return report


# Registry of available recovery handlers (Tier 1A artifacts only)
#
# NOTE: Thumbnails (Tier 1B) are NOT registered here because:
# - Thumbnails are disposable cache, not derived artifacts
# - Missing thumbnails are cache misses, not corruption
# - Thumbnail regeneration happens on-demand via the UI
# - No recovery framework is needed or appropriate
#
# See docs/architecture/derived-artifact-contract.md for the full tier classification.
RECOVERY_HANDLERS = {
    # Tier 1A handlers - expensive artifacts that warrant recovery:
    # 'embedding': EmbeddingRecovery,
    # 'ocr': OCRRecovery,
    # 'object_detection': ObjectDetectionRecovery,
    # 'transcription': TranscriptionRecovery,
}


def get_recovery_handler(artifact_type: str, backend) -> Optional[BaseArtifactRecovery]:
    """
    Get a recovery handler for an artifact type.

    Args:
        artifact_type: Type of artifact ('embedding', 'ocr', 'object_detection', etc.)
        backend: Storage backend instance

    Returns:
        Recovery handler instance, or None if not supported (including thumbnails)

    Note:
        Thumbnails (Tier 1B) are not supported by this function.
        Thumbnail regeneration happens on-demand, not via recovery framework.
    """
    handler_class = RECOVERY_HANDLERS.get(artifact_type.lower())
    if handler_class:
        return handler_class(backend)
    return None
