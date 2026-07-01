# P4 — Replace AppState Singleton with Dependency Injection

**Source:** V-002, TD-008  
**Effort:** High | **Risk:** Medium | **Priority:** 4

---

## Problem

`AppState` in `api/app_state.py` is a global singleton (`_state`) accessed through module-level functions. Every route and component imports and calls these module-level helpers, creating hidden global state.

This pattern:
- Makes unit-testing individual routes impossible without patching global state.
- Prevents running multiple library instances in one process.
- Couples every component to the same backend instance.
- Prevents horizontal scaling (each process has its own global state).

## Impact

- Testing requires monkey-patching or replacing the global.
- Multi-library deployments are architecturally impossible today.
- Tight coupling makes future migrations (e.g. swap PostgreSQL for another backend) riskier.

## Files Affected

| File | Action |
|------|--------|
| `api/app_state.py` | Remove `_state` global; make `AppState` a regular class |
| `api/app.py` | Instantiate `AppState` once; register as FastAPI dependency |
| `api/routes/*.py` | Replace module-level helper calls with `Depends(get_app_state)` |
| `tests/` | Update fixtures to inject a fresh `AppState` per test |

## Steps

1. Remove the module-level `_state` variable and all module-level accessor functions.
2. Make `AppState` a plain instantiable class with no global side effects on import.
3. In `app.py`, create the single `AppState` instance during application startup (`lifespan` context).
4. Add a FastAPI dependency function `get_app_state()` that returns the instance.
5. Update every route to accept `app_state: AppState = Depends(get_app_state)` instead of importing the global.
6. Update tests to create a fresh `AppState` (backed by a test database) injected via dependency override.
7. Remove any remaining imports of the old module-level helpers.

## Definition of Done

- No module-level `_state` variable exists.
- All routes use `Depends(get_app_state)`.
- Tests inject a test `AppState` without patching globals.
- All existing tests pass.
- Two parallel `AppState` instances can be created in the same process without interference.
