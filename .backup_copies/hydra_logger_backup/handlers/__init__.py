"""
Handlers Module for Hydra-Logger

This module provides a comprehensive collection of output destination handlers
for different logging targets. Handlers are responsible for taking formatted
log records and delivering them to their final destinations.

ARCHITECTURE:
- BaseHandler: Abstract base class for all handlers
- Console Handlers: Synchronous and asynchronous console output
- File Handlers: Local file storage with intelligent buffering
- Network Handlers: HTTP, WebSocket, Socket, and Datagram protocols
- Database Handlers: SQLite, PostgreSQL, MongoDB, and Redis storage
- Queue Handlers: RabbitMQ, Kafka, and Redis Streams messaging
- Cloud Handlers: AWS CloudWatch, Azure Monitor, Google Cloud, Elasticsearch
- System Handlers: Syslog, Systemd Journal, Windows Event Log
- Composite Handlers: Fallback, load balancing, circuit breaker patterns
- Rotating Handlers: Time-based, size-based, and hybrid file rotation

HANDLER TYPES:
- Console: SyncConsoleHandler, AsyncConsoleHandler
- File: FileHandler, SyncFileHandler, AsyncFileHandler
- Network: HTTPHandler, WebSocketHandler, SocketHandler, DatagramHandler
- Database: SQLiteHandler, PostgreSQLHandler, MongoDBHandler, RedisHandler
- Queue: RabbitMQHandler, KafkaHandler, RedisStreamsHandler
- Cloud: AWSCloudWatchHandler, AzureMonitorHandler, GoogleCloudLoggingHandler, ElasticsearchHandler
- System: SyslogHandler, SystemdJournalHandler, WindowsEventLogHandler
- Composite: CompositeHandler, FallbackHandler, LoadBalancingHandler, CircuitBreakerHandler
- Rotating: RotatingFileHandler, TimedRotatingFileHandler, SizeRotatingFileHandler, HybridRotatingFileHandler
- Utility: NullHandler, StreamHandler

PERFORMANCE FEATURES:
- Intelligent buffering for high throughput
- Batch processing for network and database handlers
- Connection pooling for database handlers
- Circuit breaker patterns for fault tolerance
- Load balancing and fallback mechanisms
- Asynchronous processing where appropriate

USAGE EXAMPLES:

Basic Console Handler:
    from hydra_logger.handlers import SyncConsoleHandler
    
    handler = SyncConsoleHandler(use_colors=True)
    logger.addHandler(handler)

File Handler with Rotation:
    from hydra_logger.handlers import TimedRotatingFileHandler
    
    handler = TimedRotatingFileHandler(
        filename="app.log",
        when="midnight",
        backup_count=30
    )
    logger.addHandler(handler)

Database Handler:
    from hydra_logger.handlers import SQLiteHandler
    
    handler = SQLiteHandler(database_path="logs.db")
    logger.addHandler(handler)

Network Handler:
    from hydra_logger.handlers import HTTPHandler
    
    handler = HTTPHandler(
        url="https://api.example.com/logs",
        method="POST"
    )
    logger.addHandler(handler)

Composite Handler with Fallback:
    from hydra_logger.handlers import FallbackHandler, SyncConsoleHandler, FileHandler
    
    primary = SyncConsoleHandler()
    fallback = FileHandler("fallback.log")
    handler = FallbackHandler([primary], [fallback])
    logger.addHandler(handler)

HANDLER MANAGEMENT:
- HandlerManager: Centralized handler registration and management
- Factory patterns for easy handler creation
- Configuration validation and error handling
- Performance monitoring and statistics

CONFIGURATION:
- Standardized configuration classes for each handler type
- Environment variable support
- Validation and error handling
- Default values for common use cases
"""

from hydra_logger.types.enums import TimeUnit
from .base import BaseHandler
from .console import SyncConsoleHandler, AsyncConsoleHandler
from .file import FileHandler
# StreamHandler removed - simplified handlers
from .null import NullHandler
from .rotating import (
    RotatingFileHandler,
    TimedRotatingFileHandler,
    SizeRotatingFileHandler,
    HybridRotatingFileHandler,
    RotationConfig,
    RotationStrategy
)
from .network import (
    BaseNetworkHandler,
    HTTPHandler,
    WebSocketHandler,
    SocketHandler,
    DatagramHandler,
    NetworkHandlerFactory,
    NetworkConfig,
    NetworkProtocol,
    RetryPolicy
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
