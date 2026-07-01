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
**Status:** Audit Complete

Following the EXIF investigation, a second architectural layer was identified: metadata ownership, persistence, lifecycle, and presentation. This audit examines these gaps.

### Findings Summary

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| E1 | mime_type Not Persisted | Critical | Open |
| E2 | structured_data Dropped | Critical | Open |
| E3 | GPS Not Copied to locations | High | Open |
| E4 | Inconsistent Metadata Ownership | High | Open |
| E5 | Thumbnail Persistence Missing | Medium | Open |
| E6 | OCR Output Not Persisted | Medium | Open |
| E7 | Embedding Storage Incomplete | Medium | Open |
| E8 | Location/EXIF Disconnect | High | Open |
| E9 | API/UI Metadata Gaps | Medium | Open |
| E10 | State Confusion | Low | Open |

### Quick Links

- [Operation EXIF Dashboard](./operation-exif/README.md)
- [Dependency Graph](./operation-exif/DEPENDENCIES.md)
- [Implementation Waves](./operation-exif/WAVES.md)

### Implementation Order

1. **Wave 1:** E1 (mime_type), E5 (thumbnails), E6 (OCR), E7 (embeddings), E10 (state) - parallelizable
2. **Wave 2:** E2 (structured_data), E3 (GPS), E8 (Location/EXIF) - sequential
3. **Wave 3:** E4 (ownership), E9 (API/UI) - dependent

### Estimated Effort

- Wave 1: 22-35 hours
- Wave 2: 10-18 hours
- Wave 3: 6-9 hours
- **Total: 38-62 hours**

### Individual Findings

| Document | Description |
|----------|-------------|
| [E1: mime_type](./operation-exif/E1-mime-type-not-persisted.md) | Critical - schema exists but never populated |
| [E2: structured_data](./operation-exif/E2-structured-data-dropped.md) | Critical - parser output dropped |
| [E3: GPS to locations](./operation-exif/E3-gps-not-copied-to-locations.md) | High - photo_metadata GPS never copied |
| [E4: Metadata Ownership](./operation-exif/E4-inconsistent-metadata-ownership.md) | High - unclear ownership model |
| [E5: Thumbnails](./operation-exif/E5-thumbnail-persistence-missing.md) | Medium - job queued but not implemented |
| [E6: OCR](./operation-exif/E6-ocr-output-not-persisted.md) | Medium - job queued but not implemented |
| [E7: Embeddings](./operation-exif/E7-embedding-storage-incomplete.md) | Medium - table exists but storage incomplete |
| [E8: Location/EXIF](./operation-exif/E8-location-exif-disconnect.md) | High - two separate location systems |
| [E9: API/UI Gaps](./operation-exif/E9-api-ui-metadata-gaps.md) | Medium - available data not exposed |
| [E10: State Confusion](./operation-exif/E10-state-confusion.md) | Low - documentation needed |

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
