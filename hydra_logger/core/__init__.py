"""
Role: Public core package exports.
Used By:
 - Consumers importing `hydra_logger.core` symbols directly.
Depends On:
 - constants
 - types
 - layer_management
 - exceptions
Notes:
 - Re-exports core constants, exceptions, and layer management primitives.
"""

from ..types.levels import LogLevel
from .constants import Colors, QueuePolicy, ShutdownPhase
from .exceptions import (
    ConfigurationError,
    FormatterError,
    HandlerError,
    HydraLoggerError,
    PluginError,
    SecurityError,
    ValidationError,
)
from .layer_management import LayerConfiguration, LayerManager

__all__ = [
    # Constants
    "Colors",
    "LogLevel",
    "QueuePolicy",
    "ShutdownPhase",
    # Layer Management
    "LayerManager",
    "LayerConfiguration",
    # Exceptions
    "HydraLoggerError",
    "ConfigurationError",
    "ValidationError",
    "HandlerError",
    "FormatterError",
    "PluginError",
    "SecurityError",
]
