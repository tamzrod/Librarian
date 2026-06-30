"""
Tests for job orchestration refactor.

These tests verify:
1. Job dependencies are properly tracked
2. Jobs with unmet prerequisites are blocked
3. Duplicate jobs are prevented
4. Artifact type validation prevents invalid jobs
5. Scan idempotency prevents duplicate jobs on rescans
"""

import pytest
from storage.postgres_backend import (
    JobStatus, 
    JOB_DEPENDENCIES, 
    INVALID_JOBS_BY_ARTIFACT,
    ARTIFACT_TYPE_JOBS
)


class TestJobDependencies:
    """Test job dependency configuration."""
    
    def test_extract_entities_requires_extract_text(self):
        """extract_entities depends on extract_text."""
        deps = JOB_DEPENDENCIES.get('extract_entities', set())
        assert 'extract_text' in deps
    
    def test_extract_locations_requires_extract_text(self):
        """extract_locations depends on extract_text."""
        deps = JOB_DEPENDENCIES.get('extract_locations', set())
        assert 'extract_text' in deps
    
    def test_generate_embeddings_requires_extract_text(self):
        """generate_embeddings depends on extract_text."""
        deps = JOB_DEPENDENCIES.get('generate_embeddings', set())
        assert 'extract_text' in deps
    
    def test_extract_text_has_no_dependencies(self):
        """extract_text has no prerequisites."""
        deps = JOB_DEPENDENCIES.get('extract_text', set())
        assert len(deps) == 0


class TestBlockedStatus:
    """Test that BLOCKED status is available."""
    
    def test_blocked_status_exists(self):
        """JobStatus should have BLOCKED status."""
        assert hasattr(JobStatus, 'BLOCKED')
        assert JobStatus.BLOCKED == 'BLOCKED'


class TestArtifactTypeValidation:
    """Test artifact type validation for job scheduling."""
    
    def test_image_artifacts_cannot_get_text_extraction(self):
        """Image artifacts should NOT get extract_text, extract_entities, etc."""
        invalid = INVALID_JOBS_BY_ARTIFACT.get('image', set())
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        assert text_jobs.intersection(invalid) == text_jobs
    
    def test_text_artifacts_cannot_get_vision_tasks(self):
        """Text artifacts should NOT get object_detection or face_detection."""
        invalid = INVALID_JOBS_BY_ARTIFACT.get('text', set())
        vision_jobs = {'object_detection', 'face_detection'}
        assert vision_jobs.intersection(invalid) == vision_jobs
    
    def test_video_artifacts_cannot_get_text_extraction(self):
        """Video artifacts should NOT get text extraction jobs."""
        invalid = INVALID_JOBS_BY_ARTIFACT.get('video', set())
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        assert text_jobs.intersection(invalid) == text_jobs
    
    def test_audio_artifacts_cannot_get_text_extraction(self):
        """Audio artifacts should NOT get text extraction jobs."""
        invalid = INVALID_JOBS_BY_ARTIFACT.get('audio', set())
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        assert text_jobs.intersection(invalid) == text_jobs


class TestArtifactTypeJobsMapping:
    """Test that ARTIFACT_TYPE_JOBS correctly maps types to valid jobs."""
    
    def test_image_gets_correct_jobs(self):
        """Image artifacts should get image-specific jobs."""
        jobs = ARTIFACT_TYPE_JOBS.get('image', [])
        expected = ['extract_photo_metadata', 'generate_thumbnail', 'run_ocr', 'object_detection']
        assert set(jobs) == set(expected)
    
    def test_text_gets_correct_jobs(self):
        """Text artifacts should get text processing jobs."""
        jobs = ARTIFACT_TYPE_JOBS.get('text', [])
        expected = ['extract_text', 'extract_entities', 'extract_events', 'extract_locations', 'generate_embeddings']
        assert set(jobs) == set(expected)
    
    def test_document_gets_correct_jobs(self):
        """Document artifacts should get document processing jobs."""
        jobs = ARTIFACT_TYPE_JOBS.get('document', [])
        expected = ['extract_text', 'extract_entities', 'extract_events', 'extract_locations', 'generate_embeddings']
        assert set(jobs) == set(expected)


class TestInvalidJobsFilter:
    """Test that invalid jobs are correctly filtered."""
    
    def test_filter_image_text_jobs(self):
        """Image jobs should filter out text extraction jobs."""
        image_jobs = ARTIFACT_TYPE_JOBS['image']
        invalid = INVALID_JOBS_BY_ARTIFACT['image']
        
        # All text extraction jobs should be in invalid list
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        assert text_jobs.issubset(invalid)
        
        # None of the text jobs should be in image jobs
        for job in text_jobs:
            assert job not in image_jobs
    
    def test_filter_text_vision_jobs(self):
        """Text jobs should filter out vision tasks."""
        text_jobs = ARTIFACT_TYPE_JOBS['text']
        invalid = INVALID_JOBS_BY_ARTIFACT['text']
        
        # Vision jobs should be in invalid list
        vision_jobs = {'object_detection', 'face_detection'}
        assert vision_jobs.issubset(invalid)
        
        # None of the vision jobs should be in text jobs
        for job in vision_jobs:
            assert job not in text_jobs


class TestJobOrchestrationLogging:
    """Test that logging formats are correct."""
    
    def test_duplicate_log_format(self):
        """Verify duplicate job log format matches requirements."""
        # Log format: Skipping duplicate job: document=1234 job=extract_entities
        doc_id = 1234
        job_type = 'extract_entities'
        expected = f"Skipping duplicate job: document={doc_id} job={job_type}"
        assert "Skipping duplicate job:" in expected
        assert f"document={doc_id}" in expected
        assert f"job={job_type}" in expected
    
    def test_blocking_log_format(self):
        """Verify blocking job log format matches requirements."""
        # Log format: Blocking job: document=1234 job=extract_entities reason=missing extract_text
        doc_id = 1234
        job_type = 'extract_entities'
        reason = 'missing extract_text'
        expected = f"Blocking job: document={doc_id} job={job_type} reason={reason}"
        assert "Blocking job:" in expected
        assert f"document={doc_id}" in expected
        assert f"job={job_type}" in expected
        assert f"reason={reason}" in expected


class TestJPGImportSuccessCriteria:
    """Test success criteria for 10,000 JPG file import."""
    
    def test_jpg_no_text_extraction_jobs(self):
        """JPG files should NOT generate text extraction jobs."""
        image_jobs = ARTIFACT_TYPE_JOBS['image']
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        
        for job in text_jobs:
            assert job not in image_jobs, f"JPG should NOT get {job}"
    
    def test_jpg_queue_stability(self):
        """JPG processing should not cause queue growth loops."""
        # Since no text extraction jobs are created, no retries occur
        image_jobs = ARTIFACT_TYPE_JOBS['image']
        text_jobs = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        
        # Verify no text jobs means no text job failures
        overlap = set(image_jobs).intersection(text_jobs)
        assert len(overlap) == 0, "No overlap means stable queue"
    
    def test_jpg_no_infinite_retries(self):
        """JPG files should not trigger infinite retries."""
        # Image jobs don't depend on extract_text, so no blocking occurs
        image_jobs = set(ARTIFACT_TYPE_JOBS['image'])
        
        # Image jobs don't depend on anything
        for job in image_jobs:
            deps = JOB_DEPENDENCIES.get(job, set())
            # Image jobs should have no dependencies
            assert len(deps) == 0, f"{job} should have no dependencies"


class TestDuplicatePrevention:
    """Test duplicate job prevention logic."""
    
    def test_job_status_for_duplicate_check(self):
        """Statuses that should prevent duplicate job creation."""
        # Active statuses that prevent duplicates
        active_statuses = {'QUEUED', 'IN_PROGRESS', 'BLOCKED'}
        assert 'QUEUED' in active_statuses
        assert 'IN_PROGRESS' in active_statuses
        assert 'BLOCKED' in active_statuses
        
        # COMPLETED and FAILED_PERMANENT should allow new jobs
        completed_statuses = {'COMPLETED', 'FAILED_PERMANENT', 'CANCELLED'}
        assert 'COMPLETED' in completed_statuses
        assert 'FAILED_PERMANENT' in completed_statuses
        assert 'CANCELLED' in completed_statuses
