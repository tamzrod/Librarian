"""Tests for explorer path handling."""

import ast
from pathlib import Path


def _load_resolve_folder_path():
    source_path = Path(__file__).parent.parent / "api" / "routes" / "explorer.py"
    source = source_path.read_text(encoding="utf-8")
    module_ast = ast.parse(source)

    fn_node = next(
        node for node in module_ast.body
        if isinstance(node, ast.FunctionDef) and node.name == "resolve_folder_path"
    )

    fn_module = ast.Module(body=[fn_node], type_ignores=[])
    ast.fix_missing_locations(fn_module)

    namespace = {}
    exec("from urllib.parse import unquote", namespace)
    exec(compile(fn_module, filename=str(source_path), mode="exec"), namespace)
    return namespace["resolve_folder_path"]


resolve_folder_path = _load_resolve_folder_path()


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
