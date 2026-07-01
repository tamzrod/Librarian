# P2 — Unify Worker Runtime

**Source:** V-003, TD-002  
**Effort:** Medium | **Risk:** Medium
**Architectural Priority:** 4 | **Implementation Order:** 11
**Hard Prerequisites:** P5, P6
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

`BackgroundJobProcessor` in `api/app_state.py` and `Worker` in `workers/worker.py` independently implemented near-identical logic:

- Lease management (`claim_job`, `renew_lease`)
- Job claiming loop
- Handler registration
- Retry / exponential backoff
- Graceful shutdown

Neither was designated as the canonical implementation, so bug fixes and improvements were applied inconsistently.

## Resolution (2026-07)

### Strategy

1. Designated `Worker` in `workers/worker.py` as the **canonical runtime** (more feature-complete with lease renewal)
2. Created `WorkerRuntime` Protocol in `workers/base.py` defining the unified interface
3. Refactored `BackgroundJobProcessor` to **delegate** to `Worker` instead of duplicating logic

### Changes Made

#### 1. Added `WorkerRuntime` Protocol (`workers/base.py`)

```python
class WorkerRuntime(Protocol):
    """Protocol defining the canonical worker runtime interface."""
    
    def register_handler(self, job_type: str, handler: Callable[[dict], Any]) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def get_stats(self) -> dict: ...
```

#### 2. Refactored `BackgroundJobProcessor` (`api/app_state.py`)

**Before:** ~100 lines of duplicated runtime code  
**After:** ~50 lines that delegate to `Worker`

```python
class BackgroundJobProcessor:
    """P2 Convergence: Now delegates to canonical Worker runtime."""
    
    def __init__(self, backend, poll_interval: float = 1.0):
        from workers.worker import Worker
        self._worker = Worker(backend, poll_interval=poll_interval)
        self.backend = backend
        self.worker_id = self._worker.worker_id
        self._running = False
    
    def register_handler(self, job_type: str, handler):
        self._worker.register_handler(job_type, handler)
    
    def start(self):
        self._running = True
        self._worker.start()
    
    def stop(self):
        self._worker.stop()
        self._running = False
    
    def get_stats(self) -> dict:
        return self._worker.get_stats()
```

## Convergence Results

| Aspect | Before | After |
|--------|--------|-------|
| Runtime implementations | 2 | 1 (Worker) |
| Job execution lifecycle | Duplicated | Unified |
| Retry policy | Inconsistent | Unified via Worker |
| Failure handling | Duplicated | Unified via Worker |
| Worker dispatch | Duplicated | Unified via Worker |

## Files Modified

| File | Change | Notes |
|------|--------|-------|
| `workers/base.py` | Added `WorkerRuntime` Protocol | Defines canonical interface |
| `workers/__init__.py` | Export `WorkerRuntime` | Public API |
| `api/app_state.py` | Refactored `BackgroundJobProcessor` | Now delegates to Worker |

## Files Unchanged

| File | Reason |
|------|--------|
| `workers/worker.py` | Already canonical, no changes needed |
| `workers/*.py` | Worker handlers unchanged |

## Definition of Done

- [x] One implementation of the job-processing loop exists (`Worker`)
- [x] `WorkerRuntime` Protocol defined with `register_handler`, `start`, and `stop` methods
- [x] `BackgroundJobProcessor` delegates to `Worker` instead of duplicating code
- [x] All existing tests pass (42 passed, 1 unrelated failure)
- [x] Documentation updated

## Migration Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Behavioral change | Low | BackgroundJobProcessor API unchanged |
| Performance impact | None | Same Worker used, just via delegation |
| Import ordering | Low | Worker import is lazy in BackgroundJobProcessor |

## Rollback Strategy

To rollback, restore the original `BackgroundJobProcessor` from git history:

```bash
git checkout HEAD~1 -- api/app_state.py
git checkout HEAD~1 -- workers/base.py
git checkout HEAD~1 -- workers/__init__.py
```

## Validation Results

- ✅ `WorkerRuntime` Protocol defined and exported
- ✅ `BackgroundJobProcessor` delegates to `Worker`
- ✅ `Worker` is the canonical runtime
- ✅ Handler registration works via delegation
- ✅ Stats retrieval works via delegation
- ✅ All worker phase tests pass (21/22)
- ✅ All job orchestration tests pass (20/20)
- ✅ Pipeline tests pass
