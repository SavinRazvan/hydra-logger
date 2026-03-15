"""
Role: Init implementation.
Used By:
 - (update when known)
Depends On:
 - hydra_logger
 - base_handler
 - console_handler
 - file_handler
 - null_handler
Notes:
 - Header standardized by slim-header migration.
"""

from hydra_logger.types.enums import TimeUnit

from .base_handler import BaseHandler
from .console_handler import AsyncConsoleHandler, SyncConsoleHandler
from .file_handler import FileHandler
from .network_handler import (
    BaseNetworkHandler,
    DatagramHandler,
    HTTPHandler,
    NetworkConfig,
    NetworkHandlerFactory,
    NetworkProtocol,
    RetryPolicy,
    SocketHandler,
    WebSocketHandler,
)

# StreamHandler removed - simplified handlers
from .null_handler import NullHandler
from .rotating_handler import (
    HybridRotatingFileHandler,
    RotatingFileHandler,
    RotationConfig,
    RotationStrategy,
    SizeRotatingFileHandler,
    TimedRotatingFileHandler,
)

# Removed over-engineered handlers: system, database, queue, cloud, composite

__all__ = [
    # Base classes
    "BaseHandler",
    # Console handlers
    "SyncConsoleHandler",
    "AsyncConsoleHandler",
    # File handlers
    "FileHandler",
    # Rotating file handlers
    "RotatingFileHandler",
    "TimedRotatingFileHandler",
    "SizeRotatingFileHandler",
    "HybridRotatingFileHandler",
    "RotationConfig",
    "RotationStrategy",
    "TimeUnit",
    # Network handlers
    "BaseNetworkHandler",
    "HTTPHandler",
    "WebSocketHandler",
    "SocketHandler",
    "DatagramHandler",
    "NetworkHandlerFactory",
    "NetworkConfig",
    "NetworkProtocol",
    "RetryPolicy",
    # Utility handlers
    "NullHandler",
]
