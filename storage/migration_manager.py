"""
Schema Migration Manager for Librarian.

This module provides automatic database schema migration handling to ensure
backward compatibility with older database versions while supporting new features.

Migration System:
- Migration files are named with version prefixes (e.g., 003_photo_metadata.sql)
- Each migration is recorded in the schema_migrations table after successful execution
- Migrations are applied in sorted order (by version number)
- Schema verification runs at startup before any operations begin

Required Columns (added in V5 - 005_artifact_inventory.sql):
- artifact_type: Classification of artifact type
- exists_on_disk: Whether file still exists on disk
- deleted_at: Timestamp when file was deleted
- lifecycle_state: Simplified lifecycle tracking

V2 databases (without these columns) are automatically upgraded on startup.
"""

import os
import re
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Status of a migration."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class MigrationInfo:
    """Information about a migration file."""
    version: str  # e.g., "003"
    name: str     # e.g., "003_photo_metadata.sql"
    description: str  # Human-readable description
    path: str     # Full path to migration file
    sql: str      # SQL content
    
    @property
    def version_int(self) -> int:
        """Get version as integer for sorting."""
        try:
            return int(self.version)
        except ValueError:
            return 0


@dataclass
class MigrationResult:
    """Result of a migration run."""
    success: bool
    current_version: int
    target_version: int
    applied_migrations: List[str]
    failed_migration: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: float = 0.0


class SchemaMigrationError(Exception):
    """Raised when schema migration fails."""
    
    def __init__(self, message: str, migration_name: str = None, details: str = None):
        self.migration_name = migration_name
        self.details = details
        super().__init__(message)


class SchemaVerificationError(Exception):
    """Raised when schema verification fails."""
    
    def __init__(self, message: str, missing_columns: List[str] = None):
        self.missing_columns = missing_columns or []
        super().__init__(message)


class MigrationManager:
    """
    Manages database schema migrations.
    
    This class handles:
    - Discovery of migration files
    - Execution of pending migrations
    - Schema verification before operations
    - Detailed logging of migration progress
    
    Usage:
        manager = MigrationManager(backend)
        result = manager.run_migrations()
        if not result.success:
            raise SchemaMigrationError(result.error_message)
    """
    
    # Required columns that must exist in the documents table
    REQUIRED_COLUMNS = [
        'artifact_type',
        'exists_on_disk',
        'deleted_at',
        'lifecycle_state'
    ]
    
    # Target schema version (derived from latest migration)
    TARGET_SCHEMA_VERSION = 5  # Corresponds to 005_artifact_inventory.sql
    
    def __init__(self, backend):
        """
        Initialize MigrationManager.
        
        Args:
            backend: PostgresBackend instance
        """
        self.backend = backend
        self._migrations_cache: Optional[List[MigrationInfo]] = None
    
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
    
    def _extract_version(self, filename: str) -> Tuple[Optional[str], str]:
        """
        Extract version number and description from migration filename.
        
        Args:
            filename: e.g., "003_photo_metadata.sql"
            
        Returns:
            Tuple of (version_str, description)
        """
        # Match pattern: NNN_description.sql
        match = re.match(r'^(\d+)_(.+)\.sql$', filename)
        if match:
            version = match.group(1)
            # Convert underscores to spaces for description
            description = match.group(2).replace('_', ' ')
            return version, description
        return None, filename
    
    def discover_migrations(self) -> List[MigrationInfo]:
        """
        Discover all migration files in the migrations directory.
        
        Only includes .sql files that match the naming pattern (e.g., 003_photo_metadata.sql).
        Excludes schema.sql and any non-matching files.
        
        Returns:
            List of MigrationInfo sorted by version number
        """
        if self._migrations_cache is not None:
            return self._migrations_cache
        
        migrations_dir = self._get_migrations_directory()
        
        if not os.path.exists(migrations_dir):
            logger.warning(f"Migrations directory not found: {migrations_dir}")
            self._migrations_cache = []
            return []
        
        migrations = []
        
        for filename in os.listdir(migrations_dir):
            # Skip non-SQL files and schema.sql
            if not filename.endswith('.sql') or filename == 'schema.sql':
                continue
            
            # Extract version number
            version, description = self._extract_version(filename)
            if version is None:
                logger.debug(f"Skipping migration (no version): {filename}")
                continue
            
            filepath = os.path.join(migrations_dir, filename)
            
            try:
                with open(filepath, 'r') as f:
                    sql = f.read()
            except Exception as e:
                logger.error(f"Error reading migration file {filename}: {e}")
                continue
            
            migrations.append(MigrationInfo(
                version=version,
                name=filename,
                description=description,
                path=filepath,
                sql=sql
            ))
        
        # Sort by version number
        migrations.sort(key=lambda m: m.version_int)
        self._migrations_cache = migrations
        
        return migrations
    
    def get_applied_migrations(self) -> Dict[str, datetime]:
        """
        Get all applied migrations from the schema_migrations table.
        
        Returns:
            Dict mapping migration names to their application timestamps
        """
        try:
            conn = self.backend._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT migration_name, applied_at 
                FROM schema_migrations 
                ORDER BY applied_at
            """)
            result = {row[0]: row[1] for row in cur.fetchall()}
            cur.close()
            conn.close()
            return result
        except Exception as e:
            logger.warning(f"Could not get applied migrations: {e}")
            return {}
    
    def get_current_schema_version(self) -> int:
        """
        Get the current schema version based on applied migrations.
        
        Returns:
            Highest version number of applied migrations, or 0 if none
        """
        applied = self.get_applied_migrations()
        if not applied:
            return 0
        
        max_version = 0
        for name in applied.keys():
            version, _ = self._extract_version(name)
            if version:
                max_version = max(max_version, int(version))
        
        return max_version
    
    def verify_required_columns(self) -> Tuple[bool, List[str]]:
        """
        Verify that all required columns exist in the documents table.
        
        Returns:
            Tuple of (all_exist, missing_columns)
        """
        try:
            conn = self.backend._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'documents'
            """)
            existing_columns = {row[0] for row in cur.fetchall()}
            cur.close()
            conn.close()
            
            missing = [col for col in self.REQUIRED_COLUMNS if col not in existing_columns]
            return len(missing) == 0, missing
            
        except Exception as e:
            logger.error(f"Error verifying required columns: {e}")
            return False, self.REQUIRED_COLUMNS
    
    def _ensure_migrations_table(self) -> bool:
        """Ensure the schema_migrations tracking table exists."""
        try:
            conn = self.backend._get_connection()
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
    
    def _record_migration(self, migration_name: str) -> bool:
        """Record that a migration has been applied."""
        try:
            conn = self.backend._get_connection()
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
    
    def _execute_migration_sql(self, migration: MigrationInfo) -> Tuple[bool, str]:
        """
        Execute the SQL statements in a migration file.
        
        Args:
            migration: MigrationInfo containing the SQL to execute
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            conn = self.backend._get_connection()
            cur = conn.cursor()
            
            # Split by semicolons
            raw_statements = migration.sql.split(';')
            
            for raw_stmt in raw_statements:
                # Split into lines and filter out comments
                lines = []
                for line in raw_stmt.split('\n'):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('--'):
                        continue
                    lines.append(line)
                
                stmt = '\n'.join(lines).strip()
                
                # Skip empty statements
                if not stmt:
                    continue
                
                try:
                    cur.execute(stmt)
                except Exception as e:
                    error_msg = f"SQL error in {migration.name}: {e}"
                    logger.error(error_msg)
                    conn.rollback()
                    cur.close()
                    conn.close()
                    return False, error_msg
            
            conn.commit()
            cur.close()
            conn.close()
            return True, ""
            
        except Exception as e:
            error_msg = f"Error executing migration {migration.name}: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def run_migrations(self) -> MigrationResult:
        """
        Run all pending migrations.
        
        This is the main entry point for migration execution.
        It:
        1. Discovers all migration files
        2. Checks which migrations have been applied
        3. Runs pending migrations in version order
        4. Records successful migrations
        5. Returns detailed result information
        
        Returns:
            MigrationResult with success status and details
            
        Raises:
            SchemaMigrationError: If migration fails (for integration with startup)
        """
        start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("SCHEMA MIGRATION STARTING")
        logger.info("=" * 60)
        
        # Ensure migrations table exists
        if not self._ensure_migrations_table():
            return MigrationResult(
                success=False,
                current_version=0,
                target_version=self.TARGET_SCHEMA_VERSION,
                applied_migrations=[],
                error_message="Failed to create migrations tracking table"
            )
        
        # Get current state
        applied_migrations = self.get_applied_migrations()
        current_version = self.get_current_schema_version()
        migrations = self.discover_migrations()
        
        # Determine target version from migrations
        target_version = migrations[-1].version_int if migrations else 0
        
        logger.info(f"Current schema version: {current_version}")
        logger.info(f"Target schema version: {target_version}")
        logger.info(f"Applied migrations: {list(applied_migrations.keys())}")
        logger.info(f"Discovered migrations: {[m.name for m in migrations]}")
        
        if not migrations:
            logger.info("No migration files found")
            return MigrationResult(
                success=True,
                current_version=current_version,
                target_version=target_version,
                applied_migrations=list(applied_migrations.keys()),
                duration_ms=(time.time() - start_time) * 1000
            )
        
        # Find pending migrations
        pending = [m for m in migrations if m.name not in applied_migrations]
        
        if not pending:
            logger.info("No pending migrations - schema is up to date")
            
            # Verify required columns exist even if no migrations needed
            columns_ok, missing = self.verify_required_columns()
            if not columns_ok:
                return MigrationResult(
                    success=False,
                    current_version=current_version,
                    target_version=target_version,
                    applied_migrations=list(applied_migrations.keys()),
                    error_message=f"Schema verification failed: missing columns {missing}"
                )
            
            return MigrationResult(
                success=True,
                current_version=current_version,
                target_version=target_version,
                applied_migrations=list(applied_migrations.keys()),
                duration_ms=(time.time() - start_time) * 1000
            )
        
        logger.info(f"Pending migrations: {[m.name for m in pending]}")
        
        # Run pending migrations
        applied_list = list(applied_migrations.keys())
        failed_migration = None
        error_message = None
        
        for migration in pending:
            logger.info(f"Applying migration: {migration.name}")
            logger.info(f"  Description: {migration.description}")
            
            success, error = self._execute_migration_sql(migration)
            
            if success:
                self._record_migration(migration.name)
                applied_list.append(migration.name)
                current_version = migration.version_int
                logger.info(f"  SUCCESS: Migration {migration.name} applied")
            else:
                failed_migration = migration.name
                error_message = error
                logger.error(f"  FAILED: {error}")
                break
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info("=" * 60)
        logger.info("SCHEMA MIGRATION COMPLETE")
        logger.info(f"  Success: {failed_migration is None}")
        logger.info(f"  Current version: {current_version if failed_migration is None else 'unknown'}")
        logger.info(f"  Target version: {target_version}")
        logger.info(f"  Applied migrations: {applied_list}")
        logger.info(f"  Duration: {duration_ms:.1f}ms")
        logger.info("=" * 60)
        
        if failed_migration:
            return MigrationResult(
                success=False,
                current_version=current_version,
                target_version=target_version,
                applied_migrations=applied_list,
                failed_migration=failed_migration,
                error_message=error_message,
                duration_ms=duration_ms
            )
        
        # Final verification
        columns_ok, missing = self.verify_required_columns()
        if not columns_ok:
            return MigrationResult(
                success=False,
                current_version=current_version,
                target_version=target_version,
                applied_migrations=applied_list,
                error_message=f"Post-migration verification failed: missing columns {missing}",
                duration_ms=duration_ms
            )
        
        return MigrationResult(
            success=True,
            current_version=current_version,
            target_version=target_version,
            applied_migrations=applied_list,
            duration_ms=duration_ms
        )
    
    def verify_schema(self) -> Tuple[bool, str]:
        """
        Verify the database schema is compatible with application requirements.
        
        This should be called at startup before any operations begin.
        
        Returns:
            Tuple of (is_compatible, error_message)
        """
        logger.info("Verifying database schema compatibility...")
        
        # Check if tables exist
        try:
            conn = self.backend._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'documents'
                )
            """)
            tables_exist = cur.fetchone()[0]
            cur.close()
            conn.close()
            
            if not tables_exist:
                return False, "Documents table does not exist. Please run database initialization."
        except Exception as e:
            return False, f"Error checking database tables: {e}"
        
        # Check required columns
        columns_ok, missing = self.verify_required_columns()
        if not columns_ok:
            msg = (
                f"Database schema is outdated. Missing required columns: {', '.join(missing)}. "
                f"Please run migrations to upgrade the database to schema version {self.TARGET_SCHEMA_VERSION}. "
                f"Current version: {self.get_current_schema_version()}"
            )
            logger.error(msg)
            return False, msg
        
        logger.info("Schema verification passed - all required columns exist")
        return True, ""


def run_migrations_for_backend(backend) -> MigrationResult:
    """
    Convenience function to run migrations for a backend.
    
    Args:
        backend: PostgresBackend instance
        
    Returns:
        MigrationResult
        
    Raises:
        SchemaMigrationError: If migrations fail
    """
    manager = MigrationManager(backend)
    result = manager.run_migrations()
    
    if not result.success:
        raise SchemaMigrationError(
            f"Migration failed: {result.error_message}",
            migration_name=result.failed_migration,
            details=result.error_message
        )
    
    return result


def verify_backend_schema(backend) -> None:
    """
    Verify backend schema compatibility.
    
    Args:
        backend: PostgresBackend instance
        
    Raises:
        SchemaVerificationError: If schema is not compatible
    """
    manager = MigrationManager(backend)
    is_compatible, error = manager.verify_schema()
    
    if not is_compatible:
        raise SchemaVerificationError(error)
