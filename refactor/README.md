# Refactor Plans

Plans are ordered from highest to lowest value. Resolve them top-to-bottom.

| # | Plan | ID | Effort | Risk |
|---|------|----|--------|------|
| 1 | [Consolidate Ingestion Paths](./P1-consolidate-ingestion-paths.md) | V-001 / TD-001, TD-005 | Medium | Low |
| 2 | [Unify Worker Runtime](./P2-unify-worker-runtime.md) | V-003 / TD-002 | Medium | Medium |
| 3 | [Enforce Backend Interface](./P3-enforce-backend-interface.md) | V-007 / TD-003 | Low | Low |
| 4 | [Replace Singleton with Dependency Injection](./P4-replace-singleton-with-di.md) | V-002 / TD-008 | High | Medium |
| 5 | [Add Worker Abstract Base](./P5-add-worker-abstract-base.md) | V-004 / TD-004 | Low | Low |
| 6 | [Add Integration Tests](./P6-add-integration-tests.md) | TD-011 | Medium | Medium |
| 7 | [Add Missing DB Indexes](./P7-add-missing-db-indexes.md) | TD-007 | Low | Medium |
| 8 | [Fix Soft Delete](./P8-fix-soft-delete.md) | V-005 / TD-009 | Low | Low |
| 9 | [Standardise Environment Variables](./P9-standardise-env-vars.md) | V-006 / TD-010 | Low | Low |
| 10 | [Document Schema Migrations](./P10-document-schema-migrations.md) | TD-006 | Low | Medium |
| 11 | [Remove JSON Persistence Layer](./P11-remove-json-persistence.md) | TD-005 | Low | Low |
| 12 | [Add ParserRegistry.get_supported_extensions()](./P12-parser-registry-extensions.md) | TD-012 | Low | Low |

---

Source: `docs/architecture/architectural-audit-2026-06.md`
