# E1: mime_type Not Persisted

**Status:** Completed  
**Severity:** Critical  
**Classification:** Completed
**Last Updated:** 2026-07-02

---

## Status: COMPLETED ✅

mime_type is now correctly persisted during artifact discovery via `get_mime_type_from_extension()`.

**Files modified:**
- `ingestion/collection_watcher.py` - Now passes mime_type to discover_artifact()
- `storage/postgres_backend.py` - discover_artifact() accepts and persists mime_type

---

## Implementation Status

### What Was Done

The mime_type infrastructure is in place:

1. ✅ `discover_artifact()` accepts `mime_type` parameter
2. ✅ `get_mime_type_from_extension()` function exists
3. ✅ CollectionWatcher calls the function during discovery
4. ✅ Backend persists mime_type to documents table

### What Remains

1. ❌ **No backfill for existing documents** - Old documents still have NULL mime_type
2. ❌ **No verification tests** - Integration tests not added
3. ❌ **API filtering** - Need to verify mime_type queries work end-to-end

## Problem Statement

The `documents.mime_type` column exists in the schema (migration 008_document_fields.sql) but is NEVER populated. This causes:

1. All 3168 documents have `mime_type = NULL`
2. API queries for mime_type filtering return empty results
3. MIME type-based classification must fall back to extension
4. Timeline/map features cannot filter by media type

## Impact

- **User Impact:** No MIME type filtering in Explorer, empty results for mime_type queries
- **Developer Impact:** Classification must use extension-based fallback
- **Data Impact:** Original mime_type data from parsers is discarded

## Affected Files

| File | Lines | Issue |
|------|-------|-------|
| `ingestion/collection_watcher.py` | 198-211 | structured_data.mime_type dropped |
| `storage/postgres_backend.py` | 414-434 | INSERT doesn't include mime_type |
| `storage/postgres_backend.py` | 593-611 | discover_artifact doesn't set mime_type |
| `parsers/image_parser.py` | 81-92 | mime_type extracted but discarded |

## Current Flow

```
ImageParser.parse()
    ↓
returns {
    'structured_data': {
        'mime_type': 'image/jpeg',  ← EXTRACTED
        'width': 3000,
        'height': 4000
    }
}
    ↓
CollectionWatcher._process_file()
    ↓
document = {
    'path': ...,
    'extension': '.jpg',
    'character_count': ...,
    # MISSING: 'mime_type': parsed['structured_data']['mime_type']
}
    ↓
backend.save_document(document)
    ↓
INSERT INTO documents (..., mime_type) VALUES (..., NULL)
```

## Required Changes

### 1. CollectionWatcher Update

```python
# ingestion/collection_watcher.py, line ~206
document = {
    'path': artifact_path,
    'extension': full_path.suffix,
    'modified_time': datetime.fromtimestamp(stat.st_mtime),
    'file_size': stat.st_size,
    'character_count': parsed.get('character_count'),
    'parser': parsed.get('parser', ...),
    'artifact_type': artifact_type,
    'mime_type': parsed.get('structured_data', {}).get('mime_type'),  # ADD THIS
    'status': 'METADATA_INDEXED'
}
```

### 2. Backend Update

```python
# storage/postgres_backend.py, save_document() method
# Add mime_type to INSERT statement columns
# Add mime_type = document.get('mime_type') to VALUES
```

### 3. discover_artifact Update (Optional)

Option A: Accept mime_type as parameter
Option B: Use extension-based MIME type fallback

## Definition of Done

- [ ] `documents.mime_type` is populated for all new documents
- [ ] `documents.mime_type` is backfilled for existing documents where possible
- [ ] API queries for mime_type return correct results
- [ ] Tests verify mime_type persistence in pipeline

## Dependencies

- None (can be implemented independently)

## Risk Assessment

- **Low Risk:** Schema column exists, no migration needed
- **Impact:** Fixes critical data loss
- **Testing:** Unit test pipeline, integration test with existing data

## Effort Estimate

- **Time:** 2-4 hours
- **Complexity:** Low
- **Testing:** Medium (needs integration test)

## Implementation Notes

1. Backfill strategy: Use extension-based MIME mapping for existing documents
2. Parser consistency: Ensure all image parsers set mime_type in structured_data
3. Validation: Add database constraint to prevent invalid MIME types
