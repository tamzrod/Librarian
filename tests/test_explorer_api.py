"""Tests for explorer path handling."""

from api.routes.explorer import resolve_folder_path


def test_resolve_folder_path_handles_relative_path():
    full_path, relative_path = resolve_folder_path("Camera", "/library")
    assert full_path == "/library/Camera"
    assert relative_path == "Camera"


def test_resolve_folder_path_handles_absolute_path():
    full_path, relative_path = resolve_folder_path("/library/Camera", "/library")
    assert full_path == "/library/Camera"
    assert relative_path == "Camera"


def test_resolve_folder_path_handles_url_encoded_absolute_path():
    full_path, relative_path = resolve_folder_path("%2Flibrary%2FCamera", "/library")
    assert full_path == "/library/Camera"
    assert relative_path == "Camera"


def test_resolve_folder_path_handles_root_path():
    full_path, relative_path = resolve_folder_path("/library", "/library")
    assert full_path == "/library"
    assert relative_path == ""
