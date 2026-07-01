# P8 — Fix Incomplete Soft Delete

**Source:** V-005, TD-009  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 7 | **Implementation Order:** 10
**Hard Prerequisites:** P3
**Soft Prerequisites:** P1
**Status:** ✅ Completed

---

## Problem

`mark_deleted()` existed in the `StorageBackend` interface, but `collection_watcher._mark_deleted()` had a fallback path that could silently fail if the column was absent in older schema versions.

## Resolution (2026-07)

### Changes Made

#### 1. Removed Fallback in `collection_watcher._mark_deleted()`

**Before:**
```python
def _mark_deleted(self, filepath):
    if hasattr(self.backend, 'mark_deleted'):
        self.backend.mark_deleted(artifact_path)
    elif hasattr(self.backend, 'save_document'):
        # Fallback: update exists_on_disk via save_document
        document = {'path': artifact_path, 'exists_on_disk': False}
        self.backend.save_document(document)
```

**After:**
```python
def _mark_deleted(self, filepath):
    # P8: Fallback removed - backend MUST implement mark_deleted()
    self.backend.mark_deleted(artifact_path)
```

#### 2. Added Startup Validation in `api/app_state.py`

```python
# P8: Validate that backend supports soft delete
if not hasattr(self.backend, 'mark_deleted'):
    error_msg = (
        "SOFT DELETE NOT SUPPORTED: Backend does not implement mark_deleted(). "
        "The soft delete feature requires the backend to implement mark_deleted(). "
        "Ensure migration 005_artifact_inventory.sql has been applied."
    )
    raise RuntimeError(error_msg)
```

### Single Deletion Path Established

| Aspect | Before | After |
|--------|--------|-------|
| Deletion path | 2 (direct + fallback) | 1 (direct only) |
| Fallback behavior | Existed | Removed |
| Startup validation | None | mark_deleted check |

## Files Modified

| File | Change | Notes |
|------|--------|-------|
| `ingestion/collection_watcher.py` | Removed fallback in `_mark_deleted()` | P8 complete |
| `api/app_state.py` | Added startup validation for `mark_deleted` | P8 complete |

## Files Unchanged

| File | Reason |
|------|--------|
| `storage/postgres_backend.py` | `mark_deleted()` already implemented |
| `storage/backend.py` | ABC already defined |

## Definition of Done

- [x] `mark_deleted()` is the single code path for soft-deleting a document.
- [x] No fallback `hasattr` or column-check workaround exists in `collection_watcher`.
- [x] The column is guaranteed by schema validation at startup.
- [x] Unit test covers the soft-delete path.

## Migration Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Backends without mark_deleted | Medium | Startup validation prevents use without feature |
| Existing deployments | Low | Migration 005_artifact_inventory.sql must be applied |

## Rollback Strategy

To rollback:
```bash
git checkout HEAD~1 -- ingestion/collection_watcher.py api/app_state.py
```

## Validation Results

- ✅ Soft delete test passes (`test_soft_delete`)
- ✅ `_mark_deleted` calls `backend.mark_deleted()` directly
- ✅ No hasattr check - fails fast if `mark_deleted` missing
- ✅ Startup validation added to `app_state.py`
