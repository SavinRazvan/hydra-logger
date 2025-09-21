"""
Plugin Interface for Hydra-Logger

This module defines the abstract interface that all plugin implementations
must follow, ensuring consistent behavior across different plugin types.
It provides a standardized contract for plugin lifecycle and operations.

ARCHITECTURE:
- PluginInterface: Abstract interface for all plugin implementations
- Defines contract for plugin lifecycle and operations
- Ensures consistent behavior across different plugin types
- Supports plugin discovery and management

CORE FEATURES:
- Plugin initialization and cleanup
- Plugin enable/disable operations
- Plugin configuration management
- Plugin type and version information
- Plugin compatibility checking

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import PluginInterface
    from typing import Any, Dict
    
    class CustomFormatterPlugin(PluginInterface):
        def __init__(self, name: str = "custom_formatter"):
            self._name = name
            self._version = "1.0.0"
            self._plugin_type = "formatter"
            self._enabled = False
            self._initialized = False
            self._config = {}
        
        def initialize(self) -> bool:
            try:
                self._initialized = True
                return True
            except Exception:
                return False
        
        def is_enabled(self) -> bool:
            return self._enabled
        
        def is_initialized(self) -> bool:
            return self._initialized
        
        def enable(self) -> None:
            self._enabled = True
        
        def disable(self) -> None:
            self._enabled = False
        
        def get_config(self) -> Dict[str, Any]:
            return self._config.copy()
        
        def get_plugin_type(self) -> str:
            return self._plugin_type
        
        def get_version(self) -> str:
            return self._version
        
        def get_compatibility_info(self) -> Dict[str, Any]:
            return {
                "min_hydra_version": "1.0.0",
                "max_hydra_version": "2.0.0",
                "python_versions": ["3.8", "3.9", "3.10", "3.11"]
            }

Plugin Usage:
    from hydra_logger.interfaces import PluginInterface
    
    def use_plugin(plugin: PluginInterface):
        \"\"\"Use any plugin that implements PluginInterface.\"\"\"
        # Initialize plugin
        if plugin.initialize():
            print("Plugin initialized")
            
            # Check if initialized
            if plugin.is_initialized():
                print("Plugin is initialized")
            
            # Enable plugin
            plugin.enable()
            if plugin.is_enabled():
                print("Plugin is enabled")
            
            # Get plugin info
            print(f"Plugin type: {plugin.get_plugin_type()}")
            print(f"Version: {plugin.get_version()}")
            
            # Get configuration
            config = plugin.get_config()
            print(f"Configuration: {config}")
            
            # Get compatibility info
            compat = plugin.get_compatibility_info()
            print(f"Compatibility: {compat}")
            
            # Disable plugin
            plugin.disable()
            if not plugin.is_enabled():
                print("Plugin is disabled")
        else:
            print("Failed to initialize plugin")

Plugin Discovery:
    from hydra_logger.interfaces import PluginInterface
    
    def discover_plugins(plugins: List[PluginInterface]):
        \"\"\"Discover and manage multiple plugins.\"\"\"
        # Initialize all plugins
        for plugin in plugins:
            if plugin.initialize():
                print(f"Plugin initialized: {plugin.get_plugin_type()}")
            else:
                print(f"Failed to initialize plugin: {plugin.get_plugin_type()}")
        
        # Check plugin status
        for plugin in plugins:
            if plugin.is_initialized():
                info = {
                    "type": plugin.get_plugin_type(),
                    "version": plugin.get_version(),
                    "enabled": plugin.is_enabled(),
                    "config": plugin.get_config()
                }
                print(f"Plugin info: {info}")
        
        # Enable all plugins
        for plugin in plugins:
            if plugin.is_initialized():
                plugin.enable()
                print(f"Plugin enabled: {plugin.get_plugin_type()}")

Configuration Management:
    from hydra_logger.interfaces import PluginInterface
    
    def manage_plugin_config(plugin: PluginInterface):
        \"\"\"Manage plugin configuration using the interface.\"\"\"
        # Get current configuration
        config = plugin.get_config()
        print(f"Current config: {config}")
        
        # Check plugin status
        if plugin.is_initialized():
            print("Plugin is initialized")
        else:
            print("Plugin is not initialized")
        
        if plugin.is_enabled():
            print("Plugin is enabled")
        else:
            print("Plugin is disabled")

INTERFACE CONTRACTS:
- initialize(): Initialize plugin
- is_enabled(): Check if plugin is enabled
- is_initialized(): Check if plugin is initialized
- enable(): Enable plugin
- disable(): Disable plugin
- get_config(): Get plugin configuration
- get_plugin_type(): Get plugin type
- get_version(): Get plugin version
- get_compatibility_info(): Get compatibility information

ERROR HANDLING:
- All methods return boolean success indicators
- Clear error messages and status reporting
- Graceful handling of plugin failures
- Safe configuration management

BENEFITS:
- Consistent plugin API across implementations
- Easy testing with mock plugins
- Clear contracts for custom plugins
- Polymorphic usage without tight coupling
- Better plugin discovery and management
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from ..types.records import LogRecord


class PluginInterface(ABC):
    """
    Abstract interface for all plugin implementations.
    
    This interface defines the contract that all plugins must implement,
    ensuring consistent behavior across different plugin types.
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            True if initialization successful, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Check if plugin is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if plugin is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def enable(self) -> None:
        """Enable the plugin."""
        raise NotImplementedError
    
    @abstractmethod
    def disable(self) -> None:
        """Disable the plugin."""
        raise NotImplementedError
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get plugin configuration.
        
        Returns:
            Configuration dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_plugin_type(self) -> str:
        """
        Get the plugin type.
        
        Returns:
            Plugin type string
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_version(self) -> str:
        """
        Get plugin version.
        
        Returns:
            Plugin version string
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_compatibility_info(self) -> Dict[str, Any]:
        """
        Get plugin compatibility information.
        
        Returns:
            Compatibility information dictionary
        """
        raise NotImplementedError
