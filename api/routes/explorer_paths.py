"""Path utilities for explorer routes."""

from urllib.parse import unquote


def resolve_folder_path(folder_path: str, collection_root: str) -> tuple[str, str]:
    """Resolve request folder path to a full absolute path and relative path."""
    decoded_path = unquote(folder_path or "").strip()
    normalized_root = collection_root.rstrip("/")
    root_no_leading_slash = normalized_root.lstrip("/")

    if not decoded_path or decoded_path == "/" or decoded_path in {normalized_root, root_no_leading_slash}:
        return normalized_root, ""

    if decoded_path.startswith(f"{normalized_root}/"):
        relative_path = decoded_path[len(normalized_root):].strip("/")
    elif decoded_path.startswith(f"{root_no_leading_slash}/"):
        relative_path = decoded_path[len(root_no_leading_slash):].strip("/")
    else:
        relative_path = decoded_path.strip("/")

    parts = [part for part in relative_path.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        raise ValueError("Invalid folder path")

    normalized_relative = "/".join(parts)
    full_path = normalized_root if not normalized_relative else f"{normalized_root}/{normalized_relative}"
    return full_path, normalized_relative
