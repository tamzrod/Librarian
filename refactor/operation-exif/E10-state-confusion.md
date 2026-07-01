# E10: Discovery vs Enrichment State Confusion

**Status:** Completed  
**Severity:** Low  
**Classification:** Technical Debt  
**Completed:** 2026-07-01

---

## Executive Summary

This document clarifies the distinction between **Discovery metadata** (filesystem-derived) and **Enrichment metadata** (worker-derived). It establishes a clear state matrix separating these two phases of the document lifecycle.

---

## Problem Statement

### Original Issue

The document lifecycle states were not clearly aligned with the artifact inventory model. Discovery and enrichment states were mixed together, making it unclear:

1. Which states are filesystem-derived vs worker-derived
2. Which states are rebuildable vs transient
3. Which states can transition in which directions

### Current States (Before Clarification)

```
DISCOVERED → METADATA_INDEXED → CONTENT_EXTRACTED → ENTITY_EXTRACTED 
→ RELATIONSHIPS_BUILT → EMBEDDED → COMPLETE
```

### Problems Identified

| Problem | Description |
|---------|-------------|
| **DISCOVERED ambiguity** | Used for both newly discovered artifacts AND artifacts without parsers |
| **METADATA_INDEXED confusion** | Applied after parsing, but may contain no actual metadata indexing |
| **State ownership unclear** | Which states are Discovery vs Enrichment was not documented |
| **Rebuildability undefined** | Which states survive a database rebuild was not defined |

---

## State Matrix: Discovery vs Enrichment

This matrix clarifies which states belong to which phase and their rebuildability.

### State Classification

| State | Discovery | Enrichment | Phase Source | Rebuildable | Notes |
|-------|-----------|-----------|--------------|-------------|-------|
| `DISCOVERED` | ✓ | - | Filesystem | ✓ | Minimal record: path, extension, file_size, mime_type |
| `METADATA_INDEXED` | ✓ | partial | Parser | ✓ | Parser ran, basic metadata extracted (character_count, parser name) |
| `CONTENT_EXTRACTED` | - | ✓ | Worker | ✗ | Text content extracted from document |
| `ENTITY_EXTRACTED` | - | ✓ | Worker | ✗ | Entities identified from content |
| `RELATIONSHIPS_BUILT` | - | ✓ | Worker | ✗ | Relationships mapped between entities |
| `EMBEDDED` | - | ✓ | Worker | ✗ | Vector embeddings generated |
| `COMPLETE` | ✓ | ✓ | System | ✓ | All enrichment jobs completed |
| `FAILED` | - | ✓ | System | - | Processing failed (retryable) |

### Legend

| Symbol | Meaning |
|--------|---------|
| ✓ | Belongs to this phase |
| - | Not applicable to this phase |
| partial | Belongs to phase but completion varies |
| rebuildable | Survives database deletion + rebuild |
| ✗ | Requires workers to regenerate |

---

## Phase Diagrams

### Discovery Phase

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DISCOVERY PHASE                                    │
│                   (Filesystem-derived, Rebuildable)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  filesystem                                                                  │
│      │                                                                        │
│      ▼                                                                        │
│  artifact discovered                                                         │
│      │                                                                        │
│      ├─► No parser? ─────────────────────────────────────────────────────    │
│      │    │                                                                  │
│      │    ▼                                                                  │
│      │    DISCOVERED (terminal for unknown artifacts)                         │
│      │    └─► Artifacts without parsers remain in DISCOVERED state          │
│      │        They are inventoried but not enriched                         │
│      │                                                                  │
│      ▼                                                                        │
│  inventory record created                                                    │
│      │                                                                        │
│      ▼                                                                        │
│  Explorer usable                                                             │
│      │                                                                        │
│      └─► DISCOVERED: path, extension, file_size, mime_type available        │
│          METADATA_INDEXED: character_count, parser, artifact_type added     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Enrichment Phase

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENRICHMENT PHASE                                   │
│                     (Worker-derived, Non-rebuildable)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  inventory exists                                                           │
│      │                                                                        │
│      ▼                                                                        │
│  jobs created                                                               │
│      │                                                                        │
│      ├─► JobType.EXTRACT_TEXT (text documents only)                         │
│      ├─► JobType.EXTRACT_ENTITIES                                           │
│      ├─► JobType.EXTRACT_EVENTS                                             │
│      ├─► JobType.EXTRACT_LOCATIONS                                          │
│      ├─► JobType.GENERATE_EMBEDDINGS                                        │
│      └─► JobType.EXTRACT_PHOTO_METADATA (images only)                       │
│                                                                              │
│      ▼                                                                        │
│  worker processing                                                          │
│      │                                                                        │
│      ├─► Worker claims job (status: IN_PROGRESS)                            │
│      ├─► Worker processes (may take time)                                   │
│      └─► Worker completes (status: COMPLETED) or fails (status: FAILED)     │
│                                                                              │
│      ▼                                                                        │
│  metadata persisted                                                         │
│      │                                                                        │
│      ├─► content: text content in document_content                          │
│      ├─► entities: in entities table                                        │
│      ├─► locations: in locations table                                     │
│      ├─► embeddings: in document_embeddings                                 │
│      └─► photo_metadata: in photo_metadata                                  │
│                                                                              │
│      ▼                                                                        │
│  UI updated                                                                 │
│      │                                                                        │
│      └─► Document status transitions to next state                          │
│          DISCOVERED → METADATA_INDEXED → CONTENT_EXTRACTED → ... → COMPLETE │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## State Transitions

### Allowed Transitions

```
┌────────────────────┬─────────────────────────────────────────────────────────┐
│ From State         │ Allowed Transitions                                      │
├────────────────────┼─────────────────────────────────────────────────────────┤
│ DISCOVERED         │ → METADATA_INDEXED, → FAILED                            │
│ METADATA_INDEXED   │ → CONTENT_EXTRACTED, → FAILED                           │
│ CONTENT_EXTRACTED  │ → ENTITY_EXTRACTED, → FAILED                            │
│ ENTITY_EXTRACTED  │ → RELATIONSHIPS_BUILT, → FAILED                          │
│ RELATIONSHIPS_BUILT│ → EMBEDDED, → FAILED                                     │
│ EMBEDDED           │ → COMPLETE, → FAILED                                     │
│ COMPLETE           │ → FAILED (can fail after completion)                     │
│ FAILED             │ → METADATA_INDEXED (retry path)                          │
└────────────────────┴─────────────────────────────────────────────────────────┘
```

### Invalid Transitions

| From | To | Reason |
|------|-----|--------|
| DISCOVERED | COMPLETE | Must go through full enrichment pipeline |
| DISCOVERED | EMBEDDED | Must go through enrichment pipeline |
| FAILED | COMPLETE | Only retry path allowed (→ METADATA_INDEXED) |
| COMPLETE | CONTENT_EXTRACTED | No backwards transitions |
| COMPLETE | DISCOVERED | No backwards transitions |
| FAILED | ENTITY_EXTRACTED | Must restart from METADATA_INDEXED |

### Code Reference

```python
# storage/postgres_backend.py
VALID_TRANSITIONS = {
    DocumentStatus.DISCOVERED: {DocumentStatus.METADATA_INDEXED, DocumentStatus.FAILED},
    DocumentStatus.METADATA_INDEXED: {DocumentStatus.CONTENT_EXTRACTED, DocumentStatus.FAILED},
    DocumentStatus.CONTENT_EXTRACTED: {DocumentStatus.ENTITY_EXTRACTED, DocumentStatus.FAILED},
    DocumentStatus.ENTITY_EXTRACTED: {DocumentStatus.RELATIONSHIPS_BUILT, DocumentStatus.FAILED},
    DocumentStatus.RELATIONSHIPS_BUILT: {DocumentStatus.EMBEDDED, DocumentStatus.FAILED},
    DocumentStatus.EMBEDDED: {DocumentStatus.COMPLETE, DocumentStatus.FAILED},
    DocumentStatus.COMPLETE: {DocumentStatus.FAILED},  # Can fail after completion
    DocumentStatus.FAILED: {DocumentStatus.METADATA_INDEXED},  # Retry path
}
```

---

## Rebuild Behavior

### What Survives Database Rebuild

When the database is deleted and rebuilt:

| Phase | Data | Survives Rebuild? | Notes |
|-------|------|-------------------|-------|
| **Discovery** | path | ✓ | From filesystem scan |
| | extension | ✓ | From filesystem |
| | file_size | ✓ | From filesystem |
| | mime_type | ✓ | From extension mapping |
| | status (DISCOVERED) | ✓ | Default state |
| **Discovery** | character_count | ✓ | From parser (if available) |
| | artifact_type | ✓ | From parser registry |
| | parser name | ✓ | From parser |
| **Enrichment** | text content | ✗ | Requires workers to regenerate |
| | entities | ✗ | Requires workers to regenerate |
| | locations | ✗ | Requires workers to regenerate |
| | embeddings | ✗ | Requires workers to regenerate |
| | photo_metadata | ✗ | Requires workers to regenerate |

### Rebuild Process

```
delete database
    │
    ▼
inventory rebuild (CollectionWatcher re-scans filesystem)
    │
    ▼
artifacts re-discovered (status: DISCOVERED)
    │
    ▼
parsers re-run (status: METADATA_INDEXED)
    │
    ▼
workers replay (jobs re-created)
    │
    ▼
state restoration (enrichment re-applied)
```

### Worker Replay

When workers replay after a database rebuild:

```python
# Workers process jobs in dependency order:
# 1. EXTRACT_TEXT → must complete first (prerequisite for entities, events, locations)
# 2. EXTRACT_ENTITIES, EXTRACT_EVENTS, EXTRACT_LOCATIONS → parallel (depend on text)
# 3. GENERATE_EMBEDDINGS → depends on text
# 4. EXTRACT_PHOTO_METADATA → for images only (independent)

JOB_DEPENDENCIES = {
    'extract_entities': {'extract_text'},
    'extract_locations': {'extract_text'},
    'generate_embeddings': {'extract_text'},
    # extract_text has no dependencies
    # extract_events depends on text (implicit through extract_entities)
}
```

---

## Failure Recovery

### Failure States

| State | Meaning | Retryable? | Recovery Action |
|-------|---------|------------|----------------|
| `FAILED` | Job failed during processing | ✓ | Automatic retry via job queue |
| `FAILED_PERMANENT` | Job failed after max retries | ✗ | Manual intervention required |
| `CANCELLED` | Job cancelled by admin | ✗ | Re-queue manually |

### Retry Configuration

```python
MAX_RETRIES = 5
RETRY_DELAYS = {
    1: timedelta(seconds=0),      # Immediate
    2: timedelta(minutes=1),
    3: timedelta(minutes=5),
    4: timedelta(minutes=30),
    5: timedelta(hours=2),
}
```

### Recovery Flow

```
Job fails
    │
    ▼
Check attempt_count < MAX_RETRIES?
    │
    ├─► YES: Schedule retry with backoff delay
    │    │
    │    ▼
    │    Job returns to QUEUED status
    │    │
    │    ▼
    │    Worker re-claims job
    │
    └─► NO: Mark as FAILED_PERMANENT
         │
         ▼
         Alert admin (if alerts configured)
         │
         ▼
         Manual intervention required
```

### Document-level Failure Recovery

If a document fails at any enrichment stage:

```python
# Document can retry from METADATA_INDEXED
# This ensures deterministic state restoration
DocumentStatus.FAILED: {DocumentStatus.METADATA_INDEXED}
```

---

## Metadata Ownership

### Discovery Metadata (owned by CollectionWatcher)

| Field | Source | Persistence | Rebuildable |
|-------|--------|-------------|-------------|
| path | Filesystem | ✓ | ✓ |
| extension | Filesystem | ✓ | ✓ |
| file_size | Filesystem | ✓ | ✓ |
| modified_time | Filesystem | ✓ | ✓ |
| mime_type | Extension mapping | ✓ | ✓ |
| character_count | Parser | ✓ | ✓ |
| parser | Parser | ✓ | ✓ |
| artifact_type | Parser registry | ✓ | ✓ |

### Enrichment Metadata (owned by Workers)

| Field | Source | Persistence | Rebuildable |
|-------|--------|-------------|-------------|
| content | ContentExtractor | ✓ | ✗ |
| entities | EntityExtractor | ✓ | ✗ |
| events | EventExtractor | ✓ | ✗ |
| locations | LocationExtractor | ✓ | ✗ |
| embeddings | EmbeddingGenerator | ✓ | ✗ |
| photo_metadata | PhotoMetadataExtractor | ✓ | ✗ |

---

## State Machine Code Reference

### State Constants

```python
# storage/postgres_backend.py
class DocumentStatus:
    DISCOVERED = 'DISCOVERED'
    METADATA_INDEXED = 'METADATA_INDEXED'
    CONTENT_EXTRACTED = 'CONTENT_EXTRACTED'
    ENTITY_EXTRACTED = 'ENTITY_EXTRACTED'
    RELATIONSHIPS_BUILT = 'RELATIONSHIPS_BUILT'
    EMBEDDED = 'EMBEDDED'
    COMPLETE = 'COMPLETE'
    FAILED = 'FAILED'
```

### CollectionWatcher Behavior

```python
# ingestion/collection_watcher.py

# Step 1: Discover artifact immediately (no parser required)
# Status: DISCOVERED
doc_id = backend.discover_artifact(
    path=artifact_path,
    extension=full_path.suffix,
    file_size=stat.st_size,
    modified_time=datetime.fromtimestamp(stat.st_mtime),
    mime_type=mime_type
)

# Step 2: If parser exists, enrich artifact
# Status: METADATA_INDEXED
if parser:
    parsed = parser.parse(full_path)
    document = {
        'status': 'METADATA_INDEXED',
        'character_count': parsed.get('character_count'),
        'parser': parsed.get('parser'),
        'artifact_type': artifact_type,
    }
    backend.save_document(document)
    
    # Create enrichment jobs
    job_ids = backend.create_jobs_for_document(doc_id)
```

---

## Verification Queries

### Check State Distribution

```sql
SELECT status, COUNT(*) as count
FROM documents
GROUP BY status
ORDER BY count DESC;
```

### Check Discovery Phase Completeness

```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN mime_type IS NOT NULL THEN 1 ELSE 0 END) as with_mime,
    SUM(CASE WHEN artifact_type != 'unknown' THEN 1 ELSE 0 END) as classified
FROM documents;
```

### Check Enrichment Progress

```sql
SELECT 
    d.id, d.path, d.status,
    COUNT(j.id) FILTER (WHERE j.status = 'COMPLETED') as completed_jobs,
    COUNT(j.id) FILTER (WHERE j.status = 'QUEUED') as queued_jobs,
    COUNT(j.id) FILTER (WHERE j.status = 'FAILED') as failed_jobs
FROM documents d
LEFT JOIN document_jobs j ON d.id = j.document_id
GROUP BY d.id, d.path, d.status
ORDER BY d.status;
```

### Check Rebuildable vs Non-rebuildable Data

```sql
-- Discovery metadata (should be 100%)
SELECT 
    COUNT(*) FILTER (WHERE path IS NOT NULL) as has_path,
    COUNT(*) FILTER (WHERE extension IS NOT NULL) as has_extension,
    COUNT(*) FILTER (WHERE mime_type IS NOT NULL) as has_mime
FROM documents;

-- Enrichment metadata (depends on worker completion)
SELECT 
    COUNT(DISTINCT d.id) as total_docs,
    COUNT(DISTINCT dc.id) as with_content,
    COUNT(DISTINCT e.id) as with_entities,
    COUNT(DISTINCT l.id) as with_locations,
    COUNT(DISTINCT de.id) as with_embeddings,
    COUNT(DISTINCT pm.id) as with_photo_meta
FROM documents d
LEFT JOIN document_content dc ON d.id = dc.document_id
LEFT JOIN entities e ON d.id = e.document_id
LEFT JOIN locations l ON d.id = l.document_id
LEFT JOIN document_embeddings de ON d.id = de.document_id
LEFT JOIN photo_metadata pm ON d.id = pm.document_id;
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Discovery Phase** | The process of detecting artifacts on the filesystem and creating inventory records |
| **Enrichment Phase** | The process of extracting semantic information from artifacts using workers |
| **Discovery Metadata** | Metadata derived from filesystem inspection (path, size, mime_type) |
| **Enrichment Metadata** | Metadata derived from worker processing (content, entities, embeddings) |
| **Rebuildable** | Data that survives database deletion and recreation |
| **Non-rebuildable** | Data that requires workers to regenerate after rebuild |
| **State Machine** | The defined set of valid states and transitions for documents |
| **Job Dependencies** | The prerequisite relationships between different job types |

---

## Summary

| Aspect | Discovery | Enrichment |
|--------|-----------|------------|
| **Trigger** | Filesystem change | Job queue |
| **Owner** | CollectionWatcher | Workers |
| **States** | DISCOVERED, METADATA_INDEXED | CONTENT_EXTRACTED, ENTITY_EXTRACTED, etc. |
| **Rebuildable** | ✓ Yes | ✗ No |
| **Final State** | METADATA_INDEXED (if no parser) | COMPLETE (if all jobs succeed) |

---

## Definition of Done

- [x] States documented
- [x] State transitions clear
- [x] Discovery vs Enrichment phases separated
- [x] State matrix created
- [x] Allowed/invalid transitions documented
- [x] Rebuild behavior documented
- [x] Failure recovery documented
- [x] Metadata ownership clarified
