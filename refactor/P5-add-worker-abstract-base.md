# P5 — Add Worker Abstract Base

**Source:** V-004, TD-004  
**Effort:** Low | **Risk:** Low | **Priority:** 5

---

## Problem

Worker classes (`ContentExtractor`, `EntityExtractor`, `LocationExtractor`, etc.) in `workers/` share no common interface. Each exposes a different method signature (`extract_content`, `extract_entities`, etc.). The `run_worker()` function instantiates each class directly and retrieves the method as a bound callable by name — a fragile pattern that breaks silently if a worker renames its method.

## Impact

- Adding a new worker requires knowing the undocumented naming convention.
- Refactoring a method name on any extractor silently breaks handler registration.
- No static analysis catches a missing or mis-named method.

## Files Affected

| File | Action |
|------|--------|
| `workers/base.py` (new) | Define `BaseWorker` ABC or `Protocol` |
| `workers/content_extractor.py` | Implement `BaseWorker` |
| `workers/entity_extractor.py` | Implement `BaseWorker` |
| `workers/event_extractor.py` | Implement `BaseWorker` |
| `workers/location_extractor.py` | Implement `BaseWorker` |
| `workers/worker.py` | Update handler registration to use `BaseWorker.process()` |

## Steps

1. Define `BaseWorker` in `workers/base.py` with a single required method: `process(job: dict) -> None`.
2. Have every extractor class inherit from `BaseWorker` and rename its entry-point method to `process`.
3. Update `run_worker()` (or `WorkerRuntime` after P2) to call `worker.process(job)` instead of looking up a method by string.
4. Delete any now-unused method aliases.
5. Run the test suite to confirm nothing broke.

## Definition of Done

- `BaseWorker` ABC exists with `@abstractmethod process(job)`.
- All extractors implement `process`.
- `run_worker` / `WorkerRuntime` calls `worker.process(job)` uniformly.
- All existing tests pass.
