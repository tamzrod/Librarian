# P8 — Fix Incomplete Soft Delete

**Source:** V-005, TD-009  
**Effort:** Low | **Risk:** Low | **Priority:** 8

---

## Problem

`mark_deleted()` exists in the `StorageBackend` interface, but the implementation in `collection_watcher._mark_deleted()` has a fallback path that sets `exists_on_disk` directly — which silently does nothing if the column is absent in older schema versions.

## Impact

- Deleted file tracking may fail silently on older database schemas.
- Audit trail for deleted files may be incomplete.

## Files Affected

| File | Action |
|------|--------|
| `storage/postgres_backend.py` | Verify/complete `mark_deleted()` implementation |
| `ingestion/collection_watcher.py` | Remove fallback; use `mark_deleted()` exclusively |
| `api/app_state.py` | Add startup assertion that `exists_on_disk` column exists |

## Steps

1. Confirm `exists_on_disk` column is present in all supported schema versions (check migration history).
2. If any migration is missing the column addition, add it in a new migration.
3. Remove the fallback in `collection_watcher._mark_deleted()` — call `self.backend.mark_deleted(document_id)` only.
4. Add a startup check (or schema validation step) that asserts the column exists before the watcher starts.
5. Write a unit test: create a document, delete the file, trigger the watcher, assert `exists_on_disk = false` and `deleted_at` is set.

## Definition of Done

- `mark_deleted()` is the single code path for soft-deleting a document.
- No fallback `hasattr` or column-check workaround exists in `collection_watcher`.
- The column is guaranteed by schema validation at startup.
- Unit test covers the soft-delete path.
