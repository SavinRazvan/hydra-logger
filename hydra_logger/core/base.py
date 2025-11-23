"""
Base Classes and Mixins for Hydra-Logger

This module provides the foundational base classes and mixins that form the core
architecture of the Hydra-Logger system. All components inherit from these base
classes to ensure consistent behavior and interface compliance.

ARCHITECTURE:
- BaseComponent: Abstract base class for all system components
- BaseLogger: Abstract base class for all logger implementations
- BaseHandler: Abstract base class for all log handlers
- BaseFormatter: Abstract base class for all formatters
- BasePlugin: Abstract base class for all plugins
- BaseMonitor: Abstract base class for all monitoring components

FEATURES:
- Consistent lifecycle management (initialize/shutdown)
- Standardized configuration handling
- Enable/disable functionality
- Abstract method enforcement
- Common interface patterns

USAGE EXAMPLES:

Creating Custom Components:
    from hydra_logger.core.base import BaseComponent

    class MyComponent(BaseComponent):
        def initialize(self):
            # Component initialization logic
            self._initialized = True

        def shutdown(self):
            # Component cleanup logic
            self._initialized = False

Creating Custom Loggers:
    from hydra_logger.core.base import BaseLogger

    class MyLogger(BaseLogger):
        def log(self, level: str, message: str, **kwargs):
            # Custom logging implementation
            pass

Creating Custom Handlers:
    from hydra_logger.core.base import BaseHandler

    class MyHandler(BaseHandler):
        def emit(self, record):
            # Custom record emission logic
            pass
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseComponent(ABC):
    """Base class for all components in the system."""

    def __init__(self, name: str, **kwargs):
        self.name = name
        self._initialized = False
        self._enabled = kwargs.get("enabled", True)
        self._config = kwargs.get("config", {})

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the component."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the component."""
        pass

    def is_initialized(self) -> bool:
        """Check if the component is initialized."""
        return self._initialized

    def is_enabled(self) -> bool:
        """Check if the component is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable the component."""
        self._enabled = True

    def disable(self) -> None:
        """Disable the component."""
        self._enabled = False

    def get_config(self) -> Dict[str, Any]:
        """Get the component configuration."""
        return self._config.copy()

    def update_config(self, config: Dict[str, Any]) -> None:
        """Update the component configuration."""
        self._config.update(config)


class BaseLogger(BaseComponent):
    """Base class for all loggers."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self._handlers = {}
        self._formatters = {}

    @abstractmethod
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message at the specified level."""
        pass

    def add_handler(self, name: str, handler) -> None:
        """Add a handler to the logger."""
        self._handlers[name] = handler

    def remove_handler(self, name: str) -> None:
        """Remove a handler from the logger."""
        if name in self._handlers:
            del self._handlers[name]

    def get_handlers(self) -> Dict[str, Any]:
        """Get all handlers."""
        return self._handlers.copy()


class BaseHandler(BaseComponent):
    """Base class for all handlers."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self._formatter = None
        self._level = kwargs.get("level", "INFO")

    @abstractmethod
    def emit(self, record) -> None:
        """Emit a log record."""
        pass

    def set_formatter(self, formatter) -> None:
        """Set the formatter for this handler."""
        self._formatter = formatter

    def get_formatter(self):
        """Get the formatter for this handler."""
        return self._formatter

    def set_level(self, level: str) -> None:
        """Set the log level for this handler."""
        self._level = level

    def get_level(self) -> str:
        """Get the log level for this handler."""
        return self._level


class BaseFormatter(BaseComponent):
    """Base class for all formatters."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self._format_string = kwargs.get("format_string", "")

    @abstractmethod
    def format(self, record) -> str:
        """Format a log record."""
        pass

    def get_format_string(self) -> str:
        """Get the format string."""
        return self._format_string

    def set_format_string(self, format_string: str) -> None:
        """Set the format string."""
        self._format_string = format_string


class BasePlugin(BaseComponent):
    """Base class for all plugins."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self._plugin_type = kwargs.get("plugin_type", "generic")

    @abstractmethod
    def process_event(self, event: Any) -> None:
        """Process an event."""
        pass

    def get_plugin_type(self) -> str:
        """Get the plugin type."""
        return self._plugin_type


class BaseMonitor(BaseComponent):
    """Base class for all monitors."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self._metrics = {}

    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics."""
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return self._metrics.copy()

    def update_metric(self, name: str, value: Any) -> None:
        """Update a metric value."""
        self._metrics[name] = value
