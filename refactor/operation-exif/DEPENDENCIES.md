# Operation EXIF - Dependency Graph

## Dependency Overview

```
E1 ────────────────────────────────┬─────────────────────────────────► E4
mime_type persistence               │                                 Metadata
                                  │                                 Ownership
                                  │
                                  ├─────────────────────────────────► E2
                                  │                                 structured_data
                                  │                                 Dropped
                                  │
                                  └─────────────────────────────────► E3
                                                                        GPS to
                                                                        locations
                                                                         │
                                                                         ▼
E8 ◄───────────────────────────────────────────────────────────────── E9
Location/                                                                 API/UI
EXIF                                                                    Gaps
Disconnect                                                               
                                                                         │
                                                                         ▼
E7 ◄───────────────────────────────────────────────────────────────── E6
Embeddings ◄────────────────────────────────────────────────────────── OCR
             │                                                            │
             │                                                            ▼
             └─────────────────────────────────────────────────────────► E5
             Thumbnail                                                    Thumbnail
             Persistence                                                  Persistence
                                                                          │
                                                                          ▼
                                                                         E10
                                                                         State
                                                                         Confusion
```

## Detailed Dependencies

### E1: mime_type Not Persisted

**Prerequisites:** None
**Enables:**
- E2 (structured_data can include mime_type)
- E4 (metadata ownership clear)
- E9 (API can expose mime_type)

**Can parallelize with:** All other tasks

### E2: structured_data Dropped

**Prerequisites:** E1 (mime_type)
**Enables:**
- E3 (can extract dimensions to photo_metadata)
- E4 (metadata ownership clear)
- E5 (can include dimensions in thumbnail)

**Cannot parallelize with:** E1

### E3: GPS Not Copied to locations

**Prerequisites:** E2 (structured_data handling)
**Enables:**
- E8 (unified location queries)
- E9 (API can show GPS locations)

**Cannot parallelize with:** E2

### E4: Inconsistent Metadata Ownership

**Prerequisites:** E1, E2, E3
**Enables:** E9
**Complexity:** Documentation only

**Can parallelize with:** After prerequisites met

### E5: Thumbnail Persistence Missing

**Prerequisites:** None
**Enables:** E9

**Can parallelize with:** All other tasks

### E6: OCR Output Not Persisted

**Prerequisites:** None
**Enables:** E9

**Can parallelize with:** All other tasks

### E7: Embedding Storage Incomplete

**Prerequisites:** None
**Enables:** E9

**Can parallelize with:** All other tasks

### E8: Location/EXIF Disconnect

**Prerequisites:** E3
**Enables:** E9

**Cannot parallelize with:** E3

### E9: API/UI Metadata Gaps

**Prerequisites:** E1, E3, E7
**Complexity:** API additions only

**Cannot parallelize with:** E1, E3, E7 (partially)

### E10: State Confusion

**Prerequisites:** None
**Complexity:** Documentation only

**Can parallelize with:** All other tasks

## Hard Dependencies Summary

| Task | Hard Prerequisites |
|------|-------------------|
| E1 | None |
| E2 | E1 |
| E3 | E2 |
| E4 | E1, E2, E3 |
| E5 | None |
| E6 | None |
| E7 | None |
| E8 | E3 |
| E9 | E1, E3, E7 |
| E10 | None |

## Parallelizable Tasks

The following tasks can be implemented in parallel:

| Task Group | Tasks | Reason |
|------------|-------|--------|
| Wave 1A | E1, E5, E6, E7, E10 | Independent, no prerequisites |
| Wave 1B | E2 | Depends on E1 |
| Wave 2A | E3, E8 | E3 depends on E2, E8 depends on E3 |
| Wave 2B | E4 | Depends on E1, E2, E3 |
| Wave 3 | E9 | Depends on E1, E3, E7 |

## Dangerous Combinations

### E1 + E2 Concurrently

**Risk:** Race condition if both modify save_document() simultaneously
**Mitigation:** Implement E1 first, then E2

### E3 + E8 Concurrently

**Risk:** E8 assumes E3 structure exists
**Mitigation:** Implement E3 first, then E8

### E5 + E6 + E7 + E10

**Risk:** Low - all independent
**Benefit:** Can implement all in parallel

## Implementation Order Recommendation

```
Phase 1: Independent Fixes
├── E1 (mime_type) - 2-4 hours
├── E5 (thumbnails) - 4-6 hours
├── E6 (OCR) - 8-12 hours
├── E7 (embeddings) - 6-10 hours
└── E10 (state) - 2-3 hours

Phase 2: Sequential Fixes
├── E2 (structured_data) - 4-8 hours
│   └── Must complete before E3
├── E3 (GPS to locations) - 2-4 hours
│   └── Must complete before E8
└── E8 (Location/EXIF) - 4-6 hours
    └── Can parallelize with E4, E9

Phase 3: Dependent Fixes
├── E4 (ownership) - 2-3 hours
└── E9 (API/UI) - 4-6 hours
```

## Total Effort

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1 | E1, E5, E6, E7, E10 | 22-35 hours |
| Phase 2 | E2, E3, E8 | 10-18 hours |
| Phase 3 | E4, E9 | 6-9 hours |
| **Total** | All | **38-62 hours** |

## Risk Levels

| Task | Risk | Reason |
|------|------|--------|
| E1 | Low | Schema exists |
| E2 | Medium | Schema change possible |
| E3 | Low | Simple DB inserts |
| E4 | Low | Documentation |
| E5 | Low | New storage |
| E6 | Medium | New dependency |
| E7 | Medium | External service |
| E8 | Medium | Coordination |
| E9 | Low | API additions |
| E10 | Low | Documentation |
