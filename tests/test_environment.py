import importlib
import logging

import environment


def test_get_library_root_prefers_canonical(monkeypatch, caplog):
    monkeypatch.setenv("LIBRARIAN_LIBRARY_ROOT", "/canonical")
    monkeypatch.setenv("LIBRARY_ROOT", "/deprecated")

    caplog.set_level(logging.WARNING)

    assert environment.get_library_root() == "/canonical"
    assert "deprecated; use LIBRARIAN_LIBRARY_ROOT instead." not in caplog.text


def test_get_library_root_supports_deprecated_alias(monkeypatch, caplog):
    monkeypatch.delenv("LIBRARIAN_LIBRARY_ROOT", raising=False)
    monkeypatch.setenv("LIBRARY_ROOT", "/legacy")

    caplog.set_level(logging.WARNING)

    assert environment.get_library_root() == "/legacy"
    assert "LIBRARY_ROOT is deprecated; use LIBRARIAN_LIBRARY_ROOT instead." in caplog.text


def test_get_api_url_supports_deprecated_alias(monkeypatch, caplog):
    monkeypatch.delenv("LIBRARIAN_API_URL", raising=False)
    monkeypatch.setenv("API_URL", "http://legacy:8000")

    caplog.set_level(logging.WARNING)

    assert environment.get_api_url() == "http://legacy:8000"
    assert "API_URL is deprecated; use LIBRARIAN_API_URL instead." in caplog.text


def test_deprecation_warning_emitted_once(monkeypatch, caplog):
    module = importlib.reload(environment)
    monkeypatch.delenv("LIBRARIAN_LIBRARY_ROOT", raising=False)
    monkeypatch.setenv("LIBRARY_ROOT", "/legacy")

    caplog.set_level(logging.WARNING)

    assert module.get_library_root() == "/legacy"
    assert module.get_library_root() == "/legacy"
    assert caplog.text.count("LIBRARY_ROOT is deprecated; use LIBRARIAN_LIBRARY_ROOT instead.") == 1
