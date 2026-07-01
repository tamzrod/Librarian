# P3 — Enforce Backend Interface

**Source:** V-007, TD-003  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 2 | **Implementation Order:** 4
**Hard Prerequisites:** None
**Soft Prerequisites:** None

---

## Problem

`EvidenceBuilder` in `evidence/evidence_builder.py` uses `hasattr` duck-typing to call backend methods:

```python
if hasattr(self.backend, 'search_documents'):
    return self.backend.search_documents(query) or []
return []
```

This silently swallows missing interface implementations instead of surfacing them early. If a backend forgets to implement a method, queries return empty results with no error.

## Impact

- Silent failures that are hard to diagnose.
- No compile-time or startup-time guarantee that the backend is complete.
- Masks interface violations from the `StorageBackend` ABC.

## Files Affected

| File | Action |
|------|--------|
| `storage/backend.py` | Add `@abstractmethod` decorators to all required methods |
| `evidence/evidence_builder.py` | Replace `hasattr` checks with direct calls |
| `storage/postgres_backend.py` | Verify all abstract methods are implemented |

## Steps

1. Audit `storage/backend.py` — identify every method that should be required.
2. Decorate each required method with `@abstractmethod` (convert `StorageBackend` to an ABC if not already one).
3. In `evidence/evidence_builder.py`, remove all `hasattr` guards and call backend methods directly.
4. Run tests — any `NotImplementedError` raised now points to a real gap.
5. Implement any missing methods in `storage/postgres_backend.py`.
6. Add a startup assertion (or a Protocol `runtime_checkable`) that verifies the configured backend at application start.

## Definition of Done

- `StorageBackend` is a proper ABC with `@abstractmethod` on every required method.
- `EvidenceBuilder` contains no `hasattr` checks.
- All existing tests pass.
- Instantiating a partial backend raises `TypeError` immediately.
