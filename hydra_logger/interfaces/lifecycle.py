"""
Lifecycle Interface for Hydra-Logger

This module defines the abstract interface for lifecycle management
including initialization, shutdown, and state transitions. It ensures
consistent behavior across all lifecycle-managed components.

ARCHITECTURE:
- LifecycleInterface: Abstract interface for all lifecycle management implementations
- Defines contract for component initialization and shutdown
- Ensures consistent behavior across different lifecycle types
- Supports state tracking and lifecycle statistics

CORE FEATURES:
- Component initialization and shutdown
- Lifecycle state tracking and management
- Lifecycle statistics and monitoring
- State transition validation
- Error handling and recovery

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import LifecycleInterface
    from typing import Any, Dict
    
    class ManagedComponent(LifecycleInterface):
        def __init__(self):
            self._initialized = False
            self._shutdown = False
            self._state = "created"
            self._stats = {"init_count": 0, "shutdown_count": 0}
        
        def initialize(self) -> bool:
            try:
                # Perform initialization logic
                self._initialized = True
                self._state = "initialized"
                self._stats["init_count"] += 1
                return True
            except Exception:
                self._state = "error"
                return False
        
        def shutdown(self) -> bool:
            try:
                # Perform shutdown logic
                self._shutdown = True
                self._state = "shutdown"
                self._stats["shutdown_count"] += 1
                return True
            except Exception:
                self._state = "error"
                return False
        
        def is_initialized(self) -> bool:
            return self._initialized
        
        def is_shutdown(self) -> bool:
            return self._shutdown
        
        def get_lifecycle_state(self) -> str:
            return self._state
        
        def get_lifecycle_stats(self) -> Dict[str, Any]:
            return self._stats.copy()
        
        def reset_lifecycle(self) -> None:
            self._initialized = False
            self._shutdown = False
            self._state = "created"
            self._stats = {"init_count": 0, "shutdown_count": 0}

Lifecycle Management:
    from hydra_logger.interfaces import LifecycleInterface
    
    def manage_lifecycle(component: LifecycleInterface):
        \"\"\"Manage component lifecycle using the interface.\"\"\"
        # Initialize component
        if component.initialize():
            print(f"Component initialized: {component.get_lifecycle_state()}")
            
            # Check if initialized
            if component.is_initialized():
                print("Component is ready for use")
            
            # Shutdown component
            if component.shutdown():
                print(f"Component shutdown: {component.get_lifecycle_state()}")
            else:
                print("Failed to shutdown component")
        else:
            print("Failed to initialize component")

Polymorphic Usage:
    from hydra_logger.interfaces import LifecycleInterface
    
    def manage_components(components: List[LifecycleInterface]):
        \"\"\"Manage multiple components with lifecycle interface.\"\"\"
        # Initialize all components
        for component in components:
            if component.initialize():
                print(f"Component initialized: {component.get_lifecycle_state()}")
            else:
                print(f"Failed to initialize component: {component.get_lifecycle_state()}")
        
        # Check initialization status
        for component in components:
            if component.is_initialized():
                stats = component.get_lifecycle_stats()
                print(f"Component ready: {stats}")
        
        # Shutdown all components
        for component in components:
            if component.shutdown():
                print(f"Component shutdown: {component.get_lifecycle_state()}")
            else:
                print(f"Failed to shutdown component: {component.get_lifecycle_state()}")

Lifecycle Monitoring:
    from hydra_logger.interfaces import LifecycleInterface
    
    def monitor_lifecycle(components: List[LifecycleInterface]):
        \"\"\"Monitor lifecycle status of all components.\"\"\"
        for component in components:
            state = component.get_lifecycle_state()
            stats = component.get_lifecycle_stats()
            
            if component.is_initialized() and not component.is_shutdown():
                print(f"Component active: {state}, stats: {stats}")
            elif component.is_shutdown():
                print(f"Component shutdown: {state}, stats: {stats}")
            else:
                print(f"Component not ready: {state}, stats: {stats}")

INTERFACE CONTRACTS:
- initialize(): Initialize the component
- shutdown(): Shutdown the component
- is_initialized(): Check if component is initialized
- is_shutdown(): Check if component is shutdown
- get_lifecycle_state(): Get current lifecycle state
- get_lifecycle_stats(): Get lifecycle statistics
- reset_lifecycle(): Reset lifecycle state

ERROR HANDLING:
- All methods return boolean success indicators
- State tracking prevents invalid transitions
- Clear error messages and status reporting
- Graceful handling of initialization/shutdown failures

BENEFITS:
- Consistent lifecycle API across implementations
- Easy testing with mock lifecycle components
- Clear contracts for custom lifecycle management
- Polymorphic usage without tight coupling
- Better lifecycle monitoring and state management
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List


class LifecycleInterface(ABC):
    """
    Abstract interface for all lifecycle management implementations.
    
    This interface defines the contract that all lifecycle components must implement,
    ensuring consistent behavior across different lifecycle types.
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the component.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def shutdown(self) -> bool:
        """
        Shutdown the component.
        
        Returns:
            True if shutdown successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if component is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_shutdown(self) -> bool:
        """
        Check if component is shutdown.
        
        Returns:
            True if shutdown, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_lifecycle_state(self) -> str:
        """
        Get current lifecycle state.
        
        Returns:
            Lifecycle state string
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_lifecycle_stats(self) -> Dict[str, Any]:
        """
        Get lifecycle statistics.
        
        Returns:
            Lifecycle statistics dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def reset_lifecycle(self) -> None:
        """Reset lifecycle state."""
        raise NotImplementedError
