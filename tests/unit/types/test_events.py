"""
Tests for hydra_logger.types.events module.
"""

import pytest
import time
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
from hydra_logger.types.events import (
    EventType, EventSeverity, EventStatus, LogEvent, LogEntryEvent,
    SecurityEvent, PerformanceEvent, ErrorEvent, SystemEvent,
    EventHandler, EventBus, create_event, create_log_entry_event, create_security_event
)


class TestEventType:
    """Test EventType enum."""
    
    def test_event_type_values(self):
        """Test EventType enum values."""
        assert EventType.LOG_ENTRY.value == "log_entry"
        assert EventType.LOG_LEVEL_CHANGE.value == "log_level_change"
        assert EventType.HANDLER_ADDED.value == "handler_added"
        assert EventType.HANDLER_REMOVED.value == "handler_removed"
        assert EventType.FORMATTER_CHANGED.value == "formatter_changed"
        assert EventType.CONFIGURATION_CHANGED.value == "configuration_changed"
        assert EventType.PLUGIN_LOADED.value == "plugin_loaded"
        assert EventType.PLUGIN_UNLOADED.value == "plugin_unloaded"
        assert EventType.SECURITY_EVENT.value == "security_event"
        assert EventType.PERFORMANCE_EVENT.value == "performance_event"
        assert EventType.ERROR_EVENT.value == "error_event"
        assert EventType.SYSTEM_EVENT.value == "system_event"
        assert EventType.CUSTOM_EVENT.value == "custom_event"
    
    def test_event_type_members(self):
        """Test EventType enum members."""
        assert len(list(EventType)) == 13
        assert EventType.LOG_ENTRY in EventType
        assert EventType.CUSTOM_EVENT in EventType


class TestEventSeverity:
    """Test EventSeverity enum."""
    
    def test_event_severity_values(self):
        """Test EventSeverity enum values."""
        assert EventSeverity.DEBUG.value == "debug"
        assert EventSeverity.INFO.value == "info"
        assert EventSeverity.WARNING.value == "warning"
        assert EventSeverity.ERROR.value == "error"
        assert EventSeverity.CRITICAL.value == "critical"
    
    def test_event_severity_members(self):
        """Test EventSeverity enum members."""
        assert len(list(EventSeverity)) == 5
        assert EventSeverity.DEBUG in EventSeverity
        assert EventSeverity.CRITICAL in EventSeverity


class TestEventStatus:
    """Test EventStatus enum."""
    
    def test_event_status_values(self):
        """Test EventStatus enum values."""
        assert EventStatus.PENDING.value == "pending"
        assert EventStatus.PROCESSING.value == "processing"
        assert EventStatus.COMPLETED.value == "completed"
        assert EventStatus.FAILED.value == "failed"
        assert EventStatus.CANCELLED.value == "cancelled"
    
    def test_event_status_members(self):
        """Test EventStatus enum members."""
        assert len(list(EventStatus)) == 5
        assert EventStatus.PENDING in EventStatus
        assert EventStatus.CANCELLED in EventStatus


class TestLogEvent:
    """Test LogEvent class."""
    
    def test_log_event_creation(self):
        """Test LogEvent creation."""
        event = LogEvent()
        
        assert isinstance(event.event_id, str)
        assert event.event_type == EventType.CUSTOM_EVENT
        assert event.severity == EventStatus.PENDING
        assert isinstance(event.timestamp, float)
        assert event.message == ""
        assert event.data == {}
        assert event.source is not None  # Should be detected
        assert event.component is None
        assert event.user_id is None
        assert event.status == EventStatus.PENDING
        assert event.retry_count == 0
        assert event.max_retries == 3
        assert event.parent_event_id is None
        assert event.child_event_ids == []
        assert isinstance(event.created_at, datetime)
        assert event.processed_at is None
        assert event.completed_at is None
    
    def test_log_event_with_parameters(self):
        """Test LogEvent creation with specific parameters."""
        event = LogEvent(
            event_type=EventType.LOG_ENTRY,
            message="Test message",
            data={"key": "value"},
            source="test_module",
            component="test_component",
            user_id="user123",
            severity=EventSeverity.INFO
        )
        
        assert event.event_type == EventType.LOG_ENTRY
        assert event.message == "Test message"
        assert event.data == {"key": "value"}
        assert event.source == "test_module"
        assert event.component == "test_component"
        assert event.user_id == "user123"
        assert event.severity == EventSeverity.INFO
    
    def test_log_event_detect_source(self):
        """Test LogEvent source detection."""
        event = LogEvent()
        
        # Source should be detected automatically
        assert event.source is not None
        assert event.source != "unknown"
    
    @patch('inspect.currentframe')
    def test_log_event_detect_source_no_frame(self, mock_currentframe):
        """Test LogEvent source detection when no frame available."""
        mock_currentframe.return_value = None
        
        event = LogEvent()
        assert event.source == "unknown"
    
    @patch('inspect.currentframe')
    def test_log_event_detect_source_exception(self, mock_currentframe):
        """Test LogEvent source detection when exception occurs."""
        # Mock currentframe to raise an exception
        mock_currentframe.side_effect = Exception("Test exception")
        
        event = LogEvent()
        assert event.source == "unknown"
    
    def test_mark_processing(self):
        """Test mark_processing method."""
        event = LogEvent()
        
        event.mark_processing()
        
        assert event.status == EventStatus.PROCESSING
        assert event.processed_at is not None
        assert isinstance(event.processed_at, datetime)
    
    def test_mark_completed(self):
        """Test mark_completed method."""
        event = LogEvent()
        
        event.mark_completed()
        
        assert event.status == EventStatus.COMPLETED
        assert event.completed_at is not None
        assert isinstance(event.completed_at, datetime)
    
    def test_mark_failed(self):
        """Test mark_failed method."""
        event = LogEvent()
        
        event.mark_failed()
        
        assert event.status == EventStatus.FAILED
        assert event.completed_at is not None
        assert isinstance(event.completed_at, datetime)
    
    def test_mark_cancelled(self):
        """Test mark_cancelled method."""
        event = LogEvent()
        
        event.mark_cancelled()
        
        assert event.status == EventStatus.CANCELLED
        assert event.completed_at is not None
        assert isinstance(event.completed_at, datetime)
    
    def test_retry_success(self):
        """Test retry method when retry is allowed."""
        event = LogEvent()
        event.max_retries = 2
        
        # First retry
        result = event.retry()
        assert result is True
        assert event.retry_count == 1
        assert event.status == EventStatus.PENDING
        assert event.processed_at is None
        assert event.completed_at is None
        
        # Second retry
        result = event.retry()
        assert result is True
        assert event.retry_count == 2
        assert event.status == EventStatus.PENDING
    
    def test_retry_failure(self):
        """Test retry method when retry is not allowed."""
        event = LogEvent()
        event.max_retries = 1
        event.retry_count = 1
        
        result = event.retry()
        assert result is False
        assert event.retry_count == 1  # Should not increase
        assert event.status == EventStatus.PENDING  # Should not change
    
    def test_add_child_event(self):
        """Test add_child_event method."""
        event = LogEvent()
        child_id = "child123"
        
        event.add_child_event(child_id)
        assert child_id in event.child_event_ids
        
        # Adding same child again should not duplicate
        event.add_child_event(child_id)
        assert event.child_event_ids.count(child_id) == 1
    
    def test_remove_child_event(self):
        """Test remove_child_event method."""
        event = LogEvent()
        child_id = "child123"
        
        event.add_child_event(child_id)
        assert child_id in event.child_event_ids
        
        event.remove_child_event(child_id)
        assert child_id not in event.child_event_ids
        
        # Removing non-existent child should not raise error
        event.remove_child_event("nonexistent")
    
    def test_set_parent_event(self):
        """Test set_parent_event method."""
        event = LogEvent()
        parent_id = "parent123"
        
        event.set_parent_event(parent_id)
        assert event.parent_event_id == parent_id
    
    def test_to_dict(self):
        """Test to_dict method."""
        event = LogEvent(
            message="Test message",
            data={"key": "value"},
            source="test_module"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_id"] == event.event_id
        assert event_dict["event_type"] == event.event_type.value
        assert event_dict["severity"] == event.severity.value
        assert event_dict["timestamp"] == event.timestamp
        assert event_dict["message"] == "Test message"
        assert event_dict["data"] == {"key": "value"}
        assert event_dict["source"] == "test_module"
        assert event_dict["status"] == event.status.value
        assert event_dict["retry_count"] == 0
        assert event_dict["max_retries"] == 3
        assert event_dict["parent_event_id"] is None
        assert event_dict["child_event_ids"] == []
        assert "created_at" in event_dict
        assert event_dict["processed_at"] is None
        assert event_dict["completed_at"] is None
    
    def test_to_dict_with_dates(self):
        """Test to_dict method with processed and completed dates."""
        event = LogEvent()
        event.mark_processing()
        event.mark_completed()
        
        event_dict = event.to_dict()
        
        assert event_dict["processed_at"] is not None
        assert event_dict["completed_at"] is not None
        assert isinstance(event_dict["processed_at"], str)
        assert isinstance(event_dict["completed_at"], str)
    
    def test_str_representation(self):
        """Test string representation."""
        event = LogEvent(
            event_type=EventType.LOG_ENTRY,
            message="Test message",
            status=EventStatus.COMPLETED
        )
        
        str_repr = str(event)
        assert "[log_entry]" in str_repr
        assert "Test message" in str_repr
        assert "(completed)" in str_repr
    
    def test_init_method(self):
        """Test __init__ method directly."""
        event = LogEvent.__new__(LogEvent)
        LogEvent.__init__(event)
        
        assert isinstance(event.event_id, str)
        assert event.event_type == EventType.CUSTOM_EVENT
        assert event.severity == EventStatus.PENDING
        assert isinstance(event.timestamp, float)
        assert event.message == ""
        assert event.data == {}
        assert event.source is not None
        assert event.component is None
        assert event.user_id is None
        assert event.status == EventStatus.PENDING
        assert event.retry_count == 0
        assert event.max_retries == 3
        assert event.parent_event_id is None
        assert event.child_event_ids == []
        assert isinstance(event.created_at, datetime)
        assert event.processed_at is None
        assert event.completed_at is None
    
    def test_post_init_method(self):
        """Test __post_init__ method."""
        event = LogEvent.__new__(LogEvent)
        LogEvent.__init__(event)
        
        # Call __post_init__ directly
        LogEvent.__post_init__(event)
        
        # Should not change anything since it's already initialized
        assert isinstance(event.event_id, str)
        assert event.event_type == EventType.CUSTOM_EVENT


class TestLogEntryEvent:
    """Test LogEntryEvent class."""
    
    def test_log_entry_event_creation(self):
        """Test LogEntryEvent creation."""
        event = LogEntryEvent()
        
        assert event.event_type == EventType.LOG_ENTRY
        assert event.log_record is None
        assert event.log_level is None
        assert event.log_layer is None
    
    def test_log_entry_event_with_log_record(self):
        """Test LogEntryEvent with log record."""
        mock_record = MagicMock()
        mock_record.level_name = "INFO"
        mock_record.layer = "test"
        mock_record.message = "Log message"
        
        event = LogEntryEvent(
            message="Event message",
            log_record=mock_record
        )
        
        assert event.event_type == EventType.LOG_ENTRY
        assert event.log_record == mock_record
        assert event.log_level == "INFO"
        assert event.log_layer == "test"
        assert event.message == "Log message"  # Should use log record message
    
    def test_log_entry_event_without_log_record(self):
        """Test LogEntryEvent without log record."""
        event = LogEntryEvent(message="Event message")
        
        assert event.event_type == EventType.LOG_ENTRY
        assert event.log_record is None
        assert event.log_level is None
        assert event.log_layer is None
        assert event.message == "Event message"


class TestSecurityEvent:
    """Test SecurityEvent class."""
    
    def test_security_event_creation(self):
        """Test SecurityEvent creation."""
        event = SecurityEvent()
        
        assert event.event_type == EventType.SECURITY_EVENT
        assert event.threat_level == "low"
        assert event.threat_type is None
        assert event.affected_resource is None
        assert event.mitigation_action is None
    
    def test_security_event_with_parameters(self):
        """Test SecurityEvent with parameters."""
        event = SecurityEvent(
            message="Security breach detected",
            threat_level="high",
            threat_type="malware",
            affected_resource="server01",
            mitigation_action="quarantine"
        )
        
        assert event.event_type == EventType.SECURITY_EVENT
        assert event.message == "Security breach detected"
        assert event.threat_level == "high"
        assert event.threat_type == "malware"
        assert event.affected_resource == "server01"
        assert event.mitigation_action == "quarantine"


class TestPerformanceEvent:
    """Test PerformanceEvent class."""
    
    def test_performance_event_creation(self):
        """Test PerformanceEvent creation."""
        event = PerformanceEvent()
        
        assert event.event_type == EventType.PERFORMANCE_EVENT
        assert event.metric_name is None
        assert event.metric_value is None
        assert event.threshold is None
        assert event.unit is None
    
    def test_performance_event_with_parameters(self):
        """Test PerformanceEvent with parameters."""
        event = PerformanceEvent(
            message="High CPU usage",
            metric_name="cpu_usage",
            metric_value=95.5,
            threshold=90.0,
            unit="percent"
        )
        
        assert event.event_type == EventType.PERFORMANCE_EVENT
        assert event.message == "High CPU usage"
        assert event.metric_name == "cpu_usage"
        assert event.metric_value == 95.5
        assert event.threshold == 90.0
        assert event.unit == "percent"


class TestErrorEvent:
    """Test ErrorEvent class."""
    
    def test_error_event_creation(self):
        """Test ErrorEvent creation."""
        event = ErrorEvent()
        
        assert event.event_type == EventType.ERROR_EVENT
        assert event.error_type is None
        assert event.error_code is None
        assert event.stack_trace is None
        assert event.recovery_action is None
    
    def test_error_event_with_parameters(self):
        """Test ErrorEvent with parameters."""
        event = ErrorEvent(
            message="Database connection failed",
            error_type="ConnectionError",
            error_code="DB001",
            stack_trace="Traceback...",
            recovery_action="retry_connection"
        )
        
        assert event.event_type == EventType.ERROR_EVENT
        assert event.message == "Database connection failed"
        assert event.error_type == "ConnectionError"
        assert event.error_code == "DB001"
        assert event.stack_trace == "Traceback..."
        assert event.recovery_action == "retry_connection"


class TestSystemEvent:
    """Test SystemEvent class."""
    
    def test_system_event_creation(self):
        """Test SystemEvent creation."""
        event = SystemEvent()
        
        assert event.event_type == EventType.SYSTEM_EVENT
        assert event.system_component is None
        assert event.operation is None
        assert event.result is None
        assert event.duration is None
    
    def test_system_event_with_parameters(self):
        """Test SystemEvent with parameters."""
        event = SystemEvent(
            message="System startup completed",
            system_component="logger",
            operation="startup",
            result="success",
            duration=1.5
        )
        
        assert event.event_type == EventType.SYSTEM_EVENT
        assert event.message == "System startup completed"
        assert event.system_component == "logger"
        assert event.operation == "startup"
        assert event.result == "success"
        assert event.duration == 1.5


class TestEventHandler:
    """Test EventHandler class."""
    
    def test_event_handler_creation(self):
        """Test EventHandler creation."""
        def handler_func(event):
            pass
        
        handler = EventHandler("test_handler", handler_func)
        
        assert handler.name == "test_handler"
        assert handler.handler_func == handler_func
        assert handler.enabled is True
        assert handler.processed_count == 0
        assert handler.error_count == 0
    
    def test_event_handler_handle_success(self):
        """Test EventHandler handle method with success."""
        events_handled = []
        
        def handler_func(event):
            events_handled.append(event)
        
        handler = EventHandler("test_handler", handler_func)
        event = LogEvent(message="Test event")
        
        handler.handle(event)
        
        assert len(events_handled) == 1
        assert events_handled[0] == event
        assert handler.processed_count == 1
        assert handler.error_count == 0
    
    def test_event_handler_handle_error(self):
        """Test EventHandler handle method with error."""
        def handler_func(event):
            raise ValueError("Test error")
        
        handler = EventHandler("test_handler", handler_func)
        event = LogEvent(message="Test event")
        
        # Should not raise exception
        handler.handle(event)
        
        assert handler.processed_count == 0
        assert handler.error_count == 1
    
    def test_event_handler_disabled(self):
        """Test EventHandler when disabled."""
        events_handled = []
        
        def handler_func(event):
            events_handled.append(event)
        
        handler = EventHandler("test_handler", handler_func)
        handler.enabled = False
        event = LogEvent(message="Test event")
        
        handler.handle(event)
        
        assert len(events_handled) == 0
        assert handler.processed_count == 0
        assert handler.error_count == 0


class TestEventBus:
    """Test EventBus class."""
    
    def test_event_bus_creation(self):
        """Test EventBus creation."""
        bus = EventBus()
        
        assert bus._handlers == {}
        assert bus._global_handlers == []
        assert bus._event_history == []
        assert bus._max_history == 1000
    
    def test_subscribe(self):
        """Test subscribe method."""
        bus = EventBus()
        handler = EventHandler("test_handler", lambda e: None)
        
        bus.subscribe(EventType.LOG_ENTRY, handler)
        
        assert EventType.LOG_ENTRY in bus._handlers
        assert handler in bus._handlers[EventType.LOG_ENTRY]
    
    def test_subscribe_multiple_handlers(self):
        """Test subscribe method with multiple handlers."""
        bus = EventBus()
        handler1 = EventHandler("handler1", lambda e: None)
        handler2 = EventHandler("handler2", lambda e: None)
        
        bus.subscribe(EventType.LOG_ENTRY, handler1)
        bus.subscribe(EventType.LOG_ENTRY, handler2)
        
        assert len(bus._handlers[EventType.LOG_ENTRY]) == 2
        assert handler1 in bus._handlers[EventType.LOG_ENTRY]
        assert handler2 in bus._handlers[EventType.LOG_ENTRY]
    
    def test_subscribe_global(self):
        """Test subscribe_global method."""
        bus = EventBus()
        handler = EventHandler("global_handler", lambda e: None)
        
        bus.subscribe_global(handler)
        
        assert handler in bus._global_handlers
    
    def test_unsubscribe(self):
        """Test unsubscribe method."""
        bus = EventBus()
        handler = EventHandler("test_handler", lambda e: None)
        
        bus.subscribe(EventType.LOG_ENTRY, handler)
        assert handler in bus._handlers[EventType.LOG_ENTRY]
        
        bus.unsubscribe(EventType.LOG_ENTRY, handler)
        assert handler not in bus._handlers[EventType.LOG_ENTRY]
    
    def test_unsubscribe_global(self):
        """Test unsubscribe_global method."""
        bus = EventBus()
        handler = EventHandler("global_handler", lambda e: None)
        
        bus.subscribe_global(handler)
        assert handler in bus._global_handlers
        
        bus.unsubscribe_global(handler)
        assert handler not in bus._global_handlers
    
    def test_publish(self):
        """Test publish method."""
        bus = EventBus()
        events_handled = []
        
        def handler_func(event):
            events_handled.append(event)
        
        handler = EventHandler("test_handler", handler_func)
        bus.subscribe(EventType.LOG_ENTRY, handler)
        
        event = LogEvent(event_type=EventType.LOG_ENTRY, message="Test event")
        bus.publish(event)
        
        assert len(events_handled) == 1
        assert events_handled[0] == event
        assert len(bus._event_history) == 1
        assert bus._event_history[0] == event
    
    def test_publish_global_handler(self):
        """Test publish method with global handler."""
        bus = EventBus()
        events_handled = []
        
        def handler_func(event):
            events_handled.append(event)
        
        handler = EventHandler("global_handler", handler_func)
        bus.subscribe_global(handler)
        
        event = LogEvent(event_type=EventType.LOG_ENTRY, message="Test event")
        bus.publish(event)
        
        assert len(events_handled) == 1
        assert events_handled[0] == event
    
    def test_publish_both_handlers(self):
        """Test publish method with both type-specific and global handlers."""
        bus = EventBus()
        type_events = []
        global_events = []
        
        def type_handler(event):
            type_events.append(event)
        
        def global_handler(event):
            global_events.append(event)
        
        type_handler_obj = EventHandler("type_handler", type_handler)
        global_handler_obj = EventHandler("global_handler", global_handler)
        
        bus.subscribe(EventType.LOG_ENTRY, type_handler_obj)
        bus.subscribe_global(global_handler_obj)
        
        event = LogEvent(event_type=EventType.LOG_ENTRY, message="Test event")
        bus.publish(event)
        
        assert len(type_events) == 1
        assert len(global_events) == 1
        assert type_events[0] == event
        assert global_events[0] == event
    
    def test_publish_history_limit(self):
        """Test publish method with history limit."""
        bus = EventBus()
        bus._max_history = 2
        
        # Add more events than the limit
        for i in range(3):
            event = LogEvent(message=f"Event {i}")
            bus.publish(event)
        
        assert len(bus._event_history) == 2
        assert bus._event_history[0].message == "Event 1"  # First event should be removed
        assert bus._event_history[1].message == "Event 2"
    
    def test_get_event_history(self):
        """Test get_event_history method."""
        bus = EventBus()
        
        # Add events of different types
        event1 = LogEvent(event_type=EventType.LOG_ENTRY, message="Log event")
        event2 = LogEvent(event_type=EventType.ERROR_EVENT, message="Error event")
        event3 = LogEvent(event_type=EventType.LOG_ENTRY, message="Another log event")
        
        bus.publish(event1)
        bus.publish(event2)
        bus.publish(event3)
        
        # Get all events
        all_events = bus.get_event_history()
        assert len(all_events) == 3
        
        # Get events by type
        log_events = bus.get_event_history(EventType.LOG_ENTRY)
        assert len(log_events) == 2
        assert all(e.event_type == EventType.LOG_ENTRY for e in log_events)
        
        error_events = bus.get_event_history(EventType.ERROR_EVENT)
        assert len(error_events) == 1
        assert error_events[0].event_type == EventType.ERROR_EVENT
    
    def test_clear_history(self):
        """Test clear_history method."""
        bus = EventBus()
        
        # Add some events
        for i in range(3):
            event = LogEvent(message=f"Event {i}")
            bus.publish(event)
        
        assert len(bus._event_history) == 3
        
        bus.clear_history()
        assert len(bus._event_history) == 0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_event(self):
        """Test create_event function."""
        event = create_event(
            EventType.LOG_ENTRY,
            "Test message",
            {"key": "value"},
            EventSeverity.INFO
        )
        
        assert isinstance(event, LogEvent)
        assert event.event_type == EventType.LOG_ENTRY
        assert event.message == "Test message"
        assert event.data == {"key": "value"}
        assert event.severity == EventSeverity.INFO
    
    def test_create_event_defaults(self):
        """Test create_event function with defaults."""
        event = create_event(EventType.LOG_ENTRY, "Test message")
        
        assert isinstance(event, LogEvent)
        assert event.event_type == EventType.LOG_ENTRY
        assert event.message == "Test message"
        assert event.data == {}
        assert event.severity == EventSeverity.INFO
    
    def test_create_log_entry_event(self):
        """Test create_log_entry_event function."""
        mock_record = MagicMock()
        mock_record.level_name = "INFO"
        mock_record.layer = "test"
        mock_record.message = "Log message"
        
        event = create_log_entry_event(mock_record, "Event message")
        
        assert isinstance(event, LogEntryEvent)
        assert event.event_type == EventType.LOG_ENTRY
        assert event.log_record == mock_record
        assert event.log_level == "INFO"
        assert event.log_layer == "test"
        assert event.message == "Log message"  # Should use log record message
    
    def test_create_security_event(self):
        """Test create_security_event function."""
        event = create_security_event(
            "Security breach",
            "high",
            "malware"
        )
        
        assert isinstance(event, SecurityEvent)
        assert event.event_type == EventType.SECURITY_EVENT
        assert event.message == "Security breach"
        assert event.threat_level == "high"
        assert event.threat_type == "malware"
    
    def test_create_security_event_defaults(self):
        """Test create_security_event function with defaults."""
        event = create_security_event("Security breach")
        
        assert isinstance(event, SecurityEvent)
        assert event.event_type == EventType.SECURITY_EVENT
        assert event.message == "Security breach"
        assert event.threat_level == "low"
        assert event.threat_type is None


class TestEventIntegration:
    """Integration tests for event functionality."""
    
    def test_event_lifecycle(self):
        """Test complete event lifecycle."""
        event = LogEvent(
            event_type=EventType.LOG_ENTRY,
            message="Test event"
        )
        
        # Initial state
        assert event.status == EventStatus.PENDING
        assert event.processed_at is None
        assert event.completed_at is None
        
        # Mark as processing
        event.mark_processing()
        assert event.status == EventStatus.PROCESSING
        assert event.processed_at is not None
        
        # Mark as completed
        event.mark_completed()
        assert event.status == EventStatus.COMPLETED
        assert event.completed_at is not None
    
    def test_event_retry_cycle(self):
        """Test event retry cycle."""
        event = LogEvent(max_retries=2)
        
        # First retry
        assert event.retry() is True
        assert event.retry_count == 1
        assert event.status == EventStatus.PENDING
        
        # Second retry
        assert event.retry() is True
        assert event.retry_count == 2
        assert event.status == EventStatus.PENDING
        
        # Third retry should fail
        assert event.retry() is False
        assert event.retry_count == 2  # Should not increase
    
    def test_event_hierarchy(self):
        """Test event parent-child relationships."""
        parent = LogEvent(message="Parent event")
        child1 = LogEvent(message="Child event 1")
        child2 = LogEvent(message="Child event 2")
        
        # Set up hierarchy
        child1.set_parent_event(parent.event_id)
        child2.set_parent_event(parent.event_id)
        parent.add_child_event(child1.event_id)
        parent.add_child_event(child2.event_id)
        
        # Verify relationships
        assert child1.parent_event_id == parent.event_id
        assert child2.parent_event_id == parent.event_id
        assert child1.event_id in parent.child_event_ids
        assert child2.event_id in parent.child_event_ids
    
    def test_event_bus_complete_workflow(self):
        """Test complete event bus workflow."""
        bus = EventBus()
        events_received = []
        
        def log_handler(event):
            events_received.append(("log", event))
        
        def error_handler(event):
            events_received.append(("error", event))
        
        def global_handler(event):
            events_received.append(("global", event))
        
        # Subscribe handlers
        bus.subscribe(EventType.LOG_ENTRY, EventHandler("log_handler", log_handler))
        bus.subscribe(EventType.ERROR_EVENT, EventHandler("error_handler", error_handler))
        bus.subscribe_global(EventHandler("global_handler", global_handler))
        
        # Publish events
        log_event = LogEvent(event_type=EventType.LOG_ENTRY, message="Log message")
        error_event = LogEvent(event_type=EventType.ERROR_EVENT, message="Error message")
        
        bus.publish(log_event)
        bus.publish(error_event)
        
        # Verify all handlers received events
        assert len(events_received) == 4  # 2 events × 2 handlers each (type-specific + global)
        
        # Check event history
        history = bus.get_event_history()
        assert len(history) == 2
        assert log_event in history
        assert error_event in history
