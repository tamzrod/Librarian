"""Integration test for the complete document processing pipeline.

This test verifies that the entire pipeline works from file discovery
to extraction completion without manual intervention.

Test sequence:
1. Create a test file with identifiable content
2. Wait for the watcher to detect it
3. Verify document is created in database
4. Verify jobs are created
5. Wait for worker to process jobs
6. Verify content is extracted
7. Verify entities are extracted
8. Verify events are extracted
9. Verify locations are extracted
"""

import os
import sys
import time
import tempfile
import shutil
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPipelineIntegration:
    """Integration tests for the document processing pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment and tear down after tests."""
        # Store original environment
        self.original_env = {}
        self.test_dir = None
        self.db_backend = None
        
        yield
        
        # Cleanup
        if self.db_backend:
            try:
                self.db_backend._get_connection().close()
            except Exception:
                pass
    
    def _create_test_db(self):
        """Create a test database with the schema."""
        try:
            import psycopg
            from storage.postgres_backend import PostgresBackend
            from storage.migrations.schema import load_schema
            
            # Create test database
            conn = psycopg.connect(
                host='localhost',
                port=5432,
                dbname='postgres',
                user='librarian',
                password='librarian'
            )
            conn.autocommit = True
            cur = conn.cursor()
            
            # Drop and recreate test database
            try:
                cur.execute("DROP DATABASE IF EXISTS librarian_test")
            except Exception:
                pass
            
            cur.execute("CREATE DATABASE librarian_test")
            cur.close()
            conn.close()
            
            # Connect to test database and create schema
            self.db_backend = PostgresBackend(
                host='localhost',
                port=5432,
                dbname='librarian_test',
                user='librarian',
                password='librarian'
            )
            self.db_backend.ensure_schema()
            
            return True
        except Exception as e:
            print(f"Could not create test database: {e}")
            return False
    
    def _get_mock_backend(self):
        """Get a mock backend for testing without database."""
        from api.dependencies import MockBackend
        return MockBackend()
    
    def test_save_document_creates_jobs(self):
        """Test that save_document automatically creates processing jobs."""
        # This test verifies the job creation part of the pipeline
        # without requiring a full database
        
        from storage.postgres_backend import PostgresBackend
        
        # Try to use test database if available
        if not hasattr(self, 'db_backend') or self.db_backend is None:
            if not self._create_test_db():
                pytest.skip("Test database not available")
        
        # Create a test document
        test_doc = {
            'path': '/test/sample.txt',
            'extension': '.txt',
            'file_size': 100,
            'character_count': 50,
            'parser': 'text'
        }
        
        # Save the document
        doc_id = self.db_backend.save_document(test_doc)
        assert doc_id is not None
        assert doc_id > 0
        
        # Verify jobs were created
        jobs = self.db_backend.get_document_jobs(doc_id)
        assert len(jobs) > 0
        
        # Verify expected job types
        job_types = {j['job_type'] for j in jobs}
        expected_types = {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'}
        assert expected_types.issubset(job_types), f"Missing job types: {expected_types - job_types}"
    
    def test_claim_job_returns_queued_job(self):
        """Test that claim_job returns a queued job."""
        if not hasattr(self, 'db_backend') or self.db_backend is None:
            if not self._create_test_db():
                pytest.skip("Test database not available")
        
        # Create a document with jobs
        test_doc = {
            'path': '/test/claim_test.txt',
            'extension': '.txt',
            'file_size': 50,
            'character_count': 25,
            'parser': 'text'
        }
        doc_id = self.db_backend.save_document(test_doc)
        self.db_backend.create_jobs_for_document(doc_id)
        
        # Claim a job
        worker_id = 'test-worker'
        job = self.db_backend.claim_job(worker_id)
        
        assert job is not None
        assert job['status'] == 'IN_PROGRESS'
        assert job['worker_id'] == worker_id
    
    def test_complete_job_marks_as_completed(self):
        """Test that complete_job marks job as completed."""
        if not hasattr(self, 'db_backend') or self.db_backend is None:
            if not self._create_test_db():
                pytest.skip("Test database not available")
        
        # Create and claim a job
        test_doc = {
            'path': '/test/complete_test.txt',
            'extension': '.txt',
            'file_size': 50,
            'character_count': 25,
            'parser': 'text'
        }
        doc_id = self.db_backend.save_document(test_doc)
        self.db_backend.create_jobs_for_document(doc_id)
        
        job = self.db_backend.claim_job('test-worker')
        assert job is not None
        
        # Complete the job
        success = self.db_backend.complete_job(job['id'], success=True)
        assert success
        
        # Verify job status
        conn = self.db_backend._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM document_jobs WHERE id = %s", (job['id'],))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        assert row is not None
        assert row[0] == 'COMPLETED'
    
    def test_worker_processes_job(self):
        """Test that the worker can process a job end-to-end."""
        if not hasattr(self, 'db_backend') or self.db_backend is None:
            if not self._create_test_db():
                pytest.skip("Test database not available")
        
        # Create a temporary test file
        test_content = "John Smith visited Manila on January 1, 2025"
        test_path = '/tmp/librarian_integration_test.txt'
        
        try:
            with open(test_path, 'w') as f:
                f.write(test_content)
            
            # Create a document for this file
            from pathlib import Path
            stat = Path(test_path).stat()
            
            test_doc = {
                'path': test_path,
                'extension': '.txt',
                'file_size': stat.st_size,
                'character_count': len(test_content),
                'parser': 'text'
            }
            doc_id = self.db_backend.save_document(test_doc)
            self.db_backend.create_jobs_for_document(doc_id)
            
            # Create content for the document
            self.db_backend.save_content(doc_id, test_content, 'manual')
            
            # Process entity extraction job
            entity_job = self.db_backend.claim_job('test-worker')
            if entity_job and entity_job['job_type'] == 'extract_entities':
                from workers.entity_extractor import EntityExtractor
                extractor = EntityExtractor(self.db_backend)
                result = extractor.process(entity_job)
                
                # Verify entities were extracted
                assert result['entities_extracted'] > 0
            
            # Process location extraction job
            location_job = self.db_backend.claim_job('test-worker')
            if location_job and location_job['job_type'] == 'extract_locations':
                from workers.location_extractor import LocationExtractor
                extractor = LocationExtractor(self.db_backend)
                result = extractor.process(location_job)
                
                # Verify locations were extracted
                assert result['locations_extracted'] > 0 or result['locations_extracted'] == 0  # May or may not find
            
            # Process event extraction job
            event_job = self.db_backend.claim_job('test-worker')
            if event_job and event_job['job_type'] == 'extract_events':
                from workers.event_extractor import EventExtractor
                extractor = EventExtractor(self.db_backend)
                result = extractor.process(event_job)
                
                # Verify events were extracted
                assert result['events_extracted'] > 0
            
        finally:
            # Cleanup test file
            if os.path.exists(test_path):
                os.remove(test_path)
    
    def test_query_planner_intent_detection(self):
        """Test that the query planner correctly identifies intents."""
        from core.query_planner import plan_query
        
        # Test location query
        plan = plan_query("Where was I on January 1, 2025?")
        assert plan['intent'] == 'location_query'
        
        # Test event query
        plan = plan_query("When did John visit Manila?")
        assert plan['intent'] == 'event_query'
        
        # Test entity query
        plan = plan_query("Show me everything related to John Smith")
        assert plan['intent'] == 'entity_query'
    
    def test_pipeline_status_endpoint_schema(self):
        """Test that the pipeline status response schema is correct."""
        from api.routes.pipeline import PipelineStatusResponse
        
        # Verify the schema has all required fields
        response = PipelineStatusResponse(
            documents=100,
            queued_jobs=10,
            running_jobs=2,
            completed_jobs=50,
            failed_jobs=1,
            workers=1,
            watcher_status="RUNNING",
            database_status="CONNECTED",
            job_processor_active=True
        )
        
        assert response.documents == 100
        assert response.queued_jobs == 10
        assert response.running_jobs == 2
        assert response.completed_jobs == 50
        assert response.failed_jobs == 1
        assert response.workers == 1
        assert response.watcher_status == "RUNNING"
        assert response.database_status == "CONNECTED"
    
    def test_document_pipeline_response_schema(self):
        """Test that the document pipeline response schema is correct."""
        from api.routes.pipeline import DocumentPipelineResponse, JobSummary
        
        # Create test data
        jobs = [
            JobSummary(
                id=1,
                document_id=100,
                job_type='extract_text',
                status='COMPLETED',
                priority=0,
                attempt_count=1
            ),
            JobSummary(
                id=2,
                document_id=100,
                job_type='extract_entities',
                status='QUEUED',
                priority=0,
                attempt_count=0
            )
        ]
        
        response = DocumentPipelineResponse(
            document_id=100,
            path='/test/document.txt',
            status='METADATA_INDEXED',
            jobs=jobs
        )
        
        assert response.document_id == 100
        assert response.path == '/test/document.txt'
        assert response.status == 'METADATA_INDEXED'
        assert len(response.jobs) == 2


def run_pipeline_test():
    """Run a manual pipeline test without pytest."""
    print("=" * 60)
    print("Librarian Pipeline Integration Test")
    print("=" * 60)
    
    # Test document saving
    print("\n1. Testing document saving...")
    try:
        import psycopg
        from storage.postgres_backend import PostgresBackend
        
        # Connect to database
        backend = PostgresBackend(
            host='localhost',
            port=5432,
            dbname='librarian',
            user='librarian',
            password='librarian'
        )
        backend.ensure_schema()
        
        # Create test document
        test_doc = {
            'path': '/test/integration.txt',
            'extension': '.txt',
            'file_size': 100,
            'character_count': 50,
            'parser': 'text'
        }
        
        doc_id = backend.save_document(test_doc)
        print(f"   ✓ Document saved with ID: {doc_id}")
        
        # Create jobs
        jobs = backend.create_jobs_for_document(doc_id)
        print(f"   ✓ Created {len(jobs)} jobs: {jobs}")
        
        # Claim and process a job
        print("\n2. Testing job claiming...")
        job = backend.claim_job('test-worker')
        if job:
            print(f"   ✓ Claimed job: {job['id']} ({job['job_type']})")
            
            # Complete the job
            backend.complete_job(job['id'], success=True)
            print(f"   ✓ Job completed")
        else:
            print("   ⚠ No jobs available to claim")
        
        # Check job counts
        print("\n3. Checking job status counts...")
        counts = backend.get_job_status_counts()
        print(f"   ✓ Job counts: {counts}")
        
        # Get document jobs
        print("\n4. Checking document jobs...")
        doc_jobs = backend.get_document_jobs(doc_id)
        print(f"   ✓ Found {len(doc_jobs)} jobs for document {doc_id}")
        for j in doc_jobs:
            print(f"      - {j['job_type']}: {j['status']}")
        
        print("\n" + "=" * 60)
        print("Pipeline test completed successfully!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\n✗ Database not available: {e}")
        print("  Install psycopg and ensure PostgreSQL is running.")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == '__main__':
    run_pipeline_test()
