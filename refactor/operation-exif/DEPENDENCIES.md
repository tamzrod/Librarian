# Operation EXIF - Dependency Graph

## Status: Post-Implementation Audit

**Last Updated:** 2026-07-02

---

## Implementation Status Summary

| Task | Status | Notes |
|------|--------|-------|
| E1 | **Partial** | Infrastructure exists, no backfill |
| E2 | **Completed** | Router module implemented |
| E3 | **Cancelled** | Replaced by E8 |
| E4 | **Completed** | Documentation only |
| E5 | **Completed** | Handler registered |
| E6 | **Open** | Job queued, no handler |
| E7 | **Partial** | Worker exists, no retrieval API |
| E8 | **Open** | Not implemented |
| E9 | **Partial** | Some metadata exposed |
| E10 | **Completed** | Documentation only |

---

## Dependency Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    PHASE 0 (Parallel)                             │
│                                                                   │
│   E1 ──────────────────────────────────────────┐                │
│   mime_type (2-4h)                              │                │
│                                                 │                │
│   E4 ──────────────────────────────────────────┼─────────────┐ │
│   Ownership (2-3h)                               │             │ │
│                                                 │             │ │
│   E10 ──────────────────────────────────────────┼─────────────┼─┤
│   State docs (2-3h)                              │             │ │
│                                                 │             │ │
└─────────────────────────────────────────────────┼─────────────┼─┘ │
                                                  │             │   │
                                                  │             │   │
                                                  ▼             │   │
┌─────────────────────────────────────────────────┐             │   │
│                   PHASE 1                       │             │   │
│                                                  │             │   │
│   E2 ───────────────────────────────────────────┼─────────────┘   │
│   structured_data (4-8h)                         │                 │
│   [Depends on E1]                                 │                 │
│                                                  │                 │
│   E7 ───────────────────────────────────────────┼─────────────────┘
│   Embeddings (6-10h)                              │
│   [Independent]                                   │
│                                                  │
└──────────────────────────────────────────────────┘
                          │
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│                   PHASE 2 (Parallel)              │
│                                                   │
│   E5 ────────────────────────────────────────────┤
│   Thumbnails (4-6h)                               │
│                                                   │
│   E6 ────────────────────────────────────────────┤
│   OCR (8-12h)                                     │
│                                                   │
└──────────────────────────────────────────────────┘
                          │
                          │
                          ▼
┌──────────────────────────────────────────────────┐
│                   PHASE 3 (Sequential)           │
│                                                   │
│   E8 ────────────────────────────────────────────┤
│   Map Aggregation (4-6h)                          │
│   [Depends on E2]                                 │
│                                                   │
│   E9 ────────────────────────────────────────────┤
│   API/UI (4-6h)                                   │
│   [Depends on E1, E7, E8]                        │
│                                                   │
└──────────────────────────────────────────────────┘
```

---

## Updated Dependency Table

### Hard Dependencies (Must Complete First)

| Task | Hard Prerequisites | Enables |
|------|-------------------|---------|
| E1 | None | E2 |
| E2 | **E1** | E8 |
| E4 | None | E9 (soft) |
| E5 | None | - |
| E6 | None | - |
| E7 | None | E9 |
| E8 | **E2** | E9 |
| E9 | **E1, E7, E8** | - |
| E10 | None | - |

### Can Parallelize With

| Task | Can Parallel With | Notes |
|------|-------------------|-------|
| E1 | E4, E5, E6, E7, E10 | Foundation task |
| E2 | None | Sequential (depends on E1) |
| E4 | E1, E10 | Documentation |
| E5 | E1, E6, E7, E10 | Independent feature |
| E6 | E1, E5, E7, E10 | Independent feature |
| E7 | E1, E5, E6, E10 | Independent feature |
| E8 | None | Sequential (depends on E2) |
| E9 | None | Sequential (depends on E1, E7, E8) |
| E10 | E1, E4, E5, E6, E7 | Documentation |
| ~~E3~~ | **CANCELLED** | - |

---

## Implementation Sequence

### Phase 0: Foundation (Parallel)

```
E1, E4, E10 ──► All can start immediately
```

### Phase 1: Contract (Partial Parallel)

```
E1 ──► E2 (sequential)
   │
   └──► E7 (parallel)
```

### Phase 2: Features (Parallel)

```
E5, E6 ──► Parallel, no dependencies
```

### Phase 3: Integration (Sequential)

```
E2 ──► E8 ──► E9
```

---

## Critical Path

```
E1 ──► E2 ──► E8 ──► E9
(2-4h)  (4-8h)  (4-6h)  (4-6h)
─────────────────────────────
Total Critical Path: 14-24 hours
```

---

## Parallelization Opportunities

### Maximum Parallelization (Week 1)

```
Track A: E1 (mime_type)
Track B: E4 (ownership docs)
Track C: E10 (state docs)
Track D: E7 (embeddings - independent)
Track E: E5 (thumbnails - independent)
Track F: E6 (OCR - independent)
```

**Note:** 6 parallel tracks possible in Week 1!

### After E1 Complete

```
E2 (sequential) ──► E8 (sequential) ──► E9 (sequential)
```

### Safe Parallel Combinations

| Combination | Safe? | Reason |
|------------|-------|--------|
| E1 + E4 + E10 | ✓ Yes | Different files, no conflicts |
| E1 + E5 + E6 + E7 | ✓ Yes | Different files |
| E2 + E7 | ✓ Yes | E7 is independent |
| E5 + E6 | ✓ Yes | Both independent |
| E8 + E9 | ✗ No | E9 depends on E8 |
| E1 + E2 | ✗ No | E2 depends on E1 |

---

## Dangerous Combinations

### D1: E1 + E2 in Same PR

**Risk:** Both modify `save_document()` and `_process_file()`.
**Mitigation:** Separate PRs.
**Blast Radius:** Medium.

### D2: E2 + E8 in Same PR

**Risk:** E2 changes structured_data handling, E8 assumes E2 structure.
**Mitigation:** Separate PRs.
**Blast Radius:** Medium.

### D3: E8 + E9 in Same PR

**Risk:** E9 assumes E8 structure exists.
**Mitigation:** Separate PRs.
**Blast Radius:** Medium.

---

## Recommended PR Sequence

| PR # | Tasks | Phase | Notes |
|------|-------|-------|-------|
| #1 | E1 | 0 | Foundation |
| #2 | E4 + E10 | 0 | Documentation |
| #3 | E7 | 1 | Independent |
| #4 | E2 | 1 | Sequential (after #1) |
| #5 | E5 | 2 | Independent |
| #6 | E6 | 2 | Independent |
| #7 | E8 | 3 | Sequential (after #4) |
| #8 | E9 | 3 | Sequential (after #7) |

---

## E3 Cancellation Impact

### Before (Old Order)

```
E1 → E2 → E3 → E8 → E9
```

### After (New Order)

```
E1 → E2 → E8 → E9
     ↑
     E7 (parallel)
```

**Benefit:** Removed unnecessary data duplication step. E3 was going to copy GPS from `photo_metadata` to `locations` table, but this creates dual ownership and sync issues.

**New Approach:** E8 creates a Map Aggregation Layer that queries both `photo_metadata` (for GPS) and `locations` (for semantic names) and returns unified results.

---

## Risk Levels

| Task | Risk | Reason |
|------|------|--------|
| E1 | Low | Schema column exists |
| E2 | Medium | May require schema decision |
| E4 | None | Documentation only |
| E5 | Low | New storage |
| E6 | Medium | New dependency (OCR library) |
| E7 | Medium | External service |
| E8 | Medium | API changes |
| E9 | Low | API additions |
| E10 | None | Documentation only |
