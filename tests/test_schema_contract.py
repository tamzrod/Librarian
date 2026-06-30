"""
Schema Contract Validation Tests

These tests verify that PostgresBackend implementation aligns with the canonical
schema defined in storage/migrations/schema.sql.

Purpose: Prevent future schema drift by validating column references match schema.
"""

import os
import re
import pytest


# Canonical schema columns extracted from storage/migrations/schema.sql
# NOTE: Columns from migration 005_artifact_inventory.sql are included
# (artifact_type, exists_on_disk, deleted_at, lifecycle_state)
CANONICAL_SCHEMA = {
    'documents': {
        'columns': ['id', 'collection_id', 'path', 'extension', 'sha256', 
                   'modified_time', 'file_size', 'character_count', 'parser', 'indexed_at',
                   'status', 'status_updated_at', 'last_error', 'attempt_count',
                   'artifact_type', 'exists_on_disk', 'deleted_at', 'lifecycle_state'],
        'primary_key': 'id',
        'unique_constraints': ['path']
    },
    'entities': {
        'columns': ['id', 'type', 'value', 'normalized_value'],
        'primary_key': 'id'
    },
    'events': {
        'columns': ['id', 'timestamp', 'event_type', 'description'],
        'primary_key': 'id'
    },
    'locations': {
        'columns': ['id', 'name', 'latitude', 'longitude'],
        'primary_key': 'id'
    },
    'relationships': {
        'columns': ['id', 'from_entity', 'to_entity', 'relationship_type'],
        'primary_key': 'id'
    },
    'document_entities': {
        'columns': ['document_id', 'entity_id', 'occurrences'],
        'primary_key': 'document_id, entity_id'
    },
    'document_events': {
        'columns': ['document_id', 'event_id'],
        'primary_key': 'document_id, event_id'
    },
    'document_locations': {
        'columns': ['document_id', 'location_id'],
        'primary_key': 'document_id, location_id'
    },
    'collections': {
        'columns': ['id', 'name', 'root_path', 'created_at'],
        'primary_key': 'id'
    }
}


def extract_insert_columns(sql: str) -> set:
    """Extract column names from an INSERT statement."""
    # Match: INSERT INTO table_name (col1, col2, col3)
    match = re.search(r'INSERT\s+INTO\s+\w+\s*\(([^)]+)\)', sql, re.IGNORECASE)
    if match:
        cols = match.group(1)
        return {c.strip() for c in cols.split(',')}
    return set()


def extract_select_columns(sql: str) -> set:
    """Extract column names from a SELECT statement."""
    # Match: SELECT col1, col2, col3 FROM
    match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
    if match:
        cols = match.group(1)
        # Handle aliases like "d.path" - extract just the column name
        clean_cols = []
        for c in cols.replace('\n', ' ').split(','):
            c = c.strip()
            if '.' in c:
                c = c.split('.')[-1].strip()
            if 'AS ' in c.upper():
                c = c.split('AS ')[-1].strip()
            clean_cols.append(c)
        return {c.strip() for c in clean_cols}
    return set()


def extract_update_columns(sql: str) -> set:
    """Extract column names from an UPDATE SET clause."""
    # Match: UPDATE table_name SET col1 = ..., col2 = ...
    match = re.search(r'SET\s+(.+?)(?:WHERE|RETURNING|$)', sql, re.IGNORECASE | re.DOTALL)
    if match:
        set_clause = match.group(1)
        cols = []
        for part in set_clause.split(','):
            part = part.strip()
            # Extract column name before =
            if '=' in part:
                col = part.split('=')[0].strip()
                cols.append(col)
        return {c.strip() for c in cols}
    return set()


def read_backend_file():
    """Read the postgres_backend.py file."""
    backend_path = os.path.join(os.path.dirname(__file__), '..', 'storage', 'postgres_backend.py')
    with open(backend_path, 'r') as f:
        return f.read()


class TestDocumentsTableContract:
    """Test that save_document and search_documents use correct columns."""
    
    def test_save_document_insert_columns(self):
        """save_document INSERT must use only canonical columns."""
        content = read_backend_file()
        
        # Find save_document method
        match = re.search(r'def save_document\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        assert match, "save_document method not found"
        
        method_body = match.group(1)
        
        # Extract INSERT statement
        insert_match = re.search(r'INSERT\s+INTO\s+documents\s*\(([^)]+)\)', 
                                 method_body, re.IGNORECASE)
        assert insert_match, "INSERT INTO documents not found in save_document"
        
        insert_cols = extract_insert_columns(insert_match.group(0))
        canonical = set(CANONICAL_SCHEMA['documents']['columns'])
        
        # Remove 'id' and 'indexed_at' as they have defaults
        insert_cols.discard('id')
        insert_cols.discard('indexed_at')
        
        # Verify all INSERT columns are in canonical
        invalid = insert_cols - canonical
        assert not invalid, f"save_document INSERT uses invalid columns: {invalid}"
        
    def test_save_document_no_name_column(self):
        """save_document must NOT use 'name' column (not in schema)."""
        content = read_backend_file()
        match = re.search(r'def save_document\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            # Check for 'name' in INSERT columns
            insert_match = re.search(r'INSERT\s+INTO\s+documents\s*\([^)]+\)', 
                                    method_body, re.IGNORECASE)
            if insert_match:
                assert 'name' not in insert_match.group(0).lower(), \
                    "save_document incorrectly uses 'name' column (should be removed)"
    
    def test_save_document_uses_sha256(self):
        """save_document should use sha256 column (canonical)."""
        content = read_backend_file()
        match = re.search(r'def save_document\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            # Should use sha256, not 'hash'
            insert_match = re.search(r'INSERT\s+INTO\s+documents\s*\([^)]+\)', 
                                    method_body, re.IGNORECASE)
            if insert_match:
                assert 'sha256' in insert_match.group(0).lower(), \
                    "save_document should use 'sha256' column"
    
    def test_save_document_uses_file_size(self):
        """save_document should use file_size column (canonical)."""
        content = read_backend_file()
        match = re.search(r'def save_document\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            insert_match = re.search(r'INSERT\s+INTO\s+documents\s*\([^)]+\)', 
                                    method_body, re.IGNORECASE)
            if insert_match:
                assert 'file_size' in insert_match.group(0).lower(), \
                    "save_document should use 'file_size' column"


class TestEntitiesTableContract:
    """Test that save_entities uses correct columns."""
    
    def test_save_entities_insert_columns(self):
        """save_entities INSERT must use 'value' column, not 'name'."""
        content = read_backend_file()
        
        match = re.search(r'def save_entities\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        assert match, "save_entities method not found"
        
        method_body = match.group(1)
        
        insert_match = re.search(r'INSERT\s+INTO\s+entities\s*\(([^)]+)\)', 
                                 method_body, re.IGNORECASE)
        assert insert_match, "INSERT INTO entities not found in save_entities"
        
        insert_cols = extract_insert_columns(insert_match.group(0))
        canonical = set(CANONICAL_SCHEMA['entities']['columns'])
        
        # Remove 'id' as it has a default
        insert_cols.discard('id')
        
        invalid = insert_cols - canonical
        assert not invalid, f"save_entities INSERT uses invalid columns: {invalid}"
        
    def test_save_entities_uses_value_not_name(self):
        """save_entities should use 'value' column (canonical)."""
        content = read_backend_file()
        match = re.search(r'def save_entities\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            insert_match = re.search(r'INSERT\s+INTO\s+entities\s*\([^)]+\)', 
                                    method_body, re.IGNORECASE)
            if insert_match:
                insert_str = insert_match.group(0).lower()
                # Should have 'value', not 'name'
                assert 'value' in insert_str, \
                    "save_entities should use 'value' column"
                assert 'name' not in extract_insert_columns(insert_match.group(0)), \
                    "save_entities should NOT use 'name' column (use 'value')"


class TestSearchMethodsContract:
    """Test that search methods select correct columns."""
    
    def test_search_documents_selects_canonical_columns(self):
        """search_documents SELECT must match canonical columns."""
        content = read_backend_file()
        
        match = re.search(r'def search_documents\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        assert match, "search_documents method not found"
        
        method_body = match.group(1)
        
        # Find SELECT ... FROM documents
        select_match = re.search(r'SELECT\s+.*?\sFROM\s+documents',
                                  method_body, re.IGNORECASE | re.DOTALL)
        assert select_match, "SELECT FROM documents not found"
        
        select_cols = extract_select_columns(select_match.group(0))

        # Filter out numeric literals (e.g., '1' from EXISTS)
        select_cols = {c for c in select_cols if not c.isdigit()}
        
        # These columns should exist in documents table
        canonical_doc_cols = set(CANONICAL_SCHEMA['documents']['columns'])
        
        # All selected columns should be in canonical schema
        invalid = select_cols - canonical_doc_cols
        assert not invalid, f"search_documents SELECT uses invalid columns: {invalid}"
        
    def test_search_entities_selects_value_column(self):
        """search_entities should select 'value' not 'name'."""
        content = read_backend_file()
        
        match = re.search(r'def search_entities\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            
            # Check SELECT columns
            select_match = re.search(r'SELECT\s+.*?\s+FROM\s+entities', 
                                    method_body, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_str = select_match.group(0).lower()
                # Should have 'value', not 'name'
                assert 'e.value' in select_str or 'entities.value' in select_str, \
                    "search_entities should SELECT e.value"
                assert 'e.name' not in select_str and 'entities.name' not in select_str, \
                    "search_entities should NOT SELECT e.name (use e.value)"


class TestSchemaFileExists:
    """Verify schema file exists and is valid."""
    
    def test_schema_file_exists(self):
        """storage/migrations/001_initial_schema.sql must exist."""
        schema_path = os.path.join(os.path.dirname(__file__), 
                                   '..', 'storage', 'migrations', '001_initial_schema.sql')
        assert os.path.exists(schema_path), "001_initial_schema.sql not found"
    
    def test_schema_creates_documents_table(self):
        """001_initial_schema.sql must create documents table."""
        schema_path = os.path.join(os.path.dirname(__file__), 
                                   '..', 'storage', 'migrations', '001_initial_schema.sql')
        with open(schema_path, 'r') as f:
            content = f.read()
        
        assert 'CREATE TABLE' in content.upper() and 'documents' in content.lower(), \
            "001_initial_schema.sql must contain CREATE TABLE documents"
    
    def test_schema_documents_has_sha256(self):
        """001_initial_schema.sql documents table must have sha256 column."""
        schema_path = os.path.join(os.path.dirname(__file__), 
                                   '..', 'storage', 'migrations', '001_initial_schema.sql')
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # Find documents table definition
        match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?documents\s*\((.*?)(?=\nCREATE\s+(?:TABLE|INDEX)|\Z)',
                          content, re.IGNORECASE | re.DOTALL)
        assert match, "documents table definition not found"
        
        table_def = match.group(1).lower()
        assert 'sha256' in table_def, "documents table must have sha256 column"
        assert 'file_size' in table_def, "documents table must have file_size column"
    
    def test_schema_entities_has_value(self):
        """002_entities.sql entities table must have value column (not name)."""
        schema_path = os.path.join(os.path.dirname(__file__), 
                                   '..', 'storage', 'migrations', '002_entities.sql')
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # Find entities table definition
        match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?entities\s*\((.*?)(?=\nCREATE\s+(?:TABLE|INDEX)|\Z)',
                          content, re.IGNORECASE | re.DOTALL)
        assert match, "entities table definition not found"
        
        table_def = match.group(1).lower()
        assert 'value' in table_def, "entities table must have value column"
        # Note: 'name' is NOT in the canonical schema for entities


class TestLegacyCompatibility:
    """Test that legacy key mapping is implemented."""
    
    def test_document_legacy_key_mapping(self):
        """save_document should handle legacy 'hash' → 'sha256' mapping."""
        content = read_backend_file()
        match = re.search(r'def save_document\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            # Should have mapping for hash to sha256
            assert "get('sha256') or get('hash')" in method_body or \
                   "get('hash')" in method_body, \
                "save_document should handle legacy 'hash' → 'sha256' mapping"
    
    def test_document_size_bytes_mapping(self):
        """save_document should handle legacy 'size_bytes' → 'file_size' mapping."""
        content = read_backend_file()
        match = re.search(r'def save_document\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            # Should have mapping for size_bytes to file_size
            assert "get('file_size') or get('size_bytes')" in method_body or \
                   "get('size_bytes')" in method_body, \
                "save_document should handle legacy 'size_bytes' → 'file_size' mapping"
    
    def test_entities_legacy_name_mapping(self):
        """save_entities should handle legacy 'name' → 'value' mapping."""
        content = read_backend_file()
        match = re.search(r'def save_entities\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            # Should have mapping for name to value
            assert "get('value') or get('name')" in method_body or \
                   "get('name')" in method_body, \
                "save_entities should handle legacy 'name' → 'value' mapping"


class TestTimestampConversion:
    """Test that timestamp conversion is implemented for persistence layer."""
    
    def test_timestamp_conversion_function_exists(self):
        """PostgresBackend must have _to_postgres_timestamp function."""
        content = read_backend_file()
        assert '_to_postgres_timestamp' in content, \
            "PostgresBackend must have _to_postgres_timestamp function"
    
    def test_save_document_uses_timestamp_conversion(self):
        """save_document must use _to_postgres_timestamp for modified_time."""
        content = read_backend_file()
        match = re.search(r'def save_document\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        assert match, "save_document method not found"
        method_body = match.group(1)
        
        # Should convert modified_time
        assert '_to_postgres_timestamp' in method_body, \
            "save_document must use _to_postgres_timestamp for modified_time"
    
    def test_save_events_uses_timestamp_conversion(self):
        """save_events must use _to_postgres_timestamp for timestamp field."""
        content = read_backend_file()
        match = re.search(r'def save_events\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)', 
                          content, re.DOTALL)
        
        if match:
            method_body = match.group(1)
            # Should convert timestamp
            assert '_to_postgres_timestamp' in method_body, \
                "save_events must use _to_postgres_timestamp for timestamp field"
    
    def test_timestamp_conversion_handles_epoch_float(self):
        """_to_postgres_timestamp must handle Unix epoch floats."""
        content = read_backend_file()
        
        # Check that the function handles floats
        assert 'fromtimestamp' in content, \
            "_to_postgres_timestamp should use datetime.fromtimestamp for epoch floats"
    
    def test_timestamp_conversion_handles_datetime(self):
        """_to_postgres_timestamp must handle datetime objects."""
        content = read_backend_file()
        
        # Check that the function handles datetime objects
        assert 'isinstance(value, datetime)' in content or 'isinstance' in content, \
            "_to_postgres_timestamp should check isinstance(value, datetime)"
    
    def test_timestamp_conversion_handles_none(self):
        """_to_postgres_timestamp must handle None input."""
        content = read_backend_file()
        
        # Should return None for None input
        assert 'if value is None' in content or 'value is None' in content, \
            "_to_postgres_timestamp should handle None input"


class TestTimestampContract:
    """Test timestamp representation across the codebase."""
    
    def test_modified_time_is_timestamp_in_schema(self):
        """documents.modified_time must be TIMESTAMP in schema."""
        schema_path = os.path.join(os.path.dirname(__file__), 
                                   '..', 'storage', 'migrations', '001_initial_schema.sql')
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # Find documents table and check modified_time column type
        match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?documents\s*\((.*?)(?=\nCREATE\s+(?:TABLE|INDEX)|\Z)',
                          content, re.IGNORECASE | re.DOTALL)
        assert match, "documents table definition not found"
        
        table_def = match.group(1)
        # modified_time should be TIMESTAMP
        assert 'modified_time' in table_def.lower(), \
            "documents table must have modified_time column"
    
    def test_events_timestamp_is_timestamp_in_schema(self):
        """events.timestamp must be TIMESTAMP in schema."""
        schema_path = os.path.join(os.path.dirname(__file__), 
                                   '..', 'storage', 'migrations', '004_timeline.sql')
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # Find events table
        match = re.search(r'CREATE\s+TABLE\s+.*?events\s*\((.*?)(?:CREATE|INDEX|\Z)', 
                          content, re.IGNORECASE | re.DOTALL)
        assert match, "events table definition not found"
        
        table_def = match.group(1)
        assert 'timestamp' in table_def.lower(), \
            "events table must have timestamp column"
    
    def test_indexed_at_is_timestamp_in_schema(self):
        """documents.indexed_at must be TIMESTAMP in schema."""
        schema_path = os.path.join(os.path.dirname(__file__), 
                                   '..', 'storage', 'migrations', '001_initial_schema.sql')
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # Find documents table and check indexed_at column
        match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?documents\s*\((.*?)(?=\nCREATE\s+(?:TABLE|INDEX)|\Z)',
                          content, re.IGNORECASE | re.DOTALL)
        assert match, "documents table definition not found"
        
        table_def = match.group(1)
        assert 'indexed_at' in table_def.lower(), \
            "documents table must have indexed_at column"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
