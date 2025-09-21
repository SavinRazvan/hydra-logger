"""
Registry System for Hydra-Logger Component Management

This module provides a comprehensive registry system for managing all types of
components including loggers, handlers, formatters, plugins, and custom components.
It includes discovery, lifecycle management, versioning, compatibility tracking,
and metadata management capabilities.

FEATURES:
- Component registration and lifecycle management
- Automatic component discovery and loading
- Version management and compatibility tracking
- Rich metadata storage and search
- Plugin system integration
- Handler and formatter specific registries

REGISTRY TYPES:
- ComponentRegistry: Generic component registry
- PluginRegistry: Plugin-specific registry
- HandlerRegistry: Handler-specific registry
- FormatterRegistry: Formatter-specific registry

MANAGEMENT SYSTEMS:
- ComponentDiscovery: Automatic component discovery
- RegistryMetadata: Rich metadata management
- ComponentVersioning: Version and compatibility management
- CompatibilityTracker: Component compatibility checking
- ComponentLifecycleManager: Lifecycle state management

USAGE:
    from hydra_logger.registry import ComponentRegistry, ComponentType
    
    # Create component registry
    registry = ComponentRegistry(enabled=True)
    
    # Register a component
    success = registry.register_component(
        ComponentType.LOGGER,
        "my_logger",
        my_logger_instance,
        metadata={"version": "1.0.0", "author": "Developer"}
    )
    
    # Get component
    component = registry.get_component(ComponentType.LOGGER, "my_logger")
    
    # Search components
    results = registry.search_components("logger")
"""

from .component_registry import ComponentRegistry
from .plugin_registry import PluginRegistry
from .handler_registry import HandlerRegistry
from .formatter_registry import FormatterRegistry
from .discovery import ComponentDiscovery
from .metadata import RegistryMetadata
from .versioning import ComponentVersioning
from .compatibility import CompatibilityTracker
from .lifecycle import ComponentLifecycleManager

__all__ = [
    "ComponentRegistry",
    "PluginRegistry", 
    "HandlerRegistry",
    "FormatterRegistry",
    "ComponentDiscovery",
    "RegistryMetadata",
    "ComponentVersioning",
    "CompatibilityTracker",
    "ComponentLifecycleManager"
]
