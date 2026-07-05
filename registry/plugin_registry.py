"""
Plugin Registry for Job Scheduling.

P13/P17: Plugin Registry - Controls which plugins generate jobs.
Operation Plugin Foundation: Added plugin identity fields (namespace, type, engine, version)

This module provides:
- Plugin discovery (detects which plugins have handlers)
- Persistent plugin configuration (from config/plugins.yaml)
- Plugin identity (namespace, type, engine, version) for provenance tracking
- Integration with job scheduling
- Only installed plugins appear in the registry

Plugin Architecture:
- Registry is source of truth for plugin existence
- Configuration is source of truth for enabled state
- Only enabled plugins generate jobs
- Prevents queue pollution from unsupported job types
- Clear separation between scheduling and execution

Plugin Identity (Operation Plugin Foundation):
- Every plugin has a namespace: category.type.engine (e.g., metadata.exif.pillow)
- Every plugin has a type: exif, ocr, object-detection, etc.
- Every plugin has an engine: pillow, tesseract, yolo, etc.
- Every plugin has a version: 1.0.0, etc.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Plugin definitions - metadata about each known plugin
# These define what COULD exist, but only INSTALLED plugins appear in the registry
#
# Operation Plugin Foundation: Added identity fields:
# - namespace: Fully qualified name (e.g., metadata.exif.pillow)
# - type: Plugin type (e.g., exif, ocr)
# - engine: Engine name (e.g., pillow-exif)
# - version: Plugin version (e.g., 1.0.0)
PLUGIN_DEFINITIONS = {
    'photo_metadata': {
        'job_type': 'extract_photo_metadata',
        'description': 'Extract EXIF metadata from images (GPS, camera info, timestamps)',
        'category': 'metadata',
        # Operation Plugin Foundation: Identity fields
        'namespace': 'metadata.exif.pillow',
        'type': 'exif',
        'engine': 'pillow-exif',
        'version': '1.0.0',
    },
    'thumbnail': {
        'job_type': 'generate_thumbnail',
        'description': 'Generate thumbnail images for preview',
        'category': 'metadata',
        # Operation Plugin Foundation: Identity fields
        'namespace': 'metadata.thumbnail.pillow',
        'type': 'thumbnail',
        'engine': 'pillow-thumbnail',
        'version': '1.0.0',
    },
    'ocr': {
        'job_type': 'run_ocr',
        'description': 'Optical character recognition',
        'category': 'vision',
        # Operation Plugin Foundation: Identity fields
        'namespace': 'vision.ocr.tesseract',
        'type': 'ocr',
        'engine': 'tesseract',
        'version': '1.0.0',
    },
    'object_detection': {
        'job_type': 'object_detection',
        'description': 'Detect objects in images',
        'category': 'vision',
        # Operation Plugin Foundation: Identity fields
        'namespace': 'vision.object-detection.yolo',
        'type': 'object-detection',
        'engine': 'yolo',
        'version': '1.0.0',
    },
    'transcription': {
        'job_type': 'transcription',
        'description': 'Transcribe audio/video to text',
        'category': 'audio',
        # Operation Plugin Foundation: Identity fields
        'namespace': 'audio.transcription.whisper',
        'type': 'transcription',
        'engine': 'whisper',
        'version': '1.0.0',
    },
    'embeddings': {
        'job_type': 'generate_embeddings',
        'description': 'Generate vector embeddings',
        'category': 'embeddings',
        # Operation Plugin Foundation: Identity fields
        'namespace': 'embeddings.openai',
        'type': 'embeddings',
        'engine': 'openai-ada002',
        'version': '1.0.0',
    },
}


class Plugin:
    """
    Represents an installed plugin with its configuration.
    
    Operation Plugin Foundation: Added identity fields (namespace, type, engine, version)
    for provenance tracking.
    """
    
    def __init__(self, name: str, job_type: str, enabled: bool = False, 
                 description: str = "", category: str = "general",
                 namespace: str = None, type: str = None, 
                 engine: str = None, version: str = None):
        self.name = name
        self.job_type = job_type
        self.enabled = enabled
        self.description = description
        self.category = category
        # Operation Plugin Foundation: Identity fields
        self.namespace = namespace or name  # Fully qualified name (e.g., metadata.exif.pillow)
        self.type = type or category        # Plugin type (e.g., exif)
        self.engine = engine               # Engine name (e.g., pillow-exif)
        self.version = version or "1.0.0"  # Plugin version


def _discover_installed_plugins() -> set[str]:
    """
    Discover which plugins have actual handler implementations.
    
    This checks for the existence of handler registrations for each plugin.
    Only plugins with handlers are considered "installed".
    
    Currently detected:
    - photo_metadata: extract_photo_metadata handler exists
    - thumbnail: generate_thumbnail handler exists
    
    Returns:
        Set of plugin names that have handlers registered
    """
    # Map job_types to plugin names
    job_type_to_plugin = {}
    for plugin_name, defn in PLUGIN_DEFINITIONS.items():
        job_type_to_plugin[defn['job_type']] = plugin_name
    
    # Check for handlers by looking at worker registrations
    # Only image-related plugins are currently considered "installed"
    # because they have concrete handler implementations
    registered_job_types = {
        'extract_photo_metadata',  # photo_metadata_extractor.py - implemented
        'generate_thumbnail',       # thumbnail_generator.py - implemented
        # The following have handlers registered in run_worker() but are
        # text/document extraction plugins, not image plugins:
        # - extract_text
        # - extract_entities
        # - extract_events
        # - extract_locations
        # - generate_embeddings
    }
    
    # Find installed plugins
    installed_plugins = set()
    for job_type, plugin_name in job_type_to_plugin.items():
        if job_type in registered_job_types:
            installed_plugins.add(plugin_name)
    
    return installed_plugins


# Discover installed plugins at module load time
INSTALLED_PLUGINS = _discover_installed_plugins()
logger.info(f"Discovered installed plugins: {INSTALLED_PLUGINS}")


class PluginRegistry:
    """
    Registry for managing plugin state.
    
    This controls which job types are scheduled for artifacts.
    Only installed AND enabled plugins will have jobs created for them.
    
    Architecture:
    1. Plugin Implementation → worker handlers register job_types
    2. Plugin Registry Discovery → detect installed plugins from handlers
    3. Plugin Configuration → load enabled/disabled from config file
    4. Scheduler → create jobs only for installed AND enabled plugins
    
    Usage:
        registry = PluginRegistry()
        
        # Check if plugin is available and enabled
        if registry.is_enabled('photo_metadata'):
            # Schedule job
        
        # Get all visible plugins (installed only)
        plugins = registry.get_installed_plugins()
    """
    
    def __init__(self):
        """Initialize the plugin registry."""
        self._config_manager = None
        self._plugins: dict[str, Plugin] = {}
        self._initialized = False
        self._initialize_plugins()
    
    def _initialize_plugins(self) -> None:
        """Initialize plugins from discovery and configuration."""
        # Lazy import to avoid circular dependencies
        try:
            from config.plugin_config import get_plugin_config_manager
            self._config_manager = get_plugin_config_manager()
        except ImportError:
            logger.warning("Plugin config manager not available, using defaults")
            self._config_manager = None
        
        # Build plugin list from INSTALLED plugins only
        for plugin_name in INSTALLED_PLUGINS:
            defn = PLUGIN_DEFINITIONS.get(plugin_name, {})
            
            # Get enabled state from configuration
            if self._config_manager:
                enabled = self._config_manager.get_enabled(plugin_name)
            else:
                # Default: only photo_metadata is enabled
                enabled = (plugin_name == 'photo_metadata')
            
            # Operation Plugin Foundation: Pass identity fields
            plugin = Plugin(
                name=plugin_name,
                job_type=defn.get('job_type', ''),
                enabled=enabled,
                description=defn.get('description', ''),
                category=defn.get('category', 'general'),
                # Identity fields
                namespace=defn.get('namespace'),
                type=defn.get('type'),
                engine=defn.get('engine'),
                version=defn.get('version'),
            )
            self._plugins[plugin_name] = plugin
        
        self._initialized = True
        logger.info(f"Plugin registry initialized with {len(self._plugins)} installed plugins")
    
    def reload_config(self) -> None:
        """Reload configuration from disk."""
        if self._config_manager:
            self._config_manager.reload()
            # Re-apply configuration to plugins
            for plugin_name, plugin in self._plugins.items():
                plugin.enabled = self._config_manager.get_enabled(plugin_name)
            logger.info("Plugin configuration reloaded")
    
    def is_installed(self, plugin_name: str) -> bool:
        """Check if a plugin is installed (has a handler).
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if the plugin is installed, False otherwise
        """
        return plugin_name in self._plugins
    
    def is_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled (installed AND enabled).
        
        Args:
            plugin_name: Name of the plugin (e.g., 'photo_metadata')
            
        Returns:
            True if the plugin is installed AND enabled, False otherwise
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.debug(f"Unknown plugin: {plugin_name}")
            return False
        return plugin.enabled
    
    def enable(self, plugin_name: str) -> bool:
        """Enable a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if successful, False if plugin not found or not installed
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Cannot enable unknown plugin: {plugin_name}")
            return False
        
        plugin.enabled = True
        
        # Persist to configuration
        if self._config_manager:
            self._config_manager.set_enabled(plugin_name, True)
        
        logger.info(f"Plugin '{plugin_name}' enabled")
        return True
    
    def disable(self, plugin_name: str) -> bool:
        """Disable a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            True if successful, False if plugin not found or not installed
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Cannot disable unknown plugin: {plugin_name}")
            return False
        
        plugin.enabled = False
        
        # Persist to configuration
        if self._config_manager:
            self._config_manager.set_enabled(plugin_name, False)
        
        logger.info(f"Plugin '{plugin_name}' disabled")
        return True
    
    def get_installed_plugins(self) -> list[dict]:
        """Get list of installed plugins with their status.
        
        Returns:
            List of dicts with plugin info:
            [
                {
                    'name': 'photo_metadata',
                    'installed': True,
                    'enabled': True,
                    'job_type': 'extract_photo_metadata',
                    'description': '...',
                    'category': 'metadata',
                    'namespace': 'metadata.exif.pillow',
                    'type': 'exif',
                    'engine': 'pillow-exif',
                    'version': '1.0.0'
                },
                ...
            ]
        """
        return [
            {
                'name': p.name,
                'installed': True,
                'enabled': p.enabled,
                'job_type': p.job_type,
                'description': p.description,
                'category': p.category,
                'namespace': p.namespace,
                'type': p.type,
                'engine': p.engine,
                'version': p.version,
            }
            for p in self._plugins.values()
        ]
    
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
        """Get all installed plugins with their status.
        
        Returns:
            Dict mapping plugin names to enabled status
        """
        return {name: p.enabled for name, p in self._plugins.items()}
    
    def get_job_types_for_artifact(self, artifact_type: str) -> list[str]:
        """Get enabled job types for an artifact type.
        
        This uses plugin configuration to determine which jobs to schedule.
        Only installed AND enabled plugins generate job types.
        
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
            # Only include if plugin is installed AND enabled
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
            Dict with plugin info, or None if not installed
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            return None
        # Operation Plugin Foundation: Include identity fields
        return {
            'name': plugin.name,
            'job_type': plugin.job_type,
            'enabled': plugin.enabled,
            'description': plugin.description,
            'category': plugin.category,
            'installed': True,
            # Identity fields (Operation Plugin Foundation)
            'namespace': plugin.namespace,
            'type': plugin.type,
            'engine': plugin.engine,
            'version': plugin.version,
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