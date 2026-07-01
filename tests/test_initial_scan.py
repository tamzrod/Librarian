"""Smoke tests for initial scan via CollectionWatcher.

P1: Verifies that the initial scan uses the CollectionWatcher artifact inventory
path (discover_artifact → PostgreSQL) rather than the legacy Librarian/JSON path.
"""
import tempfile
from pathlib import Path

from ingestion.collection_watcher import CollectionWatcher


class _MockBackend:
    def __init__(self):
        self.artifacts = {}
        self.job_calls = []

    def discover_artifact(self, path, extension=None, file_size=None, modified_time=None, mime_type=None):
        doc_id = len(self.artifacts) + 1
        self.artifacts[path] = {
            'id': doc_id,
            'path': path,
            'extension': extension,
            'file_size': file_size,
            'modified_time': modified_time,
            'status': 'DISCOVERED',
            'mime_type': mime_type,
        }
        return doc_id

    def create_jobs_for_document(self, doc_id, **kwargs):
        self.job_calls.append(doc_id)
        return [1]


class _MockParserRegistry:
    def get_parser(self, filepath):
        return None

    def get_artifact_type(self, filepath):
        return 'unknown'


def test_initial_scan_discovers_all_files():
    """scan_collection() discovers every file as an artifact in the backend."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library = Path(tmpdir) / "library"
        library.mkdir()

        (library / "document.txt").write_text("Hello world")
        (library / "photo.jpg").write_bytes(b"fake-jpeg")
        sub = library / "subdir"
        sub.mkdir()
        (sub / "notes.md").write_text("# Notes")

        backend = _MockBackend()
        watcher = CollectionWatcher(str(library), backend, _MockParserRegistry())

        stats = watcher.scan_collection()

        assert stats['errors'] == 0, f"Unexpected scan errors: {stats}"
        artifact_paths = list(backend.artifacts.keys())
        assert len(artifact_paths) == 3, f"Expected 3 artifacts, got {artifact_paths}"
        assert any("document.txt" in p for p in artifact_paths)
        assert any("photo.jpg" in p for p in artifact_paths)
        assert any("notes.md" in p for p in artifact_paths)


def test_initial_scan_skips_hidden_directories():
    """scan_collection() does not descend into hidden directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library = Path(tmpdir) / "library"
        library.mkdir()

        (library / "visible.txt").write_text("visible")
        hidden = library / ".hidden"
        hidden.mkdir()
        (hidden / "secret.txt").write_text("should not be discovered")

        backend = _MockBackend()
        watcher = CollectionWatcher(str(library), backend, _MockParserRegistry())

        watcher.scan_collection()

        paths = list(backend.artifacts.keys())
        assert len(paths) == 1, f"Expected only 1 artifact, got {paths}"
        assert any("visible.txt" in p for p in paths)


def test_initial_scan_skips_system_directories():
    """scan_collection() does not descend into __pycache__, .venv, node_modules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library = Path(tmpdir) / "library"
        library.mkdir()

        (library / "real_doc.txt").write_text("real content")

        for sysdir in ("__pycache__", ".venv", "node_modules"):
            d = library / sysdir
            d.mkdir()
            (d / "sys_file.txt").write_text("should not be discovered")

        backend = _MockBackend()
        watcher = CollectionWatcher(str(library), backend, _MockParserRegistry())

        watcher.scan_collection()

        paths = list(backend.artifacts.keys())
        assert len(paths) == 1, f"Expected only 1 artifact, got {paths}"
        assert any("real_doc.txt" in p for p in paths)


def test_initial_scan_skips_hidden_files():
    """scan_collection() does not process files whose name starts with '.'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library = Path(tmpdir) / "library"
        library.mkdir()

        (library / "readable.txt").write_text("content")
        (library / ".gitignore").write_text("*.pyc")

        backend = _MockBackend()
        watcher = CollectionWatcher(str(library), backend, _MockParserRegistry())

        watcher.scan_collection()

        paths = list(backend.artifacts.keys())
        assert len(paths) == 1, f"Expected only readable.txt, got {paths}"
        assert any("readable.txt" in p for p in paths)
