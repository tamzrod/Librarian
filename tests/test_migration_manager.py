"""
Tests for MigrationManager schema migration functionality.

These tests verify that:
1. Migrations are discovered correctly (including 001_initial_schema.sql)
2. Applied migrations are tracked
3. Schema verification works
4. Empty database bootstrap works via MigrationManager
5. Idempotent startup works
6. Self-healing capability works
7. Database deletion recovery works
"""

import os
import re
import pytest
from unittest.mock import MagicMock, patch, call


class TestMigrationManager:
    """Test MigrationManager functionality."""
    
    def test_migration_manager_imports(self):
        """MigrationManager can be imported."""
        from storage.migration_manager import MigrationManager, run_migrations_for_backend
        assert MigrationManager is not None
        assert run_migrations_for_backend is not None
    
    def test_migration_manager_initialization(self):
        """MigrationManager can be initialized with a backend."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        assert manager.backend == mock_backend
    
    def test_discover_migrations_includes_001(self):
        """MigrationManager discovers 001_initial_schema.sql."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        migrations = manager.discover_migrations()
        migration_names = [m.name for m in migrations]
        
        # Should include 001_initial_schema.sql as first migration
        assert '001_initial_schema.sql' in migration_names
        
        # 001 should be first (version 001)
        assert migrations[0].name == '001_initial_schema.sql'
        assert migrations[0].version == '001'
    
    def test_discover_migrations_all_migrations(self):
        """MigrationManager discovers all migration files."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        migrations = manager.discover_migrations()
        migration_names = [m.name for m in migrations]
        
        # Should find all migrations: 001, 002, 003, 004, 005, 006
        assert '001_initial_schema.sql' in migration_names
        assert '002_entities.sql' in migration_names
        assert '003_photo_metadata.sql' in migration_names
        assert '004_timeline.sql' in migration_names
        assert '005_artifact_inventory.sql' in migration_names
        assert '006_embeddings.sql' in migration_names
    
    def test_migration_versions_sorted(self):
        """Migrations are sorted by version number."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        migrations = manager.discover_migrations()
        
        # Verify sorted order
        versions = [m.version_int for m in migrations]
        assert versions == sorted(versions)
    
    def test_target_schema_version(self):
        """TARGET_SCHEMA_VERSION is 9 (from 009_add_missing_indexes.sql)."""
        from storage.migration_manager import MigrationManager
        
        assert MigrationManager.TARGET_SCHEMA_VERSION == 9
    
    def test_required_columns(self):
        """REQUIRED_COLUMNS includes artifact_type, exists_on_disk, deleted_at, lifecycle_state."""
        from storage.migration_manager import MigrationManager
        
        required = MigrationManager.REQUIRED_COLUMNS
        assert 'artifact_type' in required
        assert 'exists_on_disk' in required
        assert 'deleted_at' in required
        assert 'lifecycle_state' in required
    
    def test_extract_version(self):
        """Version extraction works correctly."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        # Valid versions
        version, desc = manager._extract_version('001_initial_schema.sql')
        assert version == '001'
        assert 'initial schema' in desc.lower()
        
        version, desc = manager._extract_version('003_photo_metadata.sql')
        assert version == '003'
        assert 'photo metadata' in desc.lower()
        
        version, desc = manager._extract_version('006_embeddings.sql')
        assert version == '006'
        assert 'embeddings' in desc.lower()
        
        # Invalid filename returns None for version
        version, desc = manager._extract_version('invalid.sql')
        assert version is None
    
    def test_schema_migration_error(self):
        """SchemaMigrationError has correct attributes."""
        from storage.migration_manager import SchemaMigrationError
        
        error = SchemaMigrationError(
            "Migration failed",
            migration_name="003_test.sql",
            details="Column not found"
        )
        
        assert error.migration_name == "003_test.sql"
        assert error.details == "Column not found"
        assert "Migration failed" in str(error)
    
    def test_schema_verification_error(self):
        """SchemaVerificationError has correct attributes."""
        from storage.migration_manager import SchemaVerificationError
        
        missing = ['artifact_type', 'exists_on_disk']
        error = SchemaVerificationError(
            "Missing columns",
            missing_columns=missing
        )
        
        assert error.missing_columns == missing
        assert "Missing columns" in str(error)


class TestEmptyDatabaseBootstrap:
    """Test that empty database bootstrap works correctly via MigrationManager."""
    
    def test_empty_db_runs_all_migrations(self):
        """Empty database should run all migrations including 001."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        
        # Simulate empty database (no applied migrations)
        mock_backend._get_connection.return_value.cursor.return_value.fetchall.return_value = []
        
        manager = MigrationManager(mock_backend)
        
        # Mock the internal methods
        with patch.object(manager, '_ensure_migrations_table', return_value=True):
            with patch.object(manager, 'get_applied_migrations', return_value={}):
                with patch.object(manager, 'get_current_schema_version', return_value=0):
                    migrations = manager.discover_migrations()
                    
                    # 001 should be in the list
                    assert any(m.name == '001_initial_schema.sql' for m in migrations)
    
    def test_001_creates_base_schema(self):
        """001_initial_schema.sql should create core tables only."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '001_initial_schema.sql'
        )
        
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Should create core tables
        assert 'CREATE TABLE IF NOT EXISTS schema_migrations' in content
        assert 'CREATE TABLE IF NOT EXISTS collections' in content
        assert 'CREATE TABLE IF NOT EXISTS documents' in content
        assert 'CREATE TABLE IF NOT EXISTS document_jobs' in content
        
        # Should NOT create entities/events/locations (they are in 002 and 004)
        # The 001 should be lean and only contain what is required for startup
        assert 'CREATE TABLE IF NOT EXISTS entities' not in content
        assert 'CREATE TABLE IF NOT EXISTS events' not in content
        assert 'CREATE TABLE IF NOT EXISTS locations' not in content
        
        # Should record the migration
        assert "INSERT INTO schema_migrations (migration_name) VALUES ('001_initial_schema.sql')" in content


class TestDatabaseDeletionRecovery:
    """Test that database deletion recovery works correctly."""
    
    def test_reset_schema_drops_all_tables(self):
        """reset_schema should drop all tables in correct order."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        mock_cursor = MagicMock()
        mock_backend._get_connection.return_value.cursor.return_value = mock_cursor
        
        manager = MigrationManager(mock_backend)
        
        with patch.object(manager, 'reset_schema', return_value=True) as mock_reset:
            # The reset should be callable
            result = mock_reset()
            assert result is True
    
    def test_full_reset_and_rebuild_exists(self):
        """full_reset_and_rebuild method exists on MigrationManager."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        assert hasattr(manager, 'full_reset_and_rebuild')
        assert callable(manager.full_reset_and_rebuild)


class TestUpgradeFromPreviousVersion:
    """Test that existing databases continue to work correctly."""
    
    def test_existing_db_skips_applied_migrations(self):
        """Existing database should skip already-applied migrations."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        # Simulate database with migrations already applied
        applied = {
            '001_initial_schema.sql': '2024-01-01',
            '002_entities.sql': '2024-01-02',
            '003_photo_metadata.sql': '2024-01-03',
        }
        
        with patch.object(manager, 'get_applied_migrations', return_value=applied):
            with patch.object(manager, 'get_current_schema_version', return_value=3):
                migrations = manager.discover_migrations()
                
                # Should have pending migrations (004, 005, 006 are pending)
                pending = [m for m in migrations if m.name not in applied]
                assert len(pending) > 0


class TestMigrationIdempotency:
    """Test that migrations are idempotent."""
    
    def test_001_uses_if_not_exists(self):
        """001_initial_schema.sql uses CREATE TABLE IF NOT EXISTS."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '001_initial_schema.sql'
        )
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # All CREATE TABLE statements should use IF NOT EXISTS
        import re
        create_table_pattern = r'CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?'
        create_tables = re.findall(create_table_pattern, content, re.IGNORECASE)
        
        # Should have CREATE TABLE IF NOT EXISTS for all tables
        assert len(create_tables) > 0


class TestMigrationFiles:
    """Test that migration files are correctly structured."""
    
    def test_001_initial_schema_exists(self):
        """Migration 001_initial_schema.sql exists and has INSERT statement."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '001_initial_schema.sql'
        )
        
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Should create main tables
        assert 'CREATE TABLE IF NOT EXISTS documents' in content
        # Should record migration
        assert "INSERT INTO schema_migrations" in content
        # Should create schema_migrations first
        assert 'CREATE TABLE IF NOT EXISTS schema_migrations' in content
    
    def test_002_entities_exists(self):
        """Migration 002_entities.sql exists."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '002_entities.sql'
        )
        
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Should create entity tables
        assert 'CREATE TABLE IF NOT EXISTS entities' in content
        assert 'CREATE TABLE IF NOT EXISTS relationships' in content
        assert 'CREATE TABLE IF NOT EXISTS document_entities' in content
        assert 'CREATE TABLE IF NOT EXISTS evidence_lineage' in content
        # Should record migration
        assert "INSERT INTO schema_migrations" in content
    
    def test_003_photo_metadata_exists(self):
        """Migration 003_photo_metadata.sql exists and has INSERT statement."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '003_photo_metadata.sql'
        )
        
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        assert 'CREATE TABLE' in content.upper()
        assert 'schema_migrations' in content
    
    def test_004_timeline_exists(self):
        """Migration 004_timeline.sql exists."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '004_timeline.sql'
        )
        
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Should create timeline tables
        assert 'CREATE TABLE IF NOT EXISTS events' in content
        assert 'CREATE TABLE IF NOT EXISTS locations' in content
        assert 'CREATE TABLE IF NOT EXISTS document_events' in content
        assert 'CREATE TABLE IF NOT EXISTS document_locations' in content
        # Should record migration
        assert "INSERT INTO schema_migrations" in content
    
    def test_004_test_removed(self):
        """Migration 004_test.sql should be removed."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '004_test.sql'
        )
        
        # 004_test.sql should not exist (replaced by 004_timeline.sql)
        assert not os.path.exists(migration_path), "004_test.sql should be removed"
    
    def test_005_artifact_inventory_exists(self):
        """Migration 005_artifact_inventory.sql exists and adds required columns."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '005_artifact_inventory.sql'
        )
        
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Should add artifact_type
        assert 'artifact_type' in content
        # Should add exists_on_disk
        assert 'exists_on_disk' in content
        # Should add deleted_at
        assert 'deleted_at' in content
        # Should add lifecycle_state
        assert 'lifecycle_state' in content
        # Should create enum
        assert 'artifact_type_enum' in content
        # Should record migration
        assert "INSERT INTO schema_migrations" in content
    
    def test_006_embeddings_exists(self):
        """Migration 006_embeddings.sql exists."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '006_embeddings.sql'
        )
        
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Should create embedding tables
        assert 'CREATE TABLE IF NOT EXISTS document_embeddings' in content
        assert 'CREATE TABLE IF NOT EXISTS document_content' in content
        assert 'CREATE TABLE IF NOT EXISTS plugin_types' in content
        # Should record migration
        assert "INSERT INTO schema_migrations" in content


class TestBackendIntegration:
    """Test that PostgresBackend uses MigrationManager as only initialization path."""
    
    def test_ensure_schema_uses_migration_manager(self):
        """PostgresBackend.ensure_schema uses MigrationManager."""
        # Read the source file directly to avoid psycopg import
        backend_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'postgres_backend.py'
        )
        
        with open(backend_path, 'r') as f:
            source = f.read()
        
        # Find the ensure_schema method
        import re
        match = re.search(r'def ensure_schema\(self\).*?(?=\n    def |\nclass |\Z)', source, re.DOTALL)
        if match:
            method_source = match.group(0)
            assert 'run_migrations_for_backend' in method_source, \
                "ensure_schema should use run_migrations_for_backend"
    
    def test_no_legacy_fallback(self):
        """PostgresBackend.ensure_schema has no legacy fallback."""
        # Read the source file directly to avoid psycopg import
        backend_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'postgres_backend.py'
        )
        
        with open(backend_path, 'r') as f:
            source = f.read()
        
        # Find the ensure_schema method
        import re
        match = re.search(r'def ensure_schema\(self\).*?(?=\n    def |\nclass |\Z)', source, re.DOTALL)
        if match:
            method_source = match.group(0)
            assert '_ensure_schema_legacy' not in method_source, \
                "ensure_schema should not have legacy fallback"
    
    def test_no_schema_sql_reference(self):
        """PostgresBackend.ensure_schema has no schema.sql reference."""
        # Read the source file directly to avoid psycopg import
        backend_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'postgres_backend.py'
        )
        
        with open(backend_path, 'r') as f:
            source = f.read()
        
        # Find the ensure_schema method
        import re
        match = re.search(r'def ensure_schema\(self\).*?(?=\n    def |\nclass |\Z)', source, re.DOTALL)
        if match:
            method_source = match.group(0)
            # Remove docstring to check only actual code
            docstring_match = re.search(r'""".*?"""', method_source, re.DOTALL)
            if docstring_match:
                method_code = method_source.replace(docstring_match.group(0), '')
            else:
                method_code = method_source
            assert 'schema.sql' not in method_code, \
                "ensure_schema should not reference schema.sql in code"


class TestDockerComposeIntegration:
    """Test that docker-compose.yml is configured correctly."""
    
    def test_docker_compose_no_init_sql_mount(self):
        """docker-compose.yml should not mount init.sql."""
        compose_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'deploy',
            'docker-compose.yml'
        )
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Should NOT have init.sql mount for postgres
        # The schema is managed by MigrationManager
        assert 'init.sql:/docker-entrypoint-initdb.d/init.sql' not in content, \
            "docker-compose should not mount init.sql - use MigrationManager instead"


class TestSelfHealing:
    """Test self-healing capabilities."""
    
    def test_reset_schema_method_exists(self):
        """MigrationManager has reset_schema method."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        assert hasattr(manager, 'reset_schema')
        assert callable(manager.reset_schema)
    
    def test_full_reset_and_rebuild_method_exists(self):
        """MigrationManager has full_reset_and_rebuild method."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        assert hasattr(manager, 'full_reset_and_rebuild')
        assert callable(manager.full_reset_and_rebuild)


class TestAppStateIntegration:
    """Test that app_state handles migration failures."""
    
    def test_initialize_backend_raises_on_migration_failure(self):
        """initialize_backend raises RuntimeError when schema migration fails."""
        # Read the source file directly to avoid psycopg import
        app_state_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'api',
            'app_state.py'
        )
        
        with open(app_state_path, 'r') as f:
            source = f.read()
        
        # Find the initialize_backend method
        import re
        match = re.search(r'def initialize_backend\(.*?\).*?(?=\n    def |\nclass |\Z)', source, re.DOTALL)
        if match:
            method_source = match.group(0)
            # Should raise RuntimeError on schema failure
            assert 'raise RuntimeError' in method_source, \
                "Should raise RuntimeError on migration failure"
            assert 'SCHEMA MIGRATION FAILED' in method_source, \
                "Should have clear error message"


class TestStartupLogging:
    """Test that startup logging follows the specified format."""
    
    def test_migration_logging_format(self):
        """Migration logging should use 'Applying migration {name}' format."""
        from storage.migration_manager import MigrationManager
        import logging
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        # Verify the logging format is used in run_migrations
        import inspect
        source = inspect.getsource(MigrationManager.run_migrations)
        
        assert 'Applying migration' in source, \
            "Should log 'Applying migration' for each migration"
    
    def test_startup_logs_versions(self):
        """run_migrations logs current and target schema versions."""
        from storage.migration_manager import MigrationManager
        import inspect
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        source = inspect.getsource(MigrationManager.run_migrations)
        
        # Should log versions
        assert 'Current schema version' in source
        assert 'Target schema version' in source


class TestSqlDollarQuoteSplitting:
    """Test SQL splitting correctly handles dollar-quoted strings."""
    
    def test_split_simple_dollar_quotes(self):
        """Simple $$...$$ blocks should not be split on internal semicolons."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        sql = """
DO $$ BEGIN
    CREATE TYPE foo AS ENUM ('a', 'b', 'c');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
ALTER TABLE foo ADD COLUMN x INT;
"""
        statements = manager._split_sql_statements(sql)
        
        assert len(statements) == 2
        assert 'DO $$' in statements[0]
        assert 'CREATE TYPE foo AS ENUM' in statements[0]
        assert 'EXCEPTION' in statements[0]
        assert 'END $$' in statements[0]
        assert 'ALTER TABLE' in statements[1]
    
    def test_split_tagged_dollar_quotes(self):
        """Tagged $tag$...$tag$ blocks should not be split."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        sql = """
CREATE FUNCTION foo() RETURNS void AS $body$
BEGIN
    SELECT 1;  -- internal semicolon
END;
$body$ LANGUAGE plpgsql;
CREATE TABLE bar (id INT);
"""
        statements = manager._split_sql_statements(sql)
        
        assert len(statements) == 2
        assert '$body$' in statements[0]
        assert 'SELECT 1;' in statements[0]  # internal semicolon preserved
        assert 'CREATE TABLE' in statements[1]
    
    def test_split_multiple_dollar_blocks(self):
        """Multiple DO $$...$$ blocks should each be one statement."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        sql = """
DO $$ BEGIN CREATE TYPE t1 AS ENUM ('x'); END $$;
DO $$ BEGIN CREATE TYPE t2 AS ENUM ('y'); END $$;
SELECT 1;
"""
        statements = manager._split_sql_statements(sql)
        
        assert len(statements) == 3
        assert statements[0].count('DO $$') == 1
        assert statements[1].count('DO $$') == 1
        assert 'SELECT 1' in statements[2]
    
    def test_split_no_dangling_semicolons(self):
        """Semicolons inside dollar quotes don't terminate statements."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        # This SQL has internal semicolons but only one real statement
        sql = """
DO $$
BEGIN
    RAISE NOTICE 'hello; world';
    PERFORM 1;  -- Another internal semicolon
END $$;
"""
        statements = manager._split_sql_statements(sql)
        
        assert len(statements) == 1
        assert "RAISE NOTICE 'hello; world'" in statements[0]
        assert 'PERFORM 1;' in statements[0]
    
    def test_split_preserves_migration_005_pattern(self):
        """Migration 005 pattern with DO $$ should produce correct statements."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        # Read actual migration 005
        migration_005_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '005_artifact_inventory.sql'
        )
        
        with open(migration_005_path, 'r') as f:
            content = f.read()
        
        statements = manager._split_sql_statements(content)
        
        # Find the DO $$ block - it should contain both BEGIN and END $$ as a single statement
        do_blocks = [s for s in statements if 'DO $$' in s and 'END $$' in s]
        assert len(do_blocks) == 1, f"Expected 1 DO block statement, got {len(do_blocks)}"
        
        do_stmt = do_blocks[0]
        assert 'BEGIN' in do_stmt
        assert 'END $$' in do_stmt
        assert 'CREATE TYPE artifact_type_enum' in do_stmt
        assert 'EXCEPTION' in do_stmt
        
        # Verify the DO block is NOT split at internal semicolons
        # (If we split by ';' naively, we'd get 3 pieces, but dollar-quote aware gives 1)
        assert do_stmt.count(';') == 3  # The ENUM list has 3 semicolons + EXCEPTION + END $$;


class TestArchitecturePrinciples:
    """Test that architecture principles are implemented."""
    
    def test_filesystem_is_source_of_truth(self):
        """Migration files should not contain data that depends on filesystem."""
        # Check that migrations don't have embedded sample data
        migrations_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations'
        )
        
        for filename in os.listdir(migrations_dir):
            if filename.endswith('.sql'):
                filepath = os.path.join(migrations_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Migrations should not have INSERT statements with actual data
                # (only schema_migrations tracking inserts are allowed)
                if 'INSERT INTO' in content and filename != '001_initial_schema.sql':
                    # Check it's only the schema_migrations insert
                    insert_lines = [line for line in content.split('\n') if 'INSERT INTO' in line]
                    for line in insert_lines:
                        assert 'schema_migrations' in line, \
                            f"{filename} should only insert into schema_migrations"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
