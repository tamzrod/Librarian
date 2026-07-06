# Multi-Engine Readiness

**Purpose:** Document how the architecture supports multiple engines within the same plugin category

---

## Multi-Engine Requirements

The architecture must not prevent:

```
Object Detection
├── YOLO
├── Grounding DINO
└── OWL-ViT
```

from coexisting.

This operation does not require implementation of those engines. Only readiness for coexistence.

## Current State

### UNIQUE Constraint Problem

```sql
-- Current: UNIQUE on document_id only
CREATE TABLE photo_metadata (
    document_id INTEGER REFERENCES documents(id) UNIQUE,
    ...
);
```

This prevents multiple engines from storing observations for the same document.

### Example Conflict

```
Document: IMG_0001.JPG

EXIF (current):
  Only one row allowed per document.

Future Multi-Engine:
  yolo_v8: {objects: [...]}     ✓ Should be allowed
  grounding_dino: {objects: [...]}  ✓ Should be allowed
  owl_vit: {objects: [...]}     ✓ Should be allowed
```

## Required Schema

### Multi-Engine UNIQUE Constraint

```sql
-- Required: UNIQUE on (document_id, plugin_name, engine_name)
CREATE TABLE object_detections (
    document_id INTEGER REFERENCES documents(id),
    plugin_name VARCHAR(100) NOT NULL,
    engine_name VARCHAR(100) NOT NULL,
    plugin_version VARCHAR(50) NOT NULL,
    
    -- Data
    objects JSONB NOT NULL,
    
    -- Unique constraint allows multiple engines
    UNIQUE (document_id, plugin_name, engine_name)
);
```

### What This Enables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MULTI-ENGINE STORAGE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Document: IMG_0001.JPG                                                    │
│                                                                             │
│  object_detections table:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ engine_name        | objects                                       │  │
│  ├─────────────────────────────────────────────────────────────────────┤  │
│  │ yolo_v8n          | [{label: "person", confidence: 0.95}]         │  │
│  │ yolo_v8s          | [{label: "person", confidence: 0.97}]         │  │
│  │ grounding_dino_s   | [{label: "person", confidence: 0.99}]         │  │
│  │ owl_vit_base       | [{label: "person", confidence: 0.93}]         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  All engines coexist. Each has its own row.                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Engine Identity

### Engine Naming

| Engine | Full Name | Category | Type |
|--------|-----------|----------|------|
| YOLOv8 Nano | `vision.object-detection.yolo_v8n` | vision | object-detection |
| YOLOv8 Small | `vision.object-detection.yolo_v8s` | vision | object-detection |
| Grounding DINO | `vision.object-detection.grounding_dino` | vision | object-detection |
| OWL-ViT | `vision.object-detection.owl_vit` | vision | object-detection |

### Engine Identification

```python
# Each engine has unique identity
class DetectionEngine:
    def __init__(self, name: str, version: str):
        self.name = name          # e.g., "yolo_v8n"
        self.version = version    # e.g., "8.0.0"
        self.full_name = f"vision.object-detection.{name}"
        # e.g., "vision.object-detection.yolo_v8n"
```

## Multi-Engine Queries

### Get All Engine Results

```sql
SELECT 
    document_id,
    engine_name,
    plugin_version,
    objects
FROM object_detections
WHERE document_id = 123
ORDER BY engine_name;
```

### Compare Engine Results

```sql
SELECT 
    engine_name,
    JSONB_ARRAY_LENGTH(objects) as object_count
FROM object_detections
WHERE document_id = 123;
```

### Merge Results

```python
def merge_detections(document_id: int) -> list:
    """Merge detections from all engines."""
    
    results = db.query("""
        SELECT engine_name, objects
        FROM object_detections
        WHERE document_id = %s
    """, document_id)
    
    merged = []
    for row in results:
        for obj in row.objects:
            merged.append({
                **obj,
                'source_engine': row.engine_name
            })
    
    return merged
```

## Engine Selection

### Default Engine

```yaml
# config/plugins.yaml
plugins:
  vision.object-detection:
    default_engine: yolo_v8n
    engines:
      yolo_v8n:
        enabled: true
      grounding_dino:
        enabled: false
      owl_vit:
        enabled: false
```

### Runtime Selection

```python
def get_engine(plugin_name: str, engine_name: str = None):
    """Get engine instance by name."""
    
    if engine_name is None:
        # Use default engine
        config = get_plugin_config(plugin_name)
        engine_name = config['default_engine']
    
    # Return engine instance
    if engine_name == 'yolo_v8n':
        return YOLOv8Engine(model='yolov8n.pt')
    elif engine_name == 'grounding_dino':
        return GroundingDINOEngine()
    # ...
```

## Current Tables to Update

### photo_metadata

Current:
```sql
UNIQUE (document_id)
```

Required:
```sql
UNIQUE (document_id, plugin_name, engine_name)
```

Note: For EXIF, `plugin_name='metadata.exif.pillow'` and `engine_name='pillow-exif'` would be constant.

### Future Tables

For Object Detection:
```sql
CREATE TABLE object_detections (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    plugin_name VARCHAR(100) NOT NULL DEFAULT 'vision.object-detection.yolo',
    engine_name VARCHAR(100) NOT NULL,
    plugin_version VARCHAR(50) NOT NULL,
    objects JSONB NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (document_id, plugin_name, engine_name)
);
```

## Migration Path

### Phase 1: Update UNIQUE Constraints

```sql
-- For photo_metadata
ALTER TABLE photo_metadata 
    DROP CONSTRAINT IF EXISTS photo_metadata_document_id_key;

ALTER TABLE photo_metadata 
    ADD CONSTRAINT uq_photo_metadata_multi_engine
    UNIQUE (document_id, plugin_name, engine_name);
```

### Phase 2: Future Tables

New tables for new plugins will use multi-engine schema:

```sql
-- Object Detection (when implemented)
CREATE TABLE object_detections (
    ...
    UNIQUE (document_id, plugin_name, engine_name)
);
```

## Engine Coexistence Example

```python
# Example: Processing an image with multiple engines

def process_with_all_engines(document_id: int):
    """Process document with all enabled engines."""
    
    document = get_document(document_id)
    
    # Get enabled engines
    engines = get_enabled_engines('vision.object-detection')
    
    results = []
    for engine in engines:
        # Run inference
        result = engine.detect(document.path)
        
        # Store result
        save_observation(
            document_id=document_id,
            plugin_name='vision.object-detection.yolo',
            engine_name=engine.name,
            plugin_version='1.0.0',
            data={'objects': result.objects}
        )
        
        results.append({
            'engine': engine.name,
            'objects': result.objects
        })
    
    return results
```

## Summary

| Aspect | Current | Required |
|--------|---------|----------|
| UNIQUE constraint | `document_id` only | `(document_id, plugin_name, engine_name)` |
| Multiple engines | ❌ Not supported | ✅ Supported |
| Engine comparison | ❌ Not possible | ✅ Possible |
| Engine selection | N/A | ✅ Configurable |

---

## Implementation Checklist

- [ ] Update UNIQUE constraint on photo_metadata
- [ ] Design multi-engine schema for future plugins
- [ ] Add engine selection to configuration
- [ ] Document multi-engine query patterns
