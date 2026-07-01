# P8 — Fix Incomplete Soft Delete

**Source:** V-005, TD-009  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 7 | **Implementation Order:** 10
**Hard Prerequisites:** P3
**Soft Prerequisites:** P1
**Status:** ⚠️ Partially Complete

---

## Problem

`mark_deleted()` exists in the `StorageBackend` interface, but the implementation in `collection_watcher._mark_deleted()` has a fallback path that sets `exists_on_disk` directly — which silently does nothing if the column is absent in older schema versions.

## Resolution Progress (2026-07)

### Completed
- ✅ `mark_deleted()` is defined in `StorageBackend` ABC with docstring and artifact inventory rationale
- ✅ P3 prerequisite completed — backend interface enforced

### Remaining Work
- 🔴 Fallback still exists in `collection_watcher._mark_deleted()` (lines 238-249):
  ```python
  if hasattr(self.backend, 'mark_deleted'):
      self.backend.mark_deleted(artifact_path)
  elif hasattr(self.backend, 'save_document'):
      # Fallback: update exists_on_disk via save_document
      ...
  ```
- 🔴 No startup validation of `exists_on_disk` column

## Files Affected

| File | Action | Status |
|------|--------|--------|
| `storage/postgres_backend.py` | Verify/complete `mark_deleted()` implementation | ✅ Done |
| `ingestion/collection_watcher.py` | Remove fallback; use `mark_deleted()` exclusively | 🔴 Pending |
| `api/app_state.py` | Add startup assertion that `exists_on_disk` column exists | 🔴 Pending |

## Definition of Done

- [ ] `mark_deleted()` is the single code path for soft-deleting a document.
- [ ] No fallback `hasattr` or column-check workaround exists in `collection_watcher`.
- [ ] The column is guaranteed by schema validation at startup.
- [ ] Unit test covers the soft-delete path.
