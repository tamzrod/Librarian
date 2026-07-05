# P12 — Add ParserRegistry.get_supported_extensions()

**Source:** TD-012  
**Effort:** Low | **Risk:** Low
**Architectural Priority:** 12 | **Implementation Order:** 3
**Hard Prerequisites:** None
**Soft Prerequisites:** None
**Status:** ✅ Completed

---

## Problem

`ParserRegistry` in `registry/parser_registry.py` had no method to list all file extensions it supports. Callers that needed this information (e.g. UI file-type filters, documentation generators) had to inspect internal registry data structures directly.

## Resolution (2026-07)

- ✅ `get_supported_extensions() -> list[str]` method added to `ParserRegistry`
- ✅ Returns a sorted list of all registered file extensions
- ✅ Documented with docstring

## Implementation Evidence

```python
# registry/parser_registry.py:46-52
def get_supported_extensions(self) -> list[str]:
    """Return a sorted list of all file extensions registered with this registry.

    Returns:
        A sorted list of extension strings (e.g. ``[".csv", ".json", ...]``).
    """
    return sorted(self.parsers.keys())
```

## Definition of Done

- ✅ `ParserRegistry.get_supported_extensions()` is implemented and documented.
- ✅ Unit test exists and passes.
- ✅ No caller directly inspects the internal extension map.
