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
    EXTRACT_EXIF = 'extract_exif'
    EXTRACT_GPS = 'extract_gps'
    GENERATE_THUMBNAIL = 'generate_thumbnail'
    RUN_OCR = 'run_ocr'
    OBJECT_DETECTION = 'object_detection'
    TRANSCRIPTION = 'transcription'
    INVENTORY = 'inventory'


# Artifact type to job types mapping
# Each artifact type only gets jobs appropriate for its format
ARTIFACT_TYPE_JOBS = {
    'text': [
        JobType.EXTRACT_TEXT,
        JobType.EXTRACT_ENTITIES,
        JobType.EXTRACT_EVENTS,
        JobType.EXTRACT_LOCATIONS,
        JobType.GENERATE_EMBEDDINGS,
    ],
    'document': [
        JobType.EXTRACT_TEXT,
        JobType.EXTRACT_ENTITIES,
        JobType.EXTRACT_EVENTS,
        JobType.EXTRACT_LOCATIONS,
        JobType.GENERATE_EMBEDDINGS,
    ],
    'structured': [
        JobType.EXTRACT_TEXT,
        JobType.EXTRACT_ENTITIES,
        JobType.EXTRACT_EVENTS,
        JobType.EXTRACT_LOCATIONS,
        JobType.GENERATE_EMBEDDINGS,
    ],
    'image': [
        JobType.EXTRACT_PHOTO_METADATA,
        JobType.GENERATE_THUMBNAIL,
        JobType.RUN_OCR,
        JobType.OBJECT_DETECTION,
    ],
    'video': [
        JobType.EXTRACT_PHOTO_METADATA,
        JobType.GENERATE_THUMBNAIL,
        JobType.TRANSCRIPTION,
    ],
    'audio': [
        JobType.TRANSCRIPTION,
        JobType.GENERATE_EMBEDDINGS,
    ],
    'archive': [
        JobType.INVENTORY,
    ],
    'executable': [
        JobType.INVENTORY,
    ],
    'unknown': [
        # Default for unknown types - minimal processing
        JobType.INVENTORY,
    ],
}


# Image extensions for photo metadata extraction (Phase 1A: Evidence Timeline)
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif'}


# Job status
class JobStatus:
    QUEUED = 'QUEUED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    BLOCKED = 'BLOCKED'  # Waiting on prerequisites
    FAILED_PERMANENT = 'FAILED_PERMANENT'
    CANCELLED = 'CANCELLED'


# Job dependencies - what must complete before a job can run
# Format: job_type -> set of prerequisite job_types that must be COMPLETED
JOB_DEPENDENCIES = {
    'extract_entities': {'extract_text'},
    'extract_locations': {'extract_text'},
    'generate_embeddings': {'extract_text'},
}


# Invalid job types per artifact type (these jobs should NEVER be created)
# Images cannot do text extraction, text cannot do vision tasks
INVALID_JOBS_BY_ARTIFACT = {
    'image': {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'},
    'video': {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'},
    'audio': {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'},
    'archive': {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'},
    'executable': {'extract_text', 'extract_entities', 'extract_events', 'extract_locations'},
    'unknown': {'extract_text', 'extract_entities', 'extract_events', 'extract_locations',
                'object_detection', 'face_detection'},
    'text': {'object_detection', 'face_detection'},
    'document': {'object_detection', 'face_detection'},
    'structured': {'object_detection', 'face_detection'},
}


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

    def _get_migrations_directory(self) -> str:
        """Get the path to the migrations directory."""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'migrations'),
            '/app/storage/migrations',
            os.path.join(os.getcwd(), 'storage', 'migrations'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return possible_paths[0]

    def ensure_schema(self) -> bool:
        """
        Ensure database schema exists, creating it if necessary.

        Uses the MigrationManager as the only schema initialization mechanism.
        For fresh databases, MigrationManager runs 001_initial_schema.sql first.
        For existing databases, MigrationManager applies pending migrations.

        Returns:
            True if schema is ready, False on failure
        """
        if self._schema_verified:
            return True

        try:
            # Import here to avoid circular imports
            from storage.migration_manager import run_migrations_for_backend
            
            # Use MigrationManager for proper migration handling
            result = run_migrations_for_backend(self)
            
            if result.success:
                logger.info(f"Schema migration complete: version {result.current_version} (target: {result.target_version})")
                self._schema_verified = True
                return True
            else:
                logger.error(f"Schema migration failed: {result.error_message}")
                if result.failed_migration:
                    logger.error(f"Failed migration: {result.failed_migration}")
                return False

        except Exception as e:
            logger.error(f"Error during schema initialization: {e}")
            return False

    def save_document(self, document):
        """Save a document to the database.
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        
        A file exists immediately upon discovery. Parser availability does not affect existence.
        
        Canonical schema columns: path, extension, sha256, file_size, 
        character_count, parser, modified_time, status, status_updated_at,
        last_error, attempt_count, indexed_at, artifact_type, exists_on_disk,
        deleted_at, lifecycle_state
        
        Handles timestamp conversion: Unix epoch floats are converted to
        PostgreSQL-compatible datetime objects.
        
        Lifecycle States (legacy 'status' field):
        - DISCOVERED: File detected, document created immediately
        - METADATA_INDEXED: Basic metadata extracted
        - CONTENT_EXTRACTED: Text content available
        - ENTITY_EXTRACTED: Entities identified
        - EMBEDDED: Vector embeddings generated
        - COMPLETE: All processing finished
        - FAILED: Processing failed
        
        Artifact Types:
        - unknown: Default for undiscovered/unclassified artifacts
        - image: Photos, graphics (.jpg, .png, .gif, etc.)
        - document: PDFs, office docs, text (.pdf, .doc, .txt, etc.)
        - video: Movies, recordings (.mp4, .mov, etc.)
        - audio: Music, voice (.mp3, .wav, etc.)
        - archive: Compressed files (.zip, .tar, .gz, etc.)
        - structured: Data files (.csv, .json, .xml, .db, etc.)
        - executable: Binaries, scripts (.exe, .sh, .py, etc.)
        - other: Known but uncategorized
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
        # Default to DISCOVERED since save_document is called immediately upon discovery
        status = document.get('status', 'DISCOVERED')
        status_updated_at = _to_postgres_timestamp(datetime.now(timezone.utc))
        last_error = document.get('last_error')
        attempt_count = document.get('attempt_count', 1)
        
        # Artifact inventory fields
        # artifact_type: Classified based on extension, or 'unknown' if no parser
        artifact_type = document.get('artifact_type') or self._classify_artifact_type(extension, parser)
        # exists_on_disk: Always True for new documents (soft delete handled separately)
        exists_on_disk = document.get('exists_on_disk', True)
        # lifecycle_state: Simplified lifecycle view
        lifecycle_state = document.get('lifecycle_state', 'discovered')
        
        cur.execute(
            """
            INSERT INTO documents (path, extension, sha256, file_size, character_count, parser, modified_time, status, status_updated_at, last_error, attempt_count, artifact_type, exists_on_disk, lifecycle_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                attempt_count = EXCLUDED.attempt_count,
                artifact_type = EXCLUDED.artifact_type,
                exists_on_disk = EXCLUDED.exists_on_disk,
                lifecycle_state = EXCLUDED.lifecycle_state
            RETURNING id
            """,
            (path, extension, sha256, file_size, character_count, parser, modified_time, status, status_updated_at, last_error, attempt_count, artifact_type, exists_on_disk, lifecycle_state)
        )
        document_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return document_id
    
    def _classify_artifact_type(self, extension: str = None, parser: str = None) -> str:
        """Classify artifact type based on extension and parser.
        
        This is a fallback classifier used when artifact_type is not provided.
        The parser registry may provide better classification.
        
        Returns:
            Artifact type string: unknown, image, document, video, audio, archive, structured, executable, other
        """
        ext = (extension or '').lower()
        
        # Image types
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.tif', '.heic', '.heif'}
        if ext in image_exts:
            return 'image'
        
        # Video types
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        if ext in video_exts:
            return 'video'
        
        # Audio types
        audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'}
        if ext in audio_exts:
            return 'audio'
        
        # Archive types
        archive_exts = {'.zip', '.tar', '.gz', '.bz2', '.xz', '.rar', '.7z', '.tgz'}
        if ext in archive_exts:
            return 'archive'
        
        # Structured data types
        structured_exts = {'.csv', '.tsv', '.json', '.xml', '.yaml', '.yml', '.toml', '.db', '.sqlite', '.sql'}
        if ext in structured_exts:
            return 'structured'
        
        # Executable types
        exec_exts = {'.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.sh', '.bash', '.bat', '.cmd', '.ps1'}
        if ext in exec_exts:
            return 'executable'
        
        # Document types
        doc_exts = {'.pdf', '.doc', '.docx', '.odt', '.rtf', '.txt', '.md', '.rst'}
        if ext in doc_exts:
            return 'document'
        
        # Parser-based classification as fallback
        if parser:
            parser_lower = parser.lower()
            if 'image' in parser_lower or 'photo' in parser_lower:
                return 'image'
            if 'video' in parser_lower or 'media' in parser_lower:
                return 'video'
            if 'audio' in parser_lower or 'sound' in parser_lower:
                return 'audio'
            if 'archive' in parser_lower or 'compressed' in parser_lower:
                return 'archive'
            if 'text' in parser_lower or 'document' in parser_lower:
                return 'document'
        
        # Default to unknown - artifacts exist before classification
        return 'unknown'
    
    def _get_document_artifact_type(self, document_id: int) -> str:
        """Get the artifact_type for a document by its ID.
        
        Used by create_jobs_for_document to determine which jobs to create
        based on the document's artifact type.
        
        Args:
            document_id: ID of the document
            
        Returns:
            artifact_type string, or 'unknown' if not found
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT artifact_type FROM documents WHERE id = %s",
                (document_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0]:
                return row[0]
            return 'unknown'
        except Exception as e:
            logger.error(f"Error getting artifact_type for document {document_id}: {e}")
            return 'unknown'

    def save_collection(self, collection):
        """Save a collection to the database and return its ID."""
        conn = self._get_connection()
        cur = conn.cursor()

        created_at = _to_postgres_timestamp(
            collection.get('created_at') or datetime.now(timezone.utc)
        )

        cur.execute(
            """
            INSERT INTO collections (name, root_path, created_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                collection.get('name'),
                collection.get('root_path'),
                created_at,
            ),
        )
        collection_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return collection_id
    
    def discover_artifact(self, path: str, extension: str = None, file_size: int = None, modified_time = None, mime_type: str = None) -> int:
        """Create an artifact record immediately upon discovery.
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        A file exists immediately upon discovery. Parser availability does not affect existence.
        
        This method creates a minimal document record without requiring a parser.
        It is called by CollectionWatcher before any parsing is attempted.
        
        Args:
            path: Full path to the file
            extension: File extension (e.g., '.jpg')
            file_size: File size in bytes
            modified_time: Last modified timestamp
            mime_type: MIME type of the artifact (e.g., 'image/jpeg')
                       Persisted as Discovery Metadata - determined from extension
                       during discovery, no worker or parser dependency.
            
        Returns:
            Document ID if created, None on failure
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Convert timestamp
            mod_time = _to_postgres_timestamp(modified_time)
            
            # Classify artifact type based on extension
            artifact_type = self._classify_artifact_type(extension)
            
            # Default to DISCOVERED status
            status = 'DISCOVERED'
            status_updated_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            cur.execute(
                """
                INSERT INTO documents (
                    path, extension, file_size, modified_time, 
                    status, status_updated_at, artifact_type, 
                    exists_on_disk, lifecycle_state, mime_type
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (path) DO UPDATE SET
                    extension = EXCLUDED.extension,
                    file_size = EXCLUDED.file_size,
                    modified_time = EXCLUDED.modified_time,
                    exists_on_disk = TRUE,
                    deleted_at = NULL,
                    artifact_type = EXCLUDED.artifact_type,
                    mime_type = EXCLUDED.mime_type
                RETURNING id
                """,
                (path, extension, file_size, mod_time, status, status_updated_at, artifact_type, True, 'discovered', mime_type)
            )
            document_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Discovered artifact: {path} -> id:{document_id}, mime_type:{mime_type}")
            return document_id
        except Exception as e:
            logger.error(f"Error discovering artifact {path}: {e}")
            return None
    
    def mark_deleted(self, path: str) -> bool:
        """Mark a document as deleted (soft delete).
        
        ARTIFACT INVENTORY MODEL: Discovery precedes understanding.
        Deleted files are marked, not deleted. Records are preserved for auditability.
        
        Args:
            path: Document path to mark as deleted
            
        Returns:
            True if marked, False otherwise
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            deleted_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            cur.execute(
                """
                UPDATE documents
                SET exists_on_disk = FALSE,
                    deleted_at = %s,
                    status_updated_at = %s
                WHERE path = %s AND exists_on_disk = TRUE
                """,
                (deleted_at, deleted_at, path)
            )
            
            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            
            if updated > 0:
                logger.info(f"Marked as deleted: {path}")
                return True
            else:
                logger.info(f"Document not found or already deleted: {path}")
                return False
        except Exception as e:
            logger.error(f"Error marking deleted {path}: {e}")
            return False
    
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

    def save_photo_metadata(
        self,
        document_id: int,
        metadata: dict,
        plugin_name: str = None,
        engine_name: str = None,
        plugin_version: str = None,
        processed_at: datetime = None,
        artifact_hash: str = None
    ) -> bool:
        """Save photo metadata for a document (Phase 1A: Evidence Timeline).

        Operation Plugin Foundation: Now supports provenance tracking via plugin_name,
        engine_name, plugin_version, processed_at, and artifact_hash fields.

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
            plugin_name: Plugin that produced this observation (e.g., 'metadata.exif.pillow')
            engine_name: Engine used by plugin (e.g., 'pillow-exif')
            plugin_version: Version of the plugin (e.g., '1.0.0')
            processed_at: When this observation was created (defaults to now)
            artifact_hash: SHA256 hash of source artifact for integrity

        Returns:
            True if save succeeded
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Provenance defaults (Operation Plugin Foundation)
            plugin_name = plugin_name or 'metadata.exif.pillow'
            engine_name = engine_name or 'pillow-exif'
            plugin_version = plugin_version or '1.0.0'
            processed_at = processed_at or datetime.now(timezone.utc)
            artifact_hash = artifact_hash

            # Convert timestamps
            ts_original = _to_postgres_timestamp(metadata.get('timestamp_original'))
            ts_digitized = _to_postgres_timestamp(metadata.get('timestamp_digitized'))
            ts_metadata = _to_postgres_timestamp(metadata.get('timestamp_metadata'))
            ts_processed = _to_postgres_timestamp(processed_at)

            # Operation Plugin Foundation: Use new provenance columns
            # UNIQUE constraint is now (document_id, plugin_name, engine_name) for multi-engine support
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
                    plugin_name,
                    engine_name,
                    plugin_version,
                    processed_at,
                    artifact_hash,
                    raw_exif
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id, plugin_name, engine_name) DO UPDATE SET
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
                    plugin_name = EXCLUDED.plugin_name,
                    engine_name = EXCLUDED.engine_name,
                    plugin_version = EXCLUDED.plugin_version,
                    processed_at = EXCLUDED.processed_at,
                    artifact_hash = EXCLUDED.artifact_hash,
                    raw_exif = EXCLUDED.raw_exif
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
                    plugin_name,
                    engine_name,
                    plugin_version,
                    ts_processed,
                    artifact_hash,
                    psycopg.types.json.Jsonb(metadata.get('raw_exif', {})) if metadata.get('raw_exif') else None,
                )
            )
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Saved photo metadata for document {document_id} (plugin: {plugin_name}, engine: {engine_name})")
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
    
    def get_artifact_hash(self, document_id: int) -> Optional[str]:
        """
        Get the SHA256 hash of an artifact for provenance tracking.
        
        Operation Plugin Foundation: Added for provenance tracking.
        Every observation should include the hash of its source artifact.
        
        Args:
            document_id: ID of the document
            
        Returns:
            SHA256 hash of the artifact, or None if not found
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute(
                "SELECT sha256 FROM documents WHERE id = %s",
                (document_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if row and row[0]:
                return f"sha256:{row[0]}"
            return None
        except Exception as e:
            logger.error(f"Error getting artifact hash: {e}")
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
    
    def create_job(self, document_id: int, job_type: str, priority: int = 0,
                  worker_version: str = None, scan_snapshot_id: int = None) -> int:
        """Create a new job for a document with duplicate prevention and dependency handling.
        
        Args:
            document_id: ID of the document to process
            job_type: Type of job
            priority: Job priority (higher = more important)
            worker_version: Version of the worker (for scan idempotency)
            scan_snapshot_id: ID of the scan snapshot (for tracking)
            
        Returns:
            Job ID if created, None on failure or if duplicate exists
        """
        try:
            # Check for existing active job of this type
            if self.is_duplicate_job(document_id, job_type):
                logger.info(f"Skipping duplicate job: document={document_id} job={job_type}")
                return None
            
            conn = self._get_connection()
            cur = conn.cursor()
            created_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            # Insert job - database will also prevent duplicates via unique constraint
            cur.execute(
                """
                INSERT INTO document_jobs (document_id, job_type, priority, status, created_at, 
                                         worker_version, scan_snapshot_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id, job_type) DO NOTHING
                RETURNING id
                """,
                (document_id, job_type, priority, JobStatus.QUEUED, created_at, 
                 worker_version, scan_snapshot_id)
            )
            row = cur.fetchone()
            conn.commit()
            
            if row:
                job_id = row[0]
                logger.info(f"Created job {job_id}: {job_type} for document {document_id}")
                
                # Check if job should be blocked due to missing prerequisites
                all_met, reason = self.check_job_prerequisites(document_id, job_type)
                if not all_met:
                    self.block_job(job_id, reason)
                    logger.info(f"Blocking job: document={document_id} job={job_type} reason={reason}")
                
                cur.close()
                conn.close()
                return job_id
            else:
                cur.close()
                conn.close()
                logger.info(f"Skipping duplicate job: document={document_id} job={job_type}")
                return None
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return None
    
    def create_jobs_for_document(self, document_id: int, job_types: list = None,
                                worker_version: str = None, scan_snapshot_id: int = None) -> list:
        """Create multiple jobs for a document based on artifact_type.
        
        ARCHITECTURE REQUIREMENT: Job scheduling must depend on artifact_type.
        
        If job_types is None, the document's artifact_type is looked up and
        the appropriate jobs are created based on the plugin registry.
        
        This prevents binary artifacts (images, videos, archives, executables)
        from entering the text extraction pipeline, which causes:
        - "No content found for document XXX"
        - "PostgreSQL text fields cannot contain NUL bytes"
        
        P13 Plugin Registry:
        - Only enabled plugins generate jobs
        - Prevents queue pollution from unsupported job types
        
        ARTIFACT TYPE VALIDATION:
        - Image artifacts may never receive: extract_text, extract_entities, extract_events, extract_locations
        - Text artifacts may never receive: object_detection, face_detection
        
        Args:
            document_id: ID of the document
            job_types: List of job types to create. If None, uses artifact_type mapping.
            worker_version: Version of the worker (for scan idempotency)
            scan_snapshot_id: ID of the scan snapshot (for tracking)
            
        Returns:
            List of created job IDs
        """
        # Get artifact type for validation
        artifact_type = self._get_document_artifact_type(document_id)
        invalid_jobs = self.get_invalid_jobs_for_artifact(artifact_type)
        
        # If job_types is not specified, determine based on artifact_type
        if job_types is None:
            # P13: Use plugin registry to determine job types
            try:
                from registry.plugin_registry import get_plugin_registry
                registry = get_plugin_registry()
                job_types = registry.get_job_types_for_artifact(artifact_type)
                
                # For non-image artifacts, also include text extraction jobs
                # (plugin registry only handles image/video plugins)
                if artifact_type in ('text', 'document', 'structured'):
                    job_types = ARTIFACT_TYPE_JOBS.get(
                        artifact_type,
                        [JobType.EXTRACT_TEXT]
                    )
                
                # Fallback for unknown artifact types
                if not job_types:
                    job_types = [JobType.INVENTORY]
                    
            except ImportError:
                # Fallback to hardcoded mapping if plugin registry unavailable
                logger.warning("Plugin registry unavailable, falling back to hardcoded mapping")
                job_types = ARTIFACT_TYPE_JOBS.get(
                    artifact_type, 
                    ARTIFACT_TYPE_JOBS.get('unknown', [JobType.INVENTORY])
                )
            
            logger.info(f"Creating jobs for document {document_id} based on artifact_type '{artifact_type}': {job_types}")
        
        # Filter out invalid jobs for this artifact type
        filtered_job_types = [jt for jt in job_types if jt not in invalid_jobs]
        skipped_jobs = [jt for jt in job_types if jt in invalid_jobs]
        
        if skipped_jobs:
            logger.warning(f"Skipping invalid jobs for artifact type '{artifact_type}': {skipped_jobs}")
        
        job_ids = []
        for job_type in filtered_job_types:
            job_id = self.create_job(
                document_id, job_type, priority=0,
                worker_version=worker_version, scan_snapshot_id=scan_snapshot_id
            )
            if job_id:
                job_ids.append(job_id)
        
        logger.info(f"Created {len(job_ids)} jobs for document {document_id} (filtered {len(skipped_jobs)} invalid)")
        return job_ids
    
    def claim_job(self, worker_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> dict:
        """Claim a queued job for processing with prerequisite checking.
        
        Uses SELECT FOR UPDATE to atomically claim the oldest queued job.
        Only claims jobs that are ready for retry (next_retry_at <= now).
        
        Jobs with unmet prerequisites are BLOCKED rather than retried.
        
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
            
            # Claim the next queued job
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
                job_id = row[0]
                document_id = row[1]
                job_type = row[2]
                
                # Check prerequisites before running
                all_met, reason = self.check_job_prerequisites(document_id, job_type)
                
                if not all_met:
                    # Block the job instead of running it
                    self.block_job(job_id, reason)
                    logger.info(f"Blocking job: document={document_id} job={job_type} reason={reason}")
                    cur.close()
                    conn.close()
                    # Try to claim another job
                    return self.claim_job(worker_id, lease_seconds)
                
                job = {
                    'id': job_id,
                    'document_id': document_id,
                    'job_type': job_type,
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
                
                # Get job info before closing cursor for unblocking
                cur.execute(
                    "SELECT document_id, job_type FROM document_jobs WHERE id = %s",
                    (job_id,)
                )
                row = cur.fetchone()
                document_id = row[0] if row else None
                job_type = row[1] if row else None
                
                conn.commit()
                cur.close()
                conn.close()
                logger.info(f"Job {job_id} marked as COMPLETED")
                
                # Unblock any dependent jobs now that prerequisites may be met
                if document_id and job_type:
                    self.unblock_dependent_jobs(document_id, job_type)
                
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
    # Job Dependency and Orchestration Methods
    # =========================================================================

    def check_job_prerequisites(self, document_id: int, job_type: str) -> tuple[bool, str]:
        """Check if all prerequisites for a job are met.
        
        Args:
            document_id: ID of the document
            job_type: Type of job to check
            
        Returns:
            Tuple of (all_met, reason) where reason explains what's missing if not met
        """
        prerequisites = JOB_DEPENDENCIES.get(job_type, set())
        if not prerequisites:
            return True, ""
        
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Check if any prerequisite is NOT completed
            cur.execute(
                """
                SELECT job_type FROM document_jobs
                WHERE document_id = %s AND job_type = ANY(%s) AND status != 'COMPLETED'
                """,
                (document_id, list(prerequisites))
            )
            incomplete = [row[0] for row in cur.fetchall()]
            cur.close()
            conn.close()
            
            if incomplete:
                reason = f"missing {', '.join(sorted(incomplete))}"
                return False, reason
            return True, ""
        except Exception as e:
            logger.error(f"Error checking prerequisites for job {job_type}: {e}")
            return False, str(e)

    def block_job(self, job_id: int, reason: str) -> bool:
        """Block a job that cannot execute due to missing prerequisites.
        
        Args:
            job_id: ID of the job to block
            reason: Why the job is blocked
            
        Returns:
            True if update succeeded
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE document_jobs
                SET status = %s, last_error = %s, error_message = %s
                WHERE id = %s AND status = %s
                """,
                (JobStatus.BLOCKED, reason, f"Blocked: {reason}", job_id, JobStatus.QUEUED)
            )
            rows = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            
            if rows > 0:
                logger.info(f"Blocking job {job_id}: {reason}")
            return rows > 0
        except Exception as e:
            logger.error(f"Error blocking job {job_id}: {e}")
            return False

    def unblock_dependent_jobs(self, document_id: int, completed_job_type: str) -> int:
        """Unblock jobs that were waiting for a completed job.
        
        When a job completes, any jobs that depend on it may now be able to run.
        
        Args:
            document_id: ID of the document
            completed_job_type: The job type that just completed
            
        Returns:
            Number of jobs unblocked
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Find blocked jobs that depend on the completed job type
            cur.execute(
                """
                UPDATE document_jobs j
                SET status = %s
                FROM job_prerequisites p
                WHERE j.document_id = %s
                  AND j.status = %s
                  AND p.job_type = j.job_type
                  AND p.requires_job_type = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM document_jobs dep
                      JOIN job_prerequisites pd ON dep.job_type = pd.requires_job_type
                      WHERE dep.document_id = j.document_id
                        AND pd.job_type = j.job_type
                        AND dep.status != 'COMPLETED'
                  )
                RETURNING j.id, j.job_type
                """,
                (JobStatus.QUEUED, document_id, JobStatus.BLOCKED, completed_job_type)
            )
            unblocked = cur.fetchall()
            conn.commit()
            cur.close()
            conn.close()
            
            count = len(unblocked)
            if count > 0:
                logger.info(f"Unblocked {count} jobs for document {document_id} after {completed_job_type} completed")
                for row in unblocked:
                    logger.debug(f"  Unblocked job {row[0]}: {row[1]}")
            
            return count
        except Exception as e:
            logger.error(f"Error unblocking dependent jobs: {e}")
            return 0

    def is_duplicate_job(self, document_id: int, job_type: str) -> bool:
        """Check if an active job of this type already exists for the document.
        
        Checks across QUEUED, IN_PROGRESS, and BLOCKED statuses.
        
        Args:
            document_id: ID of the document
            job_type: Type of job
            
        Returns:
            True if an active job of this type exists
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id FROM document_jobs
                WHERE document_id = %s 
                  AND job_type = %s
                  AND status IN ('QUEUED', 'IN_PROGRESS', 'BLOCKED')
                LIMIT 1
                """,
                (document_id, job_type)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row is not None
        except Exception as e:
            logger.error(f"Error checking duplicate job: {e}")
            return False

    def update_job_priority(self, document_id: int, job_type: str, priority: int) -> bool:
        """Update the priority of a queued job for a document.
        
        Only updates jobs that are in QUEUED status.
        
        Args:
            document_id: ID of the document
            job_type: Type of job
            priority: New priority value (higher = more important)
            
        Returns:
            True if a job was updated, False otherwise
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE document_jobs
                SET priority = %s
                WHERE document_id = %s 
                  AND job_type = %s
                  AND status = 'QUEUED'
                """,
                (priority, document_id, job_type)
            )
            updated = cur.rowcount > 0
            conn.commit()
            cur.close()
            conn.close()
            if updated:
                logger.debug(f"Updated priority to {priority} for job: document={document_id} job={job_type}")
            return updated
        except Exception as e:
            logger.error(f"Error updating job priority: {e}")
            return False

    def prioritize_thumbnail_jobs(self, document_ids: list[int], priority: int = 100) -> int:
        """Prioritize thumbnail generation jobs for visible documents.
        
        Updates priority for queued generate_thumbnail jobs matching the given documents.
        Only updates jobs that are not already at the target priority or higher.
        
        Args:
            document_ids: List of document IDs to prioritize
            priority: Priority level to set (default: 100 for viewport items)
            
        Returns:
            Number of jobs updated
        """
        if not document_ids:
            return 0
        
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE document_jobs
                SET priority = %s
                WHERE document_id = ANY(%s)
                  AND job_type = 'generate_thumbnail'
                  AND status = 'QUEUED'
                  AND priority < %s
                """,
                (priority, document_ids, priority)
            )
            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            if updated > 0:
                logger.info(f"Prioritized {updated} thumbnail jobs to priority {priority}")
            return updated
        except Exception as e:
            logger.error(f"Error prioritizing thumbnail jobs: {e}")
            return 0

    def create_or_update_thumbnail_job(self, document_id: int, priority: int = 50) -> int:
        """Create or update priority of a thumbnail generation job for a document.
        
        If a job already exists in QUEUED status, updates its priority.
        If no job exists, creates a new one with the specified priority.
        
        Args:
            document_id: ID of the document
            priority: Priority level (default: 50 for current folder)
            
        Returns:
            Job ID if created/updated, None on failure
        """
        try:
            # First check if job exists in QUEUED status
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, priority FROM document_jobs
                WHERE document_id = %s 
                  AND job_type = 'generate_thumbnail'
                  AND status = 'QUEUED'
                LIMIT 1
                """,
                (document_id,)
            )
            row = cur.fetchone()
            
            if row:
                job_id = row[0]
                current_priority = row[1]
                # Update priority only if new priority is higher
                if priority > current_priority:
                    cur.execute(
                        """
                        UPDATE document_jobs
                        SET priority = %s
                        WHERE id = %s
                        """,
                        (priority, job_id)
                    )
                    conn.commit()
                    logger.debug(f"Updated thumbnail job {job_id} priority from {current_priority} to {priority}")
                cur.close()
                conn.close()
                return job_id
            
            # No existing job - create new one
            cur.close()
            
            created_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO document_jobs (document_id, job_type, priority, status, created_at)
                VALUES (%s, 'generate_thumbnail', %s, %s, %s)
                ON CONFLICT (document_id, job_type) DO NOTHING
                RETURNING id
                """,
                (document_id, priority, JobStatus.QUEUED, created_at)
            )
            row = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            
            if row:
                job_id = row[0]
                logger.debug(f"Created thumbnail job {job_id} for document {document_id} with priority {priority}")
                return job_id
            
            return None
        except Exception as e:
            logger.error(f"Error creating/updating thumbnail job: {e}")
            return None

    def create_scan_snapshot(self, collection_id: int, scan_path: str, file_hash: str, 
                           artifact_type: str = None, worker_version: str = None) -> int:
        """Create a snapshot entry for an artifact in a scan.
        
        Used for idempotent rescans - tracks what was processed.
        
        Args:
            collection_id: ID of the collection
            scan_path: Path of the file
            file_hash: SHA256 hash of the file
            artifact_type: Classified artifact type
            worker_version: Version of the workers
            
        Returns:
            Snapshot ID if created, None on failure
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            created_at = _to_postgres_timestamp(datetime.now(timezone.utc))
            
            cur.execute(
                """
                INSERT INTO scan_snapshots (collection_id, scan_path, file_hash, artifact_type, worker_version, processed_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (scan_path, file_hash) DO UPDATE SET
                    artifact_type = COALESCE(EXCLUDED.artifact_type, scan_snapshots.artifact_type),
                    worker_version = EXCLUDED.worker_version,
                    processed_at = EXCLUDED.processed_at
                RETURNING id
                """,
                (collection_id, scan_path, file_hash, artifact_type, worker_version, created_at)
            )
            snapshot_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            return snapshot_id
        except Exception as e:
            logger.error(f"Error creating scan snapshot: {e}")
            return None

    def check_scan_snapshot_exists(self, scan_path: str, file_hash: str, 
                                   worker_version: str = None) -> bool:
        """Check if a scan snapshot exists and is current.
        
        Args:
            scan_path: Path of the file
            file_hash: SHA256 hash of the file
            worker_version: Version of the workers (if changed, snapshot is stale)
            
        Returns:
            True if snapshot exists and is current
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            if worker_version:
                cur.execute(
                    """
                    SELECT id FROM scan_snapshots
                    WHERE scan_path = %s AND file_hash = %s AND worker_version = %s
                    LIMIT 1
                    """,
                    (scan_path, file_hash, worker_version)
                )
            else:
                cur.execute(
                    """
                    SELECT id FROM scan_snapshots
                    WHERE scan_path = %s AND file_hash = %s
                    LIMIT 1
                    """,
                    (scan_path, file_hash)
                )
            
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row is not None
        except Exception as e:
            logger.error(f"Error checking scan snapshot: {e}")
            return False

    def get_invalid_jobs_for_artifact(self, artifact_type: str) -> set:
        """Get the set of invalid job types for an artifact type.
        
        Args:
            artifact_type: The artifact type
            
        Returns:
            Set of invalid job type strings
        """
        return INVALID_JOBS_BY_ARTIFACT.get(artifact_type, set())

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
        """Load a collection by ID or name."""
        if collection_id is None and name is None:
            raise ValueError("Either collection_id or name must be provided")

        conn = self._get_connection()
        cur = conn.cursor()

        if collection_id is not None:
            cur.execute(
                """
                SELECT id, name, root_path, created_at
                FROM collections
                WHERE id = %s
                """,
                (collection_id,),
            )
        else:
            cur.execute(
                """
                SELECT id, name, root_path, created_at
                FROM collections
                WHERE name = %s
                """,
                (name,),
            )

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            return None

        return {
            'id': row[0],
            'name': row[1],
            'root_path': row[2],
            'created_at': row[3],
        }

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
    # =============================================================================
    # Trace View Methods (Operation TRACE v2)
    # =============================================================================

    def get_trace_filters(self) -> dict:
        """
        Get available filters for the Trace view.
        
        Returns collapsible filter groups for:
        - Devices (cameras)
        - Collections
        - Years
        - Sources
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            groups = []
            
            # Devices (cameras) group
            cur.execute("""
                SELECT 
                    COALESCE(camera_make, 'Unknown') || ' ' || COALESCE(camera_model, '') as camera,
                    COUNT(*) as count,
                    camera_make IS NULL OR camera_make = '' as is_unknown
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                WHERE d.status != 'DELETED'
                GROUP BY camera_make, camera_model
                ORDER BY is_unknown ASC, count DESC
            """)
            camera_options = []
            has_unknown = False
            for row in cur.fetchall():
                camera = row[0].strip()
                is_unknown = row[2]
                if is_unknown:
                    has_unknown = True
                    camera_options.append({
                        'id': 'Unknown Device',
                        'label': 'Unknown Device',
                        'count': row[1],
                        'checked': False
                    })
                elif camera:
                    camera_options.append({
                        'id': camera,
                        'label': camera,
                        'count': row[1],
                        'checked': True
                    })
            
            # Add Unknown Device toggle option
            if has_unknown:
                groups.append({
                    'id': 'devices',
                    'label': 'Devices',
                    'expanded': True,
                    'options': camera_options,
                    'has_unknown': True
                })
            elif camera_options:
                groups.append({
                    'id': 'devices',
                    'label': 'Devices',
                    'expanded': True,
                    'options': camera_options
                })
            
            # Collections group
            cur.execute("""
                SELECT 
                    c.id::text,
                    COALESCE(c.name, 'Uncategorized'),
                    COUNT(DISTINCT d.id) as count
                FROM collections c
                JOIN documents d ON c.id = d.collection_id
                WHERE d.status != 'DELETED'
                GROUP BY c.id, c.name
                ORDER BY count DESC
            """)
            collection_options = []
            for row in cur.fetchall():
                collection_options.append({
                    'id': row[0],
                    'label': row[1],
                    'count': row[2],
                    'checked': True
                })
            if collection_options:
                groups.append({
                    'id': 'collections',
                    'label': 'Collections',
                    'expanded': True,
                    'options': collection_options
                })
            
            # Years group
            cur.execute("""
                SELECT 
                    EXTRACT(YEAR FROM pm.timestamp_original)::int as year,
                    COUNT(*) as count
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                WHERE pm.timestamp_original IS NOT NULL
                    AND d.status != 'DELETED'
                GROUP BY EXTRACT(YEAR FROM pm.timestamp_original)
                ORDER BY year DESC
            """)
            year_options = []
            for row in cur.fetchall():
                if row[0]:
                    year_options.append({
                        'id': str(row[0]),
                        'label': str(row[0]),
                        'count': row[1],
                        'checked': True
                    })
            if year_options:
                groups.append({
                    'id': 'years',
                    'label': 'Years',
                    'expanded': True,
                    'options': year_options
                })
            
            # Time Range group - returns min/max timestamps for date pickers
            cur.execute("""
                SELECT 
                    MIN(pm.timestamp_original) as min_date,
                    MAX(pm.timestamp_original) as max_date
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                WHERE pm.timestamp_original IS NOT NULL
                    AND d.status != 'DELETED'
            """)
            time_range_row = cur.fetchone()
            if time_range_row and time_range_row[0]:
                groups.append({
                    'id': 'timeRange',
                    'label': 'Time Range',
                    'expanded': False,
                    'options': [],
                    'min_date': time_range_row[0].isoformat() if time_range_row[0] else None,
                    'max_date': time_range_row[1].isoformat() if time_range_row[1] else None
                })
            
            # Sources group (GPS, OCR, AI, Manual based on metadata availability)
            cur.execute("""
                SELECT 
                    (CASE 
                        WHEN pm.gps_latitude IS NOT NULL THEN 'gps'
                        ELSE NULL 
                    END) as source,
                    COUNT(*) as count
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                WHERE d.status != 'DELETED'
                    AND pm.gps_latitude IS NOT NULL
                GROUP BY source
            """)
            source_options = []
            for row in cur.fetchall():
                if row[0]:
                    source_options.append({
                        'id': row[0],
                        'label': 'GPS EXIF',
                        'count': row[1],
                        'checked': True
                    })
            if source_options:
                groups.append({
                    'id': 'sources',
                    'label': 'Sources',
                    'expanded': False,
                    'options': source_options
                })
            
            # Get total count
            cur.execute("SELECT COUNT(*) FROM documents WHERE status != 'DELETED'")
            total_items = cur.fetchone()[0] or 0
            
            cur.close()
            conn.close()
            
            return {
                'groups': groups,
                'total_items': total_items
            }
        except Exception as e:
            logger.error(f"Error getting trace filters: {e}")
            return {'groups': [], 'total_items': 0}

    def get_trace_data(
        self,
        cameras: list = None,
        collections: list = None,
        years: list = None,
        sources: list = None,
        start_date: str = None,
        end_date: str = None,
        include_unknown_device: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> dict:
        """
        Get Trace data with filters applied.
        
        Returns both map markers and event stream items.
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Build filter conditions
            conditions = ["d.status != 'DELETED'"]
            params = []
            
            # Camera filter (excluding Unknown Device unless explicitly included)
            if cameras:
                known_cameras = [c for c in cameras if c != 'Unknown Device']
                if known_cameras:
                    camera_placeholders = ','.join(['%s'] * len(known_cameras))
                    conditions.append(f"(pm.camera_make || ' ' || COALESCE(pm.camera_model, '')) IN ({camera_placeholders})")
                    params.extend(known_cameras)
                elif not include_unknown_device:
                    # If only "Unknown Device" is selected but it's not included, exclude all
                    conditions.append("(pm.camera_make IS NULL OR pm.camera_make = '')")
            
            # Include/exclude unknown devices based on filter
            if cameras and 'Unknown Device' not in cameras and not include_unknown_device:
                conditions.append("(pm.camera_make IS NOT NULL AND pm.camera_make != '')")
            
            # Time range filter
            if start_date:
                conditions.append("pm.timestamp_original >= %s")
                params.append(start_date)
            if end_date:
                conditions.append("pm.timestamp_original <= %s")
                params.append(end_date)
            
            # Collection filter
            if collections:
                collection_placeholders = ','.join(['%s'] * len(collections))
                conditions.append(f"d.collection_id IN ({collection_placeholders})")
                params.extend(collections)
            
            # Year filter
            if years:
                year_placeholders = ','.join(['%s'] * len(years))
                conditions.append(f"EXTRACT(YEAR FROM pm.timestamp_original)::int IN ({year_placeholders})")
                params.extend(years)
            
            # Source filter (GPS only)
            if sources:
                if 'gps' in sources:
                    conditions.append("pm.gps_latitude IS NOT NULL AND pm.gps_longitude IS NOT NULL")
            
            where_clause = " AND ".join(conditions)
            
            # Get total count
            count_sql = f"""
                SELECT COUNT(*)
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                WHERE {where_clause}
            """
            cur.execute(count_sql, params)
            total = cur.fetchone()[0] or 0
            
            # Get map markers (photos with GPS)
            markers_sql = f"""
                SELECT 
                    pm.document_id,
                    pm.gps_latitude,
                    pm.gps_longitude,
                    pm.timestamp_original,
                    pm.camera_make,
                    pm.camera_model,
                    d.path as filename,
                    d.thumbnail_path,
                    pm.gps_altitude,
                    c.id as collection_id,
                    c.name as collection_name,
                    EXTRACT(YEAR FROM pm.timestamp_original)::int as year
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                LEFT JOIN collections c ON d.collection_id = c.id
                WHERE {where_clause}
                    AND pm.gps_latitude IS NOT NULL 
                    AND pm.gps_longitude IS NOT NULL
                ORDER BY pm.timestamp_original DESC
                LIMIT %s OFFSET %s
            """
            marker_params = params + [limit, offset]
            cur.execute(markers_sql, marker_params)
            
            markers = []
            for row in cur.fetchall():
                camera_make = row[4] or ''
                camera_model = row[5] or ''
                camera = f"{camera_make} {camera_model}".strip()
                
                markers.append({
                    'document_id': row[0],
                    'latitude': row[1],
                    'longitude': row[2],
                    'timestamp': row[3].isoformat() + 'Z' if row[3] else None,
                    'camera': camera or None,
                    'camera_make': row[4],
                    'camera_model': row[5],
                    'filename': row[6],
                    'thumbnail_path': row[7],
                    'altitude': row[8],
                    'collection_id': str(row[9]) if row[9] else None,
                    'collection_name': row[10],
                    'year': row[11]
                })
            
            # Get event stream items
            events_sql = f"""
                SELECT 
                    pm.document_id,
                    pm.timestamp_original,
                    pm.camera_make,
                    pm.camera_model,
                    pm.gps_latitude,
                    pm.gps_longitude,
                    d.path as filename,
                    d.thumbnail_path,
                    c.name as collection_name,
                    EXTRACT(YEAR FROM pm.timestamp_original)::int as year
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                LEFT JOIN collections c ON d.collection_id = c.id
                WHERE {where_clause}
                ORDER BY pm.timestamp_original DESC
                LIMIT %s OFFSET %s
            """
            cur.execute(events_sql, marker_params)
            
            events = []
            for row in cur.fetchall():
                camera_make = row[2] or ''
                camera_model = row[3] or ''
                camera = f"{camera_make} {camera_model}".strip()
                
                events.append({
                    'document_id': row[0],
                    'timestamp': row[1].isoformat() + 'Z' if row[1] else None,
                    'camera': camera or None,
                    'location': None,
                    'latitude': row[4],
                    'longitude': row[5],
                    'filename': row[6],
                    'thumbnail_path': row[7],
                    'collection_name': row[8],
                    'year': row[9]
                })
            
            # Get stats
            stats_sql = f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN pm.gps_latitude IS NOT NULL THEN 1 END) as with_gps,
                    COUNT(DISTINCT pm.camera_make || ' ' || COALESCE(pm.camera_model, '')) as unique_cameras,
                    MIN(EXTRACT(YEAR FROM pm.timestamp_original)) as min_year,
                    MAX(EXTRACT(YEAR FROM pm.timestamp_original)) as max_year
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                WHERE {where_clause}
            """
            cur.execute(stats_sql, params)
            stats_row = cur.fetchone()
            
            cur.close()
            conn.close()
            
            return {
                'markers': markers,
                'events': events,
                'stats': {
                    'total': stats_row[0] or 0,
                    'with_gps': stats_row[1] or 0,
                    'unique_cameras': stats_row[2] or 0,
                    'year_range': {
                        'min': int(stats_row[3]) if stats_row[3] else None,
                        'max': int(stats_row[4]) if stats_row[4] else None
                    }
                },
                'pagination': {
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'returned': len(events)
                }
            }
        except Exception as e:
            logger.error(f"Error getting trace data: {e}")
            return {
                'markers': [],
                'events': [],
                'stats': {
                    'total': 0,
                    'with_gps': 0,
                    'unique_cameras': 0,
                    'year_range': {'min': None, 'max': None}
                },
                'pagination': {
                    'total': 0,
                    'limit': limit,
                    'offset': offset,
                    'returned': 0
                }
            }

    def get_trace_photo_detail(self, document_id: int) -> dict:
        """
        Get full photo metadata for Trace view.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dict with full photo metadata or None
        """
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    pm.document_id,
                    d.path as filename,
                    d.path,
                    pm.timestamp_original,
                    pm.timestamp_digitized,
                    pm.gps_latitude,
                    pm.gps_longitude,
                    pm.gps_altitude,
                    pm.camera_make,
                    pm.camera_model,
                    pm.lens_model,
                    pm.width,
                    pm.height,
                    pm.orientation,
                    pm.file_format,
                    d.thumbnail_path,
                    c.name as collection_name,
                    pm.extracted_at
                FROM photo_metadata pm
                JOIN documents d ON pm.document_id = d.id
                LEFT JOIN collections c ON d.collection_id = c.id
                WHERE pm.document_id = %s
            """, (document_id,))
            
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if not row:
                return None
            
            return {
                'document_id': row[0],
                'filename': row[1],
                'path': row[2],
                'timestamp': row[3].isoformat() + 'Z' if row[3] else None,
                'timestamp_digitized': row[4].isoformat() + 'Z' if row[4] else None,
                'gps_latitude': row[5],
                'gps_longitude': row[6],
                'gps_altitude': row[7],
                'camera_make': row[8],
                'camera_model': row[9],
                'lens_model': row[10],
                'width': row[11] or 0,
                'height': row[12] or 0,
                'orientation': row[13],
                'file_format': row[14] or 'UNKNOWN',
                'thumbnail_path': row[15],
                'collection_name': row[16],
                'extracted_at': row[17].isoformat() + 'Z' if row[17] else None
            }
        except Exception as e:
            logger.error(f"Error getting trace photo detail: {e}")
            return None

    # =============================================================================
    # Object Detection Methods (Operation Object Detection)
    # =============================================================================

    def save_detections(
        self,
        artifact_id: int,
        detections: list,
        plugin_name: str = None,
        engine_name: str = None,
        plugin_version: str = None,
        processed_at: datetime = None,
        artifact_hash: str = None
    ) -> int:
        """Save object detection observations to the database.

        Operation Object Detection: Stores detections with provenance tracking.

        Args:
            artifact_id: ID of the artifact/document
            detections: List of detection dicts with label, confidence, bbox
            plugin_name: Plugin name for provenance (e.g., 'vision.object-detection.yolo')
            engine_name: Engine name for provenance (e.g., 'yolo')
            plugin_version: Plugin version for provenance (e.g., 'v8n')
            processed_at: Timestamp when processing occurred
            artifact_hash: Hash of the artifact for reprocessing detection

        Returns:
            Number of detections saved
        """
        if not detections:
            return 0

        from datetime import timezone
        if processed_at is None:
            processed_at = datetime.now(timezone.utc)

        conn = self._get_connection()
        cur = conn.cursor()
        saved_count = 0

        try:
            for detection in detections:
                cur.execute(
                    """
                    INSERT INTO object_detections (
                        artifact_id, plugin_name, engine_name, plugin_version,
                        processed_at, artifact_hash,
                        label, confidence,
                        bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                        bbox_norm_x1, bbox_norm_y1, bbox_norm_x2, bbox_norm_y2,
                        source
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s
                    )
                    """,
                    (
                        artifact_id,
                        plugin_name or 'vision.object-detection.yolo',
                        engine_name or 'yolo',
                        plugin_version or 'v8n',
                        processed_at,
                        artifact_hash,
                        detection['label'],
                        detection['confidence'],
                        detection['bbox_x1'],
                        detection['bbox_y1'],
                        detection['bbox_x2'],
                        detection['bbox_y2'],
                        detection.get('bbox_norm_x1'),
                        detection.get('bbox_norm_y1'),
                        detection.get('bbox_norm_x2'),
                        detection.get('bbox_norm_y2'),
                        'yolo'
                    )
                )
                saved_count += 1

            conn.commit()
            logger.info(f"Saved {saved_count} object detections for artifact {artifact_id}")
            return saved_count

        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving object detections: {e}")
            raise
        finally:
            cur.close()
            conn.close()

    def get_detections(self, artifact_id: int) -> list:
        """Get all object detections for an artifact.

        Args:
            artifact_id: ID of the artifact/document

        Returns:
            List of detection dicts
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT
                    id, artifact_id, plugin_name, engine_name, plugin_version,
                    processed_at, artifact_hash,
                    label, confidence,
                    bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                    bbox_norm_x1, bbox_norm_y1, bbox_norm_x2, bbox_norm_y2,
                    source, created_at
                FROM object_detections
                WHERE artifact_id = %s AND deleted_at IS NULL
                ORDER BY confidence DESC
                """,
                (artifact_id,)
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()

            return [
                {
                    'id': row[0],
                    'artifact_id': row[1],
                    'plugin_name': row[2],
                    'engine_name': row[3],
                    'plugin_version': row[4],
                    'processed_at': row[5].isoformat() if row[5] else None,
                    'artifact_hash': row[6],
                    'label': row[7],
                    'confidence': float(row[8]),
                    'bbox_x1': row[9],
                    'bbox_y1': row[10],
                    'bbox_x2': row[11],
                    'bbox_y2': row[12],
                    'bbox_norm_x1': float(row[13]) if row[13] else None,
                    'bbox_norm_y1': float(row[14]) if row[14] else None,
                    'bbox_norm_x2': float(row[15]) if row[15] else None,
                    'bbox_norm_y2': float(row[16]) if row[16] else None,
                    'source': row[17],
                    'created_at': row[18].isoformat() if row[18] else None,
                }
                for row in rows
            ]

        except Exception as e:
            cur.close()
            conn.close()
            logger.error(f"Error getting detections: {e}")
            return []

    def search_detections_by_label(self, label: str, limit: int = 100) -> list:
        """Search for artifacts by detected object label.

        Operation Object Detection: Enables object=car style queries.

        Args:
            label: Object label to search for (e.g., 'car', 'person')
            limit: Maximum number of results

        Returns:
            List of artifact IDs with that detection
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            # Search for unique labels (aggregated)
            cur.execute(
                """
                SELECT DISTINCT ON (artifact_id)
                    artifact_id,
                    label,
                    MAX(confidence) as max_confidence,
                    COUNT(*) as detection_count
                FROM object_detections
                WHERE label ILIKE %s AND deleted_at IS NULL
                GROUP BY artifact_id, label
                ORDER BY artifact_id, MAX(confidence) DESC
                LIMIT %s
                """,
                (f'%{label}%', limit)
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()

            return [
                {
                    'artifact_id': row[0],
                    'label': row[1],
                    'max_confidence': float(row[2]),
                    'detection_count': row[3],
                }
                for row in rows
            ]

        except Exception as e:
            cur.close()
            conn.close()
            logger.error(f"Error searching detections: {e}")
            return []

    def delete_detections(self, artifact_id: int) -> int:
        """Soft delete all detections for an artifact (for reprocessing).

        Args:
            artifact_id: ID of the artifact

        Returns:
            Number of detections deleted
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                UPDATE object_detections
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE artifact_id = %s AND deleted_at IS NULL
                """,
                (artifact_id,)
            )
            deleted_count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Soft deleted {deleted_count} detections for artifact {artifact_id}")
            return deleted_count

        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            logger.error(f"Error deleting detections: {e}")
            raise

    def get_unique_labels(self, artifact_id: int = None) -> list:
        """Get all unique object labels in the system or for an artifact.

        Args:
            artifact_id: Optional artifact ID to filter by

        Returns:
            List of unique label strings
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            if artifact_id:
                cur.execute(
                    """
                    SELECT DISTINCT label
                    FROM object_detections
                    WHERE artifact_id = %s AND deleted_at IS NULL
                    ORDER BY label
                    """,
                    (artifact_id,)
                )
            else:
                cur.execute(
                    """
                    SELECT DISTINCT label
                    FROM object_detections
                    WHERE deleted_at IS NULL
                    ORDER BY label
                    """
                )

            rows = cur.fetchall()
            cur.close()
            conn.close()

            return [row[0] for row in rows]

        except Exception as e:
            cur.close()
            conn.close()
            logger.error(f"Error getting unique labels: {e}")
            return []
