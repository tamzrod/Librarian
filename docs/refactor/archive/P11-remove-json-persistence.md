# P11 — Remove JSON Persistence Layer

**Source:** TD-005  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 9 | **Implementation Order:** 8
**Hard Prerequisites:** P1
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

`ingestion/persistence.py` contained the original JSON snapshot code that pre-dated the PostgreSQL catalog. After P1 was complete (ingestion consolidated to the `CollectionWatcher` path), this file had no callers and was deleted.

## Resolution (2026-07)

- ✅ `ingestion/persistence.py` deleted
- ✅ `ingestion/librarian.py` deleted (as part of P1)
- ✅ No remaining imports of `persistence` module
- ✅ All tests pass

## Verification

```bash
$ ls ingestion/persistence.py
ls: cannot access 'ingestion/persistence.py': No such file or directory

$ ls ingestion/librarian.py
ls: cannot access 'ingestion/librarian.py': No such file or directory
```

## Definition of Done

- ✅ `ingestion/persistence.py` does not exist.
- ✅ `ingestion/librarian.py` does not exist.
- ✅ All tests pass.
