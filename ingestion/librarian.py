"""Deprecated ingestion engine.

This module is retained temporarily for backward compatibility.
All ingestion now uses CollectionWatcher.scan_collection() via the
artifact inventory model (PostgreSQL).

This file will be deleted in P11 (Remove JSON Persistence Layer).
"""
import warnings


class Librarian:
    """Deprecated: use CollectionWatcher for ingestion.

    This class is a no-op stub retained only to avoid immediate import errors
    during the transition to the artifact inventory model. It will be removed
    in P11.
    """

    def __init__(self):
        warnings.warn(
            "Librarian is deprecated. Use CollectionWatcher.scan_collection() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.index = []

    def ingest(self, path, persist_path=None):
        warnings.warn(
            "Librarian.ingest() is deprecated. Use CollectionWatcher.scan_collection() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def load_index(self, filename):
        warnings.warn(
            "Librarian.load_index() is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )

    def search(self, query):
        warnings.warn(
            "Librarian.search() is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )
        return []

    def get_dependencies(self, file_path):
        warnings.warn(
            "Librarian.get_dependencies() is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )
        return []

    def detect_changes(self, previous_index_path, current_index=None):
        warnings.warn(
            "Librarian.detect_changes() is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )
        return {"added": [], "removed": [], "modified": [], "unchanged": []}
