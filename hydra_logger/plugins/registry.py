"""
Plugin Registry for Hydra-Logger

This module provides plugin registration and management functionality with
support for plugin type organization, lookup operations, and lifecycle
tracking. It serves as the central repository for all registered plugins.

FEATURES:
- Plugin registration and unregistration
- Plugin type organization and filtering
- Plugin lookup and retrieval operations
- Plugin count and type statistics
- Thread-safe plugin management

USAGE:
    from hydra_logger.plugins import PluginRegistry, FormatterPlugin
    
    # Create plugin registry
    registry = PluginRegistry()
    
    # Register plugin
    plugin = MyFormatter("custom_formatter", "my_format")
    success = registry.register_plugin(plugin)
    
    # Get plugin by name
    plugin = registry.get_plugin("custom_formatter")
    
    # List plugins by type
    formatters = registry.get_plugins_by_type("FormatterPlugin")
    
    # Get plugin count
    count = registry.get_plugin_count()
"""

from typing import Dict, List, Optional, Type
from .base import BasePlugin


class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self):
        """Initialize plugin registry."""
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_types: Dict[str, List[str]] = {}
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """
        Register a plugin.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if plugin.name in self._plugins:
                return False  # Plugin already exists
            
            self._plugins[plugin.name] = plugin
            
            # Track by plugin type
            plugin_type = plugin.__class__.__name__
            if plugin_type not in self._plugin_types:
                self._plugin_types[plugin_type] = []
            self._plugin_types[plugin_type].append(plugin.name)
            
            return True
            
        except Exception:
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        if plugin_name not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_name]
        plugin_type = plugin.__class__.__name__
        
        # Remove from plugins
        del self._plugins[plugin_name]
        
        # Remove from type tracking
        if plugin_type in self._plugin_types:
            if plugin_name in self._plugin_types[plugin_type]:
                self._plugin_types[plugin_type].remove(plugin_name)
            
            # Clean up empty type lists
            if not self._plugin_types[plugin_type]:
                del self._plugin_types[plugin_type]
        
        return True
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by name.
        
        Args:
            plugin_name: Name of plugin to get
            
        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(plugin_name)
    
    def list_plugins(self, plugin_type: Optional[str] = None) -> List[str]:
        """
        List registered plugins.
        
        Args:
            plugin_type: Optional plugin type to filter by
            
        Returns:
            List of plugin names
        """
        if plugin_type:
            return self._plugin_types.get(plugin_type, [])
        return list(self._plugins.keys())
    
    def get_plugins_by_type(self, plugin_type: str) -> List[BasePlugin]:
        """
        Get all plugins of a specific type.
        
        Args:
            plugin_type: Plugin type to get
            
        Returns:
            List of plugin instances
        """
        plugin_names = self._plugin_types.get(plugin_type, [])
        return [self._plugins[name] for name in plugin_names if name in self._plugins]
    
    def clear_plugins(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()
        self._plugin_types.clear()
    
    def get_plugin_count(self) -> int:
        """
        Get total number of registered plugins.
        
        Returns:
            Plugin count
        """
        return len(self._plugins)
    
    def get_plugin_types(self) -> List[str]:
        """
        Get list of registered plugin types.
        
        Returns:
            List of plugin type names
        """
        return list(self._plugin_types.keys())
    
    def is_plugin_registered(self, plugin_name: str) -> bool:
        """
        Check if a plugin is registered.
        
        Args:
            plugin_name: Name of plugin to check
            
        Returns:
            True if registered, False otherwise
        """
        return plugin_name in self._plugins
