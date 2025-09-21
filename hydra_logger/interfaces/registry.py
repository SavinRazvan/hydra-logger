"""
Registry Interface for Hydra-Logger

This module defines the abstract interface for registry components
including component registration, discovery, and lifecycle management.
It ensures consistent behavior across all registry implementations.

ARCHITECTURE:
- RegistryInterface: Abstract interface for all registry implementations
- Defines contract for component registration and discovery
- Ensures consistent behavior across different registry types
- Supports component lifecycle management

CORE FEATURES:
- Component registration and unregistration
- Component discovery and lookup
- Component lifecycle management
- Registry cleanup and maintenance
- Component metadata management

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import RegistryInterface
    from typing import Any, Dict, Optional, Type
    
    class ComponentRegistry(RegistryInterface):
        def __init__(self):
            self._components = {}
        
        def register_component(self, name: str, component: Any) -> bool:
            try:
                self._components[name] = component
                return True
            except Exception:
                return False
        
        def unregister_component(self, name: str) -> bool:
            try:
                if name in self._components:
                    del self._components[name]
                    return True
                return False
            except Exception:
                return False
        
        def get_component(self, name: str) -> Optional[Any]:
            return self._components.get(name)
        
        def list_components(self) -> List[str]:
            return list(self._components.keys())
        
        def is_component_registered(self, name: str) -> bool:
            return name in self._components
        
        def get_component_count(self) -> int:
            return len(self._components)
        
        def clear_components(self) -> None:
            self._components.clear()

Registry Usage:
    from hydra_logger.interfaces import RegistryInterface
    
    def use_registry(registry: RegistryInterface):
        \"\"\"Use any registry that implements RegistryInterface.\"\"\"
        # Register components
        if registry.register_component("formatter1", MyFormatter()):
            print("Component registered")
        
        if registry.register_component("handler1", MyHandler()):
            print("Handler registered")
        
        # Check if registered
        if registry.is_component_registered("formatter1"):
            print("Formatter is registered")
        
        # Get component
        formatter = registry.get_component("formatter1")
        if formatter:
            print(f"Retrieved formatter: {formatter}")
        
        # List components
        components = registry.list_components()
        print(f"Registered components: {components}")
        
        # Get component count
        count = registry.get_component_count()
        print(f"Total components: {count}")
        
        # Unregister component
        if registry.unregister_component("formatter1"):
            print("Component unregistered")
        
        # Clear registry
        registry.clear_components()
        print("Registry cleared")

Component Management:
    from hydra_logger.interfaces import RegistryInterface
    
    def manage_components(registry: RegistryInterface):
        \"\"\"Manage components using the registry interface.\"\"\"
        # Register multiple components
        components = [
            ("formatter1", MyFormatter()),
            ("handler1", MyHandler()),
            ("logger1", MyLogger())
        ]
        
        for name, component in components:
            if registry.register_component(name, component):
                print(f"Registered: {name}")
            else:
                print(f"Failed to register: {name}")
        
        # Check registration status
        for name, _ in components:
            if registry.is_component_registered(name):
                print(f"{name} is registered")
            else:
                print(f"{name} is not registered")
        
        # Get all components
        all_components = registry.list_components()
        print(f"All components: {all_components}")
        
        # Get component count
        count = registry.get_component_count()
        print(f"Total components: {count}")

INTERFACE CONTRACTS:
- register_component(name, component): Register component
- unregister_component(name): Unregister component
- get_component(name): Get component by name
- list_components(): List all component names
- is_component_registered(name): Check if component is registered
- get_component_count(): Get total component count
- clear_components(): Clear all components

ERROR HANDLING:
- All methods return boolean success indicators
- Clear error messages and status reporting
- Graceful handling of registration failures
- Safe component management

BENEFITS:
- Consistent registry API across implementations
- Easy testing with mock registries
- Clear contracts for custom registries
- Polymorphic usage without tight coupling
- Better component discovery and management
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List


class RegistryInterface(ABC):
    """
    Abstract interface for all registry implementations.
    
    This interface defines the contract that all registry components must implement,
    ensuring consistent behavior across different registry types.
    """
    
    @abstractmethod
    def register_component(self, name: str, component: Any) -> bool:
        """
        Register a component.
        
        Args:
            name: Component name
            component: Component instance
            
        Returns:
            True if registered successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def unregister_component(self, name: str) -> bool:
        """
        Unregister a component.
        
        Args:
            name: Component name
            
        Returns:
            True if unregistered successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a component by name.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        raise NotImplementedError
    
    @abstractmethod
    def list_components(self) -> List[str]:
        """
        List all registered components.
        
        Returns:
            List of component names
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_component_registered(self, name: str) -> bool:
        """
        Check if component is registered.
        
        Args:
            name: Component name
            
        Returns:
            True if registered, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_component_count(self) -> int:
        """
        Get total number of registered components.
        
        Returns:
            Component count
        """
        raise NotImplementedError
    
    @abstractmethod
    def clear_components(self) -> None:
        """Clear all registered components."""
        raise NotImplementedError
