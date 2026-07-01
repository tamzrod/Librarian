# P11 — Remove JSON Persistence Layer

**Source:** TD-005  
**Effort:** Low | **Risk:** Low | **Priority:** 11

---

## Problem

`ingestion/persistence.py` contains the original JSON snapshot code that pre-dates the PostgreSQL catalog. After P1 is complete (ingestion consolidated to the `CollectionWatcher` path), this file will have no callers and can be deleted.

**Prerequisite:** P1 must be completed first.

## Impact

- Dead code in the repository increases cognitive load.
- Any future search for "how does persistence work?" may land on the stale JSON code.

## Files Affected

| File | Action |
|------|--------|
| `ingestion/persistence.py` | Delete |
| `ingestion/librarian.py` | Delete (if not already removed by P1) |
| Any file importing `persistence` | Remove import |

## Steps

1. Confirm P1 is complete and no production code imports from `ingestion/persistence.py`.
2. Run `grep -r "from ingestion.persistence\|import persistence"` to verify no remaining callers.
3. Delete `ingestion/persistence.py`.
4. Delete `ingestion/librarian.py` if still present.
5. Run the full test suite to confirm nothing broke.

## Definition of Done

- `ingestion/persistence.py` does not exist.
- `ingestion/librarian.py` does not exist.
- All tests pass.
