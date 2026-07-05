# Implementation Options

**Purpose:** Document the implementation approaches for Operation Plugin Foundation

---

## Scope

Operation Plugin Foundation implements the minimum runtime foundation:

1. Plugin Identity
2. Provenance
3. Namespacing
4. Reprocessing Boundaries
5. Multi-Engine Readiness

This is NOT a full plugin framework - just the minimum required for coexistence.

## Options Analysis

### Option A: Minimal Change (Recommended)

**Approach:** Add columns to existing tables, update existing code minimally.

**Changes:**
1. Add identity columns to observation tables
2. Update plugin registry with identity fields
3. Update existing workers to include provenance
4. Update UNIQUE constraints

**Pros:**
- ✅ Minimal blast radius
- ✅ Low risk
- ✅ Incremental evolution
- ✅ Works with existing tests

**Cons:**
- ❌ May need future refactoring
- ❌ Not as clean as full redesign

**Effort:** ~2-3 days

---

### Option B: Hybrid Approach

**Approach:** Add columns + create observation lineage table.

**Changes:**
1. Add identity columns to observation tables
2. Create unified observation_lineage table
3. Update workers to populate both
4. Update queries to use lineage

**Pros:**
- ✅ Better for future queries
- - ✅ Unified provenance tracking
- ✅ Clear separation

**Cons:**
- ❌ More complex
- ❌ More changes
- ❌ Migration complexity

**Effort:** ~1 week

---

### Option C: Full Redesign

**Approach:** Create unified observations table, migrate all data.

**Changes:**
1. Create unified observations table
2. Migrate all existing data
3. Update all queries
4. Update all workers

**Pros:**
- ✅ Clean design
- ✅ Future-proof
- ✅ Single source of truth

**Cons:**
- ❌ High risk
- ❌ Complex migration
- ❌ Long timeline
- ❌ Not aligned with "small changes" principle

**Effort:** ~2-3 weeks

---

## Recommended: Option A

Operation Plugin Foundation recommends **Option A: Minimal Change** because:

1. **Principle alignment:** "small changes, incremental evolution, low blast radius"
2. **Risk mitigation:** Existing system remains stable
3. **Future flexibility:** Option B or C can be pursued later if needed
4. **Timeline:** Completes within sprint

## Option A: Implementation Details

### 1. Database Migration

```sql
-- Migration: 011_plugin_foundation.sql
-- Adds plugin identity and provenance to observation tables

-- photo_metadata table updates
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100) 
        DEFAULT 'metadata.exif.pillow',
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100) 
        DEFAULT 'pillow-exif',
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50) 
        DEFAULT '1.0.0',
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP 
        DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS artifact_hash VARCHAR(64);

-- Update existing rows
UPDATE photo_metadata 
SET plugin_name = 'metadata.exif.pillow',
    engine_name = 'pillow-exif',
    plugin_version = '1.0.0',
    processed_at = CURRENT_TIMESTAMP,
    artifact_hash = (SELECT sha256 FROM documents WHERE id = photo_metadata.document_id)
WHERE plugin_name IS NULL;

-- Update UNIQUE constraint
ALTER TABLE photo_metadata 
    DROP CONSTRAINT IF EXISTS photo_metadata_document_id_key;

ALTER TABLE photo_metadata 
    ADD CONSTRAINT uq_photo_metadata_identity
    UNIQUE (document_id, plugin_name, engine_name);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_photo_metadata_plugin 
    ON photo_metadata(plugin_name);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_engine 
    ON photo_metadata(engine_name);
```

### 2. Plugin Registry Updates

```python
# Update PLUGIN_DEFINITIONS
PLUGIN_DEFINITIONS = {
    'metadata.exif.pillow': {
        'job_type': 'extract_exif',
        'description': 'Extract EXIF metadata',
        'category': 'metadata',
        'type': 'exif',
        'engine': 'pillow-exif',
        'version': '1.0.0',
    },
    # ... others
}

# Update Plugin class
@dataclass
class Plugin:
    name: str
    job_type: str
    enabled: bool
    category: str
    type: str  # NEW
    engine: str  # NEW
    version: str  # NEW
```

### 3. Worker Updates

```python
# BaseWorker includes provenance
class BaseWorker:
    def __init__(self, backend):
        self.backend = backend
        self.plugin_name = self.__class__.PLUGIN_NAME
        self.engine_name = self.__class__.ENGINE_NAME
        self.plugin_version = self.__class__.PLUGIN_VERSION
    
    def get_provenance(self, document_id: int) -> dict:
        """Build provenance for observation."""
        artifact_hash = self.backend.get_artifact_hash(document_id)
        return {
            'plugin_name': self.plugin_name,
            'engine_name': self.engine_name,
            'plugin_version': self.plugin_version,
            'processed_at': datetime.utcnow().isoformat(),
            'artifact_hash': artifact_hash,
        }

# PhotoMetadataExtractor
class PhotoMetadataExtractor(BaseWorker):
    PLUGIN_NAME = 'metadata.exif.pillow'
    ENGINE_NAME = 'pillow-exif'
    PLUGIN_VERSION = '1.0.0'
    
    def process(self, job: dict) -> dict:
        document_id = job['document_id']
        
        # Extract metadata
        data = self._extract_metadata(document_id)
        
        # Build observation with provenance
        observation = {
            'document_id': document_id,
            'provenance': self.get_provenance(document_id),
            'data': data,
        }
        
        # Save with provenance
        self.backend.save_with_provenance('photo_metadata', observation)
        
        return observation
```

### 4. Backend Updates

```python
def save_with_provenance(self, table: str, observation: dict):
    """Save observation with provenance."""
    
    provenance = observation['provenance']
    data = observation['data']
    
    sql = f"""
        INSERT INTO {table} (
            document_id,
            plugin_name,
            engine_name,
            plugin_version,
            processed_at,
            artifact_hash,
            ...
        ) VALUES (
            %s, %s, %s, %s, %s, %s, ...
        )
        ON CONFLICT (document_id, plugin_name, engine_name)
        DO UPDATE SET
            plugin_version = EXCLUDED.plugin_version,
            processed_at = EXCLUDED.processed_at,
            ...
    """
```

## Migration Path

### Phase 1: Database (Day 1)

1. Create migration file
2. Add columns to photo_metadata
3. Update UNIQUE constraint
4. Add indexes
5. Validate migration

### Phase 2: Registry (Day 1-2)

1. Update PLUGIN_DEFINITIONS
2. Update Plugin class
3. Add validation
4. Update get_plugin_info()

### Phase 3: Workers (Day 2-3)

1. Update BaseWorker with provenance
2. Update PhotoMetadataExtractor
3. Add get_provenance() method
4. Test with existing data

### Phase 4: Backend (Day 3)

1. Add save_with_provenance()
2. Update existing save methods
3. Update queries for identity

### Phase 5: Testing (Day 3-4)

1. Run existing tests
2. Add provenance validation tests
3. Test migration rollback
4. Validate backward compatibility

## Backward Compatibility

### Old API Response

```json
{
    "document_id": 123,
    "gps": {"latitude": 10.3, "longitude": 123.9}
}
```

### New API Response

```json
{
    "document_id": 123,
    "provenance": {
        "plugin_name": "metadata.exif.pillow",
        "engine_name": "pillow-exif",
        "plugin_version": "1.0.0",
        "processed_at": "2026-07-05T10:30:00Z"
    },
    "data": {
        "gps": {"latitude": 10.3, "longitude": 123.9}
    }
}
```

### Compatibility Layer

For backward compatibility, add provenance as optional field:

```python
def get_photo_metadata(document_id: int, include_provenance: bool = False):
    """Get photo metadata, optionally with provenance."""
    
    result = db.query("""
        SELECT * FROM photo_metadata
        WHERE document_id = %s
    """, document_id)
    
    if include_provenance:
        return {
            'document_id': result.document_id,
            'provenance': {
                'plugin_name': result.plugin_name,
                'engine_name': result.engine_name,
                'plugin_version': result.plugin_name,
                'processed_at': result.processed_at.isoformat(),
            },
            'data': {
                'gps': {...},
                ...
            }
        }
    else:
        # Legacy format
        return {
            'document_id': result.document_id,
            'gps': {...},
            ...
        }
```

## Validation

### Migration Validation

```python
def validate_migration():
    """Validate migration completed successfully."""
    
    # Check columns exist
    columns = get_columns('photo_metadata')
    assert 'plugin_name' in columns
    assert 'engine_name' in columns
    assert 'plugin_version' in columns
    
    # Check no NULL values
    null_count = query("""
        SELECT COUNT(*) FROM photo_metadata
        WHERE plugin_name IS NULL
    """)
    assert null_count == 0
    
    # Check UNIQUE constraint
    # Should allow multiple engines in future
    duplicates = query("""
        SELECT document_id, COUNT(*) as cnt
        FROM photo_metadata
        GROUP BY document_id
        HAVING COUNT(*) > 1
    """)
    assert len(duplicates) == 0  # Currently only one engine
```

### Functional Validation

```python
def test_provenance():
    """Test provenance is included in observations."""
    
    # Create document
    doc = create_test_document()
    
    # Process with EXIF extractor
    extractor = PhotoMetadataExtractor(backend)
    result = extractor.process({'document_id': doc.id})
    
    # Verify provenance
    assert result['provenance']['plugin_name'] == 'metadata.exif.pillow'
    assert result['provenance']['engine_name'] == 'pillow-exif'
    assert result['provenance']['plugin_version'] == '1.0.0'
    assert result['provenance']['processed_at'] is not None
    assert result['provenance']['artifact_hash'] is not None
```

## Summary

| Option | Effort | Risk | Complexity | Recommendation |
|--------|--------|------|------------|----------------|
| A: Minimal | 2-3 days | Low | Low | ✅ **Recommended** |
| B: Hybrid | 1 week | Medium | Medium | For future |
| C: Full | 2-3 weeks | High | High | Not recommended |

Operation Plugin Foundation uses **Option A** to establish the minimum foundation for plugin coexistence.
