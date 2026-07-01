# P12 — Add ParserRegistry.get_supported_extensions()

**Source:** TD-012  
**Effort:** Low | **Risk:** Low | **Priority:** 12

---

## Problem

`ParserRegistry` in `registry/parser_registry.py` has no method to list all file extensions it supports. Callers that need this information (e.g. UI file-type filters, documentation generators) must inspect internal registry data structures directly.

## Impact

- External code has to know internal implementation details of the registry.
- If the internal data structure changes, callers silently break.

## Files Affected

| File | Action |
|------|--------|
| `registry/parser_registry.py` | Add `get_supported_extensions() -> list[str]` method |

## Steps

1. Add `get_supported_extensions() -> list[str]` to `ParserRegistry` that returns a sorted list of all registered file extensions (e.g. `[".csv", ".ini", ".json", ...]`).
2. Add a unit test that registers a few parsers and asserts the method returns the correct extensions.
3. Search for any existing callers that inspect registry internals to list extensions, and update them to use the new method.

## Definition of Done

- `ParserRegistry.get_supported_extensions()` is implemented and documented.
- Unit test exists and passes.
- No caller directly inspects the internal extension map.
