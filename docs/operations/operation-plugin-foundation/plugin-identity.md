# Plugin Identity

**Purpose:** Document the minimum identity requirements for plugins in Librarian

---

## Identity Requirements

Every observation in Librarian must be attributable to:

| Field | Description | Example |
|-------|-------------|---------|
| `plugin_name` | The plugin that produced this observation | `exif`, `yolo`, `ocr` |
| `engine_name` | The specific engine used | `pillow-exif`, `yolov8n`, `tesseract` |
| `plugin_version` | Version of the plugin | `1.0.0`, `2.1.0` |

## Identity Examples

### EXIF Plugin

```python
plugin_name = "exif"
engine_name = "pillow-exif"
plugin_version = "1.0.0"
```

### Object Detection (Future)

```python
# YOLO engine
plugin_name = "object-detection"
engine_name = "yolov8n"
plugin_version = "1.0.0"

# Grounding DINO engine
plugin_name = "object-detection"
engine_name = "grounding-dino-s"
plugin_version = "1.0.0"
```

### OCR (Future)

```python
plugin_name = "ocr"
engine_name = "tesseract"
plugin_version = "1.0.0"
```

## Identity Structure

### Flat Names (Current)

```
photo_metadata
thumbnail
ocr
object_detection
transcription
embeddings
```

### Namespaced Names (Required)

```
exif.gps
exif.timestamp
exif.camera

vision.object-detection.yolo
vision.object-detection.grounding-dino

vision.ocr.tesseract

audio.transcription.whisper

embeddings.openai
embeddings.sentence-transformers
```

## Plugin Class Data

```python
@dataclass
class PluginIdentity:
    """Minimum identity for a plugin."""
    
    # Required fields
    plugin_name: str           # e.g., "exif", "object-detection"
    engine_name: str          # e.g., "pillow-exif", "yolov8n"
    plugin_version: str        # e.g., "1.0.0"
    
    # Optional but recommended
    plugin_category: str = None  # e.g., "metadata", "vision", "audio"
```

## Registry Changes

### Current Registry Entry

```python
PLUGIN_DEFINITIONS = {
    'photo_metadata': {
        'job_type': 'extract_photo_metadata',
        'description': 'Extract EXIF metadata',
        'category': 'metadata',
    },
}
```

### Required Registry Entry

```python
PLUGIN_DEFINITIONS = {
    'exif': {
        'job_type': 'extract_exif',
        'description': 'Extract EXIF metadata',
        'category': 'metadata',
        'engine': 'pillow-exif',        # Required
        'version': '1.0.0',            # Required
    },
}
```

## Observation Identity

Every observation stored must include:

```python
{
    "observation_id": "uuid",
    "document_id": 123,
    
    # Identity (required)
    "plugin_name": "exif",
    "engine_name": "pillow-exif", 
    "plugin_version": "1.0.0",
    
    # Data
    "data": {
        "gps": {"latitude": 10.3, "longitude": 123.9},
        "timestamp": "2026-01-01T12:00:00Z"
    }
}
```

## Identity in Database

### Current Schema

```sql
-- photo_metadata table
CREATE TABLE photo_metadata (
    document_id INTEGER REFERENCES documents(id) UNIQUE,
    extraction_method VARCHAR(50),  -- Partial identity
    extraction_version VARCHAR(50),
    ...
);
```

### Required Schema

```sql
-- photo_metadata table with full identity
CREATE TABLE photo_metadata (
    document_id INTEGER REFERENCES documents(id),
    
    -- Full identity
    plugin_name VARCHAR(100) NOT NULL DEFAULT 'exif',
    engine_name VARCHAR(100) NOT NULL,
    plugin_version VARCHAR(50) NOT NULL,
    
    -- Data
    gps_latitude DOUBLE PRECISION,
    gps_longitude DOUBLE PRECISION,
    ...
    
    -- Unique constraint allows multiple engines
    UNIQUE (document_id, plugin_name, engine_name)
);
```

## Migration Path

### Phase 1: Add Identity Columns

```sql
ALTER TABLE photo_metadata
    ADD COLUMN IF NOT EXISTS plugin_name VARCHAR(100) DEFAULT 'exif',
    ADD COLUMN IF NOT EXISTS engine_name VARCHAR(100) DEFAULT 'pillow-exif',
    ADD COLUMN IF NOT EXISTS plugin_version VARCHAR(50) DEFAULT '1.0.0';

-- Backfill existing rows
UPDATE photo_metadata 
SET plugin_name = 'exif',
    engine_name = 'pillow-exif',
    plugin_version = '1.0.0'
WHERE plugin_name IS NULL;
```

### Phase 2: Update UNIQUE Constraint

```sql
-- Remove old constraint
ALTER TABLE photo_metadata 
    DROP CONSTRAINT IF EXISTS photo_metadata_document_id_key;

-- Add new constraint
ALTER TABLE photo_metadata 
    ADD CONSTRAINT uq_photo_metadata_identity
    UNIQUE (document_id, plugin_name, engine_name);
```

## Version Format

Use semantic versioning:

```
MAJOR.MINOR.PATCH

1.0.0 - Initial release
1.1.0 - Added new fields
2.0.0 - Breaking changes
```

## Identity Validation

```python
def validate_identity(identity: PluginIdentity) -> bool:
    """Validate plugin identity has all required fields."""
    
    required_fields = ['plugin_name', 'engine_name', 'plugin_version']
    
    for field in required_fields:
        if not getattr(identity, field, None):
            raise ValueError(f"Missing required field: {field}")
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', identity.plugin_version):
        raise ValueError(f"Invalid version format: {identity.plugin_version}")
    
    return True
```

## Summary

| Requirement | Current | Required |
|-------------|---------|----------|
| plugin_name | Partial | ✅ Required |
| engine_name | ❌ Missing | ✅ Required |
| plugin_version | Partial | ✅ Required |
| Namespaced naming | ❌ None | ✅ Required |
| UNIQUE with engine | ❌ No | ✅ Yes |

---

## Implementation Checklist

- [ ] Update Plugin class with identity fields
- [ ] Update PLUGIN_DEFINITIONS with engine and version
- [ ] Add identity columns to photo_metadata table
- [ ] Update UNIQUE constraint
- [ ] Update workers to set identity
- [ ] Validate identity in worker base class
