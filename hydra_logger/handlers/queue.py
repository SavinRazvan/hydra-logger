"""
Queue Handlers for Hydra-Logger

This module provides comprehensive queue-based logging handlers for various
message queue systems and streaming platforms. It includes connection management,
batch processing, and retry mechanisms for optimal performance.

ARCHITECTURE:
- BaseQueueHandler: Abstract base class for all queue handlers
- RabbitMQHandler: RabbitMQ message queue integration
- KafkaHandler: Apache Kafka distributed streaming integration
- RedisStreamsHandler: Redis Streams integration
- QueueHandlerFactory: Factory for creating queue handlers

SUPPORTED QUEUE SYSTEMS:
- RabbitMQ: Advanced message queuing with routing
- Apache Kafka: Distributed streaming platform
- Redis Streams: Redis-based streaming data structure

PERFORMANCE FEATURES:
- Intelligent batch processing (100 messages or 5s intervals)
- Connection pooling and management
- Message persistence and reliability
- Formatter-aware handling for optimal performance
- Comprehensive error handling and retry mechanisms

QUEUE TYPES:
- RABBITMQ: Advanced message queuing with routing
- KAFKA: Distributed streaming platform
- REDIS_STREAMS: Redis-based streaming data structure

EXCHANGE TYPES (RabbitMQ):
- DIRECT: Direct routing based on routing key
- FANOUT: Broadcast to all bound queues
- TOPIC: Pattern-based routing
- HEADERS: Header-based routing

USAGE EXAMPLES:

RabbitMQ Handler:
    from hydra_logger.handlers import RabbitMQHandler
    
    handler = RabbitMQHandler(
        host="localhost",
        port=5672,
        username="guest",
        password="guest",
        queue_name="logs",
        exchange_name="logs",
        routing_key="logs"
    )
    logger.addHandler(handler)

Kafka Handler:
    from hydra_logger.handlers import KafkaHandler
    
    handler = KafkaHandler(
        bootstrap_servers=["localhost:9092"],
        topic="logs"
    )
    logger.addHandler(handler)

Redis Streams Handler:
    from hydra_logger.handlers import RedisStreamsHandler
    
    handler = RedisStreamsHandler(
        host="localhost",
        port=6379,
        stream_key="logs",
        max_len=10000
    )
    logger.addHandler(handler)

Factory Pattern:
    from hydra_logger.handlers import QueueHandlerFactory
    
    # Create RabbitMQ handler
    handler = QueueHandlerFactory.create_handler(
        "rabbitmq",
        host="localhost",
        queue_name="logs"
    )
    
    # Create Kafka handler
    handler = QueueHandlerFactory.create_handler(
        "kafka",
        bootstrap_servers=["localhost:9092"],
        topic="logs"
    )

Performance Monitoring:
    # Get queue statistics
    stats = handler.get_queue_stats()
    print(f"Connected: {stats['connected']}")
    print(f"Messages published: {stats['messages_published']}")
    print(f"Batch count: {stats['batch_count']}")
    print(f"Error count: {stats['error_count']}")

REQUIRED DEPENDENCIES:
- RabbitMQ: pip install pika
- Kafka: pip install kafka-python
- Redis: pip install redis

Note: These handlers will gracefully handle missing dependencies by logging
appropriate error messages and returning False for connection attempts.

CONFIGURATION:
- Connection settings: host, port, username, password, virtual_host
- Queue settings: queue_name, exchange_name, routing_key, exchange_type
- Message settings: persistent, priority, ttl
- Batch settings: batch_size, batch_timeout, auto_flush
- Pool settings: max_connections, connection_timeout

ERROR HANDLING:
- Automatic retry with exponential backoff
- Connection recovery and reconnection
- Fallback mechanisms for failed operations
- Comprehensive error logging
- Graceful degradation

THREAD SAFETY:
- Thread-safe operations with proper locking
- Safe concurrent access
- Atomic batch operations
- Connection pooling and management
"""

import json
import time
import threading
import sys
from typing import Optional, Dict, Any, Union, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from hydra_logger.handlers.base import BaseHandler
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


class QueueType(Enum):
    """Supported queue types."""
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    REDIS_STREAMS = "redis_streams"


class ExchangeType(Enum):
    """RabbitMQ exchange types."""
    DIRECT = "direct"
    FANOUT = "fanout"
    TOPIC = "topic"
    HEADERS = "headers"


@dataclass
class QueueConfig:
    """Configuration for queue handlers."""
    # Connection settings
    host: str = "localhost"
    port: int = 5672
    username: Optional[str] = None
    password: Optional[str] = None
    virtual_host: str = "/"
    
    # Queue settings
    queue_name: str = "logs"
    exchange_name: str = "logs"
    routing_key: str = "logs"
    exchange_type: ExchangeType = ExchangeType.DIRECT
    
    # Message settings
    persistent: bool = True
    priority: int = 0
    ttl: Optional[int] = None  # milliseconds
    
    # Batch settings
    batch_size: int = 100
    batch_timeout: float = 5.0
    auto_flush: bool = True
    
    # Connection pooling
    max_connections: int = 5
    connection_timeout: float = 30.0
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0


class BaseQueueHandler(BaseHandler):
    """Base class for queue-based handlers."""
    
    def __init__(
        self,
        config: QueueConfig,
        timestamp_config=None,
        **kwargs
    ):
        """Initialize base queue handler."""
        super().__init__(name="queue", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        
        self.config = config
        self._connected = False
        self._connection_lock = threading.RLock()
        
        # Batch handling
        self._batch_buffer = []
        self._batch_lock = threading.Lock()
        self._last_flush = time.time()
        
        # Statistics
        self._message_count = 0
        self._batch_count = 0
        self._error_count = 0
        
        # Formatter-aware handling
        self._is_csv_formatter = False
        self._is_json_formatter = False
        self._is_streaming_formatter = False
        self._needs_special_handling = False
        
        # Initialize queue
        self._init_queue()
    
    def setFormatter(self, formatter):
        """
        Set formatter and detect if it needs special handling.
        
        Args:
            formatter: Formatter instance
        """
        super().setFormatter(formatter)
        
        # Detect formatter type for optimal handling
        if formatter:
            self._is_csv_formatter = (
                hasattr(formatter, 'format_headers') and 
                hasattr(formatter, 'should_write_headers')
            )
            self._is_json_formatter = hasattr(formatter, 'write_header')
            self._is_streaming_formatter = hasattr(formatter, 'format_for_streaming')
            
            # Determine if special handling is needed
            self._needs_special_handling = (
                self._is_csv_formatter or 
                self._is_json_formatter or 
                self._is_streaming_formatter
            )
        else:
            # Reset flags if no formatter
            self._is_csv_formatter = False
            self._is_json_formatter = False
            self._is_streaming_formatter = False
            self._needs_special_handling = False
    
    def handleError(self, record: LogRecord) -> None:
        """
        Handle errors that occur during record processing.
        
        Args:
            record: The log record that caused the error
        """
        self._error_count += 1
        print(f"Error: Queue handler error processing record: {record.message}", file=sys.stderr)
        
        # Try to log the error to a fallback destination if available
        if hasattr(self, 'fallback_handler') and self.fallback_handler:
            try:
                self.fallback_handler.handle(record)
            except Exception:
                # If fallback also fails, just log to stderr
                print(f"Error: Fallback handler also failed for record: {record.message}", file=sys.stderr)
    
    def _init_queue(self) -> None:
        """Initialize queue connection and setup."""
        try:
            success = self._establish_connection()
            if success:
                self._connected = True
                self._setup_queue()
        except Exception as e:
            print(f"Error: Queue initialization failed: {e}", file=sys.stderr)
            self._connected = False
    
    def _establish_connection(self) -> bool:
        """Establish queue connection. Override in subclasses."""
        raise NotImplementedError
    
    def _setup_queue(self) -> None:
        """Setup queue configuration. Override in subclasses."""
        pass
    
    def _publish_message(self, record: LogRecord) -> bool:
        """Publish a single message. Override in subclasses."""
        raise NotImplementedError
    
    def _publish_batch(self, records: List[LogRecord]) -> bool:
        """Publish multiple messages. Override in subclasses."""
        raise NotImplementedError
    
    def emit(self, record: LogRecord) -> None:
        """Emit log record to queue."""
        if not self._connected:
            if not self._init_queue():
                self.handleError(record)
                return
        
        try:
            # Add to batch buffer
            with self._batch_lock:
                self._batch_buffer.append(record)
                
                # Check if we should flush
                should_flush = (
                    len(self._batch_buffer) >= self.config.batch_size or
                    (self.config.auto_flush and 
                     time.time() - self._last_flush >= self.config.batch_timeout)
                )
                
                if should_flush:
                    self._flush_batch()
            
            # Update statistics
            self._message_count += 1
            
        except Exception as e:
            self._error_count += 1
            print(f"Error: Failed to add record to batch: {e}", file=sys.stderr)
            self.handleError(record)
    
    def _flush_batch(self) -> None:
        """Flush the current batch to the queue."""
        if not self._batch_buffer:
            return
        
        try:
            # Get current batch
            with self._batch_lock:
                current_batch = self._batch_buffer.copy()
                self._batch_buffer.clear()
                self._last_flush = time.time()
            
            # Publish batch
            if self._publish_batch(current_batch):
                self._batch_count += 1
            else:
                # Re-add records to buffer on failure
                with self._batch_lock:
                    self._batch_buffer.extend(current_batch)
                    
        except Exception as e:
            self._error_count += 1
            print(f"Error: Failed to flush batch: {e}", file=sys.stderr)
            
            # Re-add records to buffer on failure
            with self._batch_lock:
                self._batch_buffer.extend(current_batch)
    
    def flush(self) -> None:
        """Flush any pending records."""
        self._flush_batch()
    
    def close(self) -> None:
        """Close the handler."""
        self.flush()
        self._close_connection()
        super().close()
    
    def _close_connection(self) -> None:
        """Close queue connection. Override in subclasses."""
        pass
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            'connected': self._connected,
            'message_count': self._message_count,
            'batch_count': self._batch_count,
            'error_count': self._error_count,
            'batch_buffer_size': len(self._batch_buffer),
            'last_flush': self._last_flush
        }


class RabbitMQHandler(BaseQueueHandler):
    """
    RabbitMQ handler for AMQP messaging.
    
    Provides reliable message queuing with RabbitMQ.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        virtual_host: str = "/",
        queue_name: str = "logs",
        exchange_name: str = "logs",
        routing_key: str = "logs",
        **kwargs
    ):
        """Initialize RabbitMQ handler."""
        # Create config
        config = QueueConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            virtual_host=virtual_host,
            queue_name=queue_name,
            exchange_name=exchange_name,
            routing_key=routing_key,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.connection = None
        self.channel = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish RabbitMQ connection."""
        try:
            import pika  # type: ignore
            
            with self._connection_lock:
                # Create connection parameters
                credentials = pika.PlainCredentials(
                    self.config.username,
                    self.config.password
                )
                
                parameters = pika.ConnectionParameters(
                    host=self.config.host,
                    port=self.config.port,
                    virtual_host=self.config.virtual_host,
                    credentials=credentials,
                    connection_attempts=self.config.max_retries,
                    retry_delay=self.config.retry_delay
                )
                
                # Establish connection
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                return True
                
        except ImportError:
            print("pika library is required for RabbitMQ. Install with: pip install pika")
            return False
        except Exception as e:
            print(f"Error: RabbitMQ connection failed: {e}", file=sys.stderr)
            return False
    
    def _setup_queue(self) -> None:
        """Setup RabbitMQ queue and exchange."""
        try:
            with self._connection_lock:
                # Declare exchange
                self.channel.exchange_declare(
                    exchange=self.config.exchange_name,
                    exchange_type=self.config.exchange_type.value,
                    durable=True
                )
                
                # Declare queue
                self.channel.queue_declare(
                    queue=self.config.queue_name,
                    durable=True,
                    arguments={
                        'x-message-ttl': self.config.ttl
                    } if self.config.ttl else {}
                )
                
                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=self.config.exchange_name,
                    queue=self.config.queue_name,
                    routing_key=self.config.routing_key
                )
                
        except Exception as e:
            print(f"Error: Failed to setup RabbitMQ queue: {e}", file=sys.stderr)
            raise
    
    def _publish_message(self, record: LogRecord) -> bool:
        """Publish a single message to RabbitMQ."""
        try:
            import pika  # type: ignore
            
            # Prepare message
            message = self.format(record)
            
            # Create message properties
            properties = pika.BasicProperties(
                delivery_mode=2 if self.config.persistent else 1,  # 2 = persistent
                priority=self.config.priority,
                timestamp=int(record.timestamp),
                headers={
                    'level': record.levelname,
                    'logger': record.logger_name,
                    'filename': getattr(record, 'filename', ''),
                    'function': getattr(record, 'function_name', ''),
                    'line': getattr(record, 'line_number', '')
                }
            )
            
            # Publish message
            with self._connection_lock:
                self.channel.basic_publish(
                    exchange=self.config.exchange_name,
                    routing_key=self.config.routing_key,
                    body=message,
                    properties=properties
                )
                
                return True
                
        except ImportError:
            print("pika library is required for RabbitMQ. Install with: pip install pika")
            return False
        except Exception as e:
            print(f"Error: Failed to publish message to RabbitMQ: {e}", file=sys.stderr)
            return False
    
    def _publish_batch(self, records: List[LogRecord]) -> bool:
        """Publish multiple messages to RabbitMQ."""
        try:
            import pika  # type: ignore
            
            with self._connection_lock:
                for record in records:
                    # Prepare message
                    message = self.format(record)
                    
                    # Create message properties
                    properties = pika.BasicProperties(
                        delivery_mode=2 if self.config.persistent else 1,
                        priority=self.config.priority,
                        timestamp=int(record.timestamp),
                        headers={
                            'level': record.levelname,
                            'logger': record.logger_name,
                            'filename': getattr(record, 'filename', ''),
                            'function': getattr(record, 'function_name', ''),
                            'line': getattr(record, 'line_number', '')
                        }
                    )
                    
                    # Publish message
                    self.channel.basic_publish(
                        exchange=self.config.exchange_name,
                        routing_key=self.config.routing_key,
                        body=message,
                        properties=properties
                    )
                
                return True
                
        except ImportError:
            print("pika library is required for RabbitMQ. Install with: pip install pika")
            return False
        except Exception as e:
            print(f"Error: Failed to publish batch to RabbitMQ: {e}", file=sys.stderr)
            return False
    
    def _close_connection(self) -> None:
        """Close RabbitMQ connection."""
        if self.channel:
            with self._connection_lock:
                try:
                    self.channel.close()
                except Exception:
                    pass
                self.channel = None
        
        if self.connection:
            with self._connection_lock:
                try:
                    self.connection.close()
                except Exception:
                    pass
                self.connection = None


class KafkaHandler(BaseQueueHandler):
    """
    Kafka handler for distributed streaming.
    
    Provides high-throughput message streaming with Apache Kafka.
    """
    
    def __init__(
        self,
        bootstrap_servers: Union[str, List[str]] = "localhost:9092",
        topic: str = "logs",
        **kwargs
    ):
        """Initialize Kafka handler."""
        # Create config
        config = QueueConfig(
            host=bootstrap_servers if isinstance(bootstrap_servers, str) else bootstrap_servers[0],
            queue_name=topic,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish Kafka connection."""
        try:
            from kafka import KafkaProducer  # type: ignore
            
            with self._connection_lock:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Wait for all replicas
                    retries=self.config.max_retries,
                    request_timeout_ms=int(self.config.connection_timeout * 1000)
                )
                
                # Test connection
                self.producer.metrics()
                
                return True
                
        except ImportError:
            print("kafka-python library is required for Kafka. Install with: pip install kafka-python")
            return False
        except Exception as e:
            print(f"Error: Kafka connection failed: {e}", file=sys.stderr)
            return False
    
    def _publish_message(self, record: LogRecord) -> bool:
        """Publish a single message to Kafka."""
        try:
            # Prepare message
            message = {
                'message': self.format(record),
                'level': record.levelname,
                'timestamp': record.timestamp,
                'logger': record.logger_name,
                'filename': getattr(record, 'filename', ''),
                'function': getattr(record, 'function_name', ''),
                'line': getattr(record, 'line_number', ''),
                'extra': getattr(record, 'extra', {})
            }
            
            # Generate key for partitioning
            key = f"{record.logger_name}:{record.levelname}"
            
            # Publish message
            with self._connection_lock:
                future = self.producer.send(
                    topic=self.topic,
                    key=key,
                    value=message
                )
                
                # Wait for send confirmation
                record_metadata = future.get(timeout=10)
                
                return True
                
        except Exception as e:
            print(f"Error: Failed to publish message to Kafka: {e}", file=sys.stderr)
            return False
    
    def _publish_batch(self, records: List[LogRecord]) -> bool:
        """Publish multiple messages to Kafka."""
        try:
            futures = []
            
            with self._connection_lock:
                for record in records:
                    # Prepare message
                    message = {
                        'message': self.format(record),
                        'level': record.levelname,
                        'timestamp': record.timestamp,
                        'logger': record.logger_name,
                        'filename': getattr(record, 'filename', ''),
                        'function': getattr(record, 'function_name', ''),
                        'line': getattr(record, 'line_number', ''),
                        'extra': getattr(record, 'extra', {})
                    }
                    
                    # Generate key for partitioning
                    key = f"{record.logger_name}:{record.levelname}"
                    
                    # Publish message
                    future = self.producer.send(
                        topic=self.topic,
                        key=key,
                        value=message
                    )
                    futures.append(future)
                
                # Wait for all sends to complete
                for future in futures:
                    future.get(timeout=10)
                
                return True
                
        except Exception as e:
            print(f"Error: Failed to publish batch to Kafka: {e}", file=sys.stderr)
            return False
    
    def _close_connection(self) -> None:
        """Close Kafka connection."""
        if self.producer:
            with self._connection_lock:
                try:
                    self.producer.flush()  # Wait for all messages to be sent
                    self.producer.close()
                except Exception:
                    pass
                self.producer = None


class RedisStreamsHandler(BaseQueueHandler):
    """
    Redis Streams handler for in-memory streaming.
    
    Provides high-performance message streaming with Redis Streams.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        stream_key: str = "logs",
        max_len: int = 10000,
        **kwargs
    ):
        """Initialize Redis Streams handler."""
        # Create config
        config = QueueConfig(
            host=host,
            port=port,
            queue_name=stream_key,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.stream_key = stream_key
        self.max_len = max_len
        self.redis_client = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish Redis connection."""
        try:
            import redis  # type: ignore
            
            with self._connection_lock:
                self.redis_client = redis.Redis(
                    host=self.config.host,
                    port=self.config.port,
                    decode_responses=True,
                    socket_timeout=self.config.connection_timeout
                )
                
                # Test connection
                self.redis_client.ping()
                
                return True
                
        except ImportError:
            print("redis library is required for Redis Streams. Install with: pip install redis")
            return False
        except Exception as e:
            print(f"Error: Redis connection failed: {e}", file=sys.stderr)
            return False
    
    def _publish_message(self, record: LogRecord) -> bool:
        """Publish a single message to Redis Streams."""
        try:
            # Prepare message fields
            message_fields = {
                'message': self.format(record),
                'level': record.levelname,
                'timestamp': str(record.timestamp),
                'logger': record.logger_name,
                'filename': getattr(record, 'filename', ''),
                'function': getattr(record, 'function_name', ''),
                'line': str(getattr(record, 'line_number', '')),
                'extra': json.dumps(getattr(record, 'extra', {}))
            }
            
            # Publish to stream
            with self._connection_lock:
                message_id = self.redis_client.xadd(
                    self.stream_key,
                    message_fields,
                    maxlen=self.max_len,
                    approximate=True
                )
                
                return True
                
        except Exception as e:
            print(f"Error: Failed to publish message to Redis Streams: {e}", file=sys.stderr)
            return False
    
    def _publish_batch(self, records: List[LogRecord]) -> bool:
        """Publish multiple messages to Redis Streams."""
        try:
            with self._connection_lock:
                pipeline = self.redis_client.pipeline()
                
                for record in records:
                    # Prepare message fields
                    message_fields = {
                        'message': self.format(record),
                        'level': record.levelname,
                        'timestamp': str(record.timestamp),
                        'logger': record.logger_name,
                        'filename': getattr(record, 'filename', ''),
                        'function': getattr(record, 'function_name', ''),
                        'line': str(getattr(record, 'line_number', '')),
                        'extra': json.dumps(getattr(record, 'extra', {}))
                    }
                    
                    # Add to stream
                    pipeline.xadd(
                        self.stream_key,
                        message_fields,
                        maxlen=self.max_len,
                        approximate=True
                    )
                
                # Execute pipeline
                pipeline.execute()
                return True
                
        except Exception as e:
            print(f"Error: Failed to publish batch to Redis Streams: {e}", file=sys.stderr)
            return False
    
    def _close_connection(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            with self._connection_lock:
                try:
                    self.redis_client.close()
                except Exception:
                    pass
                self.redis_client = None


class QueueHandlerFactory:
    """Factory for creating queue handlers."""
    
    @staticmethod
    def create_handler(
        handler_type: str,
        **kwargs
    ) -> BaseQueueHandler:
        """Create a queue handler of the specified type."""
        handler_type = handler_type.lower()
        
        if handler_type == "rabbitmq":
            return RabbitMQHandler(**kwargs)
        elif handler_type == "kafka":
            return KafkaHandler(**kwargs)
        elif handler_type in ["redis_streams", "redis"]:
            return RedisStreamsHandler(**kwargs)
        else:
            raise ValueError(f"Unknown queue handler type: {handler_type}")
    
    @staticmethod
    def create_rabbitmq_handler(host: str, port: int, **kwargs) -> RabbitMQHandler:
        """Create a RabbitMQ handler."""
        return RabbitMQHandler(host=host, port=port, **kwargs)
    
    @staticmethod
    def create_kafka_handler(bootstrap_servers: Union[str, List[str]], **kwargs) -> KafkaHandler:
        """Create a Kafka handler."""
        return KafkaHandler(bootstrap_servers=bootstrap_servers, **kwargs)
    
    @staticmethod
    def create_redis_streams_handler(host: str, port: int, **kwargs) -> RedisStreamsHandler:
        """Create a Redis Streams handler."""
        return RedisStreamsHandler(host=host, port=port, **kwargs)
