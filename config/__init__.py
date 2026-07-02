"""Configuration module for Librarian."""

from .plugin_config import (
    PluginConfig,
    PluginConfigManager,
    get_plugin_config_manager,
)

__all__ = [
    'PluginConfig',
    'PluginConfigManager', 
    'get_plugin_config_manager',
]
