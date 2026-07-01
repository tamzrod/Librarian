# Operation EXIF - Metadata Architecture Audit

**Date:** 2026-07-01
**Status:** Re-prioritization Complete
**Priority:** Architectural

## Executive Summary

This audit examines the second architectural layer exposed by the EXIF investigation: metadata ownership, persistence, lifecycle, and presentation. The original refactor stabilized ingestion, worker runtime, backend contracts, startup, migrations, and soft delete. This audit identifies critical gaps in how metadata flows through the system.

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
| E1 | mime_type Not Persisted | Critical | Architectural Violation | **1** |
| E2 | structured_data Dropped in Pipeline | Critical | Open | **3** |
| E3 | GPS Not Copied to locations Table | High | **Cancelled** | N/A |
| E4 | Inconsistent Metadata Ownership | High | Architectural Violation | **2** |
| E5 | Thumbnail Persistence Missing | Medium | Open | **5** |
| E6 | OCR Output Not Persisted | Medium | Open | **6** |
| E7 | Embedding Storage Incomplete | Medium | Open | **4** |
| E8 | Location/EXIF Disconnect → Map Aggregation | High | Open | **7** |
| E9 | API/UI Metadata Gaps | Medium | Partial | **8** |
| E10 | Discovery vs Enrichment State Confusion | Low | Technical Debt | **2a** |

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

## Rollback Safety

| Task | Rollback Complexity | Notes |
|------|-------------------|-------|
| E1 | **Low** | Remove mime_type from INSERT - non-breaking |
| E2 | **Medium** | Depends on approach (Option A vs B) |
| E4 | **None** | Documentation only |
| E5 | **Low** | Drop thumbnail table |
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

1. **mime_type**: Schema exists, never populated
2. **structured_data**: Produced by parsers, dropped at ingestion
3. **Thumbnails**: Job queued, not implemented
4. **OCR**: Job queued, output not persisted
5. **Embeddings**: Table exists, storage incomplete
6. **Location API**: Returns only text-extracted locations, not GPS

---

## Status Tracking

| Task | Status | Started | Completed | Notes |
|------|--------|---------|-----------|-------|
| E1 | Planned | - | - | mime_type persistence |
| E2 | Planned | - | - | structured_data handling |
| ~~E3~~ | **Cancelled** | - | - | Replaced by E8 Map Aggregation Layer |
| E4 | Planned | - | - | Metadata ownership |
| E5 | Planned | - | - | Thumbnails |
| E6 | Planned | - | - | OCR persistence |
| E7 | Planned | - | - | Embeddings |
| E8 | Planned | - | - | Location/EXIF → Map Aggregation |
| E9 | Planned | - | - | API/UI gaps |
| E10 | Planned | - | - | State confusion |

---

## Affected Files Reference

### Core Ingestion

| File | Role |
|------|------|
| `ingestion/collection_watcher.py` | Metadata drops here |
| `ingestion/scanner.py` | Discovery metadata source |
| `ingestion/indexer.py` | Indexing logic |

### Storage

| File | Role |
|------|------|
| `storage/postgres_backend.py` | Document persistence |
| `storage/migrations/*.sql` | Schema definitions |

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
| `api/routes/explorer.py` | Document queries |
| `api/routes/timeline.py` | Photo metadata queries |
| `api/routes/operations.py` | System stats |

### Parsers

| File | Role |
|------|------|
| `parsers/image_parser.py` | Image metadata extraction |
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

1. Review this prioritization document
2. Assign ownership for Wave 0 tasks
3. Begin E1 (mime_type) implementation - no dependencies
4. Begin E4 + E10 (documentation) in parallel
5. Schedule review of E2 approach (Option A vs B vs C)

---

**Document Version:** 2.0
**Re-prioritization Completed:** 2026-07-01
**Next Review:** After Wave 0 implementation
