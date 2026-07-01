# Operation EXIF - Implementation Waves

## Wave Overview

This document defines implementation waves for Operation EXIF, prioritizing high-value fixes and parallelizing independent work.

---

## Wave 1: Critical Data Loss Prevention

**Priority:** Critical
**Time Estimate:** 22-35 hours
**Parallelizable:** Yes (except E1 → E2 dependency)

### Tasks

| Task | Time | Risk | Priority |
|------|------|------|----------|
| E1: mime_type Not Persisted | 2-4h | Low | 1 |
| E5: Thumbnail Persistence | 4-6h | Low | 2 |
| E6: OCR Persistence | 8-12h | Medium | 3 |
| E7: Embedding Storage | 6-10h | Medium | 4 |
| E10: State Confusion | 2-3h | Low | 5 |

### Rationale

E1 is the most critical - it prevents permanent data loss. E5, E6, E7, and E10 are independent and can run in parallel.

### Dependencies in Wave 1

```
E1 ────► E2 (in Wave 2)
   │
   └──► E5, E6, E7, E10 (parallel)
```

### Definition of Done for Wave 1

- [ ] `documents.mime_type` is populated for all new documents
- [ ] Thumbnails can be stored and served
- [ ] OCR text is persisted
- [ ] Embeddings are stored and retrievable
- [ ] Document states are documented

---

## Wave 2: Data Flow Fixes

**Priority:** High
**Time Estimate:** 10-18 hours
**Parallelizable:** No (sequential)

### Tasks

| Task | Time | Risk | Priority |
|------|------|------|----------|
| E2: structured_data Dropped | 4-8h | Medium | 1 |
| E3: GPS Not Copied to locations | 2-4h | Low | 2 |
| E8: Location/EXIF Disconnect | 4-6h | Medium | 3 |

### Rationale

E2 must complete before E3. E3 must complete before E8. These are sequential dependencies.

### Dependencies in Wave 2

```
E2 ────► E3 ────► E8
```

### Definition of Done for Wave 2

- [ ] structured_data is handled (either persisted or extracted)
- [ ] GPS coordinates are stored in locations table
- [ ] LocationExtractor can use photo_metadata GPS data

---

## Wave 3: Architectural Clarity

**Priority:** Medium
**Time Estimate:** 6-9 hours
**Parallelizable:** Partial

### Tasks

| Task | Time | Risk | Priority |
|------|------|------|----------|
| E4: Metadata Ownership | 2-3h | Low | 1 |
| E9: API/UI Metadata Gaps | 4-6h | Low | 2 |

### Rationale

E4 is documentation-only and can run anytime. E9 depends on E1, E3, and E7.

### Dependencies in Wave 3

```
E4: No dependencies
E9: E1, E3, E7 (Wave 1 + Wave 2)
```

### Definition of Done for Wave 3

- [ ] Metadata ownership policy documented
- [ ] API exposes all available metadata
- [ ] Dashboard uses available metadata

---

## Summary Timeline

```
Month 1:
├── Week 1-2: Wave 1 (E1, E5, E6, E7, E10)
├── Week 3-4: Wave 2 (E2, E3, E8)

Month 2:
├── Week 1-2: Wave 3 (E4, E9)
└── Week 3-4: Testing and stabilization
```

---

## Parallelization Strategy

### Week 1: E1 + E5 + E10 (3 parallel tracks)

**Track A (E1 - mime_type):**
- 2-4 hours
- Low risk
- Start first

**Track B (E5 - Thumbnails):**
- 4-6 hours
- Independent

**Track C (E10 - State docs):**
- 2-3 hours
- Documentation only

### Week 2: E6 + E7 (2 parallel tracks)

**Track A (E6 - OCR):**
- 8-12 hours
- Requires OCR library setup

**Track B (E7 - Embeddings):**
- 6-10 hours
- Requires embedding model setup

### Week 3: E2 (sequential)

**Track A (E2 - structured_data):**
- 4-8 hours
- Depends on E1

### Week 4: E3 + E8 (sequential)

**Track A (E3 - GPS):**
- 2-4 hours
- Depends on E2

**Track B (E8 - Location/EXIF):**
- 4-6 hours
- Depends on E3

### Week 5-6: E4 + E9 (parallel)

**Track A (E4 - Ownership docs):**
- 2-3 hours
- No dependencies

**Track B (E9 - API/UI):**
- 4-6 hours
- Depends on E1, E3, E7

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
| E3 | Delete location records (no side effects) |
| E5 | Remove thumbnail table |
| E6 | Remove OCR storage |
| E7 | Remove embedding records |

---

## Testing Strategy

### Unit Tests

Each task should have unit tests:
- E1: Test mime_type in save_document
- E2: Test structured_data handling per parser
- E3: Test GPS location creation
- E5: Test thumbnail generation/storage
- E6: Test OCR text storage
- E7: Test embedding storage/retrieval
- E8: Test location queries with GPS
- E9: Test API responses
- E10: N/A (documentation)

### Integration Tests

| Test | Covers |
|------|--------|
| Full pipeline test | E1, E2 |
| Image metadata test | E1, E2, E3 |
| Location query test | E3, E8 |
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
| Data Loss Prevention | E1, E2 | 6-12h |
| Feature Completion | E5, E6, E7 | 18-28h |
| Integration | E3, E8, E9 | 10-16h |
| Documentation | E4, E10 | 4-6h |
| **Total** | All | **38-62h** |
