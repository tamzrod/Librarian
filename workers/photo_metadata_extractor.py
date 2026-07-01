"""
Photo metadata extraction handler for the worker.

Phase 1A: Evidence Timeline - Photo Metadata Extraction

This module handles the 'extract_photo_metadata' job type.
It extracts deterministic EXIF metadata from image files.

DO NOT IMPLEMENT:
- OCR
- Face recognition
- Object recognition
- Scene recognition
- AI tagging
- Reverse geocoding
- Maps
"""

import os
import logging
from pathlib import Path
from typing import Optional
from environment import get_library_root
from .base import BaseWorker

logger = logging.getLogger(__name__)


class PhotoMetadataExtractor(BaseWorker):
    """
    Extracts photo metadata from image files.
    
    This is a job handler that can be registered with the Worker.
    It handles the 'extract_photo_metadata' job type.
    
    Phase 1A: Only extracts EXIF metadata present in the image file.
    No AI inference, no OCR, no object detection.
    """
    
    # Supported image extensions for Phase 1A
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif'}
    
    def __init__(self, backend, library_root: str = None):
        """
        Initialize the photo metadata extractor.
        
        Args:
            backend: Storage backend
            library_root: Root path of the document library
        """
        self.backend = backend
        self.library_root = library_root or get_library_root()
    
    def process(self, job: dict) -> dict:
        """
        Extract photo metadata from an image document.
        
        This is the job handler for 'extract_photo_metadata' jobs.
        
        Args:
            job: Job dict with document_id and job_type
            
        Returns:
            Dict with extraction results
        """
        document_id = job['document_id']
        job_id = job['id']
        
        logger.info(f"Starting photo metadata extraction for document {document_id}")
        
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
            
            # Extract metadata
            metadata = self._extract_metadata(full_path)
            
            if metadata is None:
                raise ValueError(f"Failed to extract metadata from {full_path}")
            
            # Save metadata to database
            success = self.backend.save_photo_metadata(document_id, metadata)
            
            if not success:
                raise RuntimeError(f"Failed to save photo metadata for document {document_id}")
            
            # Update document status to METADATA_INDEXED (if not already further along)
            try:
                self.backend.transition_document_status(
                    document_id,
                    'METADATA_INDEXED'
                )
            except ValueError as e:
                # State transition might fail if already in that state or beyond
                logger.debug(f"State transition skipped: {e}")
            
            # Log extracted info
            extracted_fields = self._count_extracted_fields(metadata)
            logger.info(
                f"Successfully extracted photo metadata for document {document_id}: "
                f"{extracted_fields} fields"
            )
            
            return {
                'document_id': document_id,
                'fields_extracted': extracted_fields,
                'has_gps': metadata.get('gps_latitude') is not None and metadata.get('gps_longitude') is not None,
                'has_timestamp': metadata.get('timestamp_original') is not None,
                'camera': f"{metadata.get('camera_make', '')} {metadata.get('camera_model', '')}".strip() or None,
            }
            
        except Exception as e:
            logger.error(f"Photo metadata extraction failed for document {document_id}: {e}")
            raise
    
    def _is_supported_image(self, extension: str) -> bool:
        """Check if file extension is a supported image type."""
        if not extension:
            return False
        # Remove leading dot if present
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
        return ext in self.SUPPORTED_EXTENSIONS
    
    def _extract_metadata(self, filepath: Path) -> Optional[dict]:
        """
        Extract metadata from an image file.
        
        Args:
            filepath: Path to the image file
            
        Returns:
            Dict with extracted metadata, or None if extraction failed
        """
        try:
            # Import here to avoid circular imports and handle missing PIL gracefully
            from parsers.image_parser import extract_photo_metadata as parse_image
            
            return parse_image(filepath)
        except ImportError as e:
            logger.error(f"PIL not available for image parsing: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting photo metadata from {filepath}: {e}")
            return None
    
    def _count_extracted_fields(self, metadata: dict) -> int:
        """Count how many meaningful fields were extracted."""
        count = 0
        
        # Core fields
        if metadata.get('timestamp_original'):
            count += 1
        if metadata.get('gps_latitude') is not None:
            count += 1
        if metadata.get('gps_longitude') is not None:
            count += 1
        if metadata.get('camera_make'):
            count += 1
        if metadata.get('camera_model'):
            count += 1
        if metadata.get('lens_model'):
            count += 1
        if metadata.get('width') and metadata.get('height'):
            count += 1  # Dimensions as one field
        if metadata.get('orientation'):
            count += 1
        if metadata.get('file_format'):
            count += 1
        
        return count
