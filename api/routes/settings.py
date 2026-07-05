"""Settings API routes for plugin management.

Provides endpoints for:
- GET /api/v1/settings/plugins - List all installed plugins
- PUT /api/v1/settings/plugins/{plugin_name} - Update plugin enabled state
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from registry.plugin_registry import get_plugin_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


class PluginInfo(BaseModel):
    """Plugin information response."""
    name: str = Field(description="Plugin name (e.g., 'photo_metadata')")
    installed: bool = Field(description="Whether the plugin is installed")
    enabled: bool = Field(description="Whether the plugin is enabled")
    job_type: str = Field(description="The job type this plugin generates")
    description: str = Field(description="Human-readable description")
    category: str = Field(default="general", description="Plugin category")
    # Operation Plugin Foundation: Identity fields for provenance
    namespace: Optional[str] = Field(default=None, description="Fully qualified plugin namespace (e.g., 'metadata.exif.pillow')")
    type: Optional[str] = Field(default=None, description="Plugin type (e.g., 'exif', 'ocr')")
    engine: Optional[str] = Field(default=None, description="Engine name (e.g., 'pillow-exif')")
    version: Optional[str] = Field(default=None, description="Plugin version (e.g., '1.0.0')")


class PluginListResponse(BaseModel):
    """Response for listing plugins."""
    plugins: list[PluginInfo]
    total: int


class PluginUpdateRequest(BaseModel):
    """Request to update plugin configuration."""
    enabled: bool = Field(description="Enable or disable the plugin")


class PluginUpdateResponse(BaseModel):
    """Response for plugin update."""
    name: str
    installed: bool
    enabled: bool
    message: str


@router.get(
    "/plugins",
    response_model=PluginListResponse,
    summary="List installed plugins"
)
async def list_plugins() -> PluginListResponse:
    """
    Get all installed plugins with their current configuration.
    
    Only installed plugins are returned. Non-existent plugins do not appear.
    
    Returns:
        List of plugins with their enabled status
    """
    registry = get_plugin_registry()
    plugins_data = registry.get_installed_plugins()
    
    plugins = [
        PluginInfo(
            name=p['name'],
            installed=p['installed'],
            enabled=p['enabled'],
            job_type=p['job_type'],
            description=p['description'],
            category=p.get('category', 'general'),
            namespace=p.get('namespace'),
            type=p.get('type'),
            engine=p.get('engine'),
            version=p.get('version'),
        )
        for p in plugins_data
    ]
    
    return PluginListResponse(
        plugins=plugins,
        total=len(plugins)
    )


@router.get(
    "/plugins/{plugin_name}",
    response_model=PluginInfo,
    summary="Get plugin information"
)
async def get_plugin(plugin_name: str) -> PluginInfo:
    """
    Get information about a specific plugin.
    
    Args:
        plugin_name: Name of the plugin
        
    Returns:
        Plugin information
        
    Raises:
        404: Plugin not found or not installed
    """
    registry = get_plugin_registry()
    plugin_info = registry.get_plugin_info(plugin_name)
    
    if not plugin_info:
        raise HTTPException(
            status_code=404,
            detail=f"Plugin '{plugin_name}' not found or not installed"
        )
    
    return PluginInfo(
        name=plugin_info['name'],
        installed=plugin_info['installed'],
        enabled=plugin_info['enabled'],
        job_type=plugin_info['job_type'],
        description=plugin_info['description'],
        category=plugin_info.get('category', 'general'),
        namespace=plugin_info.get('namespace'),
        type=plugin_info.get('type'),
        engine=plugin_info.get('engine'),
        version=plugin_info.get('version'),
    )


@router.put(
    "/plugins/{plugin_name}",
    response_model=PluginUpdateResponse,
    summary="Update plugin configuration"
)
async def update_plugin(
    plugin_name: str,
    request: PluginUpdateRequest
) -> PluginUpdateResponse:
    """
    Enable or disable a plugin.
    
    Args:
        plugin_name: Name of the plugin
        request: Update request with enabled state
        
    Returns:
        Updated plugin information
        
    Raises:
        404: Plugin not found or not installed
    """
    registry = get_plugin_registry()
    
    # Check if plugin exists
    if not registry.is_installed(plugin_name):
        raise HTTPException(
            status_code=404,
            detail=f"Plugin '{plugin_name}' not found or not installed"
        )
    
    # Update plugin state
    if request.enabled:
        registry.enable(plugin_name)
        message = f"Plugin '{plugin_name}' has been enabled"
    else:
        registry.disable(plugin_name)
        message = f"Plugin '{plugin_name}' has been disabled"
    
    logger.info(f"Plugin '{plugin_name}' updated: enabled={request.enabled}")
    
    return PluginUpdateResponse(
        name=plugin_name,
        installed=True,
        enabled=request.enabled,
        message=message
    )
