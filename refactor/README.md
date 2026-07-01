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
