"""
Event Types for Hydra-Logger

This module provides comprehensive event type definitions for managing
logging events, notifications, and system events. It includes event
creation, processing, and distribution through an event bus system.

FEATURES:
- LogEvent: Base event class with lifecycle management
- EventType: Different types of logging events
- EventSeverity: Event severity levels
- EventStatus: Event processing status
- EventHandler: Event processing handlers
- EventBus: Event distribution and subscription system

EVENT TYPES:
- LOG_ENTRY: Log entry events
- LOG_LEVEL_CHANGE: Log level configuration changes
- HANDLER_ADDED/REMOVED: Handler management events
- FORMATTER_CHANGED: Formatter configuration changes
- CONFIGURATION_CHANGED: System configuration changes
- PLUGIN_LOADED/UNLOADED: Plugin lifecycle events
- SECURITY_EVENT: Security-related events
- PERFORMANCE_EVENT: Performance monitoring events
- ERROR_EVENT: Error condition events
- SYSTEM_EVENT: System-level events
- CUSTOM_EVENT: Custom application events

SPECIALIZED EVENTS:
- LogEntryEvent: Log record events
- SecurityEvent: Security monitoring events
- PerformanceEvent: Performance metric events
- ErrorEvent: Error tracking events
- SystemEvent: System operation events

USAGE:
    from hydra_logger.types import LogEvent, EventType, EventBus, EventHandler
    
    # Create event bus
    event_bus = EventBus()
    
    # Create event handler
    def log_handler(event):
        print(f"Event: {event.message}")
    
    handler = EventHandler("log_handler", log_handler)
    
    # Subscribe to events
    event_bus.subscribe(EventType.LOG_ENTRY, handler)
    
    # Create and publish event
    event = LogEvent(
        event_type=EventType.LOG_ENTRY,
        message="Application started",
        severity=EventSeverity.INFO
    )
    event_bus.publish(event)
    
    # Create specialized events
    from hydra_logger.types import create_security_event
    security_event = create_security_event(
        "Login attempt failed",
        threat_level="medium",
        threat_type="brute_force"
    )
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List, Callable
from datetime import datetime
from enum import Enum
import time
import uuid


class EventType(Enum):
    """Types of logging events."""
    LOG_ENTRY = "log_entry"
    LOG_LEVEL_CHANGE = "log_level_change"
    HANDLER_ADDED = "handler_added"
    HANDLER_REMOVED = "handler_removed"
    FORMATTER_CHANGED = "formatter_changed"
    CONFIGURATION_CHANGED = "configuration_changed"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    SECURITY_EVENT = "security_event"
    PERFORMANCE_EVENT = "performance_event"
    ERROR_EVENT = "error_event"
    SYSTEM_EVENT = "system_event"
    CUSTOM_EVENT = "custom_event"


class EventSeverity(Enum):
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventStatus(Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LogEvent:
    """Base class for all logging events."""
    
    # Core event information
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM_EVENT
    severity: EventStatus = EventStatus.PENDING
    timestamp: float = field(default_factory=time.time)
    
    # Event content
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Event metadata
    source: Optional[str] = None
    component: Optional[str] = None
    user_id: Optional[str] = None
    
    # Event processing
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    
    # Event relationships
    parent_event_id: Optional[str] = None
    child_event_ids: List[str] = field(default_factory=list)
    
    # Event lifecycle
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize event after creation."""
        if not self.source:
            self.source = self._detect_source()
    
    def _detect_source(self) -> str:
        """Detect the source of the event."""
        try:
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                module = frame.f_back.f_globals.get('__name__', 'unknown')
                return module
        except:
            pass
        return "unknown"
    
    def mark_processing(self) -> None:
        """Mark event as being processed."""
        self.status = EventStatus.PROCESSING
        self.processed_at = datetime.now()
    
    def mark_completed(self) -> None:
        """Mark event as completed."""
        self.status = EventStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def mark_failed(self) -> None:
        """Mark event as failed."""
        self.status = EventStatus.FAILED
        self.completed_at = datetime.now()
    
    def mark_cancelled(self) -> None:
        """Mark event as cancelled."""
        self.status = EventStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def retry(self) -> bool:
        """Attempt to retry the event. Returns True if retry is allowed."""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = EventStatus.PENDING
            self.processed_at = None
            self.completed_at = None
            return True
        return False
    
    def add_child_event(self, child_event_id: str) -> None:
        """Add a child event ID."""
        if child_event_id not in self.child_event_ids:
            self.child_event_ids.append(child_event_id)
    
    def remove_child_event(self, child_event_id: str) -> None:
        """Remove a child event ID."""
        if child_event_id in self.child_event_ids:
            self.child_event_ids.remove(child_event_id)
    
    def set_parent_event(self, parent_event_id: str) -> None:
        """Set the parent event ID."""
        self.parent_event_id = parent_event_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp,
            'message': self.message,
            'data': self.data,
            'source': self.source,
            'component': self.component,
            'user_id': self.user_id,
            'status': self.status.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'parent_event_id': self.parent_event_id,
            'child_event_ids': self.child_event_ids,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"[{self.event_type.value}] {self.message} ({self.status.value})"


@dataclass
class LogEntryEvent(LogEvent):
    """Event representing a log entry."""
    
    log_record: Optional[Any] = None  # LogRecord instance
    log_level: Optional[str] = None
    log_layer: Optional[str] = None
    
    def __post_init__(self):
        """Initialize log entry event."""
        super().__post_init__()
        self.event_type = EventType.LOG_ENTRY
        
        if self.log_record:
            self.log_level = getattr(self.log_record, 'level_name', None)
            self.log_layer = getattr(self.log_record, 'layer', None)
            self.message = getattr(self.log_record, 'message', self.message)


@dataclass
class SecurityEvent(LogEvent):
    """Event representing a security-related event."""
    
    threat_level: str = "low"
    threat_type: Optional[str] = None
    affected_resource: Optional[str] = None
    mitigation_action: Optional[str] = None
    
    def __post_init__(self):
        """Initialize security event."""
        super().__post_init__()
        self.event_type = EventType.SECURITY_EVENT


@dataclass
class PerformanceEvent(LogEvent):
    """Event representing a performance-related event."""
    
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    unit: Optional[str] = None
    
    def __post_init__(self):
        """Initialize performance event."""
        super().__post_init__()
        self.event_type = EventType.PERFORMANCE_EVENT


@dataclass
class ErrorEvent(LogEvent):
    """Event representing an error condition."""
    
    error_type: Optional[str] = None
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    recovery_action: Optional[str] = None
    
    def __post_init__(self):
        """Initialize error event."""
        super().__post_init__()
        self.event_type = EventType.ERROR_EVENT


@dataclass
class SystemEvent(LogEvent):
    """Event representing a system-level event."""
    
    system_component: Optional[str] = None
    operation: Optional[str] = None
    result: Optional[str] = None
    duration: Optional[float] = None
    
    def __post_init__(self):
        """Initialize system event."""
        super().__post_init__()
        self.event_type = EventType.SYSTEM_EVENT


class EventHandler:
    """Handler for processing events."""
    
    def __init__(self, name: str, handler_func: Callable[[LogEvent], None]):
        self.name = name
        self.handler_func = handler_func
        self.enabled = True
        self.processed_count = 0
        self.error_count = 0
    
    def handle(self, event: LogEvent) -> None:
        """Handle an event."""
        if not self.enabled:
            return
        
        try:
            self.handler_func(event)
            self.processed_count += 1
        except Exception as e:
            self.error_count += 1
            # Log the error but don't re-raise to avoid breaking event processing
            print(f"Error in event handler {self.name}: {e}")


class EventBus:
    """Event bus for managing event distribution."""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[LogEvent] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to events of a specific type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def subscribe_global(self, handler: EventHandler) -> None:
        """Subscribe to all events."""
        self._global_handlers.append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe from events of a specific type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]
    
    def unsubscribe_global(self, handler: EventHandler) -> None:
        """Unsubscribe from all events."""
        self._global_handlers = [h for h in self._global_handlers if h != handler]
    
    def publish(self, event: LogEvent) -> None:
        """Publish an event to all subscribers."""
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify type-specific handlers
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                handler.handle(event)
        
        # Notify global handlers
        for handler in self._global_handlers:
            handler.handle(event)
    
    def get_event_history(self, event_type: Optional[EventType] = None) -> List[LogEvent]:
        """Get event history, optionally filtered by type."""
        if event_type is None:
            return self._event_history.copy()
        return [e for e in self._event_history if e.event_type == event_type]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


# Convenience functions
def create_event(event_type: EventType, message: str, 
                data: Optional[Dict[str, Any]] = None,
                severity: EventSeverity = EventSeverity.INFO) -> LogEvent:
    """Create a new log event."""
    return LogEvent(
        event_type=event_type,
        message=message,
        data=data or {},
        severity=severity
    )


def create_log_entry_event(log_record: Any, message: str = "") -> LogEntryEvent:
    """Create a log entry event."""
    return LogEntryEvent(
        message=message,
        log_record=log_record
    )


def create_security_event(message: str, threat_level: str = "low",
                         threat_type: Optional[str] = None) -> SecurityEvent:
    """Create a security event."""
    return SecurityEvent(
        message=message,
        threat_level=threat_level,
        threat_type=threat_type
    )


# Export the main classes and functions
__all__ = [
    "EventType",
    "EventSeverity", 
    "EventStatus",
    "LogEvent",
    "LogEntryEvent",
    "SecurityEvent",
    "PerformanceEvent",
    "ErrorEvent",
    "SystemEvent",
    "EventHandler",
    "EventBus",
    "create_event",
    "create_log_entry_event",
    "create_security_event"
]
