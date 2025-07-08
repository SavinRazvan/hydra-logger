"""
Custom exceptions for Hydra-Logger.

This module defines all custom exceptions used throughout the Hydra-Logger system.
"""


class HydraLoggerError(Exception):
    """Base exception for all Hydra-Logger errors."""
    pass


class ConfigurationError(HydraLoggerError):
    """Raised when there's an error in configuration."""
    pass


class ValidationError(HydraLoggerError):
    """Raised when validation fails."""
    pass


class HandlerError(HydraLoggerError):
    """Raised when there's an error with handlers."""
    pass


class FormatterError(HydraLoggerError):
    """Raised when there's an error with formatters."""
    pass


class AsyncError(HydraLoggerError):
    """Raised when there's an error with async operations."""
    pass


class PluginError(HydraLoggerError):
    """Raised when there's an error with plugins."""
    pass


class DataProtectionError(HydraLoggerError):
    """Raised when there's an error with data protection."""
    pass


class AnalyticsError(HydraLoggerError):
    """Raised when there's an error with analytics."""
    pass


class CompatibilityError(HydraLoggerError):
    """Raised when there's an error with backward compatibility."""
    pass


class PerformanceError(HydraLoggerError):
    """Raised when there's an error with performance monitoring."""
    pass 