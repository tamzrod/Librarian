# P9 — Standardise Environment Variable Naming

**Source:** V-006, TD-010  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 10 | **Implementation Order:** 1
**Hard Prerequisites:** None
**Soft Prerequisites:** None

---

## Problem

`LIBRARY_ROOT = "/library"` is hardcoded in `api/app.py` and `api/app_state.py`, with an environment variable override whose name (`LIBRARIAN_LIBRARY_ROOT`) may be inconsistent with other env vars used elsewhere in the codebase.

## Impact

- Deployment documentation may reference the wrong variable name.
- Operators who set the wrong variable get the hardcoded default with no warning.

## Files Affected

| File | Action |
|------|--------|
| `api/app.py` | Centralise env var reading; log the resolved path on startup |
| `api/app_state.py` | Remove duplicate hardcoded default; import from `app.py` |
| `README.md` / `docs/` | Update to document the canonical env var name |

## Steps

1. Audit all env var names used across `api/` (`grep -r "os.environ\|os.getenv" api/`).
2. Decide on a single naming convention (e.g. `LIBRARIAN_` prefix for all vars).
3. Rename any inconsistent vars; update all call sites.
4. Add a startup log line: `logger.info("Library root: %s", LIBRARY_ROOT)`.
5. Update `README.md` with the canonical env var list.

## Definition of Done

- All environment variables follow a consistent naming convention.
- Startup logs the resolved `LIBRARY_ROOT`.
- `README.md` documents all supported env vars.
- No duplicate hardcoded defaults exist across files.
