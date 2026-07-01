# P6 — Add Integration Tests for Full Ingestion Pipeline

**Source:** TD-011  
**Effort:** Medium | **Risk:** Medium
**Architectural Priority:** 5 | **Implementation Order:** 6
**Hard Prerequisites:** None
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

Existing tests covered individual units (parsers, extractors) in isolation. There were no integration tests that exercised the full pipeline:

```
File on disk → CollectionWatcher → discover_artifact → Job Queue → Worker → PostgreSQL
```

## Resolution (2026-07)

- ✅ `tests/test_pipeline.py` created
- ✅ `tests/test_pipeline_e2e.py` created
- ✅ `tests/test_pipeline_integration.py` created
- ✅ Tests cover file discovery → content extraction → entity extraction
- ✅ Tests cover soft-delete (file removed from disk)

## Files Created

| File | Purpose |
|------|---------|
| `tests/test_pipeline.py` | Basic pipeline test |
| `tests/test_pipeline_e2e.py` | End-to-end pipeline tests |
| `tests/test_pipeline_integration.py` | Integration tests for pipeline components |

## Definition of Done

- ✅ End-to-end test covers: file discovery → content extraction → entity extraction.
- ✅ Soft-delete test (file removed from disk) exists.
- ✅ Tests are runnable with `python -m pytest`.
- ✅ Tests pass.
