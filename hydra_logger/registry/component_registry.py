"""
Generic Component Registry for Hydra-Logger

This module provides a comprehensive generic component registry system for
managing all types of components including loggers, handlers, formatters,
plugins, monitors, and custom components. It includes lifecycle management,
dependency tracking, validation, and search capabilities.

FEATURES:
- Generic component registration and management
- Component lifecycle tracking and callbacks
- Dependency management and validation
- Component search and filtering
- Metadata storage and retrieval
- Statistics and analytics
- Export/import functionality

COMPONENT TYPES:
- Logger: Logging components
- Handler: Log handlers
- Formatter: Log formatters
- Plugin: Plugin components
- Monitor: Monitoring components
- Security: Security components
- Factory: Factory components
- Utility: Utility components
- Custom: Custom components

USAGE:
    from hydra_logger.registry import ComponentRegistry, ComponentType
    
    # Create component registry
    registry = ComponentRegistry(enabled=True)
    
    # Register a component
    success = registry.register_component(
        ComponentType.LOGGER,
        "my_logger",
        my_logger_instance,
        metadata={"version": "1.0.0", "author": "Developer"},
        aliases=["logger", "main_logger"]
    )
    
    # Get component
    component = registry.get_component(ComponentType.LOGGER, "my_logger")
    
    # Search components
    results = registry.search_components("logger")
    
    # Get registry statistics
    stats = registry.get_registry_stats()
"""

import time
import threading
import json
from typing import Any, Dict, List, Optional, Callable, Type, Union
from collections import defaultdict, deque
from enum import Enum
from ..interfaces.registry import RegistryInterface


class ComponentType(Enum):
    """Types of components that can be registered."""
    LOGGER = "logger"
    HANDLER = "handler"
    FORMATTER = "formatter"
    PLUGIN = "plugin"
    MONITOR = "monitor"
    SECURITY = "security"
    FACTORY = "factory"
    UTILITY = "utility"
    CUSTOM = "custom"


class ComponentStatus(Enum):
    """Component status states."""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"


class ComponentRegistry(RegistryInterface):
    """Real generic component registry for comprehensive component management."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        
        # Component storage
        self._components = defaultdict(dict)  # type -> {id -> component}
        self._component_metadata = defaultdict(dict)  # type -> {id -> metadata}
        self._component_aliases = defaultdict(dict)  # alias -> (type, id)
        
        # Component discovery and loading
        self._discovery_callbacks = defaultdict(list)  # type -> [callbacks]
        self._auto_discovery = True
        self._discovery_paths = []
        
        # Component lifecycle management
        self._lifecycle_callbacks = defaultdict(list)  # event -> [callbacks]
        self._component_dependencies = defaultdict(set)  # id -> {dependency_ids}
        self._component_dependents = defaultdict(set)  # id -> {dependent_ids}
        
        # Component validation and compatibility
        self._validation_rules = defaultdict(list)  # type -> [validation_rules]
        self._compatibility_matrix = {}
        
        # Threading
        self._lock = threading.RLock()
        
        # Statistics
        self._total_registrations = 0
        self._total_unregistrations = 0
        self._failed_registrations = 0
        self._last_registration_time = 0.0
    
    def register_component(self, component_type: ComponentType, component_id: str, 
                          component: Any, metadata: Optional[Dict[str, Any]] = None,
                          aliases: Optional[List[str]] = None) -> bool:
        """
        Register a component in the registry.
        
        Args:
            component_type: Type of component
            component_id: Unique identifier for the component
            component: The component instance
            metadata: Additional component metadata
            aliases: Alternative names for the component
            
        Returns:
            True if registration successful
        """
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Check if component already exists
                if component_id in self._components[component_type]:
                    return False
                
                # Validate component
                if not self._validate_component(component_type, component, metadata):
                    self._failed_registrations += 1
                    return False
                
                # Store component
                self._components[component_type][component_id] = component
                
                # Store metadata
                component_metadata = {
                    "id": component_id,
                    "type": component_type.value,
                    "class_name": component.__class__.__name__,
                    "module_name": component.__class__.__module__,
                    "registration_time": time.time(),
                    "status": ComponentStatus.REGISTERED.value,
                    "version": metadata.get("version", "1.0.0") if metadata else "1.0.0",
                    "description": metadata.get("description", "") if metadata else "",
                    "tags": metadata.get("tags", []) if metadata else [],
                    "dependencies": metadata.get("dependencies", []) if metadata else [],
                    "compatibility": metadata.get("compatibility", {}) if metadata else {},
                    "author": metadata.get("author", "") if metadata else "",
                    "license": metadata.get("license", "") if metadata else ""
                }
                
                self._component_metadata[component_type][component_id] = component_metadata
                
                # Register aliases
                if aliases:
                    for alias in aliases:
                        self._component_aliases[alias] = (component_type, component_id)
                
                # Update dependencies
                self._update_component_dependencies(component_id, component_metadata.get("dependencies", []))
                
                # Trigger discovery callbacks
                self._trigger_discovery_callbacks(component_type, component_id, component, component_metadata)
                
                # Trigger lifecycle callbacks
                self._trigger_lifecycle_callbacks("registered", component_type, component_id, component)
                
                # Update statistics
                self._total_registrations += 1
                self._last_registration_time = time.time()
                
                return True
                
        except Exception as e:
            self._failed_registrations += 1
            return False
    
    def unregister_component(self, component_type: ComponentType, component_id: str) -> bool:
        """
        Unregister a component from the registry.
        
        Args:
            component_type: Type of component
            component_id: Component identifier
            
        Returns:
            True if unregistration successful
        """
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if component_type not in self._components or component_id not in self._components[component_type]:
                    return False
                
                # Get component before removal
                component = self._components[component_type][component_id]
                metadata = self._component_metadata[component_type].get(component_id, {})
                
                # Check if component can be unregistered
                if not self._can_unregister_component(component_type, component_id):
                    return False
                
                # Remove component
                del self._components[component_type][component_id]
                
                # Remove metadata
                if component_id in self._component_metadata[component_type]:
                    del self._component_metadata[component_type][component_id]
                
                # Remove aliases
                aliases_to_remove = []
                for alias, (comp_type, comp_id) in self._component_aliases.items():
                    if comp_type == component_type and comp_id == component_id:
                        aliases_to_remove.append(alias)
                
                for alias in aliases_to_remove:
                    del self._component_aliases[alias]
                
                # Update dependencies
                self._remove_component_dependencies(component_id)
                
                # Trigger lifecycle callbacks
                self._trigger_lifecycle_callbacks("unregistered", component_type, component_id, component)
                
                # Update statistics
                self._total_unregistrations += 1
                
                return True
                
        except Exception:
            return False
    
    def get_component(self, component_type: ComponentType, component_id: str) -> Optional[Any]:
        """Get a component by type and ID."""
        if not self._enabled:
            return None
        
        try:
            with self._lock:
                return self._components[component_type].get(component_id)
        except Exception:
            return None
    
    def get_component_by_alias(self, alias: str) -> Optional[Any]:
        """Get a component by alias."""
        if not self._enabled or alias not in self._component_aliases:
            return None
        
        try:
            with self._lock:
                component_type, component_id = self._component_aliases[alias]
                return self.get_component(component_type, component_id)
        except Exception:
            return None
    
    def get_components_by_type(self, component_type: ComponentType) -> Dict[str, Any]:
        """Get all components of a specific type."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                return self._components[component_type].copy()
        except Exception:
            return {}
    
    def get_component_metadata(self, component_type: ComponentType, component_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific component."""
        if not self._enabled:
            return None
        
        try:
            with self._lock:
                return self._component_metadata[component_type].get(component_id, {}).copy()
        except Exception:
            return None
    
    def get_all_components(self) -> Dict[ComponentType, Dict[str, Any]]:
        """Get all registered components."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                return {comp_type: components.copy() for comp_type, components in self._components.items()}
        except Exception:
            return {}
    
    def get_component_count(self, component_type: Optional[ComponentType] = None) -> int:
        """Get count of components, optionally filtered by type."""
        if not self._enabled:
            return 0
        
        try:
            with self._lock:
                if component_type:
                    return len(self._components[component_type])
                else:
                    return sum(len(components) for components in self._components.values())
        except Exception:
            return 0
    
    def has_component(self, component_type: ComponentType, component_id: str) -> bool:
        """Check if a component exists."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                return component_id in self._components[component_type]
        except Exception:
            return False
    
    def list_component_types(self) -> List[ComponentType]:
        """List all registered component types."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._components.keys())
        except Exception:
            return []
    
    def list_components(self, component_type: ComponentType) -> List[str]:
        """List all component IDs of a specific type."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._components[component_type].keys())
        except Exception:
            return []
    
    def list_aliases(self) -> List[str]:
        """List all registered aliases."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._component_aliases.keys())
        except Exception:
            return []
    
    def update_component_metadata(self, component_type: ComponentType, component_id: str,
                                 metadata_updates: Dict[str, Any]) -> bool:
        """Update component metadata."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if component_type not in self._component_metadata or component_id not in self._component_metadata[component_type]:
                    return False
                
                current_metadata = self._component_metadata[component_type][component_id]
                current_metadata.update(metadata_updates)
                current_metadata["last_updated"] = time.time()
                
                return True
                
        except Exception:
            return False
    
    def set_component_status(self, component_type: ComponentType, component_id: str,
                            status: ComponentStatus) -> bool:
        """Set component status."""
        return self.update_component_metadata(component_type, component_id, {"status": status.value})
    
    def get_component_status(self, component_type: ComponentType, component_id: str) -> Optional[ComponentStatus]:
        """Get component status."""
        metadata = self.get_component_metadata(component_type, component_id)
        if metadata and "status" in metadata:
            try:
                return ComponentStatus(metadata["status"])
            except ValueError:
                return ComponentStatus.UNKNOWN
        return None
    
    def register_discovery_callback(self, component_type: ComponentType, callback: Callable) -> bool:
        """Register a callback for component discovery events."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._discovery_callbacks[component_type].append(callback)
                return True
        except Exception:
            return False
    
    def unregister_discovery_callback(self, component_type: ComponentType, callback: Callable) -> bool:
        """Unregister a discovery callback."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if component_type in self._discovery_callbacks:
                    try:
                        self._discovery_callbacks[component_type].remove(callback)
                        return True
                    except ValueError:
                        return False
                return False
        except Exception:
            return False
    
    def register_lifecycle_callback(self, event: str, callback: Callable) -> bool:
        """Register a callback for component lifecycle events."""
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
    
    def add_validation_rule(self, component_type: ComponentType, rule: Callable) -> bool:
        """Add a validation rule for a component type."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._validation_rules[component_type].append(rule)
                return True
        except Exception:
            return False
    
    def remove_validation_rule(self, component_type: ComponentType, rule: Callable) -> bool:
        """Remove a validation rule."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if component_type in self._validation_rules:
                    try:
                        self._validation_rules[component_type].remove(rule)
                        return True
                    except ValueError:
                        return False
                return False
        except Exception:
            return False
    
    def search_components(self, query: str, component_type: Optional[ComponentType] = None) -> List[Dict[str, Any]]:
        """Search for components by query string."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                results = []
                search_types = [component_type] if component_type else self._components.keys()
                
                for comp_type in search_types:
                    for comp_id, metadata in self._component_metadata[comp_type].items():
                        if self._matches_search_query(query, metadata):
                            results.append({
                                "type": comp_type.value,
                                "id": comp_id,
                                "metadata": metadata.copy()
                            })
                
                return results
                
        except Exception:
            return []
    
    def export_registry(self, format: str = "json") -> str:
        """Export registry data."""
        if not self._enabled:
            return ""
        
        try:
            with self._lock:
                export_data = {
                    "export_time": time.time(),
                    "total_components": self.get_component_count(),
                    "components_by_type": {
                        comp_type.value: {
                            comp_id: metadata.copy()
                            for comp_id, metadata in self._component_metadata[comp_type].items()
                        }
                        for comp_type in self._components.keys()
                    },
                    "aliases": dict(self._component_aliases),
                    "statistics": self.get_registry_stats()
                }
                
                if format.lower() == "json":
                    return json.dumps(export_data, indent=2, default=str)
                else:
                    return str(export_data)
                    
        except Exception:
            return ""
    
    def clear_registry(self, component_type: Optional[ComponentType] = None) -> bool:
        """Clear all components or components of a specific type."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if component_type:
                    if component_type in self._components:
                        del self._components[component_type]
                    if component_type in self._component_metadata:
                        del self._component_metadata[component_type]
                else:
                    self._components.clear()
                    self._component_metadata.clear()
                    self._component_aliases.clear()
                
                return True
                
        except Exception:
            return False
    
    def _validate_component(self, component_type: ComponentType, component: Any, 
                           metadata: Optional[Dict[str, Any]]) -> bool:
        """Validate a component before registration."""
        try:
            # Check if component is not None
            if component is None:
                return False
            
            # Apply validation rules
            for rule in self._validation_rules[component_type]:
                if not rule(component, metadata):
                    return False
            
            # Basic validation
            if not hasattr(component, '__class__'):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _can_unregister_component(self, component_type: ComponentType, component_id: str) -> bool:
        """Check if a component can be unregistered."""
        # Check if other components depend on this one
        if component_id in self._component_dependents:
            dependents = self._component_dependents[component_id]
            if dependents:
                return False
        
        return True
    
    def _update_component_dependencies(self, component_id: str, dependencies: List[str]) -> None:
        """Update component dependency tracking."""
        # Remove old dependencies
        self._remove_component_dependencies(component_id)
        
        # Add new dependencies
        for dep_id in dependencies:
            self._component_dependencies[component_id].add(dep_id)
            if dep_id not in self._component_dependents:
                self._component_dependents[dep_id] = set()
            self._component_dependents[dep_id].add(component_id)
    
    def _remove_component_dependencies(self, component_id: str) -> None:
        """Remove component dependency tracking."""
        # Remove from dependents of other components
        if component_id in self._component_dependencies:
            for dep_id in self._component_dependencies[component_id]:
                if dep_id in self._component_dependents:
                    self._component_dependents[dep_id].discard(component_id)
            del self._component_dependencies[component_id]
        
        # Remove from dependents list
        if component_id in self._component_dependents:
            del self._component_dependents[component_id]
    
    def _trigger_discovery_callbacks(self, component_type: ComponentType, component_id: str,
                                   component: Any, metadata: Dict[str, Any]) -> None:
        """Trigger discovery callbacks for a new component."""
        for callback in self._discovery_callbacks[component_type]:
            try:
                callback(component_type, component_id, component, metadata)
            except Exception:
                # Continue with other callbacks
                pass
    
    def _trigger_lifecycle_callbacks(self, event: str, component_type: ComponentType,
                                   component_id: str, component: Any) -> None:
        """Trigger lifecycle callbacks for a component event."""
        for callback in self._lifecycle_callbacks[event]:
            try:
                callback(event, component_type, component_id, component)
            except Exception:
                # Continue with other callbacks
                pass
    
    def _matches_search_query(self, query: str, metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches search query."""
        query_lower = query.lower()
        
        # Search in various metadata fields
        searchable_fields = [
            metadata.get("id", ""),
            metadata.get("class_name", ""),
            metadata.get("description", ""),
            " ".join(metadata.get("tags", [])),
            metadata.get("author", "")
        ]
        
        return any(query_lower in field.lower() for field in searchable_fields if field)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_registrations": self._total_registrations,
            "total_unregistrations": self._total_unregistrations,
            "failed_registrations": self._failed_registrations,
            "success_rate": (self._total_registrations / (self._total_registrations + self._failed_registrations) 
                           if (self._total_registrations + self._failed_registrations) > 0 else 0),
            "total_components": self.get_component_count(),
            "components_by_type": {
                comp_type.value: len(components)
                for comp_type, components in self._components.items()
            },
            "total_aliases": len(self._component_aliases),
            "last_registration_time": self._last_registration_time,
            "enabled": self._enabled
        }
    
    def reset_registry_stats(self) -> None:
        """Reset registry statistics."""
        with self._lock:
            self._total_registrations = 0
            self._total_unregistrations = 0
            self._failed_registrations = 0
            self._last_registration_time = 0.0
