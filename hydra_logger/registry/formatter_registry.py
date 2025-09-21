"""
Formatter-Specific Registry for Hydra-Logger

This module provides a specialized registry system for managing log formatters
with advanced capabilities including formatter types, capabilities detection,
template management, and performance tracking. It extends the generic component
registry with formatter-specific functionality.

FEATURES:
- Formatter registration and lifecycle management
- Formatter type classification and organization
- Capability detection and management
- Template management and storage
- Performance metrics tracking
- Formatter search and filtering
- Export/import functionality

FORMATTER TYPES:
- Text: Plain text formatters
- JSON: JSON format formatters
- CSV: CSV format formatters
- XML: XML format formatters
- YAML: YAML format formatters
- Binary: Binary format formatters
- Template: Template-based formatters
- Colored: Colored output formatters
- Structured: Structured data formatters
- Streaming: Streaming formatters
- Custom: Custom formatters

FORMATTER CAPABILITIES:
- Colored Output: Color support
- Template Based: Template functionality
- Structured Output: Structured data support
- Streaming: Streaming capabilities
- Binary: Binary data support
- Compressed: Compression support
- Encrypted: Encryption support
- Filtered: Filtering capabilities
- Cached: Caching support
- Async: Asynchronous processing

USAGE:
    from hydra_logger.registry import FormatterRegistry, FormatterType, FormatterCapability
    
    # Create formatter registry
    registry = FormatterRegistry(enabled=True)
    
    # Register a formatter
    success = registry.register_formatter(
        "my_formatter",
        my_formatter_instance,
        FormatterType.JSON,
        metadata={"version": "1.0.0", "author": "Developer"}
    )
    
    # Get formatter by type
    formatters = registry.get_formatters_by_type(FormatterType.JSON)
    
    # Get formatters by capability
    colored_formatters = registry.get_formatters_by_capability(FormatterCapability.COLORED_OUTPUT)
    
    # Set formatter template
    registry.set_formatter_template("my_formatter", "{timestamp} {level} {message}")
    
    # Search formatters
    results = registry.search_formatters("json")
"""

import time
import threading
import json
from typing import Any, Dict, List, Optional, Callable, Type
from collections import defaultdict, deque
from enum import Enum
from ..interfaces.registry import RegistryInterface
from ..interfaces.formatter import FormatterInterface
from .component_registry import ComponentRegistry, ComponentType, ComponentStatus


class FormatterType(Enum):
    """Types of formatters."""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"
    BINARY = "binary"
    TEMPLATE = "template"
    COLORED = "colored"
    STRUCTURED = "structured"
    STREAMING = "streaming"
    CUSTOM = "custom"


class FormatterCapability(Enum):
    """Formatter capabilities."""
    COLORED_OUTPUT = "colored_output"
    TEMPLATE_BASED = "template_based"
    STRUCTURED_OUTPUT = "structured_output"
    STREAMING = "streaming"
    BINARY = "binary"
    COMPRESSED = "compressed"
    ENCRYPTED = "encrypted"
    FILTERED = "filtered"
    CACHED = "cached"
    ASYNC = "async"


class FormatterRegistry(RegistryInterface):
    """Real formatter-specific registry with advanced formatter management capabilities."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        
        # Core component registry
        self._component_registry = ComponentRegistry(enabled=enabled)
        
        # Formatter-specific storage
        self._formatter_types = defaultdict(dict)        # type -> {id -> formatter}
        self._formatter_capabilities = defaultdict(set)  # formatter_id -> {capabilities}
        self._formatter_templates = defaultdict(dict)    # formatter_id -> template_info
        self._formatter_options = defaultdict(dict)      # formatter_id -> options
        self._formatter_metrics = defaultdict(dict)      # formatter_id -> metrics
        
        # Formatter discovery and loading
        self._discovery_paths = []
        self._auto_discovery = True
        self._discovery_callbacks = []
        
        # Formatter validation and compatibility
        self._validation_rules = []
        self._capability_checkers = []
        self._performance_requirements = {}
        
        # Formatter lifecycle management
        self._lifecycle_callbacks = defaultdict(list)  # event -> [callbacks]
        self._formatter_states = {}  # formatter_id -> state
        
        # Threading
        self._lock = threading.RLock()
        
        # Statistics
        self._total_formatters = 0
        self._active_formatters = 0
        self._failed_formatters = 0
        self._last_formatter_load = 0.0
    
    def register_formatter(self, formatter_id: str, formatter: FormatterInterface, 
                          formatter_type: FormatterType, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a formatter in the registry.
        
        Args:
            formatter_id: Unique identifier for the formatter
            formatter: The formatter instance
            formatter_type: Type of formatter
            metadata: Additional formatter metadata
            
        Returns:
            True if registration successful
        """
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Validate formatter
                if not self._validate_formatter(formatter, metadata):
                    self._failed_formatters += 1
                    return False
                
                # Check capabilities
                capabilities = self._detect_formatter_capabilities(formatter, metadata)
                
                # Prepare metadata
                formatter_metadata = self._prepare_formatter_metadata(formatter_id, formatter, formatter_type, metadata, capabilities)
                
                # Register in component registry
                success = self._component_registry.register_component(
                    ComponentType.FORMATTER, formatter_id, formatter, formatter_metadata
                )
                
                if success:
                    # Store formatter-specific information
                    self._store_formatter_info(formatter_id, formatter, formatter_type, capabilities)
                    
                    # Update statistics
                    self._total_formatters += 1
                    self._last_formatter_load = time.time()
                    
                    # Trigger lifecycle callbacks
                    self._trigger_lifecycle_callbacks("registered", formatter_id, formatter, formatter_metadata)
                    
                    return True
                else:
                    self._failed_formatters += 1
                    return False
                    
        except Exception as e:
            self._failed_formatters += 1
            return False
    
    def unregister_formatter(self, formatter_id: str) -> bool:
        """
        Unregister a formatter from the registry.
        
        Args:
            formatter_id: Formatter identifier
            
        Returns:
            True if unregistration successful
        """
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Get formatter before removal
                formatter = self._component_registry.get_component(ComponentType.FORMATTER, formatter_id)
                metadata = self._component_registry.get_component_metadata(ComponentType.FORMATTER, formatter_id)
                
                if not formatter:
                    return False
                
                # Check if formatter can be unregistered
                if not self._can_unregister_formatter(formatter_id):
                    return False
                
                # Unregister from component registry
                success = self._component_registry.unregister_component(ComponentType.FORMATTER, formatter_id)
                
                if success:
                    # Remove formatter-specific information
                    self._remove_formatter_info(formatter_id)
                    
                    # Update statistics
                    if formatter_id in self._formatter_states and self._formatter_states[formatter_id] == "active":
                        self._active_formatters -= 1
                    
                    # Trigger lifecycle callbacks
                    self._trigger_lifecycle_callbacks("unregistered", formatter_id, formatter, metadata)
                    
                    return True
                else:
                    return False
                    
        except Exception:
            return False
    
    def get_formatter(self, formatter_id: str) -> Optional[FormatterInterface]:
        """Get a formatter by ID."""
        if not self._enabled:
            return None
        
        return self._component_registry.get_component(ComponentType.FORMATTER, formatter_id)
    
    def get_formatters_by_type(self, formatter_type: FormatterType) -> Dict[str, FormatterInterface]:
        """Get all formatters of a specific type."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                return self._formatter_types[formatter_type].copy()
        except Exception:
            return {}
    
    def get_formatters_by_capability(self, capability: FormatterCapability) -> List[FormatterInterface]:
        """Get formatters with a specific capability."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                formatters = []
                for formatter_id, capabilities in self._formatter_capabilities.items():
                    if capability in capabilities:
                        formatter = self.get_formatter(formatter_id)
                        if formatter:
                            formatters.append(formatter)
                return formatters
        except Exception:
            return []
    
    def get_formatter_metadata(self, formatter_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific formatter."""
        if not self._enabled:
            return None
        
        return self._component_registry.get_component_metadata(ComponentType.FORMATTER, formatter_id)
    
    def get_all_formatters(self) -> Dict[str, FormatterInterface]:
        """Get all registered formatters."""
        if not self._enabled:
            return {}
        
        return self._component_registry.get_components_by_type(ComponentType.FORMATTER)
    
    def get_formatter_count(self, formatter_type: Optional[FormatterType] = None) -> int:
        """Get count of formatters, optionally filtered by type."""
        if not self._enabled:
            return 0
        
        try:
            with self._lock:
                if formatter_type:
                    return len(self._formatter_types[formatter_type])
                else:
                    return self._component_registry.get_component_count(ComponentType.FORMATTER)
        except Exception:
            return 0
    
    def has_formatter(self, formatter_id: str) -> bool:
        """Check if a formatter exists."""
        if not self._enabled:
            return False
        
        return self._component_registry.has_component(ComponentType.FORMATTER, formatter_id)
    
    def list_formatter_types(self) -> List[FormatterType]:
        """List all formatter types."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._formatter_types.keys())
        except Exception:
            return []
    
    def list_formatters(self, formatter_type: Optional[FormatterType] = None) -> List[str]:
        """List all formatter IDs, optionally filtered by type."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                if formatter_type:
                    return list(self._formatter_types[formatter_type].keys())
                else:
                    return self._component_registry.list_components(ComponentType.FORMATTER)
        except Exception:
            return []
    
    def activate_formatter(self, formatter_id: str) -> bool:
        """Activate a formatter."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if not self.has_formatter(formatter_id):
                    return False
                
                # Check formatter capabilities
                if not self._check_formatter_capabilities(formatter_id):
                    return False
                
                # Update formatter state
                self._formatter_states[formatter_id] = "active"
                self._active_formatters += 1
                
                # Update component status
                self._component_registry.set_component_status(
                    ComponentType.FORMATTER, formatter_id, ComponentStatus.ACTIVE
                )
                
                # Trigger lifecycle callbacks
                formatter = self.get_formatter(formatter_id)
                metadata = self.get_formatter_metadata(formatter_id)
                self._trigger_lifecycle_callbacks("activated", formatter_id, formatter, metadata)
                
                return True
                
        except Exception:
            return False
    
    def deactivate_formatter(self, formatter_id: str) -> bool:
        """Deactivate a formatter."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if not self.has_formatter(formatter_id):
                    return False
                
                # Update formatter state
                if formatter_id in self._formatter_states and self._formatter_states[formatter_id] == "active":
                    self._formatter_states[formatter_id] = "inactive"
                    self._active_formatters -= 1
                
                # Update component status
                self._component_registry.set_component_status(
                    ComponentType.FORMATTER, formatter_id, ComponentStatus.INACTIVE
                )
                
                # Trigger lifecycle callbacks
                formatter = self.get_formatter(formatter_id)
                metadata = self.get_formatter_metadata(formatter_id)
                self._trigger_lifecycle_callbacks("deactivated", formatter_id, formatter, metadata)
                
                return True
                
        except Exception:
            return False
    
    def get_formatter_state(self, formatter_id: str) -> str:
        """Get formatter state."""
        if not self._enabled:
            return "unknown"
        
        return self._formatter_states.get(formatter_id, "unknown")
    
    def get_active_formatters(self) -> List[str]:
        """Get list of active formatter IDs."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return [fid for fid, state in self._formatter_states.items() if state == "active"]
        except Exception:
            return []
    
    def get_inactive_formatters(self) -> List[str]:
        """Get list of inactive formatter IDs."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return [fid for fid, state in self._formatter_states.items() if state == "inactive"]
        except Exception:
            return []
    
    def get_formatter_capabilities(self, formatter_id: str) -> List[FormatterCapability]:
        """Get capabilities for a formatter."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                return list(self._formatter_capabilities.get(formatter_id, set()))
        except Exception:
            return []
    
    def has_formatter_capability(self, formatter_id: str, capability: FormatterCapability) -> bool:
        """Check if a formatter has a specific capability."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                return capability in self._formatter_capabilities.get(formatter_id, set())
        except Exception:
            return False
    
    def set_formatter_template(self, formatter_id: str, template: str, template_type: str = "default") -> bool:
        """Set a template for a formatter."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if formatter_id not in self._formatter_templates:
                    self._formatter_templates[formatter_id] = {}
                
                self._formatter_templates[formatter_id][template_type] = {
                    "template": template,
                    "set_time": time.time()
                }
                return True
                
        except Exception:
            return False
    
    def get_formatter_template(self, formatter_id: str, template_type: str = "default") -> Optional[str]:
        """Get a template for a formatter."""
        if not self._enabled:
            return None
        
        try:
            with self._lock:
                if formatter_id in self._formatter_templates and template_type in self._formatter_templates[formatter_id]:
                    return self._formatter_templates[formatter_id][template_type]["template"]
                return None
        except Exception:
            return None
    
    def remove_formatter_template(self, formatter_id: str, template_type: str) -> bool:
        """Remove a template from a formatter."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if formatter_id in self._formatter_templates and template_type in self._formatter_templates[formatter_id]:
                    del self._formatter_templates[formatter_id][template_type]
                    return True
                return False
                
        except Exception:
            return False
    
    def set_formatter_options(self, formatter_id: str, options: Dict[str, Any]) -> bool:
        """Set options for a formatter."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._formatter_options[formatter_id] = options.copy()
                return True
        except Exception:
            return False
    
    def get_formatter_options(self, formatter_id: str) -> Dict[str, Any]:
        """Get options for a formatter."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                return self._formatter_options.get(formatter_id, {}).copy()
        except Exception:
            return {}
    
    def update_formatter_metrics(self, formatter_id: str, metrics: Dict[str, Any]) -> bool:
        """Update formatter metrics."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._formatter_metrics[formatter_id] = metrics.copy()
                return True
        except Exception:
            return False
    
    def get_formatter_metrics(self, formatter_id: str) -> Dict[str, Any]:
        """Get formatter metrics."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                return self._formatter_metrics.get(formatter_id, {}).copy()
        except Exception:
            return {}
    
    def search_formatters(self, query: str, formatter_type: Optional[FormatterType] = None) -> List[Dict[str, Any]]:
        """Search for formatters by query string."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                results = []
                search_types = [formatter_type] if formatter_type else self._formatter_types.keys()
                
                for ftype in search_types:
                    for formatter_id, formatter in self._formatter_types[ftype].items():
                        metadata = self.get_formatter_metadata(formatter_id)
                        if metadata and self._matches_formatter_search(query, metadata):
                            results.append({
                                "id": formatter_id,
                                "type": ftype.value,
                                "formatter": formatter,
                                "metadata": metadata.copy(),
                                "state": self._formatter_states.get(formatter_id, "unknown"),
                                "capabilities": list(self._formatter_capabilities.get(formatter_id, set()))
                            })
                
                return results
                
        except Exception:
            return []
    
    def add_validation_rule(self, rule: Callable) -> bool:
        """Add a formatter validation rule."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._validation_rules.append(rule)
                return True
        except Exception:
            return False
    
    def remove_validation_rule(self, rule: Callable) -> bool:
        """Remove a formatter validation rule."""
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
        """Add a formatter capability checker."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._capability_checkers.append(checker)
                return True
        except Exception:
            return False
    
    def remove_capability_checker(self, checker: Callable) -> bool:
        """Remove a formatter capability checker."""
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
        """Register a callback for formatter lifecycle events."""
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
    
    def export_formatter_registry(self, format: str = "json") -> str:
        """Export formatter registry data."""
        if not self._enabled:
            return ""
        
        try:
            with self._lock:
                export_data = {
                    "export_time": time.time(),
                    "total_formatters": self._total_formatters,
                    "active_formatters": self._active_formatters,
                    "formatters_by_type": {
                        ftype.value: {
                            fid: {
                                "state": self._formatter_states.get(fid, "unknown"),
                                "capabilities": list(self._formatter_capabilities.get(fid, set())),
                                "templates": self._formatter_templates.get(fid, {}),
                                "options": self._formatter_options.get(fid, {}),
                                "metadata": self.get_formatter_metadata(fid)
                            }
                            for fid in formatters.keys()
                        }
                        for ftype, formatters in self._formatter_types.items()
                    },
                    "formatter_states": dict(self._formatter_states),
                    "formatter_capabilities": {
                        fid: list(caps) for fid, caps in self._formatter_capabilities.items()
                    },
                    "statistics": self.get_formatter_registry_stats()
                }
                
                if format.lower() == "json":
                    return json.dumps(export_data, indent=2, default=str)
                else:
                    return str(export_data)
                    
        except Exception:
            return ""
    
    def clear_formatter_registry(self) -> bool:
        """Clear all formatters from the registry."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                # Clear component registry
                self._component_registry.clear_registry(ComponentType.FORMATTER)
                
                # Clear formatter-specific storage
                self._formatter_types.clear()
                self._formatter_capabilities.clear()
                self._formatter_templates.clear()
                self._formatter_options.clear()
                self._formatter_metrics.clear()
                self._formatter_states.clear()
                
                # Reset statistics
                self._total_formatters = 0
                self._active_formatters = 0
                self._failed_formatters = 0
                self._last_formatter_load = 0.0
                
                return True
                
        except Exception:
            return False
    
    def _validate_formatter(self, formatter: FormatterInterface, metadata: Optional[Dict[str, Any]]) -> bool:
        """Validate a formatter before registration."""
        try:
            # Check if formatter implements required interface
            if not isinstance(formatter, FormatterInterface):
                return False
            
            # Apply validation rules
            for rule in self._validation_rules:
                if not rule(formatter, metadata):
                    return False
            
            # Basic validation
            if not hasattr(formatter, 'format'):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _detect_formatter_capabilities(self, formatter: FormatterInterface, 
                                     metadata: Optional[Dict[str, Any]]) -> set:
        """Detect formatter capabilities."""
        capabilities = set()
        
        try:
            # Check for colored output capability
            if hasattr(formatter, 'colors') or hasattr(formatter, 'color_scheme'):
                capabilities.add(FormatterCapability.COLORED_OUTPUT)
            
            # Check for template-based capability
            if hasattr(formatter, 'template') or hasattr(formatter, 'set_template'):
                capabilities.add(FormatterCapability.TEMPLATE_BASED)
            
            # Check for structured output capability
            if hasattr(formatter, 'structure') or hasattr(formatter, 'structured'):
                capabilities.add(FormatterCapability.STRUCTURED_OUTPUT)
            
            # Check for streaming capability
            if hasattr(formatter, 'stream') or hasattr(formatter, 'streaming'):
                capabilities.add(FormatterCapability.STREAMING)
            
            # Check for binary capability
            if hasattr(formatter, 'binary') or hasattr(formatter, 'binary_output'):
                capabilities.add(FormatterCapability.BINARY)
            
            # Check for compression capability
            if hasattr(formatter, 'compress') or hasattr(formatter, 'compression'):
                capabilities.add(FormatterCapability.COMPRESSED)
            
            # Check for encryption capability
            if hasattr(formatter, 'encrypt') or hasattr(formatter, 'encryption'):
                capabilities.add(FormatterCapability.ENCRYPTED)
            
            # Check for filtering capability
            if hasattr(formatter, 'filter') or hasattr(formatter, 'filters'):
                capabilities.add(FormatterCapability.FILTERED)
            
            # Check for caching capability
            if hasattr(formatter, 'cache') or hasattr(formatter, 'caching'):
                capabilities.add(FormatterCapability.CACHED)
            
            # Check for async capability
            if hasattr(formatter, 'format') and callable(getattr(formatter, 'format', None)):
                import inspect
                if inspect.iscoroutinefunction(formatter.format):
                    capabilities.add(FormatterCapability.ASYNC)
            
            # Apply capability checkers
            for checker in self._capability_checkers:
                detected_caps = checker(formatter, metadata)
                if detected_caps:
                    capabilities.update(detected_caps)
            
        except Exception:
            pass
        
        return capabilities
    
    def _prepare_formatter_metadata(self, formatter_id: str, formatter: FormatterInterface,
                                   formatter_type: FormatterType, metadata: Optional[Dict[str, Any]],
                                   capabilities: set) -> Dict[str, Any]:
        """Prepare formatter metadata for registration."""
        base_metadata = {
            "id": formatter_id,
            "type": "formatter",
            "formatter_type": formatter_type.value,
            "class_name": formatter.__class__.__name__,
            "module_name": formatter.__class__.__module__,
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
    
    def _store_formatter_info(self, formatter_id: str, formatter: FormatterInterface,
                             formatter_type: FormatterType, capabilities: set) -> None:
        """Store formatter-specific information."""
        # Store by type
        self._formatter_types[formatter_type][formatter_id] = formatter
        
        # Store capabilities
        self._formatter_capabilities[formatter_id] = capabilities.copy()
        
        # Set initial state
        self._formatter_states[formatter_id] = "inactive"
    
    def _remove_formatter_info(self, formatter_id: str) -> None:
        """Remove formatter-specific information."""
        # Remove from types
        for formatters in self._formatter_types.values():
            if formatter_id in formatters:
                del formatters[formatter_id]
        
        # Remove capabilities and other info
        if formatter_id in self._formatter_capabilities:
            del self._formatter_capabilities[formatter_id]
        if formatter_id in self._formatter_templates:
            del self._formatter_templates[formatter_id]
        if formatter_id in self._formatter_options:
            del self._formatter_options[formatter_id]
        if formatter_id in self._formatter_metrics:
            del self._formatter_metrics[formatter_id]
        if formatter_id in self._formatter_states:
            del self._formatter_states[formatter_id]
    
    def _can_unregister_formatter(self, formatter_id: str) -> bool:
        """Check if a formatter can be unregistered."""
        # For now, allow unregistration of any formatter
        # In the future, this could check for active usage
        return True
    
    def _check_formatter_capabilities(self, formatter_id: str) -> bool:
        """Check if formatter capabilities are sufficient."""
        # For now, all formatters are considered capable
        # In the future, this could check specific requirements
        return True
    
    def _trigger_lifecycle_callbacks(self, event: str, formatter_id: str, 
                                   formatter: FormatterInterface, metadata: Dict[str, Any]) -> None:
        """Trigger lifecycle callbacks for a formatter event."""
        for callback in self._lifecycle_callbacks[event]:
            try:
                callback(event, formatter_id, formatter, metadata)
            except Exception:
                # Continue with other callbacks
                pass
    
    def _matches_formatter_search(self, query: str, metadata: Dict[str, Any]) -> bool:
        """Check if formatter metadata matches search query."""
        query_lower = query.lower()
        
        # Search in various metadata fields
        searchable_fields = [
            metadata.get("id", ""),
            metadata.get("class_name", ""),
            metadata.get("formatter_type", ""),
            metadata.get("description", ""),
            " ".join(metadata.get("tags", [])),
            " ".join(metadata.get("capabilities", [])),
            metadata.get("author", "")
        ]
        
        return any(query_lower in field.lower() for field in searchable_fields if field)
    
    def get_formatter_registry_stats(self) -> Dict[str, Any]:
        """Get formatter registry statistics."""
        return {
            "total_formatters": self._total_formatters,
            "active_formatters": self._active_formatters,
            "failed_formatters": self._failed_formatters,
            "success_rate": (self._total_formatters / (self._total_formatters + self._failed_formatters) 
                           if (self._total_formatters + self._failed_formatters) > 0 else 0),
            "formatters_by_type": {
                ftype.value: len(formatters)
                for ftype, formatters in self._formatter_types.items()
            },
            "total_capabilities": sum(len(caps) for caps in self._formatter_capabilities.values()),
            "total_templates": sum(len(templates) for templates in self._formatter_templates.values()),
            "total_options": len(self._formatter_options),
            "last_formatter_load": self._last_formatter_load,
            "enabled": self._enabled
        }
    
    def reset_formatter_registry_stats(self) -> None:
        """Reset formatter registry statistics."""
        with self._lock:
            self._total_formatters = 0
            self._active_formatters = 0
            self._failed_formatters = 0
            self._last_formatter_load = 0.0
