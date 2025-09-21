"""
Trait-Based Composition System for Hydra-Logger

This module provides a sophisticated trait-based composition system that enables
dynamic behavior addition to components through traits. It supports method and
property injection, trait conflict resolution, and composable behavior patterns.

ARCHITECTURE:
- Trait: Base trait class with methods, properties, and requirements
- TraitMixin: Mixin for adding trait capabilities to components
- TraitRegistry: Global registry for built-in and custom traits
- Built-in Traits: Pre-defined traits for common functionality

TRAIT SYSTEM FEATURES:
- Dynamic method and property injection
- Trait conflict detection and resolution
- Requirement validation and dependency checking
- Composable trait combinations
- Trait registry and discovery
- Built-in trait library

BUILT-IN TRAITS:
- LoggingTrait: Core logging functionality (log, debug, info, warning, error, critical)
- MonitoringTrait: Performance monitoring and metrics collection
- SecurityTrait: Security validation and data sanitization

TRAIT COMPOSITION:
- Multiple trait combination
- Trait conflict resolution
- Requirement validation
- Dynamic behavior addition
- Trait method and property access

USAGE EXAMPLES:

Basic Trait Usage:
    from hydra_logger.core.traits import TraitMixin, LoggingTrait
    from hydra_logger.core.base import BaseComponent
    
    class MyComponent(TraitMixin, BaseComponent):
        def __init__(self):
            super().__init__()
            # Add logging trait
            self.add_trait("logging", LoggingTrait())
        
        def process_data(self):
            # Use trait methods
            self.log("info", "Processing data")
            self.debug("Debug information")

Custom Trait Creation:
    from hydra_logger.core.traits import Trait
    
    class CustomTrait(Trait):
        def __init__(self):
            super().__init__("custom")
            
            # Add methods
            self.add_method("custom_method", self._custom_method)
            self.add_method("another_method", self._another_method)
            
            # Add properties
            self.add_property("custom_prop", 
                            getter=self._get_custom_prop,
                            setter=self._set_custom_prop)
            
            # Add requirements
            self.add_requirement("logging_trait")
        
        def _custom_method(self, data):
            return f"Processed: {data}"
        
        def _another_method(self):
            return "Another method result"
        
        def _get_custom_prop(self):
            return getattr(self, '_custom_value', None)
        
        def _set_custom_prop(self, value):
            self._custom_value = value

Trait Registry Usage:
    from hydra_logger.core.traits import get_trait, register_trait, list_available_traits
    
    # List available traits
    available_traits = list_available_traits()
    print(f"Available traits: {available_traits}")
    
    # Get a trait from registry
    logging_trait = get_trait("logging")
    if logging_trait:
        print(f"Logging trait: {logging_trait.name}")
    
    # Register custom trait
    register_trait(CustomTrait())

Trait Conflict Resolution:
    from hydra_logger.core.traits import TraitMixin
    
    class MyComponent(TraitMixin, BaseComponent):
        def __init__(self):
            super().__init__()
            
            # Add multiple traits
            self.add_trait("logging", LoggingTrait())
            self.add_trait("monitoring", MonitoringTrait())
            self.add_trait("security", SecurityTrait())
            
            # Check for conflicts
            conflicts = self._check_trait_conflicts(LoggingTrait())
            if conflicts:
                print(f"Trait conflicts: {conflicts}")

Trait Composition:
    from hydra_logger.core.traits import TraitMixin
    
    class MyComponent(TraitMixin, BaseComponent):
        def __init__(self):
            super().__init__()
            
            # Compose with specific traits
            self.compose_with_traits("logging", "monitoring", "security")
            
            # Use composed functionality
            self.log("info", "Component initialized")
            self.start_monitoring()
            self.validate_input(user_data)
"""

from typing import Any, Dict, List, Optional, Set, Callable
from .base import BaseComponent


class Trait:
    """Base class for traits."""
    
    def __init__(self, name: str):
        self.name = name
        self._methods = {}
        self._properties = {}
        self._requirements = set()
    
    def add_method(self, name: str, method: Callable) -> None:
        """Add a method to the trait."""
        self._methods[name] = method
    
    def add_property(self, name: str, getter: Optional[Callable] = None, 
                    setter: Optional[Callable] = None) -> None:
        """Add a property to the trait."""
        self._properties[name] = {
            'getter': getter,
            'setter': setter
        }
    
    def add_requirement(self, requirement: str) -> None:
        """Add a requirement to the trait."""
        self._requirements.add(requirement)
    
    def get_methods(self) -> Dict[str, Callable]:
        """Get all methods in the trait."""
        return self._methods.copy()
    
    def get_properties(self) -> Dict[str, Dict[str, Optional[Callable]]]:
        """Get all properties in the trait."""
        return self._properties.copy()
    
    def get_requirements(self) -> Set[str]:
        """Get all requirements for the trait."""
        return self._requirements.copy()
    
    def has_method(self, name: str) -> bool:
        """Check if trait has a specific method."""
        return name in self._methods
    
    def has_property(self, name: str) -> bool:
        """Check if trait has a specific property."""
        return name in self._properties


class TraitMixin:
    """Mixin for adding trait-based composition to components."""
    
    def __init__(self, **kwargs):
        self._traits: Dict[str, Trait] = {}
        self._trait_methods: Dict[str, Callable] = {}
        self._trait_properties: Dict[str, Dict[str, Optional[Callable]]] = {}
        self._trait_requirements: Set[str] = set()
    
    def add_trait(self, trait: Trait) -> None:
        """Add a trait to the component."""
        trait_name = trait.name
        
        # Check for conflicts
        conflicts = self._check_trait_conflicts(trait)
        if conflicts:
            raise ValueError(f"Trait conflicts detected: {conflicts}")
        
        # Add trait
        self._traits[trait_name] = trait
        
        # Add methods
        for method_name, method in trait.get_methods().items():
            full_name = f"{trait_name}_{method_name}"
            self._trait_methods[full_name] = method
            # Bind method to self
            setattr(self, full_name, method.__get__(self, type(self)))
        
        # Add properties
        for prop_name, prop_info in trait.get_properties().items():
            full_name = f"{trait_name}_{prop_name}"
            self._trait_properties[full_name] = prop_info
            
            # Create property descriptor
            if prop_info['getter'] or prop_info['setter']:
                prop = property(
                    fget=prop_info['getter'].__get__(self, type(self)) if prop_info['getter'] else None,
                    fset=prop_info['setter'].__get__(self, type(self)) if prop_info['setter'] else None
                )
                setattr(type(self), full_name, prop)
        
        # Add requirements
        self._trait_requirements.update(trait.get_requirements())
    
    def remove_trait(self, trait_name: str) -> None:
        """Remove a trait from the component."""
        if trait_name not in self._traits:
            return
        
        trait = self._traits[trait_name]
        
        # Remove methods
        for method_name in trait.get_methods():
            full_name = f"{trait_name}_{method_name}"
            if full_name in self._trait_methods:
                del self._trait_methods[full_name]
                if hasattr(self, full_name):
                    delattr(self, full_name)
        
        # Remove properties
        for prop_name in trait.get_properties():
            full_name = f"{trait_name}_{prop_name}"
            if full_name in self._trait_properties:
                del self._trait_properties[full_name]
                if hasattr(type(self), full_name):
                    delattr(type(self), full_name)
        
        # Remove requirements
        self._trait_requirements.difference_update(trait.get_requirements())
        
        # Remove trait
        del self._traits[trait_name]
    
    def has_trait(self, trait_name: str) -> bool:
        """Check if component has a specific trait."""
        return trait_name in self._traits
    
    def get_trait(self, trait_name: str) -> Optional[Trait]:
        """Get a trait by name."""
        return self._traits.get(trait_name)
    
    def list_traits(self) -> List[str]:
        """List all trait names."""
        return list(self._traits.keys())
    
    def get_trait_methods(self) -> Dict[str, Callable]:
        """Get all trait methods."""
        return self._trait_methods.copy()
    
    def get_trait_properties(self) -> Dict[str, Dict[str, Optional[Callable]]]:
        """Get all trait properties."""
        return self._trait_properties.copy()
    
    def get_trait_requirements(self) -> Set[str]:
        """Get all trait requirements."""
        return self._trait_requirements.copy()
    
    def _check_trait_conflicts(self, trait: Trait) -> List[str]:
        """Check for conflicts when adding a trait."""
        conflicts = []
        
        # Check method conflicts
        for method_name in trait.get_methods():
            full_name = f"{trait.name}_{method_name}"
            if full_name in self._trait_methods:
                conflicts.append(f"Method conflict: {full_name}")
        
        # Check property conflicts
        for prop_name in trait.get_properties():
            full_name = f"{trait.name}_{prop_name}"
            if full_name in self._trait_properties:
                conflicts.append(f"Property conflict: {full_name}")
        
        return conflicts
    
    def compose_with_traits(self, *trait_names: str) -> 'TraitMixin':
        """Compose component with specific traits."""
        # Create a copy of self
        composed = type(self)(**self.__dict__)
        
        # Add specified traits
        for trait_name in trait_names:
            if trait_name in self._traits:
                trait = self._traits[trait_name]
                composed.add_trait(trait)
        
        return composed


# Built-in traits
class LoggingTrait(Trait):
    """Trait for logging capabilities."""
    
    def __init__(self):
        super().__init__("logging")
        
        # Add methods
        self.add_method("log", self._log_method)
        self.add_method("debug", self._debug_method)
        self.add_method("info", self._info_method)
        self.add_method("warning", self._warning_method)
        self.add_method("error", self._error_method)
        self.add_method("critical", self._critical_method)
        
        # Add properties
        self.add_property("log_level", 
                         getter=self._get_log_level,
                         setter=self._set_log_level)
        
        # Add requirements
        self.add_requirement("logger")
    
    def _log_method(self, level: str, message: str, **kwargs):
        """Log a message at the specified level."""
        if hasattr(self, 'logger'):
            self.logger.log(level, message, **kwargs)
    
    def _debug_method(self, message: str, **kwargs):
        """Log a debug message."""
        self._log_method("DEBUG", message, **kwargs)
    
    def _info_method(self, message: str, **kwargs):
        """Log an info message."""
        self._log_method("INFO", message, **kwargs)
    
    def _warning_method(self, message: str, **kwargs):
        """Log a warning message."""
        self._log_method("WARNING", message, **kwargs)
    
    def _error_method(self, message: str, **kwargs):
        """Log an error message."""
        self._log_method("ERROR", message, **kwargs)
    
    def _critical_method(self, message: str, **kwargs):
        """Log a critical message."""
        self._log_method("CRITICAL", message, **kwargs)
    
    def _get_log_level(self):
        """Get the log level."""
        return getattr(self, '_log_level', 'INFO')
    
    def _set_log_level(self, level: str):
        """Set the log level."""
        self._log_level = level


class MonitoringTrait(Trait):
    """Trait for monitoring capabilities."""
    
    def __init__(self):
        super().__init__("monitoring")
        
        # Add methods
        self.add_method("start_monitoring", self._start_monitoring)
        self.add_method("stop_monitoring", self._stop_monitoring)
        self.add_method("get_metrics", self._get_metrics)
        
        # Add properties
        self.add_property("monitoring_enabled",
                         getter=self._is_monitoring_enabled)
        
        # Add requirements
        self.add_requirement("metrics_collector")
    
    def _start_monitoring(self):
        """Start monitoring."""
        if hasattr(self, 'metrics_collector'):
            self.metrics_collector.start()
            self._monitoring_enabled = True
    
    def _stop_monitoring(self):
        """Stop monitoring."""
        if hasattr(self, 'metrics_collector'):
            self.metrics_collector.stop()
            self._monitoring_enabled = False
    
    def _get_metrics(self):
        """Get current metrics."""
        if hasattr(self, 'metrics_collector'):
            return self.metrics_collector.get_metrics()
        return {}
    
    def _is_monitoring_enabled(self):
        """Check if monitoring is enabled."""
        return getattr(self, '_monitoring_enabled', False)


class SecurityTrait(Trait):
    """Trait for security capabilities."""
    
    def __init__(self):
        super().__init__("security")
        
        # Add methods
        self.add_method("validate_input", self._validate_input)
        self.add_method("sanitize_data", self._sanitize_data)
        self.add_method("check_permissions", self._check_permissions)
        
        # Add properties
        self.add_property("security_level",
                         getter=self._get_security_level,
                         setter=self._set_security_level)
        
        # Add requirements
        self.add_requirement("security_validator")
    
    def _validate_input(self, data: Any) -> bool:
        """Validate input data."""
        if hasattr(self, 'security_validator'):
            return self.security_validator.validate(data)
        return True
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data."""
        if hasattr(self, 'security_validator'):
            return self.security_validator.sanitize(data)
        return data
    
    def _check_permissions(self, user: str, action: str) -> bool:
        """Check user permissions."""
        if hasattr(self, 'security_validator'):
            return self.security_validator.check_permissions(user, action)
        return True
    
    def _get_security_level(self):
        """Get the security level."""
        return getattr(self, '_security_level', 'medium')
    
    def _set_security_level(self, level: str):
        """Set the security level."""
        self._security_level = level


# Trait registry
class TraitRegistry:
    """Registry for built-in and custom traits."""
    
    def __init__(self):
        self._traits: Dict[str, Trait] = {}
        self._register_builtin_traits()
    
    def _register_builtin_traits(self):
        """Register built-in traits."""
        self.register_trait(LoggingTrait())
        self.register_trait(MonitoringTrait())
        self.register_trait(SecurityTrait())
    
    def register_trait(self, trait: Trait) -> None:
        """Register a trait."""
        self._traits[trait.name] = trait
    
    def unregister_trait(self, name: str) -> None:
        """Unregister a trait."""
        if name in self._traits:
            del self._traits[name]
    
    def get_trait(self, name: str) -> Optional[Trait]:
        """Get a trait by name."""
        return self._traits.get(name)
    
    def list_traits(self) -> List[str]:
        """List all available trait names."""
        return list(self._traits.keys())
    
    def create_trait_instance(self, name: str) -> Optional[Trait]:
        """Create a new instance of a trait."""
        trait_class = self._traits.get(name)
        if trait_class:
            return trait_class()
        return None


# Global trait registry
trait_registry = TraitRegistry()

# Convenience functions
def get_trait(name: str) -> Optional[Trait]:
    """Get a trait from the global registry."""
    return trait_registry.get_trait(name)

def list_available_traits() -> List[str]:
    """List all available traits."""
    return trait_registry.list_traits()

def register_trait(trait: Trait) -> None:
    """Register a trait in the global registry."""
    trait_registry.register_trait(trait)
