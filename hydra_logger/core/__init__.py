"""
Role: Init implementation.
Used By:
 - (update when known)
Depends On:
 - constants
 - types
 - layer_management
 - exceptions
Notes:
 - Header standardized by slim-header migration.
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
