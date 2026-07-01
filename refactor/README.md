# Refactor Plans

This folder tracks the approved refactor strategy.

- **Architectural Priority** answers: which problems matter most to solve from a system design perspective.
- **Implementation Order** answers: which sequence should be executed to minimize risk, preserve safety nets, and reduce cross-PR blast radius.

These two orders are intentionally different. High architectural importance does **not** imply a plan should be implemented first.

## Architectural Priority vs Implementation Order

| Architectural Priority | Implementation Order | ID | Plan | Effort | Risk | Notes | Status |
|---|---:|---|---|---|---|---|---|
| 1 | 12 | P4 | [Replace AppState Singleton with Dependency Injection](./P4-replace-singleton-with-di.md) | High | Medium | Highest architectural value; intentionally last due to blast radius | Planned |
| 2 | 4 | P3 | [Enforce Backend Interface](./P3-enforce-backend-interface.md) | Low | Low | Foundational backend contract before later structural changes | Planned |
| 3 | 7 | P1 | [Consolidate Ingestion Paths](./P1-consolidate-ingestion-paths.md) | Medium | Low | Removes duplicate ingestion architecture after baseline tests exist | Planned |
| 4 | 11 | P2 | [Unify Worker Runtime](./P2-unify-worker-runtime.md) | Medium | Medium | Important runtime consolidation, but safer after P5 and P6 | Planned |
| 5 | 6 | P6 | [Add Integration Tests](./P6-add-integration-tests.md) | Medium | Medium | Baseline regression suite required before larger refactors | Planned |
| 6 | 5 | P5 | [Add Worker Abstract Base](./P5-add-worker-abstract-base.md) | Low | Low | Small enabling contract for P2 | Planned |
| 7 | 10 | P8 | [Fix Soft Delete](./P8-fix-soft-delete.md) | Low | Low | Depends on enforced backend contract; simpler after ingestion cleanup | Planned |
| 8 | 9 | P7 | [Add Missing DB Indexes](./P7-add-missing-db-indexes.md) | Low | Medium | Important operational improvement; scheduled after migration docs | Planned |
| 9 | 8 | P11 | [Remove JSON Persistence Layer](./P11-remove-json-persistence.md) | Low | Low | Cleanup step that should land immediately after P1 | Planned |
| 10 | 1 | P9 | [Standardise Environment Variables](./P9-standardise-env-vars.md) | Low | Low | Safe, low-blast-radius setup work | Completed |
| 11 | 2 | P10 | [Document Schema Migrations](./P10-document-schema-migrations.md) | Low | Medium | Documentation-first migration hygiene before schema changes | In Progress |
| 12 | 3 | P12 | [Add ParserRegistry.get_supported_extensions()](./P12-parser-registry-extensions.md) | Low | Low | Isolated API improvement with no sequencing pressure | Planned |

## Approved Implementation Order

1. [P9 — Standardise Environment Variables](./P9-standardise-env-vars.md)
2. [P10 — Document Schema Migrations](./P10-document-schema-migrations.md)
3. [P12 — Add ParserRegistry.get_supported_extensions()](./P12-parser-registry-extensions.md)
4. [P3 — Enforce Backend Interface](./P3-enforce-backend-interface.md)
5. [P5 — Add Worker Abstract Base](./P5-add-worker-abstract-base.md)
6. [P6 — Add Integration Tests](./P6-add-integration-tests.md) — baseline regression suite
7. [P1 — Consolidate Ingestion Paths](./P1-consolidate-ingestion-paths.md)
8. [P11 — Remove JSON Persistence Layer](./P11-remove-json-persistence.md)
9. [P7 — Add Missing DB Indexes](./P7-add-missing-db-indexes.md)
10. [P8 — Fix Incomplete Soft Delete](./P8-fix-soft-delete.md)
11. [P2 — Unify Worker Runtime](./P2-unify-worker-runtime.md)
12. [P4 — Replace AppState Singleton with Dependency Injection](./P4-replace-singleton-with-di.md)

## Dependency Graph

```text
P10 ──soft──▶ P7
P3  ──hard──▶ P8
P3  ──soft──▶ P4
P5  ──hard──▶ P2
P6  ──hard──▶ P1
P6  ──hard──▶ P2
P6  ──hard──▶ P4
P1  ──hard──▶ P11
P1  ──soft──▶ P8
P2  ──soft──▶ P4
```

### Hard prerequisites

- **P6 → P1** — baseline ingestion regression coverage must exist first
- **P6 → P2** — worker-runtime consolidation must have regression coverage first
- **P6 → P4** — the AppState/route rewrite must have regression coverage first
- **P5 → P2** — P2 should standardise on `BaseWorker.process()` instead of inventing a separate worker contract
- **P3 → P8** — soft-delete cleanup assumes `mark_deleted()` is a real backend contract
- **P1 → P11** — JSON persistence cleanup is valid only after ingestion is consolidated

### Soft prerequisites

- **P3 → P4** — dependency injection is safer once backend contracts are enforced
- **P10 → P7** — document migration behaviour before adding new schema migrations
- **P1 → P8** — soft-delete cleanup is simpler once the ingestion path is consolidated
- **P2 → P4** — removing duplicate worker runtime logic first narrows P4's refactor surface in `api/app_state.py`

### Sequencing notes

- **P11 should immediately follow P1** to remove obsolete JSON persistence before it becomes stale cleanup work.
- **P4 is intentionally last** because it touches application startup, route wiring, test fixtures, and repository-wide state access patterns.

## Implementation Waves

| Wave | Plans | Purpose |
|---|---|---|
| 1 | P9, P10, P12 | Low-risk setup and documentation work with no blocking dependencies |
| 2 | P3, P5 | Establish backend and worker contracts |
| 3 | P6 | Land the baseline regression suite before structural refactors |
| 4 | P1, P11 | Consolidate ingestion, then remove JSON persistence immediately after |
| 5 | P7, P8 | Database/schema follow-up work after contracts and ingestion cleanup |
| 6 | P2 | Consolidate worker runtime after worker contract and regression coverage exist |
| 7 | P4 | Final repository-wide dependency injection refactor |

## Plans That Can Execute in Parallel

These plans can run in parallel once all prerequisites for that wave are satisfied:

- **Wave 1:** P9, P10, and P12
- **Wave 2:** P3 and P5
- **Wave 5:** P7 and P8

Plans that should remain sequential:

- **P6 before P1, P2, and P4**
- **P1 before P11**
- **P5 before P2**
- **P3 before P8**
- **P4 after all prior waves**

## Plans That Must Not Be Combined into a Single PR

- **P1 + P2** — both are medium-sized structural refactors and both touch `api/app_state.py`
- **P1 + P4** — combines ingestion consolidation with repository-wide dependency injection
- **P2 + P4** — combines worker-runtime consolidation with the broadest state-management rewrite
- **P4 + P8** — mixes repository-wide DI churn with schema/backend soft-delete changes
- **P7 + P8** — two migration-bearing changes should remain independently reviewable and rollbackable
- **P3 + P4** — P3 should merge first so P4 can build on a verified backend contract

Natural pairings that *can* stay together when scope remains small:

- **P1 + P11** — cleanup immediately after ingestion consolidation
- **P9 + P12** — independent, low-risk documentation/API improvements
- **P10 + P7** — migration documentation plus the related schema update
- **P3 + P5** — small interface-enforcement changes in separate subsystems

---

Source: `docs/architecture/architectural-audit-2026-06.md`
