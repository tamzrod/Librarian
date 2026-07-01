# P1 — Consolidate Ingestion Paths

**Source:** V-001, TD-001, TD-005  
**Effort:** Medium | **Risk:** Low
**Architectural Priority:** 3 | **Implementation Order:** 7
**Hard Prerequisites:** P6
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

Two parallel ingestion pipelines existed side-by-side:

1. **Legacy path** — `Librarian.ingest()` → `parse_file()` → JSON persistence (`ingestion/persistence.py`)
2. **Current path** — `CollectionWatcher` → `discover_artifact()` → PostgreSQL

`app_state.py:run_initial_scan()` used the legacy path and then duplicated entries into PostgreSQL via `save_document()`. This meant the initial scan bypassed the artifact inventory model and created double processing.

## Resolution (2026-07)

- ✅ `ingestion/librarian.py` deleted
- ✅ `ingestion/persistence.py` deleted
- ✅ `run_initial_scan()` in `app_state.py` now uses `CollectionWatcher.scan_collection()` (lines 291-324)
- ✅ All ingestion routes through `discover_artifact()` path

## Implementation Evidence

```python
# api/app_state.py:291-324
def run_initial_scan(self):
    """Run initial scan of the library in a background thread.
    
    Uses CollectionWatcher.scan_collection() — the artifact inventory path —
    so every file is discovered via PostgreSQL regardless of parser availability.
    """
    # ... now calls self.watcher.scan_collection()
```

## Definition of Done

- ✅ `run_initial_scan()` uses only the `CollectionWatcher` path.
- ✅ `ingestion/librarian.py` and `ingestion/persistence.py` deleted.
- ✅ No JSON snapshot files are written during ingestion.
- ✅ All existing tests still pass.
