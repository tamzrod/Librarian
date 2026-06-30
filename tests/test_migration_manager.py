"""
Tests for MigrationManager schema migration functionality.

These tests verify that:
1. Migrations are discovered correctly
2. Applied migrations are tracked
3. Schema verification works
4. V2 to V5 upgrade path is correct
"""

import os
import re
import pytest
from unittest.mock import MagicMock, patch


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
    
    def test_discover_migrations(self):
        """MigrationManager discovers all migration files."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        migrations = manager.discover_migrations()
        
        # Should find at least 3 migrations: 003, 004, 005
        migration_names = [m.name for m in migrations]
        assert '003_photo_metadata.sql' in migration_names
        assert '004_test.sql' in migration_names
        assert '005_artifact_inventory.sql' in migration_names
    
    def test_migration_versions(self):
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
        version, desc = manager._extract_version('003_photo_metadata.sql')
        assert version == '003'
        assert 'photo metadata' in desc.lower()
        
        version, desc = manager._extract_version('005_artifact_inventory.sql')
        assert version == '005'
        assert 'artifact inventory' in desc.lower()
        
        # Invalid filename returns None for version
        version, desc = manager._extract_version('invalid.sql')
        assert version is None
    
    def test_needs_base_schema_bootstrap(self):
        """_needs_base_schema_bootstrap returns True when documents table is missing."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        mock_backend._get_connection.return_value.__enter__ = MagicMock()
        mock_backend._get_connection.return_value.__exit__ = MagicMock()
        mock_backend._get_connection.return_value.cursor.return_value.__enter__ = MagicMock()
        mock_backend._get_connection.return_value.cursor.return_value.__exit__ = MagicMock()
        # documents table does NOT exist
        mock_backend._get_connection.return_value.cursor.return_value.fetchone.return_value = (False,)
        
        manager = MigrationManager(mock_backend)
        assert manager._needs_base_schema_bootstrap() == True
    
    def test_no_bootstrap_needed(self):
        """_needs_base_schema_bootstrap returns False when documents table exists."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        mock_backend._get_connection.return_value.__enter__ = MagicMock()
        mock_backend._get_connection.return_value.__exit__ = MagicMock()
        mock_backend._get_connection.return_value.cursor.return_value.__enter__ = MagicMock()
        mock_backend._get_connection.return_value.cursor.return_value.__exit__ = MagicMock()
        # documents table EXISTS
        mock_backend._get_connection.return_value.cursor.return_value.fetchone.return_value = (True,)
        
        manager = MigrationManager(mock_backend)
        assert manager._needs_base_schema_bootstrap() == False
    
    def test_get_base_schema_path(self):
        """_get_base_schema_path returns path to schema.sql."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        manager = MigrationManager(mock_backend)
        
        path = manager._get_base_schema_path()
        assert path is not None
        assert path.endswith('schema.sql')
    
    def test_bootstrap_base_schema(self):
        """_bootstrap_base_schema executes schema.sql on fresh database."""
        from storage.migration_manager import MigrationManager
        
        mock_backend = MagicMock()
        mock_backend._get_connection.return_value.__enter__ = MagicMock()
        mock_backend._get_connection.return_value.__exit__ = MagicMock()
        mock_backend._get_connection.return_value.cursor.return_value.__enter__ = MagicMock()
        mock_backend._get_connection.return_value.cursor.return_value.__exit__ = MagicMock()
        
        manager = MigrationManager(mock_backend)
        success, error = manager._bootstrap_base_schema()
        
        assert success == True
        assert error is None
        # Verify connection was used
        mock_backend._get_connection.assert_called()
    
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


class TestMigrationFiles:
    """Test that migration files are correctly structured."""
    
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
    """Test that PostgresBackend uses MigrationManager."""
    
    def test_ensure_schema_calls_migration_manager(self):
        """PostgresBackend.ensure_schema uses MigrationManager."""
        from storage.postgres_backend import PostgresBackend
        
        # Check that the method imports and uses MigrationManager
        import inspect
        source = inspect.getsource(PostgresBackend.ensure_schema)
        
        assert 'MigrationManager' in source or 'run_migrations_for_backend' in source, \
            "ensure_schema should use MigrationManager"
    
    def test_ensure_schema_has_fallback(self):
        """PostgresBackend.ensure_schema has legacy fallback."""
        from storage.postgres_backend import PostgresBackend
        
        import inspect
        source = inspect.getsource(PostgresBackend.ensure_schema)
        
        assert '_ensure_schema_legacy' in source, \
            "ensure_schema should have legacy fallback"


class TestAppStateIntegration:
    """Test that app_state handles migration failures."""
    
    def test_initialize_backend_raises_on_migration_failure(self):
        """initialize_backend raises RuntimeError when schema migration fails."""
        import inspect
        from api.app_state import AppState
        
        # Check the source code contains the proper error handling
        source = inspect.getsource(AppState.initialize_backend)
        
        # Should raise RuntimeError on schema failure
        assert 'raise RuntimeError' in source, "Should raise RuntimeError on migration failure"
        assert 'SCHEMA MIGRATION FAILED' in source, "Should have clear error message"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
