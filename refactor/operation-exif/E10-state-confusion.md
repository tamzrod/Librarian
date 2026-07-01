# E10: Discovery vs Enrichment State Confusion

**Status:** Open  
**Severity:** Low  
**Classification:** Technical Debt

## Problem Statement

The document lifecycle states are not clearly aligned with the artifact inventory model:

### Current States

```
DISCOVERED → METADATA_INDEXED → CONTENT_EXTRACTED → ENTITY_EXTRACTED 
→ RELATIONSHIPS_BUILT → EMBEDDED → COMPLETE
```

### Problems

1. **DISCOVERED state:** Not just discovered - is also the state for artifacts without parsers
2. **METADATA_INDEXED state:** Applied to artifacts parsed by CollectionWatcher but no actual metadata indexing occurs
3. **State confusion:** When `discover_artifact()` is called, is the artifact DISCOVERED or METADATA_INDEXED?

## Current Code

```python
# ingestion/collection_watcher.py
# Line 172: status = 'DISCOVERED'
doc_id = backend.save_document({
    'status': 'DISCOVERED'
})

# But then at line 206:
# status = 'METADATA_INDEXED'
doc_id = backend.save_document({
    'status': 'METADATA_INDEXED'
})
```

```python
# storage/postgres_backend.py, discover_artifact()
# Line 590: Always DISCOVERED
status = 'DISCOVERED'
```

## Impact

- **User Impact:** Unclear what states mean
- **Developer Impact:** State transitions confusing
- **Data Impact:** Inconsistent state usage

## Affected Files

| File | Issue |
|------|-------|
| `storage/postgres_backend.py` | State definitions |
| `ingestion/collection_watcher.py` | Inconsistent state setting |
| `workers/*.py` | State transition methods |

## Required Changes

### 1. Clarify States

```
DISCOVERED: File detected, record created, minimal metadata only
METADATA_INDEXED: Parser ran, basic metadata extracted
CONTENT_EXTRACTED: Text content available
ENTITY_EXTRACTED: Entities identified
RELATIONSHIPS_BUILT: Relationships mapped
EMBEDDED: Vector embeddings generated
COMPLETE: All processing finished
```

### 2. Align with Artifact Inventory

```
Discovery Phase:
  - DISCOVERED: Minimal metadata (path, extension, file_size)
  - No parser required

Enrichment Phase:
  - METADATA_INDEXED: Parser ran successfully
  - CONTENT_EXTRACTED: Text extracted
  - etc.
```

### 3. Documentation

Add state transition diagram to codebase:

```python
"""
Document Lifecycle States:
=========================

DISCOVERED → File exists in filesystem, record created
    │
    ├─ No parser → remains DISCOVERED
    │
    └─ Parser exists → METADATA_INDEXED

METADATA_INDEXED → Parser ran, metadata extracted
    │
    └─ CONTENT_EXTRACTED (text extracted)

... etc ...
"""
```

## Definition of Done

- [ ] States documented
- [ ] State transitions clear
- [ ] CollectionWatcher consistent
- [ ] discover_artifact vs save_document clear

## Dependencies

- None

## Risk Assessment

- **Low Risk:** Documentation and minor refactor
- **Impact:** Developer clarity
- **Testing:** Code review

## Effort Estimate

- **Time:** 2-3 hours
- **Complexity:** Low
- **Testing:** N/A (documentation)
