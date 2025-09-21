"""
Component Lifecycle Management System for Hydra-Logger

This module provides comprehensive component lifecycle management with state
tracking, transition management, dependency handling, and event callbacks.
It ensures proper component initialization, activation, and cleanup throughout
their lifecycle.

FEATURES:
- Component lifecycle state management
- State transition validation and tracking
- Dependency resolution and management
- Event handlers and callbacks
- Performance tracking and metrics
- Auto-restart capabilities
- Health monitoring integration

LIFECYCLE STATES:
- Unregistered: Component not registered
- Registered: Component registered but not initialized
- Initializing: Component being initialized
- Active: Component active and running
- Paused: Component paused
- Stopping: Component being stopped
- Stopped: Component stopped
- Error: Component in error state
- Deprecated: Component deprecated
- Removed: Component removed

LIFECYCLE EVENTS:
- Registered: Component registered
- Initializing: Component initializing
- Initialized: Component initialized
- Activated: Component activated
- Paused: Component paused
- Resumed: Component resumed
- Stopping: Component stopping
- Stopped: Component stopped
- Error: Component error
- Deprecated: Component deprecated
- Removed: Component removed
- Health Check: Health check performed
- Performance Update: Performance metrics updated
- Configuration Change: Configuration changed

USAGE:
    from hydra_logger.registry import ComponentLifecycleManager, LifecycleState, LifecycleEvent
    
    # Create lifecycle manager
    manager = ComponentLifecycleManager()
    
    # Register component
    manager.register_component("my_component", auto_restart=True)
    
    # Transition component state
    manager.transition_component("my_component", LifecycleState.ACTIVE)
    
    # Add event handler
    def on_activated(component_id, transition):
        print(f"Component {component_id} activated")
    
    manager.add_event_handler(LifecycleEvent.ACTIVATED, on_activated)
    
    # Get component lifecycle
    lifecycle = manager.get_component_lifecycle("my_component")
    
    # Get lifecycle summary
    summary = manager.get_lifecycle_summary()
"""

import time
import json
import threading
from typing import Any, Dict, List, Optional, Union, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future


class LifecycleState(Enum):
    """Component lifecycle states."""
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class LifecycleEvent(Enum):
    """Lifecycle events that can occur."""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    ACTIVATED = "activated"
    PAUSED = "paused"
    RESUMED = "resumed"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEPRECATED = "deprecated"
    REMOVED = "removed"
    HEALTH_CHECK = "health_check"
    PERFORMANCE_UPDATE = "performance_update"
    CONFIGURATION_CHANGE = "configuration_change"


class LifecyclePhase(Enum):
    """Lifecycle phases for component management."""
    SETUP = "setup"
    STARTUP = "startup"
    RUNNING = "running"
    SHUTDOWN = "shutdown"
    CLEANUP = "cleanup"


@dataclass
class LifecycleTransition:
    """A transition between lifecycle states."""
    
    # Transition details
    from_state: LifecycleState
    to_state: LifecycleState
    event: LifecycleEvent
    timestamp: datetime
    
    # Transition metadata
    reason: Optional[str] = None
    user_initiated: bool = False
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
    # Context
    component_id: str
    phase: LifecyclePhase
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transition to dictionary."""
        return {
            'from_state': self.from_state.value,
            'to_state': self.to_state.value,
            'event': self.event.value,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason,
            'user_initiated': self.user_initiated,
            'error_message': self.error_message,
            'performance_metrics': self.performance_metrics,
            'component_id': self.component_id,
            'phase': self.phase.value,
            'metadata': self.metadata
        }


@dataclass
class ComponentLifecycle:
    """Lifecycle information for a component."""
    
    # Basic information
    component_id: str
    current_state: LifecycleState
    current_phase: LifecyclePhase
    
    # State history
    state_history: List[LifecycleTransition] = field(default_factory=list)
    current_state_start: Optional[datetime] = None
    
    # Lifecycle management
    auto_restart: bool = False
    max_restart_attempts: int = 3
    restart_delay: float = 5.0  # seconds
    health_check_interval: float = 30.0  # seconds
    
    # Performance tracking
    startup_time: Optional[float] = None
    shutdown_time: Optional[float] = None
    total_uptime: float = 0.0
    restart_count: int = 0
    
    # Dependencies
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    tags: Set[str] = field(default_factory=set)
    
    def add_transition(self, transition: LifecycleTransition):
        """Add a lifecycle transition."""
        self.state_history.append(transition)
        self.current_state = transition.to_state
        self.current_phase = transition.phase
        self.current_state_start = transition.timestamp
        self.last_updated = transition.timestamp
        
        # Update uptime tracking
        if transition.event == LifecycleEvent.ACTIVATED:
            self.startup_time = time.time()
        elif transition.event == LifecycleEvent.STOPPED:
            if self.startup_time:
                self.total_uptime += time.time() - self.startup_time
                self.startup_time = None
    
    def get_current_uptime(self) -> float:
        """Get current uptime if component is active."""
        if self.current_state == LifecycleState.ACTIVE and self.startup_time:
            return time.time() - self.startup_time
        return 0.0
    
    def get_total_uptime(self) -> float:
        """Get total uptime including current session."""
        current_uptime = self.get_current_uptime()
        return self.total_uptime + current_uptime
    
    def get_state_duration(self) -> Optional[timedelta]:
        """Get duration of current state."""
        if self.current_state_start:
            return datetime.now() - self.current_state_start
        return None
    
    def can_transition_to(self, target_state: LifecycleState) -> bool:
        """Check if transition to target state is valid."""
        valid_transitions = {
            LifecycleState.UNREGISTERED: [LifecycleState.REGISTERED],
            LifecycleState.REGISTERED: [LifecycleState.INITIALIZING, LifecycleState.REMOVED],
            LifecycleState.INITIALIZING: [LifecycleState.ACTIVE, LifecycleState.ERROR],
            LifecycleState.ACTIVE: [LifecycleState.PAUSED, LifecycleState.STOPPING, LifecycleState.ERROR],
            LifecycleState.PAUSED: [LifecycleState.ACTIVE, LifecycleState.STOPPING],
            LifecycleState.STOPPING: [LifecycleState.STOPPED, LifecycleState.ERROR],
            LifecycleState.STOPPED: [LifecycleState.REGISTERED, LifecycleState.REMOVED],
            LifecycleState.ERROR: [LifecycleState.REGISTERED, LifecycleState.REMOVED],
            LifecycleState.DEPRECATED: [LifecycleState.REMOVED],
            LifecycleState.REMOVED: []
        }
        
        return target_state in valid_transitions.get(self.current_state, [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert lifecycle to dictionary."""
        return {
            'component_id': self.component_id,
            'current_state': self.current_state.value,
            'current_phase': self.current_phase.value,
            'state_history': [t.to_dict() for t in self.state_history],
            'current_state_start': self.current_state_start.isoformat() if self.current_state_start else None,
            'auto_restart': self.auto_restart,
            'max_restart_attempts': self.max_restart_attempts,
            'restart_delay': self.restart_delay,
            'health_check_interval': self.health_check_interval,
            'startup_time': self.startup_time,
            'shutdown_time': self.shutdown_time,
            'total_uptime': self.total_uptime,
            'restart_count': self.restart_count,
            'dependencies': list(self.dependencies),
            'dependents': list(self.dependents),
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'tags': list(self.tags)
        }


class ComponentLifecycleManager:
    """Component lifecycle management system."""
    
    def __init__(self):
        """Initialize the lifecycle manager."""
        self._lifecycles: Dict[str, ComponentLifecycle] = {}
        self._event_handlers: Dict[LifecycleEvent, List[Callable]] = defaultdict(list)
        self._state_handlers: Dict[LifecycleState, List[Callable]] = defaultdict(list)
        self._phase_handlers: Dict[LifecyclePhase, List[Callable]] = defaultdict(list)
        
        # Lifecycle policies
        self._auto_restart_policy = "smart"  # disabled, simple, smart
        self._dependency_resolution = "strict"  # strict, relaxed, none
        self._health_check_enabled = True
        self._performance_monitoring = True
        
        # Threading
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="LifecycleManager")
        self._background_tasks: List[Future] = []
        
        # Statistics
        self._total_transitions = 0
        self._total_events = 0
        self._failed_transitions = 0
        
        # Health monitoring
        self._health_check_timer = None
        self._health_check_interval = 30.0  # seconds
    
    def register_component(self, component_id: str, **kwargs) -> bool:
        """Register a component for lifecycle management."""
        try:
            with self._lock:
                if component_id in self._lifecycles:
                    return False
                
                lifecycle = ComponentLifecycle(
                    component_id=component_id,
                    current_state=LifecycleState.REGISTERED,
                    current_phase=LifecyclePhase.SETUP,
                    **kwargs
                )
                
                self._lifecycles[component_id] = lifecycle
                
                # Record initial transition
                transition = LifecycleTransition(
                    from_state=LifecycleState.UNREGISTERED,
                    to_state=LifecycleState.REGISTERED,
                    event=LifecycleEvent.REGISTERED,
                    timestamp=datetime.now(),
                    component_id=component_id,
                    phase=LifecyclePhase.SETUP
                )
                
                lifecycle.add_transition(transition)
                self._total_transitions += 1
                
                # Trigger event handlers
                self._trigger_event_handlers(LifecycleEvent.REGISTERED, component_id, transition)
                
                return True
        except Exception:
            return False
    
    def unregister_component(self, component_id: str) -> bool:
        """Unregister a component from lifecycle management."""
        try:
            with self._lock:
                if component_id not in self._lifecycles:
                    return False
                
                lifecycle = self._lifecycles[component_id]
                
                # Record removal transition
                transition = LifecycleTransition(
                    from_state=lifecycle.current_state,
                    to_state=LifecycleState.REMOVED,
                    event=LifecycleEvent.REMOVED,
                    timestamp=datetime.now(),
                    component_id=component_id,
                    phase=LifecyclePhase.CLEANUP
                )
                
                lifecycle.add_transition(transition)
                self._total_transitions += 1
                
                # Trigger event handlers
                self._trigger_event_handlers(LifecycleEvent.REMOVED, component_id, transition)
                
                # Remove from management
                del self._lifecycles[component_id]
                
                return True
        except Exception:
            return False
    
    def transition_component(self, component_id: str, target_state: LifecycleState, 
                           reason: Optional[str] = None, user_initiated: bool = False,
                           **kwargs) -> bool:
        """Transition a component to a new state."""
        try:
            with self._lock:
                if component_id not in self._lifecycles:
                    return False
                
                lifecycle = self._lifecycles[component_id]
                
                # Check if transition is valid
                if not lifecycle.can_transition_to(target_state):
                    self._failed_transitions += 1
                    return False
                
                # Determine event and phase
                event, phase = self._get_transition_details(lifecycle.current_state, target_state)
                
                # Create transition
                transition = LifecycleTransition(
                    from_state=lifecycle.current_state,
                    to_state=target_state,
                    event=event,
                    timestamp=datetime.now(),
                    reason=reason,
                    user_initiated=user_initiated,
                    component_id=component_id,
                    phase=phase,
                    **kwargs
                )
                
                # Apply transition
                lifecycle.add_transition(transition)
                self._total_transitions += 1
                self._total_events += 1
                
                # Trigger handlers
                self._trigger_event_handlers(event, component_id, transition)
                self._trigger_state_handlers(target_state, component_id, transition)
                self._trigger_phase_handlers(phase, component_id, transition)
                
                # Handle auto-restart if needed
                if target_state == LifecycleState.ERROR and lifecycle.auto_restart:
                    self._schedule_restart(component_id)
                
                return True
        except Exception:
            self._failed_transitions += 1
            return False
    
    def get_component_lifecycle(self, component_id: str) -> Optional[ComponentLifecycle]:
        """Get lifecycle information for a component."""
        return self._lifecycles.get(component_id)
    
    def get_all_lifecycles(self) -> List[ComponentLifecycle]:
        """Get all component lifecycles."""
        return list(self._lifecycles.values())
    
    def get_components_by_state(self, state: LifecycleState) -> List[str]:
        """Get all components in a specific state."""
        return [
            component_id for component_id, lifecycle in self._lifecycles.items()
            if lifecycle.current_state == state
        ]
    
    def get_components_by_phase(self, phase: LifecyclePhase) -> List[str]:
        """Get all components in a specific phase."""
        return [
            component_id for component_id, lifecycle in self._lifecycles.items()
            if lifecycle.current_phase == phase
        ]
    
    def add_event_handler(self, event: LifecycleEvent, handler: Callable):
        """Add an event handler."""
        self._event_handlers[event].append(handler)
    
    def add_state_handler(self, state: LifecycleState, handler: Callable):
        """Add a state change handler."""
        self._state_handlers[state].append(handler)
    
    def add_phase_handler(self, phase: LifecyclePhase, handler: Callable):
        """Add a phase change handler."""
        self._phase_handlers[phase].append(handler)
    
    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """Get a summary of all lifecycle information."""
        summary = {
            'total_components': len(self._lifecycles),
            'total_transitions': self._total_transitions,
            'total_events': self._total_events,
            'failed_transitions': self._failed_transitions,
            'state_distribution': defaultdict(int),
            'phase_distribution': defaultdict(int),
            'components_by_state': {},
            'components_by_phase': {},
            'recent_transitions': 0,
            'total_uptime': 0.0
        }
        
        now = datetime.now()
        recent_threshold = now - timedelta(hours=1)
        
        for component_id, lifecycle in self._lifecycles.items():
            # State distribution
            summary['state_distribution'][lifecycle.current_state.value] += 1
            
            # Phase distribution
            summary['phase_distribution'][lifecycle.current_phase.value] += 1
            
            # Components by state
            state_key = lifecycle.current_state.value
            if state_key not in summary['components_by_state']:
                summary['components_by_state'][state_key] = []
            summary['components_by_state'][state_key].append(component_id)
            
            # Components by phase
            phase_key = lifecycle.current_phase.value
            if phase_key not in summary['components_by_phase']:
                summary['components_by_phase'][phase_key] = []
            summary['components_by_phase'][phase_key].append(component_id)
            
            # Recent transitions
            if lifecycle.last_updated > recent_threshold:
                summary['recent_transitions'] += 1
            
            # Total uptime
            summary['total_uptime'] += lifecycle.get_total_uptime()
        
        return summary
    
    def export_lifecycle_data(self, format_type: str = "json") -> Union[str, Dict[str, Any]]:
        """Export lifecycle data in specified format."""
        export_data = {
            'lifecycles': {
                component_id: lifecycle.to_dict()
                for component_id, lifecycle in self._lifecycles.items()
            },
            'summary': self.get_lifecycle_summary(),
            'policies': {
                'auto_restart_policy': self._auto_restart_policy,
                'dependency_resolution': self._dependency_resolution,
                'health_check_enabled': self._health_check_enabled,
                'performance_monitoring': self._performance_monitoring
            }
        }
        
        if format_type.lower() == "json":
            return json.dumps(export_data, indent=2)
        elif format_type.lower() == "dict":
            return export_data
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def import_lifecycle_data(self, data: Union[str, Dict[str, Any]], format_type: str = "json") -> bool:
        """Import lifecycle data from external source."""
        try:
            if format_type.lower() == "json" and isinstance(data, str):
                data = json.loads(data)
            
            if not isinstance(data, dict) or 'lifecycles' not in data:
                return False
            
            # Import lifecycles
            for component_id, lifecycle_dict in data['lifecycles'].items():
                # Create lifecycle object
                lifecycle = ComponentLifecycle(**lifecycle_dict)
                self._lifecycles[component_id] = lifecycle
                
                # Update statistics
                self._total_transitions += len(lifecycle.state_history)
                self._total_events += len(lifecycle.state_history)
            
            # Import policies
            if 'policies' in data:
                policies = data['policies']
                self._auto_restart_policy = policies.get('auto_restart_policy', self._auto_restart_policy)
                self._dependency_resolution = policies.get('dependency_resolution', self._dependency_resolution)
                self._health_check_enabled = policies.get('health_check_enabled', self._health_check_enabled)
                self._performance_monitoring = policies.get('performance_monitoring', self._performance_monitoring)
            
            return True
        except Exception:
            return False
    
    def set_lifecycle_policy(self, auto_restart: str = "smart", 
                           dependency_resolution: str = "strict",
                           health_check_enabled: bool = True,
                           performance_monitoring: bool = True):
        """Set lifecycle management policies."""
        self._auto_restart_policy = auto_restart
        self._dependency_resolution = dependency_resolution
        self._health_check_enabled = health_check_enabled
        self._performance_monitoring = performance_monitoring
    
    def _get_transition_details(self, from_state: LifecycleState, 
                               to_state: LifecycleState) -> tuple[LifecycleEvent, LifecyclePhase]:
        """Get event and phase for a state transition."""
        transition_map = {
            (LifecycleState.REGISTERED, LifecycleState.INITIALIZING): (LifecycleEvent.INITIALIZING, LifecyclePhase.STARTUP),
            (LifecycleState.INITIALIZING, LifecycleState.ACTIVE): (LifecycleEvent.INITIALIZED, LifecyclePhase.RUNNING),
            (LifecycleState.ACTIVE, LifecycleState.PAUSED): (LifecycleEvent.PAUSED, LifecyclePhase.RUNNING),
            (LifecycleState.PAUSED, LifecycleState.ACTIVE): (LifecycleEvent.RESUMED, LifecyclePhase.RUNNING),
            (LifecycleState.ACTIVE, LifecycleState.STOPPING): (LifecycleEvent.STOPPING, LifecyclePhase.SHUTDOWN),
            (LifecycleState.STOPPING, LifecycleState.STOPPED): (LifecycleEvent.STOPPED, LifecyclePhase.SHUTDOWN),
            (LifecycleState.REGISTERED, LifecycleState.REMOVED): (LifecycleEvent.REMOVED, LifecyclePhase.CLEANUP),
            (LifecycleState.STOPPED, LifecycleState.REMOVED): (LifecycleEvent.REMOVED, LifecyclePhase.CLEANUP),
            (LifecycleState.ERROR, LifecycleState.REMOVED): (LifecycleEvent.REMOVED, LifecyclePhase.CLEANUP)
        }
        
        return transition_map.get((from_state, to_state), (LifecycleEvent.ERROR, LifecyclePhase.SETUP))
    
    def _trigger_event_handlers(self, event: LifecycleEvent, component_id: str, transition: LifecycleTransition):
        """Trigger event handlers for a lifecycle event."""
        for handler in self._event_handlers[event]:
            try:
                self._executor.submit(handler, event, component_id, transition)
            except Exception:
                pass  # Ignore handler errors
    
    def _trigger_state_handlers(self, state: LifecycleState, component_id: str, transition: LifecycleTransition):
        """Trigger state change handlers."""
        for handler in self._state_handlers[state]:
            try:
                self._executor.submit(handler, state, component_id, transition)
            except Exception:
                pass
    
    def _trigger_phase_handlers(self, phase: LifecyclePhase, component_id: str, transition: LifecycleTransition):
        """Trigger phase change handlers."""
        for handler in self._phase_handlers[phase]:
            try:
                self._executor.submit(handler, phase, component_id, transition)
            except Exception:
                pass
    
    def _schedule_restart(self, component_id: str):
        """Schedule a component restart."""
        lifecycle = self._lifecycles.get(component_id)
        if not lifecycle or lifecycle.restart_count >= lifecycle.max_restart_attempts:
            return
        
        def delayed_restart():
            time.sleep(lifecycle.restart_delay)
            self.transition_component(component_id, LifecycleState.REGISTERED, 
                                   reason="Auto-restart after error")
        
        future = self._executor.submit(delayed_restart)
        self._background_tasks.append(future)
    
    def shutdown(self):
        """Shutdown the lifecycle manager."""
        # Stop all components
        for component_id in list(self._lifecycles.keys()):
            self.transition_component(component_id, LifecycleState.STOPPED, 
                                   reason="Lifecycle manager shutdown")
        
        # Cancel background tasks
        for future in self._background_tasks:
            future.cancel()
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
