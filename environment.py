"""Environment variable helpers for Librarian."""

import logging
import os
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

DEFAULT_LIBRARY_ROOT = "/library"
DEFAULT_LIBRARIAN_DATA_ROOT = "/librarian-data"
DEFAULT_API_URL = "http://localhost:8000"

_warned_aliases: set[tuple[str, str]] = set()


def get_env(
    canonical_name: str,
    *,
    aliases: Iterable[str] = (),
    default: Optional[str] = None,
) -> Optional[str]:
    """Return an environment variable value with optional compatibility aliases."""
    value = os.environ.get(canonical_name)
    if value is not None:
        return value

    for alias in aliases:
        value = os.environ.get(alias)
        if value is not None:
            _warn_deprecated_alias(alias, canonical_name)
            return value

    return default


def get_database_url(default: Optional[str] = None) -> Optional[str]:
    """Return the configured database URL."""
    return get_env("DATABASE_URL", default=default)


def get_library_root(default: str = DEFAULT_LIBRARY_ROOT) -> str:
    """Return the configured library root."""
    return get_env(
        "LIBRARIAN_LIBRARY_ROOT",
        aliases=("LIBRARY_ROOT",),
        default=default,
    ) or default


def get_librarian_data_root(default: str = DEFAULT_LIBRARIAN_DATA_ROOT) -> str:
    """Return the configured Librarian data root for derived artifacts."""
    return get_env(
        "LIBRARIAN_DATA_ROOT",
        default=default,
    ) or default


def get_api_url(default: str = DEFAULT_API_URL) -> str:
    """Return the configured API URL for clients."""
    return get_env(
        "LIBRARIAN_API_URL",
        aliases=("API_URL",),
        default=default,
    ) or default


def get_worker_id(default: Optional[str] = None) -> Optional[str]:
    """Return the worker identifier."""
    return get_env("WORKER_ID", default=default)


def get_embedding_model(default: Optional[str] = None) -> Optional[str]:
    """Return the preferred embedding model name."""
    return get_env("EMBEDDING_MODEL", default=default)


def _warn_deprecated_alias(alias: str, canonical_name: str) -> None:
    """Warn once when a deprecated alias is used."""
    warning_key = (alias, canonical_name)
    if warning_key in _warned_aliases:
        return

    logger.warning(
        "Environment variable %s is deprecated; use %s instead.",
        alias,
        canonical_name,
    )
    _warned_aliases.add(warning_key)
