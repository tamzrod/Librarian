"""
Plugin Configuration Manager.

This module provides persistent plugin configuration through YAML files.
It handles:
- Loading plugin configuration from config/plugins.yaml
- Saving configuration changes
- Providing defaults for missing plugins
"""

import os
import logging
import threading
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import yaml

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_DIR = Path(__file__).parent
CONFIG_FILE = CONFIG_DIR / "plugins.yaml"


@dataclass
class PluginConfig:
    """Configuration for a single plugin."""
    name: str
    enabled: bool
    category: str = "general"
    description: str = ""


class PluginConfigManager:
    """
    Manages plugin configuration persistence.
    
    This class provides thread-safe read/write access to the plugins.yaml
    configuration file. It caches configuration in memory and writes
    changes to disk.
    
    Configuration Rules:
    - Missing plugin in config: defaults to disabled (enabled=false)
    - Plugin missing from registry: ignored completely
    - Only installed plugins appear in API responses
    """
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        self._config_file = config_file
        self._config: dict[str, dict] = {}
        self._lock = threading.RLock()
        self._initialized = False
    
    def _load_config(self) -> dict[str, dict]:
        """Load configuration from YAML file."""
        if not self._config_file.exists():
            logger.info(f"Plugin config file not found: {self._config_file}, using defaults")
            return {}
        
        try:
            with open(self._config_file, 'r') as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing plugin config: {e}")
            return {}
        except IOError as e:
            logger.error(f"Error reading plugin config: {e}")
            return {}
    
    def _save_config(self, config: dict[str, dict]) -> bool:
        """Save configuration to YAML file."""
        try:
            # Ensure directory exists
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            return True
        except IOError as e:
            logger.error(f"Error writing plugin config: {e}")
            return False
    
    def initialize(self) -> None:
        """Load configuration into memory."""
        with self._lock:
            self._config = self._load_config()
            self._initialized = True
            logger.info(f"Plugin configuration loaded: {len(self._config)} plugins configured")
    
    def get_enabled(self, plugin_name: str) -> bool:
        """
        Get enabled status for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if enabled, False otherwise (including if not in config)
        """
        with self._lock:
            if not self._initialized:
                self.initialize()
            
            plugin_config = self._config.get(plugin_name, {})
            return plugin_config.get('enabled', False)
    
    def set_enabled(self, plugin_name: str, enabled: bool) -> bool:
        """
        Set enabled status for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            enabled: Whether the plugin should be enabled
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if not self._initialized:
                self.initialize()
            
            # Ensure the plugin has an entry
            if plugin_name not in self._config:
                self._config[plugin_name] = {}
            
            self._config[plugin_name]['enabled'] = enabled
            
            # Save to disk
            return self._save_config(self._config)
    
    def get_all_config(self) -> dict[str, dict]:
        """
        Get all plugin configuration.
        
        Returns:
            Dict mapping plugin names to their configuration
        """
        with self._lock:
            if not self._initialized:
                self.initialize()
            return self._config.copy()
    
    def get_plugin_config(self, plugin_name: str) -> Optional[dict]:
        """
        Get configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration dict or None if not configured
        """
        with self._lock:
            if not self._initialized:
                self.initialize()
            return self._config.get(plugin_name)
    
    def reload(self) -> None:
        """Reload configuration from disk."""
        with self._lock:
            self._config = self._load_config()
            logger.info("Plugin configuration reloaded")


# Global config manager instance
_config_manager: Optional[PluginConfigManager] = None


def get_plugin_config_manager() -> PluginConfigManager:
    """Get the global plugin configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = PluginConfigManager()
        _config_manager.initialize()
    return _config_manager
