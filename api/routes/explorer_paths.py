"""Path utilities for explorer routes."""

from urllib.parse import unquote


def resolve_folder_path(folder_path: str, collection_root: str) -> tuple[str, str]:
    """Resolve request folder path to a full absolute path and relative path."""
    if not collection_root or not collection_root.strip("/"):
        raise ValueError("Collection root must be non-empty")

    normalized_root = f"/{collection_root.strip('/')}"
    decoded_path = unquote(folder_path or "").strip().replace("\\", "/")
    root_no_leading_slash = normalized_root.lstrip("/")
    decoded_no_leading_slash = decoded_path.lstrip("/")

    raw_parts = [part for part in decoded_no_leading_slash.split("/") if part]
    if any(part in {".", ".."} for part in raw_parts):
        raise ValueError("Invalid folder path: path traversal detected")

    if not decoded_path or decoded_path == "/" or decoded_no_leading_slash == root_no_leading_slash:
        return normalized_root, ""

    if decoded_path.startswith(f"{normalized_root}/"):
        relative_path = decoded_path[len(normalized_root):].strip("/")
    elif decoded_no_leading_slash.startswith(f"{root_no_leading_slash}/"):
        relative_path = decoded_no_leading_slash[len(root_no_leading_slash):].strip("/")
    else:
        relative_path = decoded_no_leading_slash

    normalized_relative = "/".join(part for part in relative_path.split("/") if part)
    full_path = normalized_root if not normalized_relative else f"{normalized_root}/{normalized_relative}"
    return full_path, normalized_relative
