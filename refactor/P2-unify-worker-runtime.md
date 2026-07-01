# P2 — Unify Worker Runtime

**Source:** V-003, TD-002  
**Effort:** Medium | **Risk:** Medium
**Architectural Priority:** 4 | **Implementation Order:** 11
**Hard Prerequisites:** P5, P6
**Soft Prerequisites:** None
**Status:** ⚠️ Partially Complete

---

## Problem

`BackgroundJobProcessor` in `api/app_state.py` and `Worker` in `workers/worker.py` independently implement near-identical logic:

- Lease management (`claim_job`, `renew_lease`)
- Job claiming loop
- Handler registration
- Retry / exponential backoff
- Graceful shutdown

Neither was designated as the canonical implementation, so bug fixes and improvements are applied inconsistently.

## Resolution Progress (2026-07)

### Completed
- ✅ P5 (Worker Abstract Base) completed — all workers now inherit from `BaseWorker` and implement `process(job)` uniformly
- ✅ Handler registration unified through `BaseWorker.process()` method

### Remaining Work
- 🔴 Both `BackgroundJobProcessor` and `Worker` still exist independently
- 🔴 No `WorkerRuntime` ABC/Protocol defined yet
- 🔴 No canonical implementation designated
- 🔴 Duplicate code still exists

## Current State

Both implementations exist and use the same handler registration pattern:

```python
# BackgroundJobProcessor (app_state.py)
self.job_processor.register_handler(
    'extract_text', 
    ContentExtractor(self.backend, library_root).process
)

# Worker (workers/worker.py)  
worker.register_handler('extract_text', ContentExtractor(backend).process)
```

## Files Affected

| File | Action | Status |
|------|--------|--------|
| `api/app_state.py` | Remove or delegate `BackgroundJobProcessor` | 🔴 Pending |
| `workers/worker.py` | Promote to canonical `WorkerRuntime` | 🔴 Pending |
| `workers/*.py` | No changes expected | ✅ Done |

## Definition of Done

- [ ] One implementation of the job-processing loop exists.
- [ ] `WorkerRuntime` ABC/Protocol is defined with `register_handler`, `start`, and `stop` methods.
- [ ] All existing tests pass.
- [ ] A brief comment in the canonical file explains why the old duplicate was removed.
