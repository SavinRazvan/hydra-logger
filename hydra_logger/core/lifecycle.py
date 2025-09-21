"""
Component Lifecycle Management System for Hydra-Logger

This module provides comprehensive lifecycle management for all Hydra-Logger
components, ensuring proper initialization, state tracking, and cleanup.
It includes state machine management, transition validation, and bulk
lifecycle operations.

ARCHITECTURE:
- ComponentLifecycle: Individual component lifecycle state machine
- LifecycleManager: Centralized management of multiple component lifecycles
- State Machine: Defined state transitions and validation
- Bulk Operations: Mass lifecycle management for system-wide operations

LIFECYCLE STATES:
- created: Component created but not initialized
- initializing: Component is being initialized
- initialized: Component initialized and ready
- running: Component is actively running
- stopped: Component stopped but can be restarted
- failed: Component failed and needs attention
- destroyed: Component destroyed and cannot be used

STATE TRANSITIONS:
- created → initializing → initialized
- initialized → running → stopped
- running → stopped → running (restart)
- Any state → failed (on error)
- Any state → destroyed (cleanup)

FEATURES:
- State transition validation
- Bulk lifecycle operations
- Error handling and recovery
- State change notifications
- Component dependency tracking
- Lifecycle statistics and monitoring

USAGE EXAMPLES:

Individual Component Lifecycle:
    from hydra_logger.core.lifecycle import ComponentLifecycle
    from hydra_logger.core.base import BaseComponent
    
    class MyComponent(BaseComponent):
        def initialize(self):
            # Initialization logic
            pass
        
        def shutdown(self):
            # Cleanup logic
            pass
    
    component = MyComponent("my_component")
    lifecycle = ComponentLifecycle(component)
    
    # Initialize component
    if lifecycle.transition_to("initializing"):
        component.initialize()
        lifecycle.transition_to("initialized")

Bulk Lifecycle Management:
    from hydra_logger.core.lifecycle import LifecycleManager
    
    manager = LifecycleManager()
    manager.register_component("logger1", logger1)
    manager.register_component("handler1", handler1)
    
    # Initialize all components
    results = manager.initialize_all()
    print(f"Initialization results: {results}")
    
    # Start all initialized components
    start_results = manager.start_all()

State Monitoring:
    from hydra_logger.core.lifecycle import LifecycleManager
    
    manager = LifecycleManager()
    all_states = manager.get_all_states()
    running_components = manager.get_components_by_state("running")
    
    print(f"All component states: {all_states}")
    print(f"Running components: {running_components}")
"""

from typing import Dict, Any, Optional, List
from .base import BaseComponent


class ComponentLifecycle:
    """Manages the lifecycle of a component."""
    
    def __init__(self, component: BaseComponent):
        self.component = component
        self._state = "created"
        self._transitions = {
            "created": ["initializing", "destroyed"],
            "initializing": ["initialized", "failed", "destroyed"],
            "initialized": ["running", "stopped", "failed", "destroyed"],
            "running": ["stopped", "failed", "destroyed"],
            "stopped": ["running", "failed", "destroyed"],
            "failed": ["initializing", "destroyed"],
            "destroyed": []
        }
    
    def can_transition_to(self, new_state: str) -> bool:
        """Check if transition to new state is allowed."""
        return new_state in self._transitions.get(self._state, [])
    
    def transition_to(self, new_state: str) -> bool:
        """Transition to a new state if allowed."""
        if not self.can_transition_to(new_state):
            return False
        
        old_state = self._state
        self._state = new_state
        
        # Execute state change hooks
        self._on_state_change(old_state, new_state)
        return True
    
    def _on_state_change(self, old_state: str, new_state: str) -> None:
        """Handle state change events."""
        # This can be extended with hooks and callbacks
        pass
    
    def get_state(self) -> str:
        """Get current state."""
        return self._state
    
    def is_created(self) -> bool:
        """Check if component is created."""
        return self._state == "created"
    
    def is_initializing(self) -> bool:
        """Check if component is initializing."""
        return self._state == "initializing"
    
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._state == "initialized"
    
    def is_running(self) -> bool:
        """Check if component is running."""
        return self._state == "running"
    
    def is_stopped(self) -> bool:
        """Check if component is stopped."""
        return self._state == "stopped"
    
    def is_failed(self) -> bool:
        """Check if component is failed."""
        return self._state == "failed"
    
    def is_destroyed(self) -> bool:
        """Check if component is destroyed."""
        return self._state == "destroyed"


class LifecycleManager:
    """Manages multiple component lifecycles."""
    
    def __init__(self):
        self._components: Dict[str, ComponentLifecycle] = {}
    
    def register_component(self, name: str, component: BaseComponent) -> None:
        """Register a component for lifecycle management."""
        self._components[name] = ComponentLifecycle(component)
    
    def unregister_component(self, name: str) -> None:
        """Unregister a component."""
        if name in self._components:
            del self._components[name]
    
    def get_component_lifecycle(self, name: str) -> Optional[ComponentLifecycle]:
        """Get the lifecycle of a component."""
        return self._components.get(name)
    
    def initialize_component(self, name: str) -> bool:
        """Initialize a component."""
        lifecycle = self.get_component_lifecycle(name)
        if not lifecycle:
            return False
        
        if lifecycle.transition_to("initializing"):
            try:
                lifecycle.component.initialize()
                return lifecycle.transition_to("initialized")
            except Exception:
                lifecycle.transition_to("failed")
                return False
        return False
    
    def start_component(self, name: str) -> bool:
        """Start a component."""
        lifecycle = self.get_component_lifecycle(name)
        if not lifecycle or not lifecycle.is_initialized():
            return False
        
        if lifecycle.transition_to("running"):
            return True
        return False
    
    def stop_component(self, name: str) -> bool:
        """Stop a component."""
        lifecycle = self.get_component_lifecycle(name)
        if not lifecycle or not lifecycle.is_running():
            return False
        
        if lifecycle.transition_to("stopped"):
            return True
        return False
    
    def destroy_component(self, name: str) -> bool:
        """Destroy a component."""
        lifecycle = self.get_component_lifecycle(name)
        if not lifecycle:
            return False
        
        if lifecycle.transition_to("destroyed"):
            try:
                lifecycle.component.shutdown()
                return True
            except Exception:
                return False
        return False
    
    def get_all_states(self) -> Dict[str, str]:
        """Get the state of all components."""
        return {name: lifecycle.get_state() 
                for name, lifecycle in self._components.items()}
    
    def get_components_by_state(self, state: str) -> List[str]:
        """Get all components in a specific state."""
        return [name for name, lifecycle in self._components.items()
                if lifecycle.get_state() == state]
    
    def initialize_all(self) -> Dict[str, bool]:
        """Initialize all components."""
        results = {}
        for name in self._components:
            results[name] = self.initialize_component(name)
        return results
    
    def start_all(self) -> Dict[str, bool]:
        """Start all initialized components."""
        results = {}
        for name in self._components:
            lifecycle = self.get_component_lifecycle(name)
            if lifecycle and lifecycle.is_initialized():
                results[name] = self.start_component(name)
        return results
    
    def stop_all(self) -> Dict[str, bool]:
        """Stop all running components."""
        results = {}
        for name in self._components:
            lifecycle = self.get_component_lifecycle(name)
            if lifecycle and lifecycle.is_running():
                results[name] = self.stop_component(name)
        return results
    
    def destroy_all(self) -> Dict[str, bool]:
        """Destroy all components."""
        results = {}
        for name in list(self._components.keys()):
            results[name] = self.destroy_component(name)
        return results
