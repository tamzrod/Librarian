"""
Thumbnail generation handler for the worker.

This module handles the 'generate_thumbnail' job type.
It generates thumbnail images from source images and stores them in Librarian-managed storage.

THUMBNAIL CONTRACT (Tier 1B - Disposable Cache):
================================================
Thumbnails are NOT evidence.
Thumbnails are NOT expensive artifacts.
Thumbnails are CACHE.

If a thumbnail disappears, regenerate it.

Key characteristics:
- Generation cost: Low (<1 second CPU)
- External dependencies: None
- Recovery framework: NOT REQUIRED
- Integrity audits: NOT REQUIRED
- Missing thumbnail = cache miss, NOT corruption

See docs/architecture/derived-artifact-contract.md for the full tier classification.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from environment import get_library_root, get_librarian_data_root
from .base import BaseWorker

logger = logging.getLogger(__name__)

# Thumbnail settings
THUMBNAIL_SIZE = (256, 256)  # Max width/height for thumbnails
THUMBNAIL_DIR = "thumbnails"  # Directory name within librarian data root


class ThumbnailGenerator(BaseWorker):
    """
    Generates thumbnails from image documents.

    This is a job handler that can be registered with the Worker.
    It handles the 'generate_thumbnail' job type.

    TIER 1B - DISPOSABLE CACHE:
    This worker produces Tier 1B artifacts (disposable cache).
    - Thumbnails are cheap to generate (<1 second CPU)
    - No external dependencies required
    - No recovery framework needed
    - Missing thumbnails are cache misses, not corruption

    See docs/architecture/derived-artifact-contract.md for the full contract.
    """

    # Supported image extensions for thumbnail generation
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif'}

    # Operation Plugin Foundation: Plugin identity
    PLUGIN_NAME = 'metadata.thumbnail.pillow'  # Fully qualified namespace
    ENGINE_NAME = 'pillow-thumbnail'           # Engine identifier
    PLUGIN_VERSION = '1.0.0'                  # Plugin version

    def __init__(self, backend, library_root: str = None, librarian_data_root: str = None):
        """
        Initialize the thumbnail generator.

        Args:
            backend: Storage backend
            library_root: Root path of the document library
            librarian_data_root: Root path for Librarian-managed derived artifacts
        """
        self.backend = backend
        self.library_root = library_root or get_library_root()
        self.librarian_data_root = librarian_data_root or get_librarian_data_root()

    def process(self, job: dict) -> dict:
        """
        Generate a thumbnail for an image document.

        This worker implements the thumbnail contract:
        1. Generate thumbnail
        2. Save thumbnail to filesystem
        3. Verify file exists AND has size > 0
        4. Only then update database and mark COMPLETE

        A job must NEVER reach COMPLETE before filesystem verification.

        Args:
            job: Job dict with document_id and job_type

        Returns:
            Dict with generation results

        Raises:
            RuntimeError: If thumbnail file cannot be verified on filesystem
        """
        document_id = job['document_id']
        job_id = job['id']

        logger.info(f"Starting thumbnail generation for document {document_id}")

        try:
            # Get document info
            conn = self.backend._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, path, extension FROM documents WHERE id = %s",
                (document_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                raise ValueError(f"Document {document_id} not found")

            doc_id, doc_path, extension = row

            # Check if file is a supported image type
            if not self._is_supported_image(extension):
                raise ValueError(f"Document {document_id} is not a supported image type: {extension}")

            # Resolve full path
            if os.path.isabs(doc_path):
                full_path = Path(doc_path)
            else:
                full_path = Path(self.library_root) / doc_path

            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {full_path}")

            # Generate and save thumbnail
            thumbnail_path = self._generate_thumbnail(full_path, document_id)

            # CRITICAL: Verify filesystem state BEFORE updating database
            # This is the "Worker Contract" - COMPLETE must never occur before filesystem verification
            full_thumbnail_path = Path(self.librarian_data_root) / thumbnail_path
            if not self._verify_thumbnail_filesystem(full_thumbnail_path):
                raise RuntimeError(
                    f"Thumbnail filesystem verification failed for {full_thumbnail_path}. "
                    f"Job will NOT be marked complete until file exists with size > 0."
                )

            # Only update database after filesystem verification passes
            self._save_thumbnail_path(document_id, thumbnail_path)

            logger.info(f"Successfully generated and verified thumbnail for document {document_id}: {thumbnail_path}")

            return {
                'document_id': document_id,
                'thumbnail_path': thumbnail_path,
                'success': True,
                'verified': True
            }

        except Exception as e:
            logger.error(f"Thumbnail generation failed for document {document_id}: {e}")
            raise

    def _is_supported_image(self, extension: str) -> bool:
        """Check if file extension is a supported image type."""
        if not extension:
            return False
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
        return ext in self.SUPPORTED_EXTENSIONS

    def _generate_thumbnail(self, source_path: Path, document_id: int) -> str:
        """
        Generate a thumbnail from an image file.

        Args:
            source_path: Path to the source image
            document_id: Document ID for naming

        Returns:
            Relative path to the generated thumbnail (relative to catalog root)
        """
        try:
            from PIL import Image

            # Create thumbnail directory in librarian data root
            data_root = Path(self.librarian_data_root)
            thumbnail_dir = data_root / THUMBNAIL_DIR
            thumbnail_dir.mkdir(parents=True, exist_ok=True)

            # Generate thumbnail filename
            source_name = source_path.stem
            thumbnail_filename = f"{document_id}_{source_name}_thumb.jpg"
            thumbnail_full_path = thumbnail_dir / thumbnail_filename

            # Generate thumbnail
            with Image.open(source_path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Generate thumbnail (maintains aspect ratio)
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

                # Save thumbnail
                img.save(thumbnail_full_path, 'JPEG', quality=85)

            # Return relative path from librarian data root (catalog path)
            return str(Path(THUMBNAIL_DIR) / thumbnail_filename)

        except ImportError:
            logger.error("PIL not available for thumbnail generation")
            raise RuntimeError("PIL (Pillow) is required for thumbnail generation")
        except Exception as e:
            logger.error(f"Error generating thumbnail from {source_path}: {e}")
            raise

    def _save_thumbnail_path(self, document_id: int, thumbnail_path: str):
        """
        Save thumbnail path to the database.

        Args:
            document_id: Document ID
            thumbnail_path: Relative path to thumbnail
        """
        try:
            conn = self.backend._get_connection()
            cur = conn.cursor()

            # Add thumbnail_path column if it doesn't exist
            # This is a lightweight migration
            cur.execute("""
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS thumbnail_path VARCHAR(500)
            """)

            # Update the document with thumbnail path
            cur.execute("""
                UPDATE documents
                SET thumbnail_path = %s
                WHERE id = %s
            """, (thumbnail_path, document_id))

            conn.commit()
            cur.close()
            conn.close()

            logger.debug(f"Saved thumbnail path for document {document_id}: {thumbnail_path}")

        except Exception as e:
            logger.error(f"Error saving thumbnail path for document {document_id}: {e}")
            raise

    def _verify_thumbnail_filesystem(self, thumbnail_full_path: Path) -> bool:
        """
        Verify that a thumbnail file exists on the filesystem with size > 0.

        This is the critical verification step in the Worker Contract.
        We MUST verify filesystem existence before marking a job COMPLETE.

        Args:
            thumbnail_full_path: Full filesystem path to the thumbnail

        Returns:
            True if file exists and has size > 0, False otherwise
        """
        try:
            # Check file exists
            if not thumbnail_full_path.exists():
                logger.warning(f"Thumbnail file does not exist: {thumbnail_full_path}")
                return False

            # Check it is a file (not a directory)
            if not thumbnail_full_path.is_file():
                logger.warning(f"Thumbnail path is not a file: {thumbnail_full_path}")
                return False

            # Check file size > 0
            file_size = thumbnail_full_path.stat().st_size
            if file_size == 0:
                logger.warning(f"Thumbnail file has zero size: {thumbnail_full_path}")
                return False

            logger.debug(f"Thumbnail filesystem verification passed: {thumbnail_full_path} ({file_size} bytes)")
            return True

        except Exception as e:
            logger.error(f"Error verifying thumbnail filesystem state: {e}")
            return False
