"""
Plugin-Specific Registry for Hydra-Logger

This module provides a specialized registry system for managing plugins with
advanced capabilities including plugin categorization, compatibility checking,
dependency management, and lifecycle tracking. It extends the generic component
registry with plugin-specific functionality.

FEATURES:
- Plugin registration and lifecycle management
- Plugin categorization and organization
- Compatibility checking and validation
- Dependency and conflict resolution
- Plugin search and filtering
- Export/import functionality
- Plugin analytics and statistics

PLUGIN CATEGORIES:
- Analytics: Analytics and insights plugins
- Security: Security and threat detection plugins
- Performance: Performance monitoring plugins
- Monitoring: System monitoring plugins
- Formatter: Log formatter plugins
- Handler: Log handler plugins
- Integration: Third-party integration plugins
- Custom: Custom plugins

PLUGIN COMPATIBILITY LEVELS:
- Fully Compatible: Complete compatibility
- Partially Compatible: Partial compatibility
- Incompatible: No compatibility
- Unknown: Compatibility unknown

USAGE:
    from hydra_logger.registry import PluginRegistry, PluginCategory, PluginCompatibility
    
    # Create plugin registry
    registry = PluginRegistry(enabled=True)
    
    # Register a plugin
    success = registry.register_plugin(
        "my_plugin",
        my_plugin_instance,
        metadata={"version": "1.0.0", "author": "Developer"}
    )
    
    # Get plugins by category
    analytics_plugins = registry.get_plugins_by_category(PluginCategory.ANALYTICS)
    
    # Get plugin dependencies
    dependencies = registry.get_plugin_dependencies("my_plugin")
    
    # Check plugin conflicts
    conflicts = registry.get_plugin_conflicts("my_plugin")
    
    # Search plugins
    results = registry.search_plugins("analytics")
    
    # Get plugin registry statistics
    stats = registry.get_plugin_registry_stats()
"""

import time
import threading
import json
from typing import Any, Dict, List, Optional, Callable, Type
from collections import defaultdict, deque
from enum import Enum
from ..interfaces.registry import RegistryInterface
from ..interfaces.plugin import PluginInterface
from .component_registry import ComponentRegistry, ComponentType, ComponentStatus


class PluginCategory(Enum):
    """Plugin categories."""
    ANALYTICS = "analytics"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MONITORING = "monitoring"
    FORMATTER = "formatter"
    HANDLER = "handler"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class PluginCompatibility(Enum):
    """Plugin compatibility levels."""
    FULLY_COMPATIBLE = "fully_compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


class PluginRegistry(RegistryInterface):
    """Real plugin-specific registry with advanced plugin management capabilities."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        
        # Core component registry
        self._component_registry = ComponentRegistry(enabled=enabled)
        
        # Plugin-specific storage
        self._plugin_categories = defaultdict(dict)  # category -> {id -> plugin}
        self._plugin_versions = defaultdict(dict)  # name -> {version -> plugin_id}
        self._plugin_dependencies = defaultdict(set)  # plugin_id -> {dependency_ids}
        self._plugin_conflicts = defaultdict(set)  # plugin_id -> {conflicting_plugin_ids}
        
        # Plugin discovery and loading
        self._discovery_paths = []
        self._auto_discovery = True
        self._discovery_callbacks = []
        
        # Plugin validation and compatibility
        self._validation_rules = []
        self._compatibility_checkers = []
        self._version_requirements = {}
        
        # Plugin lifecycle management
        self._lifecycle_callbacks = defaultdict(list)  # event -> [callbacks]
        self._plugin_states = {}  # plugin_id -> state
        
        # Threading
        self._lock = threading.RLock()
        
        # Statistics
        self._total_plugins = 0
        self._active_plugins = 0
        self._failed_plugins = 0
        self._last_plugin_load = 0.0
    
    def register_plugin(self, plugin_id: str, plugin: PluginInterface, 
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a plugin in the registry.
        
        Args:
            plugin_id: Unique identifier for the plugin
            plugin: The plugin instance
            metadata: Additional plugin metadata
            
        Returns:
            True if registration successful
        """
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Validate plugin
                if not self._validate_plugin(plugin, metadata):
                    self._failed_plugins += 1
                    return False
                
                # Check compatibility
                compatibility = self._check_plugin_compatibility(plugin, metadata)
                if compatibility == PluginCompatibility.INCOMPATIBLE:
                    self._failed_plugins += 1
                    return False
                
                # Prepare metadata
                plugin_metadata = self._prepare_plugin_metadata(plugin_id, plugin, metadata, compatibility)
                
                # Register in component registry
                success = self._component_registry.register_component(
                    ComponentType.PLUGIN, plugin_id, plugin, plugin_metadata
                )
                
                if success:
                    # Store plugin-specific information
                    self._store_plugin_info(plugin_id, plugin, plugin_metadata)
                    
                    # Update statistics
                    self._total_plugins += 1
                    self._last_plugin_load = time.time()
                    
                    # Trigger lifecycle callbacks
                    self._trigger_lifecycle_callbacks("registered", plugin_id, plugin, plugin_metadata)
                    
                    return True
                else:
                    self._failed_plugins += 1
                    return False
                    
        except Exception as e:
            self._failed_plugins += 1
            return False
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """
        Unregister a plugin from the registry.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if unregistration successful
        """
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Get plugin before removal
                plugin = self._component_registry.get_component(ComponentType.PLUGIN, plugin_id)
                metadata = self._component_registry.get_component_metadata(ComponentType.PLUGIN, plugin_id)
                
                if not plugin:
                    return False
                
                # Check if plugin can be unregistered
                if not self._can_unregister_plugin(plugin_id):
                    return False
                
                # Unregister from component registry
                success = self._component_registry.unregister_component(ComponentType.PLUGIN, plugin_id)
                
                if success:
                    # Remove plugin-specific information
                    self._remove_plugin_info(plugin_id)
                    
                    # Update statistics
                    if plugin_id in self._plugin_states and self._plugin_states[plugin_id] == "active":
                        self._active_plugins -= 1
                    
                    # Trigger lifecycle callbacks
                    self._trigger_lifecycle_callbacks("unregistered", plugin_id, plugin, metadata)
                    
                    return True
                else:
                    return False
                    
        except Exception:
            return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """Get a plugin by ID."""
        if not self._enabled:
            return None
        
        return self._component_registry.get_component(ComponentType.PLUGIN, plugin_id)
    
    def get_plugins_by_category(self, category: PluginCategory) -> Dict[str, PluginInterface]:
        """Get all plugins of a specific category."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                return self._plugin_categories[category].copy()
        except Exception:
            return {}
    
    def get_plugins_by_version(self, name: str, version: str) -> List[PluginInterface]:
        """Get plugins by name and version."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                plugins = []
                if name in self._plugin_versions and version in self._plugin_versions[name]:
                    plugin_id = self._plugin_versions[name][version]
                    plugin = self.get_plugin(plugin_id)
                    if plugin:
                        plugins.append(plugin)
                return plugins
        except Exception:
            return []
    
    def get_plugin_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific plugin."""
        if not self._enabled:
            return None
        
        return self._component_registry.get_component_metadata(ComponentType.PLUGIN, plugin_id)
    
    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """Get all registered plugins."""
        if not self._enabled:
            return {}
        
        return self._component_registry.get_components_by_type(ComponentType.PLUGIN)
    
    def get_plugin_count(self, category: Optional[PluginCategory] = None) -> int:
        """Get count of plugins, optionally filtered by category."""
        if not self._enabled:
            return 0
        
        try:
            with self._lock:
                if category:
                    return len(self._plugin_categories[category])
                else:
                    return self._component_registry.get_component_count(ComponentType.PLUGIN)
        except Exception:
            return 0
    
    def has_plugin(self, plugin_id: str) -> bool:
        """Check if a plugin exists."""
        if not self._enabled:
            return False
        
        return self._component_registry.has_component(ComponentType.PLUGIN, plugin_id)
    
    def list_plugin_categories(self) -> List[PluginCategory]:
        """List all plugin categories."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._plugin_categories.keys())
        except Exception:
            return []
    
    def list_plugins(self, category: Optional[PluginCategory] = None) -> List[str]:
        """List all plugin IDs, optionally filtered by category."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                if category:
                    return list(self._plugin_categories[category].keys())
                else:
                    return self._component_registry.list_components(ComponentType.PLUGIN)
        except Exception:
            return []
    
    def activate_plugin(self, plugin_id: str) -> bool:
        """Activate a plugin."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if not self.has_plugin(plugin_id):
                    return False
                
                # Check dependencies
                if not self._check_plugin_dependencies(plugin_id):
                    return False
                
                # Check conflicts
                if not self._check_plugin_conflicts(plugin_id):
                    return False
                
                # Update plugin state
                self._plugin_states[plugin_id] = "active"
                self._active_plugins += 1
                
                # Update component status
                self._component_registry.set_component_status(
                    ComponentType.PLUGIN, plugin_id, ComponentStatus.ACTIVE
                )
                
                # Trigger lifecycle callbacks
                plugin = self.get_plugin(plugin_id)
                metadata = self.get_plugin_metadata(plugin_id)
                self._trigger_lifecycle_callbacks("activated", plugin_id, plugin, metadata)
                
                return True
                
        except Exception:
            return False
    
    def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate a plugin."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if not self.has_plugin(plugin_id):
                    return False
                
                # Update plugin state
                if plugin_id in self._plugin_states and self._plugin_states[plugin_id] == "active":
                    self._plugin_states[plugin_id] = "inactive"
                    self._active_plugins -= 1
                
                # Update component status
                self._component_registry.set_component_status(
                    ComponentType.PLUGIN, plugin_id, ComponentStatus.INACTIVE
                )
                
                # Trigger lifecycle callbacks
                plugin = self.get_plugin(plugin_id)
                metadata = self.get_plugin_metadata(plugin_id)
                self._trigger_lifecycle_callbacks("deactivated", plugin_id, plugin, metadata)
                
                return True
                
        except Exception:
            return False
    
    def get_plugin_state(self, plugin_id: str) -> str:
        """Get plugin state."""
        if not self._enabled:
            return "unknown"
        
        return self._plugin_states.get(plugin_id, "unknown")
    
    def get_active_plugins(self) -> List[str]:
        """Get list of active plugin IDs."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return [pid for pid, state in self._plugin_states.items() if state == "active"]
        except Exception:
            return []
    
    def get_inactive_plugins(self) -> List[str]:
        """Get list of inactive plugin IDs."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return [pid for pid, state in self._plugin_states.items() if state == "inactive"]
        except Exception:
            return []
    
    def search_plugins(self, query: str, category: Optional[PluginCategory] = None) -> List[Dict[str, Any]]:
        """Search for plugins by query string."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                results = []
                search_categories = [category] if category else self._plugin_categories.keys()
                
                for cat in search_categories:
                    for plugin_id, plugin in self._plugin_categories[cat].items():
                        metadata = self.get_plugin_metadata(plugin_id)
                        if metadata and self._matches_plugin_search(query, metadata):
                            results.append({
                                "id": plugin_id,
                                "category": cat.value,
                                "plugin": plugin,
                                "metadata": metadata.copy(),
                                "state": self._plugin_states.get(plugin_id, "unknown")
                            })
                
                return results
                
        except Exception:
            return []
    
    def get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """Get dependencies for a plugin."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._plugin_dependencies.get(plugin_id, set()))
        except Exception:
            return []
    
    def get_plugin_conflicts(self, plugin_id: str) -> List[str]:
        """Get conflicts for a plugin."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._plugin_conflicts.get(plugin_id, set()))
        except Exception:
            return []
    
    def add_validation_rule(self, rule: Callable) -> bool:
        """Add a plugin validation rule."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._validation_rules.append(rule)
                return True
        except Exception:
            return False
    
    def remove_validation_rule(self, rule: Callable) -> bool:
        """Remove a plugin validation rule."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if rule in self._validation_rules:
                    self._validation_rules.remove(rule)
                    return True
                return False
        except Exception:
            return False
    
    def add_compatibility_checker(self, checker: Callable) -> bool:
        """Add a plugin compatibility checker."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._compatibility_checkers.append(checker)
                return True
        except Exception:
            return False
    
    def remove_compatibility_checker(self, checker: Callable) -> bool:
        """Remove a plugin compatibility checker."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if checker in self._compatibility_checkers:
                    self._compatibility_checkers.remove(checker)
                    return True
                return False
        except Exception:
            return False
    
    def register_lifecycle_callback(self, event: str, callback: Callable) -> bool:
        """Register a callback for plugin lifecycle events."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._lifecycle_callbacks[event].append(callback)
                return True
        except Exception:
            return False
    
    def unregister_lifecycle_callback(self, event: str, callback: Callable) -> bool:
        """Unregister a lifecycle callback."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if event in self._lifecycle_callbacks:
                    try:
                        self._lifecycle_callbacks[event].remove(callback)
                        return True
                    except ValueError:
                        return False
                return False
        except Exception:
            return False
    
    def export_plugin_registry(self, format: str = "json") -> str:
        """Export plugin registry data."""
        if not self._enabled:
            return ""
        
        try:
            with self._lock:
                export_data = {
                    "export_time": time.time(),
                    "total_plugins": self._total_plugins,
                    "active_plugins": self._active_plugins,
                    "plugins_by_category": {
                        cat.value: {
                            pid: {
                                "state": self._plugin_states.get(pid, "unknown"),
                                "metadata": self.get_plugin_metadata(pid)
                            }
                            for pid in plugins.keys()
                        }
                        for cat, plugins in self._plugin_categories.items()
                    },
                    "plugin_states": dict(self._plugin_states),
                    "plugin_dependencies": {
                        pid: list(deps) for pid, deps in self._plugin_dependencies.items()
                    },
                    "plugin_conflicts": {
                        pid: list(conflicts) for pid, conflicts in self._plugin_conflicts.items()
                    },
                    "statistics": self.get_plugin_registry_stats()
                }
                
                if format.lower() == "json":
                    return json.dumps(export_data, indent=2, default=str)
                else:
                    return str(export_data)
                    
        except Exception:
            return ""
    
    def clear_plugin_registry(self) -> bool:
        """Clear all plugins from the registry."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Clear component registry
                self._component_registry.clear_registry(ComponentType.PLUGIN)
                
                # Clear plugin-specific storage
                self._plugin_categories.clear()
                self._plugin_versions.clear()
                self._plugin_dependencies.clear()
                self._plugin_conflicts.clear()
                self._plugin_states.clear()
                
                # Reset statistics
                self._total_plugins = 0
                self._active_plugins = 0
                self._failed_plugins = 0
                self._last_plugin_load = 0.0
                
                return True
                
        except Exception:
            return False
    
    def _validate_plugin(self, plugin: PluginInterface, metadata: Optional[Dict[str, Any]]) -> bool:
        """Validate a plugin before registration."""
        try:
            # Check if plugin implements required interface
            if not isinstance(plugin, PluginInterface):
                return False
            
            # Apply validation rules
            for rule in self._validation_rules:
                if not rule(plugin, metadata):
                    return False
            
            # Basic validation
            if not hasattr(plugin, 'initialize'):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _check_plugin_compatibility(self, plugin: PluginInterface, 
                                  metadata: Optional[Dict[str, Any]]) -> PluginCompatibility:
        """Check plugin compatibility."""
        try:
            # Apply compatibility checkers
            for checker in self._compatibility_checkers:
                result = checker(plugin, metadata)
                if result == PluginCompatibility.INCOMPATIBLE:
                    return PluginCompatibility.INCOMPATIBLE
            
            # Basic compatibility check
            if metadata and "compatibility" in metadata:
                compat_info = metadata["compatibility"]
                if "python_version" in compat_info:
                    # Simple Python version check
                    import sys
                    required_version = compat_info["python_version"]
                    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                    if current_version < required_version:
                        return PluginCompatibility.INCOMPATIBLE
            
            return PluginCompatibility.FULLY_COMPATIBLE
            
        except Exception:
            return PluginCompatibility.UNKNOWN
    
    def _prepare_plugin_metadata(self, plugin_id: str, plugin: PluginInterface,
                                metadata: Optional[Dict[str, Any]], 
                                compatibility: PluginCompatibility) -> Dict[str, Any]:
        """Prepare plugin metadata for registration."""
        base_metadata = {
            "id": plugin_id,
            "type": "plugin",
            "class_name": plugin.__class__.__name__,
            "module_name": plugin.__class__.__module__,
            "registration_time": time.time(),
            "status": ComponentStatus.REGISTERED.value,
            "compatibility": compatibility.value,
            "version": metadata.get("version", "1.0.0") if metadata else "1.0.0",
            "description": metadata.get("description", "") if metadata else "",
            "tags": metadata.get("tags", []) if metadata else [],
            "dependencies": metadata.get("dependencies", []) if metadata else [],
            "author": metadata.get("author", "") if metadata else "",
            "license": metadata.get("license", "") if metadata else "",
            "category": metadata.get("category", PluginCategory.CUSTOM.value) if metadata else PluginCategory.CUSTOM.value
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        return base_metadata
    
    def _store_plugin_info(self, plugin_id: str, plugin: PluginInterface, metadata: Dict[str, Any]) -> None:
        """Store plugin-specific information."""
        # Store by category
        category = PluginCategory(metadata.get("category", PluginCategory.CUSTOM.value))
        self._plugin_categories[category][plugin_id] = plugin
        
        # Store by version
        name = metadata.get("name", plugin_id)
        version = metadata.get("version", "1.0.0")
        if name not in self._plugin_versions:
            self._plugin_versions[name] = {}
        self._plugin_versions[name][version] = plugin_id
        
        # Store dependencies
        dependencies = metadata.get("dependencies", [])
        if dependencies:
            self._plugin_dependencies[plugin_id] = set(dependencies)
        
        # Store conflicts
        conflicts = metadata.get("conflicts", [])
        if conflicts:
            self._plugin_conflicts[plugin_id] = set(conflicts)
        
        # Set initial state
        self._plugin_states[plugin_id] = "inactive"
    
    def _remove_plugin_info(self, plugin_id: str) -> None:
        """Remove plugin-specific information."""
        # Remove from categories
        for category in self._plugin_categories.values():
            if plugin_id in category:
                del category[plugin_id]
        
        # Remove from versions
        for versions in self._plugin_versions.values():
            versions_to_remove = [v for v, pid in versions.items() if pid == plugin_id]
            for version in versions_to_remove:
                del versions[version]
        
        # Remove dependencies and conflicts
        if plugin_id in self._plugin_dependencies:
            del self._plugin_dependencies[plugin_id]
        if plugin_id in self._plugin_conflicts:
            del self._plugin_conflicts[plugin_id]
        
        # Remove state
        if plugin_id in self._plugin_states:
            del self._plugin_states[plugin_id]
    
    def _can_unregister_plugin(self, plugin_id: str) -> bool:
        """Check if a plugin can be unregistered."""
        # Check if other plugins depend on this one
        for deps in self._plugin_dependencies.values():
            if plugin_id in deps:
                return False
        
        return True
    
    def _check_plugin_dependencies(self, plugin_id: str) -> bool:
        """Check if plugin dependencies are satisfied."""
        if plugin_id not in self._plugin_dependencies:
            return True
        
        dependencies = self._plugin_dependencies[plugin_id]
        for dep_id in dependencies:
            if not self.has_plugin(dep_id):
                return False
            if self._plugin_states.get(dep_id) != "active":
                return False
        
        return True
    
    def _check_plugin_conflicts(self, plugin_id: str) -> bool:
        """Check if plugin conflicts with active plugins."""
        if plugin_id not in self._plugin_conflicts:
            return True
        
        conflicts = self._plugin_conflicts[plugin_id]
        active_plugins = self.get_active_plugins()
        
        for conflict_id in conflicts:
            if conflict_id in active_plugins:
                return False
        
        return True
    
    def _trigger_lifecycle_callbacks(self, event: str, plugin_id: str, 
                                   plugin: PluginInterface, metadata: Dict[str, Any]) -> None:
        """Trigger lifecycle callbacks for a plugin event."""
        for callback in self._lifecycle_callbacks[event]:
            try:
                callback(event, plugin_id, plugin, metadata)
            except Exception:
                # Continue with other callbacks
                pass
    
    def _matches_plugin_search(self, query: str, metadata: Dict[str, Any]) -> bool:
        """Check if plugin metadata matches search query."""
        query_lower = query.lower()
        
        # Search in various metadata fields
        searchable_fields = [
            metadata.get("id", ""),
            metadata.get("class_name", ""),
            metadata.get("description", ""),
            " ".join(metadata.get("tags", [])),
            metadata.get("author", ""),
            metadata.get("category", "")
        ]
        
        return any(query_lower in field.lower() for field in searchable_fields if field)
    
    def get_plugin_registry_stats(self) -> Dict[str, Any]:
        """Get plugin registry statistics."""
        return {
            "total_plugins": self._total_plugins,
            "active_plugins": self._active_plugins,
            "failed_plugins": self._failed_plugins,
            "success_rate": (self._total_plugins / (self._total_plugins + self._failed_plugins) 
                           if (self._total_plugins + self._failed_plugins) > 0 else 0),
            "plugins_by_category": {
                cat.value: len(plugins)
                for cat, plugins in self._plugin_categories.items()
            },
            "total_dependencies": sum(len(deps) for deps in self._plugin_dependencies.values()),
            "total_conflicts": sum(len(conflicts) for conflicts in self._plugin_conflicts.values()),
            "last_plugin_load": self._last_plugin_load,
            "enabled": self._enabled
        }
    
    def reset_plugin_registry_stats(self) -> None:
        """Reset plugin registry statistics."""
        with self._lock:
            self._total_plugins = 0
            self._active_plugins = 0
            self._failed_plugins = 0
            self._last_plugin_load = 0.0
