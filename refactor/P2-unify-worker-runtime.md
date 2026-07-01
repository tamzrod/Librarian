# P2 — Unify Worker Runtime

**Source:** V-003, TD-002  
**Effort:** Medium | **Risk:** Medium
**Architectural Priority:** 4 | **Implementation Order:** 11
**Hard Prerequisites:** P5, P6
**Soft Prerequisites:** None

---

## Problem

`BackgroundJobProcessor` in `api/app_state.py` and `Worker` in `workers/worker.py` independently implement near-identical logic:

- Lease management (`claim_job`, `renew_lease`)
- Job claiming loop
- Handler registration
- Retry / exponential backoff
- Graceful shutdown

Neither is designated as the canonical implementation, so bug fixes and improvements are applied inconsistently.

## Impact

- Duplicate code that diverges silently over time.
- Any change to job retry semantics must be made in two places.
- Unclear which implementation runs in production vs. testing.

## Files Affected

| File | Action |
|------|--------|
| `api/app_state.py` | Remove or delegate `BackgroundJobProcessor` |
| `workers/worker.py` | Promote to canonical `WorkerRuntime` |
| `workers/*.py` | No changes expected; handler registration interface stays the same |

## Steps

1. Compare `BackgroundJobProcessor` and `Worker` method-by-method; document any behavioural differences.
2. Decide on canonical implementation:
   - **Option A:** Make `BackgroundJobProcessor` a thin wrapper that instantiates and delegates to `Worker`.
   - **Option B:** Deprecate standalone `Worker` and fold its logic into `BackgroundJobProcessor` renamed to `WorkerRuntime`.
3. Extract a `WorkerRuntime` ABC or `Protocol` that both honour (lease management, handler registration, start/stop).
4. Migrate all call sites to use the chosen canonical class.
5. Delete the non-canonical implementation.
6. Add unit tests that cover the lease renewal and retry paths.

## Definition of Done

- One implementation of the job-processing loop exists.
- `WorkerRuntime` ABC/Protocol is defined with `register_handler`, `start`, and `stop` methods.
- All existing tests pass.
- A brief comment in the canonical file explains why the old duplicate was removed.
