# Refactor Plans

This folder tracks the approved refactor strategy for the Librarian codebase.

---

## Active Plans

Plans currently in progress or ready to begin implementation.

No active plans at this time.

---

## Planned

Approved plans not yet started.

| ID | Plan | Effort | Risk | Priority | Notes |
|----|------|--------|------|----------|-------|
| P4 | [Replace AppState Singleton with DI](./P4-replace-singleton-with-di.md) | High | Medium | 1 | Intentionally last due to blast radius |

---

## Operation EXIF - Metadata Architecture Audit

**Audit Date:** 2026-07-01
**Priority:** Critical
**Status:** Re-prioritization Complete

Following the EXIF investigation, a second architectural layer was identified: metadata ownership, persistence, lifecycle, and presentation. This audit examines these gaps.

### Key Architectural Decision

**E3 has been CANCELLED.** GPS coordinates should remain in `photo_metadata`, semantic locations in `locations` table. E8 now implements a Map Aggregation Layer that queries both sources.

### Findings Summary

| ID | Finding | Severity | Status | Priority |
|----|---------|----------|--------|----------|
| E1 | mime_type Not Persisted | Critical | Planned | 1 |
| E2 | structured_data Dropped | Critical | Planned | 3 |
| ~~E3~~ | GPS Not Copied to locations | High | **Cancelled** | N/A |
| E4 | Inconsistent Metadata Ownership | High | Planned | 2 |
| E5 | Thumbnail Persistence Missing | Medium | Planned | 5 |
| E6 | OCR Output Not Persisted | Medium | Planned | 6 |
| E7 | Embedding Storage Incomplete | Medium | Planned | 4 |
| E8 | Location/EXIF → Map Aggregation | High | Planned | 7 |
| E9 | API/UI Metadata Gaps | Medium | Planned | 8 |
| E10 | State Confusion | Low | Planned | 2a |

### Quick Links

- [Operation EXIF Dashboard](./operation-exif/README.md)
- [Dependency Graph](./operation-exif/DEPENDENCIES.md)
- [Implementation Waves](./operation-exif/WAVES.md)

### Implementation Order (Updated)

1. **Phase 0 (Week 1):** E1 (mime_type), E4 (ownership), E10 (state) - parallelizable, zero dependencies
2. **Phase 1 (Week 2):** E2 (structured_data), E7 (embeddings) - E2 depends on E1
3. **Phase 2 (Week 3-4):** E5 (thumbnails), E6 (OCR) - parallelizable
4. **Phase 3 (Week 5):** E8 (Map Aggregation), E9 (API/UI) - sequential

### Estimated Effort

- Phase 0: 6-10 hours
- Phase 1: 10-18 hours
- Phase 2: 12-18 hours
- Phase 3: 8-12 hours
- **Total: 36-58 hours**

### Critical Path

```
E1 (2-4h) → E2 (4-8h) → E8 (4-6h) → E9 (4-6h)
────────────────────────────────────────────────
Total: 14-24 hours
```

### Individual Findings

| Document | Description | Status |
|----------|-------------|--------|
| [E1: mime_type](./operation-exif/E1-mime-type-not-persisted.md) | Critical - schema exists but never populated | Planned |
| [E2: structured_data](./operation-exif/E2-structured-data-dropped.md) | Critical - parser output dropped | Planned |
| [E3: GPS to locations](./operation-exif/E3-gps-not-copied-to-locations.md) | **Cancelled** - Replaced by E8 Map Aggregation | Cancelled |
| [E4: Metadata Ownership](./operation-exif/E4-inconsistent-metadata-ownership.md) | High - unclear ownership model | Planned |
| [E5: Thumbnails](./operation-exif/E5-thumbnail-persistence-missing.md) | Medium - job queued but not implemented | Planned |
| [E6: OCR](./operation-exif/E6-ocr-output-not-persisted.md) | Medium - job queued but not implemented | Planned |
| [E7: Embeddings](./operation-exif/E7-embedding-storage-incomplete.md) | Medium - table exists but storage incomplete | Planned |
| [E8: Location/EXIF](./operation-exif/E8-location-exif-disconnect.md) | High - **Now: Map Aggregation Layer** | Planned |
| [E9: API/UI Gaps](./operation-exif/E9-api-ui-metadata-gaps.md) | Medium - available data not exposed | Planned |
| [E10: State Confusion](./operation-exif/E10-state-confusion.md) | Low - documentation needed | Planned |

---

## Archived Plans

Completed refactor plans. See [archive/](archive/) for historical documentation.

### Wave 1 — Setup and Documentation

| ID | Plan | Completion Date | Effort | Priority |
|----|------|-----------------|--------|----------|
| P9 | [Standardise Environment Variables](./archive/P9-standardise-env-vars.md) | 2026-07 | Low | 10 |
| P10 | [Document Schema Migrations](./archive/P10-document-schema-migrations.md) | 2026-07 | Low | 11 |
| P12 | [Add ParserRegistry Extensions](./archive/P12-parser-registry-extensions.md) | 2026-07 | Low | 12 |

### Wave 2 — Establish Contracts

| ID | Plan | Completion Date | Effort | Priority |
|----|------|-----------------|--------|----------|
| P3 | [Enforce Backend Interface](./archive/P3-enforce-backend-interface.md) | 2026-07 | Low | 2 |
| P5 | [Add Worker Abstract Base](./archive/P5-add-worker-abstract-base.md) | 2026-07 | Low | 6 |

### Wave 3 — Regression Coverage

| ID | Plan | Completion Date | Effort | Priority |
|----|------|-----------------|--------|----------|
| P6 | [Add Integration Tests](./archive/P6-add-integration-tests.md) | 2026-07 | Medium | 5 |

### Wave 4 — Consolidate Ingestion

| ID | Plan | Completion Date | Effort | Priority |
|----|------|-----------------|--------|----------|
| P1 | [Consolidate Ingestion Paths](./archive/P1-consolidate-ingestion-paths.md) | 2026-07 | Medium | 3 |
| P11 | [Remove JSON Persistence](./archive/P11-remove-json-persistence.md) | 2026-07 | Low | 9 |

### Wave 5 — Database Improvements

| ID | Plan | Completion Date | Effort | Priority |
|----|------|-----------------|--------|----------|
| P7 | [Add Missing DB Indexes](./archive/P7-add-missing-db-indexes.md) | 2026-07 | Low | 8 |

### Wave 6 — Runtime Unification

| ID | Plan | Completion Date | Effort | Priority |
|----|------|-----------------|--------|----------|
| P2 | [Unify Worker Runtime](./P2-unify-worker-runtime.md) | 2026-07 | Medium | 4 |

### Wave 7 — Soft Delete Fix

| ID | Plan | Completion Date | Effort | Priority |
|----|------|-----------------|--------|----------|
| P8 | [Fix Soft Delete](./P8-fix-soft-delete.md) | 2026-07 | Low | 7 |

---

## Dependency Graph

```text
P10 ──soft──▶ P7
P3  ──hard──▶ P8 ✅
P3  ──soft──▶ P4
P5  ──hard──▶ P2 ✅
P6  ──hard──▶ P1
P6  ──hard──▶ P2 ✅
P6  ──hard──▶ P4
P1  ──hard──▶ P11
P1  ──soft──▶ P8 ✅
P2  ──soft──▶ P4 ✅
```

### Prerequisites for Remaining Plans

| Plan | Hard Prerequisites | Soft Prerequisites |
|------|-------------------|-------------------|
| **P4** | P6 ✅ | P3 ✅, P2 ✅ |

---

## Sequencing Notes

- **P4 is intentionally last** because it touches application startup, route wiring, test fixtures, and repository-wide state access patterns.

---

Source: `docs/architecture/architectural-audit-2026-06.md`
Audit: `docs/architecture/architectural-audit-2026-07.md`
