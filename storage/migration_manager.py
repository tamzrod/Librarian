"""
Schema Migration Manager for Librarian.

This module provides automatic database schema migration handling to ensure
backward compatibility with older database versions while supporting new features.

Migration System:
- Migration files are named with version prefixes (e.g., 001_initial_schema.sql)
- Migration 001_initial_schema.sql creates the base schema for fresh databases
- Each migration is recorded in the schema_migrations table after successful execution
- Migrations are applied in sorted order (by version number)
- Schema verification runs at startup before any operations begin

Startup Sequence:
  Empty DB → 001_initial_schema.sql → remaining migrations → startup complete

Required Columns (added in V5 - 005_artifact_inventory.sql):
- artifact_type: Classification of artifact type
- exists_on_disk: Whether file still exists on disk
- deleted_at: Timestamp when file was deleted
- lifecycle_state: Simplified lifecycle tracking

Existing databases are automatically upgraded on startup through MigrationManager.
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
    - Bootstrap of base schema on fresh databases
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
    # Updated to 9 after adding 009_add_missing_indexes.sql
    TARGET_SCHEMA_VERSION = 9  # Corresponds to 009_add_missing_indexes.sql
    
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
        
        Only includes .sql files that match the naming pattern (e.g., 001_initial_schema.sql).
        All migrations including 001_initial_schema.sql are discovered and applied in order.
        
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
            # Skip non-SQL files
            if not filename.endswith('.sql'):
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
    
    def _split_sql_statements(self, sql: str) -> List[str]:
        """
        Split SQL by semicolons, respecting dollar-quoted strings ($$).
        
        PostgreSQL uses dollar-quoting for function bodies and DO blocks:
            DO $$ ... END $$;
            CREATE FUNCTION foo() AS $body$ ... $body$ LANGUAGE plpgsql;
        
        Dollar quotes work by matching tags. The tag (between $ signs) must match.
        
        Args:
            sql: Raw SQL content
            
        Returns:
            List of individual SQL statements
        """
        statements = []
        current = []
        i = 0
        n = len(sql)
        
        while i < n:
            # Check for dollar quote start
            if sql[i] == '$':
                # Check if this starts a dollar quote
                # Dollar quote format: $tag$ or $$$...$$$
                j = i + 1
                
                # Find the end of the opening tag
                # The tag ends at the next $
                while j < n and sql[j] != '$':
                    j += 1
                
                if j >= n:
                    # No closing $, treat as literal
                    current.append(sql[i])
                    i += 1
                    continue
                
                # Extract the tag
                tag = sql[i+1:j]
                num_dollars = len(tag) + 1  # tag length + opening $
                
                # Find matching closing delimiter
                k = j + 1  # Start after the closing $
                found = False
                while k < n:
                    if sql[k] == '$':
                        # Find end of potential closing tag
                        l = k + 1
                        while l < n and sql[l] != '$':
                            l += 1
                        
                        if l >= n:
                            # No closing $
                            k += 1
                            continue
                        
                        close_tag = sql[k+1:l]
                        if len(close_tag) + 1 == num_dollars:
                            # Same number of $ signs
                            if close_tag == tag:
                                # Found matching close! Add from i to l+1 (include closing $)
                                for idx in range(i, l+1):
                                    current.append(sql[idx])
                                i = l + 1
                                found = True
                                break
                        k = l + 1
                    else:
                        k += 1
                
                if not found:
                    # No matching close found, treat $ as literal
                    current.append(sql[i])
                    i += 1
                continue
            
            # Check for semicolon (statement separator)
            if sql[i] == ';':
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
                i += 1
                continue
            
            # Regular character
            current.append(sql[i])
            i += 1
        
        # Add final statement
        final = ''.join(current).strip()
        if final:
            statements.append(final)
        
        return statements
    
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
            
            # Split by semicolons, respecting dollar-quoted strings
            statements = self._split_sql_statements(migration.sql)
            
            for stmt in statements:
                # Filter out comment-only lines
                lines = []
                for line in stmt.split('\n'):
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
        1. Ensures migrations table exists
        2. Discovers all migration files
        3. Checks which migrations have been applied
        4. Runs pending migrations in version order (including 001_initial_schema.sql)
        5. Records successful migrations
        6. Returns detailed result information
        
        For fresh databases, migration 001_initial_schema.sql creates all base tables.
        For existing databases, pending migrations are applied to upgrade the schema.
        
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
        
        # Log current state (required format per spec)
        logger.info("Current schema version: %d", current_version)
        logger.info("Target schema version: %d", target_version)
        
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
        
        # Log applied migrations
        applied_list = list(applied_migrations.keys())
        if applied_list:
            logger.info("Applied migrations: %s", applied_list)
        else:
            logger.info("Applied migrations: (none)")
        
        # Log pending migrations if any (required format per spec)
        if pending:
            logger.info("Pending migrations: %d", len(pending))
            for m in pending:
                logger.info("  Applying: %s", m.name)
        else:
            logger.info("Pending migrations: (none)")
        
        if not pending:
            logger.info("No pending migrations - schema is up to date")
            
            # Verify required columns exist even if no migrations needed
            columns_ok, missing = self.verify_required_columns()
            if not columns_ok:
                return MigrationResult(
                    success=False,
                    current_version=current_version,
                    target_version=target_version,
                    applied_migrations=applied_list,
                    error_message=f"Schema verification failed: missing columns {missing}"
                )
            
            return MigrationResult(
                success=True,
                current_version=current_version,
                target_version=target_version,
                applied_migrations=applied_list,
                duration_ms=(time.time() - start_time) * 1000
            )
        
        # Run pending migrations
        applied_list = list(applied_migrations.keys())
        failed_migration = None
        error_message = None
        
        for migration in pending:
            logger.info("Applying migration %s", migration.name)
            
            success, error = self._execute_migration_sql(migration)
            
            if success:
                self._record_migration(migration.name)
                applied_list.append(migration.name)
                current_version = migration.version_int
                logger.info("Applied migration %s", migration.name)
            else:
                failed_migration = migration.name
                error_message = error
                logger.error("Failed migration %s: %s", migration.name, error)
                break
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info("=" * 60)
        logger.info("SCHEMA MIGRATION COMPLETE")
        logger.info("  Success: %s", failed_migration is None)
        logger.info("  Current version: %s", current_version if failed_migration is None else "unknown")
        logger.info("  Target version: %d", target_version)
        logger.info("  Applied migrations: %s", applied_list)
        logger.info("  Duration: %.1fms", duration_ms)
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
    
    def reset_schema(self) -> bool:
        """
        Reset the database schema by dropping all tables.
        
        This is used for self-healing when database corruption is detected.
        After reset, run_migrations() will recreate the schema from scratch.
        
        FILESYSTEM = SOURCE OF TRUTH
        DATABASE = REGENERATABLE CACHE
        
        Returns:
            True if reset was successful, False on failure
        """
        logger.warning("RESETTING DATABASE SCHEMA - All data will be lost!")
        logger.warning("Database is a regeneratable cache. Filesystem is source of truth.")
        
        try:
            conn = self.backend._get_connection()
            cur = conn.cursor()
            
            # Drop all tables in correct order (respecting foreign keys)
            # Order matters for foreign key constraints
            tables_to_drop = [
                'evidence_lineage',
                'document_embeddings',
                'document_content',
                'document_entities',
                'document_events',
                'document_locations',
                'document_jobs',
                'entities',
                'relationships',
                'events',
                'locations',
                'photo_metadata',
                'plugin_types',
                'documents',
                'collections',
                'schema_migrations',
            ]
            
            for table in tables_to_drop:
                try:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    logger.info("Dropped table: %s", table)
                except Exception as e:
                    logger.debug("Could not drop %s: %s", table, e)
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Clear migrations cache to force re-discovery
            self._migrations_cache = None
            
            logger.info("Schema reset complete. Migrations will reapply on next startup.")
            return True
            
        except Exception as e:
            logger.error("Failed to reset schema: %s", e)
            return False
    
    def full_reset_and_rebuild(self) -> MigrationResult:
        """
        Complete self-healing: reset schema and rebuild from migrations.
        
        This is the ultimate self-healing method that:
        1. Drops all tables
        2. Recreates schema from migrations
        3. Returns detailed result
        
        Use this when database corruption is detected and the database
        should be rebuilt from scratch.
        
        Returns:
            MigrationResult from the rebuild process
        """
        logger.info("=" * 60)
        logger.info("SELF-HEALING: FULL DATABASE RESET AND REBUILD")
        logger.info("=" * 60)
        
        # Step 1: Reset schema
        if not self.reset_schema():
            return MigrationResult(
                success=False,
                current_version=0,
                target_version=self.TARGET_SCHEMA_VERSION,
                applied_migrations=[],
                error_message="Failed to reset schema during self-healing"
            )
        
        logger.info("Schema reset complete. Beginning rebuild...")
        
        # Step 2: Run migrations (this will apply all migrations including 001)
        result = self.run_migrations()
        
        if result.success:
            logger.info("=" * 60)
            logger.info("SELF-HEALING COMPLETE")
            logger.info("  Database rebuilt successfully")
            logger.info("  Schema version: %d", result.current_version)
            logger.info("=" * 60)
        else:
            logger.error("=" * 60)
            logger.error("SELF-HEALING FAILED")
            logger.error("  Error: %s", result.error_message)
            logger.error("=" * 60)
        
        return result


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
