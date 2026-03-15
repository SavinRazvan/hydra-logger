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

from .constants import Colors, QueuePolicy, ShutdownPhase
from ..types.levels import LogLevel
from .layer_management import LayerManager, LayerConfiguration
from .exceptions import (
    HydraLoggerError,
    ConfigurationError,
    ValidationError,
    HandlerError,
    FormatterError,
    PluginError,
    SecurityError,
)

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
