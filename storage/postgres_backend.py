import os
import logging
from datetime import datetime, timezone
import psycopg
from .backend import StorageBackend

logger = logging.getLogger(__name__)


def _to_postgres_timestamp(value) -> datetime:
    """
    Convert various timestamp representations to PostgreSQL-compatible datetime.
    
    Handles:
    - Unix epoch float (e.g., 1751188142.314672)
    - datetime object
    - ISO format string
    - None (returns None)
    
    Returns:
        datetime object in UTC, or None if input is None/invalid
    """
    if value is None:
        return None
    
    # Already a datetime
    if isinstance(value, datetime):
        # Ensure timezone-aware datetime is converted to UTC
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    
    # Unix epoch float
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).replace(tzinfo=None)
    
    # String - try parsing as float (epoch) or ISO format
    if isinstance(value, str):
        try:
            # Try as epoch float first
            epoch = float(value)
            return datetime.fromtimestamp(epoch, tz=timezone.utc).replace(tzinfo=None)
        except ValueError:
            # Try as ISO format
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt
            except ValueError:
                pass
    
    # Could not convert - return None
    logger.warning(f"Could not convert timestamp value: {value!r} (type: {type(value).__name__})")
    return None


class PostgresBackend(StorageBackend):
    def __init__(self, host='localhost', port=5432, dbname='librarian',
                 user='librarian', password='librarian'):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self._connection = None
        self._schema_verified = False

    def _get_connection(self):
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )

    def _check_tables_exist(self) -> bool:
        """Check if core tables exist in the database."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'documents'
                )
            """)
            exists = cur.fetchone()[0]
            cur.close()
            conn.close()
            return exists
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    def _ensure_migrations_table(self) -> bool:
        """Ensure the schema_migrations tracking table exists."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error creating migrations table: {e}")
            return False
    
    def _get_applied_migrations(self) -> set:
        """Get set of already applied migration names."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT migration_name FROM schema_migrations")
            migrations = {row[0] for row in cur.fetchall()}
            cur.close()
            conn.close()
            return migrations
        except Exception as e:
            logger.warning(f"Could not get applied migrations: {e}")
            return set()
    
    def _record_migration(self, migration_name: str) -> bool:
        """Record that a migration has been applied."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (%s) ON CONFLICT DO NOTHING",
                (migration_name,)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error recording migration: {e}")
            return False

    def _get_schema_path(self) -> str:
        """Get the path to the schema.sql file."""
        # Try multiple locations for the schema file
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'migrations', 'schema.sql'),
            '/app/storage/migrations/schema.sql',
            os.path.join(os.getcwd(), 'storage', 'migrations', 'schema.sql'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return possible_paths[0]  # Return first option for error message

    def _check_unique_constraint_exists(self) -> bool:
        """Check if the unique constraint on documents.path exists."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_type = 'UNIQUE'
                AND table_name = 'documents'
                AND constraint_name LIKE '%path%'
            """)
            exists = cur.fetchone() is not None
            cur.close()
            conn.close()
            return exists
        except Exception as e:
            logger.debug(f"Error checking unique constraint: {e}")
            return False
    
    def _run_schema_migrations(self) -> bool:
        """Run additional schema migrations for existing databases."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Migration 002: Add unique index on documents.path for UPSERT support
            # This handles existing databases that don't have the UNIQUE constraint
            if '002_documents_path_unique' not in self._get_applied_migrations():
                if not self._check_unique_constraint_exists():
                    logger.info("Running migration: adding unique index on documents.path")
                    cur.execute("""
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_path_unique 
                        ON documents(path)
                    """)
                    conn.commit()
                self._record_migration('002_documents_path_unique')
                logger.info("Migration 002 completed: documents.path unique index added")
            
            # Migration 003: Add document lifecycle columns
            # Adds status, status_updated_at, last_error, attempt_count for async processing
            if '003_document_lifecycle' not in self._get_applied_migrations():
                logger.info("Running migration: adding document lifecycle columns")
                
                # Check if columns exist before adding
                cur.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'status'
                """)
                if not cur.fetchone():
                    cur.execute("""
                        ALTER TABLE documents 
                        ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'METADATA_INDEXED'
                    """)
                
                cur.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'status_updated_at'
                """)
                if not cur.fetchone():
                    cur.execute("""
                        ALTER TABLE documents 
                        ADD COLUMN status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """)
                
                cur.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'last_error'
                """)
                if not cur.fetchone():
                    cur.execute("""
                        ALTER TABLE documents 
                        ADD COLUMN last_error TEXT
                    """)
                
                cur.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'attempt_count'
                """)
                if not cur.fetchone():
                    cur.execute("""
                        ALTER TABLE documents 
                        ADD COLUMN attempt_count INTEGER DEFAULT 0
                    """)
                
                conn.commit()
                
                # Add index on status column
                try:
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_documents_status 
                        ON documents(status)
                    """)
                    conn.commit()
                except Exception:
                    pass  # Index may already exist
                
                self._record_migration('003_document_lifecycle')
                logger.info("Migration 003 completed: document lifecycle columns added")
            
            # Migration 004: Add document_jobs table for job queue
            if '004_document_jobs' not in self._get_applied_migrations():
                logger.info("Running migration: creating document_jobs table")
                
                # Check if table exists
                cur.execute("""
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'document_jobs'
                """)
                if not cur.fetchone():
                    cur.execute("""
                        CREATE TABLE document_jobs (
                            id SERIAL PRIMARY KEY,
                            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                            job_type VARCHAR(100) NOT NULL,
                            priority INTEGER DEFAULT 0,
                            status VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            started_at TIMESTAMP,
                            completed_at TIMESTAMP,
                            worker_id VARCHAR(100),
                            error_message TEXT
                        )
                    """)
                    
                    # Create indexes
                    cur.execute("""
                        CREATE INDEX idx_document_jobs_document 
                        ON document_jobs(document_id)
                    """)
                    cur.execute("""
                        CREATE INDEX idx_document_jobs_status 
                        ON document_jobs(status)
                    """)
                    cur.execute("""
                        CREATE INDEX idx_document_jobs_type 
                        ON document_jobs(job_type)
                    """)
                    
                    conn.commit()
                    logger.info("Migration 004 completed: document_jobs table created")
                else:
                    logger.info("Migration 004 skipped: document_jobs table already exists")
                
                self._record_migration('004_document_jobs')
            
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error running schema migrations: {e}")
            return False

    def ensure_schema(self) -> bool:
        """
        Ensure database schema exists, creating it if necessary.
        
        Uses migration tracking to prevent duplicate execution and
        support future schema upgrades.
        
        Returns:
            True if schema is ready, False on failure
        """
        if self._schema_verified:
            return True
        
        try:
            # First, ensure migrations table exists
            self._ensure_migrations_table()
            
            # Check for existing initial migration
            applied = self._get_applied_migrations()
            
            # Check if tables already exist
            if self._check_tables_exist():
                # Tables exist - run any pending migrations
                self._run_schema_migrations()
                
                # Check if we have migration record
                if '001_initial' not in applied:
                    # Tables exist but no migration record - record it
                    self._record_migration('001_initial')
                logger.info("Database schema already exists")
                self._schema_verified = True
                return True
            
            # Schema doesn't exist, create it
            logger.warning("Database schema not found, creating...")
            
            schema_path = self._get_schema_path()
            if not os.path.exists(schema_path):
                logger.error(f"Schema file not found at: {schema_path}")
                return False
            
            # Read and execute schema
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Execute each statement separately
            statements = []
            current_stmt = []
            for line in schema_sql.split('\n'):
                stripped = line.strip()
                # Skip comments and empty lines
                if not stripped or stripped.startswith('--'):
                    continue
                current_stmt.append(line)
                if stripped.endswith(';'):
                    statements.append('\n'.join(current_stmt))
                    current_stmt = []
            
            # Execute each statement
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    try:
                        cur.execute(stmt)
                    except Exception as e:
                        # Log but continue - some statements might fail on re-run
                        logger.debug(f"Statement execution note: {e}")
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Run any additional migrations after initial schema creation
            self._run_schema_migrations()
            
            # Verify schema was created
            if self._check_tables_exist():
                logger.info("Database schema created successfully")
                # Record the migration
                self._record_migration('001_initial')
                self._schema_verified = True
                return True
            else:
                logger.error("Schema creation failed - tables still don't exist")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring schema: {e}")
            return False

    def save_document(self, document):
        """Save a document to the database.
        
        Canonical schema columns: path, extension, sha256, file_size, 
        character_count, parser, modified_time, status, status_updated_at,
        last_error, attempt_count, indexed_at
        
        Handles timestamp conversion: Unix epoch floats are converted to
        PostgreSQL-compatible datetime objects.
        
        Document Lifecycle States:
        - DISCOVERED: File detected, metadata not yet indexed
        - METADATA_INDEXED: Metadata extracted, content not yet processed (default for save_document)
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        path = document.get('path', '')
        
        # Map legacy input keys to canonical schema columns
        # hash → sha256, size_bytes → file_size
        sha256 = document.get('sha256') or document.get('hash')
        file_size = document.get('file_size') or document.get('size_bytes')
        character_count = document.get('character_count')
        modified_time = _to_postgres_timestamp(document.get('modified_time'))
        parser = document.get('parser')
        extension = document.get('extension')
        
        # Document lifecycle state
        # Default to METADATA_INDEXED since save_document is called after metadata extraction
        status = document.get('status', 'METADATA_INDEXED')
        status_updated_at = _to_postgres_timestamp(datetime.now(timezone.utc))
        last_error = document.get('last_error')
        attempt_count = document.get('attempt_count', 1)
        
        cur.execute(
            """
            INSERT INTO documents (path, extension, sha256, file_size, character_count, parser, modified_time, status, status_updated_at, last_error, attempt_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (path) DO UPDATE SET
                extension = EXCLUDED.extension,
                sha256 = EXCLUDED.sha256,
                file_size = EXCLUDED.file_size,
                character_count = EXCLUDED.character_count,
                parser = EXCLUDED.parser,
                modified_time = EXCLUDED.modified_time,
                status = EXCLUDED.status,
                status_updated_at = EXCLUDED.status_updated_at,
                last_error = EXCLUDED.last_error,
                attempt_count = EXCLUDED.attempt_count
            RETURNING id
            """,
            (path, extension, sha256, file_size, character_count, parser, modified_time, status, status_updated_at, last_error, attempt_count)
        )
        document_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return document_id
    
    def update_document_status(self, document_id: int, status: str, last_error: str = None) -> bool:
        """Update document processing status.
        
        Args:
            document_id: ID of the document to update
            status: New status (DISCOVERED, METADATA_INDEXED, CONTENT_EXTRACTED, etc.)
            last_error: Error message if status is FAILED, None otherwise
            
        Returns:
            True if update succeeded, False otherwise
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            status_updated_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            cur.execute(
                """
                UPDATE documents 
                SET status = %s, status_updated_at = %s, last_error = %s
                WHERE id = %s
                """,
                (status, status_updated_at, last_error, document_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            return False
    
    def increment_attempt_count(self, document_id: int) -> bool:
        """Increment the attempt count for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            True if update succeeded, False otherwise
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE documents SET attempt_count = attempt_count + 1 WHERE id = %s",
                (document_id,)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error incrementing attempt count: {e}")
            return False
    
    def get_document_status_counts(self) -> dict:
        """Get count of documents grouped by status.
        
        Returns:
            Dict mapping status -> count, e.g. {'METADATA_INDEXED': 10, 'FAILED': 2}
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT status, COUNT(*) as count 
                FROM documents 
                GROUP BY status 
                ORDER BY status
                """
            )
            results = {row[0]: row[1] for row in cur.fetchall()}
            cur.close()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting document status counts: {e}")
            return {}
    
    # =========================================================================
    # Job Queue Methods (Phase 2)
    # =========================================================================
    
    def create_job(self, document_id: int, job_type: str, priority: int = 0) -> int:
        """Create a new job for a document.
        
        Args:
            document_id: ID of the document to process
            job_type: Type of job (compute_sha256, extract_text, extract_entities, etc.)
            priority: Job priority (higher = more important)
            
        Returns:
            Job ID if created, None on failure
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            created_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            cur.execute(
                """
                INSERT INTO document_jobs (document_id, job_type, priority, status, created_at)
                VALUES (%s, %s, %s, 'QUEUED', %s)
                RETURNING id
                """,
                (document_id, job_type, priority, created_at)
            )
            job_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Created job {job_id}: {job_type} for document {document_id}")
            return job_id
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return None
    
    def create_jobs_for_document(self, document_id: int, job_types: list = None) -> list:
        """Create multiple jobs for a document.
        
        Args:
            document_id: ID of the document
            job_types: List of job types to create. If None, creates default set.
            
        Returns:
            List of created job IDs
        """
        if job_types is None:
            job_types = ['extract_text', 'extract_entities', 'extract_events', 'extract_locations']
        
        job_ids = []
        for job_type in job_types:
            job_id = self.create_job(document_id, job_type)
            if job_id:
                job_ids.append(job_id)
        return job_ids
    
    def claim_job(self, worker_id: str) -> dict:
        """Claim a queued job for processing.
        
        Uses SELECT FOR UPDATE to atomically claim the oldest queued job.
        
        Args:
            worker_id: ID of the worker claiming the job
            
        Returns:
            Job dict with all fields, or None if no jobs available
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            started_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            # Claim the oldest queued job
            cur.execute(
                """
                UPDATE document_jobs
                SET status = 'IN_PROGRESS', worker_id = %s, started_at = %s
                WHERE id = (
                    SELECT id FROM document_jobs
                    WHERE status = 'QUEUED'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id, document_id, job_type, priority, status, worker_id, created_at, started_at
                """,
                (worker_id, started_at)
            )
            row = cur.fetchone()
            conn.commit()
            
            if row:
                job = {
                    'id': row[0],
                    'document_id': row[1],
                    'job_type': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'worker_id': row[5],
                    'created_at': row[6],
                    'started_at': row[7]
                }
                cur.close()
                conn.close()
                logger.info(f"Worker {worker_id} claimed job {job['id']}: {job['job_type']}")
                return job
            
            cur.close()
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error claiming job: {e}")
            return None
    
    def complete_job(self, job_id: int, error_message: str = None) -> bool:
        """Mark a job as completed.
        
        Args:
            job_id: ID of the job to complete
            error_message: Error message if failed, None if succeeded
            
        Returns:
            True if update succeeded, False otherwise
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            completed_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            status = 'FAILED' if error_message else 'COMPLETED'
            
            cur.execute(
                """
                UPDATE document_jobs
                SET status = %s, completed_at = %s, error_message = %s
                WHERE id = %s
                """,
                (status, completed_at, error_message, job_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Job {job_id} marked as {status}")
            return True
        except Exception as e:
            logger.error(f"Error completing job: {e}")
            return False
    
    def get_job_status_counts(self) -> dict:
        """Get count of jobs grouped by status.
        
        Returns:
            Dict mapping status -> count
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT status, COUNT(*) as count 
                FROM document_jobs 
                GROUP BY status 
                ORDER BY status
                """
            )
            results = {row[0]: row[1] for row in cur.fetchall()}
            cur.close()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error getting job status counts: {e}")
            return {}
    
    def get_document_jobs(self, document_id: int) -> list:
        """Get all jobs for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of job dicts
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, document_id, job_type, priority, status, 
                       created_at, started_at, completed_at, worker_id, error_message
                FROM document_jobs
                WHERE document_id = %s
                ORDER BY created_at DESC
                """,
                (document_id,)
            )
            jobs = []
            for row in cur.fetchall():
                jobs.append({
                    'id': row[0],
                    'document_id': row[1],
                    'job_type': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'started_at': row[6],
                    'completed_at': row[7],
                    'worker_id': row[8],
                    'error_message': row[9]
                })
            cur.close()
            conn.close()
            return jobs
        except Exception as e:
            logger.error(f"Error getting document jobs: {e}")
            return []
    
    def get_queued_jobs_count(self) -> int:
        """Get count of queued jobs waiting to be processed.
        
        Returns:
            Number of queued jobs
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM document_jobs WHERE status = 'QUEUED'"
            )
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting queued jobs count: {e}")
            return 0
    
    def save_entities(self, document_id, entities):
        """Save entities to the database.
        
        Canonical schema columns: value, type, normalized_value
        Supports legacy 'name' key mapped to 'value'.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        for entity in entities:
            # Map legacy 'name' to canonical 'value'
            value = entity.get('value') or entity.get('name')
            entity_type = entity.get('type')
            normalized_value = entity.get('normalized_value')
            
            cur.execute(
                """
                INSERT INTO entities (value, type, normalized_value)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (value, entity_type, normalized_value)
            )
            result = cur.fetchone()
            if result:
                entity_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM entities WHERE value = %s AND type = %s",
                    (value, entity_type)
                )
                entity_id = cur.fetchone()[0]
            
            cur.execute(
                """
                INSERT INTO document_entities (document_id, entity_id, occurrences)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id, entity_id) DO UPDATE SET occurrences = document_entities.occurrences + 1
                """,
                (document_id, entity_id, entity.get('occurrences', 1))
            )
        conn.commit()
        cur.close()
        conn.close()

    def save_events(self, document_id, events):
        """Save events to the database.
        
        Handles timestamp conversion for events.timestamp field.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        for event in events:
            timestamp = _to_postgres_timestamp(event.get('timestamp'))
            cur.execute(
                """
                INSERT INTO events (timestamp, event_type, description)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (timestamp, event.get('event_type'), event.get('description'))
            )
            result = cur.fetchone()
            if result:
                event_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM events WHERE timestamp = %s AND event_type = %s AND description = %s",
                    (timestamp, event.get('event_type'), event.get('description'))
                )
                event_id = cur.fetchone()[0]
            
            cur.execute(
                """
                INSERT INTO document_events (document_id, event_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (document_id, event_id)
            )
        conn.commit()
        cur.close()
        conn.close()

    def save_locations(self, document_id, locations):
        conn = self._get_connection()
        cur = conn.cursor()
        for location in locations:
            cur.execute(
                """
                INSERT INTO locations (name, latitude, longitude)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (location.get('name'), location.get('latitude'), location.get('longitude'))
            )
            result = cur.fetchone()
            if result:
                location_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM locations WHERE name = %s AND latitude = %s AND longitude = %s",
                    (location.get('name'), location.get('latitude'), location.get('longitude'))
                )
                location_id = cur.fetchone()[0]
            
            cur.execute(
                """
                INSERT INTO document_locations (document_id, location_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (document_id, location_id)
            )
        conn.commit()
        cur.close()
        conn.close()

    def load_collection(self, collection_id=None, name=None):
        raise NotImplementedError()

    def search_documents(self, query=None, entity=None, date=None, month=None, location=None):
        """Search documents with optional filters.
        
        Canonical schema columns: path, extension, sha256, file_size, 
        character_count, parser, modified_time, indexed_at
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        # Query text search
        if query:
            conditions.append("(d.path ILIKE %s OR d.extension ILIKE %s)")
            params.extend([f"%{query}%", f"%{query}%"])
        
        # Entity filter - join with document_entities
        if entity:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_entities de
                    JOIN entities e ON de.entity_id = e.id
                    WHERE de.document_id = d.id AND e.value ILIKE %s
                )
            """)
            params.append(f"%{entity}%")
        
        # Date filter - documents indexed on that date
        if date:
            conditions.append("d.indexed_at::date = %s")
            params.append(date)
        
        # Month filter - documents indexed in that month
        if month:
            conditions.append("TO_CHAR(d.indexed_at, 'YYYY-MM') = %s")
            params.append(month)
        
        # Location filter - join with document_locations
        if location:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_locations dl
                    JOIN locations l ON dl.location_id = l.id
                    WHERE dl.document_id = d.id AND l.name ILIKE %s
                )
            """)
            params.append(f"%{location}%")
        
        # Build query - use canonical column names
        sql = """SELECT d.id, d.path, d.extension, d.sha256, d.file_size, 
                        d.character_count, d.parser, d.modified_time, d.indexed_at 
                 FROM documents d"""
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY d.indexed_at DESC LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'path': row[1],
                'extension': row[2],
                'sha256': row[3],
                'file_size': row[4],
                'character_count': row[5],
                'parser': row[6],
                'modified_time': row[7],
                'indexed_at': row[8]
            })
        
        cur.close()
        conn.close()
        return results

    def search_entities(self, entity_type=None, value=None):
        """Search entities with optional filters.
        
        Canonical schema columns: value, type, normalized_value
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        if entity_type:
            conditions.append("e.type = %s")
            params.append(entity_type)
        
        if value:
            conditions.append("e.value ILIKE %s")
            params.append(f"%{value}%")
        
        sql = """
            SELECT e.id, e.type, e.value, e.normalized_value, 
                   COUNT(DISTINCT de.document_id) as doc_count
            FROM entities e
            LEFT JOIN document_entities de ON e.id = de.entity_id
        """
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " GROUP BY e.id, e.type, e.value, e.normalized_value"
        sql += " ORDER BY doc_count DESC, e.value LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'type': row[1],
                'value': row[2],
                'normalized_value': row[3],
                'document_count': row[4]
            })
        
        cur.close()
        conn.close()
        return results

    def search_events(self, date=None, month=None, entity=None, event_type=None):
        """Search events with optional filters."""
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        # Date filter - event on specific date
        if date:
            conditions.append("e.timestamp >= %s")
            conditions.append("e.timestamp < %s::date + INTERVAL '1 day'")
            params.append(date)
            params.append(date)
        
        # Month filter - events in specific month
        if month:
            year, mon = month.split('-')
            start_date = f"{year}-{mon}-01"
            # Calculate next month
            if mon == '12':
                next_month = f"{int(year) + 1}-01-01"
            else:
                next_month = f"{year}-{int(mon) + 1:02d}-01"
            conditions.append("e.timestamp >= %s")
            conditions.append("e.timestamp < %s")
            params.append(start_date)
            params.append(next_month)
        
        # Entity filter - events from documents containing entity
        if entity:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_events dev
                    JOIN document_entities de ON dev.document_id = de.document_id
                    JOIN entities ent ON de.entity_id = ent.id
                    WHERE dev.event_id = e.id AND ent.value ILIKE %s
                )
            """)
            params.append(f"%{entity}%")
        
        # Event type filter
        if event_type:
            conditions.append("e.event_type = %s")
            params.append(event_type)
        
        sql = """
            SELECT e.id, e.timestamp, e.event_type, e.description,
                   COUNT(DISTINCT dev.document_id) as doc_count
            FROM events e
            LEFT JOIN document_events dev ON e.id = dev.event_id
        """
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " GROUP BY e.id, e.timestamp, e.event_type, e.description"
        sql += " ORDER BY e.timestamp DESC LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'timestamp': row[1],
                'event_type': row[2],
                'description': row[3],
                'document_count': row[4]
            })
        
        cur.close()
        conn.close()
        return results

    def search_locations(self, date=None, month=None, entity=None, location_name=None):
        """Search locations with optional filters."""
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        # Date filter - locations from documents modified on that date
        if date:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_locations dl
                    JOIN documents d ON dl.document_id = d.id
                    WHERE dl.location_id = l.id AND d.modified_time::date = %s
                )
            """)
            params.append(date)
        
        # Month filter - locations from documents modified in that month
        if month:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_locations dl
                    JOIN documents d ON dl.document_id = d.id
                    WHERE dl.location_id = l.id AND TO_CHAR(d.modified_time, 'YYYY-MM') = %s
                )
            """)
            params.append(month)
        
        # Entity filter - locations from documents containing entity
        if entity:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM document_locations dl
                    JOIN document_entities de ON dl.document_id = de.document_id
                    JOIN entities ent ON de.entity_id = ent.id
                    WHERE dl.location_id = l.id AND ent.value ILIKE %s
                )
            """)
            params.append(f"%{entity}%")
        
        # Location name filter
        if location_name:
            conditions.append("l.name ILIKE %s")
            params.append(f"%{location_name}%")
        
        sql = """
            SELECT l.id, l.name, l.latitude, l.longitude,
                   COUNT(DISTINCT dl.document_id) as doc_count
            FROM locations l
            LEFT JOIN document_locations dl ON l.id = dl.location_id
        """
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " GROUP BY l.id, l.name, l.latitude, l.longitude"
        sql += " ORDER BY doc_count DESC, l.name LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'document_count': row[4]
            })
        
        cur.close()
        conn.close()
        return results

    def search_relationships(self, entity=None, relationship_type=None):
        """Search relationships with optional filters."""
        conn = self._get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        # Entity filter - relationships involving entity
        if entity:
            conditions.append("(r.from_entity ILIKE %s OR r.to_entity ILIKE %s)")
            params.extend([f"%{entity}%", f"%{entity}%"])
        
        # Relationship type filter
        if relationship_type:
            conditions.append("r.relationship_type = %s")
            params.append(relationship_type)
        
        sql = "SELECT id, from_entity, to_entity, relationship_type FROM relationships"
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY relationship_type, from_entity LIMIT 100"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'from': row[1],
                'to': row[2],
                'type': row[3]
            })
        
        cur.close()
        conn.close()
        return results