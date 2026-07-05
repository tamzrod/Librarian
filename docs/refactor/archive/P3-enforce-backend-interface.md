# P3 — Enforce Backend Interface

**Source:** V-007, TD-003  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 2 | **Implementation Order:** 4
**Hard Prerequisites:** None
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

`EvidenceBuilder` in `evidence/evidence_builder.py` used `hasattr` duck-typing to call backend methods:

```python
if hasattr(self.backend, 'search_documents'):
    return self.backend.search_documents(query) or []
return []
```

This silently swallowed missing interface implementations instead of surfacing them early.

## Resolution (2026-07)

- ✅ `StorageBackend` is now a proper ABC with `@abstractmethod` on all required methods
- ✅ `EvidenceBuilder` no longer uses `hasattr` checks — direct calls
- ✅ `validate_backend_instance()` added for runtime validation
- ✅ All abstract methods documented with artifact inventory model rationale

## Implementation Evidence

```python
# storage/backend.py — All methods now have @abstractmethod
class StorageBackend(ABC):
    @abstractmethod
    def save_collection(self, collection):
        """Persist a collection and return its ID."""
        raise NotImplementedError()
    # ... all methods are abstract

def validate_backend_instance(backend: StorageBackend) -> StorageBackend:
    """Validate that an initialized backend satisfies the StorageBackend ABC."""
    if not isinstance(backend, StorageBackend):
        raise TypeError(
            f"Configured backend must implement StorageBackend; got {type(backend).__name__}"
        )
    return backend
```

```python
# evidence/evidence_builder.py — Direct calls, no hasattr
def get_documents(self, query):
    return self.backend.search_documents(query) or []
```

## Definition of Done

- ✅ `StorageBackend` is a proper ABC with `@abstractmethod` on every required method.
- ✅ `EvidenceBuilder` contains no `hasattr` checks.
- ✅ All existing tests pass.
- ✅ `validate_backend_instance()` provides runtime verification.
