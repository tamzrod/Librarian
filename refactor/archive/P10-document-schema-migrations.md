# P10 — Document Schema Migration Behaviour

**Source:** TD-006  
**Effort:** Low | **Risk:** Medium
**Architectural Priority:** 11 | **Implementation Order:** 2
**Hard Prerequisites:** None
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

Schema migrations 001–004 existed but their behaviour on upgrade, downgrade, and partial application was undocumented. Operators upgrading from an older version had no reference for what each migration does or whether it is safe to run on a live database.

## Resolution (2026-07)

- ✅ `storage/migrations/CHANGELOG.md` created with comprehensive documentation
- ✅ Each migration documented with:
  - Upgrade summary
  - Live-DB safety rating
  - Manual steps required
- ✅ Detailed notes for each migration file
- ✅ Recovery and rollback procedures documented

## Implementation Evidence

```markdown
# storage/migrations/CHANGELOG.md

## Migration Summary

| Migration | Upgrade Summary | Live-DB Safety | Manual Steps |
|---|---|---|---|
| `001_initial_schema.sql` | Creates schema_migrations, collections, documents... | Fresh-install safe | None |
| `002_entities.sql` | Adds entity, relationship... | Safe on live systems | None |
| ...
```

## Definition of Done

- ✅ Every migration file documented (via CHANGELOG.md).
- ✅ `storage/migrations/CHANGELOG.md` exists and is up to date.
- ✅ The README/docs reference the migration guide.
