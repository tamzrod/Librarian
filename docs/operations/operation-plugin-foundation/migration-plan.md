# Migration Plan

**Purpose:** Document the database and code changes for Operation Plugin Foundation

---

## Migration Overview

Operation Plugin Foundation requires:

1. Database migration (new columns, constraints)
2. Plugin registry updates
3. Worker updates
4. Backend updates

## Database Migration

### Migration File: 011_plugin_foundation.sql

```sql
-- Migration: 011_plugin_foundation.sql
-- Operation Plugin Foundation
-- Purpose: Add plugin identity and provenance columns to observation tables
-- Safety: Safe on live database (additive changes)
-- Rollback: Available

-- =============================================================================
-- STEP 1: Add identity columns to photo_metadata
-- =============================================================================

-- Add provenance columns (nullable first)
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100);
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100);
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50);
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS artifact_hash VARCHAR(64);

-- Set DEFAULT values for existing rows
UPDATE photo_metadata
SET 
    plugin_name = 'metadata.exif.pillow',
    engine_name = 'pillow-exif',
    plugin_version = '1.0.0',
    processed_at = COALESCE(extracted_at, CURRENT_TIMESTAMP)
WHERE plugin_name IS NULL;

-- Add NOT NULL constraints after backfill
ALTER TABLE photo_metadata
    ALTER COLUMN plugin_name SET NOT NULL,
    ALTER COLUMN engine_name SET NOT NULL,
    ALTER COLUMN plugin_version SET NOT NULL,
    ALTER COLUMN processed_at SET NOT NULL;

ALTER TABLE photo_metadata
    ALTER COLUMN plugin_name SET DEFAULT 'metadata.exif.pillow',
    ALTER COLUMN engine_name SET DEFAULT 'pillow-exif',
    ALTER COLUMN plugin_version SET DEFAULT '1.0.0',
    ALTER COLUMN processed_at SET DEFAULT CURRENT_TIMESTAMP;

-- =============================================================================
-- STEP 2: Update UNIQUE constraint for multi-engine support
-- =============================================================================

-- Remove old UNIQUE constraint (if exists)
ALTER TABLE photo_metadata 
    DROP CONSTRAINT IF EXISTS photo_metadata_document_id_key;

-- Add new multi-engine UNIQUE constraint
-- This allows multiple engines per document (future-proofing)
ALTER TABLE photo_metadata 
    ADD CONSTRAINT uq_photo_metadata_identity
    UNIQUE (document_id, plugin_name, engine_name);

-- =============================================================================
-- STEP 3: Add indexes for provenance queries
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_photo_metadata_plugin
    ON photo_metadata(plugin_name);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_engine
    ON photo_metadata(engine_name);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_version
    ON photo_metadata(plugin_version);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_processed
    ON photo_metadata(processed_at DESC);

-- =============================================================================
-- STEP 4: Add comments for documentation
-- =============================================================================

COMMENT ON COLUMN photo_metadata.plugin_name IS 
    'Plugin that produced this observation (e.g., metadata.exif.pillow)';
COMMENT ON COLUMN photo_metadata.engine_name IS 
    'Engine used by plugin (e.g., pillow-exif)';
COMMENT ON COLUMN photo_metadata.plugin_version IS 
    'Version of the plugin (e.g., 1.0.0)';
COMMENT ON COLUMN photo_metadata.processed_at IS 
    'When this observation was created';
COMMENT ON COLUMN photo_metadata.artifact_hash IS 
    'SHA256 hash of source artifact for integrity';

-- =============================================================================
-- STEP 5: Apply to other existing tables
-- =============================================================================

-- entities table
ALTER TABLE entities
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100) DEFAULT 'entity-extractor';
ALTER TABLE entities
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100) DEFAULT 'spacy';
ALTER TABLE entities
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50) DEFAULT '1.0.0';
ALTER TABLE entities
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- document_content table
ALTER TABLE document_content
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100) DEFAULT 'text-extractor';
ALTER TABLE document_content
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100) DEFAULT 'textract';
ALTER TABLE document_content
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50) DEFAULT '1.0.0';
ALTER TABLE document_content
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- document_embeddings table
ALTER TABLE document_embeddings
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100) DEFAULT 'embeddings';
ALTER TABLE document_embeddings
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100);
ALTER TABLE document_embeddings
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50) DEFAULT '1.0.0';
ALTER TABLE document_embeddings
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- =============================================================================
-- STEP 6: Update existing evidence_lineage table
-- =============================================================================

-- Ensure plugin_name is not nullable
ALTER TABLE evidence_lineage
    ALTER COLUMN plugin_name SET NOT NULL;

-- =============================================================================
-- STEP 7: Record migration
-- =============================================================================

INSERT INTO schema_migrations (migration_name)
VALUES ('011_plugin_foundation.sql');
```

## Rollback Procedure

```sql
-- Rollback: 011_plugin_foundation.sql

-- Remove new indexes
DROP INDEX IF EXISTS idx_photo_metadata_processed;
DROP INDEX IF EXISTS idx_photo_metadata_version;
DROP INDEX IF EXISTS idx_photo_metadata_engine;
DROP INDEX IF EXISTS idx_photo_metadata_plugin;

-- Restore original UNIQUE constraint
ALTER TABLE photo_metadata 
    DROP CONSTRAINT IF EXISTS uq_photo_metadata_identity;
ALTER TABLE photo_metadata 
    ADD CONSTRAINT photo_metadata_document_id_key
    UNIQUE (document_id);

-- Remove added columns
ALTER TABLE photo_metadata
    DROP COLUMN IF EXISTS artifact_hash;
ALTER TABLE photo_metadata
    DROP COLUMN IF EXISTS processed_at;
ALTER TABLE photo_metadata
    DROP COLUMN IF EXISTS plugin_version;
ALTER TABLE photo_metadata
    DROP COLUMN IF EXISTS engine_name;
ALTER TABLE photo_metadata
    DROP COLUMN IF EXISTS plugin_name;

-- Remove from other tables (similar pattern)
-- ...

-- Remove migration record
DELETE FROM schema_migrations
WHERE migration_name = '011_plugin_foundation.sql';
```

## Code Changes

### 1. Plugin Registry (registry/plugin_registry.py)

```python
# Update PLUGIN_DEFINITIONS
PLUGIN_DEFINITIONS = {
    # Legacy names (for backward compatibility)
    'photo_metadata': {
        'job_type': 'extract_photo_metadata',
        'description': 'Extract EXIF metadata',
        'category': 'metadata',
        'type': 'exif',
        'engine': 'pillow-exif',
        'version': '1.0.0',
        'namespace': 'metadata.exif.pillow',  # NEW
    },
    # ... other plugins
}

# Update Plugin class
@dataclass
class Plugin:
    name: str                    # Legacy name
    job_type: str
    enabled: bool
    description: str = ""
    category: str = "general"
    type: str = None            # NEW
    engine: str = None          # NEW
    version: str = None         # NEW
    namespace: str = None       # NEW
```

### 2. Base Worker (workers/base.py)

```python
from abc import ABC, abstractmethod
from datetime import datetime

class BaseWorker(ABC):
    """Base class for worker job handlers."""
    
    # Class-level identity (set by subclasses)
    PLUGIN_NAME: str = None
    ENGINE_NAME: str = None
    PLUGIN_VERSION: str = None
    
    def __init__(self, backend):
        self.backend = backend
    
    def get_provenance(self, document_id: int) -> dict:
        """Build provenance for observation."""
        artifact_hash = self.backend.get_artifact_hash(document_id)
        
        return {
            'plugin_name': self.PLUGIN_NAME,
            'engine_name': self.ENGINE_NAME,
            'plugin_version': self.PLUGIN_VERSION,
            'processed_at': datetime.utcnow().isoformat(),
            'artifact_hash': artifact_hash,
        }
    
    @abstractmethod
    def process(self, job: dict) -> dict:
        """Process a single job."""
        pass
```

### 3. PhotoMetadataExtractor (workers/photo_metadata_extractor.py)

```python
class PhotoMetadataExtractor(BaseWorker):
    """Extracts photo metadata from image files."""
    
    # Plugin identity (NEW)
    PLUGIN_NAME = 'metadata.exif.pillow'
    ENGINE_NAME = 'pillow-exif'
    PLUGIN_VERSION = '1.0.0'
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif'}
    
    def __init__(self, backend, library_root: str = None):
        super().__init__(backend)
        self.library_root = library_root or get_library_root()
    
    def process(self, job: dict) -> dict:
        document_id = job['document_id']
        
        # ... existing extraction logic ...
        
        # Build observation with provenance (NEW)
        observation = {
            'document_id': document_id,
            'provenance': self.get_provenance(document_id),
            'data': metadata,  # Existing fields
        }
        
        # Save with provenance (NEW)
        self.backend.save_photo_metadata_with_provenance(document_id, observation)
        
        return observation
```

### 4. Backend (storage/postgres_backend.py)

```python
def save_photo_metadata_with_provenance(self, document_id: int, observation: dict):
    """Save photo metadata with provenance."""
    
    provenance = observation['provenance']
    data = observation['data']
    
    sql = """
        INSERT INTO photo_metadata (
            document_id,
            plugin_name,
            engine_name,
            plugin_version,
            processed_at,
            artifact_hash,
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
            file_format
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (document_id, plugin_name, engine_name)
        DO UPDATE SET
            plugin_version = EXCLUDED.plugin_version,
            processed_at = EXCLUDED.processed_at,
            timestamp_original = EXCLUDED.timestamp_original,
            gps_latitude = EXCLUDED.gps_latitude,
            gps_longitude = EXCLUDED.gps_longitude,
            -- ... other fields
    """
    
    params = (
        document_id,
        provenance['plugin_name'],
        provenance['engine_name'],
        provenance['plugin_version'],
        provenance['processed_at'],
        provenance.get('artifact_hash'),
        data.get('timestamp_original'),
        data.get('timestamp_digitized'),
        data.get('timestamp_metadata'),
        data.get('gps_latitude'),
        data.get('gps_longitude'),
        data.get('gps_altitude'),
        data.get('camera_make'),
        data.get('camera_model'),
        data.get('lens_model'),
        data.get('width'),
        data.get('height'),
        data.get('orientation'),
        data.get('file_format')
    )
    
    self._execute(sql, params)
```

## Validation Checklist

### Database Validation

```python
def validate_migration():
    """Validate migration completed successfully."""
    
    # 1. Check columns exist
    columns = get_columns('photo_metadata')
    required = ['plugin_name', 'engine_name', 'plugin_version', 'processed_at']
    for col in required:
        assert col in columns, f"Missing column: {col}"
    
    # 2. Check no NULL values
    null_counts = query("""
        SELECT COUNT(*) FROM photo_metadata
        WHERE plugin_name IS NULL
            OR engine_name IS NULL
            OR plugin_version IS NULL
            OR processed_at IS NULL
    """)
    assert null_counts == 0, f"Found {null_counts} rows with NULL identity"
    
    # 3. Check UNIQUE constraint
    constraint_exists = query("""
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_photo_metadata_identity'
    """)
    assert constraint_exists, "Missing UNIQUE constraint"
    
    # 4. Check indexes
    indexes = get_indexes('photo_metadata')
    required_indexes = ['idx_photo_metadata_plugin', 'idx_photo_metadata_engine']
    for idx in required_indexes:
        assert idx in indexes, f"Missing index: {idx}"
```

### Functional Validation

```python
def test_provenance():
    """Test provenance is included in observations."""
    
    # 1. Create test document
    doc = create_test_document(path='test.jpg')
    
    # 2. Process with extractor
    extractor = PhotoMetadataExtractor(backend)
    result = extractor.process({'document_id': doc.id})
    
    # 3. Verify provenance
    prov = result['provenance']
    assert prov['plugin_name'] == 'metadata.exif.pillow'
    assert prov['engine_name'] == 'pillow-exif'
    assert prov['plugin_version'] == '1.0.0'
    assert prov['processed_at'] is not None
    
    # 4. Verify stored
    stored = backend.get_photo_metadata(doc.id)
    assert stored['plugin_name'] == 'metadata.exif.pillow'
```

## Migration Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| 1. Database | 30 min | Run migration |
| 2. Registry | 1 hour | Update plugin_registry.py |
| 3. Workers | 2 hours | Update BaseWorker, extractors |
| 4. Backend | 1 hour | Update save methods |
| 5. Testing | 2 hours | Run tests, validate |
| 6. Staging | 4 hours | Deploy, verify |
| 7. Production | 1 hour | Deploy, verify |

**Total:** ~1-2 days

## Go/No-Go Criteria

### Database

- [ ] Migration runs without error
- [ ] All columns added
- [ ] All rows backfilled
- [ ] UNIQUE constraint applied
- [ ] Indexes created

### Code

- [ ] Plugin registry compiles
- [ ] Workers set identity
- [ ] Provenance included in observations
- [ ] Existing tests pass

### API

- [ ] Responses include provenance
- [ ] Backward compatible (existing clients work)
- [ ] No breaking changes

---

## Summary

| Aspect | Approach |
|--------|----------|
| Database | Additive columns + constraint update |
| Code | Update registry + workers |
| Backward compatibility | Default values + optional API |
| Rollback | Available via migration rollback |
| Testing | Validate migration + functional tests |
| Timeline | 1-2 days |
