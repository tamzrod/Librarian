# Reprocessing Boundaries

**Purpose:** Document how plugins maintain clear ownership for independent reprocessing

---

## Reprocessing Requirements

Support:

```
Reprocess: Object Detection
Without:   EXIF, OCR, Thumbnails, Embeddings
```

Plugins must have clear ownership boundaries.

## Current State

### What's Available

```sql
-- scan_snapshots table tracks processed files
CREATE TABLE scan_snapshots (
    scan_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    worker_version VARCHAR(100),
    ...
);

-- document_jobs tracks per-job status
CREATE TABLE document_jobs (
    document_id INTEGER REFERENCES documents(id),
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50),
    ...
);
```

### What's Missing

| Capability | Current | Required |
|-----------|---------|----------|
| Per-plugin reprocessing | ❌ No | ✅ Yes |
| Plugin version tracking | ⚠️ Partial | ✅ Yes |
| Selective reprocessing | ❌ No | ✅ Yes |

## Ownership Model

### Plugin Ownership

Each plugin owns its observations:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OWNERSHIP MODEL                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Artifact: IMG_0001.JPG                                                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ EXIF Plugin                                                          │  │
│  │ owns: photo_metadata                                                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Object Detection Plugin (future)                                     │  │
│  │ owns: object_detections                                              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ OCR Plugin (future)                                                  │  │
│  │ owns: ocr_text                                                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Each plugin owns its observation tables. Reprosessing one does not        │
│  affect others.                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Reprocessing Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REPROCESSING BOUNDARIES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  When reprocessing EXIF:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Reprocess: photo_metadata                                            │  │
│  │ Skip: object_detections, ocr_text, thumbnails, embeddings           │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  When reprocessing Object Detection:                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Reprocess: object_detections                                        │  │
│  │ Skip: photo_metadata, ocr_text, thumbnails, embeddings              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Each plugin's reprocessing is isolated to its own tables.                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Implementation

### Per-Plugin Job Types

Current:
```python
job_type = 'extract_photo_metadata'
```

Required:
```python
job_type = 'extract_exif'  # From metadata.exif.pillow plugin
job_type = 'detect_objects'  # From vision.object-detection.yolo plugin
```

### Job Scheduling

```python
def schedule_jobs(document_id: int, artifact_type: str):
    """Schedule jobs based on enabled plugins."""
    
    plugins = get_enabled_plugins(artifact_type)
    
    for plugin in plugins:
        # Each plugin creates its own job type
        job_type = f"process_{plugin.type}"  # e.g., extract_exif, detect_objects
        
        # Job is isolated to this plugin
        create_job(
            document_id=document_id,
            job_type=job_type,
            plugin_name=plugin.name,  # e.g., metadata.exif.pillow
        )
```

### Reprocessing API

```python
# Reprocess specific plugin
POST /api/v1/plugins/{plugin_name}/reprocess

# Reprocess specific plugin for specific artifacts
POST /api/v1/plugins/{plugin_name}/reprocess
{
    "document_ids": [1, 2, 3]
}

# Reprocess ALL artifacts for plugin
POST /api/v1/plugins/{plugin_name}/reprocess
{
    "scope": "all"
}
```

### Reprocessing Logic

```python
def reprocess_plugin(plugin_name: str, document_ids: list = None):
    """
    Reprocess observations for a specific plugin.
    
    Only affects observations owned by this plugin.
    """
    
    # Get plugin identity
    plugin = get_plugin(plugin_name)
    
    # Determine scope
    if document_ids:
        docs = document_ids
    else:
        # Get all documents with this plugin's observations
        docs = get_documents_with_observation(plugin_name)
    
    # Queue jobs for each document
    for doc_id in docs:
        create_job(
            document_id=doc_id,
            job_type=f"process_{plugin.type}",
            plugin_name=plugin.name,
            reprocess=True,
            reprocess_reason=f"manual_reprocess_{datetime.utcnow().isoformat()}"
        )
```

## Version-Based Reprocessing

### Version Tracking

```python
# Each observation tracks plugin version
observation = {
    'document_id': 123,
    'plugin_name': 'metadata.exif.pillow',
    'plugin_version': '1.0.0',
    'data': {...}
}
```

### Automatic Reprocessing

```python
def on_plugin_upgrade(plugin_name: str, old_version: str, new_version: str):
    """
    Trigger reprocessing when plugin version changes.
    """
    
    # Find all observations with old version
    affected = get_observations(
        plugin_name=plugin_name,
        plugin_version=old_version
    )
    
    # Queue reprocessing
    for obs in affected:
        create_job(
            document_id=obs.document_id,
            job_type=f"process_{plugin.type}",
            plugin_name=plugin_name,
            reprocess=True,
            reprocess_reason=f"version_upgrade_{old_version}_to_{new_version}"
        )
```

## Isolation Guarantees

### What Each Plugin Controls

| Plugin | Owns | Reprocesses |
|--------|------|-------------|
| EXIF | photo_metadata | photo_metadata only |
| Object Detection | object_detections | object_detections only |
| OCR | ocr_text | ocr_text only |
| Thumbnails | thumbnails | thumbnails only |

### Cross-Plugin Independence

```python
# Reprocessing EXIF does NOT touch other tables
def reprocess_exif(document_id: int):
    # Updates photo_metadata
    update_photo_metadata(document_id, ...)
    
    # Does NOT touch:
    # - object_detections
    # - ocr_text
    # - thumbnails
    # - embeddings
```

## Database Schema

### Per-Plugin Observation Tables

```sql
-- Each plugin has its own table
CREATE TABLE photo_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    plugin_name VARCHAR(100) NOT NULL DEFAULT 'metadata.exif.pillow',
    plugin_version VARCHAR(50) NOT NULL,
    ...
);

CREATE TABLE object_detections (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    plugin_name VARCHAR(100) NOT NULL DEFAULT 'vision.object-detection.yolo',
    plugin_version VARCHAR(50) NOT NULL,
    ...
);

CREATE TABLE ocr_text (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    plugin_name VARCHAR(100) NOT NULL DEFAULT 'vision.ocr.tesseract',
    plugin_version VARCHAR(50) NOT NULL,
    ...
);
```

## API Boundaries

### Get Observations by Plugin

```python
GET /api/v1/plugins/{plugin_name}/observations

Response:
{
    "plugin_name": "metadata.exif.pillow",
    "observation_count": 1523,
    "observations": [...]
}
```

### Reprocess Plugin

```python
POST /api/v1/plugins/{plugin_name}/reprocess

Request:
{
    "document_ids": [1, 2, 3],  # Optional, omit for all
    "reason": "manual"
}

Response:
{
    "job_id": "reprocess-123",
    "plugin_name": "metadata.exif.pillow",
    "queued_count": 3,
    "status": "queued"
}
```

## Summary

| Requirement | Implementation |
|-------------|---------------|
| Per-plugin reprocessing | Each plugin owns its table |
| Isolated reprocessing | Reprocess one table, others unchanged |
| Version-based reprocessing | Track plugin_version in observations |
| Selective reprocessing | Reprocess by document_ids |

---

## Implementation Checklist

- [ ] Update job types to be per-plugin
- [ ] Update job scheduling to use plugin names
- [ ] Add reprocessing API for plugin
- [ ] Add version tracking to observations
- [ ] Test reprocessing isolation
