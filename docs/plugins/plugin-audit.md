# Plugin Architecture Audit

**Date:** 2026-07-05  
**Objective:** Determine whether the current Librarian architecture supports multiple independent plugins operating on the same artifact.

---

## 1. Multiple Metadata Producers Per Artifact

**Classification:** Partially Supported

### Analysis

The architecture supports multiple metadata producers for some artifact types but not others:

**Supported:**
- **Entities**: The `evidence_lineage` table (`storage/migrations/002_entities.sql`) tracks `plugin_name`, allowing multiple plugins to produce entities for the same document. The `EntityExtractor` (`workers/entity_extractor.py`) records `plugin_name='entity_extractor'` in `record_evidence()`.

**Unsupported:**
- **Photo Metadata**: `photo_metadata` table has `UNIQUE` constraint on `document_id` (`storage/migrations/003_photo_metadata.sql`). Only one metadata record per document.
  
- **Embeddings**: `document_embeddings` table has `UNIQUE` constraint on `document_id` (`storage/migrations/006_embeddings.sql`). Only one embedding per document.

- **Content**: `document_content` table has `UNIQUE` constraint on `document_id`. Only one content extraction per document.

- **Thumbnails**: `documents.thumbnail_path` column stores a single thumbnail path. Only one thumbnail per document.

### Blockers
1. **UNIQUE constraints** on `document_id` in metadata tables prevent multiple producers
2. **No plugin identifier** in most metadata tables to disambiguate producers
3. **Single-valued columns** (e.g., `thumbnail_path`) limit to one artifact

### Implementation Complexity
**High** - Requires schema changes to:
1. Remove or modify UNIQUE constraints
2. Add plugin namespacing columns
3. Update query patterns to filter by plugin

---

## 2. Metadata Namespacing

**Classification:** Unsupported

### Analysis

No plugin namespacing exists in metadata storage:

| Table | Has Plugin Column | Namespacing Pattern |
|-------|------------------|---------------------|
| `photo_metadata` | No | None |
| `document_embeddings` | No | None |
| `document_content` | No | None |
| `documents.thumbnail_path` | No | None |
| `evidence_lineage` | Yes (`plugin_name`) | Flat string |

The `evidence_lineage` table has a `plugin_name` VARCHAR(100) column, but this is for provenance tracking, not namespacing. There is no hierarchical or prefixed namespacing (e.g., `exif_gps_latitude`, `ocr_text`, `plugin_ocr_gps_latitude`).

### Blockers
1. No namespacing infrastructure in storage schema
2. No convention defined for namespaced metadata access
3. API endpoints return flat metadata structures

### Implementation Complexity
**Medium-High** - Requires:
1. Defining namespacing convention
2. Schema migration to add namespace columns or prefixes
3. Updating all query/insert patterns

---

## 3. Plugin Provenance Tracking

**Classification:** Partially Supported

### Analysis

Provenance tracking is inconsistent across metadata types:

**Supported:**
- **Entities**: `evidence_lineage` table fully tracks `plugin_name`, `confidence`, `processing_time_ms`, `version`

**Limited/Partial:**
- **Photo Metadata**: Has `extraction_method` and `extraction_version` but **no `plugin_name`** column. Cannot distinguish which plugin produced the metadata.

- **Embeddings**: Has `model` column (e.g., embedding model name) but **no `plugin_name**. Cannot track which plugin created the embedding.

- **Content**: Has `extraction_method` column but **no `plugin_name`**.

- **Thumbnails**: No provenance tracking at all.

### Blockers
1. `photo_metadata` table lacks `plugin_name` column
2. `document_embeddings` lacks `plugin_name` column  
3. `document_content` lacks `plugin_name` column
4. Thumbnails have no provenance table/columns

### Implementation Complexity
**Medium** - Add `plugin_name` columns to existing tables:
1. New migration: `ALTER TABLE photo_metadata ADD COLUMN plugin_name VARCHAR(100)`
2. New migration: `ALTER TABLE document_embeddings ADD COLUMN plugin_name VARCHAR(100)`
3. New migration: `ALTER TABLE document_content ADD COLUMN plugin_name VARCHAR(100)`
4. Create `thumbnail_metadata` table for thumbnail provenance
5. Update worker handlers to populate new columns

---

## 4. Independent Plugin Execution

**Classification:** Supported

### Analysis

The job queue system supports independent execution:

**Evidence:**
- `document_jobs` table tracks jobs by `document_id` and `job_type` (`storage/migrations/007_job_orchestration.sql`)
- `create_jobs_for_document()` creates multiple job types per document (`postgres_backend.py:1513`)
- Worker system processes jobs independently with `worker_id` and `lease_seconds` tracking (`workers/worker.py`)
- Jobs have independent state: `QUEUED`, `IN_PROGRESS`, `COMPLETED`, `BLOCKED`, `FAILED_PERMANENT`
- Job prerequisites allow ordering but plugins still execute independently (`job_prerequisites` table)

**Example Flow:**
```
Document discovered → Jobs created for each enabled plugin
                    → photo_metadata job queued
                    → thumbnail job queued  
                    → ocr job queued (if enabled)
                    → Each job runs independently
                    → Each job completes/fails independently
```

### Implementation Notes
This is a core capability already working well. No changes needed for independent plugin execution.

---

## 5. Independent Plugin Failure Handling

**Classification:** Supported

### Analysis

Robust failure handling per job:

**Evidence:**
- **Retry Logic**: Jobs retry with exponential backoff (defined in `postgres_backend.py:150-157`)
  - Attempt 1: Immediate
  - Attempt 2: 1 minute
  - Attempt 3: 5 minutes
  - Attempt 4: 30 minutes
  - Attempt 5: 2 hours
  - After 5 failures: `FAILED_PERMANENT` status

- **Independent States**: Each job tracks its own `attempt_count`, `error_message`, `next_retry_at`

- **Job Completion**: `complete_job()` method handles success/failure independently (`postgres_backend.py:1683`)

- **Lease Recovery**: Expired leases are recovered, allowing failed workers' jobs to be retried (`backend.recover_expired_leases()`)

### Implementation Notes
This is a core capability already working well. Plugin failures are isolated and don't cascade.

---

## 6. Plugin Enable/Disable Support

**Classification:** Supported

### Analysis

Full enable/disable infrastructure:

**Components:**
- `PluginRegistry` class (`registry/plugin_registry.py`)
  - `is_enabled(plugin_name)` - Check if plugin is enabled
  - `enable(plugin_name)` - Enable plugin
  - `disable(plugin_name)` - Disable plugin
  
- Configuration persistence (`config/plugin_config.py`)
  - `plugins.yaml` stores enabled state
  - Thread-safe read/write with `RLock`
  
- API Endpoints (`api/routes/settings.py`)
  - `GET /api/v1/settings/plugins` - List plugins
  - `PUT /api/v1/settings/plugins/{plugin_name}` - Enable/disable
  
- Runtime application (`postgres_backend.py:1549-1554`)
  - `get_job_types_for_artifact()` uses registry to filter enabled plugins
  - Only enabled plugins generate jobs

### Implementation Notes
This is a core capability already working well. Configuration survives restarts via YAML file.

---

## 7. Plugin Reprocessing Support

**Classification:** Partially Supported

### Analysis

**Supported:**
- **Failed Jobs**: Automatic retry via exponential backoff (up to 5 attempts)
- **Job Recreation**: Can create new jobs for completed documents by manually invoking `create_jobs_for_document()`

**Unsupported:**
- **No Selective Reprocessing API**: No endpoint to trigger reprocessing for a specific plugin
- **No Version-Based Reprocessing**: No mechanism to detect when a plugin version changes and needs reprocessing
- **No Artifact-Level Reprocessing**: Cannot request "reprocess document X with plugin Y" - only whole-document job creation

### Blockers
1. No `POST /reprocess` endpoint for selective reprocessing
2. No plugin version tracking to detect stale metadata
3. No mechanism to invalidate/regenerate specific plugin outputs

### Implementation Complexity
**Medium** - Would require:
1. Add `version` tracking to `plugin_types` table
2. Add `reprocess_document(document_id, plugin_name)` method to backend
3. Create API endpoint `POST /documents/{id}/reprocess`
4. Add UI support for reprocessing triggers

---

## 8. Derived Artifact Storage

**Classification:** Partially Supported

### Analysis

| Artifact Type | Storage Location | Supports Multiple | Notes |
|---------------|-----------------|------------------|-------|
| Thumbnail | `documents.thumbnail_path` (file path) | No | Single thumbnail per document |
| Embedding | `document_embeddings.embedding` (JSON TEXT) | No | UNIQUE on document_id |
| Extracted Text | `document_content.content` | No | UNIQUE on document_id |
| Photo EXIF | `photo_metadata` table | No | UNIQUE on document_id |
| Entities | `entities` + `evidence_lineage` | Yes | Multiple plugins tracked |

**Current Behavior:**
- Thumbnails stored on disk in `.thumbnails/` directory, path stored in DB
- Embeddings stored as JSON-serialized vectors
- Single value per document for most derived artifacts

### Blockers
1. UNIQUE constraints on `document_id` in `photo_metadata`, `document_embeddings`, `document_content`
2. Single `thumbnail_path` column (not an array or child table)
3. No storage pattern for multiple thumbnails (e.g., different sizes)

### Implementation Complexity
**High** - Would require:
1. Schema redesign for multi-producer metadata
2. Migration to child tables (e.g., `document_thumbnails`, `photo_metadata_v2`)
3. Update all query paths to handle multiple results
4. Implement cleanup/staleness policies

---

## Summary Table

| Capability | Status | Complexity to Fix |
|------------|--------|------------------|
| Multiple metadata producers per artifact | Partially Supported | High |
| Metadata namespacing | Unsupported | Medium-High |
| Plugin provenance tracking | Partially Supported | Medium |
| Independent plugin execution | Supported | N/A |
| Independent plugin failure handling | Supported | N/A |
| Plugin enable/disable support | Supported | N/A |
| Plugin reprocessing support | Partially Supported | Medium |
| Derived artifact storage | Partially Supported | High |

---

## Recommended Architectural Changes

### Priority 1: Add Provenance Tracking (Medium Complexity)

Add `plugin_name` columns to existing tables:

```sql
-- Photo metadata provenance
ALTER TABLE photo_metadata ADD COLUMN plugin_name VARCHAR(100);

-- Embedding provenance  
ALTER TABLE document_embeddings ADD COLUMN plugin_name VARCHAR(100);

-- Content provenance
ALTER TABLE document_content ADD COLUMN plugin_name VARCHAR(100);

-- Thumbnail provenance table
CREATE TABLE thumbnail_metadata (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    plugin_name VARCHAR(100) NOT NULL,
    thumbnail_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, plugin_name)
);
```

### Priority 2: Reprocessing API (Medium Complexity)

Add selective reprocessing capability:

```python
# In postgres_backend.py
def reprocess_document(self, document_id: int, plugin_name: str) -> bool:
    """Reprocess a document with a specific plugin."""
    plugin_info = registry.get_plugin_info(plugin_name)
    if not plugin_info:
        return False
    
    # Create job for this plugin
    job_type = plugin_info['job_type']
    self.create_job(document_id, job_type, priority=100)
    return True
```

### Priority 3: Schema Redesign for Multi-Producer (High Complexity)

For full multi-plugin support, consider:

1. Convert `photo_metadata` from single-row to multi-row with `plugin_name` PK
2. Convert `document_embeddings` to allow multiple embeddings per document
3. Create `document_thumbnails` child table
4. Update all query patterns to handle multiple results
5. Implement staleness/cleanup policies

---

## Conclusion

The Librarian architecture has a solid foundation for plugins with:
- ✅ Independent job execution
- ✅ Failure isolation  
- ✅ Enable/disable controls
- ✅ Basic provenance for entities

However, it is **not fully prepared** for multiple independent plugins operating on the same artifact due to:
- ❌ UNIQUE constraints preventing multi-producer metadata
- ❌ Missing plugin namespacing
- ❌ Inconsistent provenance tracking
- ❌ Limited reprocessing capabilities

Full multi-plugin support would require significant schema evolution but the job queue and worker infrastructure is already capable of handling multiple concurrent plugins.