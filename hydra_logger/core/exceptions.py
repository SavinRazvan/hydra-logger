"""
Role: Implements hydra_logger.core.exceptions functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - typing
Notes:
 - Provides core runtime primitives for exceptions.
"""

from typing import Any, Dict, Optional


class HydraLoggerError(Exception):
    """Base exception class for all Hydra-Logger errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = None  # Will be set by error tracker

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message

    def get_details(self) -> Dict[str, Any]:
        """Get error details."""
        return self.details.copy()


class ConfigurationError(HydraLoggerError):
    """Configuration-related errors."""

    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        config_data: Optional[Dict[str, Any]] = None,
    ):
        details = {}
        if config_path:
            details["config_path"] = config_path
        if config_data:
            details["config_data"] = config_data

        super().__init__(message, details)
        self.config_path = config_path
        self.config_data = config_data


class ValidationError(HydraLoggerError):
    """Validation-related errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        rule: Optional[str] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        if rule:
            details["rule"] = rule

        super().__init__(message, details)
        self.field = field
        self.value = value
        self.rule = rule


class HandlerError(HydraLoggerError):
    """Handler-related errors."""

    def __init__(
        self,
        message: str,
        handler_type: Optional[str] = None,
        handler_name: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if handler_type:
            details["handler_type"] = handler_type
        if handler_name:
            details["handler_name"] = handler_name
        if operation:
            details["operation"] = operation

        super().__init__(message, details)
        self.handler_type = handler_type
        self.handler_name = handler_name
        self.operation = operation


class FormatterError(HydraLoggerError):
    """Formatter-related errors."""

    def __init__(
        self,
        message: str,
        formatter_type: Optional[str] = None,
        format_string: Optional[str] = None,
    ):
        details = {}
        if formatter_type:
            details["formatter_type"] = formatter_type
        if format_string:
            details["format_string"] = format_string

        super().__init__(message, details)
        self.formatter_type = formatter_type
        self.format_string = format_string


class AsyncError(HydraLoggerError):
    """Async operation errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        coroutine_name: Optional[str] = None,
        event_loop_info: Optional[Dict[str, Any]] = None,
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if coroutine_name:
            details["coroutine_name"] = coroutine_name
        if event_loop_info:
            details["event_loop_info"] = event_loop_info

        super().__init__(message, details)
        self.operation = operation
        self.coroutine_name = coroutine_name
        self.event_loop_info = event_loop_info


class PluginError(HydraLoggerError):
    """Plugin-related errors."""

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_type: Optional[str] = None,
        plugin_path: Optional[str] = None,
    ):
        details = {}
        if plugin_name:
            details["plugin_name"] = plugin_name
        if plugin_type:
            details["plugin_type"] = plugin_type
        if plugin_path:
            details["plugin_path"] = plugin_path

        super().__init__(message, details)
        self.plugin_name = plugin_name
        self.plugin_type = plugin_type
        self.plugin_path = plugin_path


class DataProtectionError(HydraLoggerError):
    """Data protection and security errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        data_type: Optional[str] = None,
        security_level: Optional[str] = None,
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if data_type:
            details["data_type"] = data_type
        if security_level:
            details["security_level"] = security_level

        super().__init__(message, details)
        self.operation = operation
        self.data_type = data_type
        self.security_level = security_level


class AnalyticsError(HydraLoggerError):
    """Analytics and metrics errors."""

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        metric_value: Optional[Any] = None,
        aggregation_type: Optional[str] = None,
    ):
        details = {}
        if metric_name:
            details["metric_name"] = metric_name
        if metric_value is not None:
            details["metric_value"] = metric_value
        if aggregation_type:
            details["aggregation_type"] = aggregation_type

        super().__init__(message, details)
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.aggregation_type = aggregation_type


class CompatibilityError(HydraLoggerError):
    """Compatibility and migration errors."""

    def __init__(
        self,
        message: str,
        old_version: Optional[str] = None,
        new_version: Optional[str] = None,
        feature: Optional[str] = None,
    ):
        details = {}
        if old_version:
            details["old_version"] = old_version
        if new_version:
            details["new_version"] = new_version
        if feature:
            details["feature"] = feature

        super().__init__(message, details)
        self.old_version = old_version
        self.new_version = new_version
        self.feature = feature


class PerformanceError(HydraLoggerError):
    """Performance-related errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        duration: Optional[float] = None,
        threshold: Optional[float] = None,
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if duration is not None:
            details["duration"] = duration
        if threshold is not None:
            details["threshold"] = threshold

        super().__init__(message, details)
        self.operation = operation
        self.duration = duration
        self.threshold = threshold


class SecurityError(HydraLoggerError):
    """Security-related errors."""

    def __init__(
        self,
        message: str,
        threat_type: Optional[str] = None,
        severity: Optional[str] = None,
        source: Optional[str] = None,
    ):
        details = {}
        if threat_type:
            details["threat_type"] = threat_type
        if severity:
            details["severity"] = severity
        if source:
            details["source"] = source

        super().__init__(message, details)
        self.threat_type = threat_type
        self.severity = severity
        self.source = source


class RegistryError(HydraLoggerError):
    """Component registry errors."""

    def __init__(
        self,
        message: str,
        component_type: Optional[str] = None,
        component_name: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if component_type:
            details["component_type"] = component_type
        if component_name:
            details["component_name"] = component_name
        if operation:
            details["operation"] = operation

        super().__init__(message, details)
        self.component_type = component_type
        self.component_name = component_name
        self.operation = operation


class FactoryError(HydraLoggerError):
    """Component factory errors."""

    def __init__(
        self,
        message: str,
        component_type: Optional[str] = None,
        factory_method: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        details = {}
        if component_type:
            details["component_type"] = component_type
        if factory_method:
            details["factory_method"] = factory_method
        if parameters:
            details["parameters"] = parameters

        super().__init__(message, details)
        self.component_type = component_type
        self.factory_method = factory_method
        self.parameters = parameters


class LifecycleError(HydraLoggerError):
    """Component lifecycle errors."""

    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        lifecycle_phase: Optional[str] = None,
        expected_phase: Optional[str] = None,
    ):
        details = {}
        if component:
            details["component"] = component
        if lifecycle_phase:
            details["lifecycle_phase"] = lifecycle_phase
        if expected_phase:
            details["expected_phase"] = expected_phase

        super().__init__(message, details)
        self.component = component
        self.lifecycle_phase = lifecycle_phase
        self.expected_phase = expected_phase
