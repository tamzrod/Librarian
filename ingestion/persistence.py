"""Deprecated JSON persistence utilities.

Write functions are no-op stubs; documents are now persisted via PostgresBackend.
Read functions are kept temporarily for backward compatibility.

This file will be deleted in P11 (Remove JSON Persistence Layer).
"""
import json
import warnings


def save_index(index, filename):
    """Deprecated: documents are now persisted via PostgresBackend."""
    warnings.warn(
        "save_index() is deprecated. Documents are persisted via PostgresBackend.",
        DeprecationWarning,
        stacklevel=2,
    )


def load_index(filename):
    """Deprecated: documents are now retrieved via PostgresBackend."""
    warnings.warn(
        "load_index() is deprecated. Documents are retrieved via PostgresBackend.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_snapshot(scan_results, filename):
    """Deprecated: scan snapshots are now stored in PostgreSQL."""
    warnings.warn(
        "save_snapshot() is deprecated. Scan snapshots are stored in PostgreSQL.",
        DeprecationWarning,
        stacklevel=2,
    )


def load_snapshot(filename):
    """Deprecated: scan snapshots are now retrieved from PostgreSQL."""
    warnings.warn(
        "load_snapshot() is deprecated. Scan snapshots are retrieved from PostgreSQL.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print('Snapshot file not found.')
        return []
    except json.JSONDecodeError:
        print('Error decoding JSON from snapshot file.')
        return []
    except Exception as e:
        print(f'Error loading snapshot: {e}')
        return []

