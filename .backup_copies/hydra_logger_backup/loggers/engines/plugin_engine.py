"""
Plugin Engine for Hydra-Logger Loggers

This module provides comprehensive plugin management features including plugin discovery,
loading, lifecycle management, compatibility checking, and performance optimization.
It serves as the central plugin system for all logger implementations.

ARCHITECTURE:
- PluginEngine: Central plugin management engine
- PluginManager: Plugin loading and lifecycle management
- PluginDiscovery: Plugin discovery and registration
- PluginRegistry: Plugin registry and metadata management
- PluginAnalyzer: Plugin compatibility and performance analysis

CORE FEATURES:
- Plugin discovery and loading
- Plugin lifecycle management
- Plugin compatibility checking
- Plugin performance optimization
- Plugin error handling and recovery
- Plugin metrics and monitoring

USAGE EXAMPLES:

Basic Plugin Management:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Enable plugin system
    plugins.set_plugins_enabled(True)
    
    # Discover available plugins
    available_plugins = plugins.discover_plugins()
    print(f"Available plugins: {available_plugins}")
    
    # Load specific plugin
    success = plugins.load_plugin("performance_monitor")
    print(f"Plugin loaded: {success}")

Plugin Discovery:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Discover plugins in specific paths
    search_paths = ["/path/to/plugins", "/custom/plugins"]
    discovered = plugins.discover_plugins(search_paths)
    print(f"Discovered plugins: {discovered}")
    
    # Get plugin recommendations
    recommendations = plugins.get_plugin_recommendations()
    print(f"Plugin recommendations: {recommendations}")

Plugin Lifecycle Management:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Load plugin
    success = plugins.load_plugin("custom_plugin", config={"setting": "value"})
    if success:
        print("Plugin loaded successfully")
        
        # Get plugin instance
        plugin = plugins.get_plugin("custom_plugin")
        if plugin:
            print(f"Plugin instance: {plugin}")
        
        # Unload plugin
        unload_success = plugins.unload_plugin("custom_plugin")
        print(f"Plugin unloaded: {unload_success}")

Plugin Compatibility:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Check plugin compatibility
    compatible = plugins.check_plugin_compatibility("custom_plugin")
    print(f"Plugin compatible: {compatible}")
    
    # Analyze plugin
    analysis = plugins.analyze_plugin("custom_plugin")
    print(f"Plugin analysis: {analysis}")

Plugin Performance Optimization:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Optimize plugins
    optimization_result = plugins.optimize_plugins()
    print(f"Optimization result: {optimization_result}")
    
    # Get plugin metrics
    metrics = plugins.get_plugin_metrics()
    print(f"Plugin metrics: {metrics}")

Plugin Management:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Enable plugin system
    plugins.set_plugins_enabled(True)
    
    # Load multiple plugins
    plugins.load_plugin("performance_monitor")
    plugins.load_plugin("security_validator")
    plugins.load_plugin("custom_formatter")
    
    # List loaded plugins
    loaded_plugins = plugins.list_plugins()
    print(f"Loaded plugins: {loaded_plugins}")
    
    # Get plugin metrics
    metrics = plugins.get_plugin_metrics()
    print(f"Plugin metrics: {metrics}")
    
    # Reset metrics
    plugins.reset_metrics()

Plugin Error Handling:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Load plugin with error handling
    try:
        success = plugins.load_plugin("problematic_plugin")
        if not success:
            print("Failed to load plugin")
    except Exception as e:
        print(f"Plugin loading error: {e}")
    
    # Get plugin metrics including errors
    metrics = plugins.get_plugin_metrics()
    print(f"Plugin errors: {metrics['plugin_errors']}")
    print(f"Failed plugins: {metrics['failed_plugins']}")

Engine Management:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Get individual components
    manager = plugins.get_manager()
    discovery = plugins.get_discovery()
    registry = plugins.get_registry()
    analyzer = plugins.get_analyzer()
    
    # Use components directly
    # (Components are typically used internally by the engine)

PLUGIN DISCOVERY:
- Automatic plugin discovery in specified paths
- Plugin metadata extraction and validation
- Plugin registration and categorization
- Plugin dependency resolution
- Plugin conflict detection

PLUGIN LIFECYCLE:
- Plugin loading and initialization
- Plugin configuration and setup
- Plugin execution and monitoring
- Plugin cleanup and unloading
- Plugin error recovery

PLUGIN COMPATIBILITY:
- Plugin version compatibility checking
- Plugin dependency validation
- Plugin interface compatibility
- Plugin performance analysis
- Plugin recommendation system

PLUGIN PERFORMANCE:
- Plugin performance monitoring
- Plugin optimization recommendations
- Plugin resource usage tracking
- Plugin bottleneck identification
- Plugin performance tuning

ERROR HANDLING:
- Graceful error handling with fallback mechanisms
- Error isolation between plugins
- Comprehensive error reporting
- Automatic plugin recovery
- Silent error handling for maximum performance

BENEFITS:
- Comprehensive plugin management system
- Easy plugin discovery and loading
- Plugin compatibility and performance analysis
- Extensible architecture for custom plugins
- Production-ready with error handling
"""

from typing import Any, Dict, List, Optional, Union
from ...plugins.manager import PluginManager
from ...plugins.discovery import PluginDiscovery
from ...plugins.registry import PluginRegistry
from ...plugins.analyzer import PluginAnalyzer


class PluginEngine:
    """Plugin management engine for loggers."""
    
    def __init__(self):
        """Initialize the plugin engine."""
        self._manager = PluginManager()
        self._discovery = PluginDiscovery()
        self._registry = PluginRegistry()
        self._analyzer = PluginAnalyzer()
        self._plugins_enabled = True
        
        # Plugin statistics
        self._loaded_plugins = 0
        self._active_plugins = 0
        self._failed_plugins = 0
        self._plugin_errors = []
    
    def set_plugins_enabled(self, enabled: bool) -> None:
        """Enable or disable plugin system."""
        self._plugins_enabled = enabled
    
    def discover_plugins(self, search_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Discover available plugins."""
        if not self._plugins_enabled:
            return []
        
        try:
            plugins = self._discovery.discover(search_paths)
            return plugins
        except Exception as e:
            self._plugin_errors.append(f"Plugin discovery failed: {e}")
            return []
    
    def load_plugin(self, plugin_name: str, **kwargs) -> bool:
        """Load a specific plugin."""
        if not self._plugins_enabled:
            return False
        
        try:
            success = self._manager.load_plugin(plugin_name, **kwargs)
            if success:
                self._loaded_plugins += 1
                self._active_plugins += 1
            return success
        except Exception as e:
            self._failed_plugins += 1
            self._plugin_errors.append(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin."""
        if not self._plugins_enabled:
            return False
        
        try:
            success = self._manager.unload_plugin(plugin_name)
            if success:
                self._active_plugins -= 1
            return success
        except Exception as e:
            self._plugin_errors.append(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Get a specific plugin instance."""
        if not self._plugins_enabled:
            return None
        
        try:
            return self._manager.get_plugin(plugin_name)
        except Exception:
            return None
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins."""
        if not self._plugins_enabled:
            return []
        
        try:
            return self._manager.list_plugins()
        except Exception:
            return []
    
    def analyze_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Analyze a plugin for compatibility and performance."""
        if not self._plugins_enabled:
            return {'compatible': False, 'reason': 'Plugin system disabled'}
        
        try:
            return self._analyzer.analyze_plugin(plugin_name)
        except Exception as e:
            return {
                'compatible': False,
                'reason': f'Analysis failed: {e}',
                'error': str(e)
            }
    
    def check_plugin_compatibility(self, plugin_name: str) -> bool:
        """Check if a plugin is compatible with the current system."""
        if not self._plugins_enabled:
            return False
        
        try:
            analysis = self.analyze_plugin(plugin_name)
            return analysis.get('compatible', False)
        except Exception:
            return False
    
    def get_plugin_recommendations(self) -> List[Dict[str, Any]]:
        """Get plugin recommendations based on current usage."""
        if not self._plugins_enabled:
            return []
        
        try:
            return self._analyzer.get_recommendations()
        except Exception:
            return []
    
    def optimize_plugins(self) -> Dict[str, Any]:
        """Optimize plugin performance."""
        if not self._plugins_enabled:
            return {'optimized': False, 'reason': 'Plugin system disabled'}
        
        try:
            result = self._analyzer.optimize_plugins()
            return result
        except Exception as e:
            return {
                'optimized': False,
                'reason': f'Optimization failed: {e}',
                'error': str(e)
            }
    
    def get_plugin_metrics(self) -> Dict[str, Any]:
        """Get plugin metrics."""
        return {
            'plugins_enabled': self._plugins_enabled,
            'loaded_plugins': self._loaded_plugins,
            'active_plugins': self._active_plugins,
            'failed_plugins': self._failed_plugins,
            'plugin_errors': len(self._plugin_errors),
            'recent_errors': self._plugin_errors[-5:] if self._plugin_errors else []
        }
    
    def reset_metrics(self) -> None:
        """Reset plugin metrics."""
        self._loaded_plugins = 0
        self._active_plugins = 0
        self._failed_plugins = 0
        self._plugin_errors.clear()
    
    def get_manager(self) -> PluginManager:
        """Get the plugin manager."""
        return self._manager
    
    def get_discovery(self) -> PluginDiscovery:
        """Get the plugin discovery system."""
        return self._discovery
    
    def get_registry(self) -> PluginRegistry:
        """Get the plugin registry."""
        return self._registry
    
    def get_analyzer(self) -> PluginAnalyzer:
        """Get the plugin analyzer."""
        return self._analyzer
