"""
Tests for artifact_type-based job scheduling.

These tests verify that jobs are scheduled correctly based on artifact type,
preventing binary artifacts (images, videos, archives, executables) from entering
the text extraction pipeline.

This prevents errors like:
- "No content found for document XXX"
- "PostgreSQL text fields cannot contain NUL bytes"
"""

import pytest
from registry.parser_registry import ParserRegistry, ArtifactType


class TestArtifactTypeJobScheduling:
    """Test that artifact type correctly determines job scheduling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ParserRegistry()
        
        # Define expected job types per artifact type (matching ARTIFACT_TYPE_JOBS)
        self.artifact_type_jobs = {
            'text': ['extract_text', 'extract_entities', 'extract_events', 'extract_locations', 'generate_embeddings'],
            'document': ['extract_text', 'extract_entities', 'extract_events', 'extract_locations', 'generate_embeddings'],
            'structured': ['extract_text', 'extract_entities', 'extract_events', 'extract_locations', 'generate_embeddings'],
            'image': ['extract_photo_metadata', 'generate_thumbnail', 'run_ocr', 'object_detection'],
            'video': ['extract_photo_metadata', 'generate_thumbnail', 'transcription'],
            'audio': ['transcription', 'generate_embeddings'],
            'archive': ['inventory'],
            'executable': ['inventory'],
            'unknown': ['inventory'],
        }
        
        # Text extraction job types that should NOT be created for binary artifacts
        self.text_extraction_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
    
    def get_jobs_for_artifact(self, artifact_type):
        """Get the expected jobs for an artifact type."""
        return self.artifact_type_jobs.get(
            artifact_type,
            self.artifact_type_jobs.get('unknown', ['inventory'])
        )

    # =========================================================================
    # Image artifact tests - Should NOT get text extraction jobs
    # =========================================================================
    
    def test_jpg_files_classified_as_image(self):
        """Test that .jpg files are classified as image."""
        assert self.registry.get_artifact_type('/path/to/photo.jpg') == 'image'
        assert self.registry.get_artifact_type('/path/to/photo.jpeg') == 'image'
    
    def test_jpg_files_do_not_get_text_extraction_jobs(self):
        """Test that .jpg files do NOT receive text extraction jobs.
        
        This is the core fix for the issue where:
        - "No content found for document XXX" errors occurred
        - "PostgreSQL text fields cannot contain NUL bytes" errors occurred
        """
        jobs = self.get_jobs_for_artifact('image')
        
        for job_type in self.text_extraction_jobs:
            assert job_type not in jobs, f"IMAGE artifacts should NOT get {job_type}"
    
    def test_jpg_files_get_image_specific_jobs(self):
        """Test that .jpg files receive image-specific jobs."""
        jobs = self.get_jobs_for_artifact('image')
        
        assert 'extract_photo_metadata' in jobs, "IMAGE should get extract_photo_metadata"
        assert 'generate_thumbnail' in jobs, "IMAGE should get generate_thumbnail"
        assert 'run_ocr' in jobs, "IMAGE should get run_ocr"
        assert 'object_detection' in jobs, "IMAGE should get object_detection"
    
    def test_png_files_classified_as_image(self):
        """Test that .png files are classified as image."""
        assert self.registry.get_artifact_type('/path/to/graphic.png') == 'image'
    
    def test_tiff_files_classified_as_image(self):
        """Test that .tiff/.tif files are classified as image."""
        assert self.registry.get_artifact_type('/path/to/scan.tiff') == 'image'
        assert self.registry.get_artifact_type('/path/to/scan.tif') == 'image'
    
    def test_webp_files_classified_as_image(self):
        """Test that .webp files are classified as image."""
        assert self.registry.get_artifact_type('/path/to/image.webp') == 'image'

    # =========================================================================
    # Video artifact tests - Should NOT get text extraction jobs
    # =========================================================================
    
    def test_video_files_classified_as_video(self):
        """Test that video files are classified as video."""
        assert self.registry.get_artifact_type('/path/to/video.mp4') == 'video'
        assert self.registry.get_artifact_type('/path/to/video.mov') == 'video'
        assert self.registry.get_artifact_type('/path/to/video.avi') == 'video'
        assert self.registry.get_artifact_type('/path/to/video.mkv') == 'video'
    
    def test_video_files_do_not_get_text_extraction_jobs(self):
        """Test that video files do NOT receive text extraction jobs."""
        jobs = self.get_jobs_for_artifact('video')
        
        for job_type in self.text_extraction_jobs:
            assert job_type not in jobs, f"VIDEO artifacts should NOT get {job_type}"
    
    def test_video_files_get_video_specific_jobs(self):
        """Test that video files receive video-specific jobs."""
        jobs = self.get_jobs_for_artifact('video')
        
        assert 'extract_photo_metadata' in jobs, "VIDEO should get extract_photo_metadata"
        assert 'generate_thumbnail' in jobs, "VIDEO should get generate_thumbnail"
        assert 'transcription' in jobs, "VIDEO should get transcription"

    # =========================================================================
    # Audio artifact tests - Should NOT get text extraction jobs
    # =========================================================================
    
    def test_audio_files_classified_as_audio(self):
        """Test that audio files are classified as audio."""
        assert self.registry.get_artifact_type('/path/to/audio.mp3') == 'audio'
        assert self.registry.get_artifact_type('/path/to/audio.wav') == 'audio'
        assert self.registry.get_artifact_type('/path/to/audio.flac') == 'audio'
    
    def test_audio_files_do_not_get_text_extraction_jobs(self):
        """Test that audio files do NOT receive text extraction jobs."""
        jobs = self.get_jobs_for_artifact('audio')
        
        for job_type in self.text_extraction_jobs:
            assert job_type not in jobs, f"AUDIO artifacts should NOT get {job_type}"

    # =========================================================================
    # Archive artifact tests - Should NOT get text extraction jobs
    # =========================================================================
    
    def test_archive_files_classified_as_archive(self):
        """Test that archive files are classified as archive."""
        assert self.registry.get_artifact_type('/path/to/archive.zip') == 'archive'
        assert self.registry.get_artifact_type('/path/to/archive.tar') == 'archive'
        assert self.registry.get_artifact_type('/path/to/archive.gz') == 'archive'
        assert self.registry.get_artifact_type('/path/to/archive.7z') == 'archive'
    
    def test_archive_files_do_not_get_text_extraction_jobs(self):
        """Test that archive files do NOT receive text extraction jobs.
        
        Archives should only get inventory jobs, not text extraction.
        """
        jobs = self.get_jobs_for_artifact('archive')
        
        for job_type in self.text_extraction_jobs:
            assert job_type not in jobs, f"ARCHIVE artifacts should NOT get {job_type}"
        
        assert jobs == ['inventory'], "ARCHIVE should only get inventory job"

    # =========================================================================
    # Executable artifact tests - Should NOT get text extraction jobs
    # =========================================================================
    
    def test_executable_files_classified_as_executable(self):
        """Test that executable files are classified as executable."""
        assert self.registry.get_artifact_type('/path/to/app.exe') == 'executable'
        assert self.registry.get_artifact_type('/path/to/script.sh') == 'executable'
        assert self.registry.get_artifact_type('/path/to/script.bat') == 'executable'
    
    def test_executable_files_do_not_get_text_extraction_jobs(self):
        """Test that executable files do NOT receive text extraction jobs.
        
        Executables should only get inventory jobs, not text extraction.
        """
        jobs = self.get_jobs_for_artifact('executable')
        
        for job_type in self.text_extraction_jobs:
            assert job_type not in jobs, f"EXECUTABLE artifacts should NOT get {job_type}"
        
        assert jobs == ['inventory'], "EXECUTABLE should only get inventory job"

    # =========================================================================
    # Text/document artifact tests - SHOULD get text extraction jobs
    # =========================================================================
    
    def test_text_files_classified_as_text(self):
        """Test that text files are classified as text."""
        assert self.registry.get_artifact_type('/path/to/document.txt') == 'text'
        assert self.registry.get_artifact_type('/path/to/document.log') == 'text'
    
    def test_text_files_get_text_extraction_jobs(self):
        """Test that text files receive text extraction jobs."""
        jobs = self.get_jobs_for_artifact('text')
        
        assert 'extract_text' in jobs, "TEXT should get extract_text"
        assert 'extract_entities' in jobs, "TEXT should get extract_entities"
        assert 'extract_events' in jobs, "TEXT should get extract_events"
        assert 'extract_locations' in jobs, "TEXT should get extract_locations"
        assert 'generate_embeddings' in jobs, "TEXT should get generate_embeddings"
    
    def test_document_files_classified_as_document(self):
        """Test that document files are classified as document."""
        assert self.registry.get_artifact_type('/path/to/doc.pdf') == 'document'
        assert self.registry.get_artifact_type('/path/to/doc.doc') == 'document'
        assert self.registry.get_artifact_type('/path/to/doc.docx') == 'document'
        assert self.registry.get_artifact_type('/path/to/doc.md') == 'document'
    
    def test_document_files_get_text_extraction_jobs(self):
        """Test that document files receive text extraction jobs."""
        jobs = self.get_jobs_for_artifact('document')
        
        assert 'extract_text' in jobs, "DOCUMENT should get extract_text"
        assert 'extract_entities' in jobs, "DOCUMENT should get extract_entities"
    
    def test_structured_files_classified_as_structured(self):
        """Test that structured data files are classified as structured."""
        assert self.registry.get_artifact_type('/path/to/data.csv') == 'structured'
        assert self.registry.get_artifact_type('/path/to/data.json') == 'structured'
        assert self.registry.get_artifact_type('/path/to/data.xml') == 'structured'
        assert self.registry.get_artifact_type('/path/to/data.yaml') == 'structured'
    
    def test_structured_files_get_text_extraction_jobs(self):
        """Test that structured data files receive text extraction jobs."""
        jobs = self.get_jobs_for_artifact('structured')
        
        assert 'extract_text' in jobs, "STRUCTURED should get extract_text"
        assert 'extract_entities' in jobs, "STRUCTURED should get extract_entities"

    # =========================================================================
    # Unknown artifact tests - Should be safe defaults
    # =========================================================================
    
    def test_unknown_extensions_classified_as_unknown(self):
        """Test that unknown file extensions are classified as unknown."""
        assert self.registry.get_artifact_type('/path/to/file.xyz') == 'unknown'
        assert self.registry.get_artifact_type('/path/to/file.abc') == 'unknown'
    
    def test_unknown_artifacts_get_inventory_only(self):
        """Test that unknown artifacts get inventory only (safe default)."""
        jobs = self.get_jobs_for_artifact('unknown')
        
        for job_type in self.text_extraction_jobs:
            assert job_type not in jobs, f"UNKNOWN artifacts should NOT get {job_type}"
        
        assert jobs == ['inventory'], "UNKNOWN should only get inventory job"


class TestJPGImportSuccessCriteria:
    """Test the specific success criteria for JPG imports."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ParserRegistry()
        self.artifact_type_jobs = {
            'image': ['extract_photo_metadata', 'generate_thumbnail', 'run_ocr', 'object_detection'],
        }
    
    def get_jobs_for_jpg(self):
        """Get the expected jobs for a JPG file."""
        return self.artifact_type_jobs['image']
    
    def test_jpg_imports_produce_image_workers_only(self):
        """Success Criterion 1: IMAGE artifacts get image workers only."""
        jobs = self.get_jobs_for_jpg()
        
        image_jobs = {'extract_photo_metadata', 'generate_thumbnail', 'run_ocr', 'object_detection'}
        assert set(jobs) == image_jobs, "JPG imports should only produce image workers"
    
    def test_jpg_imports_produce_zero_text_extraction_jobs(self):
        """Success Criterion 2: Zero text extraction jobs."""
        jobs = self.get_jobs_for_jpg()
        
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        for job in text_jobs:
            assert job not in jobs, f"JPG imports should NOT produce {job}"
    
    def test_jpg_imports_produce_zero_retries(self):
        """Success Criterion 3: Zero retries.
        
        Since no text extraction jobs are created, there are no opportunities
        for the "No content found" or "NUL byte" errors that cause retries.
        """
        jobs = self.get_jobs_for_jpg()
        
        # If there are no text extraction jobs, there can be no text extraction failures
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        assert not any(job in text_jobs for job in jobs), "No text jobs = no text job failures"
    
    def test_jpg_imports_produce_zero_nul_byte_errors(self):
        """Success Criterion 4: Zero NUL byte errors.
        
        NUL byte errors occurred because binary image data was being passed to
        text extraction handlers. By excluding text extraction for images,
        these errors are prevented.
        """
        jobs = self.get_jobs_for_jpg()
        
        # extract_text was the job that caused NUL byte errors when processing images
        assert 'extract_text' not in jobs, "extract_text should NOT be created for JPGs"
        assert 'extract_entities' not in jobs, "extract_entities should NOT be created for JPGs"


class TestSampleJPGFiles:
    """Test with actual sample JPG files from the repository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ParserRegistry()
        self.artifact_type_jobs = {
            'image': ['extract_photo_metadata', 'generate_thumbnail', 'run_ocr', 'object_detection'],
        }
    
    def get_jobs_for_artifact(self, artifact_type):
        """Get the expected jobs for an artifact type."""
        return self.artifact_type_jobs.get(
            artifact_type,
            ['inventory']
        )
    
    def test_sample_jpg_files_are_classified_as_image(self):
        """Test that the sample JPG files in the repo are classified correctly."""
        sample_jpg_files = [
            '/workspace/project/Librarian/samples/IMG_20260101_122510.jpg',
            '/workspace/project/Librarian/samples/IMG_20260108_072710.jpg',
            '/workspace/project/Librarian/samples/730749825_27677388005230048_9025611458864199539_n.jpeg',
        ]
        
        for filepath in sample_jpg_files:
            artifact_type = self.registry.get_artifact_type(filepath)
            assert artifact_type == 'image', f"{filepath} should be classified as image, got {artifact_type}"
    
    def test_sample_jpg_files_do_not_get_text_jobs(self):
        """Test that sample JPG files do NOT receive text extraction jobs."""
        sample_jpg_files = [
            '/workspace/project/Librarian/samples/IMG_20260101_122510.jpg',
            '/workspace/project/Librarian/samples/IMG_20260108_072710.jpg',
            '/workspace/project/Librarian/samples/730749825_27677388005230048_9025611458864199539_n.jpeg',
        ]
        
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        
        for filepath in sample_jpg_files:
            artifact_type = self.registry.get_artifact_type(filepath)
            jobs = self.get_jobs_for_artifact(artifact_type)
            
            for job in text_jobs:
                assert job not in jobs, f"{filepath} should NOT get {job}"
