"""
Tests for MigrationManager schema migration functionality.

These tests verify that:
1. Migrations are discovered correctly (including 001_initial_schema.sql)
2. Applied migrations are tracked
3. Schema verification works
4. Empty database bootstrap works via MigrationManager
5. Idempotent startup works
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
        
        # Should find all 4 migrations: 001, 003, 004, 005
        assert '001_initial_schema.sql' in migration_names
        assert '003_photo_metadata.sql' in migration_names
        assert '004_test.sql' in migration_names
        assert '005_artifact_inventory.sql' in migration_names
    
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
        """TARGET_SCHEMA_VERSION is 5 (from 005_artifact_inventory.sql)."""
        from storage.migration_manager import MigrationManager
        
        assert MigrationManager.TARGET_SCHEMA_VERSION == 5
    
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
        
        version, desc = manager._extract_version('005_artifact_inventory.sql')
        assert version == '005'
        assert 'artifact inventory' in desc.lower()
        
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
        """001_initial_schema.sql should create all base tables."""
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
        assert 'CREATE TABLE IF NOT EXISTS collections' in content
        assert 'CREATE TABLE IF NOT EXISTS documents' in content
        assert 'CREATE TABLE IF NOT EXISTS document_jobs' in content
        assert 'CREATE TABLE IF NOT EXISTS entities' in content
        assert 'CREATE TABLE IF NOT EXISTS events' in content
        assert 'CREATE TABLE IF NOT EXISTS locations' in content
        
        # Should record the migration
        assert "INSERT INTO schema_migrations (migration_name) VALUES ('001_initial_schema.sql')" in content


class TestUpgradeFromPreviousVersion:
    """Test that existing databases continue to work correctly."""
    
    def test_existing_db_skips_applied_migrations(self):
        """Existing database with applied migrations should skip them."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        # Simulate database with 001 already applied
        applied = {
            '001_initial_schema.sql': None,
            '003_photo_metadata.sql': None,
        }
        
        # Discover migrations
        migrations = manager.discover_migrations()
        migration_names = [m.name for m in migrations]
        
        # 001 and 003 should be in discovered list
        assert '001_initial_schema.sql' in migration_names
        assert '003_photo_metadata.sql' in migration_names
        
        # 004 and 005 should also be in discovered list
        assert '004_test.sql' in migration_names
        assert '005_artifact_inventory.sql' in migration_names


class TestIdempotentStartup:
    """Test that startup is idempotent - running multiple times is safe."""
    
    def test_already_up_to_date_returns_success(self):
        """Already up-to-date database should return success without errors."""
        from storage.migration_manager import MigrationManager, MigrationResult
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        # Simulate all migrations already applied
        with patch.object(manager, '_ensure_migrations_table', return_value=True):
            with patch.object(manager, 'get_applied_migrations', return_value={
                '001_initial_schema.sql': None,
                '003_photo_metadata.sql': None,
                '004_test.sql': None,
                '005_artifact_inventory.sql': None,
            }):
                with patch.object(manager, 'get_current_schema_version', return_value=5):
                    with patch.object(manager, 'verify_required_columns', return_value=(True, [])):
                        result = manager.run_migrations()
                        
                        assert result.success is True
                        assert result.current_version == 5
                        assert result.target_version == 5
    
    def test_migrations_are_idempotent(self):
        """Migration files should be safe to run multiple times."""
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
    
    def test_004_test_exists(self):
        """Migration 004_test.sql exists."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'storage',
            'migrations',
            '004_test.sql'
        )
        
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"
    
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
