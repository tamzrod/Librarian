# E2: structured_data Dropped in Pipeline

**Status:** Open  
**Severity:** Critical  
**Classification:** Open

## Problem Statement

The `structured_data` blob produced by all parsers is **completely dropped** in the ingestion pipeline. This data contains:

1. **Image Parser:**
   - `mime_type` (also in documents.mime_type, but we lose the rest)
   - `width`, `height`, `aspect_ratio`

2. **Structured Data Parsers (JSON, YAML, CSV, XML, etc.):**
   - Full structured data (entities, relationships)
   - This data is NOT re-extracted by entity_extractor

3. **Event/Location Context:**
   - Timestamps from file metadata
   - GPS coordinates (if not in EXIF)
   - Custom metadata fields

## Impact

- **User Impact:** Parser-specific metadata not available for filtering/display
- **Developer Impact:** Entity extraction must re-parse structured data files
- **Data Impact:** Permanent data loss - original structured data unavailable

## Affected Files

| File | Issue |
|------|-------|
| `ingestion/collection_watcher.py` | structured_data not extracted |
| `storage/postgres_backend.py` | No column to store structured_data |
| `parsers/*.py` | All produce structured_data |
| `extractors/entity_extractor.py` | Re-extracts from structured_data files |

## Current Flow

```
Parser.parse()
    ↓
{
    'text': '...',
    'structured_data': {
        'mime_type': '...',
        'entities': [...],      ← LOST
        'relationships': [...], ← LOST
        'width': ...,           ← LOST (for images)
        'custom_fields': {...} ← LOST
    },
    'character_count': ...
}
    ↓
CollectionWatcher._process_file()
    ↓
document = {
    'path': ...,
    'text': parsed['text'],
    'character_count': parsed['character_count'],
    # MISSING: structured_data
}
    ↓
backend.save_document(document)
    ↓
structured_data NOT PERSISTED
```

## Options

### Option A: Add structured_data Column

Add JSONB column to documents table:

```sql
ALTER TABLE documents ADD COLUMN IF NOT EXISTS structured_data JSONB;
```

**Pros:**
- Preserves all parser output
- Future-proof for new metadata types
- No re-parsing needed

**Cons:**
- Schema change required
- Data duplication
- Storage overhead

### Option B: Extract Key Fields to Existing Tables

Extract specific fields to appropriate tables:
- `mime_type` → `documents.mime_type` (E1)
- `width/height` → `photo_metadata` (when available)
- `entities` → `entities` table (already done)
- `relationships` → `relationships` table (already done)

**Pros:**
- No new columns
- Normalized storage
- Already done for entities

**Cons:**
- Incomplete - loses custom fields
- Parser changes require schema updates

### Option C: Keep as-is, Document Limitation

Acknowledge that structured_data is parser output only.

**Pros:**
- No code changes
- Clear architectural boundary

**Cons:**
- Data loss
- Inconsistent with "discovery before understanding" philosophy

## Recommended Approach

**Option B with Option A for images**

1. Implement E1 (mime_type)
2. For images: Extract dimensions to `photo_metadata` during `extract_photo_metadata`
3. For structured files: Document that entities are re-extracted
4. Future: Consider JSONB column for custom metadata

## Definition of Done

- [ ] Decision made on approach (A, B, or C)
- [ ] E1 implemented (mime_type)
- [ ] Image dimensions persisted to photo_metadata
- [ ] Structured data parsers documented
- [ ] No data loss for image metadata

## Dependencies

- **Hard:** E1 (mime_type)
- **Soft:** E5 (thumbnail persistence)

## Risk Assessment

- **Medium Risk:** Schema change if Option A chosen
- **Impact:** Prevents permanent data loss
- **Testing:** Test each parser's structured_data is handled

## Effort Estimate

- **Time:** 4-8 hours (depending on approach)
- **Complexity:** Medium
- **Testing:** High (need to test each parser)
