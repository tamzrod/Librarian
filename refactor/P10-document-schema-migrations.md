# P10 — Document Schema Migration Behaviour

**Source:** TD-006  
**Effort:** Low | **Risk:** Medium
**Architectural Priority:** 11 | **Implementation Order:** 2
**Hard Prerequisites:** None
**Soft Prerequisites:** None

---

## Problem

Schema migrations 001–004 exist but their behaviour on upgrade, downgrade, and partial application is undocumented. Operators upgrading from an older version have no reference for what each migration does or whether it is safe to run on a live database.

## Impact

- Operators may run migrations without understanding their impact, causing data loss or downtime.
- Debugging a failed migration is harder without knowing what state the schema should be in.

## Files Affected

| File | Action |
|------|--------|
| `storage/migrations/` | Add a `CHANGELOG.md` or annotate each migration file |
| `docs/` | Add a short migration guide |

## Steps

1. For each migration file (001–current), add a header comment block describing:
   - What tables/columns are added, modified, or removed.
   - Whether the migration is safe to run on a live database.
   - Any required manual steps (e.g. backfill).
2. Create `storage/migrations/CHANGELOG.md` summarising all migrations in order.
3. Add a note to `README.md` or `docs/` pointing operators to the migration changelog.

## Definition of Done

- Every migration file has a descriptive header comment.
- `storage/migrations/CHANGELOG.md` exists and is up to date.
- The README/docs reference the migration guide.
