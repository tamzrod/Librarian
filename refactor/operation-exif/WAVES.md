# Operation EXIF - Implementation Waves

## Status: Post-Implementation Audit

**Last Updated:** 2026-07-02

---

## Wave Overview

This document defines the implementation waves for Operation EXIF, updated with actual implementation status.

### Implementation Status (as of 2026-07-02)

| Wave | Tasks | Status |
|------|-------|--------|
| Wave 0 | E1, E4, E10 | E1: Partial, E4: Complete, E10: Complete |
| Wave 1 | E2, E7 | E2: Complete, E7: Partial |
| Wave 2 | E5, E6 | E5: Complete, E6: Open (not implemented) |
| Wave 3 | E8, E9 | Both Open |

### Key Findings from Audit

1. **E1 marked Complete but is actually Partial** - Infrastructure exists, no backfill
2. **E7 marked Open but is actually Partial** - Worker exists, no retrieval API
3. **E6 truly Open** - Job queued but no handler registered
4. **E8, E9 truly Open** - Not implemented at all

---

## Wave 0: Zero-Dependency Foundation

**Priority:** Critical  
**Time Estimate:** 6-10 hours  
**Parallelizable:** Yes (3 parallel tracks)  
**Risk:** Low

### Tasks

| Task | Time | Risk | Priority |
|------|------|------|----------|
| E1: mime_type Not Persisted | 2-4h | Low | 1 |
| E4: Metadata Ownership | 2-3h | None | 2 |
| E10: State Confusion | 2-3h | None | 3 |

### Rationale

E1 is the most critical - it prevents permanent data loss. E4 and E10 are documentation-only and can run in parallel with E1 or each other.

### Parallel Tracks

```
Track A: E1 (mime_type) - 2-4 hours
Track B: E4 (ownership docs) - 2-3 hours
Track C: E10 (state docs) - 2-3 hours
```

### Definition of Done for Wave 0

- [ ] `documents.mime_type` is populated for all new documents
- [ ] Backfill strategy documented
- [ ] Metadata ownership policy documented
- [ ] Document lifecycle states documented

### Dependencies in Wave 0

```
None - all tasks are independent
```

---

## Wave 1: Contract Establishment

**Priority:** High  
**Time Estimate:** 10-18 hours  
**Parallelizable:** Partial (E7 independent, E2 sequential)

### Tasks

| Task | Time | Risk | Priority |
|------|------|------|----------|
| E2: structured_data Dropped | 4-8h | Medium | 1 |
| E7: Embedding Storage | 6-10h | Medium | 2 |

### Rationale

E2 must complete before E8 (Wave 3). E7 is independent and can run in parallel.

### Parallel Tracks

```
Track A: E2 (structured_data) - 4-8 hours [Depends on E1]
Track B: E7 (embeddings) - 6-10 hours [Independent]
```

### Definition of Done for Wave 1

- [ ] Decision made: Persist structured_data OR explicitly document it's dropped
- [ ] Image dimensions stored in photo_metadata (if persisting)
- [ ] Embedding storage verified complete
- [ ] Embedding retrieval API functional

### Dependencies in Wave 1

```
E1 (Wave 0) ──► E2
                │
                └──► E7 (parallel)
```

---

## Wave 2: Feature Completion

**Priority:** Medium  
**Time Estimate:** 12-18 hours  
**Parallelizable:** Yes

### Tasks

| Task | Time | Risk | Priority |
|------|------|------|----------|
| E5: Thumbnail Persistence | 4-6h | Low | 1 |
| E6: OCR Persistence | 8-12h | Medium | 2 |

### Rationale

E5 and E6 are independent features. Both are queued but unimplemented. Run in parallel for efficiency.

### Parallel Tracks

```
Track A: E5 (thumbnails) - 4-6 hours
Track B: E6 (OCR) - 8-12 hours
```

### Definition of Done for Wave 2

- [ ] `generate_thumbnail` job has worker handler
- [ ] Thumbnails stored persistently
- [ ] `run_ocr` job has worker handler
- [ ] OCR text stored persistently
- [ ] OCR text searchable via document_content

### Dependencies in Wave 2

```
None - both tasks are independent
```

---

## Wave 3: Integration

**Priority:** High  
**Time Estimate:** 8-12 hours  
**Parallelizable:** No (sequential)

### Tasks

| Task | Time | Risk | Priority |
|------|------|------|----------|
| E8: Map Aggregation Layer | 4-6h | Medium | 1 |
| E9: API/UI Metadata Gaps | 4-6h | Low | 2 |

### Rationale

E8 must complete before E9. E9 depends on E1, E7, and E8.

### Sequential Tracks

```
Track A: E8 (Map Aggregation) - 4-6 hours [Depends on E2]
         │
         └──► E9 (API/UI) - 4-6 hours [Depends on E1, E7, E8]
```

### Definition of Done for Wave 3

- [ ] Unified location API returns GPS from photo_metadata AND semantic from locations
- [ ] Explorer API exposes mime_type, photo metadata
- [ ] Timeline API exposes location names
- [ ] Dashboard filters work

### Dependencies in Wave 3

```
E2 (Wave 1) ──► E8 ──► E9
                        ↑
E1 (Wave 0) ────────────┤
                        │
E7 (Wave 1) ────────────┘
```

---

## Summary Timeline

```
Week 1: Wave 0 (E1, E4, E10) - 6 parallel tracks
Week 2: Wave 1 (E2, E7) - 2 parallel tracks
Week 3: Wave 2 (E5, E6) - 2 parallel tracks
Week 4: Wave 3 (E8, E9) - sequential

Total: 4 weeks
Total Effort: 36-58 hours
```

---

## Critical Path

```
E1 (2-4h) → E2 (4-8h) → E8 (4-6h) → E9 (4-6h)
────────────────────────────────────────────────
Total Critical Path: 14-24 hours
```

---

## Parallelization Strategy

### Maximum Parallel Tracks (Week 1)

```
Track A: E1 (mime_type)
Track B: E4 (ownership docs)
Track C: E10 (state docs)
Track D: E7 (embeddings - independent)
Track E: E5 (thumbnails - independent)
Track F: E6 (OCR - independent)
```

**Note:** 6 parallel tracks possible from Day 1!

### Week 2

```
Track A: E2 (sequential after E1)
Track B: E7 (already started or new)
```

### Week 3-4

```
Track A: E5 + E6 (parallel)
Track B: E8 (sequential after E2)
         └──► E9 (sequential after E8)
```

---

## Risk Mitigation

### High-Risk Tasks

| Task | Risk | Mitigation |
|------|------|------------|
| E2 | Schema change | Option B (extract to existing tables) |
| E6 | OCR library | Use lightweight library first |
| E7 | External service | Test with mock, then real service |
| E8 | Coordination | Clear data flow first |

### Rollback Plans

| Task | Rollback |
|------|----------|
| E1 | Remove column from INSERT (non-breaking) |
| E2 | Revert if Option A chosen |
| E4 | N/A (documentation) |
| E5 | Remove thumbnail table |
| E6 | Remove OCR storage |
| E7 | Mark embedding records as unused |
| E8 | Remove aggregation layer |
| E9 | Remove API fields |
| E10 | N/A (documentation) |

---

## Testing Strategy

### Unit Tests

| Task | Test Coverage |
|------|---------------|
| E1 | Test mime_type in save_document |
| E2 | Test structured_data handling per parser |
| E4 | N/A (documentation) |
| E5 | Test thumbnail generation/storage |
| E6 | Test OCR text storage |
| E7 | Test embedding storage/retrieval |
| E8 | Test unified location queries |
| E9 | Test API responses |
| E10 | N/A (documentation) |

### Integration Tests

| Test | Covers |
|------|--------|
| Full pipeline test | E1, E2 |
| Image metadata test | E1, E2 |
| Location query test | E8 |
| OCR pipeline test | E6 |
| Embedding pipeline test | E7 |

### Regression Tests

- All existing tests pass
- E2E tests pass
- Timeline API tests pass

---

## Effort by Category

| Category | Tasks | Time |
|----------|-------|------|
| Foundation | E1 | 2-4h |
| Documentation | E4, E10 | 4-6h |
| Contract | E2 | 4-8h |
| Features | E5, E6, E7 | 18-28h |
| Integration | E8, E9 | 8-12h |
| **Total** | All | **36-58h** |

---

## Wave Dependencies Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         WAVE 0 (Parallel)                        │
│                                                                   │
│   E1 ───────────────────────────────────────────────────────────┐ │
│   mime_type (2-4h)                                              │ │
│                                                                 │ │
│   E4 ──────────────────────────────────────────────────────────┼─┤
│   Ownership (2-3h)                                               │ │
│                                                                 │ │
│   E10 ─────────────────────────────────────────────────────────┼─┤
│   State (2-3h)                                                  │ │
│                                                                 │ │
└─────────────────────────────────────────────────────────────────┼─┘
                                                                  │
                                                                  │
                                                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                         WAVE 1 (Partial Parallel)                 │
│                                                                   │
│   E2 ───────────────────────────────────────────────────────────┼─┐
│   structured_data (4-8h)                                        │ │
│   [Depends on E1]                                                │ │
│                                                                 │ │
│   E7 ───────────────────────────────────────────────────────────┼─┤
│   Embeddings (6-10h)                                             │ │
│   [Independent]                                                  │ │
│                                                                 │ │
└─────────────────────────────────────────────────────────────────┼─┘
                                                                  │
                                                                  │
                                                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                         WAVE 2 (Parallel)                         │
│                                                                   │
│   E5 ───────────────────────────────────────────────────────────┐ │
│   Thumbnails (4-6h)                                              │ │
│                                                                 │ │
│   E6 ───────────────────────────────────────────────────────────┤ │
│   OCR (8-12h)                                                   │ │
│                                                                 │ │
└─────────────────────────────────────────────────────────────────┘
                                                                  │
                                                                  │
                                                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                         WAVE 3 (Sequential)                       │
│                                                                   │
│   E8 ───────────────────────────────────────────────────────────┐ │
│   Map Aggregation (4-6h)                                         │ │
│   [Depends on E2]                                                │ │
│                                                                 │ │
│   E9 ───────────────────────────────────────────────────────────┤ │
│   API/UI (4-6h)                                                 │ │
│   [Depends on E1, E7, E8]                                       │ │
│                                                                 │ │
└─────────────────────────────────────────────────────────────────┘
```
