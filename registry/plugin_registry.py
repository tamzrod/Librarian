"""
Plugin Registry for Job Scheduling.

P13: Plugin Registry - Controls which plugins generate jobs.

This module provides:
- Plugin registry with enabled/disabled configuration
- Integration with job scheduling
- Initial configuration: only photo_metadata enabled

Plugin Architecture:
- Only enabled plugins generate jobs
- Prevents queue pollution from unsupported job types
- Clear separation between scheduling and execution
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Plugin definitions
class Plugin:
    """Represents a plugin with its job type and enabled status."""
    
    def __init__(self, name: str, job_type: str, enabled: bool = False, 
                 description: str = ""):
        self.name = name
        self.job_type = job_type
        self.enabled = enabled
        self.description = description


# Initial plugin set
PLUGINS = {
    'photo_metadata': Plugin(
        name='photo_metadata',
        job_type='extract_photo_metadata',
        enabled=True,
        description='Extract EXIF metadata from images (GPS, camera info, timestamps)'
    ),
    'thumbnail': Plugin(
        name='thumbnail',
        job_type='generate_thumbnail',
        enabled=False,
        description='Generate thumbnail images'
    ),
    'ocr': Plugin(
        name='ocr',
        job_type='run_ocr',
        enabled=False,
        description='Optical character recognition'
    ),
    'object_detection': Plugin(
        name='object_detection',
        job_type='object_detection',
        enabled=False,
        description='Detect objects in images'
    ),
    'transcription': Plugin(
        name='transcription',
        job_type='transcription',
        enabled=False,
        description='Transcribe audio/video to text'
    ),
    'embeddings': Plugin(
        name='embeddings',
        job_type='generate_embeddings',
        enabled=False,
        description='Generate vector embeddings'
    ),
}


class PluginRegistry:
    """
    Registry for managing plugin enable/disable state.
    
    This controls which job types are scheduled for image artifacts.
    Only enabled plugins will have jobs created for them.
    
    Usage:
        registry = PluginRegistry()
        registry.enable('thumbnail')
        registry.disable('ocr')
        
        if registry.is_enabled('photo_metadata'):
            # Schedule job
    """
    
    def __init__(self):
        """Initialize the plugin registry."""
        self._plugins = PLUGINS.copy()
        self._load_from_env()
    
    def _load_from_env(self):
        """Load plugin configuration from environment variables.
        
        Environment variables follow pattern: PLUGIN_<name>=enabled|disabled
        
        Example:
            PLUGIN_PHOTO_METADATA=enabled
            PLUGIN_THUMBNAIL=disabled
        """
        for name, plugin in self._plugins.items():
            env_key = f"PLUGIN_{name.upper()}"
            env_value = os.environ.get(env_key)
            if env_value:
                if env_value.lower() == 'enabled':
                    plugin.enabled = True
                    logger.info(f"Plugin '{name}' enabled via environment")
                elif env_value.lower() == 'disabled':
                    plugin.enabled = False
                    logger.info(f"Plugin '{name}' disabled via environment")
    
    def is_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled.
        
        Args:
            plugin_name: Name of the plugin (e.g., 'photo_metadata')
            
        Returns:
            True if the plugin is enabled, False otherwise
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Unknown plugin: {plugin_name}")
            return False
        return plugin.enabled
    
    def enable(self, plugin_name: str) -> bool:
        """Enable a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if successful, False if plugin not found
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Cannot enable unknown plugin: {plugin_name}")
            return False
        plugin.enabled = True
        logger.info(f"Plugin '{plugin_name}' enabled")
        return True
    
    def disable(self, plugin_name: str) -> bool:
        """Disable a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if successful, False if plugin not found
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Cannot disable unknown plugin: {plugin_name}")
            return False
        plugin.enabled = False
        logger.info(f"Plugin '{plugin_name}' disabled")
        return True
    
    def get_enabled_plugins(self) -> list[str]:
        """Get list of enabled plugin names.
        
        Returns:
            List of enabled plugin names
        """
        return [name for name, p in self._plugins.items() if p.enabled]
    
    def get_disabled_plugins(self) -> list[str]:
        """Get list of disabled plugin names.
        
        Returns:
            List of disabled plugin names
        """
        return [name for name, p in self._plugins.items() if not p.enabled]
    
    def get_all_plugins(self) -> dict:
        """Get all plugins with their status.
        
        Returns:
            Dict mapping plugin names to enabled status
        """
        return {name: p.enabled for name, p in self._plugins.items()}
    
    def get_job_types_for_artifact(self, artifact_type: str) -> list[str]:
        """Get enabled job types for an artifact type.
        
        This replaces the hardcoded ARTIFACT_TYPE_JOBS mapping with
        plugin-aware scheduling.
        
        Args:
            artifact_type: Type of artifact (e.g., 'image', 'text')
            
        Returns:
            List of enabled job types for this artifact type
        """
        # Map artifact types to plugins
        artifact_plugins = {
            'image': ['photo_metadata', 'thumbnail', 'ocr', 'object_detection'],
            'video': ['photo_metadata', 'thumbnail', 'transcription'],
            'audio': ['transcription', 'embeddings'],
            'text': ['embeddings'],
            'document': ['embeddings'],
            'structured': ['embeddings'],
        }
        
        plugins = artifact_plugins.get(artifact_type, [])
        job_types = []
        
        for plugin_name in plugins:
            if self.is_enabled(plugin_name):
                plugin = self._plugins.get(plugin_name)
                if plugin:
                    job_types.append(plugin.job_type)
        
        return job_types
    
    def get_plugin_info(self, plugin_name: str) -> Optional[dict]:
        """Get information about a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Dict with plugin info, or None if not found
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            return None
        return {
            'name': plugin.name,
            'job_type': plugin.job_type,
            'enabled': plugin.enabled,
            'description': plugin.description,
        }
    
    def validate_against_handlers(self, registered_handlers: set) -> dict:
        """Validate that enabled plugins have registered handlers.
        
        P15: Scheduler Validation - Ensures scheduled jobs ⊆ registered handlers.
        
        Args:
            registered_handlers: Set of job types with registered handlers
            
        Returns:
            Dict with validation results:
                - missing_handlers: List of enabled plugins without handlers
                - warnings: List of warning messages
                - is_valid: True if all enabled plugins have handlers
        """
        warnings = []
        missing_handlers = []
        
        for name, plugin in self._plugins.items():
            if plugin.enabled:
                if plugin.job_type not in registered_handlers:
                    missing_handlers.append(name)
                    warnings.append(
                        f"WARNING: Plugin '{name}' enabled but no handler registered for job type: {plugin.job_type}"
                    )
        
        return {
            'missing_handlers': missing_handlers,
            'warnings': warnings,
            'is_valid': len(missing_handlers) == 0,
        }


# Global registry instance
_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance.
    
    Returns:
        The singleton PluginRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def is_plugin_enabled(plugin_name: str) -> bool:
    """Check if a plugin is enabled.
    
    Args:
        plugin_name: Name of the plugin
        
    Returns:
        True if enabled, False otherwise
    """
    return get_plugin_registry().is_enabled(plugin_name)


def get_enabled_job_types(artifact_type: str) -> list[str]:
    """Get enabled job types for an artifact type.
    
    Args:
        artifact_type: Type of artifact
        
    Returns:
        List of enabled job types
    """
    return get_plugin_registry().get_job_types_for_artifact(artifact_type)