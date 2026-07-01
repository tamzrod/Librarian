"""Unit tests for ParserRegistry."""

import pytest
from registry.parser_registry import ParserRegistry


class TestGetSupportedExtensions:
    """Tests for ParserRegistry.get_supported_extensions()."""

    def test_empty_registry_returns_empty_list(self):
        registry = ParserRegistry()
        assert registry.get_supported_extensions() == []

    def test_returns_registered_extensions(self):
        registry = ParserRegistry()
        registry.register(".csv", object())
        registry.register(".json", object())
        registry.register(".txt", object())
        assert registry.get_supported_extensions() == [".csv", ".json", ".txt"]

    def test_returns_sorted_list(self):
        registry = ParserRegistry()
        registry.register(".xml", object())
        registry.register(".csv", object())
        registry.register(".json", object())
        result = registry.get_supported_extensions()
        assert result == sorted(result)

    def test_single_extension(self):
        registry = ParserRegistry()
        registry.register(".pdf", object())
        assert registry.get_supported_extensions() == [".pdf"]

    def test_overwrite_does_not_duplicate(self):
        registry = ParserRegistry()
        parser_a = object()
        parser_b = object()
        registry.register(".csv", parser_a)
        registry.register(".csv", parser_b)
        assert registry.get_supported_extensions() == [".csv"]

    def test_register_with_artifact_type_included(self):
        registry = ParserRegistry()
        registry.register_with_artifact_type(".ini", object(), "text")
        assert registry.get_supported_extensions() == [".ini"]

    def test_returns_list_type(self):
        registry = ParserRegistry()
        registry.register(".yaml", object())
        result = registry.get_supported_extensions()
        assert isinstance(result, list)
