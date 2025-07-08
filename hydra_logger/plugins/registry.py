"""
Plugin registry for Hydra-Logger.

This module provides a dynamic plugin registry system for extensibility
and community contributions.
"""

import importlib
import threading
from typing import Any, Dict, Optional, Type

from hydra_logger.core.exceptions import PluginError


class PluginRegistry:
    """Dynamic plugin registry for extensibility."""
    
    def __init__(self):
        self._plugins: Dict[str, Any] = {}
        self._analytics_plugins: Dict[str, Type] = {}
        self._formatter_plugins: Dict[str, Type] = {}
        self._handler_plugins: Dict[str, Type] = {}
        self._lock = threading.Lock()
    
    def register_plugin(self, name: str, plugin_class: type, plugin_type: str = "analytics") -> None:
        """
        Register a plugin.
        
        Args:
            name: Plugin name
            plugin_class: Plugin class
            plugin_type: Type of plugin ('analytics', 'formatter', 'handler')
            
        Raises:
            PluginError: If plugin registration fails
        """
        with self._lock:
            try:
                if plugin_type == "analytics":
                    self._analytics_plugins[name] = plugin_class
                elif plugin_type == "formatter":
                    self._formatter_plugins[name] = plugin_class
                elif plugin_type == "handler":
                    self._handler_plugins[name] = plugin_class
                else:
                    raise PluginError(f"Unknown plugin type: {plugin_type}")
                
                self._plugins[name] = plugin_class
            except Exception as e:
                raise PluginError(f"Failed to register plugin '{name}': {e}")
    
    def get_plugin(self, name: str, plugin_type: str = "analytics") -> Optional[Type]:
        """
        Get a plugin by name.
        
        Args:
            name: Plugin name
            plugin_type: Type of plugin
            
        Returns:
            Plugin class or None if not found
        """
        with self._lock:
            if plugin_type == "analytics":
                return self._analytics_plugins.get(name)
            elif plugin_type == "formatter":
                return self._formatter_plugins.get(name)
            elif plugin_type == "handler":
                return self._handler_plugins.get(name)
            return self._plugins.get(name)
    
    def list_plugins(self, plugin_type: Optional[str] = None) -> Dict[str, Type]:
        """
        List all registered plugins.
        
        Args:
            plugin_type: Filter by plugin type
            
        Returns:
            Dictionary of plugin names to classes
        """
        with self._lock:
            if plugin_type == "analytics":
                return self._analytics_plugins.copy()
            elif plugin_type == "formatter":
                return self._formatter_plugins.copy()
            elif plugin_type == "handler":
                return self._handler_plugins.copy()
            else:
                return self._plugins.copy()
    
    def unregister_plugin(self, name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if plugin was unregistered, False if not found
        """
        with self._lock:
            if name in self._plugins:
                del self._plugins[name]
                
                # Remove from type-specific registries
                if name in self._analytics_plugins:
                    del self._analytics_plugins[name]
                if name in self._formatter_plugins:
                    del self._formatter_plugins[name]
                if name in self._handler_plugins:
                    del self._handler_plugins[name]
                
                return True
            return False
    
    def load_plugin_from_path(self, name: str, module_path: str) -> bool:
        """
        Load plugin from external module.
        
        Args:
            name: Plugin name
            module_path: Module path
            
        Returns:
            True if plugin loaded successfully
            
        Raises:
            PluginError: If plugin loading fails
        """
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, name)
            
            # Determine plugin type based on base classes
            if hasattr(plugin_class, 'process_event'):
                plugin_type = "analytics"
            elif hasattr(plugin_class, 'format'):
                plugin_type = "formatter"
            elif hasattr(plugin_class, 'emit'):
                plugin_type = "handler"
            else:
                plugin_type = "analytics"  # Default
            
            self.register_plugin(name, plugin_class, plugin_type)
            return True
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin '{name}' from '{module_path}': {e}")
    
    def clear_plugins(self) -> None:
        """Clear all registered plugins."""
        with self._lock:
            self._plugins.clear()
            self._analytics_plugins.clear()
            self._formatter_plugins.clear()
            self._handler_plugins.clear()


# Global registry instance
_plugin_registry = PluginRegistry()


def register_plugin(name: str, plugin_class: type, plugin_type: str = "analytics") -> None:
    """
    Register a plugin globally.
    
    Args:
        name: Plugin name
        plugin_class: Plugin class
        plugin_type: Type of plugin
    """
    _plugin_registry.register_plugin(name, plugin_class, plugin_type)


def get_plugin(name: str, plugin_type: str = "analytics") -> Optional[Type]:
    """
    Get a plugin globally.
    
    Args:
        name: Plugin name
        plugin_type: Type of plugin
        
    Returns:
        Plugin class or None if not found
    """
    return _plugin_registry.get_plugin(name, plugin_type)


def list_plugins(plugin_type: Optional[str] = None) -> Dict[str, Type]:
    """
    List all registered plugins globally.
    
    Args:
        plugin_type: Filter by plugin type
        
    Returns:
        Dictionary of plugin names to classes
    """
    return _plugin_registry.list_plugins(plugin_type)


def unregister_plugin(name: str) -> bool:
    """
    Unregister a plugin globally.
    
    Args:
        name: Plugin name
        
    Returns:
        True if plugin was unregistered, False if not found
    """
    return _plugin_registry.unregister_plugin(name)


def load_plugin_from_path(name: str, module_path: str) -> bool:
    """
    Load plugin from external module globally.
    
    Args:
        name: Plugin name
        module_path: Module path
        
    Returns:
        True if plugin loaded successfully
    """
    return _plugin_registry.load_plugin_from_path(name, module_path)


def clear_plugins() -> None:
    """Clear all registered plugins globally."""
    _plugin_registry.clear_plugins() 