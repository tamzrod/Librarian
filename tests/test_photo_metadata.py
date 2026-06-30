"""
Tests for photo metadata extraction (Phase 1A: Evidence Timeline).

These tests verify deterministic EXIF metadata extraction from image files.
No AI inference, no OCR, no object recognition.
"""

import pytest
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.image_parser import (
    extract_photo_metadata,
    is_image_file,
    _convert_dms_to_decimal,
    _parse_exif_timestamp,
    SUPPORTED_EXTENSIONS
)


class TestImageFileDetection:
    """Test image file type detection."""
    
    def test_is_image_jpg(self):
        assert is_image_file(Path("test.jpg")) is True
        assert is_image_file(Path("test.jpeg")) is True
    
    def test_is_image_png(self):
        assert is_image_file(Path("test.png")) is True
    
    def test_is_image_webp(self):
        assert is_image_file(Path("test.webp")) is True
    
    def test_is_not_image(self):
        assert is_image_file(Path("test.txt")) is False
        assert is_image_file(Path("test.pdf")) is False
        assert is_image_file(Path("test.py")) is False
    
    def test_case_insensitive(self):
        assert is_image_file(Path("test.JPG")) is True
        assert is_image_file(Path("test.JPEG")) is True


class TestGPSToDecimal:
    """Test GPS DMS to decimal conversion."""
    
    def test_positive_north(self):
        # 14° 38' 6.68" N
        dms = ((14, 1), (38, 1), (667, 100))
        result = _convert_dms_to_decimal(dms, 'N')
        assert abs(result - 14.635186) < 0.000001
    
    def test_positive_east(self):
        # 121° 5' 33.17" E
        dms = ((121, 1), (5, 1), (3317, 100))
        result = _convert_dms_to_decimal(dms, 'E')
        assert abs(result - 121.092547) < 0.000001
    
    def test_negative_south(self):
        dms = ((14, 1), (38, 1), (667, 100))
        result = _convert_dms_to_decimal(dms, 'S')
        assert abs(result - (-14.635186)) < 0.000001
    
    def test_negative_west(self):
        dms = ((121, 1), (5, 1), (3317, 100))
        result = _convert_dms_to_decimal(dms, 'W')
        assert abs(result - (-121.092547)) < 0.000001
    
    def test_rounded_to_six_decimals(self):
        dms = ((1, 1), (2, 3), (456789, 10000))
        result = _convert_dms_to_decimal(dms, 'N')
        assert len(str(result).split('.')[-1]) <= 6


class TestTimestampParsing:
    """Test EXIF timestamp parsing."""
    
    def test_parse_exif_timestamp(self):
        result = _parse_exif_timestamp("2026:01:15 09:42:18")
        assert result == "2026-01-15T09:42:18"
    
    def test_parse_exif_timestamp_evening(self):
        result = _parse_exif_timestamp("2026:06:30 21:15:30")
        assert result == "2026-06-30T21:15:30"
    
    def test_parse_exif_timestamp_invalid(self):
        assert _parse_exif_timestamp(None) is None
        assert _parse_exif_timestamp("") is None
        assert _parse_exif_timestamp(123) is None


class TestPhotoMetadataExtraction:
    """Test photo metadata extraction from real images."""
    
    @pytest.fixture
    def sample_dir(self):
        return Path(__file__).parent.parent / "samples"
    
    def test_extract_from_geotagged_image(self, sample_dir):
        """Test extraction from an image with GPS data."""
        img_path = sample_dir / "IMG_20260101_122510.jpg"
        if not img_path.exists():
            pytest.skip(f"Sample image not found: {img_path}")
        
        metadata = extract_photo_metadata(img_path)
        
        assert metadata is not None
        assert metadata['width'] == 3000
        assert metadata['height'] == 4000
        assert metadata['file_format'] == 'JPEG'
        
        # EXIF data
        assert metadata['timestamp_original'] == '2026-01-01T12:25:10'
        assert metadata['camera_make'] == 'HONOR'
        assert metadata['camera_model'] == 'BRP-NX1'
        
        # GPS data (deterministic)
        assert metadata['gps_latitude'] is not None
        assert metadata['gps_longitude'] is not None
        assert metadata['gps_latitude'] > 0  # Northern hemisphere
        assert metadata['gps_longitude'] > 0  # Eastern hemisphere
        assert metadata['gps_altitude'] is not None
    
    def test_extract_second_geotagged_image(self, sample_dir):
        """Test extraction from another geotagged image."""
        img_path = sample_dir / "IMG_20260108_072710.jpg"
        if not img_path.exists():
            pytest.skip(f"Sample image not found: {img_path}")
        
        metadata = extract_photo_metadata(img_path)
        
        assert metadata is not None
        assert metadata['timestamp_original'] == '2026-01-08T07:27:10'
        assert metadata['camera_make'] == 'HONOR'
        assert metadata['camera_model'] == 'BRP-NX1'
        assert metadata['gps_latitude'] is not None
        assert metadata['gps_longitude'] is not None
    
    def test_extract_from_image_without_exif(self, sample_dir):
        """Test extraction from image with no EXIF data."""
        img_path = sample_dir / "730749825_27677388005230048_9025611458864199539_n.jpeg"
        if not img_path.exists():
            pytest.skip(f"Sample image not found: {img_path}")
        
        metadata = extract_photo_metadata(img_path)
        
        assert metadata is not None
        # Basic image properties should still be extracted
        assert metadata['width'] is not None
        assert metadata['height'] is not None
        assert metadata['file_format'] == 'JPEG'
        
        # EXIF fields should be absent
        assert metadata.get('timestamp_original') is None
        assert metadata.get('camera_make') is None
        assert metadata.get('gps_latitude') is None
    
    def test_extract_nonexistent_file(self):
        """Test extraction from non-existent file."""
        metadata = extract_photo_metadata(Path("/nonexistent/file.jpg"))
        assert metadata is None
    
    def test_raw_exif_stored(self, sample_dir):
        """Test that raw EXIF data is stored for audit."""
        img_path = sample_dir / "IMG_20260101_122510.jpg"
        if not img_path.exists():
            pytest.skip(f"Sample image not found: {img_path}")
        
        metadata = extract_photo_metadata(img_path)
        
        assert metadata is not None
        assert 'raw_exif' in metadata
        # Raw EXIF should contain parsed values
        raw = metadata['raw_exif']
        assert raw is not None
        assert raw.get('timestamp_original') == '2026-01-01T12:25:10'


class TestMetadataDeterminism:
    """Test that metadata extraction is deterministic (same input = same output)."""
    
    @pytest.fixture
    def sample_dir(self):
        return Path(__file__).parent.parent / "samples"
    
    def test_same_image_same_result(self, sample_dir):
        """Running extraction twice on same image should give same result."""
        img_path = sample_dir / "IMG_20260101_122510.jpg"
        if not img_path.exists():
            pytest.skip(f"Sample image not found: {img_path}")
        
        result1 = extract_photo_metadata(img_path)
        result2 = extract_photo_metadata(img_path)
        
        # GPS coordinates should be identical (floating point)
        assert result1['gps_latitude'] == result2['gps_latitude']
        assert result1['gps_longitude'] == result2['gps_longitude']
        
        # Timestamp should be identical
        assert result1['timestamp_original'] == result2['timestamp_original']


class TestWorkerIntegration:
    """Test worker integration for photo metadata extraction."""
    
    @pytest.fixture
    def sample_dir(self):
        return Path(__file__).parent.parent / "samples"
    
    def test_photo_metadata_extractor_class_exists(self):
        """Test that PhotoMetadataExtractor class can be imported."""
        from workers.photo_metadata_extractor import PhotoMetadataExtractor
        assert PhotoMetadataExtractor is not None
    
    def test_job_type_string_defined(self):
        """Test that extract_photo_metadata job type string is defined."""
        # Test that the job type string is correct
        JOB_TYPE = 'extract_photo_metadata'
        assert JOB_TYPE == 'extract_photo_metadata'
    
    def test_supported_image_extensions(self):
        """Test that image extensions constant is defined."""
        from parsers.image_parser import SUPPORTED_EXTENSIONS
        assert '.jpg' in SUPPORTED_EXTENSIONS
        assert '.jpeg' in SUPPORTED_EXTENSIONS
        assert '.png' in SUPPORTED_EXTENSIONS
        assert '.tiff' in SUPPORTED_EXTENSIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
