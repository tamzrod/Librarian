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


def _convert_dms_to_decimal(dms: tuple, direction: str) -> float:
    """
    Convert GPS Degrees-Minutes-Seconds to decimal degrees.
    
    Args:
        dms: Tuple of ((degrees, deg_div), (minutes, min_div), (seconds, sec_div))
             or PIL IFDRational objects
        direction: 'N', 'S', 'E', or 'W'
        
    Returns:
        Decimal degrees as float
    """
    if not dms:
        return None
    
    def to_float(val):
        """Convert value to float, handling PIL IFDRational objects."""
        if hasattr(val, 'numerator') and hasattr(val, 'denominator'):
            # PIL IFDRational
            return val.numerator / val.denominator if val.denominator else 0
        elif isinstance(val, tuple) and len(val) == 2:
            # Regular fraction tuple
            return val[0] / val[1] if val[1] else 0
        else:
            # Already a number
            return float(val)
    
    degrees = to_float(dms[0])
    minutes = to_float(dms[1])
    seconds = to_float(dms[2])
    
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    # Apply direction for lat/long
    if direction in ('S', 'W'):
        decimal = -decimal
    
    # Round to 6 decimal places (about 10cm precision)
    return round(decimal, 6)


def _parse_exif_timestamp(exif_date: str) -> str:
    """
    Parse EXIF timestamp format to ISO 8601.
    
    EXIF format: "YYYY:MM:DD HH:MM:SS"
    ISO 8601: "YYYY-MM-DDTHH:MM:SS"
    
    Args:
        exif_date: EXIF date string
        
    Returns:
        ISO 8601 formatted string, or None if invalid
    """
    if not exif_date or not isinstance(exif_date, str):
        return None
    
    # EXIF format: "2026:01:15 09:42:18"
    # Handle multiple possible formats
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M", "%Y/%m/%d %H:%M:%S"):
        try:
            from datetime import datetime
            dt = datetime.strptime(exif_date.strip(), fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue
    
    return None


def extract_photo_metadata(filepath) -> dict:
    """
    Extract EXIF metadata from an image file.
    
    This function extracts deterministic metadata from image files:
    - Timestamps (original, digitized, metadata)
    - GPS coordinates (latitude, longitude, altitude)
    - Camera information (make, model, lens)
    - Image properties (dimensions, orientation, format)
    
    Args:
        filepath: Path to the image file (str or Path)
        
    Returns:
        Dict with extracted metadata, or None if extraction failed
    """
    try:
        from pathlib import Path
        from PIL import Image
        from PIL.ExifTags import TAGS
        
        path = Path(filepath)
        if not path.exists():
            return None
        
        metadata = {
            'timestamp_original': None,
            'timestamp_digitized': None,
            'timestamp_metadata': None,
            'gps_latitude': None,
            'gps_longitude': None,
            'gps_altitude': None,
            'camera_make': None,
            'camera_model': None,
            'lens_model': None,
            'width': None,
            'height': None,
            'orientation': None,
            'file_format': None,
            'raw_exif': None,
        }
        
        with Image.open(path) as img:
            # Get dimensions and format
            metadata['width'], metadata['height'] = img.size
            metadata['file_format'] = img.format or 'UNKNOWN'
            
            # Extract EXIF data
            exif_data = img.getexif()
            if not exif_data:
                return metadata
            
            # Build raw_exif dict for debugging
            raw_exif = {}
            
            # Parse EXIF tags from main IFD
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                raw_exif[str(tag)] = str(value)[:500]  # Truncate long values
                
                # Timestamp tags in main IFD
                if tag_id == 0x0132:  # DateTime (main IFD)
                    metadata['timestamp_metadata'] = _parse_exif_timestamp(value)
                
                # Camera tags in main IFD
                elif tag_id == 0x010f:  # Make
                    metadata['camera_make'] = str(value).strip() if value else None
                elif tag_id == 0x0110:  # Model
                    metadata['camera_model'] = str(value).strip() if value else None
                elif tag_id == 0x0112:  # Orientation
                    metadata['orientation'] = int(value) if value else None
            
            # Parse EXIF tags from nested Exif IFD (0x8769)
            exif_ifd = exif_data.get_ifd(0x8769)  # ExifOffset
            if exif_ifd:
                for tag_id, value in exif_ifd.items():
                    tag = TAGS.get(tag_id, tag_id)
                    raw_exif[f'Exif.{tag}'] = str(value)[:500]
                    
                    # Timestamp tags
                    if tag_id == 0x9003:  # DateTimeOriginal
                        parsed_ts = _parse_exif_timestamp(value)
                        metadata['timestamp_original'] = parsed_ts
                        raw_exif['timestamp_original'] = parsed_ts  # Store parsed ISO format
                    elif tag_id == 0x9004:  # DateTimeDigitized
                        parsed_ts = _parse_exif_timestamp(value)
                        metadata['timestamp_digitized'] = parsed_ts
                        raw_exif['timestamp_digitized'] = parsed_ts  # Store parsed ISO format
                    
                    # Lens tag
                    elif tag_id == 0xa434:  # LensModel
                        metadata['lens_model'] = str(value).strip() if value else None
            
            # Extract GPS data from GPS IFD (0x8825)
            gps_ifd = exif_data.get_ifd(0x8825)  # GPS IFD
            if gps_ifd:
                raw_exif['GPS'] = {}
                
                # GPS Latitude
                latitude = gps_ifd.get(0x0002)  # GPSLatitude
                lat_ref = gps_ifd.get(0x0001)  # GPSLatitudeRef
                if latitude:
                    direction = 'N' if str(lat_ref) == 'N' else 'S'
                    metadata['gps_latitude'] = _convert_dms_to_decimal(latitude, direction)
                    raw_exif['GPS']['latitude'] = f"{latitude}, {lat_ref}"
                
                # GPS Longitude
                longitude = gps_ifd.get(0x0004)  # GPSLongitude
                lon_ref = gps_ifd.get(0x0003)  # GPSLongitudeRef
                if longitude:
                    direction = 'E' if str(lon_ref) == 'E' else 'W'
                    metadata['gps_longitude'] = _convert_dms_to_decimal(longitude, direction)
                    raw_exif['GPS']['longitude'] = f"{longitude}, {lon_ref}"
                
                # GPS Altitude
                altitude = gps_ifd.get(0x0006)  # GPSAltitude
                if altitude:
                    alt_ref = gps_ifd.get(0x0005)  # GPSAltitudeRef
                    # Handle IFDRational, tuples, and direct values
                    if hasattr(altitude, 'numerator'):
                        alt_value = altitude.numerator / altitude.denominator if altitude.denominator else altitude.numerator
                    elif isinstance(altitude, tuple):
                        alt_value = altitude[0] / altitude[1] if altitude[1] else altitude[0]
                    else:
                        alt_value = float(altitude)
                    # alt_ref is usually a byte (0 or 1)
                    if str(alt_ref) == '1' or alt_ref == 1 or alt_ref == b'\x01':
                        alt_value = -alt_value
                    metadata['gps_altitude'] = round(alt_value, 2)
                    raw_exif['GPS']['altitude'] = str(altitude)
            
            # Store raw EXIF for debugging
            metadata['raw_exif'] = raw_exif
            
            return metadata
            
    except ImportError:
        # PIL not available
        return None
    except Exception:
        # Other errors - return what we can
        return None