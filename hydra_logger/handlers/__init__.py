"""
Role: Public exports for hydra_logger.handlers; no runtime logic besides import wiring.
Used By:
 - Importers of `hydra_logger.handlers` public API.
Depends On:
 - hydra_logger
Notes:
 - Re-exports the hydra_logger.handlers public API with stable import paths.
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
