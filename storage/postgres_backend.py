import os
import logging
from datetime import datetime, timezone, timedelta
import psycopg
from .backend import StorageBackend

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Job types
class JobType:
    EXTRACT_TEXT = 'extract_text'
    EXTRACT_ENTITIES = 'extract_entities'
    EXTRACT_EVENTS = 'extract_events'
    EXTRACT_LOCATIONS = 'extract_locations'
    GENERATE_EMBEDDINGS = 'generate_embeddings'
    OCR = 'ocr'
    PLUGIN_PROCESSING = 'plugin_processing'
    EXTRACT_PHOTO_METADATA = 'extract_photo_metadata'


# Image extensions for photo metadata extraction (Phase 1A: Evidence Timeline)
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif'}


# Job status
class JobStatus:
    QUEUED = 'QUEUED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    FAILED_PERMANENT = 'FAILED_PERMANENT'
    CANCELLED = 'CANCELLED'


# Document lifecycle states
class DocumentStatus:
    DISCOVERED = 'DISCOVERED'
    METADATA_INDEXED = 'METADATA_INDEXED'
    CONTENT_EXTRACTED = 'CONTENT_EXTRACTED'
    ENTITY_EXTRACTED = 'ENTITY_EXTRACTED'
    RELATIONSHIPS_BUILT = 'RELATIONSHIPS_BUILT'
    EMBEDDED = 'EMBEDDED'
    COMPLETE = 'COMPLETE'
    FAILED = 'FAILED'


# Valid state transitions
VALID_TRANSITIONS = {
    DocumentStatus.DISCOVERED: {DocumentStatus.METADATA_INDEXED, DocumentStatus.FAILED},
    DocumentStatus.METADATA_INDEXED: {DocumentStatus.CONTENT_EXTRACTED, DocumentStatus.FAILED},
    DocumentStatus.CONTENT_EXTRACTED: {DocumentStatus.ENTITY_EXTRACTED, DocumentStatus.FAILED},
    DocumentStatus.ENTITY_EXTRACTED: {DocumentStatus.RELATIONSHIPS_BUILT, DocumentStatus.FAILED},
    DocumentStatus.RELATIONSHIPS_BUILT: {DocumentStatus.EMBEDDED, DocumentStatus.FAILED},
    DocumentStatus.EMBEDDED: {DocumentStatus.COMPLETE, DocumentStatus.FAILED},
    DocumentStatus.COMPLETE: {DocumentStatus.FAILED},  # Can fail after completion
    DocumentStatus.FAILED: {DocumentStatus.METADATA_INDEXED},  # Retry path
}


# Retry configuration
MAX_RETRIES = 5
RETRY_DELAYS = {
    1: timedelta(seconds=0),      # Immediate
    2: timedelta(minutes=1),
    3: timedelta(minutes=5),
    4: timedelta(minutes=30),
    5: timedelta(hours=2),
}


# Lease configuration
DEFAULT_LEASE_SECONDS = 300  # 5 minutes


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
            
            # Migration 006: Phase 3 - Worker runtime enhancements
            # - Add lease management columns
            # - Add retry/backoff columns
            # - Add unique constraint
            # - Add document_content table
            if '006_worker_runtime' not in self._get_applied_migrations():
                logger.info("Running migration: Phase 3 worker runtime")
                
                # Add lease management columns to document_jobs
                for col_name, col_def in [
                    ('claimed_at', 'TIMESTAMP'),
                    ('lease_until', 'TIMESTAMP'),
                    ('attempt_count', 'INTEGER DEFAULT 0'),
                    ('last_error', 'TEXT'),
                    ('next_retry_at', 'TIMESTAMP')
                ]:
                    cur.execute(f"""
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'document_jobs' AND column_name = '{col_name}'
                    """)
                    if not cur.fetchone():
                        cur.execute(f"""
                            ALTER TABLE document_jobs ADD COLUMN {col_name} {col_def}
                        """)
                
                # Add unique constraint if not exists
                try:
                    cur.execute("""
                        ALTER TABLE document_jobs 
                        ADD CONSTRAINT uq_document_job UNIQUE (document_id, job_type)
                    """)
                except psycopg.errors.DuplicateConstraint:
                    pass  # Already exists
                
                # Add indexes for lease and retry
                try:
                    cur.execute("""
                        CREATE INDEX idx_document_jobs_lease 
                        ON document_jobs(lease_until) 
                        WHERE status = 'IN_PROGRESS'
                    """)
                except psycopg.errors.DuplicateObject:
                    pass
                
                try:
                    cur.execute("""
                        CREATE INDEX idx_document_jobs_retry 
                        ON document_jobs(next_retry_at) 
                        WHERE status = 'QUEUED'
                    """)
                except psycopg.errors.DuplicateObject:
                    pass
                
                conn.commit()
                
                # Create document_content table
                cur.execute("""
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'document_content'
                """)
                if not cur.fetchone():
                    cur.execute("""
                        CREATE TABLE document_content (
                            id SERIAL PRIMARY KEY,
                            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
                            content TEXT,
                            content_hash VARCHAR(64),
                            character_count INTEGER,
                            encoding VARCHAR(50),
                            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            extraction_method VARCHAR(100)
                        )
                    """)
                    cur.execute("""
                        CREATE INDEX idx_document_content_doc 
                        ON document_content(document_id)
                    """)
                    conn.commit()
                
                self._record_migration('006_worker_runtime')
                logger.info("Migration 006 completed: worker runtime enhancements")
            
            # Migration 005: Add evidence_lineage table for provenance tracking
            if '005_evidence_lineage' not in self._get_applied_migrations():
                logger.info("Running migration: creating evidence_lineage table")
                
                # Check if table exists
                cur.execute("""
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'evidence_lineage'
                """)
                if not cur.fetchone():
                    cur.execute("""
                        CREATE TABLE evidence_lineage (
                            id SERIAL PRIMARY KEY,
                            entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                            artifact_path TEXT,
                            plugin_name VARCHAR(100),
                            confidence DOUBLE PRECISION DEFAULT 1.0,
                            processing_time_ms INTEGER,
                            version VARCHAR(50),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes
                    cur.execute("""
                        CREATE INDEX idx_evidence_entity 
                        ON evidence_lineage(entity_id)
                    """)
                    cur.execute("""
                        CREATE INDEX idx_evidence_document 
                        ON evidence_lineage(document_id)
                    """)
                    cur.execute("""
                        CREATE INDEX idx_evidence_plugin 
                        ON evidence_lineage(plugin_name)
                    """)
                    
                    conn.commit()
                    logger.info("Migration 005 completed: evidence_lineage table created")
                else:
                    logger.info("Migration 005 skipped: evidence_lineage table already exists")
                
                self._record_migration('005_evidence_lineage')
            
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
    
    def save_document_atomic(self, document: dict, job_types: list = None) -> tuple:
        """Save document and create jobs atomically (Phase 3F: transaction atomicity).
        
        All operations are wrapped in a single transaction.
        Either all succeed or all are rolled back.
        
        Args:
            document: Document data dict
            job_types: List of job types to create. If None, creates default set.
            
        Returns:
            Tuple of (document_id, list of job_ids), or (None, []) on failure
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            path = document.get('path', '')
            sha256 = document.get('sha256') or document.get('hash')
            file_size = document.get('file_size') or document.get('size_bytes')
            character_count = document.get('character_count')
            modified_time = _to_postgres_timestamp(document.get('modified_time'))
            parser = document.get('parser')
            extension = document.get('extension')
            status = document.get('status', DocumentStatus.METADATA_INDEXED)
            status_updated_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            last_error = document.get('last_error')
            attempt_count = document.get('attempt_count', 1)
            created_at = status_updated_at
            
            # Step 1: Save document
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
            
            # Step 2: Create jobs (if any)
            job_ids = []
            if job_types is None:
                # Use default job types based on document type
                job_types = self._get_default_job_types(document)
            
            # Phase 1A: Add photo metadata extraction for images
            if self._should_queue_photo_metadata_job(document):
                if JobType.EXTRACT_PHOTO_METADATA not in job_types:
                    job_types.append(JobType.EXTRACT_PHOTO_METADATA)
            
            for job_type in job_types:
                cur.execute(
                    """
                    INSERT INTO document_jobs (document_id, job_type, priority, status, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, job_type) DO UPDATE SET document_id = EXCLUDED.document_id
                    RETURNING id
                    """,
                    (document_id, job_type, 0, JobStatus.QUEUED, created_at)
                )
                row = cur.fetchone()
                if row:
                    job_ids.append(row[0])
            
            # Commit all at once
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Atomically saved document {document_id} with {len(job_ids)} jobs")
            return (document_id, job_ids)
            
        except Exception as e:
            logger.error(f"Error in atomic save: {e}")
            if conn:
                conn.rollback()
            return (None, [])
    
    def _is_image_extension(self, extension: str) -> bool:
        """Check if extension is a supported image type for photo metadata extraction."""
        if not extension:
            return False
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
        return ext in IMAGE_EXTENSIONS
    
    def _should_queue_photo_metadata_job(self, document: dict) -> bool:
        """
        Determine if a photo metadata extraction job should be queued.
        
        Phase 1A: Queue job for images with supported extensions.
        """
        extension = document.get('extension', '')
        return self._is_image_extension(extension)
    
    def _get_default_job_types(self, document: dict = None) -> list:
        """
        Get default job types for a document.
        
        Phase 1A: For images, also include extract_photo_metadata job.
        """
        job_types = [JobType.EXTRACT_TEXT, JobType.EXTRACT_ENTITIES,
                    JobType.EXTRACT_EVENTS, JobType.EXTRACT_LOCATIONS]
        
        if document and self._should_queue_photo_metadata_job(document):
            job_types.append(JobType.EXTRACT_PHOTO_METADATA)
        
        return job_types
    
    def save_content(self, document_id: int, content: str, extraction_method: str = 'textract') -> bool:
        """Save extracted content for a document (Phase 3A: content extraction).
        
        Args:
            document_id: ID of the document
            content: Extracted text content
            extraction_method: Method used for extraction
            
        Returns:
            True if save succeeded
        """
        try:
            import hashlib
            
            conn = self._get_connection()
            cur = conn.cursor()
            extracted_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest() if content else None
            character_count = len(content) if content else 0
            
            cur.execute(
                """
                INSERT INTO document_content (document_id, content, content_hash, character_count, encoding, extracted_at, extraction_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    content_hash = EXCLUDED.content_hash,
                    character_count = EXCLUDED.character_count,
                    encoding = EXCLUDED.encoding,
                    extracted_at = EXCLUDED.extracted_at,
                    extraction_method = EXCLUDED.extraction_method
                """,
                (document_id, content, content_hash, character_count, 'utf-8', extracted_at, extraction_method)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Saved content for document {document_id}: {character_count} chars")
            return True
        except Exception as e:
            logger.error(f"Error saving content: {e}")
            return False

    def save_photo_metadata(self, document_id: int, metadata: dict) -> bool:
        """Save photo metadata for a document (Phase 1A: Evidence Timeline).
        
        Args:
            document_id: ID of the document (must be an image)
            metadata: Dict containing extracted EXIF data:
                - timestamp_original: When photo was taken
                - timestamp_digitized: When photo was digitized
                - timestamp_metadata: File metadata timestamp
                - gps_latitude: GPS latitude in decimal degrees
                - gps_longitude: GPS longitude in decimal degrees
                - gps_altitude: GPS altitude in meters
                - camera_make: Camera manufacturer
                - camera_model: Camera model
                - lens_model: Lens model
                - width: Image width in pixels
                - height: Image height in pixels
                - orientation: Image orientation
                - file_format: Image format (JPEG, PNG, etc.)
                - raw_exif: Raw EXIF data as dict
                
        Returns:
            True if save succeeded
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            extracted_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            # Convert timestamps
            ts_original = _to_postgres_timestamp(metadata.get('timestamp_original'))
            ts_digitized = _to_postgres_timestamp(metadata.get('timestamp_digitized'))
            ts_metadata = _to_postgres_timestamp(metadata.get('timestamp_metadata'))
            
            cur.execute(
                """
                INSERT INTO photo_metadata (
                    document_id,
                    timestamp_original,
                    timestamp_digitized,
                    timestamp_metadata,
                    gps_latitude,
                    gps_longitude,
                    gps_altitude,
                    camera_make,
                    camera_model,
                    lens_model,
                    width,
                    height,
                    orientation,
                    file_format,
                    extraction_method,
                    extraction_version,
                    raw_exif,
                    extracted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    timestamp_original = EXCLUDED.timestamp_original,
                    timestamp_digitized = EXCLUDED.timestamp_digitized,
                    timestamp_metadata = EXCLUDED.timestamp_metadata,
                    gps_latitude = EXCLUDED.gps_latitude,
                    gps_longitude = EXCLUDED.gps_longitude,
                    gps_altitude = EXCLUDED.gps_altitude,
                    camera_make = EXCLUDED.camera_make,
                    camera_model = EXCLUDED.camera_model,
                    lens_model = EXCLUDED.lens_model,
                    width = EXCLUDED.width,
                    height = EXCLUDED.height,
                    orientation = EXCLUDED.orientation,
                    file_format = EXCLUDED.file_format,
                    raw_exif = EXCLUDED.raw_exif,
                    extracted_at = EXCLUDED.extracted_at
                """,
                (
                    document_id,
                    ts_original,
                    ts_digitized,
                    ts_metadata,
                    metadata.get('gps_latitude'),
                    metadata.get('gps_longitude'),
                    metadata.get('gps_altitude'),
                    metadata.get('camera_make'),
                    metadata.get('camera_model'),
                    metadata.get('lens_model'),
                    metadata.get('width'),
                    metadata.get('height'),
                    metadata.get('orientation'),
                    metadata.get('file_format'),
                    'exif',
                    '1.0.0',
                    psycopg.types.json.Jsonb(metadata.get('raw_exif', {})) if metadata.get('raw_exif') else None,
                    extracted_at
                )
            )
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Saved photo metadata for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving photo metadata: {e}")
            return False

    def get_photo_metadata(self, document_id: int) -> dict:
        """Get photo metadata for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dict with photo metadata, or None if not found
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                SELECT id, document_id, timestamp_original, timestamp_digitized,
                       gps_latitude, gps_longitude, gps_altitude,
                       camera_make, camera_model, lens_model,
                       width, height, orientation, file_format,
                       extraction_method, extraction_version, extracted_at,
                       raw_exif
                FROM photo_metadata
                WHERE document_id = %s
                """,
                (document_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if not row:
                return None
            
            return {
                'id': row[0],
                'document_id': row[1],
                'timestamp_original': row[2],
                'timestamp_digitized': row[3],
                'gps_latitude': row[4],
                'gps_longitude': row[5],
                'gps_altitude': row[6],
                'camera_make': row[7],
                'camera_model': row[8],
                'lens_model': row[9],
                'width': row[10],
                'height': row[11],
                'orientation': row[12],
                'file_format': row[13],
                'extraction_method': row[14],
                'extraction_version': row[15],
                'extracted_at': row[16],
                'raw_exif': row[17]
            }
        except Exception as e:
            logger.error(f"Error getting photo metadata: {e}")
            return None

    def get_timeline_stats(self) -> dict:
        """
        Get statistics for the Evidence Timeline.
        
        Returns counts and date ranges for photo metadata.
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Get total photos
            cur.execute("SELECT COUNT(*) FROM photo_metadata")
            photos_total = cur.fetchone()[0] or 0
            
            # Get GPS tagged count
            cur.execute("""
                SELECT COUNT(*) FROM photo_metadata 
                WHERE gps_latitude IS NOT NULL AND gps_longitude IS NOT NULL
            """)
            gps_tagged = cur.fetchone()[0] or 0
            
            # Get unique cameras
            cur.execute("""
                SELECT COUNT(DISTINCT (camera_make, camera_model)) 
                FROM photo_metadata 
                WHERE camera_make IS NOT NULL AND camera_model IS NOT NULL
            """)
            unique_cameras = cur.fetchone()[0] or 0
            
            # Get first photo timestamp
            cur.execute("""
                SELECT MIN(timestamp_original) FROM photo_metadata 
                WHERE timestamp_original IS NOT NULL
            """)
            first_photo = cur.fetchone()[0]
            
            # Get last photo timestamp
            cur.execute("""
                SELECT MAX(timestamp_original) FROM photo_metadata 
                WHERE timestamp_original IS NOT NULL
            """)
            last_photo = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return {
                'photos_total': photos_total,
                'gps_tagged': gps_tagged,
                'unique_cameras': unique_cameras,
                'first_photo_timestamp': first_photo.isoformat() + 'Z' if first_photo else None,
                'last_photo_timestamp': last_photo.isoformat() + 'Z' if last_photo else None
            }
        except Exception as e:
            logger.error(f"Error getting timeline stats: {e}")
            return {
                'photos_total': 0,
                'gps_tagged': 0,
                'unique_cameras': 0,
                'first_photo_timestamp': None,
                'last_photo_timestamp': None
            }

    def search_photo_metadata(
        self,
        camera_make: str = None,
        camera_model: str = None,
        gps_only: bool = False,
        start_date: str = None,
        end_date: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple:
        """
        Search photo metadata with filters.
        
        Args:
            camera_make: Filter by camera manufacturer
            camera_model: Filter by camera model
            gps_only: Only return photos with GPS coordinates
            start_date: Filter photos after this date (ISO format)
            end_date: Filter photos before this date (ISO format)
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            Tuple of (list of results, total count)
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Build query with filters
            conditions = []
            params = []
            
            if camera_make:
                conditions.append("pm.camera_make ILIKE %s")
                params.append(f"%{camera_make}%")
            
            if camera_model:
                conditions.append("pm.camera_model ILIKE %s")
                params.append(f"%{camera_model}%")
            
            if gps_only:
                conditions.append("pm.gps_latitude IS NOT NULL AND pm.gps_longitude IS NOT NULL")
            
            if start_date:
                conditions.append("pm.timestamp_original >= %s")
                params.append(start_date)
            
            if end_date:
                conditions.append("pm.timestamp_original <= %s")
                params.append(end_date)
            
            where_sql = " AND ".join(conditions) if conditions else "1=1"
            
            # Get total count
            count_sql = f"""
                SELECT COUNT(*) FROM photo_metadata pm WHERE {where_sql}
            """
            cur.execute(count_sql, params)
            total = cur.fetchone()[0] or 0
            
            # Get results with document info
            query_sql = f"""
                SELECT 
                    pm.document_id,
                    d.path as filename,
                    pm.timestamp_original,
                    pm.gps_latitude,
                    pm.gps_longitude,
                    pm.camera_make,
                    pm.camera_model,
                    pm.width,
                    pm.height
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                WHERE {where_sql}
                ORDER BY pm.timestamp_original DESC NULLS LAST
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            cur.execute(query_sql, params)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'document_id': row[0],
                    'filename': row[1],
                    'timestamp': row[2].isoformat() + 'Z' if row[2] else None,
                    'gps_latitude': row[3],
                    'gps_longitude': row[4],
                    'camera_make': row[5],
                    'camera_model': row[6],
                    'width': row[7],
                    'height': row[8]
                })
            
            cur.close()
            conn.close()
            
            return (results, total)
        except Exception as e:
            logger.error(f"Error searching photo metadata: {e}")
            return ([], 0)

    def get_photos_with_gps(self, limit: int = 1000, offset: int = 0) -> list:
        """
        Get all photos with GPS coordinates for map display.
        
        Args:
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of photo metadata with GPS coordinates
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    pm.document_id,
                    pm.gps_latitude,
                    pm.gps_longitude,
                    pm.timestamp_original,
                    pm.camera_make,
                    pm.camera_model,
                    d.path as filename
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                WHERE pm.gps_latitude IS NOT NULL AND pm.gps_longitude IS NOT NULL
                ORDER BY pm.timestamp_original DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            results = []
            for row in cur.fetchall():
                # Combine camera make and model
                camera = f"{row[4] or ''} {row[5] or ''}".strip()
                
                results.append({
                    'document_id': row[0],
                    'latitude': row[1],
                    'longitude': row[2],
                    'timestamp': row[3].isoformat() + 'Z' if row[3] else None,
                    'camera': camera or None,
                    'filename': row[6]
                })
            
            cur.close()
            conn.close()
            
            return results
        except Exception as e:
            logger.error(f"Error getting photos with GPS: {e}")
            return []

    def get_document_for_photo(self, document_id: int) -> dict:
        """
        Get document info needed for timeline photo response.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dict with document info or None
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                "SELECT id, path, extension, modified_time FROM documents WHERE id = %s",
                (document_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if not row:
                return None
            
            # Extract filename from path
            path = row[1]
            filename = path.split('/')[-1] if path else None
            
            return {
                'document_id': row[0],
                'filename': filename,
                'extension': row[2],
                'modified_time': row[3].isoformat() + 'Z' if row[3] else None
            }
        except Exception as e:
            logger.error(f"Error getting document for photo: {e}")
            return None
    
    def get_content(self, document_id: int) -> dict:
        """Get extracted content for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dict with content data, or None if not found
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                SELECT id, document_id, content, content_hash, character_count, encoding, extracted_at, extraction_method
                FROM document_content
                WHERE document_id = %s
                """,
                (document_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'document_id': row[1],
                    'content': row[2],
                    'content_hash': row[3],
                    'character_count': row[4],
                    'encoding': row[5],
                    'extracted_at': row[6],
                    'extraction_method': row[7]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting content: {e}")
            return None
    
    def transition_document_status(self, document_id: int, new_status: str, last_error: str = None) -> bool:
        """Transition document to a new status (Phase 3E: state machine enforcement).
        
        Validates that the transition is allowed according to the state machine.
        Raises InvalidStateTransition if the transition is not valid.
        
        Args:
            document_id: ID of the document to update
            new_status: New status (must be valid transition from current)
            last_error: Error message if transitioning to FAILED
            
        Returns:
            True if transition succeeded
            
        Raises:
            ValueError: If transition is not valid
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Get current status
            cur.execute("SELECT status FROM documents WHERE id = %s", (document_id,))
            row = cur.fetchone()
            if not row:
                cur.close()
                conn.close()
                raise ValueError(f"Document {document_id} not found")
            
            current_status = row[0]
            
            # Validate transition
            allowed = VALID_TRANSITIONS.get(current_status, set())
            if new_status not in allowed:
                cur.close()
                conn.close()
                raise ValueError(
                    f"Invalid transition: {current_status} -> {new_status}. "
                    f"Allowed transitions from {current_status}: {allowed}"
                )
            
            # Perform transition
            status_updated_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            cur.execute(
                """
                UPDATE documents 
                SET status = %s, status_updated_at = %s, last_error = %s
                WHERE id = %s
                """,
                (new_status, status_updated_at, last_error, document_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Document {document_id} transitioned: {current_status} -> {new_status}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error transitioning document status: {e}")
            return False
    
    def update_document_status(self, document_id: int, status: str, last_error: str = None) -> bool:
        """Update document processing status (DEPRECATED: use transition_document_status).
        
        This method provides backward compatibility. For new code, use transition_document_status.
        
        Args:
            document_id: ID of the document to update
            status: New status
            last_error: Error message if status is FAILED
            
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
    # Phase 3A: Job Queue Methods with Lease Management
    # =========================================================================
    
    def create_job(self, document_id: int, job_type: str, priority: int = 0) -> int:
        """Create a new job for a document (Phase 3D: duplicate prevention).
        
        Args:
            document_id: ID of the document to process
            job_type: Type of job
            priority: Job priority (higher = more important)
            
        Returns:
            Job ID if created, None on failure or if duplicate exists
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            created_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            # Phase 3D: ON CONFLICT prevents duplicate jobs
            cur.execute(
                """
                INSERT INTO document_jobs (document_id, job_type, priority, status, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (document_id, job_type) DO NOTHING
                RETURNING id
                """,
                (document_id, job_type, priority, JobStatus.QUEUED, created_at)
            )
            row = cur.fetchone()
            conn.commit()
            
            if row:
                job_id = row[0]
                logger.info(f"Created job {job_id}: {job_type} for document {document_id}")
                cur.close()
                conn.close()
                return job_id
            else:
                # Duplicate job - get existing job ID
                cur.execute(
                    "SELECT id FROM document_jobs WHERE document_id = %s AND job_type = %s",
                    (document_id, job_type)
                )
                row = cur.fetchone()
                cur.close()
                conn.close()
                if row:
                    logger.info(f"Job already exists for document {document_id}: {job_type} (id={row[0]})")
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return None
    
    def create_jobs_for_document(self, document_id: int, job_types: list = None) -> list:
        """Create multiple jobs for a document (Phase 3F: atomic transaction).
        
        Args:
            document_id: ID of the document
            job_types: List of job types to create. If None, creates default set.
            
        Returns:
            List of created job IDs
        """
        if job_types is None:
            job_types = [JobType.EXTRACT_TEXT, JobType.EXTRACT_ENTITIES, 
                        JobType.EXTRACT_EVENTS, JobType.EXTRACT_LOCATIONS]
        
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            created_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            job_ids = []
            for job_type in job_types:
                # Phase 3D: ON CONFLICT prevents duplicates
                cur.execute(
                    """
                    INSERT INTO document_jobs (document_id, job_type, priority, status, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, job_type) DO UPDATE SET document_id = EXCLUDED.document_id
                    RETURNING id
                    """,
                    (document_id, job_type, 0, JobStatus.QUEUED, created_at)
                )
                row = cur.fetchone()
                if row:
                    job_ids.append(row[0])
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Created {len(job_ids)} jobs for document {document_id}")
            return job_ids
        except Exception as e:
            logger.error(f"Error creating jobs: {e}")
            if conn:
                conn.rollback()
            return []
    
    def claim_job(self, worker_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> dict:
        """Claim a queued job for processing (Phase 3A: lease management).
        
        Uses SELECT FOR UPDATE to atomically claim the oldest queued job.
        Only claims jobs that are ready for retry (next_retry_at <= now).
        
        Args:
            worker_id: ID of the worker claiming the job
            lease_seconds: How long to hold the lease
            
        Returns:
            Job dict with all fields, or None if no jobs available
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            now = _to_postgres_timestamp(datetime.now(timezone.utc))
            claimed_at = now
            lease_until = _to_postgres_timestamp(datetime.now(timezone.utc) + timedelta(seconds=lease_seconds))
            
            # Phase 3A: Include lease columns in claim
            cur.execute(
                """
                UPDATE document_jobs
                SET status = %s, worker_id = %s, claimed_at = %s, lease_until = %s,
                    started_at = COALESCE(started_at, %s), attempt_count = attempt_count + 1
                WHERE id = (
                    SELECT id FROM document_jobs
                    WHERE status = %s
                    AND (next_retry_at IS NULL OR next_retry_at <= %s)
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id, document_id, job_type, priority, status, worker_id, 
                          claimed_at, lease_until, started_at, attempt_count
                """,
                (JobStatus.IN_PROGRESS, worker_id, claimed_at, lease_until, now,
                 JobStatus.QUEUED, now)
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
                    'claimed_at': row[6],
                    'lease_until': row[7],
                    'started_at': row[8],
                    'attempt_count': row[9]
                }
                cur.close()
                conn.close()
                logger.info(f"Worker {worker_id} claimed job {job['id']}: {job['job_type']} (attempt {job['attempt_count']})")
                return job
            
            cur.close()
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error claiming job: {e}")
            return None
    
    def complete_job(self, job_id: int, success: bool = True, error_message: str = None) -> bool:
        """Mark a job as completed or failed (Phase 3C: retry logic).
        
        Args:
            job_id: ID of the job to complete
            success: True if job succeeded, False if failed
            error_message: Error message if failed
            
        Returns:
            True if update succeeded, False otherwise
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            now = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            if success:
                # Job succeeded - mark as COMPLETED, clear lease
                cur.execute(
                    """
                    UPDATE document_jobs
                    SET status = %s, completed_at = %s, error_message = NULL,
                        worker_id = NULL, lease_until = NULL
                    WHERE id = %s
                    """,
                    (JobStatus.COMPLETED, now, job_id)
                )
                conn.commit()
                cur.close()
                conn.close()
                logger.info(f"Job {job_id} marked as COMPLETED")
                return True
            else:
                # Job failed - check retry count
                cur.execute(
                    "SELECT attempt_count FROM document_jobs WHERE id = %s",
                    (job_id,)
                )
                row = cur.fetchone()
                if not row:
                    cur.close()
                    conn.close()
                    return False
                
                attempt_count = row[0]
                
                if attempt_count >= MAX_RETRIES:
                    # Max retries exceeded - permanent failure
                    cur.execute(
                        """
                        UPDATE document_jobs
                        SET status = %s, completed_at = %s, error_message = %s,
                            worker_id = NULL, lease_until = NULL
                        WHERE id = %s
                        """,
                        (JobStatus.FAILED_PERMANENT, now, error_message, job_id)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    logger.warning(f"Job {job_id} marked as FAILED_PERMANENT after {attempt_count} attempts")
                    return True
                else:
                    # Schedule retry with backoff
                    next_delay = RETRY_DELAYS.get(attempt_count + 1, timedelta(hours=2))
                    next_retry_at = _to_postgres_timestamp(datetime.now(timezone.utc) + next_delay)
                    
                    cur.execute(
                        """
                        UPDATE document_jobs
                        SET status = %s, attempt_count = attempt_count + 1,
                            last_error = %s, error_message = %s,
                            worker_id = NULL, lease_until = NULL, next_retry_at = %s
                        WHERE id = %s
                        """,
                        (JobStatus.QUEUED, error_message, error_message, next_retry_at, job_id)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    logger.info(f"Job {job_id} scheduled for retry {attempt_count + 1}/{MAX_RETRIES} at {next_retry_at}")
                    return True
        except Exception as e:
            logger.error(f"Error completing job: {e}")
            return False
    
    def release_lease(self, job_id: int) -> bool:
        """Release a job's lease without completing it (e.g., worker shutdown).
        
        Args:
            job_id: ID of the job
            
        Returns:
            True if release succeeded
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                UPDATE document_jobs
                SET status = %s, worker_id = NULL, lease_until = NULL
                WHERE id = %s AND status = %s
                """,
                (JobStatus.QUEUED, job_id, JobStatus.IN_PROGRESS)
            )
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Released lease for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error releasing lease: {e}")
            return False
    
    def renew_lease(self, job_id: int, worker_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> bool:
        """Renew a job's lease.
        
        Args:
            job_id: ID of the job
            worker_id: ID of the worker (must match current holder)
            lease_seconds: New lease duration
            
        Returns:
            True if renewal succeeded
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            lease_until = _to_postgres_timestamp(datetime.now(timezone.utc) + timedelta(seconds=lease_seconds))
            
            cur.execute(
                """
                UPDATE document_jobs
                SET lease_until = %s
                WHERE id = %s AND worker_id = %s AND status = %s
                """,
                (lease_until, job_id, worker_id, JobStatus.IN_PROGRESS)
            )
            rows = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            
            if rows > 0:
                logger.debug(f"Renewed lease for job {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error renewing lease: {e}")
            return False
    
    def recover_expired_leases(self) -> int:
        """Recover jobs with expired leases (Phase 3B: lease recovery).
        
        Returns jobs to QUEUED status so they can be re-claimed.
        
        Returns:
            Number of jobs recovered
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            now = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            cur.execute(
                """
                UPDATE document_jobs
                SET status = %s, worker_id = NULL, claimed_at = NULL, lease_until = NULL
                WHERE status = %s AND lease_until < %s
                """,
                (JobStatus.QUEUED, JobStatus.IN_PROGRESS, now)
            )
            recovered = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            
            if recovered > 0:
                logger.info(f"Recovered {recovered} expired jobs")
            return recovered
        except Exception as e:
            logger.error(f"Error recovering leases: {e}")
            return 0
    
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
    
    # =========================================================================
    # Evidence Lineage Methods (Phase 5)
    # =========================================================================
    
    def record_evidence(self, entity_id: int, document_id: int, 
                        artifact_path: str = None, plugin_name: str = None,
                        confidence: float = 1.0, processing_time_ms: int = None,
                        version: str = None) -> int:
        """Record evidence lineage for an extracted entity.
        
        Tracks: entity → derived_from → document → derived_from → artifact
        
        Args:
            entity_id: ID of the entity
            document_id: ID of the source document
            artifact_path: Original file path
            plugin_name: Name of the extractor plugin
            confidence: Extraction confidence (0.0-1.0)
            processing_time_ms: Time taken to extract
            version: Plugin version for reproducibility
            
        Returns:
            Evidence record ID
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            created_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            cur.execute(
                """
                INSERT INTO evidence_lineage 
                (entity_id, document_id, artifact_path, plugin_name, confidence, processing_time_ms, version, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (entity_id, document_id, artifact_path, plugin_name, confidence, processing_time_ms, version, created_at)
            )
            evidence_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            return evidence_id
        except Exception as e:
            logger.error(f"Error recording evidence: {e}")
            return None
    
    def record_evidence_batch(self, document_id: int, artifact_path: str,
                               plugin_name: str, entities: list,
                               processing_time_ms: int = None,
                               version: str = None) -> int:
        """Record evidence for multiple entities extracted from a document.
        
        Args:
            document_id: ID of the source document
            artifact_path: Original file path
            plugin_name: Name of the extractor plugin
            entities: List of entity dicts with 'id' field
            processing_time_ms: Time taken to extract
            version: Plugin version
            
        Returns:
            Number of evidence records created
        """
        count = 0
        for entity in entities:
            entity_id = entity.get('id')
            if entity_id:
                evidence_id = self.record_evidence(
                    entity_id=entity_id,
                    document_id=document_id,
                    artifact_path=artifact_path,
                    plugin_name=plugin_name,
                    confidence=entity.get('confidence', 1.0),
                    processing_time_ms=processing_time_ms,
                    version=version
                )
                if evidence_id:
                    count += 1
        return count
    
    def get_entity_evidence(self, entity_id: int) -> list:
        """Get all evidence records for an entity.
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            List of evidence records with document and artifact info
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.id, e.entity_id, e.document_id, d.path as document_path,
                       e.artifact_path, e.plugin_name, e.confidence, 
                       e.processing_time_ms, e.version, e.created_at
                FROM evidence_lineage e
                JOIN documents d ON e.document_id = d.id
                WHERE e.entity_id = %s
                ORDER BY e.created_at DESC
                """,
                (entity_id,)
            )
            evidence = []
            for row in cur.fetchall():
                evidence.append({
                    'id': row[0],
                    'entity_id': row[1],
                    'document_id': row[2],
                    'document_path': row[3],
                    'artifact_path': row[4],
                    'plugin_name': row[5],
                    'confidence': row[6],
                    'processing_time_ms': row[7],
                    'version': row[8],
                    'created_at': row[9]
                })
            cur.close()
            conn.close()
            return evidence
        except Exception as e:
            logger.error(f"Error getting entity evidence: {e}")
            return []
    
    def get_document_evidence(self, document_id: int) -> list:
        """Get all evidence records for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of evidence records with entity info
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.id, e.entity_id, en.value as entity_value, en.type as entity_type,
                       e.document_id, e.artifact_path, e.plugin_name, e.confidence,
                       e.processing_time_ms, e.version, e.created_at
                FROM evidence_lineage e
                JOIN entities en ON e.entity_id = en.id
                WHERE e.document_id = %s
                ORDER BY e.created_at DESC
                """,
                (document_id,)
            )
            evidence = []
            for row in cur.fetchall():
                evidence.append({
                    'id': row[0],
                    'entity_id': row[1],
                    'entity_value': row[2],
                    'entity_type': row[3],
                    'document_id': row[4],
                    'artifact_path': row[5],
                    'plugin_name': row[6],
                    'confidence': row[7],
                    'processing_time_ms': row[8],
                    'version': row[9],
                    'created_at': row[10]
                })
            cur.close()
            conn.close()
            return evidence
        except Exception as e:
            logger.error(f"Error getting document evidence: {e}")
            return []
    
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

    # =========================================================================
    # Phase 4: Individual entity/event/location methods
    # =========================================================================

    def save_entity(self, entity_type: str, value: str, normalized_value: str = None) -> int:
        """Save a single entity and return its ID (Phase 4).
        
        Args:
            entity_type: Type of entity (PERSON, ORGANIZATION, etc.)
            value: The entity value
            normalized_value: Normalized form of the value
            
        Returns:
            Entity ID
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                INSERT INTO entities (type, value, normalized_value)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (entity_type, value, normalized_value or value.lower())
            )
            result = cur.fetchone()
            if result:
                entity_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM entities WHERE value = %s AND type = %s",
                    (value, entity_type)
                )
                row = cur.fetchone()
                entity_id = row[0] if row else None
            
            conn.commit()
            cur.close()
            conn.close()
            return entity_id
        except Exception as e:
            logger.error(f"Error saving entity: {e}")
            return None

    def add_entity_to_document(self, document_id: int, entity_id: int, occurrences: int = 1) -> bool:
        """Link an entity to a document (Phase 4).
        
        Args:
            document_id: Document ID
            entity_id: Entity ID
            occurrences: Number of occurrences
            
        Returns:
            True if linked successfully
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                """
                INSERT INTO document_entities (document_id, entity_id, occurrences)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id, entity_id) DO UPDATE SET occurrences = document_entities.occurrences + 1
                """,
                (document_id, entity_id, occurrences)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error linking entity to document: {e}")
            return False

    def save_event(self, timestamp, event_type: str, description: str) -> int:
        """Save a single event and return its ID (Phase 4).
        
        Args:
            timestamp: Event timestamp
            event_type: Type of event
            description: Event description
            
        Returns:
            Event ID
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            ts = _to_postgres_timestamp(timestamp) if timestamp else None
            
            cur.execute(
                """
                INSERT INTO events (timestamp, event_type, description)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (ts, event_type, description)
            )
            result = cur.fetchone()
            if result:
                event_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM events WHERE timestamp = %s AND event_type = %s AND description = %s",
                    (ts, event_type, description)
                )
                row = cur.fetchone()
                event_id = row[0] if row else None
            
            conn.commit()
            cur.close()
            conn.close()
            return event_id
        except Exception as e:
            logger.error(f"Error saving event: {e}")
            return None

    def add_event_to_document(self, document_id: int, event_id: int) -> bool:
        """Link an event to a document (Phase 4).
        
        Args:
            document_id: Document ID
            event_id: Event ID
            
        Returns:
            True if linked successfully
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
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
            return True
        except Exception as e:
            logger.error(f"Error linking event to document: {e}")
            return False

    def save_location(self, name: str, location_type: str = 'GENERAL',
                     address: str = None, city: str = None, state: str = None,
                     country: str = None, postal_code: str = None,
                     coordinates: tuple = None) -> int:
        """Save a single location and return its ID (Phase 4).
        
        Args:
            name: Location name
            location_type: Type of location
            address: Street address
            city: City
            state: State/Province
            country: Country
            postal_code: Postal/ZIP code
            coordinates: (latitude, longitude) tuple
            
        Returns:
            Location ID
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            lat = coordinates[0] if coordinates else None
            lng = coordinates[1] if coordinates else None
            
            cur.execute(
                """
                INSERT INTO locations (name, latitude, longitude)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (name, lat, lng)
            )
            result = cur.fetchone()
            if result:
                location_id = result[0]
            else:
                cur.execute(
                    "SELECT id FROM locations WHERE name = %s",
                    (name,)
                )
                row = cur.fetchone()
                location_id = row[0] if row else None
            
            conn.commit()
            cur.close()
            conn.close()
            return location_id
        except Exception as e:
            logger.error(f"Error saving location: {e}")
            return None

    def add_location_to_document(self, document_id: int, location_id: int) -> bool:
        """Link a location to a document (Phase 4).
        
        Args:
            document_id: Document ID
            location_id: Location ID
            
        Returns:
            True if linked successfully
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
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
            return True
        except Exception as e:
            logger.error(f"Error linking location to document: {e}")
            return False

    def save_embedding(self, document_id: int, vector: list, model: str = 'unknown') -> bool:
        """Save embedding vector for a document (Phase 4).
        
        Args:
            document_id: Document ID
            vector: Embedding vector as list of floats
            model: Embedding model name
            
        Returns:
            True if saved successfully
        """
        try:
            import json
            
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Convert list to JSON string for storage
            vector_json = json.dumps(vector)
            
            cur.execute(
                """
                INSERT INTO document_embeddings (document_id, embedding, model)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    model = EXCLUDED.model
                """,
                (document_id, vector_json, model)
            )
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Saved embedding for document {document_id} ({len(vector)} dimensions)")
            return True
        except Exception as e:
            logger.error(f"Error saving embedding: {e}")
            return False

    def get_embedding(self, document_id: int) -> dict:
        """Get embedding for a document (Phase 4).
        
        Args:
            document_id: Document ID
            
        Returns:
            Dict with 'vector' and 'model' keys, or None
        """
        try:
            import json
            
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                "SELECT embedding, model FROM document_embeddings WHERE document_id = %s",
                (document_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if row:
                return {
                    'vector': json.loads(row[0]),
                    'model': row[1]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

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