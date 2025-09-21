"""
Plugin Discovery System for Hydra-Logger

This module provides automatic plugin discovery and loading capabilities with
support for multiple search paths, plugin validation, and metadata extraction.
It enables dynamic plugin loading and management without manual registration.

FEATURES:
- Automatic plugin discovery in specified paths
- Plugin metadata extraction and analysis
- Plugin validation and compatibility checking
- Configurable search paths and discovery rules
- Plugin caching and performance optimization

USAGE:
    from hydra_logger.plugins import PluginDiscovery
    
    # Create discovery system
    discovery = PluginDiscovery()
    
    # Add custom search path
    discovery.add_search_path("my_app.plugins")
    
    # Discover plugins
    plugins = discovery.discover()
    
    # Get specific plugin class
    plugin_class = discovery.get_plugin_class("my_plugin")
    
    # Validate plugin
    validation = discovery.validate_plugin("my_plugin")
"""

import os
import importlib
import inspect
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from .base import BasePlugin


class PluginDiscovery:
    """Automatic plugin discovery and loading system."""
    
    def __init__(self):
        """Initialize plugin discovery."""
        self._discovered_plugins: Dict[str, Dict[str, Any]] = {}
        self._search_paths: List[str] = []
        self._plugin_cache: Dict[str, Type[BasePlugin]] = {}
        
        # Default search paths
        self._default_paths = [
            "hydra_logger.plugins.builtin",
            "hydra_logger.plugins.custom"
        ]
        self._search_paths.extend(self._default_paths)
    
    def add_search_path(self, path: str) -> None:
        """Add a search path for plugin discovery."""
        if path not in self._search_paths:
            self._search_paths.append(path)
    
    def remove_search_path(self, path: str) -> None:
        """Remove a search path from discovery."""
        if path in self._search_paths:
            self._search_paths.remove(path)
    
    def get_search_paths(self) -> List[str]:
        """Get all current search paths."""
        return self._search_paths.copy()
    
    def discover(self, search_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Discover available plugins in the specified paths."""
        paths = search_paths or self._search_paths
        discovered = []
        
        for path in paths:
            try:
                plugins = self._discover_in_path(path)
                discovered.extend(plugins)
            except Exception as e:
                # Log discovery error but continue with other paths
                print(f"Plugin discovery failed for {path}: {e}")
                continue
        
        return discovered
    
    def _discover_in_path(self, path: str) -> List[Dict[str, Any]]:
        """Discover plugins in a specific path."""
        plugins = []
        
        try:
            # Try to import the module
            module = importlib.import_module(path)
            
            # Scan module for plugin classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and 
                    obj != BasePlugin):
                    
                    plugin_info = self._analyze_plugin_class(obj, path)
                    if plugin_info:
                        plugins.append(plugin_info)
                        self._plugin_cache[plugin_info['name']] = obj
                        
        except ImportError:
            # Path doesn't exist or can't be imported
            pass
        except Exception as e:
            # Other errors during discovery
            print(f"Error discovering plugins in {path}: {e}")
        
        return plugins
    
    def _analyze_plugin_class(self, plugin_class: Type[BasePlugin], path: str) -> Optional[Dict[str, Any]]:
        """Analyze a plugin class for metadata."""
        try:
            # Create a temporary instance to get metadata
            temp_instance = plugin_class("temp", enabled=False)
            
            plugin_info = {
                'name': temp_instance.name,
                'class_name': plugin_class.__name__,
                'module_path': path,
                'type': plugin_class.__name__,
                'enabled': temp_instance.is_enabled(),
                'description': getattr(plugin_class, '__doc__', ''),
                'version': getattr(plugin_class, '__version__', '1.0.0'),
                'author': getattr(plugin_class, '__author__', 'Unknown'),
                'requirements': getattr(plugin_class, '__requirements__', []),
                'compatibility': getattr(plugin_class, '__compatibility__', {}),
                'features': self._extract_plugin_features(plugin_class)
            }
            
            return plugin_info
            
        except Exception:
            return None
    
    def _extract_plugin_features(self, plugin_class: Type[BasePlugin]) -> List[str]:
        """Extract features from a plugin class."""
        features = []
        
        # Check for common plugin features
        if hasattr(plugin_class, 'process_event'):
            features.append('event_processing')
        if hasattr(plugin_class, 'format'):
            features.append('formatting')
        if hasattr(plugin_class, 'emit'):
            features.append('output_handling')
        if hasattr(plugin_class, 'detect_threats'):
            features.append('security')
        if hasattr(plugin_class, 'track_operation'):
            features.append('performance_monitoring')
        
        return features
    
    def get_plugin_class(self, plugin_name: str) -> Optional[Type[BasePlugin]]:
        """Get a plugin class by name."""
        return self._plugin_cache.get(plugin_name)
    
    def list_discovered_plugins(self) -> List[str]:
        """List all discovered plugin names."""
        return list(self._plugin_cache.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a discovered plugin."""
        plugin_class = self._plugin_cache.get(plugin_name)
        if not plugin_class:
            return None
        
        # Find the plugin info from discovery
        for path in self._search_paths:
            try:
                module = importlib.import_module(path)
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        obj == plugin_class):
                        return self._analyze_plugin_class(obj, path)
            except ImportError:
                continue
        
        return None
    
    def refresh_discovery(self) -> None:
        """Refresh plugin discovery."""
        self._discovered_plugins.clear()
        self._plugin_cache.clear()
        self.discover()
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        return {
            'search_paths': len(self._search_paths),
            'discovered_plugins': len(self._plugin_cache),
            'cache_size': len(self._plugin_cache),
            'default_paths': len(self._default_paths)
        }
    
    def clear_cache(self) -> None:
        """Clear the plugin cache."""
        self._plugin_cache.clear()
    
    def validate_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Validate a discovered plugin."""
        plugin_class = self._plugin_cache.get(plugin_name)
        if not plugin_class:
            return {'valid': False, 'error': 'Plugin not found'}
        
        try:
            # Try to create an instance
            instance = plugin_class(plugin_name, enabled=False)
            
            # Check if it can be initialized
            init_success = instance.initialize()
            
            return {
                'valid': True,
                'initializable': init_success,
                'class_name': plugin_class.__name__,
                'features': self._extract_plugin_features(plugin_class)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'class_name': plugin_class.__name__
            }
