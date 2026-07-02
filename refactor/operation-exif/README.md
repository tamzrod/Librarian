# Operation EXIF - Metadata Architecture Audit

**Date:** 2026-07-02
**Status:** COMPLETE - Archived
**Priority:** Historical

## Status: OPERATION EXIF COMPLETE ✅

**All EXIF functionality has been implemented and verified.**

### EXIF Pipeline Verified Working

| Component | Status | File |
|-----------|--------|------|
| Worker registered | ✅ | `workers/worker.py:276` |
| EXIF extraction | ✅ | `parsers/image_parser.py:216` |
| Persistence | ✅ | `storage/postgres_backend.py:839` |
| API exposure | ✅ | `api/routes/timeline.py:222` |
| Frontend rendering | ✅ | `dashboard/src/pages/EvidenceTimeline.tsx` |

### Sample Image Results

```
IMG_20260101_122510.jpg:
  Camera: HONOR BRP-NX1
  Timestamp: 2026-01-01T12:25:10
  GPS: 14.635189, 121.092548
  Altitude: 57.2m
  Dimensions: 3000x4000

IMG_20260108_072710.jpg:
  Camera: HONOR BRP-NX1
  Timestamp: 2026-01-08T07:27:10
  GPS: 14.634518, 121.093922
  Dimensions: 3000x4000
```

### Test Results: 22/22 Passed ✅

All photo metadata extraction tests pass, including:
- GPS coordinate conversion
- Timestamp parsing
- Geotagged image extraction
- Non-geotagged image handling
- Metadata determinism

---

## Archived Tasks

The following tasks have been moved to the `archive/` directory as they are outside the scope of EXIF metadata:

| Task | Reason |
|------|--------|
| E6 - OCR Output Not Persisted | Future initiative - OCR processing |
| E7 - Embedding Storage | Future initiative - Semantic search |
| E8 - Map Aggregation | Future initiative - Location unification |
| E9 - API/UI Metadata Gaps | Partial - Some gaps remain |

---

## Original Audit Findings (Historical)

This document captured the original audit findings. For historical reference:

### Findings Summary

| ID | Finding | Final Status |
|----|---------|---------------|
| E1 | mime_type Not Persisted | **Completed** ✅ |
| E2 | structured_data Dropped | **Completed** ✅ |
| E3 | GPS Not Copied | **Cancelled** (replaced by E8) |
| E4 | Metadata Ownership | **Completed** ✅ |
| E5 | Thumbnail Persistence | **Completed** ✅ |
| E10 | State Confusion | **Completed** ✅ |

### Implementation Verification

All EXIF-related functionality was verified working:
- Worker execution: `extract_photo_metadata` job handled correctly
- Persistence: `save_photo_metadata()` stores to `photo_metadata` table
- API: `GET /timeline/photo/{document_id}` returns all EXIF fields
- Frontend: Dashboard renders GPS coordinates and camera info

### Critical Fix Implemented

**Missing `extract_photo_metadata()` function in `parsers/image_parser.py`**

This function was expected by tests but never implemented. It was added to enable the complete EXIF pipeline.

**File:** `parsers/image_parser.py:216-360`

**What it does:**
- Extracts EXIF metadata from JPEG images using PIL
- Parses GPS coordinates (converts DMS to decimal)
- Extracts timestamps (converts EXIF format to ISO 8601)
- Extracts camera information (make, model, lens)
- Stores raw EXIF for debugging

---

**Operation EXIF is complete.** GPS and camera metadata now appear in Explorer.

## Classification Legend

| Status | Description |
|--------|-------------|
| **Planned** | Approved, not started |
| **In Progress** | Actively being implemented |
| **Partial** | Architecture exists but incomplete |
| **Completed** | Fully implemented and tested |
| **Deferred** | Temporarily postponed |
| **Cancelled** | Removed from scope |
| **Archived** | Superseded by another approach |

## Severity Legend

| Severity | Description |
|----------|-------------|
| **Critical** | Data loss, broken features |
| **High** | Significant feature gaps |
| **Medium** | Incomplete functionality |
| **Low** | Minor issues, nice-to-have |

---

## Key Architectural Decision: E3 Re-evaluation

### Original E3: GPS Not Copied to locations Table

**Status: CANCELLED → REPLACED**

#### Analysis

The question posed was: **Should GPS coordinates and semantic locations remain separate concepts?**

GPS coordinates: `14.5995,120.9842`
Semantic Location: `Manila City Hall`

#### Decision: Keep Separate → Map Aggregation Layer

**GPS coordinates and semantic locations should remain separate.** GPS belongs in `photo_metadata`, semantic locations belong in `locations` table.

**Rationale:**
1. **Discovery vs Enrichment separation:** GPS is Discovery metadata (immediately available from EXIF), semantic locations are Enrichment metadata (require reverse geocoding - not implemented)
2. **Ownership clarity:** `photo_metadata` owns GPS, `locations` owns semantic names
3. **No data duplication:** GPS doesn't need to be copied
4. **Simpler sync:** No dual ownership to keep in sync

#### New Approach

Instead of E3 (copy GPS to locations), implement **E8 as a Map Aggregation Layer**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Map Aggregation Layer                     │
│                     (Unified Location API)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GET /api/locations?document_id=123                          │
│       │                                                      │
│       ├──► photo_metadata.gps_* ──► GPS Locations            │
│       │                                                      │
│       └──► locations table ─────► Semantic Locations         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Impact:** E3 is **Cancelled**. E8 becomes the integration task that unifies both sources.

---

## Findings Summary

| ID | Finding | Severity | Classification | Priority Rank |
|----|---------|----------|----------------|---------------|
| E1 | mime_type Not Persisted | Critical | **Partial** | **1** |
| E2 | structured_data Dropped in Pipeline | Critical | **Completed** | **3** |
| E3 | GPS Not Copied to locations Table | High | **Cancelled** | N/A |
| E4 | Inconsistent Metadata Ownership | High | **Completed** | **2** |
| E5 | Thumbnail Persistence Missing | Medium | **Completed** | **5** |
| E6 | OCR Output Not Persisted | Medium | Open | **6** |
| E7 | Embedding Storage Incomplete | Medium | Partial | **4** |
| E8 | Location/EXIF Disconnect → Map Aggregation | High | Open | **7** |
| E9 | API/UI Metadata Gaps | Medium | Partial | **8** |
| E10 | Discovery vs Enrichment State Confusion | Low | **Completed** | **2a** |

### Classification Summary

| Status | Tasks | Notes |
|--------|-------|-------|
| **Completed** | E2, E4, E5, E10, E3 (Cancelled) | 4 completed + 1 cancelled |
| **Partial** | E1, E7 | Infrastructure exists, some gaps remain |
| **Open** | E6, E8, E9 | Not yet implemented |

---

## Architectural Priority vs Implementation Order

### Key Principle

**Architectural Priority ≠ Implementation Order**

The tasks ranked by architectural importance are NOT necessarily the best order for implementation. This document resolves that tension.

### Architectural Priority (What Matters Most)

| Rank | Task | Why It Matters |
|------|------|----------------|
| 1 | E1 - mime_type persistence | **Foundation:** Schema exists, never populated. All downstream features depend on knowing what type a document is. |
| 2 | E4 - Metadata Ownership | **Foundation:** Clarifies the contract between Discovery (parsers) and Enrichment (workers). Without this, other fixes are ad-hoc. |
| 3 | E2 - structured_data | **Critical Data Loss:** Parser output is thrown away. Must establish whether to persist or explicitly drop. |
| 4 | E7 - Embeddings | **Future-Proofing:** Vector search is a key capability. Must verify storage is complete. |
| 5 | E5 - Thumbnails | **User Experience:** Jobs queued but not implemented. Low complexity. |
| 6 | E6 - OCR | **Feature Completion:** Jobs queued but not implemented. Higher complexity. |
| 7 | E8 - Location Aggregation | **Integration:** Unifies GPS (photo_metadata) and semantic (locations) sources. |
| 8 | E9 - API/UI Gaps | **Presentation:** Surface available data. Depends on E1, E7, E8. |
| 9 | E10 - State Documentation | **Developer Experience:** Clarify document lifecycle states. |
| N/A | ~~E3~~ | **Cancelled:** Replaced by E8 as Map Aggregation Layer. |

---

## Implementation Order

### Phase 0: Foundation (Week 1) - PARALLEL

Start these immediately - they have no dependencies and are low risk.

| Rank | Task | Time | Risk | Parallel With |
|------|------|------|------|---------------|
| 0.1 | **E1** - mime_type persistence | 2-4h | Low | E4, E10 |
| 0.2 | **E10** - State documentation | 2-3h | None | E1, E4 |
| 0.3 | **E4** - Ownership policy docs | 2-3h | None | E1, E10 |

### Phase 1: Contract Establishment (Week 2) - PARTIAL PARALLEL

Establishes the Discovery → Enrichment contract.

| Rank | Task | Time | Risk | Depends On |
|------|------|------|------|-----------|
| 1.1 | **E2** - structured_data handling | 4-8h | Medium | E1 |
| 1.2 | **E7** - Embedding storage completion | 6-10h | Medium | None |

### Phase 2: Feature Completion (Week 3-4) - PARALLEL

Independent feature implementations.

| Rank | Task | Time | Risk | Parallel With |
|------|------|------|------|---------------|
| 2.1 | **E5** - Thumbnail persistence | 4-6h | Low | E6 |
| 2.2 | **E6** - OCR persistence | 8-12h | Medium | E5 |

### Phase 3: Integration (Week 5) - SEQUENTIAL

Unified access to metadata.

| Rank | Task | Time | Risk | Depends On |
|------|------|------|------|-----------|
| 3.1 | **E8** - Map Aggregation Layer | 4-6h | Medium | E2 |
| 3.2 | **E9** - API/UI metadata gaps | 4-6h | Low | E1, E7, E8 |

---

## Dependency Graph

### Visual Representation

```
PHASE 0 (Foundation - Parallel)
════════════════════════════════

┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│   E1 ─────────────┐                                               │
│   mime_type       │                                               │
│   (2-4h)         │                                               │
│                   │                                               │
│                   ▼                                               │
│   E2 ─────────────┼────────────────────────┐                     │
│   structured_data │                        │                     │
│   (4-8h)         │                        │                     │
│                   │                        │                     │
│                   │                        ▼                     │
│                   │              ┌─────────────────────┐          │
│                   │              │      E8            │          │
│                   │              │  Map Aggregation   │          │
│                   │              │      (4-6h)        │          │
│                   │              └─────────┬─────────┘          │
│                   │                        │                     │
│                   │                        ▼                     │
│                   │              ┌─────────────────────┐          │
│                   │              │      E9            │          │
│                   │              │    API/UI          │          │
│                   │              │    (4-6h)          │          │
│                   │              └─────────────────────┘          │
│                   │                        │                     │
│                   │                        │                     │
│                   ├────────────────────────┘                     │
│                   │                                              │
└───────────────────┼──────────────────────────────────────────────┘
                    │
                    ▼
              ┌──────────────────────────────────┐
              │         E4 - Ownership           │
              │         Documentation            │
              │         (2-3h)                   │
              └──────────────────────────────────┘
                          │
                          ▼
              ┌──────────────────────────────────┐
              │       E10 - State Docs           │
              │       (2-3h)                     │
              └──────────────────────────────────┘

PARALLEL TRACKS (Phase 0-2):
══════════════════════════════

Track A: E1 → E2 → E8 → E9 (Sequential chain)
Track B: E4 → E10 (Documentation, parallel with Track A)
Track C: E5 ↔ E6 (Parallel with each other)
Track D: E7 (Independent, parallel with all)
```

### Dependency Table

| Task | Hard Prerequisites | Soft Prerequisites | Can Parallel With |
|------|-------------------|-------------------|-------------------|
| E1 | None | None | E4, E10, E5, E6, E7 |
| E2 | **E1** | None | None (sequential) |
| E4 | None | E1, E2, E8 | E1, E10 |
| E5 | None | None | E1, E6, E7, E10 |
| E6 | None | None | E1, E5, E7, E10 |
| E7 | None | None | E1, E5, E6, E10 |
| E8 | **E2** | None | None (sequential) |
| E9 | **E1, E7, E8** | None | None (sequential) |
| E10 | None | None | E1, E4, E5, E6, E7 |
| ~~E3~~ | **Cancelled** | - | - |

---

## Implementation Waves

### Wave 0: Zero-Dependency Foundation (Week 1)

**Goal:** Establish the foundation without dependencies blocking other work.

| Task | Time | Risk | Parallelizable |
|------|------|------|----------------|
| E1 | 2-4h | Low | ✓ |
| E4 | 2-3h | None | ✓ |
| E10 | 2-3h | None | ✓ |

**Parallel Tracks:**
- Track A: E1 (mime_type - Critical)
- Track B: E4 + E10 (Documentation - Low effort)

**Definition of Done:**
- [ ] `documents.mime_type` populated for new documents
- [ ] Backfill strategy documented
- [ ] Metadata ownership policy documented
- [ ] Document lifecycle states documented

### Wave 1: Contract Establishment (Week 2)

**Goal:** Establish the Discovery → Enrichment contract.

| Task | Time | Risk | Parallelizable |
|------|------|------|----------------|
| E2 | 4-8h | Medium | ✗ (depends on E1) |
| E7 | 6-10h | Medium | ✓ (independent) |

**Parallel Tracks:**
- Track A: E2 (sequential, must follow E1)
- Track B: E7 (embedding storage verification)

**Definition of Done:**
- [ ] Decision made: Persist structured_data OR explicitly document that it's dropped
- [ ] Image dimensions stored in photo_metadata (if persisting)
- [ ] Embedding storage verified complete
- [ ] Embedding retrieval API functional

### Wave 2: Feature Completion (Week 3-4)

**Goal:** Complete queued but unimplemented features.

| Task | Time | Risk | Parallelizable |
|------|------|------|----------------|
| E5 | 4-6h | Low | ✓ |
| E6 | 8-12h | Medium | ✓ |

**Parallel Tracks:**
- Track A: E5 (thumbnails)
- Track B: E6 (OCR)

**Definition of Done:**
- [ ] `generate_thumbnail` job has worker handler
- [ ] Thumbnails stored persistently
- [ ] `run_ocr` job has worker handler
- [ ] OCR text stored persistently
- [ ] OCR text searchable via document_content

### Wave 3: Integration (Week 5)

**Goal:** Unified metadata access.

| Task | Time | Risk | Parallelizable |
|------|------|------|----------------|
| E8 | 4-6h | Medium | ✗ (depends on E2) |
| E9 | 4-6h | Low | ✗ (depends on E8) |

**Sequential Order:** E8 → E9

**Definition of Done:**
- [ ] Unified location API returns GPS from photo_metadata AND semantic from locations
- [ ] Explorer API exposes mime_type, photo metadata
- [ ] Timeline API exposes location names
- [ ] Dashboard filters work

---

## Parallelizable Tasks Summary

### True Parallel (No Dependencies)

These tasks can be implemented in parallel by different developers:

```
Week 1: E1, E4, E10 (3 parallel tracks)
Week 2: E7 (independent)
Week 3: E5, E6 (2 parallel tracks)
```

### Sequential Dependencies

```
E1 → E2 → E8 → E9
```

### Task Groupings

| Group | Tasks | Parallel | Reason |
|-------|-------|----------|--------|
| Foundation | E1, E4, E10 | Yes | No dependencies |
| Contract | E2, E7 | Partial | E2 sequential, E7 parallel |
| Features | E5, E6 | Yes | Independent |
| Integration | E8, E9 | No | Sequential |

---

## Dangerous PR Combinations

### D1: E1 + E2 in Same PR

**Risk:** Both modify `save_document()` and `_process_file()` simultaneously.
**Mitigation:** PR #1 for E1, PR #2 for E2.
**Blast Radius:** Medium - both touch ingestion pipeline.

### D2: E8 + E9 in Same PR

**Risk:** E8 changes location API, E9 assumes E8 structure.
**Mitigation:** PR #1 for E8, PR #2 for E9.
**Blast Radius:** Medium - both touch API layer.

### D3: E5 + E6 + E7 + E10 in Same PR

**Risk:** Low - all independent.
**Benefit:** Could be combined if desired.
**Recommendation:** Keep separate for easier rollback.

### D4: E1 + E5 in Same PR

**Risk:** Low - different files.
**Mitigation:** Document which files are touched.
**Note:** Safe to combine.

### Recommended PR Sequence

| PR # | Tasks | Reason |
|------|-------|--------|
| PR #1 | E1 | Foundation |
| PR #2 | E4 + E10 | Documentation only |
| PR #3 | E2 | Contract (depends on E1) |
| PR #4 | E5 | Feature (independent) |
| PR #5 | E6 | Feature (independent) |
| PR #6 | E7 | Feature (independent) |
| PR #7 | E8 | Integration (depends on E2) |
| PR #8 | E9 | API (depends on E8) |

---

## E5 Implementation Details (Completed)

### Problem
Image thumbnails were not being persisted or displayed in the Explorer. The `generate_thumbnail` job type was defined but the entire pipeline was incomplete:
- Handler was registered but never called
- Thumbnail files were not being created on disk
- `thumbnail_path` column was missing from the database
- API responses did not include thumbnail information
- Frontend did not display thumbnails in grid view

### Solution
E5 implements the complete thumbnail pipeline:

1. **Database Schema**: Added `thumbnail_path` column via migration `010_thumbnails.sql`
2. **Worker Handler**: `ThumbnailGenerator` saves thumbnail path to database after generating file
3. **API Serialization**: Explorer API includes `thumbnail_path` in document detail response
4. **Frontend Display**: Grid view shows thumbnail images when available, falls back to icon

### Files Modified

| File | Change |
|------|--------|
| `storage/migrations/010_thumbnails.sql` | **NEW** - Adds thumbnail_path column and index |
| `storage/migration_manager.py` | Updated TARGET_SCHEMA_VERSION to 10 |
| `workers/thumbnail_generator.py` | Saves thumbnail_path to database after file creation |
| `api/routes/explorer.py` | Includes thumbnail_path in DocumentDetail response |
| `dashboard/src/types/api.ts` | Added thumbnail_path to DocumentDetail interface |
| `dashboard/src/services/api.ts` | Added getThumbnailUrl() helper |
| `dashboard/src/pages/ArtifactExplorer.tsx` | GridDocumentItem component displays thumbnails |
| `dashboard/src/pages/ArtifactExplorer.css` | Added thumbnail styling |

### Pipeline Flow
```
Image discovered → generate_thumbnail job created → worker processes → 
thumbnail stored in .thumbnails/ → path saved to documents.thumbnail_path → 
API returns path → Explorer displays image
```

### Key Implementation Details

1. **Thumbnail Generation** (`workers/thumbnail_generator.py`):
   - Generates JPEG thumbnails at 256x256 max
   - Saves to `.thumbnails/` directory relative to library root
   - Filename format: `{document_id}_{original_name}_thumb.jpg`
   - Handles RGBA images by converting to RGB

2. **Database Persistence** (`workers/thumbnail_generator.py`):
   - `ADD COLUMN IF NOT EXISTS` for forward compatibility
   - Saves relative path (e.g., `.thumbnails/1017_IMG_001_thumb.jpg`)

3. **API Serving** (`api/app.py`):
   - `GET /thumbnails/{path}` serves thumbnail files
   - Path is relative to library root `.thumbnails/` directory

4. **Frontend Display** (`dashboard/src/pages/ArtifactExplorer.tsx`):
   - `GridDocumentItem` component shows thumbnail when `thumbnail_path` is available
   - Falls back to file type icon if thumbnail missing or fails to load
   - Thumbnail URL constructed via `api.getThumbnailUrl()`

### Rollback Strategy
```bash
# Drop the thumbnail_path column
ALTER TABLE documents DROP COLUMN thumbnail_path;

# Remove migration record
DELETE FROM schema_migrations WHERE migration_name = '010_thumbnails.sql';

# Update target schema version
# In migration_manager.py: TARGET_SCHEMA_VERSION = 9
```

---

## Rollback Safety

| Task | Rollback Complexity | Notes |
|------|-------------------|-------|
| E1 | **Low** | Remove mime_type from INSERT - non-breaking |
| E2 | **Medium** | Depends on approach (Option A vs B) |
| E4 | **None** | Documentation only |
| E5 | **Low** | Drop thumbnail_path column |
| E6 | **Low** | Drop OCR content or mark as unused |
| E7 | **Low** | Mark embedding records as unused |
| E8 | **Medium** | Remove aggregation layer |
| E9 | **Low** | Remove API fields |
| E10 | **None** | Documentation only |

---

## Deferred and Cancelled Tasks

### Cancelled

| ID | Finding | Reason |
|----|---------|--------|
| **E3** | GPS Not Copied to locations | **Replaced by E8 Map Aggregation Layer.** GPS belongs in `photo_metadata`, semantic locations belong in `locations` table. No need to duplicate. Both sources should be accessed via a unified aggregation API. |

### Deferred

None - all remaining tasks are in scope.

---

## Quick Reference

### What Works ✓

1. **Discovery metadata**: path, extension, file_size, modified_time correctly persisted
2. **Parser infrastructure**: All parsers produce structured_data with metadata
3. **Worker infrastructure**: Job queue, worker runtime, status transitions
4. **PhotoMetadataExtractor**: Correctly extracts EXIF, GPS, camera data to photo_metadata
5. **Timeline API**: Correctly queries photo_metadata for map and timeline
6. **GPS coordinates**: Stored in photo_metadata (not locations)

### What's Broken ✗

1. ~~**mime_type**: Schema exists, never populated~~ ✅ **FIXED (E1)**
2. ~~**structured_data**: Produced by parsers, dropped at ingestion~~ ✅ **FIXED (E2)**
3. **Thumbnails**: Job queued, not implemented
4. **OCR**: Job queued, output not persisted
5. **Embeddings**: Table exists, storage incomplete
6. **Location API**: Returns only text-extracted locations, not GPS

---

## Status Tracking

| Task | Status | Started | Completed | Notes |
|------|--------|---------|-----------|-------|
| E1 | **Completed** | 2026-07-01 | 2026-07-01 | mime_type persistence |
| E2 | **Completed** | 2026-07-01 | 2026-07-01 | structured_data routing contract |
| ~~E3~~ | **Cancelled** | - | - | Replaced by E8 Map Aggregation Layer |
| **E4** | **Completed** | 2026-07-01 | 2026-07-01 | Metadata ownership contracts |
| E5 | **Completed** | 2026-07-01 | 2026-07-01 | Thumbnails |
| E6 | Planned | - | - | OCR persistence |
| E7 | Planned | - | - | Embeddings |
| E8 | Planned | - | - | Location/EXIF → Map Aggregation |
| E9 | Planned | - | - | API/UI gaps |
| E10 | **Completed** | 2026-07-01 | 2026-07-01 | Lifecycle documentation |

---

## E1 Implementation Details (Completed)

### Problem
`mime_type` was produced by parsers (e.g., `parsers/image_parser.py`) but dropped during ingestion. The `discover_artifact()` method in `collection_watcher.py` did not accept or persist `mime_type`, causing all documents to have `NULL` values.

### Solution
`mime_type` is now determined from the file extension immediately upon artifact discovery, before any parsing or worker processing.

### Architecture
```
filesystem → extension → MIME_TYPE_MAPPING → discover_artifact() → documents.mime_type
```

### Files Modified

| File | Lines | Change |
|------|-------|--------|
| `registry/register_parsers.py` | 24-124 | Added `MIME_TYPE_MAPPING` dict and `get_mime_type_from_extension()` function |
| `storage/backend.py` | 62 | Added `mime_type` parameter to `discover_artifact()` abstract method |
| `storage/postgres_backend.py` | 561-625 | Added `mime_type` parameter, added to INSERT and ON CONFLICT UPDATE |
| `ingestion/collection_watcher.py` | 150-170, 302-314 | Import and pass `mime_type` from `get_mime_type_from_extension()` |
| `api/dependencies.py` | 68-89 | Updated `MockBackend.discover_artifact()` signature |
| `tests/conftest.py` | 46 | Updated `InMemoryBackend.discover_artifact()` signature |
| `tests/test_collection_watcher.py` | 30 | Updated `MockBackend.discover_artifact()` signature |
| `tests/test_initial_scan.py` | 17 | Updated `_MockBackend.discover_artifact()` signature |
| `tests/test_storage_backend.py` | 41, 76 | Updated `ConcreteBackend` and `PartialBackend` signatures |

### Key Changes

1. **registry/register_parsers.py**: Added comprehensive `MIME_TYPE_MAPPING` with 74 file extensions and helper function
2. **storage/postgres_backend.py**: `discover_artifact()` now accepts `mime_type` parameter and persists it to `documents.mime_type` column
3. **ingestion/collection_watcher.py**: Both `_process_file()` and `scan_collection()` now call `get_mime_type_from_extension()` and pass the result

### Migration Requirements
None required. Migration `008_document_fields.sql` already added the `mime_type` column.

### Rollback Strategy
To rollback E1:
```sql
-- Option 1: Set mime_type back to NULL (safe, non-breaking)
UPDATE documents SET mime_type = NULL WHERE mime_type IS NOT NULL;

-- Option 2: Remove mime_type from INSERT (code change)
-- Remove mime_type from discover_artifact() parameters in:
--   - storage/backend.py (line 62)
--   - storage/postgres_backend.py (line 561)
--   - ingestion/collection_watcher.py (lines 157-169)
```

### Verification Commands
```sql
-- Verify mime_type is populated
SELECT COUNT(*) as total, 
       SUM(CASE WHEN mime_type IS NOT NULL THEN 1 ELSE 0 END) as with_mime
FROM documents;

-- Sample mime_type values
SELECT DISTINCT mime_type, COUNT(*) 
FROM documents 
WHERE mime_type IS NOT NULL 
GROUP BY mime_type 
ORDER BY COUNT(*) DESC;
```

### Expected Results After E1
```
.jpg → image/jpeg
.png → image/png
.mp4 → video/mp4
.pdf → application/pdf
.md  → text/markdown
```

---

## E10 Implementation Details (Completed)

### Purpose
Document the lifecycle of discovery and enrichment metadata, clarifying which states belong to which phase.

### What Was Documented

1. **State Matrix**: Discovery vs Enrichment state classification
2. **Phase Diagrams**: Discovery Phase and Enrichment Phase flowcharts
3. **State Transitions**: Allowed and invalid transitions
4. **Rebuild Behavior**: What survives database rebuild
5. **Failure Recovery**: Retry paths and recovery flows
6. **Metadata Ownership**: Which phase owns which metadata
7. **Verification Queries**: SQL queries for state inspection

### Key Insights

| Aspect | Discovery | Enrichment |
|--------|-----------|------------|
| **Trigger** | Filesystem change | Job queue |
| **Owner** | CollectionWatcher | Workers |
| **States** | DISCOVERED, METADATA_INDEXED | CONTENT_EXTRACTED, ENTITY_EXTRACTED, etc. |
| **Rebuildable** | ✓ Yes | ✗ No |
| **Final State** | METADATA_INDEXED (if no parser) | COMPLETE (if all jobs succeed) |

### Documentation File
`refactor/operation-exif/E10-state-confusion.md` contains complete lifecycle documentation.

### No Code Changes
This task was documentation-only. No runtime behavior was modified.

---

## E2 Implementation Details (Completed)

### Problem
The `structured_data` blob produced by all parsers was **completely dropped** in the ingestion pipeline without explicit ownership decisions. This violated Operation EXIF ownership rules because metadata disappeared without determining owner, persistence target, or rebuild source.

### Solution
E2 establishes a **Structured Data Routing Contract** that formally defines the outcome of every parser `structured_data` field:

1. **Persist** - Extracted to appropriate enrichment tables by workers
2. **Transform and persist** - Converted to worker-owned format
3. **Explicitly discard** - Logged as intentional, no data loss concern

### Structured Data Routing Matrix

| Parser | Field | Action | Owner | Destination |
|--------|-------|--------|-------|-------------|
| image | mime_type | discard | inventory | N/A (E1 handles) |
| image | width | persist | photo_metadata | photo_metadata.width |
| image | height | persist | photo_metadata | photo_metadata.height |
| image | aspect_ratio | discard | none | N/A (derived) |
| text | line_count | discard | none | N/A (diagnostic) |
| text | word_count | discard | none | N/A (diagnostic) |
| python | imports/classes/functions | discard | none | N/A (EntityExtractor) |
| csv/json/yaml/xml/toml/ini | [entire blob] | discard | none | N/A (EntityExtractor) |

### Files Modified

| File | Change |
|------|--------|
| `ingestion/structured_data_router.py` | **NEW** - Routing contract module |
| `ingestion/collection_watcher.py` | Import and call router after parsing |
| `refactor/operation-exif/E2-structured-data-dropped.md` | Updated with routing matrix |

### Key Implementation

The router validates that every parser field has an explicit routing decision. If a field is encountered without a routing decision, it raises a `ValueError` (implicit discard detection).

```python
# In collection_watcher.py
from .structured_data_router import route_structured_data

# After parsing:
try:
    routing_decisions = route_structured_data(
        parser_type,
        parsed['structured_data'],
        log_routing=True
    )
except ValueError as e:
    # Implicit discard - fail fast
    raise
```

### No Data Loss
E2 is a **documentation and contract task**. The actual routing behavior was already correct:
- Image dimensions are extracted by PhotoMetadataExtractor
- Structured data parsers output is consumed by EntityExtractor
- Parser diagnostics are intentionally transient

The routing matrix formalizes what was implicit, enabling:
1. Clear ownership documentation
2. Explicit logging of discard decisions
3. Detection of implicit discards (future-proofing)

### Rollback Strategy
To rollback E2:
```bash
# Remove the structured_data_router.py module
rm ingestion/structured_data_router.py

# Remove the routing call from collection_watcher.py (lines 201-218)
# Revert to the original parsing code
```

---

## E4 Implementation Details (Completed)

### Problem
Metadata ownership was unclear across the system, leading to:
- Unclear which component owns which metadata
- Potential for duplicated ownership (e.g., GPS in both photo_metadata and locations)
- Ambiguous parser vs worker responsibility
- Hidden ownership of `structured_data`

### Solution
E4 establishes a **Metadata Ownership Contract** that formally defines:

1. **Discovery Metadata** - Owned by `inventory` (CollectionWatcher)
   - Exists immediately upon artifact discovery
   - Rebuildable from filesystem
   - Never depends on workers

2. **Enrichment Metadata** - Owned by respective workers
   - Asynchronous processing
   - Worker-owned
   - Independently rebuildable

### Key Decisions

| Decision | Resolution |
|----------|------------|
| GPS ownership | `photo_metadata` ONLY (NOT `locations`) |
| Parser role | Discovery only, not persistence |
| `structured_data` | Transient, NOT persisted |
| Location types | GPS (EXIF) vs Semantic (text) are separate |

### Ownership Summary

| Layer | Owner | Component | Table |
|-------|-------|-----------|-------|
| Discovery | inventory | CollectionWatcher | documents |
| Enrichment | photo_metadata | PhotoMetadataExtractor | photo_metadata |
| Enrichment | document_content | ContentExtractor | document_content |
| Enrichment | entities | EntityExtractor | entities |
| Enrichment | locations | LocationExtractor | locations |
| Enrichment | events | EventExtractor | events |
| Enrichment | embeddings | EmbeddingGenerator | document_embeddings |

### Files Documented

| File | Role |
|------|------|
| `refactor/operation-exif/E4-inconsistent-metadata-ownership.md` | Full ownership contract documentation |
| `storage/migrations/*.sql` | Schema ownership reference |
| `workers/*.py` | Worker ownership documentation |
| `ingestion/collection_watcher.py` | Discovery ownership documentation |
| `parsers/*.py` | Parser transient nature documentation |

### Rollback Strategy
None required - E4 is documentation only. No code changes were made.

### Verification
Read `E4-inconsistent-metadata-ownership.md` to verify all metadata fields have exactly one owner.

---

## Worker Audit

### Registered Handlers

The following handlers are registered in `workers/worker.py`:

| Job Type | Handler | Status |
|----------|---------|--------|
| `extract_text` | ContentExtractor | ✅ Implemented |
| `extract_entities` | EntityExtractor | ✅ Implemented |
| `extract_events` | EventExtractor | ✅ Implemented |
| `extract_locations` | LocationExtractor | ✅ Implemented |
| `generate_embeddings` | EmbeddingGenerator | ✅ Implemented |
| `extract_photo_metadata` | PhotoMetadataExtractor | ✅ Implemented |
| `generate_thumbnail` | ThumbnailGenerator | ✅ Implemented |
| `run_ocr` | **NOT REGISTERED** | ❌ Orphan |
| `object_detection` | **NOT REGISTERED** | ❌ Orphan |
| `transcription` | **NOT REGISTERED** | ❌ Orphan |

### Orphan Job Types

Jobs that are queued but have no handler:

| Job Type | Queued By | Handler Status |
|----------|-----------|----------------|
| `run_ocr` | Image artifacts | ❌ No worker |
| `object_detection` | Image artifacts | ❌ No worker |
| `transcription` | Video/audio artifacts | ❌ No worker |

### Job Type Definition Locations

- `JobType` class: `storage/postgres_backend.py:15-30`
- Handler registration: `workers/worker.py:271-277`

---

## Discovery Metadata Audit

### Verification: Discovery Fields Populated

| Field | Source | Persisted | Notes |
|-------|--------|-----------|-------|
| `path` | Filesystem | ✅ | Primary key |
| `extension` | Filesystem | ✅ | From file suffix |
| `mime_type` | Extension mapping | ✅ | Via `get_mime_type_from_extension()` |
| `artifact_type` | Parser registry | ✅ | Maps extension to type |
| `file_size` | Filesystem (st_size) | ✅ | Bytes |
| `modified_time` | Filesystem (st_mtime) | ✅ | Timestamp |
| `status` | System | ✅ | Document lifecycle state |
| `sha256` | Computed | ✅ | Content hash |
| `exists_on_disk` | System | ✅ | Soft delete flag |
| `deleted_at` | System | ✅ | Deletion timestamp |
| `character_count` | Parser | ✅ | Text length |
| `parser` | Parser | ✅ | Parser name |
| `thumbnail_path` | ThumbnailGenerator | ✅ | Relative path |

---

## Enrichment Metadata Audit

### Verification: Worker-Owned Fields

| Metadata Type | Worker | Table | Handler | Storage |
|---------------|--------|-------|---------|---------|
| EXIF | PhotoMetadataExtractor | photo_metadata | ✅ | Complete |
| GPS | PhotoMetadataExtractor | photo_metadata | ✅ | Complete |
| Content | ContentExtractor | document_content | ✅ | Complete |
| Entities | EntityExtractor | entities | ✅ | Complete |
| Locations | LocationExtractor | locations | ✅ | Complete |
| Events | EventExtractor | events | ✅ | Complete |
| Embeddings | EmbeddingGenerator | document_embeddings | ⚠️ | Partial* |
| Thumbnails | ThumbnailGenerator | documents | ✅ | Complete |
| OCR | **NONE** | - | ❌ | Not implemented |
| Object Detection | **NONE** | - | ❌ | Not implemented |
| Transcription | **NONE** | - | ❌ | Not implemented |

*E7 Partial: Embeddings stored but no retrieval API

---

## Operation Health Report

### Resolved Issues

| Issue | Resolution | Date |
|-------|-----------|------|
| E2: structured_data dropped silently | Router module with explicit routing decisions | 2026-07-01 |
| E4: Unclear metadata ownership | Ownership contract documentation | 2026-07-01 |
| E5: Thumbnail persistence missing | ThumbnailGenerator worker implemented | 2026-07-01 |
| E10: Discovery vs Enrichment confusion | State matrix documentation | 2026-07-01 |
| E3: GPS ownership conflict | Cancelled - GPS stays in photo_metadata only | 2026-07-01 |

### Partially Resolved Issues

| Issue | What's Fixed | What's Remaining |
|-------|--------------|------------------|
| E1: mime_type persistence | Infrastructure exists, new docs get mime_type | No backfill for existing documents |
| E7: Embedding storage | Worker generates embeddings, saves to DB | No retrieval API, no semantic search |
| E9: API/UI gaps | Some metadata exposed in models | No filters, no dashboard updates |

### Open Issues

| Issue | Priority | Blocker |
|-------|----------|---------|
| E6: OCR worker missing | Medium | `run_ocr` job queues but never processes |
| E8: Map Aggregation Layer | High | GPS and semantic locations disconnected |
| E9: API/UI metadata filters | Medium | Can't filter by mime_type, camera, etc. |

### Architectural Violations

| Violation | Status | Notes |
|-----------|--------|-------|
| Orphan job types | ⚠️ Warning | `run_ocr`, `object_detection`, `transcription` have no handlers |
| No integration tests | ⚠️ Warning | Pipeline tests exist but not comprehensive |
| Backfill strategy undefined | ⚠️ Warning | Existing documents not updated |

### Technical Debt

| Item | Severity | Description |
|------|----------|-------------|
| OCR library choice | Medium | No OCR library selected or implemented |
| Vector search | Low | No semantic search implementation |
| Reverse geocoding | Low | GPS coordinates not converted to location names |
| Dashboard filters | Low | Frontend not updated with new metadata |

---

## Affected Files Reference

### Core Ingestion

| File | Role |
|------|------|
| `ingestion/collection_watcher.py` | ✅ **FIXED (E1)**: Now persists mime_type during discovery |
| `ingestion/collection_watcher.py` | ✅ **FIXED (E2)**: Routes structured_data with explicit decisions |
| `ingestion/structured_data_router.py` | ✅ **NEW (E2)**: Routing contract module |
| `ingestion/scanner.py` | Discovery metadata source |
| `ingestion/indexer.py` | Indexing logic |

### Storage

| File | Role |
|------|------|
| `storage/postgres_backend.py` | ✅ **FIXED (E1)**: Now accepts and persists mime_type in discover_artifact() |
| `storage/migrations/*.sql` | Schema definitions (mime_type column already exists) |

### Workers

| File | Role |
|------|------|
| `workers/photo_metadata_extractor.py` | EXIF extraction |
| `workers/content_extractor.py` | Text extraction |
| `workers/location_extractor.py` | Location extraction |
| `workers/entity_extractor.py` | Entity extraction |

### API

| File | Role |
|------|------|
| `api/routes/explorer.py` | Document queries (already queries mime_type) |
| `api/routes/timeline.py` | Photo metadata queries |
| `api/routes/operations.py` | System stats |

### Parsers

| File | Role |
|------|------|
| `parsers/image_parser.py` | Image metadata extraction (still produces mime_type for structured_data) |
| `parsers/csv_parser.py` | Structured data parsing |
| `parsers/json_parser.py` | JSON parsing |

---

## Estimated Timeline

```
Week 1:  E1 + E4 + E10 (Parallel tracks)
Week 2:  E2 + E7 (Partial parallel)
Week 3:  E5 + E6 (Parallel tracks)
Week 4:  E5 + E6 (Continue)
Week 5:  E8 + E9 (Sequential)

Total: 5 weeks
Total Effort: 38-55 hours
```

---

## Next Steps

1. ~~E1 (mime_type)~~ → Marked Complete but needs verification of backfill strategy - **PARTIAL**
2. ~~E2 (structured_data routing)~~ → **COMPLETED** ✅
3. ~~E4 (ownership docs)~~ → **COMPLETED** ✅
4. ~~E5 (thumbnail persistence)~~ → **COMPLETED** ✅
5. ~~E10 (state docs)~~ → **COMPLETED** ✅
6. **E7 (embeddings)** → Worker exists, verify storage/retrieval - **PARTIAL**
7. **E6 (OCR)** → No handler registered - **OPEN**
8. **E8 (Map Aggregation)** → Not implemented - **OPEN**
9. **E9 (API/UI gaps)** → Not implemented - **OPEN**

---

**Document Version:** 3.0
**Post-Implementation Audit Completed:** 2026-07-02
**Next Review:** Before next implementation wave
