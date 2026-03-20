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

from .batched_http_handler import BatchedHTTPHandler
from .base_handler import BaseHandler
from .console_handler import AsyncConsoleHandler, SyncConsoleHandler
from .file_handler import FileHandler
from .http_payload_encoders import (
    clear_http_payload_encoders,
    load_http_encoders_from_entry_points,
    register_http_payload_encoder,
    resolve_http_payload_encoder,
    unregister_http_payload_encoder,
)
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
    "BatchedHTTPHandler",
    "HTTPHandler",
    "WebSocketHandler",
    "SocketHandler",
    "DatagramHandler",
    "NetworkHandlerFactory",
    "NetworkConfig",
    "NetworkProtocol",
    "RetryPolicy",
    "register_http_payload_encoder",
    "unregister_http_payload_encoder",
    "clear_http_payload_encoders",
    "resolve_http_payload_encoder",
    "load_http_encoders_from_entry_points",
    # Utility handlers
    "NullHandler",
]
