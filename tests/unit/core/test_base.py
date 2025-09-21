"""
Tests for core/base.py module.

This module tests the base classes and mixins used throughout the system.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict
from hydra_logger.core.base import (
    BaseComponent, BaseLogger, BaseHandler, BaseFormatter, 
    BasePlugin, BaseMonitor
)


class TestBaseComponent:
    """Test BaseComponent class."""
    
    def test_base_component_init(self):
        """Test BaseComponent initialization."""
        component = ConcreteBaseComponent("test_component")
        
        assert component.name == "test_component"
        assert not component._initialized
        assert component._enabled
        assert component._config == {}
    
    def test_base_component_init_with_kwargs(self):
        """Test BaseComponent initialization with kwargs."""
        component = ConcreteBaseComponent("test_component", enabled=False, config={"key": "value"})
        
        assert component._enabled is False
        assert component._config == {"key": "value"}
    
    def test_is_initialized(self):
        """Test is_initialized method."""
        component = ConcreteBaseComponent("test_component")
        
        assert component.is_initialized() is False
        
        component.initialize()
        assert component.is_initialized() is True
    
    def test_is_enabled(self):
        """Test is_enabled method."""
        component = ConcreteBaseComponent("test_component")
        
        assert component.is_enabled() is True
        
        component = ConcreteBaseComponent("test_component", enabled=False)
        assert component.is_enabled() is False
    
    def test_enable(self):
        """Test enable method."""
        component = ConcreteBaseComponent("test_component", enabled=False)
        
        component.enable()
        assert component.is_enabled() is True
    
    def test_disable(self):
        """Test disable method."""
        component = ConcreteBaseComponent("test_component")
        
        component.disable()
        assert component.is_enabled() is False
    
    def test_get_config(self):
        """Test get_config method."""
        component = ConcreteBaseComponent("test_component", config={"key1": "value1", "key2": "value2"})
        
        config = component.get_config()
        assert config == {"key1": "value1", "key2": "value2"}
        # Ensure it returns a copy
        assert config is not component._config
    
    def test_update_config(self):
        """Test update_config method."""
        component = ConcreteBaseComponent("test_component", config={"key1": "value1"})
        
        component.update_config({"key2": "value2", "key3": "value3"})
        assert component._config == {"key1": "value1", "key2": "value2", "key3": "value3"}


class ConcreteBaseComponent(BaseComponent):
    """Concrete implementation for testing."""
    
    def initialize(self) -> None:
        """Initialize the component."""
        self._initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the component."""
        self._initialized = False


class TestConcreteBaseComponent:
    """Test concrete BaseComponent implementation."""
    
    def test_concrete_component_init(self):
        """Test concrete component initialization."""
        component = ConcreteBaseComponent("test", enabled=True, config={"test": "value"})
        
        assert component.name == "test"
        assert component.is_enabled() is True
        assert component.get_config() == {"test": "value"}
        assert not component.is_initialized()
    
    def test_concrete_component_initialize(self):
        """Test concrete component initialization."""
        component = ConcreteBaseComponent("test")
        
        component.initialize()
        assert component.is_initialized() is True
    
    def test_concrete_component_shutdown(self):
        """Test concrete component shutdown."""
        component = ConcreteBaseComponent("test")
        component.initialize()
        
        component.shutdown()
        assert not component.is_initialized()


class TestBaseLogger:
    """Test BaseLogger class."""
    
    def test_base_logger_init(self):
        """Test BaseLogger initialization."""
        logger = ConcreteBaseLogger("test_logger")
        
        assert logger.name == "test_logger"
        assert logger._handlers == {}
        assert logger._formatters == {}
    
    def test_add_handler(self):
        """Test add_handler method."""
        logger = ConcreteBaseLogger("test_logger")
        handler = Mock()
        
        logger.add_handler("test_handler", handler)
        
        assert "test_handler" in logger._handlers
        assert logger._handlers["test_handler"] is handler
    
    def test_remove_handler(self):
        """Test remove_handler method."""
        logger = ConcreteBaseLogger("test_logger")
        handler = Mock()
        logger._handlers = {"test_handler": handler}
        
        logger.remove_handler("test_handler")
        assert "test_handler" not in logger._handlers
    
    def test_remove_nonexistent_handler(self):
        """Test remove_handler with non-existent handler."""
        logger = ConcreteBaseLogger("test_logger")
        
        # Should not raise exception
        logger.remove_handler("nonexistent")
        assert logger._handlers == {}
    
    def test_get_handlers(self):
        """Test get_handlers method."""
        logger = ConcreteBaseLogger("test_logger")
        handler1 = Mock()
        handler2 = Mock()
        logger._handlers = {"handler1": handler1, "handler2": handler2}
        
        handlers = logger.get_handlers()
        assert handlers == {"handler1": handler1, "handler2": handler2}
        # Ensure it returns a copy
        assert handlers is not logger._handlers


class ConcreteBaseLogger(BaseLogger):
    """Concrete implementation for testing."""
    
    def initialize(self) -> None:
        """Initialize the logger."""
        self._initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the logger."""
        self._initialized = False
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message at the specified level."""
        pass


class TestConcreteBaseLogger:
    """Test concrete BaseLogger implementation."""
    
    def test_concrete_logger_init(self):
        """Test concrete logger initialization."""
        logger = ConcreteBaseLogger("test_logger")
        
        assert logger.name == "test_logger"
        assert logger._handlers == {}
        assert logger._formatters == {}
    
    def test_concrete_logger_log(self):
        """Test concrete logger log method."""
        logger = ConcreteBaseLogger("test_logger")
        
        # Should not raise exception
        logger.log("INFO", "Test message")
        logger.log("ERROR", "Error message", extra={"key": "value"})


class TestBaseHandler:
    """Test BaseHandler class."""
    
    def test_base_handler_init(self):
        """Test BaseHandler initialization."""
        handler = ConcreteBaseHandler("test_handler")
        
        assert handler.name == "test_handler"
        assert handler._formatter is None
        assert handler._level == "INFO"
    
    def test_base_handler_init_with_level(self):
        """Test BaseHandler initialization with custom level."""
        handler = ConcreteBaseHandler("test_handler", level="DEBUG")
        
        assert handler._level == "DEBUG"
    
    def test_set_formatter(self):
        """Test set_formatter method."""
        handler = ConcreteBaseHandler("test_handler")
        formatter = Mock()
        
        handler.set_formatter(formatter)
        assert handler._formatter is formatter
    
    def test_get_formatter(self):
        """Test get_formatter method."""
        handler = ConcreteBaseHandler("test_handler")
        formatter = Mock()
        handler._formatter = formatter
        
        assert handler.get_formatter() is formatter
    
    def test_set_level(self):
        """Test set_level method."""
        handler = ConcreteBaseHandler("test_handler")
        
        handler.set_level("DEBUG")
        assert handler._level == "DEBUG"
    
    def test_get_level(self):
        """Test get_level method."""
        handler = ConcreteBaseHandler("test_handler")
        handler._level = "WARNING"
        
        assert handler.get_level() == "WARNING"


class ConcreteBaseHandler(BaseHandler):
    """Concrete implementation for testing."""
    
    def initialize(self) -> None:
        """Initialize the handler."""
        self._initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the handler."""
        self._initialized = False
    
    def emit(self, record) -> None:
        """Emit a log record."""
        pass


class TestConcreteBaseHandler:
    """Test concrete BaseHandler implementation."""
    
    def test_concrete_handler_init(self):
        """Test concrete handler initialization."""
        handler = ConcreteBaseHandler("test_handler", level="DEBUG")
        
        assert handler.name == "test_handler"
        assert handler.get_level() == "DEBUG"
    
    def test_concrete_handler_emit(self):
        """Test concrete handler emit method."""
        handler = ConcreteBaseHandler("test_handler")
        record = Mock()
        
        # Should not raise exception
        handler.emit(record)


class TestBaseFormatter:
    """Test BaseFormatter class."""
    
    def test_base_formatter_init(self):
        """Test BaseFormatter initialization."""
        formatter = ConcreteBaseFormatter("test_formatter")
        
        assert formatter.name == "test_formatter"
        assert formatter._format_string == ""
    
    def test_base_formatter_init_with_format_string(self):
        """Test BaseFormatter initialization with format string."""
        formatter = ConcreteBaseFormatter("test_formatter", format_string="%(levelname)s: %(message)s")
        
        assert formatter._format_string == "%(levelname)s: %(message)s"
    
    def test_get_format_string(self):
        """Test get_format_string method."""
        formatter = ConcreteBaseFormatter("test_formatter", format_string="%(levelname)s: %(message)s")
        
        assert formatter.get_format_string() == "%(levelname)s: %(message)s"
    
    def test_set_format_string(self):
        """Test set_format_string method."""
        formatter = ConcreteBaseFormatter("test_formatter")
        
        formatter.set_format_string("%(levelname)s: %(message)s")
        assert formatter._format_string == "%(levelname)s: %(message)s"


class ConcreteBaseFormatter(BaseFormatter):
    """Concrete implementation for testing."""
    
    def initialize(self) -> None:
        """Initialize the formatter."""
        self._initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the formatter."""
        self._initialized = False
    
    def format(self, record) -> str:
        """Format a log record."""
        return f"{record.level}: {record.message}"


class TestConcreteBaseFormatter:
    """Test concrete BaseFormatter implementation."""
    
    def test_concrete_formatter_init(self):
        """Test concrete formatter initialization."""
        formatter = ConcreteBaseFormatter("test_formatter", format_string="%(levelname)s: %(message)s")
        
        assert formatter.name == "test_formatter"
        assert formatter.get_format_string() == "%(levelname)s: %(message)s"
    
    def test_concrete_formatter_format(self):
        """Test concrete formatter format method."""
        formatter = ConcreteBaseFormatter("test_formatter")
        record = Mock()
        record.level = "INFO"
        record.message = "Test message"
        
        result = formatter.format(record)
        assert result == "INFO: Test message"


class TestBasePlugin:
    """Test BasePlugin class."""
    
    def test_base_plugin_init(self):
        """Test BasePlugin initialization."""
        plugin = ConcreteBasePlugin("test_plugin")
        
        assert plugin.name == "test_plugin"
        assert plugin._plugin_type == "generic"
    
    def test_base_plugin_init_with_type(self):
        """Test BasePlugin initialization with custom type."""
        plugin = ConcreteBasePlugin("test_plugin", plugin_type="custom")
        
        assert plugin._plugin_type == "custom"
    
    def test_get_plugin_type(self):
        """Test get_plugin_type method."""
        plugin = ConcreteBasePlugin("test_plugin", plugin_type="monitoring")
        
        assert plugin.get_plugin_type() == "monitoring"


class ConcreteBasePlugin(BasePlugin):
    """Concrete implementation for testing."""
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        self._initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self._initialized = False
    
    def process_event(self, event: Any) -> None:
        """Process an event."""
        pass


class TestConcreteBasePlugin:
    """Test concrete BasePlugin implementation."""
    
    def test_concrete_plugin_init(self):
        """Test concrete plugin initialization."""
        plugin = ConcreteBasePlugin("test_plugin", plugin_type="custom")
        
        assert plugin.name == "test_plugin"
        assert plugin.get_plugin_type() == "custom"
    
    def test_concrete_plugin_process_event(self):
        """Test concrete plugin process_event method."""
        plugin = ConcreteBasePlugin("test_plugin")
        event = Mock()
        
        # Should not raise exception
        plugin.process_event(event)


class TestBaseMonitor:
    """Test BaseMonitor class."""
    
    def test_base_monitor_init(self):
        """Test BaseMonitor initialization."""
        monitor = ConcreteBaseMonitor("test_monitor")
        
        assert monitor.name == "test_monitor"
        assert monitor._metrics == {}
    
    def test_get_metrics(self):
        """Test get_metrics method."""
        monitor = ConcreteBaseMonitor("test_monitor")
        monitor._metrics = {"cpu": 50.0, "memory": 75.0}
        
        metrics = monitor.get_metrics()
        assert metrics == {"cpu": 50.0, "memory": 75.0}
        # Ensure it returns a copy
        assert metrics is not monitor._metrics
    
    def test_update_metric(self):
        """Test update_metric method."""
        monitor = ConcreteBaseMonitor("test_monitor")
        
        monitor.update_metric("cpu", 50.0)
        assert monitor._metrics["cpu"] == 50.0
        
        monitor.update_metric("memory", 75.0)
        assert monitor._metrics == {"cpu": 50.0, "memory": 75.0}


class ConcreteBaseMonitor(BaseMonitor):
    """Concrete implementation for testing."""
    
    def initialize(self) -> None:
        """Initialize the monitor."""
        self._initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the monitor."""
        self._initialized = False
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics."""
        return {"cpu": 50.0, "memory": 75.0}


class TestConcreteBaseMonitor:
    """Test concrete BaseMonitor implementation."""
    
    def test_concrete_monitor_init(self):
        """Test concrete monitor initialization."""
        monitor = ConcreteBaseMonitor("test_monitor")
        
        assert monitor.name == "test_monitor"
        assert monitor._metrics == {}
    
    def test_concrete_monitor_collect_metrics(self):
        """Test concrete monitor collect_metrics method."""
        monitor = ConcreteBaseMonitor("test_monitor")
        
        metrics = monitor.collect_metrics()
        assert metrics == {"cpu": 50.0, "memory": 75.0}
    
    def test_concrete_monitor_update_metric(self):
        """Test concrete monitor update_metric method."""
        monitor = ConcreteBaseMonitor("test_monitor")
        
        monitor.update_metric("custom_metric", 100.0)
        assert monitor.get_metrics()["custom_metric"] == 100.0


class TestAbstractMethods:
    """Test that abstract methods raise NotImplementedError."""
    
    def test_base_component_abstract_methods(self):
        """Test BaseComponent abstract methods."""
        with pytest.raises(TypeError):
            BaseComponent("test")
    
    def test_base_logger_abstract_methods(self):
        """Test BaseLogger abstract methods."""
        with pytest.raises(TypeError):
            BaseLogger("test")
    
    def test_base_handler_abstract_methods(self):
        """Test BaseHandler abstract methods."""
        with pytest.raises(TypeError):
            BaseHandler("test")
    
    def test_base_formatter_abstract_methods(self):
        """Test BaseFormatter abstract methods."""
        with pytest.raises(TypeError):
            BaseFormatter("test")
    
    def test_base_plugin_abstract_methods(self):
        """Test BasePlugin abstract methods."""
        with pytest.raises(TypeError):
            BasePlugin("test")
    
    def test_base_monitor_abstract_methods(self):
        """Test BaseMonitor abstract methods."""
        with pytest.raises(TypeError):
            BaseMonitor("test")
