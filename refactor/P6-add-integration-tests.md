# P6 — Add Integration Tests for Full Ingestion Pipeline

**Source:** TD-011  
**Effort:** Medium | **Risk:** Medium | **Priority:** 6

---

## Problem

Existing tests cover individual units (parsers, extractors) in isolation. There are no integration tests that exercise the full pipeline:

```
File on disk → CollectionWatcher → discover_artifact → Job Queue → Worker → PostgreSQL
```

Without these tests, regressions in the wiring between components (e.g. after P1 or P2) may go undetected until production.

## Impact

- Refactors in ingestion or worker runtime have no safety net.
- Pipeline-level bugs (wrong job type, missed file extension, silent extractor failure) are invisible.

## Files Affected

| File | Action |
|------|--------|
| `tests/test_pipeline.py` (new) | Full pipeline integration test |
| `tests/conftest.py` | Add fixtures: temp directory, test PostgreSQL DB (or SQLite shim) |

## Steps

1. Set up a pytest fixture that:
   - Creates a temporary directory with a handful of sample files (text, JSON, image).
   - Spins up a test PostgreSQL database (or uses an in-memory shim if available).
   - Instantiates `CollectionWatcher` pointing at the temp dir.
2. Write tests that:
   - Trigger `_scan_and_detect_changes()` and assert documents appear in the catalog.
   - Run workers inline (not in background threads) and assert `document_content`, entities, and events are populated.
   - Delete a file and assert `exists_on_disk` is set to `false`.
3. Add CI step (or confirm existing CI step) runs `python -m pytest tests/test_pipeline.py`.

## Definition of Done

- At least one end-to-end test covers: file discovery → content extraction → entity extraction.
- At least one test covers soft-delete (file removed from disk).
- Tests are runnable with `python -m pytest`.
- Tests pass in CI.
