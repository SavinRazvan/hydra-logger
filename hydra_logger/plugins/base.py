"""
Base Plugin Classes for Hydra-Logger

This module provides the foundational base classes for all plugin types in the
Hydra-Logger system. It defines the common interface and behavior patterns
that all plugins must implement, ensuring consistency and interoperability.

PLUGIN TYPES:
- BasePlugin: Abstract base class for all plugins
- AnalyticsPlugin: Base class for analytics and insights plugins
- FormatterPlugin: Base class for custom log formatters
- HandlerPlugin: Base class for custom log handlers
- SecurityPlugin: Base class for security and threat detection plugins
- PerformancePlugin: Base class for performance monitoring plugins

FEATURES:
- Standardized plugin lifecycle (initialize, enable/disable)
- Common configuration and metadata handling
- Type-specific method requirements
- Plugin validation and compatibility checking

USAGE:
    from hydra_logger.plugins import FormatterPlugin
    
    # Create custom formatter plugin
    class MyFormatter(FormatterPlugin):
        def __init__(self, name: str, format_name: str):
            super().__init__(name, format_name)
        
        def initialize(self) -> bool:
            # Plugin initialization logic
            return True
        
        def format(self, record) -> str:
            # Custom formatting logic
            return f"[{record.level}] {record.message}"
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..types.records import LogRecord


class BasePlugin(ABC):
    """Abstract base class for all plugins."""
    
    def __init__(self, name: str, enabled: bool = True):
        """
        Initialize base plugin.
        
        Args:
            name: Plugin name
            enabled: Whether plugin is enabled
        """
        self.name = name
        self.enabled = enabled
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            True if initialization successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement initialize method")
    
    def is_enabled(self) -> bool:
        """
        Check if plugin is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        return self.enabled
    
    def is_initialized(self) -> bool:
        """
        Check if plugin is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
    
    def enable(self) -> None:
        """Enable the plugin."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the plugin."""
        self.enabled = False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get plugin configuration.
        
        Returns:
            Configuration dictionary
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "initialized": self._initialized,
            "type": self.__class__.__name__
        }


class AnalyticsPlugin(BasePlugin):
    """Base class for analytics plugins."""
    
    def __init__(self, name: str, enabled: bool = True):
        """Initialize analytics plugin."""
        super().__init__(name, enabled)
        self._analytics_data = {}
    
    def process_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Process an analytics event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if not self.enabled or not self._initialized:
            return
        
        if event_type not in self._analytics_data:
            self._analytics_data[event_type] = []
        
        self._analytics_data[event_type].append(data)
    
    def get_insights(self) -> Dict[str, Any]:
        """
        Get analytics insights.
        
        Returns:
            Analytics insights dictionary
        """
        return self._analytics_data.copy()
    
    def reset(self) -> None:
        """Reset analytics data."""
        self._analytics_data.clear()


class FormatterPlugin(BasePlugin):
    """Base class for formatter plugins."""
    
    def __init__(self, name: str, format_name: str):
        """
        Initialize formatter plugin.
        
        Args:
            name: Plugin name
            format_name: Format name provided by this plugin
        """
        super().__init__(name)
        self.format_name = format_name
    
    @abstractmethod
    def format(self, record: LogRecord) -> str:
        """
        Format a log record.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted string
        """
        raise NotImplementedError("Subclasses must implement format method")
    
    def get_format_name(self) -> str:
        """
        Get the format name provided by this plugin.
        
        Returns:
            Format name
        """
        return self.format_name


class HandlerPlugin(BasePlugin):
    """Base class for handler plugins."""
    
    def __init__(self, name: str, handler_type: str):
        """
        Initialize handler plugin.
        
        Args:
            name: Plugin name
            handler_type: Handler type provided by this plugin
        """
        super().__init__(name)
        self.handler_type = handler_type
    
    @abstractmethod
    def emit(self, record: LogRecord) -> None:
        """
        Emit a log record.
        
        Args:
            record: Log record to emit
        """
        raise NotImplementedError("Subclasses must implement emit method")
    
    def get_handler_type(self) -> str:
        """
        Get the handler type provided by this plugin.
        
        Returns:
            Handler type
        """
        return self.handler_type


class SecurityPlugin(BasePlugin):
    """Base class for security plugins."""
    
    def __init__(self, name: str, enabled: bool = True):
        """Initialize security plugin."""
        super().__init__(name, enabled)
        self._threat_patterns = []
        self._security_stats = {
            "threats_detected": 0,
            "suspicious_activities": 0,
            "security_score": 100
        }
    
    def add_threat_pattern(self, pattern: str) -> None:
        """
        Add a threat detection pattern.
        
        Args:
            pattern: Threat pattern to detect
        """
        self._threat_patterns.append(pattern)
    
    def detect_threats(self, data: str) -> bool:
        """
        Detect threats in data.
        
        Args:
            data: Data to analyze
            
        Returns:
            True if threat detected, False otherwise
        """
        if not self.enabled or not self._initialized:
            return False
        
        for pattern in self._threat_patterns:
            if pattern in data:
                self._security_stats["threats_detected"] += 1
                return True
        
        return False
    
    def get_security_score(self) -> int:
        """
        Get current security score.
        
        Returns:
            Security score (0-100)
        """
        return self._security_stats["security_score"]
    
    def get_security_stats(self) -> Dict[str, Any]:
        """
        Get security statistics.
        
        Returns:
            Security statistics dictionary
        """
        return self._security_stats.copy()


class PerformancePlugin(BasePlugin):
    """Base class for performance plugins."""
    
    def __init__(self, name: str, enabled: bool = True):
        """Initialize performance plugin."""
        super().__init__(name, enabled)
        self._performance_thresholds = {}
        self._performance_stats = {
            "operations_tracked": 0,
            "slow_operations": 0,
            "average_response_time": 0.0
        }
    
    def initialize(self) -> bool:
        """
        Initialize the performance plugin.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self._initialized = True
            return True
        except Exception:
            return False
    
    def set_threshold(self, metric: str, threshold: float) -> None:
        """
        Set performance threshold.
        
        Args:
            metric: Metric name
            threshold: Threshold value
        """
        self._performance_thresholds[metric] = threshold
    
    def track_operation(self, operation: str, duration: float) -> None:
        """
        Track operation performance.
        
        Args:
            operation: Operation name
            duration: Operation duration
        """
        if not self.enabled or not self._initialized:
            return
        
        self._performance_stats["operations_tracked"] += 1
        
        # Update average response time
        current_avg = self._performance_stats["average_response_time"]
        total_ops = self._performance_stats["operations_tracked"]
        self._performance_stats["average_response_time"] = (
            (current_avg * (total_ops - 1) + duration) / total_ops
        )
        
        # Check thresholds
        if operation in self._performance_thresholds:
            if duration > self._performance_thresholds[operation]:
                self._performance_stats["slow_operations"] += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Performance statistics dictionary
        """
        return self._performance_stats.copy()
