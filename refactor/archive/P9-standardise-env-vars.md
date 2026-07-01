# P9 — Standardise Environment Variable Naming

**Source:** V-006, TD-010  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 10 | **Implementation Order:** 1
**Hard Prerequisites:** None
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

`LIBRARY_ROOT = "/library"` was hardcoded in `api/app.py` and `api/app_state.py`, with an environment variable override whose name (`LIBRARIAN_LIBRARY_ROOT`) was inconsistent with other env vars used elsewhere in the codebase.

## Resolution (2026-07)

- ✅ Environment variables centralized in `environment.py`
- ✅ `LIBRARIAN_LIBRARY_ROOT` is canonical with `LIBRARY_ROOT` as deprecated alias
- ✅ Startup logging of library root in `api/app.py` (line 37): `logger.info("Library root: %s", LIBRARY_ROOT)`
- ✅ Deprecation warnings for legacy aliases via `_warn_deprecated_alias()`

## Implementation Evidence

```python
# environment.py — centralized env var handling
def get_library_root(default: str = DEFAULT_LIBRARY_ROOT) -> str:
    return get_env(
        "LIBRARIAN_LIBRARY_ROOT",
        aliases=("LIBRARY_ROOT",),
        default=default,
    ) or default

def _warn_deprecated_alias(alias: str, canonical_name: str) -> None:
    """Warn once when a deprecated alias is used."""
    logger.warning(
        "Environment variable %s is deprecated; use %s instead.",
        alias,
        canonical_name,
    )
```

## Definition of Done

- ✅ All environment variables follow a consistent `LIBRARIAN_` naming convention.
- ✅ Startup logs the resolved `LIBRARY_ROOT`.
- ✅ `README.md` documents all supported env vars.
- ✅ No duplicate hardcoded defaults exist across files.
