"""
Handler-Specific Registry for Hydra-Logger

This module provides a specialized registry system for managing log handlers
with advanced capabilities including handler types, capabilities detection,
formatter integration, and performance tracking. It extends the generic
component registry with handler-specific functionality.

FEATURES:
- Handler registration and lifecycle management
- Handler type classification and organization
- Capability detection and management
- Formatter and filter integration
- Performance metrics tracking
- Handler search and filtering
- Export/import functionality

HANDLER TYPES:
- Console: Console output handlers
- File: File output handlers
- Stream: Stream output handlers
- Rotating: Rotating file handlers
- Network: Network-based handlers
- System: System log handlers
- Database: Database handlers
- Queue: Queue-based handlers
- Cloud: Cloud service handlers
- Composite: Composite handlers
- Fallback: Fallback handlers
- Custom: Custom handlers

HANDLER CAPABILITIES:
- Async: Asynchronous processing
- Buffered: Buffering support
- Compressed: Compression support
- Encrypted: Encryption support
- Rotated: Log rotation support
- Filtered: Filtering capabilities
- Formatted: Formatting support
- Monitored: Monitoring support

USAGE:
    from hydra_logger.registry import HandlerRegistry, HandlerType, HandlerCapability
    
    # Create handler registry
    registry = HandlerRegistry(enabled=True)
    
    # Register a handler
    success = registry.register_handler(
        "my_handler",
        my_handler_instance,
        HandlerType.FILE,
        metadata={"version": "1.0.0", "author": "Developer"}
    )
    
    # Get handler by type
    handlers = registry.get_handlers_by_type(HandlerType.FILE)
    
    # Get handlers by capability
    async_handlers = registry.get_handlers_by_capability(HandlerCapability.ASYNC)
    
    # Add formatter to handler
    registry.add_handler_formatter("my_handler", "json_formatter")
    
    # Search handlers
    results = registry.search_handlers("file")
"""

import time
import threading
import json
from typing import Any, Dict, List, Optional, Callable, Type
from collections import defaultdict, deque
from enum import Enum
from ..interfaces.registry import RegistryInterface
from ..interfaces.handler import HandlerInterface
from .component_registry import ComponentRegistry, ComponentType, ComponentStatus


class HandlerType(Enum):
    """Types of handlers."""
    CONSOLE = "console"
    FILE = "file"
    STREAM = "stream"
    ROTATING = "rotating"
    NETWORK = "network"
    SYSTEM = "system"
    DATABASE = "database"
    QUEUE = "queue"
    CLOUD = "cloud"
    COMPOSITE = "composite"
    FALLBACK = "fallback"
    CUSTOM = "custom"


class HandlerCapability(Enum):
    """Handler capabilities."""
    ASYNC = "async"
    BUFFERED = "buffered"
    COMPRESSED = "compressed"
    ENCRYPTED = "encrypted"
    ROTATED = "rotated"
    FILTERED = "filtered"
    FORMATTED = "formatted"
    MONITORED = "monitored"


class HandlerRegistry(RegistryInterface):
    """Real handler-specific registry with advanced handler management capabilities."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        
        # Core component registry
        self._component_registry = ComponentRegistry(enabled=enabled)
        
        # Handler-specific storage
        self._handler_types = defaultdict(dict)  # type -> {id -> handler}
        self._handler_capabilities = defaultdict(set)  # handler_id -> {capabilities}
        self._handler_formatters = defaultdict(list)  # handler_id -> [formatter_ids]
        self._handler_filters = defaultdict(list)  # handler_id -> [filter_ids]
        self._handler_metrics = defaultdict(dict)  # handler_id -> metrics
        
        # Handler discovery and loading
        self._discovery_paths = []
        self._auto_discovery = True
        self._discovery_callbacks = []
        
        # Handler validation and compatibility
        self._validation_rules = []
        self._capability_checkers = []
        self._performance_requirements = {}
        
        # Handler lifecycle management
        self._lifecycle_callbacks = defaultdict(list)  # event -> [callbacks]
        self._handler_states = {}  # handler_id -> state
        
        # Threading
        self._lock = threading.RLock()
        
        # Statistics
        self._total_handlers = 0
        self._active_handlers = 0
        self._failed_handlers = 0
        self._last_handler_load = 0.0
    
    def register_handler(self, handler_id: str, handler: HandlerInterface, 
                        handler_type: HandlerType, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a handler in the registry.
        
        Args:
            handler_id: Unique identifier for the handler
            handler: The handler instance
            handler_type: Type of handler
            metadata: Additional handler metadata
            
        Returns:
            True if registration successful
        """
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Validate handler
                if not self._validate_handler(handler, metadata):
                    self._failed_handlers += 1
                    return False
                
                # Check capabilities
                capabilities = self._detect_handler_capabilities(handler, metadata)
                
                # Prepare metadata
                handler_metadata = self._prepare_handler_metadata(handler_id, handler, handler_type, metadata, capabilities)
                
                # Register in component registry
                success = self._component_registry.register_component(
                    ComponentType.HANDLER, handler_id, handler, handler_metadata
                )
                
                if success:
                    # Store handler-specific information
                    self._store_handler_info(handler_id, handler, handler_type, capabilities)
                    
                    # Update statistics
                    self._total_handlers += 1
                    self._last_handler_load = time.time()
                    
                    # Trigger lifecycle callbacks
                    self._trigger_lifecycle_callbacks("registered", handler_id, handler, handler_metadata)
                    
                    return True
                else:
                    self._failed_handlers += 1
                    return False
                    
        except Exception as e:
            self._failed_handlers += 1
            return False
    
    def unregister_handler(self, handler_id: str) -> bool:
        """
        Unregister a handler from the registry.
        
        Args:
            handler_id: Handler identifier
            
        Returns:
            True if unregistration successful
        """
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Get handler before removal
                handler = self._component_registry.get_component(ComponentType.HANDLER, handler_id)
                metadata = self._component_registry.get_component_metadata(ComponentType.HANDLER, handler_id)
                
                if not handler:
                    return False
                
                # Check if handler can be unregistered
                if not self._can_unregister_handler(handler_id):
                    return False
                
                # Unregister from component registry
                success = self._component_registry.unregister_component(ComponentType.HANDLER, handler_id)
                
                if success:
                    # Remove handler-specific information
                    self._remove_handler_info(handler_id)
                    
                    # Update statistics
                    if handler_id in self._handler_states and self._handler_states[handler_id] == "active":
                        self._active_handlers -= 1
                    
                    # Trigger lifecycle callbacks
                    self._trigger_lifecycle_callbacks("unregistered", handler_id, handler, metadata)
                    
                    return True
                else:
                    return False
                    
        except Exception:
            return False
    
    def get_handler(self, handler_id: str) -> Optional[HandlerInterface]:
        """Get a handler by ID."""
        if not self._enabled:
            return None
        
        return self._component_registry.get_component(ComponentType.HANDLER, handler_id)
    
    def get_handlers_by_type(self, handler_type: HandlerType) -> Dict[str, HandlerInterface]:
        """Get all handlers of a specific type."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                return self._handler_types[handler_type].copy()
        except Exception:
            return {}
    
    def get_handlers_by_capability(self, capability: HandlerCapability) -> List[HandlerInterface]:
        """Get handlers with a specific capability."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                handlers = []
                for handler_id, capabilities in self._handler_capabilities.items():
                    if capability in capabilities:
                        handler = self.get_handler(handler_id)
                        if handler:
                            handlers.append(handler)
                return handlers
        except Exception:
            return []
    
    def get_handler_metadata(self, handler_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific handler."""
        if not self._enabled:
            return None
        
        return self._component_registry.get_component_metadata(ComponentType.HANDLER, handler_id)
    
    def get_all_handlers(self) -> Dict[str, HandlerInterface]:
        """Get all registered handlers."""
        if not self._enabled:
            return {}
        
        return self._component_registry.get_components_by_type(ComponentType.HANDLER)
    
    def get_handler_count(self, handler_type: Optional[HandlerType] = None) -> int:
        """Get count of handlers, optionally filtered by type."""
        if not self._enabled:
            return 0
        
        try:
            with self._lock:
                if handler_type:
                    return len(self._handler_types[handler_type])
                else:
                    return self._component_registry.get_component_count(ComponentType.HANDLER)
        except Exception:
            return 0
    
    def has_handler(self, handler_id: str) -> bool:
        """Check if a handler exists."""
        if not self._enabled:
            return False
        
        return self._component_registry.has_component(ComponentType.HANDLER, handler_id)
    
    def list_handler_types(self) -> List[HandlerType]:
        """List all handler types."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._handler_types.keys())
        except Exception:
            return []
    
    def list_handlers(self, handler_type: Optional[HandlerType] = None) -> List[str]:
        """List all handler IDs, optionally filtered by type."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                if handler_type:
                    return list(self._handler_types[handler_type].keys())
                else:
                    return self._component_registry.list_components(ComponentType.HANDLER)
        except Exception:
            return []
    
    def activate_handler(self, handler_id: str) -> bool:
        """Activate a handler."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if not self.has_handler(handler_id):
                    return False
                
                # Check handler capabilities
                if not self._check_handler_capabilities(handler_id):
                    return False
                
                # Update handler state
                self._handler_states[handler_id] = "active"
                self._active_handlers += 1
                
                # Update component status
                self._component_registry.set_component_status(
                    ComponentType.HANDLER, handler_id, ComponentStatus.ACTIVE
                )
                
                # Trigger lifecycle callbacks
                handler = self.get_handler(handler_id)
                metadata = self.get_handler_metadata(handler_id)
                self._trigger_lifecycle_callbacks("activated", handler_id, handler, metadata)
                
                return True
                
        except Exception:
            return False
    
    def deactivate_handler(self, handler_id: str) -> bool:
        """Deactivate a handler."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if not self.has_handler(handler_id):
                    return False
                
                # Update handler state
                if handler_id in self._handler_states and self._handler_states[handler_id] == "active":
                    self._handler_states[handler_id] = "inactive"
                    self._active_handlers -= 1
                
                # Update component status
                self._component_registry.set_component_status(
                    ComponentType.HANDLER, handler_id, ComponentStatus.INACTIVE
                )
                
                # Trigger lifecycle callbacks
                handler = self.get_handler(handler_id)
                metadata = self.get_handler_metadata(handler_id)
                self._trigger_lifecycle_callbacks("deactivated", handler_id, handler, metadata)
                
                return True
                
        except Exception:
            return False
    
    def get_handler_state(self, handler_id: str) -> str:
        """Get handler state."""
        if not self._enabled:
            return "unknown"
        
        return self._handler_states.get(handler_id, "unknown")
    
    def get_active_handlers(self) -> List[str]:
        """Get list of active handler IDs."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return [hid for hid, state in self._handler_states.items() if state == "active"]
        except Exception:
            return []
    
    def get_inactive_handlers(self) -> List[str]:
        """Get list of inactive handler IDs."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return [hid for hid, state in self._handler_states.items() if state == "inactive"]
        except Exception:
            return []
    
    def get_handler_capabilities(self, handler_id: str) -> List[HandlerCapability]:
        """Get capabilities for a handler."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._handler_capabilities.get(handler_id, set()))
        except Exception:
            return []
    
    def has_handler_capability(self, handler_id: str, capability: HandlerCapability) -> bool:
        """Check if a handler has a specific capability."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                return capability in self._handler_capabilities.get(handler_id, set())
        except Exception:
            return False
    
    def add_handler_formatter(self, handler_id: str, formatter_id: str) -> bool:
        """Add a formatter to a handler."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if handler_id not in self._handler_formatters:
                    self._handler_formatters[handler_id] = []
                
                if formatter_id not in self._handler_formatters[handler_id]:
                    self._handler_formatters[handler_id].append(formatter_id)
                    return True
                
                return False
                
        except Exception:
            return False
    
    def remove_handler_formatter(self, handler_id: str, formatter_id: str) -> bool:
        """Remove a formatter from a handler."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if handler_id in self._handler_formatters:
                    try:
                        self._handler_formatters[handler_id].remove(formatter_id)
                        return True
                    except ValueError:
                        return False
                return False
                
        except Exception:
            return False
    
    def get_handler_formatters(self, handler_id: str) -> List[str]:
        """Get formatters for a handler."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return self._handler_formatters.get(handler_id, []).copy()
        except Exception:
            return []
    
    def add_handler_filter(self, handler_id: str, filter_id: str) -> bool:
        """Add a filter to a handler."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if handler_id not in self._handler_filters:
                    self._handler_filters[handler_id] = []
                
                if filter_id not in self._handler_filters[handler_id]:
                    self._handler_filters[handler_id].append(filter_id)
                    return True
                
                return False
                
        except Exception:
            return False
    
    def remove_handler_filter(self, handler_id: str, filter_id: str) -> bool:
        """Remove a filter from a handler."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if handler_id in self._handler_filters:
                    try:
                        self._handler_filters[handler_id].remove(filter_id)
                        return True
                    except ValueError:
                        return False
                return False
                
        except Exception:
            return False
    
    def get_handler_filters(self, handler_id: str) -> List[str]:
        """Get filters for a handler."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return self._handler_filters.get(handler_id, []).copy()
        except Exception:
            return []
    
    def update_handler_metrics(self, handler_id: str, metrics: Dict[str, Any]) -> bool:
        """Update handler metrics."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._handler_metrics[handler_id] = metrics.copy()
                return True
        except Exception:
            return False
    
    def get_handler_metrics(self, handler_id: str) -> Dict[str, Any]:
        """Get handler metrics."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                return self._handler_metrics.get(handler_id, {}).copy()
        except Exception:
            return {}
    
    def search_handlers(self, query: str, handler_type: Optional[HandlerType] = None) -> List[Dict[str, Any]]:
        """Search for handlers by query string."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                results = []
                search_types = [handler_type] if handler_type else self._handler_types.keys()
                
                for htype in search_types:
                    for handler_id, handler in self._handler_types[htype].items():
                        metadata = self.get_handler_metadata(handler_id)
                        if metadata and self._matches_handler_search(query, metadata):
                            results.append({
                                "id": handler_id,
                                "type": htype.value,
                                "handler": handler,
                                "metadata": metadata.copy(),
                                "state": self._handler_states.get(handler_id, "unknown"),
                                "capabilities": list(self._handler_capabilities.get(handler_id, set()))
                            })
                
                return results
                
        except Exception:
            return []
    
    def add_validation_rule(self, rule: Callable) -> bool:
        """Add a handler validation rule."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._validation_rules.append(rule)
                return True
        except Exception:
            return False
    
    def remove_validation_rule(self, rule: Callable) -> bool:
        """Remove a handler validation rule."""
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
    
    def add_capability_checker(self, checker: Callable) -> bool:
        """Add a handler capability checker."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._capability_checkers.append(checker)
                return True
        except Exception:
            return False
    
    def remove_capability_checker(self, checker: Callable) -> bool:
        """Remove a handler capability checker."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if checker in self._capability_checkers:
                    self._capability_checkers.remove(checker)
                    return True
                return False
        except Exception:
            return False
    
    def register_lifecycle_callback(self, event: str, callback: Callable) -> bool:
        """Register a callback for handler lifecycle events."""
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
    
    def export_handler_registry(self, format: str = "json") -> str:
        """Export handler registry data."""
        if not self._enabled:
            return ""
        
        try:
            with self._lock:
                export_data = {
                    "export_time": time.time(),
                    "total_handlers": self._total_handlers,
                    "active_handlers": self._active_handlers,
                    "handlers_by_type": {
                        htype.value: {
                            hid: {
                                "state": self._handler_states.get(hid, "unknown"),
                                "capabilities": list(self._handler_capabilities.get(hid, set())),
                                "formatters": self._handler_formatters.get(hid, []),
                                "filters": self._handler_filters.get(hid, []),
                                "metadata": self.get_handler_metadata(hid)
                            }
                            for hid in handlers.keys()
                        }
                        for htype, handlers in self._handler_types.items()
                    },
                    "handler_states": dict(self._handler_states),
                    "handler_capabilities": {
                        hid: list(caps) for hid, caps in self._handler_capabilities.items()
                    },
                    "statistics": self.get_handler_registry_stats()
                }
                
                if format.lower() == "json":
                    return json.dumps(export_data, indent=2, default=str)
                else:
                    return str(export_data)
                    
        except Exception:
            return ""
    
    def clear_handler_registry(self) -> bool:
        """Clear all handlers from the registry."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Clear component registry
                self._component_registry.clear_registry(ComponentType.HANDLER)
                
                # Clear handler-specific storage
                self._handler_types.clear()
                self._handler_capabilities.clear()
                self._handler_formatters.clear()
                self._handler_filters.clear()
                self._handler_metrics.clear()
                self._handler_states.clear()
                
                # Reset statistics
                self._total_handlers = 0
                self._active_handlers = 0
                self._failed_handlers = 0
                self._last_handler_load = 0.0
                
                return True
                
        except Exception:
            return False
    
    def _validate_handler(self, handler: HandlerInterface, metadata: Optional[Dict[str, Any]]) -> bool:
        """Validate a handler before registration."""
        try:
            # Check if handler implements required interface
            if not isinstance(handler, HandlerInterface):
                return False
            
            # Apply validation rules
            for rule in self._validation_rules:
                if not rule(handler, metadata):
                    return False
            
            # Basic validation
            if not hasattr(handler, 'emit'):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _detect_handler_capabilities(self, handler: HandlerInterface, 
                                   metadata: Optional[Dict[str, Any]]) -> set:
        """Detect handler capabilities."""
        capabilities = set()
        
        try:
            # Check for async capability
            if hasattr(handler, 'emit') and callable(getattr(handler, 'emit', None)):
                # Check if emit method is async
                import inspect
                if inspect.iscoroutinefunction(handler.emit):
                    capabilities.add(HandlerCapability.ASYNC)
            
            # Check for buffered capability
            if hasattr(handler, 'flush') or hasattr(handler, 'buffer_size'):
                capabilities.add(HandlerCapability.BUFFERED)
            
            # Check for compression capability
            if hasattr(handler, 'compression') or hasattr(handler, 'compress'):
                capabilities.add(HandlerCapability.COMPRESSED)
            
            # Check for encryption capability
            if hasattr(handler, 'encryption') or hasattr(handler, 'encrypt'):
                capabilities.add(HandlerCapability.ENCRYPTED)
            
            # Check for rotation capability
            if hasattr(handler, 'rotate') or hasattr(handler, 'rotation_policy'):
                capabilities.add(HandlerCapability.ROTATED)
            
            # Check for filtering capability
            if hasattr(handler, 'filter') or hasattr(handler, 'filters'):
                capabilities.add(HandlerCapability.FILTERED)
            
            # Check for formatting capability
            if hasattr(handler, 'formatter') or hasattr(handler, 'setFormatter'):
                capabilities.add(HandlerCapability.FORMATTED)
            
            # Check for monitoring capability
            if hasattr(handler, 'metrics') or hasattr(handler, 'get_metrics'):
                capabilities.add(HandlerCapability.MONITORED)
            
            # Apply capability checkers
            for checker in self._capability_checkers:
                detected_caps = checker(handler, metadata)
                if detected_caps:
                    capabilities.update(detected_caps)
            
        except Exception:
            pass
        
        return capabilities
    
    def _prepare_handler_metadata(self, handler_id: str, handler: HandlerInterface,
                                 handler_type: HandlerType, metadata: Optional[Dict[str, Any]],
                                 capabilities: set) -> Dict[str, Any]:
        """Prepare handler metadata for registration."""
        base_metadata = {
            "id": handler_id,
            "type": "handler",
            "handler_type": handler_type.value,
            "class_name": handler.__class__.__name__,
            "module_name": handler.__class__.__module__,
            "registration_time": time.time(),
            "status": ComponentStatus.REGISTERED.value,
            "capabilities": [cap.value for cap in capabilities],
            "version": metadata.get("version", "1.0.0") if metadata else "1.0.0",
            "description": metadata.get("description", "") if metadata else "",
            "tags": metadata.get("tags", []) if metadata else [],
            "author": metadata.get("author", "") if metadata else "",
            "license": metadata.get("license", "") if metadata else ""
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        return base_metadata
    
    def _store_handler_info(self, handler_id: str, handler: HandlerInterface,
                           handler_type: HandlerType, capabilities: set) -> None:
        """Store handler-specific information."""
        # Store by type
        self._handler_types[handler_type][handler_id] = handler
        
        # Store capabilities
        self._handler_capabilities[handler_id] = capabilities.copy()
        
        # Set initial state
        self._handler_states[handler_id] = "inactive"
    
    def _remove_handler_info(self, handler_id: str) -> None:
        """Remove handler-specific information."""
        # Remove from types
        for handlers in self._handler_types.values():
            if handler_id in handlers:
                del handlers[handler_id]
        
        # Remove capabilities and other info
        if handler_id in self._handler_capabilities:
            del self._handler_capabilities[handler_id]
        if handler_id in self._handler_formatters:
            del self._handler_formatters[handler_id]
        if handler_id in self._handler_filters:
            del self._handler_filters[handler_id]
        if handler_id in self._handler_metrics:
            del self._handler_metrics[handler_id]
        if handler_id in self._handler_states:
            del self._handler_states[handler_id]
    
    def _can_unregister_handler(self, handler_id: str) -> bool:
        """Check if a handler can be unregistered."""
        # For now, allow unregistration of any handler
        # In the future, this could check for active usage
        return True
    
    def _check_handler_capabilities(self, handler_id: str) -> bool:
        """Check if handler capabilities are sufficient."""
        # For now, all handlers are considered capable
        # In the future, this could check specific requirements
        return True
    
    def _trigger_lifecycle_callbacks(self, event: str, handler_id: str, 
                                   handler: HandlerInterface, metadata: Dict[str, Any]) -> None:
        """Trigger lifecycle callbacks for a handler event."""
        for callback in self._lifecycle_callbacks[event]:
            try:
                callback(event, handler_id, handler, metadata)
            except Exception:
                # Continue with other callbacks
                pass
    
    def _matches_handler_search(self, query: str, metadata: Dict[str, Any]) -> bool:
        """Check if handler metadata matches search query."""
        query_lower = query.lower()
        
        # Search in various metadata fields
        searchable_fields = [
            metadata.get("id", ""),
            metadata.get("class_name", ""),
            metadata.get("handler_type", ""),
            metadata.get("description", ""),
            " ".join(metadata.get("tags", [])),
            " ".join(metadata.get("capabilities", [])),
            metadata.get("author", "")
        ]
        
        return any(query_lower in field.lower() for field in searchable_fields if field)
    
    def get_handler_registry_stats(self) -> Dict[str, Any]:
        """Get handler registry statistics."""
        return {
            "total_handlers": self._total_handlers,
            "active_handlers": self._active_handlers,
            "failed_handlers": self._failed_handlers,
            "success_rate": (self._total_handlers / (self._total_handlers + self._failed_handlers) 
                           if (self._total_handlers + self._failed_handlers) > 0 else 0),
            "handlers_by_type": {
                htype.value: len(handlers)
                for htype, handlers in self._handler_types.items()
            },
            "total_capabilities": sum(len(caps) for caps in self._handler_capabilities.values()),
            "total_formatters": sum(len(formatters) for formatters in self._handler_formatters.values()),
            "total_filters": sum(len(filters) for filters in self._handler_filters.values()),
            "last_handler_load": self._last_handler_load,
            "enabled": self._enabled
        }
    
    def reset_handler_registry_stats(self) -> None:
        """Reset handler registry statistics."""
        with self._lock:
            self._total_handlers = 0
            self._active_handlers = 0
            self._failed_handlers = 0
            self._last_handler_load = 0.0
