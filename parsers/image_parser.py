"""
Image parser for artifact ingestion.

Artifact Ingestion Phase 1: First-Class Image Support

This module provides lightweight image artifact ingestion.
Its purpose is ingestion, NOT enrichment.

Parser responsibilities:
- Validate image file
- Identify mime type
- Identify dimensions (inexpensive)
- Create document record
- Return artifact metadata

Worker responsibilities (handled by PhotoMetadataExtractor):
- EXIF extraction
- GPS coordinates
- Camera information
- Timestamps
"""

from pathlib import Path
from typing import Optional

from PIL import Image


# MIME type mapping for supported image formats
MIME_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff',
    '.webp': 'image/webp',
    '.heic': 'image/heic',
    '.heif': 'image/heif',
}

# Supported image extensions for ingestion
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.heic', '.heif'}


class ImageParser:
    """
    Parser for image artifacts.
    
    This parser is intentionally lightweight. Its purpose is ingestion,
    not enrichment. It validates the image file and extracts basic
    metadata needed for document creation.
    
    The actual enrichment (EXIF extraction, GPS, camera info) is handled
    by the PhotoMetadataExtractor worker.
    """
    
    def parse(self, file_path):
        """
        Parse an image file and extract artifact metadata.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dict with artifact metadata, or None if parsing failed
        """
        try:
            path = Path(file_path)
            
            # Validate file exists and has supported extension
            if not path.exists():
                return None
            
            extension = path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                return None
            
            # Get MIME type
            mime_type = MIME_TYPES.get(extension, 'application/octet-stream')
            
            # Get dimensions (PIL does this without loading full image into memory)
            width, height = self._get_dimensions(path)
            
            # Get file size
            file_size = path.stat().st_size
            
            return {
                'text': None,  # Images don't have text content
                'structured_data': {
                    'mime_type': mime_type,
                    'width': width,
                    'height': height,
                    'aspect_ratio': round(width / height, 2) if height > 0 else None,
                },
                'character_count': file_size,  # Use file size as character_count equivalent
                'extension': extension,
                'parser': 'image',
            }
            
        except Exception:
            return None
    
    def _get_dimensions(self, path: Path) -> tuple:
        """
        Get image dimensions without loading full image into memory.
        
        Uses PIL's efficient dimension-only loading.
        """
        try:
            with Image.open(path) as img:
                return img.size  # Returns (width, height)
        except Exception:
            return (0, 0)


def is_image_file(filepath: Path) -> bool:
    """
    Check if a file is a supported image type.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if the file has a supported image extension
    """
    return filepath.suffix.lower() in SUPPORTED_EXTENSIONS


def get_mime_type(extension: str) -> str:
    """
    Get MIME type for a file extension.
    
    Args:
        extension: File extension (with or without dot)
        
    Returns:
        MIME type string
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    return MIME_TYPES.get(extension.lower(), 'application/octet-stream')