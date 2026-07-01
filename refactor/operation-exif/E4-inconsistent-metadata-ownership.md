# E4: Inconsistent Metadata Ownership

**Status:** Open  
**Severity:** High  
**Classification:** Architectural Violation

## Problem Statement

Metadata ownership is unclear and inconsistent across the system. Different components own different metadata:

| Metadata | Owner | Storage |
|----------|-------|---------|
| path, extension | CollectionWatcher | documents table |
| mime_type | Parser | NOT PERSISTED (E1) |
| file_size | CollectionWatcher | documents table |
| text content | Parser → ContentExtractor | document_content table |
| EXIF/GPS | Parser → PhotoMetadataExtractor | photo_metadata table |
| entities | EntityExtractor | entities table |
| locations | LocationExtractor | locations table |
| embeddings | EmbeddingGenerator | document_embeddings table |

**Problem:** `structured_data` (produced by parser) owns metadata but is dropped.

## Impact

- **User Impact:** Some metadata appears in some contexts but not others
- **Developer Impact:** Unclear ownership leads to bugs
- **Data Impact:** Data loss from inconsistent handling

## Affected Files

| File | Issue |
|------|-------|
| `parsers/*.py` | Own metadata, but don't persist |
| `ingestion/collection_watcher.py` | Doesn't know what parsers produce |
| `workers/*.py` | Re-extract what parsers already did |
| `storage/postgres_backend.py` | No clear ownership model |

## Metadata Ownership Matrix

```
                    Parser    CollectionWatcher    Worker    Backend
path                 ✓            ✓               -          ✓
extension            ✓            ✓               -          ✓
mime_type            ✓            -               -          -
file_size            -            ✓               -          ✓
text                 ✓            -               ✓          ✓
structured_data      ✓            -               -          -
dimensions           ✓            -               ✓          (photo_metadata)
EXIF                 ✓            -               ✓          ✓
GPS                  ✓            -               ✓          (photo_metadata)
entities             ✓            -               ✓          ✓
locations            -            -               ✓          ✓
embeddings           -            -               ✓          ✓
```

✓ = produces / owns, - = doesn't handle

## Required Changes

### 1. Document Metadata Ownership

Create explicit ownership policy:

```
Discovery Phase:
  - CollectionWatcher owns: path, extension, file_size, modified_time
  - Parser owns: mime_type, text, structured_data

Enrichment Phase:
  - Workers own: extracted metadata
  - Backend owns: persistence

Parser owns:
  - MIME type
  - Dimensions
  - File format
  - Raw metadata (structured_data)

Worker owns:
  - EXIF (photo_metadata_extractor)
  - Entities (entity_extractor)
  - Locations (location_extractor)
  - Embeddings (embedding_generator)
```

### 2. Clear Parser → Worker Handoff

```python
# Current: Parser produces structured_data, Worker re-extracts
# Proposed: Clear contract for what Worker receives

class MetadataContract:
    """What parsers must provide vs what workers extract."""
    
    # Parser responsibilities
    PARSER_OWNED = ['mime_type', 'dimensions', 'format']
    
    # Worker responsibilities (may re-extract)
    WORKER_OWNED = ['exif', 'entities', 'locations', 'embeddings']
```

### 3. Structured Data Handling

**Option A:** Parser → Backend (direct)
**Option B:** Parser → Worker → Backend
**Option C:** Parser → CollectionWatcher → Backend

Current code uses Option B but with data loss.

## Definition of Done

- [ ] Ownership policy documented
- [ ] Parser ownership clear
- [ ] Worker ownership clear
- [ ] Data flow between phases clear
- [ ] No metadata dropped

## Dependencies

- E1 (mime_type)
- E2 (structured_data)
- E3 (GPS to locations)

## Risk Assessment

- **Medium Risk:** Policy documentation vs code changes
- **Impact:** Prevents future ownership confusion
- **Testing:** Code review

## Effort Estimate

- **Time:** 2-3 hours (documentation)
- **Complexity:** Low
- **Testing:** N/A (documentation only)
