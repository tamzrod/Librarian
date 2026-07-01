"""Tests for the deprecated Librarian class.

Librarian is a no-op stub retained for backward compatibility (P1).
It will be deleted in P11 (Remove JSON Persistence Layer).
"""
import warnings

import pytest

from ingestion.librarian import Librarian


def test_librarian_constructor_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        Librarian()
    assert len(w) == 1
    assert issubclass(w[0].category, DeprecationWarning)
    assert "Librarian" in str(w[0].message)


def test_librarian_ingest_warns():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        lib = Librarian()
        lib.ingest('.')
    deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
    messages = [str(x.message) for x in deprecation_warnings]
    assert any("ingest" in m for m in messages)


def test_librarian_ingest_is_noop():
    """Calling ingest() must not raise and must leave index empty."""
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        lib = Librarian()
        lib.ingest('.')
    assert lib.index == []


def test_librarian_search_returns_empty():
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        lib = Librarian()
        result = lib.search('anything')
    assert result == []


def test_librarian_detect_changes_returns_empty():
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        lib = Librarian()
        result = lib.detect_changes('nonexistent.json')
    assert result == {"added": [], "removed": [], "modified": [], "unchanged": []}
