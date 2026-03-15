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
from .console_handler import SyncConsoleHandler, AsyncConsoleHandler
from .file_handler import FileHandler

# StreamHandler removed - simplified handlers
from .null_handler import NullHandler
from .rotating_handler import (
    RotatingFileHandler,
    TimedRotatingFileHandler,
    SizeRotatingFileHandler,
    HybridRotatingFileHandler,
    RotationConfig,
    RotationStrategy,
)
from .network_handler import (
    BaseNetworkHandler,
    HTTPHandler,
    WebSocketHandler,
    SocketHandler,
    DatagramHandler,
    NetworkHandlerFactory,
    NetworkConfig,
    NetworkProtocol,
    RetryPolicy,
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
