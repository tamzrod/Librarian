"""
Integration tests for Evidence Timeline API (Phase 1B).

Tests the REST API endpoints for timeline data.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTimelineRouterImports:
    """Tests that timeline router can be imported."""
    
    def test_timeline_router_imports(self):
        """Test that timeline router module can be imported."""
        from api.routes import timeline
        assert timeline.router is not None
        assert hasattr(timeline, 'get_timeline_stats')
        assert hasattr(timeline, 'list_photos')
        assert hasattr(timeline, 'get_map_markers')
        assert hasattr(timeline, 'get_photo')


class TestTimelineResponseModels:
    """Tests for response models."""
    
    def test_photo_summary_model(self):
        """Test PhotoSummary model."""
        from api.routes.timeline import PhotoSummary
        
        photo = PhotoSummary(
            document_id=1,
            filename="test.jpg",
            timestamp="2026-01-01T12:00:00Z",
            camera_make="Test",
            camera_model="Camera1",
            gps_latitude=14.5,
            gps_longitude=121.0
        )
        
        assert photo.document_id == 1
        assert photo.filename == "test.jpg"
        assert photo.gps_latitude == 14.5
    
    def test_photo_map_marker_model(self):
        """Test PhotoMapMarker model."""
        from api.routes.timeline import PhotoMapMarker
        
        marker = PhotoMapMarker(
            document_id=1,
            latitude=14.635189,
            longitude=121.092548,
            timestamp="2026-01-01T12:25:10Z",
            camera="HONOR BRP-NX1",
            filename="IMG_001.jpg"
        )
        
        assert marker.latitude == 14.635189
        assert marker.longitude == 121.092548
        assert marker.camera == "HONOR BRP-NX1"
    
    def test_timeline_stats_model(self):
        """Test TimelineStats model."""
        from api.routes.timeline import TimelineStats
        
        stats = TimelineStats(
            photos_total=127,
            gps_tagged=98,
            unique_cameras=4,
            first_photo_timestamp="2025-01-15T09:42:18Z",
            last_photo_timestamp="2026-06-30T14:32:10Z"
        )
        
        assert stats.photos_total == 127
        assert stats.gps_tagged == 98
        assert stats.unique_cameras == 4
    
    def test_photo_detail_model(self):
        """Test PhotoDetail model."""
        from api.routes.timeline import PhotoDetail
        
        detail = PhotoDetail(
            document_id=1,
            filename="IMG_001.jpg",
            timestamp="2026-01-01T12:25:10Z",
            gps_latitude=14.635189,
            gps_longitude=121.092548,
            gps_altitude=-57.2,
            camera_make="HONOR",
            camera_model="BRP-NX1",
            lens_model=None,
            width=3000,
            height=4000,
            orientation=1,
            file_format="JPEG",
            extracted_at="2026-06-30T14:32:10Z"
        )
        
        assert detail.width == 3000
        assert detail.height == 4000
        assert detail.file_format == "JPEG"


class TestPhotoMetadataExtraction:
    """Integration tests using real image extraction."""
    
    def test_extract_from_geotagged_sample(self):
        """Test extraction from sample geotagged image."""
        from parsers.image_parser import extract_photo_metadata
        
        sample_path = Path(__file__).parent.parent / 'samples' / 'IMG_20260101_122510.jpg'
        if not sample_path.exists():
            pytest.skip(f"Sample image not found: {sample_path}")
        
        metadata = extract_photo_metadata(sample_path)
        
        assert metadata is not None
        assert metadata['gps_latitude'] is not None
        assert metadata['gps_longitude'] is not None
        assert metadata['timestamp_original'] is not None
        
        # Verify data format matches API expectations
        assert isinstance(metadata['gps_latitude'], float)
        assert isinstance(metadata['gps_longitude'], float)
    
    def test_extract_second_geotagged_sample(self):
        """Test extraction from another geotagged image."""
        from parsers.image_parser import extract_photo_metadata
        
        sample_path = Path(__file__).parent.parent / 'samples' / 'IMG_20260108_072710.jpg'
        if not sample_path.exists():
            pytest.skip(f"Sample image not found: {sample_path}")
        
        metadata = extract_photo_metadata(sample_path)
        
        assert metadata is not None
        assert metadata['timestamp_original'] == '2026-01-08T07:27:10'
        assert metadata['gps_latitude'] is not None
        assert metadata['gps_longitude'] is not None
    
    def test_extract_nonexistent_returns_none(self):
        """Test that extraction from nonexistent file returns None."""
        from parsers.image_parser import extract_photo_metadata
        
        result = extract_photo_metadata(Path('/nonexistent/file.jpg'))
        assert result is None
    
    def test_extract_image_without_exif(self):
        """Test extraction from image without EXIF data."""
        from parsers.image_parser import extract_photo_metadata
        
        sample_path = Path(__file__).parent.parent / 'samples' / '730749825_27677388005230048_9025611458864199539_n.jpeg'
        if not sample_path.exists():
            pytest.skip(f"Sample image not found: {sample_path}")
        
        metadata = extract_photo_metadata(sample_path)
        
        assert metadata is not None
        # Basic properties should still be extracted
        assert metadata['width'] is not None
        assert metadata['height'] is not None
        # EXIF fields should be absent
        assert metadata.get('timestamp_original') is None
        assert metadata.get('gps_latitude') is None


class TestBackendQueryMethods:
    """Test that backend query methods exist (signature tests)."""
    
    def test_backend_has_timeline_stats_method(self):
        """Test that PostgresBackend has get_timeline_stats method."""
        # Read source file directly to avoid psycopg import
        with open('/workspace/project/Librarian/storage/postgres_backend.py', 'r') as f:
            source = f.read()
        assert 'def get_timeline_stats' in source
    
    def test_backend_has_search_photo_metadata_method(self):
        """Test that PostgresBackend has search_photo_metadata method."""
        with open('/workspace/project/Librarian/storage/postgres_backend.py', 'r') as f:
            source = f.read()
        assert 'def search_photo_metadata' in source
    
    def test_backend_has_get_photos_with_gps_method(self):
        """Test that PostgresBackend has get_photos_with_gps method."""
        with open('/workspace/project/Librarian/storage/postgres_backend.py', 'r') as f:
            source = f.read()
        assert 'def get_photos_with_gps' in source
    
    def test_backend_has_get_photo_metadata_method(self):
        """Test that PostgresBackend has get_photo_metadata method."""
        with open('/workspace/project/Librarian/storage/postgres_backend.py', 'r') as f:
            source = f.read()
        assert 'def get_photo_metadata' in source


class TestAPIEndpointPaths:
    """Test that API endpoints are properly defined."""
    
    def test_timeline_router_prefix(self):
        """Test timeline router uses correct prefix."""
        from api.routes import timeline
        
        # Check that routes are defined (paths include the /timeline prefix)
        routes = [r.path for r in timeline.router.routes]
        assert '/timeline/stats' in routes
        assert '/timeline/photos' in routes
        assert '/timeline/map' in routes
        assert '/timeline/photo/{document_id}' in routes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
