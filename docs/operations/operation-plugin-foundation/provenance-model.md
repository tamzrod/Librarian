# Provenance Model

**Purpose:** Document the minimum provenance tracking for observations

---

## Provenance Requirements

Every observation must be able to answer:

1. **Who** produced this observation?
2. **Which engine** produced it?
3. **Which version** produced it?
4. **When** was it produced?

## Provenance Model

### Minimum Provenance Fields

```python
@dataclass
class Provenance:
    """Minimum provenance for an observation."""
    
    # Who
    plugin_name: str          # Who produced this
    
    # Which engine
    engine_name: str          # Which engine
    
    # Which version  
    plugin_version: str        # Version that produced this
    
    # When
    processed_at: datetime    # When produced
    
    # Optional
    artifact_hash: str = None  # SHA256 of source artifact
```

### Extended Provenance Fields

```python
@dataclass
class ExtendedProvenance:
    """Extended provenance for detailed tracking."""
    
    # Identity
    plugin_name: str
    engine_name: str
    plugin_version: str
    
    # Source
    artifact_hash: str
    artifact_path: str
    artifact_mime_type: str
    
    # Timing
    processed_at: datetime
    processing_time_ms: int
    
    # Quality
    confidence: float = None
    
    # Lineage
    parent_observation_id: str = None
```

## Current State

### What Exists

```sql
-- photo_metadata has partial provenance
CREATE TABLE photo_metadata (
    extraction_method VARCHAR(50) DEFAULT 'exif',  -- Partial
    extraction_version VARCHAR(50),                 -- Partial
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Partial
);
```

### What's Missing

| Field | Current | Required |
|-------|---------|----------|
| plugin_name | ❌ Missing | ✅ Required |
| engine_name | ❌ Missing | ✅ Required |
| artifact_hash | ❌ Missing | ⚠️ Recommended |
| processed_at | ⚠️ Partial | ✅ Required |

## Proposed Provenance Model

### Option A: Inline Provenance

Add provenance columns directly to observation tables.

```sql
CREATE TABLE photo_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    
    -- Provenance (NEW)
    plugin_name VARCHAR(100) NOT NULL DEFAULT 'exif',
    engine_name VARCHAR(100) NOT NULL,
    plugin_version VARCHAR(50) NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    artifact_hash VARCHAR(64),
    
    -- Existing data
    gps_latitude DOUBLE PRECISION,
    gps_longitude DOUBLE PRECISION,
    ...
);
```

**Advantages:**
- Simple queries
- Fast lookups
- No JOINs needed

**Disadvantages:**
- Repeated columns
- Schema changes per table

---

### Option B: Provenance Table

Separate table for provenance, referenced by observation tables.

```sql
-- Provenance records
CREATE TABLE observation_provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identity
    plugin_name VARCHAR(100) NOT NULL,
    engine_name VARCHAR(100) NOT NULL,
    plugin_version VARCHAR(50) NOT NULL,
    
    -- Source
    artifact_hash VARCHAR(64),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    processing_time_ms INTEGER,
    confidence FLOAT
);

-- Photo metadata references provenance
CREATE TABLE photo_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    provenance_id UUID REFERENCES observation_provenance(id),
    
    -- Data
    gps_latitude DOUBLE PRECISION,
    gps_longitude DOUBLE PRECISION,
    ...
);
```

**Advantages:**
- Single source of truth
- Consistent across plugins
- Easy to query all provenance

**Disadvantages:**
- JOINs required
- More complex queries
- Referential integrity

---

### Option C: JSONB Provenance

Store provenance as JSONB column.

```sql
CREATE TABLE photo_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    
    -- Provenance as JSONB
    provenance JSONB NOT NULL DEFAULT '{
        "plugin_name": "exif",
        "engine_name": "pillow-exif", 
        "plugin_version": "1.0.0",
        "processed_at": null
    }',
    
    -- Data
    gps_latitude DOUBLE PRECISION,
    ...
);
```

**Advantages:**
- Flexible schema
- Easy to extend
- No schema changes for new fields

**Disadvantages:**
- Slower queries
- No typed columns
- Indexing challenges

---

### Recommended: Option A (Inline Provenance)

For Operation Plugin Foundation, inline provenance is recommended because:

1. **Simple** - No JOINs required
2. **Fast** - Direct column access
3. **Clear** - Provenance visible in each table
4. **Sufficient** - Meets minimum requirements

Future operations can adopt Option B if centralized provenance is needed.

## Provenance in Observations

### Worker Output

```python
def process_photo(self, document_id: int) -> dict:
    """Process a photo and return observation with provenance."""
    
    # Extract data
    data = self._extract_metadata(document_id)
    
    # Build observation with provenance
    return {
        'document_id': document_id,
        
        # Provenance (required)
        'provenance': {
            'plugin_name': self.plugin_name,
            'engine_name': self.engine_name,
            'plugin_version': self.plugin_version,
            'processed_at': datetime.utcnow().isoformat(),
            'artifact_hash': self._compute_hash(document_id)
        },
        
        # Data
        'data': data
    }
```

### Database Storage

```python
def save_photo_metadata(self, document_id: int, observation: dict):
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
            gps_latitude,
            gps_longitude,
            ...
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, ...
        )
        ON CONFLICT (document_id, plugin_name, engine_name)
        DO UPDATE SET
            plugin_version = EXCLUDED.plugin_version,
            processed_at = EXCLUDED.processed_at,
            gps_latitude = EXCLUDED.gps_latitude,
            ...
    """
```

## Provenance Queries

### Get Provenance for Observation

```sql
SELECT 
    document_id,
    plugin_name,
    engine_name,
    plugin_version,
    processed_at,
    artifact_hash
FROM photo_metadata
WHERE document_id = 123;
```

### Get All Observations with Provenance

```sql
SELECT 
    'photo_metadata' as observation_type,
    document_id,
    plugin_name,
    engine_name,
    plugin_version
FROM photo_metadata
UNION ALL
SELECT 
    'entities' as observation_type,
    document_id,
    plugin_name,
    engine_name,
    plugin_version
FROM entities;
```

### Get Observations by Plugin

```sql
SELECT *
FROM photo_metadata
WHERE plugin_name = 'exif'
ORDER BY processed_at DESC;
```

## Provenance API

### Get Observation with Provenance

```python
GET /api/v1/observations/{type}/{id}

Response:
{
    "id": 1,
    "document_id": 123,
    "provenance": {
        "plugin_name": "exif",
        "engine_name": "pillow-exif",
        "plugin_version": "1.0.0",
        "processed_at": "2026-07-05T10:30:00Z",
        "artifact_hash": "sha256:abc123..."
    },
    "data": {...}
}
```

### Get Provenance Summary

```python
GET /api/v1/provenance?document_id=123

Response:
{
    "document_id": 123,
    "observations": [
        {
            "observation_type": "photo_metadata",
            "plugin_name": "exif",
            "engine_name": "pillow-exif",
            "plugin_version": "1.0.0",
            "processed_at": "2026-07-05T10:30:00Z"
        }
    ]
}
```

## Summary

| Aspect | Current | Proposed |
|--------|---------|----------|
| plugin_name | ❌ Missing | ✅ Inline column |
| engine_name | ❌ Missing | ✅ Inline column |
| plugin_version | ⚠️ Optional | ✅ Inline column |
| processed_at | ⚠️ Partial | ✅ Inline column |
| artifact_hash | ❌ Missing | ⚠️ Optional |

---

## Implementation Checklist

- [ ] Add provenance columns to photo_metadata
- [ ] Add provenance columns to entities
- [ ] Add provenance columns to document_content
- [ ] Update workers to populate provenance
- [ ] Add provenance to API responses
- [ ] Add provenance validation
