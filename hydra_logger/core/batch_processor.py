"""
High-Performance Batch Processing for Hydra-Logger

This module provides advanced batch processing capabilities for handling high-volume
logging scenarios with maximum efficiency. It includes bulk operations, streaming
loggers, and optimized memory management for enterprise-scale logging.

ARCHITECTURE:
- BatchProcessor: High-performance batch processor with configurable batch sizes
- BulkLogger: Bulk logger for processing multiple messages efficiently
- StreamingLogger: Continuous high-throughput streaming logger with backpressure
- Object Pooling: Memory-efficient LogRecord pooling for batch operations
- Thread Safety: All operations are thread-safe with proper locking

FEATURES:
- Configurable batch sizes and flush intervals
- Automatic buffer management and flushing
- Memory-efficient object pooling
- Backpressure handling for high-volume scenarios
- Thread-safe operations
- Performance statistics and monitoring
- Zero-allocation patterns where possible

PERFORMANCE OPTIMIZATIONS:
- Pre-allocated LogRecord pools
- Bulk I/O operations
- Minimal memory allocations
- Efficient buffer management
- Optimized string formatting

USAGE EXAMPLES:

Batch Processing:
    from hydra_logger.core.batch_processor import BatchProcessor
    
    processor = BatchProcessor(batch_size=1000, flush_interval=0.01)
    processor.add_message(LogLevel.INFO, "Batch message")
    processor.flush()

Bulk Logging:
    from hydra_logger.core.batch_processor import BulkLogger
    
    logger = BulkLogger("BulkLogger", batch_size=500)
    messages = [
        {"level": LogLevel.INFO, "message": "Message 1"},
        {"level": LogLevel.WARNING, "message": "Message 2"}
    ]
    logger.log_bulk(messages)

Streaming Logger:
    from hydra_logger.core.batch_processor import StreamingLogger
    
    streamer = StreamingLogger("StreamLogger", buffer_size=10000)
    success = streamer.stream_message(LogLevel.INFO, "Stream message")
    processed = streamer.process_stream(max_messages=1000)
"""

import time
import sys
from typing import List, Dict, Any, Optional, Callable
from collections import deque
from threading import Lock
from ..types.records import LogRecord
from ..types.levels import LogLevel, LogLevelManager
from ..core.object_pool import get_log_record_pool


class BatchProcessor:
    """
    High-performance batch processor for logging operations.
    
    Features:
    - Bulk message processing
    - Efficient memory usage
    - Configurable batch sizes
    - Automatic flushing
    - Thread-safe operations
    """
    
    def __init__(self, batch_size: int = 1000, flush_interval: float = 0.01):
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._buffer = deque()
        self._last_flush = time.time()
        self._lock = Lock()
        self._record_pool = get_log_record_pool("batch_processor", initial_size=2000, max_size=10000)
        self._stats = {
            'batches_processed': 0,
            'messages_processed': 0,
            'buffer_flushes': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
    
    def add_message(self, level: LogLevel, message: str, **kwargs) -> None:
        """Add a message to the batch buffer."""
        with self._lock:
            # Use standardized LogRecord creation
            from ..types.records import LogRecordFactory
            record = LogRecordFactory.create_with_context(
                level_name=LogLevelManager.get_name(level),
                message=message,
                layer=kwargs.get('layer', 'default'),
                level=level,
                logger_name=kwargs.get('logger_name', 'BatchLogger')
            )
            
            # Add to buffer
            self._buffer.append(record)
            self._stats['messages_processed'] += 1
            
            # Check if we should flush
            if (len(self._buffer) >= self._batch_size or 
                time.time() - self._last_flush >= self._flush_interval):
                self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush the buffer to output."""
        if not self._buffer:
            return
        
        # Process all records in the buffer
        records = list(self._buffer)
        self._buffer.clear()
        
        # Write all records at once
        self._write_batch(records)
        
        # Return records to pool
        for record in records:
            self._record_pool.return_record(record)
        
        self._last_flush = time.time()
        self._stats['batches_processed'] += 1
        self._stats['buffer_flushes'] += 1
    
    def _write_batch(self, records: List[LogRecord]):
        """Write a batch of records efficiently."""
        # Pre-allocate output buffer
        output_lines = []
        
        for record in records:
            # Ultra-fast formatting
            timestamp = int(record.timestamp * 1000)
            line = f"{timestamp} {record.level_name} {record.message}\n"
            output_lines.append(line)
        
        # Write all at once
        sys.stdout.write(''.join(output_lines))
        sys.stdout.flush()
    
    def flush(self):
        """Force flush the buffer."""
        with self._lock:
            self._flush_buffer()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        with self._lock:
            return {
                'batch_size': self._batch_size,
                'flush_interval': self._flush_interval,
                'current_buffer_size': len(self._buffer),
                'batches_processed': self._stats['batches_processed'],
                'messages_processed': self._stats['messages_processed'],
                'buffer_flushes': self._stats['buffer_flushes'],
                'pool_stats': self._record_pool.get_stats()
            }


class BulkLogger:
    """
    Bulk logger that processes multiple messages efficiently.
    
    Features:
    - Bulk message logging
    - Efficient memory usage
    - Configurable batch processing
    - Thread-safe operations
    """
    
    def __init__(self, name: str = "BulkLogger", batch_size: int = 1000):
        self._name = name
        self._batch_processor = BatchProcessor(batch_size=batch_size)
        self._stats = {
            'total_messages': 0,
            'bulk_operations': 0
        }
    
    def log_bulk(self, messages: List[Dict[str, Any]]) -> None:
        """Log multiple messages in a single bulk operation."""
        for msg_data in messages:
            level = msg_data.get('level', LogLevel.INFO)
            message = msg_data.get('message', '')
            kwargs = {k: v for k, v in msg_data.items() if k not in ('level', 'message')}
            kwargs['logger_name'] = self._name
            
            self._batch_processor.add_message(level, message, **kwargs)
            self._stats['total_messages'] += 1
        
        self._stats['bulk_operations'] += 1
    
    def log_many(self, level: LogLevel, messages: List[str], **kwargs) -> None:
        """Log many messages at the same level efficiently."""
        for message in messages:
            self._batch_processor.add_message(level, message, logger_name=self._name, **kwargs)
            self._stats['total_messages'] += 1
        
        self._stats['bulk_operations'] += 1
    
    def flush(self):
        """Flush all pending messages."""
        self._batch_processor.flush()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bulk logging statistics."""
        return {
            'logger_name': self._name,
            'total_messages': self._stats['total_messages'],
            'bulk_operations': self._stats['bulk_operations'],
            'batch_processor': self._batch_processor.get_stats()
        }


class StreamingLogger:
    """
    Streaming logger for continuous high-throughput logging.
    
    Features:
    - Continuous streaming
    - Backpressure handling
    - Memory management
    - Performance monitoring
    """
    
    def __init__(self, name: str = "StreamingLogger", buffer_size: int = 10000):
        self._name = name
        self._buffer_size = buffer_size
        self._buffer = deque(maxlen=buffer_size)
        self._lock = Lock()
        self._record_pool = get_log_record_pool("streaming_logger", initial_size=5000, max_size=20000)
        self._stats = {
            'messages_streamed': 0,
            'buffer_overflows': 0,
            'dropped_messages': 0
        }
    
    def stream_message(self, level: LogLevel, message: str, **kwargs) -> bool:
        """
        Stream a message with backpressure handling.
        
        Returns:
            bool: True if message was queued, False if dropped due to backpressure
        """
        with self._lock:
            if len(self._buffer) >= self._buffer_size:
                # Buffer full, drop message
                self._stats['buffer_overflows'] += 1
                self._stats['dropped_messages'] += 1
                return False
            
            # Use standardized LogRecord creation
            from ..types.records import LogRecordFactory
            record = LogRecordFactory.create_with_context(
                level_name=LogLevelManager.get_name(level),
                message=message,
                layer=kwargs.get('layer', 'default'),
                level=level,
                logger_name=self._name
            )
            
            # Add to buffer
            self._buffer.append(record)
            self._stats['messages_streamed'] += 1
            return True
    
    def process_stream(self, max_messages: int = 1000) -> int:
        """Process messages from the stream."""
        processed = 0
        
        with self._lock:
            while self._buffer and processed < max_messages:
                record = self._buffer.popleft()
                
                # Write record
                timestamp = int(record.timestamp * 1000)
                line = f"{timestamp} {record.level_name} {record.message}\n"
                sys.stdout.write(line)
                
                # Return to pool
                self._record_pool.return_record(record)
                processed += 1
        
        if processed > 0:
            sys.stdout.flush()
        
        return processed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        with self._lock:
            return {
                'logger_name': self._name,
                'buffer_size': self._buffer_size,
                'current_buffer_usage': len(self._buffer),
                'messages_streamed': self._stats['messages_streamed'],
                'buffer_overflows': self._stats['buffer_overflows'],
                'dropped_messages': self._stats['dropped_messages'],
                'pool_stats': self._record_pool.get_stats()
            }
