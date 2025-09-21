"""
Tests for core/lifecycle.py module.

This module tests the component lifecycle management functionality.
"""

import pytest
from unittest.mock import Mock, patch
from hydra_logger.core.lifecycle import ComponentLifecycle, LifecycleManager
from hydra_logger.core.base import BaseComponent


class ConcreteComponent(BaseComponent):
    """Concrete implementation for testing."""
    
    def initialize(self) -> None:
        """Initialize the component."""
        self._initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the component."""
        self._initialized = False


class TestComponentLifecycle:
    """Test ComponentLifecycle class."""
    
    def test_component_lifecycle_init(self):
        """Test ComponentLifecycle initialization."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        assert lifecycle.component is component
        assert lifecycle.get_state() == "created"
    
    def test_can_transition_to_valid_states(self):
        """Test can_transition_to with valid states."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        # From created state
        assert lifecycle.can_transition_to("initializing") is True
        assert lifecycle.can_transition_to("destroyed") is True
        assert lifecycle.can_transition_to("running") is False
    
    def test_can_transition_to_invalid_states(self):
        """Test can_transition_to with invalid states."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        # From created state
        assert lifecycle.can_transition_to("running") is False
        assert lifecycle.can_transition_to("stopped") is False
        assert lifecycle.can_transition_to("failed") is False
    
    def test_transition_to_valid_state(self):
        """Test transition_to with valid state."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        result = lifecycle.transition_to("initializing")
        assert result is True
        assert lifecycle.get_state() == "initializing"
    
    def test_transition_to_invalid_state(self):
        """Test transition_to with invalid state."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        result = lifecycle.transition_to("running")
        assert result is False
        assert lifecycle.get_state() == "created"
    
    def test_state_check_methods(self):
        """Test state check methods."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        # Created state
        assert lifecycle.is_created() is True
        assert lifecycle.is_initializing() is False
        assert lifecycle.is_initialized() is False
        assert lifecycle.is_running() is False
        assert lifecycle.is_stopped() is False
        assert lifecycle.is_failed() is False
        assert lifecycle.is_destroyed() is False
        
        # Transition to initializing
        lifecycle.transition_to("initializing")
        assert lifecycle.is_created() is False
        assert lifecycle.is_initializing() is True
        assert lifecycle.is_initialized() is False
        assert lifecycle.is_running() is False
        assert lifecycle.is_stopped() is False
        assert lifecycle.is_failed() is False
        assert lifecycle.is_destroyed() is False
        
        # Transition to initialized
        lifecycle.transition_to("initialized")
        assert lifecycle.is_created() is False
        assert lifecycle.is_initializing() is False
        assert lifecycle.is_initialized() is True
        assert lifecycle.is_running() is False
        assert lifecycle.is_stopped() is False
        assert lifecycle.is_failed() is False
        assert lifecycle.is_destroyed() is False
        
        # Transition to running
        lifecycle.transition_to("running")
        assert lifecycle.is_created() is False
        assert lifecycle.is_initializing() is False
        assert lifecycle.is_initialized() is False
        assert lifecycle.is_running() is True
        assert lifecycle.is_stopped() is False
        assert lifecycle.is_failed() is False
        assert lifecycle.is_destroyed() is False
        
        # Transition to stopped
        lifecycle.transition_to("stopped")
        assert lifecycle.is_created() is False
        assert lifecycle.is_initializing() is False
        assert lifecycle.is_initialized() is False
        assert lifecycle.is_running() is False
        assert lifecycle.is_stopped() is True
        assert lifecycle.is_failed() is False
        assert lifecycle.is_destroyed() is False
        
        # Transition to failed
        lifecycle.transition_to("failed")
        assert lifecycle.is_created() is False
        assert lifecycle.is_initializing() is False
        assert lifecycle.is_initialized() is False
        assert lifecycle.is_running() is False
        assert lifecycle.is_stopped() is False
        assert lifecycle.is_failed() is True
        assert lifecycle.is_destroyed() is False
        
        # Transition to destroyed
        lifecycle.transition_to("destroyed")
        assert lifecycle.is_created() is False
        assert lifecycle.is_initializing() is False
        assert lifecycle.is_initialized() is False
        assert lifecycle.is_running() is False
        assert lifecycle.is_stopped() is False
        assert lifecycle.is_failed() is False
        assert lifecycle.is_destroyed() is True
    
    def test_state_transitions_workflow(self):
        """Test complete state transition workflow."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        # Created -> Initializing
        assert lifecycle.transition_to("initializing") is True
        assert lifecycle.get_state() == "initializing"
        
        # Initializing -> Initialized
        assert lifecycle.transition_to("initialized") is True
        assert lifecycle.get_state() == "initialized"
        
        # Initialized -> Running
        assert lifecycle.transition_to("running") is True
        assert lifecycle.get_state() == "running"
        
        # Running -> Stopped
        assert lifecycle.transition_to("stopped") is True
        assert lifecycle.get_state() == "stopped"
        
        # Stopped -> Running (can restart)
        assert lifecycle.transition_to("running") is True
        assert lifecycle.get_state() == "running"
        
        # Running -> Destroyed
        assert lifecycle.transition_to("destroyed") is True
        assert lifecycle.get_state() == "destroyed"
    
    def test_failed_state_transitions(self):
        """Test transitions from failed state."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        # Go to failed state
        lifecycle.transition_to("initializing")
        lifecycle.transition_to("failed")
        assert lifecycle.get_state() == "failed"
        
        # Can go back to initializing from failed
        assert lifecycle.transition_to("initializing") is True
        assert lifecycle.get_state() == "initializing"
        
        # Can go to destroyed from failed
        lifecycle.transition_to("failed")
        assert lifecycle.transition_to("destroyed") is True
        assert lifecycle.get_state() == "destroyed"
    
    def test_destroyed_state_no_transitions(self):
        """Test that destroyed state has no valid transitions."""
        component = ConcreteComponent("test_component")
        lifecycle = ComponentLifecycle(component)
        
        # Go to destroyed state
        lifecycle.transition_to("destroyed")
        assert lifecycle.get_state() == "destroyed"
        
        # No valid transitions from destroyed
        assert lifecycle.can_transition_to("created") is False
        assert lifecycle.can_transition_to("initializing") is False
        assert lifecycle.can_transition_to("initialized") is False
        assert lifecycle.can_transition_to("running") is False
        assert lifecycle.can_transition_to("stopped") is False
        assert lifecycle.can_transition_to("failed") is False
        assert lifecycle.can_transition_to("destroyed") is False


class TestLifecycleManager:
    """Test LifecycleManager class."""
    
    def test_lifecycle_manager_init(self):
        """Test LifecycleManager initialization."""
        manager = LifecycleManager()
        
        assert manager._components == {}
    
    def test_register_component(self):
        """Test register_component method."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        
        assert "test" in manager._components
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle is not None
        assert lifecycle.component is component
    
    def test_unregister_component(self):
        """Test unregister_component method."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        manager.unregister_component("test")
        
        assert "test" not in manager._components
        assert manager.get_component_lifecycle("test") is None
    
    def test_unregister_nonexistent_component(self):
        """Test unregister_component with non-existent component."""
        manager = LifecycleManager()
        
        # Should not raise exception
        manager.unregister_component("nonexistent")
    
    def test_get_component_lifecycle(self):
        """Test get_component_lifecycle method."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        lifecycle = manager.get_component_lifecycle("test")
        
        assert lifecycle is not None
        assert lifecycle.component is component
        
        # Non-existent component
        assert manager.get_component_lifecycle("nonexistent") is None
    
    def test_initialize_component_success(self):
        """Test initialize_component with success."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        result = manager.initialize_component("test")
        
        assert result is True
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle.get_state() == "initialized"
        assert component.is_initialized() is True
    
    def test_initialize_component_failure(self):
        """Test initialize_component with failure."""
        manager = LifecycleManager()
        component = Mock(spec=BaseComponent)
        component.initialize.side_effect = Exception("Initialize failed")
        
        manager.register_component("test", component)
        result = manager.initialize_component("test")
        
        assert result is False
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle.get_state() == "failed"
    
    def test_initialize_nonexistent_component(self):
        """Test initialize_component with non-existent component."""
        manager = LifecycleManager()
        
        result = manager.initialize_component("nonexistent")
        assert result is False
    
    def test_start_component_success(self):
        """Test start_component with success."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        manager.initialize_component("test")
        result = manager.start_component("test")
        
        assert result is True
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle.get_state() == "running"
    
    def test_start_component_not_initialized(self):
        """Test start_component with non-initialized component."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        result = manager.start_component("test")
        
        assert result is False
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle.get_state() == "created"
    
    def test_start_nonexistent_component(self):
        """Test start_component with non-existent component."""
        manager = LifecycleManager()
        
        result = manager.start_component("nonexistent")
        assert result is False
    
    def test_stop_component_success(self):
        """Test stop_component with success."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        manager.initialize_component("test")
        manager.start_component("test")
        result = manager.stop_component("test")
        
        assert result is True
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle.get_state() == "stopped"
    
    def test_stop_component_not_running(self):
        """Test stop_component with non-running component."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        manager.initialize_component("test")
        result = manager.stop_component("test")
        
        assert result is False
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle.get_state() == "initialized"
    
    def test_stop_nonexistent_component(self):
        """Test stop_component with non-existent component."""
        manager = LifecycleManager()
        
        result = manager.stop_component("nonexistent")
        assert result is False
    
    def test_destroy_component_success(self):
        """Test destroy_component with success."""
        manager = LifecycleManager()
        component = ConcreteComponent("test_component")
        
        manager.register_component("test", component)
        result = manager.destroy_component("test")
        
        assert result is True
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle.get_state() == "destroyed"
        assert component.is_initialized() is False
    
    def test_destroy_component_failure(self):
        """Test destroy_component with failure."""
        manager = LifecycleManager()
        component = Mock(spec=BaseComponent)
        component.shutdown.side_effect = Exception("Shutdown failed")
        
        manager.register_component("test", component)
        result = manager.destroy_component("test")
        
        assert result is False
        lifecycle = manager.get_component_lifecycle("test")
        assert lifecycle.get_state() == "destroyed"  # State still changes
    
    def test_destroy_nonexistent_component(self):
        """Test destroy_component with non-existent component."""
        manager = LifecycleManager()
        
        result = manager.destroy_component("nonexistent")
        assert result is False
    
    def test_get_all_states(self):
        """Test get_all_states method."""
        manager = LifecycleManager()
        component1 = ConcreteComponent("component1")
        component2 = ConcreteComponent("component2")
        
        manager.register_component("comp1", component1)
        manager.register_component("comp2", component2)
        
        manager.initialize_component("comp1")
        manager.initialize_component("comp2")
        manager.start_component("comp1")
        
        states = manager.get_all_states()
        
        assert states["comp1"] == "running"
        assert states["comp2"] == "initialized"
    
    def test_get_components_by_state(self):
        """Test get_components_by_state method."""
        manager = LifecycleManager()
        component1 = ConcreteComponent("component1")
        component2 = ConcreteComponent("component2")
        component3 = ConcreteComponent("component3")
        
        manager.register_component("comp1", component1)
        manager.register_component("comp2", component2)
        manager.register_component("comp3", component3)
        
        manager.initialize_component("comp1")
        manager.initialize_component("comp2")
        manager.start_component("comp1")
        
        created_components = manager.get_components_by_state("created")
        initialized_components = manager.get_components_by_state("initialized")
        running_components = manager.get_components_by_state("running")
        
        assert "comp3" in created_components
        assert "comp2" in initialized_components
        assert "comp1" in running_components
    
    def test_initialize_all(self):
        """Test initialize_all method."""
        manager = LifecycleManager()
        component1 = ConcreteComponent("component1")
        component2 = ConcreteComponent("component2")
        
        manager.register_component("comp1", component1)
        manager.register_component("comp2", component2)
        
        results = manager.initialize_all()
        
        assert results["comp1"] is True
        assert results["comp2"] is True
        
        lifecycle1 = manager.get_component_lifecycle("comp1")
        lifecycle2 = manager.get_component_lifecycle("comp2")
        assert lifecycle1.get_state() == "initialized"
        assert lifecycle2.get_state() == "initialized"
    
    def test_start_all(self):
        """Test start_all method."""
        manager = LifecycleManager()
        component1 = ConcreteComponent("component1")
        component2 = ConcreteComponent("component2")
        
        manager.register_component("comp1", component1)
        manager.register_component("comp2", component2)
        
        manager.initialize_component("comp1")
        manager.initialize_component("comp2")
        
        results = manager.start_all()
        
        assert results["comp1"] is True
        assert results["comp2"] is True
        
        lifecycle1 = manager.get_component_lifecycle("comp1")
        lifecycle2 = manager.get_component_lifecycle("comp2")
        assert lifecycle1.get_state() == "running"
        assert lifecycle2.get_state() == "running"
    
    def test_stop_all(self):
        """Test stop_all method."""
        manager = LifecycleManager()
        component1 = ConcreteComponent("component1")
        component2 = ConcreteComponent("component2")
        
        manager.register_component("comp1", component1)
        manager.register_component("comp2", component2)
        
        manager.initialize_component("comp1")
        manager.initialize_component("comp2")
        manager.start_component("comp1")
        manager.start_component("comp2")
        
        results = manager.stop_all()
        
        assert results["comp1"] is True
        assert results["comp2"] is True
        
        lifecycle1 = manager.get_component_lifecycle("comp1")
        lifecycle2 = manager.get_component_lifecycle("comp2")
        assert lifecycle1.get_state() == "stopped"
        assert lifecycle2.get_state() == "stopped"
    
    def test_destroy_all(self):
        """Test destroy_all method."""
        manager = LifecycleManager()
        component1 = ConcreteComponent("component1")
        component2 = ConcreteComponent("component2")
        
        manager.register_component("comp1", component1)
        manager.register_component("comp2", component2)
        
        results = manager.destroy_all()
        
        assert results["comp1"] is True
        assert results["comp2"] is True
        
        lifecycle1 = manager.get_component_lifecycle("comp1")
        lifecycle2 = manager.get_component_lifecycle("comp2")
        assert lifecycle1.get_state() == "destroyed"
        assert lifecycle2.get_state() == "destroyed"
    
    def test_mixed_operations(self):
        """Test mixed lifecycle operations."""
        manager = LifecycleManager()
        component1 = ConcreteComponent("component1")
        component2 = ConcreteComponent("component2")
        
        manager.register_component("comp1", component1)
        manager.register_component("comp2", component2)
        
        # Initialize both
        manager.initialize_all()
        
        # Start only comp1
        manager.start_component("comp1")
        
        # Check states
        states = manager.get_all_states()
        assert states["comp1"] == "running"
        assert states["comp2"] == "initialized"
        
        # Stop comp1
        manager.stop_component("comp1")
        
        # Check states
        states = manager.get_all_states()
        assert states["comp1"] == "stopped"
        assert states["comp2"] == "initialized"
        
        # Destroy comp1
        manager.destroy_component("comp1")
        
        # Check states
        states = manager.get_all_states()
        assert states["comp1"] == "destroyed"
        assert states["comp2"] == "initialized"
