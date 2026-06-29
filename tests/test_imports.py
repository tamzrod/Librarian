"""Import validation tests for FastAPI endpoints.

This test module validates that all FastAPI symbols used in the API are
properly imported. It catches import errors before they cause runtime
failures in deployed containers.

Run: pytest tests/test_imports.py -v
"""

import ast
import os
import re
from pathlib import Path
from typing import Set, Tuple


# FastAPI symbols that are commonly used in route definitions
FASTMPI_COMMON_SYMBOLS = {
    # Request parameter types
    "Body",
    "Form",
    "Path",
    "Query",
    "Header",
    "Cookie",
    # Core types
    "Depends",
    "BackgroundTasks",
    "HTTPException",
    # Responses
    "Response",
    "StreamingResponse",
    # Request/Response objects
    "Request",
    "status",
    # Router
    "APIRouter",
    # Application
    "FastAPI",
}

# Files to check for FastAPI imports and usage
API_FILES = [
    "api/app.py",
    "api/routes/questions.py",
    "api/routes/collections.py",
    "api/routes/operations.py",
    "api/routes/pipeline.py",
]


def extract_fastapi_imports(filepath: str) -> Set[str]:
    """Extract FastAPI imports from a Python file.
    
    Returns a set of imported symbols from fastapi.
    """
    imports = set()
    try:
        with open(filepath, "r") as f:
            content = f.read()
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            # Handle: from fastapi import A, B, C
            if isinstance(node, ast.ImportFrom):
                if node.module == "fastapi":
                    for alias in node.names:
                        imports.add(alias.name)
    except (FileNotFoundError, SyntaxError):
        pass
    
    return imports


def find_used_fastapi_symbols(filepath: str) -> Set[str]:
    """Find all FastAPI symbols used in a Python file.
    
    Detects usage of Body(), Query(), Path(), Depends(), etc.
    """
    used = set()
    try:
        with open(filepath, "r") as f:
            content = f.read()
        
        # Symbol name -> (regex pattern to detect usage)
        patterns = {
            "Body": r'\bBody\s*\(',
            "Form": r'\bForm\s*\(',
            "Path": r'\bPath\s*\(',
            "Query": r'\bQuery\s*\(',
            "Header": r'\bHeader\s*\(',
            "Cookie": r'\bCookie\s*\(',
            "Depends": r'\bDepends\s*\(',
            "BackgroundTasks": r'\bBackgroundTasks\s*\(',
            "HTTPException": r'\bHTTPException\s*[\(=]',
            "Response": r'\bResponse\s*\(',
            "StreamingResponse": r'\bStreamingResponse\s*\(',
            "APIRouter": r'\bAPIRouter\s*\(',
            "status": r'\bstatus\.HTTP_\d+',  # Only FastAPI status constants
        }
        
        for symbol, pattern in patterns.items():
            if re.search(pattern, content):
                used.add(symbol)
                
    except FileNotFoundError:
        pass
    
    return used


def test_fastapi_imports_in_api_app():
    """Test that all FastAPI symbols used in api/app.py are imported."""
    filepath = "api/app.py"
    imported = extract_fastapi_imports(filepath)
    used = find_used_fastapi_symbols(filepath)
    
    missing = used - imported
    assert not missing, (
        f"FastAPI symbols used but not imported in {filepath}: {missing}. "
        f"Add these to the import statement: from fastapi import ..., {', '.join(missing)}, ..."
    )


def test_fastapi_imports_in_routes():
    """Test that all FastAPI symbols used in route files are imported."""
    route_files = [
        "api/routes/questions.py",
        "api/routes/collections.py", 
        "api/routes/operations.py",
        "api/routes/pipeline.py",
    ]
    
    for filepath in route_files:
        if not os.path.exists(filepath):
            continue
            
        imported = extract_fastapi_imports(filepath)
        used = find_used_fastapi_symbols(filepath)
        
        missing = used - imported
        assert not missing, (
            f"FastAPI symbols used but not imported in {filepath}: {missing}. "
            f"Add these to the import statement."
        )


def test_no_unresolved_fastapi_symbols():
    """Ensure no FastAPI symbols are used without being imported."""
    project_root = Path(".")
    
    for api_file in API_FILES:
        filepath = project_root / api_file
        if not filepath.exists():
            continue
            
        imported = extract_fastapi_imports(str(filepath))
        used = find_used_fastapi_symbols(str(filepath))
        
        missing = used - imported
        assert not missing, (
            f"Unresolved FastAPI symbols in {api_file}: {missing}. "
            f"These symbols must be imported from fastapi."
        )


def test_body_imported_where_used():
    """Specific test for Body import - catches the common regression."""
    # Check api/app.py specifically since that's where Body is used
    filepath = "api/app.py"
    imported = extract_fastapi_imports(filepath)
    used = find_used_fastapi_symbols(filepath)
    
    if "Body" in used:
        assert "Body" in imported, (
            "Body is used in api/app.py but not imported. "
            "This will cause 'NameError: name Body is not defined' at runtime."
        )


if __name__ == "__main__":
    # Allow running directly for quick validation
    import sys
    
    print("Validating FastAPI imports...")
    all_passed = True
    
    for filepath in API_FILES:
        if not os.path.exists(filepath):
            continue
        imported = extract_fastapi_imports(filepath)
        used = find_used_fastapi_symbols(filepath)
        missing = used - imported
        
        if missing:
            print(f"FAIL: {filepath} - Missing imports: {missing}")
            all_passed = False
        else:
            print(f"OK: {filepath}")
    
    if all_passed:
        print("\nAll FastAPI imports are valid.")
        sys.exit(0)
    else:
        print("\nImport validation FAILED.")
        sys.exit(1)