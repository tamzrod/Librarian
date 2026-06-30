"""
Image parser for extracting EXIF metadata from image files.

Phase 1A: Evidence Timeline - Photo Metadata Extraction

This module provides deterministic metadata extraction from image files.
No AI inference, no OCR, no object recognition - only metadata already
present in the image file.
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pathlib import Path
from typing import Optional


# Supported image extensions
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif'}


def is_image_file(filepath: Path) -> bool:
    """Check if a file is a supported image type.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if the file has a supported image extension
    """
    return filepath.suffix.lower() in SUPPORTED_EXTENSIONS


def extract_photo_metadata(filepath: Path) -> Optional[dict]:
    """
    Extract photo metadata from an image file.
    
    Phase 1A implementation - only extracts EXIF metadata present in the file.
    No AI inference, no OCR, no object detection.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        Dict with extracted metadata, or None if extraction failed
    """
    try:
        img = Image.open(filepath)
        
        # Get basic image properties
        width, height = img.size
        file_format = img.format
        
        # Get EXIF data
        exif = img._getexif() if hasattr(img, '_getexif') else None
        
        metadata = {
            'width': width,
            'height': height,
            'file_format': file_format,
            'raw_exif': None,
        }
        
        # Extract EXIF fields
        if exif:
            exif_data = _parse_exif(exif)
            metadata.update(exif_data)
            metadata['raw_exif'] = exif_data
        
        return metadata
        
    except Exception as e:
        return None


def _parse_exif(exif) -> dict:
    """
    Parse EXIF data from an image.
    
    Only extracts deterministic metadata fields - no inference.
    """
    result = {}
    exif_data = {}
    
    # Convert EXIF tags to readable names
    for tag_id, value in exif.items():
        tag = TAGS.get(tag_id, tag_id)
        exif_data[tag] = value
    
    # Timestamp extraction (in order of preference)
    # DateTimeOriginal: When photo was actually taken
    # DateTimeDigitized: When photo was digitized
    # DateTime: File modification time
    for key in ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']:
        if key in exif_data:
            ts_value = _parse_exif_timestamp(exif_data[key])
            if key == 'DateTimeOriginal':
                result['timestamp_original'] = ts_value
            elif key == 'DateTimeDigitized':
                result['timestamp_digitized'] = ts_value
            else:
                result['timestamp_metadata'] = ts_value
            break
    
    # Camera make (manufacturer)
    if 'Make' in exif_data:
        result['camera_make'] = str(exif_data['Make']).strip()
    
    # Camera model
    if 'Model' in exif_data:
        result['camera_model'] = str(exif_data['Model']).strip()
    
    # Lens model
    if 'LensModel' in exif_data:
        result['lens_model'] = str(exif_data['LensModel']).strip()
    
    # Orientation
    if 'Orientation' in exif_data:
        result['orientation'] = int(exif_data['Orientation'])
    
    # GPS coordinates
    gps_ifd = exif_data.get('GPSInfo', {})
    if gps_ifd:
        gps_data = {}
        for tag_id, value in gps_ifd.items():
            tag = GPSTAGS.get(tag_id, tag_id)
            gps_data[tag] = value
        
        # GPS Latitude
        lat = gps_data.get('GPSLatitude')
        lat_ref = gps_data.get('GPSLatitudeRef')
        if lat and lat_ref:
            result['gps_latitude'] = _convert_dms_to_decimal(lat, lat_ref)
        
        # GPS Longitude
        lon = gps_data.get('GPSLongitude')
        lon_ref = gps_data.get('GPSLongitudeRef')
        if lon and lon_ref:
            result['gps_longitude'] = _convert_dms_to_decimal(lon, lon_ref)
        
        # GPS Altitude
        altitude = gps_data.get('GPSAltitude')
        if altitude is not None:
            if isinstance(altitude, tuple):
                altitude = altitude[0] / altitude[1] if altitude[1] != 0 else 0
            alt_ref = gps_data.get('GPSAltitudeRef', 0)
            result['gps_altitude'] = abs(float(altitude)) if not alt_ref else -abs(float(altitude))
    
    return result


def _parse_exif_timestamp(value) -> Optional[str]:
    """
    Parse EXIF timestamp format to ISO format.
    
    EXIF format: "YYYY:MM:DD HH:MM:SS"
    ISO format: "YYYY-MM-DDTHH:MM:SS"
    """
    if not value or not isinstance(value, str):
        return None
    
    # EXIF format: "2026:01:15 09:42:18"
    try:
        # Handle the format with space separator
        if ' ' in value:
            date_part, time_part = value.split(' ')
            # Handle colon separators in date
            date_part = date_part.replace(':', '-')
            return f"{date_part}T{time_part}"
    except (ValueError, IndexError):
        pass
    
    return None


def _convert_dms_to_decimal(dms, ref) -> float:
    """
    Convert GPS DMS (Degrees, Minutes, Seconds) to decimal degrees.
    
    Args:
        dms: Tuple of (degrees, minutes, seconds) - each can be tuple (num, denom) or int
        ref: Reference direction ('N', 'S', 'E', 'W')
        
    Returns:
        Decimal degrees as float
    """
    degrees = float(dms[0][0]) / dms[0][1] if isinstance(dms[0], tuple) else float(dms[0])
    minutes = float(dms[1][0]) / dms[1][1] if isinstance(dms[1], tuple) else float(dms[1])
    seconds = float(dms[2][0]) / dms[2][1] if isinstance(dms[2], tuple) else float(dms[2])
    
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    # Negative for South (S) or West (W)
    if ref in ['S', 'W']:
        decimal = -decimal
    
    return round(decimal, 6)


def parse_image(filepath):
    """
    Legacy function for backward compatibility.
    Use extract_photo_metadata() for new code.
    """
    structured_data = {}
    
    img = Image.open(filepath)
    exif = img._getexif() if hasattr(img, '_getexif') else None
    
    if exif:
        exif_data = _parse_exif(exif)
        
        # Map to legacy field names
        if 'timestamp_original' in exif_data:
            structured_data['timestamp'] = exif_data['timestamp_original']
        
        if 'camera_make' in exif_data:
            structured_data['camera_make'] = exif_data['camera_make']
        
        if 'camera_model' in exif_data:
            structured_data['camera_model'] = exif_data['camera_model']
        
        if 'gps_latitude' in exif_data:
            structured_data['gps_latitude'] = exif_data['gps_latitude']
        
        if 'gps_longitude' in exif_data:
            structured_data['gps_longitude'] = exif_data['gps_longitude']
        
        if 'gps_altitude' in exif_data:
            structured_data['gps_altitude'] = exif_data['gps_altitude']
    
    return structured_data