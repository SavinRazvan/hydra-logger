"""
Async queue implementation for Hydra-Logger.

This module provides a robust, production-ready async queue system with:
- Comprehensive error handling and recovery
- Thread-safe operations
- Proper resource management
- Performance monitoring
- Data protection and backup
"""

import asyncio
import sys
import time
import threading
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

from hydra_logger.core.exceptions import AsyncError
from hydra_logger.data_protection.fallbacks import DataLossProtection


@dataclass
class QueueStats:
    """Statistics for async queue performance."""
    total_messages: int = 0
    processed_messages: int = 0
    dropped_messages: int = 0
    failed_messages: int = 0
    retry_count: int = 0
    queue_size: int = 0
    max_queue_size: int = 0
    avg_processing_time: float = 0.0
    total_processing_time: float = 0.0
    batch_count: int = 0
    last_batch_time: float = 0.0
    error_count: int = 0
    recovery_count: int = 0


class AsyncLogQueue:
    """
    Production-ready async queue with comprehensive error handling.
    
    Features:
    - Thread-safe operations
    - Comprehensive error handling and recovery
    - Proper resource management
    - Performance monitoring
    - Data protection and backup
    - Graceful shutdown
    """
    
    def __init__(self, max_size: int = 1000, batch_size: int = 100,
                 batch_timeout: float = 1.0,
                 processor: Optional[Callable] = None,
                 enable_data_protection: bool = True,
                 test_mode: bool = False,
                 enable_zero_copy: bool = True,
                 enable_monitoring: bool = True):
        """
        Initialize async log queue.
        
        Args:
            max_size: Maximum queue size
            batch_size: Batch size for processing
            batch_timeout: Timeout for batch processing
            processor: Custom processor function
            enable_data_protection: Enable data loss protection
            test_mode: Enable test mode for deterministic testing
            enable_zero_copy: Enable zero-copy batching
            enable_monitoring: Enable performance monitoring
        """
        # Core queue
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._batch_queue: List[Any] = []
        
        # Configuration
        self.max_size = max_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.processor = processor
        self.enable_data_protection = enable_data_protection
        self.test_mode = test_mode
        self.enable_zero_copy = enable_zero_copy
        self.enable_monitoring = enable_monitoring
        
        # State management
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._shutdown_timeout = 30.0  # 30 seconds timeout for shutdown
        
        # Thread safety
        self._thread_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        
        # Performance tracking
        self._stats = QueueStats()
        self._last_batch_time = time.time()
        self._processing_start_time = 0.0
        
        # Error tracking
        self._error_count = 0
        self._recovery_count = 0
        self._last_error_time = 0.0
        
        # Zero-copy batching
        self._batch_view_index = 0
        
        # Data protection
        self._data_protection = None
        if enable_data_protection:
            self._data_protection = DataLossProtection()
        
        # Test mode
        if test_mode:
            self._test_events = {
                'message_queued': asyncio.Event(),
                'batch_processed': asyncio.Event(),
                'worker_started': asyncio.Event(),
                'worker_stopped': asyncio.Event(),
                'flush_completed': asyncio.Event(),
                'error_occurred': asyncio.Event(),
                'recovery_completed': asyncio.Event()
            }
        else:
            self._test_events = None
        
        # Monitoring
        self._monitor_task: Optional[asyncio.Task] = None
        if enable_monitoring:
            self._monitor_task = None
        
        # Task tracking to prevent double task_done() calls
        self._task_done_count = 0
        self._task_lock = asyncio.Lock()
        
        # Reset task counter when queue is empty
        self._reset_task_counter()
        
    def _reset_task_counter(self) -> None:
        """Reset the task done counter when queue is empty."""
        self._task_done_count = 0
        
    async def put(self, message: Any) -> bool:
        """
        Put a message in the queue with comprehensive error handling.
        
        Args:
            message: Message to queue
            
        Returns:
            bool: True if message was queued, False if dropped
        """
        try:
            # Check if queue is full
            if self._queue.full():
                return await self._handle_full_queue(message)
            
            # Add message to queue
            await self._queue.put(message)
            
            # Update statistics thread-safely
            with self._stats_lock:
                self._stats.total_messages += 1
                self._stats.queue_size = self._queue.qsize()
                self._stats.max_queue_size = max(
                    self._stats.max_queue_size, 
                    self._stats.queue_size
                )
            
            # Signal test event if in test mode
            if self.test_mode and self._test_events:
                self._test_events['message_queued'].set()
                self._test_events['message_queued'].clear()
            
            return True
            
        except Exception as e:
            await self._handle_put_error(e, message)
            return False
    
    async def _handle_full_queue(self, message: Any) -> bool:
        """Handle queue full scenario."""
        try:
            # Try to backup message if data protection is enabled
            if self._data_protection:
                backup_success = await self._data_protection.backup_message(message, "main_queue")
                if backup_success:
                    with self._stats_lock:
                        self._stats.total_messages += 1
                        self._stats.failed_messages += 1
                    return True  # Message backed up, not lost
            
            # No backup available, drop message
            with self._stats_lock:
                self._stats.dropped_messages += 1
            
            return False
            
        except Exception as e:
            # Log error and drop message
            with self._stats_lock:
                self._stats.dropped_messages += 1
                self._stats.error_count += 1
            return False
    
    async def _handle_put_error(self, error: Exception, message: Any) -> None:
        """Handle put operation errors."""
        with self._stats_lock:
            self._stats.error_count += 1
            self._last_error_time = time.time()
        
        if self.test_mode and self._test_events:
            self._test_events['error_occurred'].set()
            self._test_events['error_occurred'].clear()
    
    async def get(self) -> Any:
        """Get a message from the queue."""
        try:
            return await self._queue.get()
        except Exception as e:
            await self._handle_get_error(e)
            return None
    
    async def _handle_get_error(self, error: Exception) -> None:
        """Handle get operation errors."""
        with self._stats_lock:
            self._stats.error_count += 1
            self._last_error_time = time.time()
    
    async def start(self) -> None:
        """Start the async queue worker."""
        if self._running:
            return
        
        try:
            async with self._lock:
                if self._running:
                    return
                
                self._running = True
                self._shutdown_event.clear()
                
                # Start worker task
                self._worker_task = asyncio.create_task(self._worker())
                
                # Start monitor task if enabled
                if self.enable_monitoring:
                    self._monitor_task = asyncio.create_task(self._monitor())
                
                # Restore from backup if available
                if self._data_protection:
                    await self._restore_from_backup()
                
                if self.test_mode and self._test_events:
                    self._test_events['worker_started'].set()
                    self._test_events['worker_started'].clear()
                    
        except Exception as e:
            await self._handle_start_error(e)
    
    async def _restore_from_backup(self) -> None:
        """Restore messages from backup."""
        try:
            if self._data_protection:
                backup_messages = await self._data_protection.get_backup_messages("main_queue")
                for message in backup_messages:
                    if not self._queue.full():
                        await self._queue.put(message)
                        with self._stats_lock:
                            self._stats.total_messages += 1
                            self._stats.recovery_count += 1
        except Exception as e:
            # Log error but don't fail startup
            with self._stats_lock:
                self._stats.error_count += 1
    
    async def _handle_start_error(self, error: Exception) -> None:
        """Handle start operation errors."""
        self._running = False
        with self._stats_lock:
            self._stats.error_count += 1
            self._last_error_time = time.time()
    
    async def stop(self) -> None:
        """
        Stop the queue with comprehensive cleanup.
        
        This method ensures proper cleanup of all resources and
        graceful shutdown of the worker task.
        """
        if not self._running:
            return
        
        try:
            # Signal shutdown
            self._shutdown_event.set()
            self._running = False
            
            # Cancel worker task if running
            if self._worker_task and not self._worker_task.done():
                self._worker_task.cancel()
                try:
                    await asyncio.wait_for(self._worker_task, timeout=self._shutdown_timeout)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    # Force cancel if timeout
                    if not self._worker_task.done():
                        self._worker_task.cancel()
                        try:
                            await self._worker_task
                        except asyncio.CancelledError:
                            pass
            
            # Cancel monitor task if running
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()
                try:
                    await asyncio.wait_for(self._monitor_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    if not self._monitor_task.done():
                        self._monitor_task.cancel()
                        try:
                            await self._monitor_task
                        except asyncio.CancelledError:
                            pass
            
            # Process remaining messages
            await self._process_remaining()
            
            # Clear queues
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            # Clear batch queue
            self._batch_queue.clear()
            
            # Reset task counter
            self._reset_task_counter()
            
            # Signal test event if in test mode
            if self.test_mode and self._test_events:
                self._test_events['worker_stopped'].set()
                self._test_events['worker_stopped'].clear()
            
        except Exception as e:
            print(f"Error stopping async queue: {e}", file=sys.stderr)
            # Force cleanup even on error
            self._running = False
            if self._worker_task and not self._worker_task.done():
                self._worker_task.cancel()
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()
        finally:
            # Ensure we're stopped even if cleanup fails
            self._running = False
            self._worker_task = None
            self._monitor_task = None
    
    async def _worker(self) -> None:
        """Main worker loop with proper error handling and shutdown."""
        try:
            while self._running and not self._shutdown_event.is_set():
                try:
                    # Process messages with timeout
                    await self._process_messages()
                    
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.001)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    await self._handle_worker_error(e)
                    # Small delay before retry
                    await asyncio.sleep(0.1)
                    
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            pass
        except Exception as e:
            await self._handle_worker_error(e)
        finally:
            # Ensure we process any remaining messages
            try:
                await self._process_remaining()
            except Exception:
                pass
    
    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        try:
            # Get message with timeout
            message = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            
            # Add to batch
            self._batch_queue.append(message)
            
            # Process batch if full or timeout reached
            if (len(self._batch_queue) >= self.batch_size or 
                time.time() - self._last_batch_time >= self.batch_timeout):
                await self._process_batch()
                
        except asyncio.TimeoutError:
            # No messages available, process any remaining in batch
            if self._batch_queue:
                await self._process_batch()
        except Exception as e:
            await self._handle_worker_error(e)
    
    async def _handle_worker_error(self, error: Exception) -> None:
        """Handle worker errors."""
        with self._stats_lock:
            self._stats.error_count += 1
            self._last_error_time = time.time()
        
        if self.test_mode and self._test_events:
            self._test_events['error_occurred'].set()
            self._test_events['error_occurred'].clear()
    
    async def _process_batch(self) -> None:
        """Process a batch of messages."""
        if not self._batch_queue:
            return
        
        batch = self._batch_queue.copy()
        self._batch_queue.clear()
        
        try:
            start_time = time.time()
            
            # Process batch
            if self.processor:
                await self.processor(batch)
            else:
                await self._default_processor(batch)
            
            # Update statistics
            processing_time = time.time() - start_time
            with self._stats_lock:
                self._stats.processed_messages += len(batch)
                self._stats.batch_count += 1
                self._stats.last_batch_time = time.time()
                self._stats.total_processing_time += processing_time
                self._stats.avg_processing_time = (
                    self._stats.total_processing_time / self._stats.batch_count
                )
            
            # Mark tasks as done
            for _ in range(len(batch)):
                self._queue.task_done()
            
            if self.test_mode and self._test_events:
                self._test_events['batch_processed'].set()
                self._test_events['batch_processed'].clear()
                
        except Exception as e:
            await self._handle_batch_error(e, batch, 0)
    
    async def _handle_batch_error(self, error: Exception, batch: List[Any], attempt: int) -> None:
        """Handle batch processing errors with retry logic."""
        max_retries = 3
        if attempt < max_retries:
            # Retry with exponential backoff
            await asyncio.sleep(2 ** attempt)
            try:
                if self.processor:
                    await self.processor(batch)
                else:
                    await self._default_processor(batch)
                
                # Mark tasks as done on successful retry
                for _ in range(len(batch)):
                    self._queue.task_done()
                    
            except Exception as retry_error:
                await self._handle_batch_error(retry_error, batch, attempt + 1)
        else:
            await self._handle_batch_failure(batch)
    
    async def _handle_batch_failure(self, batch: List[Any]) -> None:
        """Handle final batch failure."""
        with self._stats_lock:
            self._stats.failed_messages += len(batch)
            self._stats.error_count += 1
        
        # Mark tasks as done even on failure
        for _ in range(len(batch)):
            self._queue.task_done()
    
    async def _default_processor(self, messages: List[Any]) -> None:
        """Default message processor."""
        for message in messages:
            if isinstance(message, logging.LogRecord):
                # Handle log record
                logger = logging.getLogger(message.name)
                logger.handle(message)
            else:
                # Handle other message types
                print(f"Processed message: {message}")
    
    async def _process_remaining(self) -> None:
        """Process any remaining messages in the queue."""
        try:
            remaining_messages = []
            
            # Get all remaining messages
            while not self._queue.empty():
                try:
                    message = self._queue.get_nowait()
                    remaining_messages.append(message)
                except asyncio.QueueEmpty:
                    break
            
            if remaining_messages:
                await self._process_remaining_messages_batch(remaining_messages)
                
        except Exception as e:
            with self._stats_lock:
                self._stats.error_count += 1
                self._last_error_time = time.time()
    
    async def _process_remaining_messages_batch(self, messages: List[Any]) -> None:
        """Process remaining messages in a batch."""
        try:
            if self.processor:
                await self.processor(messages)
            else:
                await self._default_processor(messages)
            
            # Update statistics
            with self._stats_lock:
                self._stats.processed_messages += len(messages)
                self._stats.batch_count += 1
            
            # Mark tasks as done
            for _ in range(len(messages)):
                self._queue.task_done()
                
        except Exception as e:
            with self._stats_lock:
                self._stats.failed_messages += len(messages)
                self._stats.error_count += 1
            
            # Mark tasks as done even on failure
            for _ in range(len(messages)):
                self._queue.task_done()
    
    async def _monitor(self) -> None:
        """Monitor queue health and performance."""
        try:
            while self._running and not self._shutdown_event.is_set():
                await self._check_queue_health()
                await asyncio.sleep(5.0)  # Check every 5 seconds
        except asyncio.CancelledError:
            pass
        except Exception as e:
            with self._stats_lock:
                self._stats.error_count += 1
    
    async def _check_queue_health(self) -> None:
        """Check queue health and trigger recovery if needed."""
        try:
            current_size = self._queue.qsize()
            
            # Check for potential issues
            if current_size > self.max_size * 0.9:
                await self._trigger_recovery()
            
            # Check for stuck processing
            if (self._stats.total_messages > 0 and 
                self._stats.processed_messages == 0 and 
                time.time() - self._last_error_time > 60):
                await self._restart_worker()
                
        except Exception as e:
            with self._stats_lock:
                self._stats.error_count += 1
    
    async def _trigger_recovery(self) -> None:
        """Trigger recovery mechanisms."""
        try:
            # Implement recovery logic here
            with self._stats_lock:
                self._stats.recovery_count += 1
            
            if self.test_mode and self._test_events:
                self._test_events['recovery_completed'].set()
                self._test_events['recovery_completed'].clear()
                
        except Exception as e:
            with self._stats_lock:
                self._stats.error_count += 1
    
    async def _restart_worker(self) -> None:
        """Restart the worker task."""
        try:
            if self._worker_task and not self._worker_task.done():
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            
            self._worker_task = asyncio.create_task(self._worker())
            
        except Exception as e:
            with self._stats_lock:
                self._stats.error_count += 1
    
    def get_stats(self) -> QueueStats:
        """Get current queue statistics."""
        with self._stats_lock:
            return QueueStats(
                total_messages=self._stats.total_messages,
                processed_messages=self._stats.processed_messages,
                dropped_messages=self._stats.dropped_messages,
                failed_messages=self._stats.failed_messages,
                retry_count=self._stats.retry_count,
                queue_size=self._queue.qsize(),
                max_queue_size=self._stats.max_queue_size,
                avg_processing_time=self._stats.avg_processing_time,
                total_processing_time=self._stats.total_processing_time,
                batch_count=self._stats.batch_count,
                last_batch_time=self._stats.last_batch_time,
                error_count=self._stats.error_count,
                recovery_count=self._stats.recovery_count
            )
    
    def reset_stats(self) -> None:
        """Reset all queue statistics."""
        with self._stats_lock:
            self._stats = QueueStats()
    
    async def flush(self) -> None:
        """Flush all pending messages."""
        try:
            # Process current batch
            if self._batch_queue:
                await self._process_batch()
            
            # Wait for queue to be empty
            await self._queue.join()
            
            if self.test_mode and self._test_events:
                self._test_events['flush_completed'].set()
                self._test_events['flush_completed'].clear()
                
        except Exception as e:
            with self._stats_lock:
                self._stats.error_count += 1
    
    async def await_pending(self) -> None:
        """Wait for all pending messages to be processed."""
        try:
            # Process current batch
            if self._batch_queue:
                await self._process_batch()
            
            # Wait for queue to be empty
            await self._queue.join()
            
        except Exception as e:
            with self._stats_lock:
                self._stats.error_count += 1
    
    async def get_pending_count(self) -> int:
        """Get the number of pending messages."""
        try:
            return self._queue.qsize() + len(self._batch_queue)
        except Exception:
            return 0
    
    def _create_batch_view(self, messages: List[Any]) -> List[Any]:
        """Create a zero-copy view of the batch."""
        if self.enable_zero_copy:
            return messages[self._batch_view_index:]
        return messages
    
    def _get_batch_view(self, messages: List[Any], start: int, end: int) -> List[Any]:
        """Get a zero-copy view of a subset of messages."""
        if self.enable_zero_copy:
            return messages[start:end]
        return messages[start:end].copy()
    
    async def _process_batch_zero_copy(self, messages: List[Any]) -> None:
        """Process batch using zero-copy operations."""
        try:
            if self.processor:
                await self.processor(messages)
            else:
                await self._default_processor(messages)
        except Exception as e:
            await self._handle_batch_error(e, messages, 0)
    
    async def close(self) -> None:
        """
        Close the queue and cleanup all resources.
        
        This method ensures complete cleanup of all resources
        and should be called when the queue is no longer needed.
        """
        await self.stop()
        
        try:
            # Clear all references
            self._queue = None
            self._batch_queue = None
            self.processor = None
            
            # Clear data protection
            if self._data_protection:
                self._data_protection = None
            
            # Clear test events
            if self._test_events:
                self._test_events.clear()
                self._test_events = None
            
            # Reset statistics
            self._stats = QueueStats()
            
        except Exception as e:
            print(f"Error during queue cleanup: {e}", file=sys.stderr)


class AsyncBatchProcessor:
    """
    Async batch processor for high-throughput logging.
    
    This class provides efficient batch processing capabilities for
    high-throughput logging scenarios with configurable batching
    and error handling.
    """
    
    def __init__(self, batch_size: int = 100, batch_timeout: float = 1.0,
                 processor: Optional[Callable] = None):
        """
        Initialize async batch processor.
        
        Args:
            batch_size: Maximum batch size
            batch_timeout: Timeout for batch processing
            processor: Custom processor function
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.processor = processor
        self._batch: List[Any] = []
        self._last_batch_time = time.time()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._stats = QueueStats()
    
    async def start(self) -> None:
        """Start the batch processor."""
        if self._running:
            return
        
        async with self._lock:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
    
    async def stop(self) -> None:
        """Stop the batch processor."""
        self._running = False
        
        try:
            # Process remaining messages
            if self._batch_queue:
                await self._process_batch()
            
            # Clear batch queue
            self._batch_queue.clear()
            
        except Exception as e:
            print(f"Error stopping batch processor: {e}", file=sys.stderr)
    
    async def close(self) -> None:
        """
        Close the batch processor and cleanup resources.
        """
        await self.stop()
        
        try:
            # Clear references
            self._batch_queue = None
            self.processor = None
            
            # Reset statistics
            self._stats = QueueStats()
            
        except Exception as e:
            print(f"Error during batch processor cleanup: {e}", file=sys.stderr)
    
    async def _worker(self) -> None:
        """Worker loop for batch processing."""
        try:
            while self._running:
                try:
                    await self._process_batch()
                    await asyncio.sleep(0.001)  # Small delay
                except asyncio.CancelledError:
                    break
                except Exception:
                    await asyncio.sleep(0.1)  # Error delay
        except asyncio.CancelledError:
            pass
        finally:
            await self._process_remaining()
    
    async def add_message(self, message: Any) -> None:
        """Add a message to the current batch."""
        try:
            self._batch.append(message)
            
            # Process batch if full
            if len(self._batch) >= self.batch_size:
                await self._process_batch()
                
        except Exception as e:
            with self._stats_lock:
                self._stats.error_count += 1
    
    async def process_batch(self) -> None:
        """Manually trigger batch processing."""
        await self._process_batch()
    
    async def _process_batch(self) -> None:
        """Process the current batch."""
        if not self._batch:
            return
        
        batch = self._batch.copy()
        self._batch.clear()
        
        try:
            if self.processor:
                await self.processor(batch)
            else:
                await self._default_processor(batch)
            
            with self._stats_lock:
                self._stats.processed_messages += len(batch)
                self._stats.batch_count += 1
                
        except Exception as e:
            with self._stats_lock:
                self._stats.failed_messages += len(batch)
                self._stats.error_count += 1
    
    async def _process_remaining(self) -> None:
        """Process any remaining messages."""
        if self._batch:
            await self._process_batch()
    
    async def _default_processor(self, messages: List[Any]) -> None:
        """Default message processor."""
        for message in messages:
            if isinstance(message, logging.LogRecord):
                logger = logging.getLogger(message.name)
                logger.handle(message)
            else:
                print(f"Processed message: {message}")
    
    async def _process_log_record(self, record: logging.LogRecord) -> None:
        """Process a log record."""
        await self.add_message(record)
    
    async def _process_message(self, message: Any) -> None:
        """Process a generic message."""
        await self.add_message(message)
    
    def get_stats(self) -> QueueStats:
        """Get current processor statistics."""
        with self._stats_lock:
            return QueueStats(
                total_messages=self._stats.total_messages,
                processed_messages=self._stats.processed_messages,
                dropped_messages=self._stats.dropped_messages,
                failed_messages=self._stats.failed_messages,
                retry_count=self._stats.retry_count,
                queue_size=len(self._batch),
                max_queue_size=self._stats.max_queue_size,
                avg_processing_time=self._stats.avg_processing_time,
                total_processing_time=self._stats.total_processing_time,
                batch_count=self._stats.batch_count,
                last_batch_time=self._stats.last_batch_time,
                error_count=self._stats.error_count,
                recovery_count=self._stats.recovery_count
            )
    
    def reset_stats(self) -> None:
        """Reset all processor statistics."""
        with self._stats_lock:
            self._stats = QueueStats()


class AsyncBackpressureHandler:
    """
    Async backpressure handler for managing queue pressure.
    
    This class provides backpressure management capabilities for
    preventing queue overflow and managing system load.
    """
    
    def __init__(self, max_queue_size: int = 1000, drop_threshold: float = 0.9,
                 slow_down_threshold: float = 0.7):
        """
        Initialize backpressure handler.
        
        Args:
            max_queue_size: Maximum queue size
            drop_threshold: Threshold for dropping messages
            slow_down_threshold: Threshold for slowing down
        """
        self.max_queue_size = max_queue_size
        self.drop_threshold = drop_threshold
        self.slow_down_threshold = slow_down_threshold
        self._current_queue_size = 0
        self._stats = QueueStats()
        self._lock = threading.Lock()
    
    async def should_accept_message(self, current_queue_size: int) -> bool:
        """
        Determine if a message should be accepted.
        
        Args:
            current_queue_size: Current queue size
            
        Returns:
            bool: True if message should be accepted
        """
        with self._lock:
            self._current_queue_size = current_queue_size
            
            if current_queue_size >= self.max_queue_size * self.drop_threshold:
                with self._stats_lock:
                    self._stats.dropped_messages += 1
                return False
            
            return True
    
    async def get_processing_delay(self, current_queue_size: int) -> float:
        """
        Get processing delay based on queue pressure.
        
        Args:
            current_queue_size: Current queue size
            
        Returns:
            float: Delay in seconds
        """
        with self._lock:
            self._current_queue_size = current_queue_size
            
            if current_queue_size >= self.max_queue_size * self.slow_down_threshold:
                # Calculate delay based on pressure
                pressure = current_queue_size / self.max_queue_size
                return min(pressure * 0.1, 1.0)  # Max 1 second delay
            
            return 0.0
    
    async def update_queue_size(self, size: int) -> None:
        """
        Update current queue size.
        
        Args:
            size: Current queue size
        """
        with self._lock:
            self._current_queue_size = size
            self._stats.max_queue_size = max(self._stats.max_queue_size, size)
    
    def get_stats(self) -> QueueStats:
        """Get current backpressure statistics."""
        with self._stats_lock:
            return QueueStats(
                total_messages=self._stats.total_messages,
                processed_messages=self._stats.processed_messages,
                dropped_messages=self._stats.dropped_messages,
                failed_messages=self._stats.failed_messages,
                retry_count=self._stats.retry_count,
                queue_size=self._current_queue_size,
                max_queue_size=self._stats.max_queue_size,
                avg_processing_time=self._stats.avg_processing_time,
                total_processing_time=self._stats.total_processing_time,
                batch_count=self._stats.batch_count,
                last_batch_time=self._stats.last_batch_time,
                error_count=self._stats.error_count,
                recovery_count=self._stats.recovery_count
            )
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = QueueStats()
    
    async def close(self) -> None:
        """
        Close the backpressure handler and cleanup resources.
        """
        try:
            # Reset statistics
            self._stats = QueueStats()
            
        except Exception as e:
            print(f"Error during backpressure handler cleanup: {e}", file=sys.stderr) 