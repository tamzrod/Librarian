# P1 — Consolidate Ingestion Paths

**Source:** V-001, TD-001, TD-005  
**Effort:** Medium | **Risk:** Low | **Priority:** 1 (Highest Value)

---

## Problem

Two parallel ingestion pipelines exist side-by-side:

1. **Legacy path** — `Librarian.ingest()` → `parse_file()` → JSON persistence (`ingestion/persistence.py`)
2. **Current path** — `CollectionWatcher` → `discover_artifact()` → PostgreSQL

`app_state.py:run_initial_scan()` uses the legacy path and then duplicates entries into PostgreSQL via `save_document()`. This means the initial scan bypasses the artifact inventory model and creates double processing.

## Impact

- Initial scan does not go through `discover_artifact()`, so the inventory model is skipped.
- JSON snapshots accumulate alongside the PostgreSQL catalog with no single source of truth.
- Any bug fixed in one path is not automatically fixed in the other.

## Files Affected

| File | Action |
|------|--------|
| `ingestion/librarian.py` | Deprecate `Librarian.ingest()` |
| `ingestion/persistence.py` | Remove JSON snapshot writes |
| `api/app_state.py` | Rewrite `run_initial_scan()` to use `CollectionWatcher._scan_and_detect_changes()` |
| `ingestion/collection_watcher.py` | Verify `discover_artifact()` path handles all file types covered by legacy path |

## Steps

1. Audit what `Librarian.ingest()` does that `CollectionWatcher` does not (e.g. file-type coverage, error handling).
2. Add any missing coverage to `CollectionWatcher`.
3. Rewrite `run_initial_scan()` in `app_state.py` to call `CollectionWatcher._scan_and_detect_changes()` directly — remove the `Librarian` instantiation.
4. Remove all writes in `ingestion/persistence.py` (keep file only if it has read-back utilities that are still referenced).
5. Delete `ingestion/librarian.py` once no references remain.
6. Run the full test suite; add a smoke test that triggers initial scan and checks PostgreSQL for the discovered artifacts.

## Definition of Done

- `run_initial_scan()` uses only the `CollectionWatcher` path.
- `ingestion/librarian.py` and `ingestion/persistence.py` are deleted or contain only stubs that raise `DeprecationWarning`.
- No JSON snapshot files are written during ingestion.
- All existing tests still pass.
