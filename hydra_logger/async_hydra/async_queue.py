"""
Async queue system for Hydra-Logger.

This module provides an async queue system for buffering and processing
log messages asynchronously. It supports high-throughput logging with
configurable batching and backpressure handling.

Key Features:
- AsyncLogQueue for message buffering
- Configurable batch processing
- Backpressure handling
- Performance monitoring
- Thread-safe operations

Example:
    >>> from hydra_logger.async_queue import AsyncLogQueue
    >>> queue = AsyncLogQueue(max_size=1000, batch_size=100)
    >>> await queue.put(log_record)
    >>> await queue.process_batch()
"""

import asyncio
import logging
import sys
import time
import json
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass
from collections import deque
from pathlib import Path


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


class DataLossProtection:
    """
    Data loss protection mechanisms for async logging.
    
    Provides persistent storage, retry logic, and circuit breaker
    to prevent data loss in async logging scenarios.
    """
    
    def __init__(self, backup_dir: str = ".hydra_backup", max_retries: int = 3):
        """
        Initialize data loss protection.
        
        Args:
            backup_dir (str): Directory for backup files
            max_retries (int): Maximum retry attempts
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.max_retries = max_retries
        self._circuit_open = False
        self._failure_count = 0
        self._last_failure_time = 0
        self._circuit_timeout = 30.0  # 30 seconds
    
    async def backup_message(self, message: Any, queue_name: str = "default") -> bool:
        """
        Backup a message to persistent storage.
        
        Args:
            message (Any): Message to backup
            queue_name (str): Name of the queue
            
        Returns:
            bool: True if backup successful
        """
        try:
            timestamp = time.time()
            backup_file = self.backup_dir / f"{queue_name}_{timestamp}.json"
            
            # Serialize message
            if isinstance(message, logging.LogRecord):
                serialized = {
                    "type": "log_record",
                    "name": message.name,
                    "level": message.levelname,
                    "message": message.getMessage(),
                    "timestamp": timestamp
                }
            else:
                serialized = {
                    "type": "generic",
                    "data": str(message),
                    "timestamp": timestamp
                }
            
            # Write to backup file
            with open(backup_file, 'w') as f:
                json.dump(serialized, f)
            
            return True
            
        except Exception as e:
            print(f"Error backing up message: {e}", file=sys.stderr)
            return False
    
    async def restore_messages(self, queue_name: str = "default") -> List[Any]:
        """
        Restore messages from backup storage.
        
        Args:
            queue_name (str): Name of the queue
            
        Returns:
            List[Any]: Restored messages
        """
        restored = []
        try:
            # Find backup files for this queue
            backup_files = list(self.backup_dir.glob(f"{queue_name}_*.json"))
            
            for backup_file in backup_files:
                try:
                    with open(backup_file, 'r') as f:
                        data = json.load(f)
                    
                    # Reconstruct message
                    if data["type"] == "log_record":
                        record = logging.LogRecord(
                            name=data["name"],
                            level=getattr(logging, data["level"]),
                            pathname="",
                            lineno=0,
                            msg=data["message"],
                            args=(),
                            exc_info=None
                        )
                        restored.append(record)
                    else:
                        restored.append(data["data"])
                    
                    # Remove backup file after successful restore
                    backup_file.unlink()
                    
                except Exception as e:
                    print(f"Error restoring from {backup_file}: {e}", file=sys.stderr)
                    continue
            
        except Exception as e:
            print(f"Error during message restoration: {e}", file=sys.stderr)
        
        return restored
    
    async def should_retry(self, error: Exception) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            error (Exception): The error that occurred
            
        Returns:
            bool: True if should retry
        """
        # Check circuit breaker
        if self._circuit_open:
            if time.time() - self._last_failure_time > self._circuit_timeout:
                self._circuit_open = False
                self._failure_count = 0
            else:
                return False
        
        # Increment failure count
        self._failure_count += 1
        
        # Open circuit if too many failures
        if self._failure_count >= 5:
            self._circuit_open = True
            self._last_failure_time = time.time()
            return False
        
        return True
    
    def get_protection_stats(self) -> Dict[str, Any]:
        """Get data loss protection statistics."""
        return {
            "circuit_open": self._circuit_open,
            "failure_count": self._failure_count,
            "backup_files": len(list(self.backup_dir.glob("*.json")))
        }


class AsyncLogQueue:
    """
    Async queue for buffering and processing log messages.
    
    This class provides a high-performance async queue for log messages
    with configurable batching, backpressure handling, and performance
    monitoring.
    
    Attributes:
        max_size (int): Maximum queue size
        batch_size (int): Batch size for processing
        batch_timeout (float): Timeout for batch processing
        processor (Optional[Callable]): Message processor function
        stats (QueueStats): Queue performance statistics
    """
    
    def __init__(self, max_size: int = 1000, batch_size: int = 100,
                 batch_timeout: float = 1.0,
                 processor: Optional[Callable] = None,
                 enable_data_protection: bool = True):
        """
        Initialize async log queue.
        
        Args:
            max_size (int): Maximum queue size
            batch_size (int): Batch size for processing
            batch_timeout (float): Timeout for batch processing in seconds
            processor (Optional[Callable]): Message processor function
            enable_data_protection (bool): Enable data loss protection
        """
        self.max_size = max_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.processor = processor
        self.enable_data_protection = enable_data_protection
        
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._batch_queue: deque = deque()
        self._lock = asyncio.Lock()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._stats = QueueStats()
        self._last_batch_time = time.time()
        
        # Initialize data loss protection
        if enable_data_protection:
            self._data_protection = DataLossProtection()
        else:
            self._data_protection = None
        
    async def put(self, message: Any) -> bool:
        """
        Put a message in the queue.
        
        Args:
            message (Any): Message to queue
            
        Returns:
            bool: True if message was queued, False if dropped
        """
        try:
            if self._queue.full():
                # Try to backup message if data protection is enabled
                if self._data_protection:
                    backup_success = await self._data_protection.backup_message(message, "main_queue")
                    if backup_success:
                        async with self._lock:
                            self._stats.total_messages += 1
                            self._stats.failed_messages += 1
                        return True  # Message backed up, not lost
                
                # No backup available, drop message
                async with self._lock:
                    self._stats.dropped_messages += 1
                return False
            
            await self._queue.put(message)
            
            async with self._lock:
                self._stats.total_messages += 1
                self._stats.queue_size = self._queue.qsize()
                self._stats.max_queue_size = max(
                    self._stats.max_queue_size, 
                    self._stats.queue_size
                )
            
            return True
            
        except Exception as e:
            print(f"Error putting message in queue: {e}", file=sys.stderr)
            return False
    
    async def get(self) -> Any:
        """
        Get a message from the queue.
        
        Returns:
            Any: Message from queue
            
        Raises:
            asyncio.TimeoutError: If no message available within timeout
        """
        return await asyncio.wait_for(self._queue.get(), timeout=1.0)
    
    async def start(self) -> None:
        """Start the queue worker."""
        if self._running:
            return
            
        async with self._lock:
            if self._running:
                return
                
            # Restore messages from backup if data protection is enabled
            if self._data_protection:
                restored_messages = await self._data_protection.restore_messages("main_queue")
                for message in restored_messages:
                    try:
                        await self._queue.put(message)
                        self._stats.total_messages += 1
                    except asyncio.QueueFull:
                        # If queue is full, backup again
                        await self._data_protection.backup_message(message, "main_queue")
                        self._stats.failed_messages += 1
                
                if restored_messages:
                    print(f"Restored {len(restored_messages)} messages from backup", file=sys.stderr)
                
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
    
    async def stop(self) -> None:
        """Stop the queue worker."""
        if not self._running:
            return
            
        # Set running to False first
        self._running = False
        
        # Cancel worker task immediately
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                # Wait for cancellation with a short timeout
                await asyncio.wait_for(self._worker_task, timeout=0.5)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        
        # Process any remaining messages
        await self._process_remaining()
    
    async def _worker(self) -> None:
        """Background worker for processing queued messages."""
        while self._running:
            try:
                # Use a very short timeout to be responsive
                try:
                    message = await asyncio.wait_for(self._queue.get(), timeout=0.05)
                    
                    # Add to batch
                    self._batch_queue.append(message)
                    
                    # Process immediately if batch is full or queue is empty
                    if (len(self._batch_queue) >= self.batch_size or 
                        self._queue.empty()):
                        await self._process_batch()
                        
                except asyncio.TimeoutError:
                    # Check if we should process due to timeout
                    current_time = time.time()
                    if (self._batch_queue and 
                        current_time - self._last_batch_time >= self.batch_timeout):
                        await self._process_batch()
                        
            except asyncio.CancelledError:
                # Ensure we process any remaining messages before exiting
                if self._batch_queue:
                    await self._process_batch()
                break
            except Exception as e:
                # Only print error if we have a running loop
                try:
                    if asyncio.get_running_loop():
                        print(f"Error in queue worker: {e}", file=sys.stderr)
                except RuntimeError:
                    pass
                # Continue processing even if one message fails
    
    async def _process_batch(self) -> None:
        """Process the current batch of messages."""
        if not self._batch_queue:
            return
            
        start_time = time.time()
        batch = list(self._batch_queue)
        self._batch_queue.clear()
        
        # Process with retry logic
        for attempt in range(3):  # Max 3 retries
            try:
                if self.processor:
                    # Use custom processor (handle both sync and async)
                    if asyncio.iscoroutinefunction(self.processor):
                        await self.processor(batch)
                    else:
                        # Sync processor
                        self.processor(batch)
                else:
                    # Default processing
                    await self._default_processor(batch)
                
                # Success - update statistics
                processing_time = time.time() - start_time
                async with self._lock:
                    self._stats.processed_messages += len(batch)
                    self._stats.batch_count += 1
                    self._stats.total_processing_time += processing_time
                    self._stats.avg_processing_time = (
                        self._stats.total_processing_time / self._stats.batch_count
                    )
                    self._stats.last_batch_time = time.time()
                
                # Mark tasks as done
                for _ in range(len(batch)):
                    self._queue.task_done()
                
                return  # Success, exit retry loop
                
            except Exception as e:
                # Check if we should retry
                if self._data_protection and await self._data_protection.should_retry(e):
                    self._stats.retry_count += 1
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    # Final failure - backup messages if data protection is enabled
                    if self._data_protection:
                        for message in batch:
                            await self._data_protection.backup_message(message, "failed_batch")
                        self._stats.failed_messages += len(batch)
                    
                    print(f"Error processing batch after {attempt + 1} attempts: {e}", file=sys.stderr)
                    break
    
    async def _default_processor(self, messages: List[Any]) -> None:
        """
        Default message processor.
        
        Args:
            messages (List[Any]): List of messages to process
        """
        # Default implementation just prints messages
        for message in messages:
            if isinstance(message, logging.LogRecord):
                print(f"LOG: {message.getMessage()}")
            else:
                print(f"MSG: {message}")
    
    async def _process_remaining(self) -> None:
        """Process any remaining messages in the queue."""
        # Process remaining messages in batch
        remaining = []
        try:
            while not self._queue.empty():
                try:
                    # Use get_nowait() which is synchronous
                    message = self._queue.get_nowait()
                    remaining.append(message)
                except asyncio.QueueEmpty:
                    break
        except Exception as e:
            # Handle any queue-related errors
            print(f"Error processing remaining messages: {e}", file=sys.stderr)
        
        if remaining:
            # Add remaining messages to batch and process
            self._batch_queue.extend(remaining)
            await self._process_batch()
    
    def get_stats(self) -> QueueStats:
        """
        Get current queue statistics.
        
        Returns:
            QueueStats: Current queue statistics
        """
        # Note: This method is not async but accesses async state
        # In a real implementation, you might want to make this async
        # or use a different approach for thread safety
        queue_size = self._queue.qsize()
        return QueueStats(
            total_messages=self._stats.total_messages,
            processed_messages=self._stats.processed_messages,
            dropped_messages=self._stats.dropped_messages,
            queue_size=queue_size,
            max_queue_size=self._stats.max_queue_size,
            avg_processing_time=self._stats.avg_processing_time,
            total_processing_time=self._stats.total_processing_time,
            batch_count=self._stats.batch_count,
            last_batch_time=self._stats.last_batch_time
        )
    
    def reset_stats(self) -> None:
        """Reset queue statistics."""
        self._stats = QueueStats()

    def get_data_protection_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get data loss protection statistics.
        
        Returns:
            Optional[Dict[str, Any]]: Protection statistics or None if disabled
        """
        if self._data_protection:
            return self._data_protection.get_protection_stats()
        return None


class AsyncBatchProcessor:
    """
    Async batch processor for high-throughput logging.
    
    This class provides efficient batch processing of log messages
    with configurable batching strategies and performance optimization.
    
    Attributes:
        batch_size (int): Maximum batch size
        batch_timeout (float): Maximum time to wait for batch completion
        processor (Callable): Batch processing function
        stats (QueueStats): Processing statistics
    """
    
    def __init__(self, batch_size: int = 100, batch_timeout: float = 1.0,
                 processor: Optional[Callable] = None):
        """
        Initialize async batch processor.
        
        Args:
            batch_size (int): Maximum batch size
            batch_timeout (float): Maximum time to wait for batch completion
            processor (Optional[Callable]): Batch processing function
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.processor = processor
        
        self._current_batch: List[Any] = []
        self._lock = asyncio.Lock()
        self._stats = QueueStats()
        self._last_batch_time = time.time()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the batch processor worker."""
        if self._running:
            return
            
        async with self._lock:
            if self._running:
                return
                
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
    
    async def stop(self) -> None:
        """Stop the batch processor worker."""
        if not self._running:
            return
            
        # Set running to False first
        self._running = False
        
        # Cancel worker task immediately
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                # Wait for cancellation with a short timeout
                await asyncio.wait_for(self._worker_task, timeout=0.5)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        
        # Process any remaining messages
        await self._process_remaining()
    
    async def _worker(self) -> None:
        """Background worker for automatic batch processing."""
        while self._running:
            try:
                # Check if we should process due to timeout
                current_time = time.time()
                if (self._current_batch and 
                    current_time - self._last_batch_time >= self.batch_timeout):
                    await self._process_batch()
                
                # Sleep for a short interval to avoid busy waiting
                await asyncio.sleep(0.05)
                
            except asyncio.CancelledError:
                # Ensure we process any remaining messages before exiting
                if self._current_batch:
                    await self._process_batch()
                break
            except Exception as e:
                # Only print error if we have a running loop
                try:
                    if asyncio.get_running_loop():
                        print(f"Error in batch processor worker: {e}", file=sys.stderr)
                except RuntimeError:
                    pass
                # Continue processing even if one batch fails
    
    async def add_message(self, message: Any) -> None:
        """
        Add a message to the current batch.
        
        Args:
            message (Any): Message to add to batch
        """
        async with self._lock:
            self._current_batch.append(message)
            
            # Update statistics
            self._stats.total_messages += 1
            
            # Check if batch is full
            if len(self._current_batch) >= self.batch_size:
                await self._process_batch()
    
    async def process_batch(self) -> None:
        """Process the current batch immediately."""
        async with self._lock:
            await self._process_batch()
    
    async def _process_batch(self) -> None:
        """Process the current batch of messages."""
        if not self._current_batch:
            return
            
        start_time = time.time()
        batch = list(self._current_batch)
        self._current_batch.clear()
        
        try:
            if self.processor:
                # Use custom processor (handle both sync and async)
                if asyncio.iscoroutinefunction(self.processor):
                    await self.processor(batch)
                else:
                    # Sync processor
                    self.processor(batch)
            else:
                # Default processing
                await self._default_processor(batch)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._stats.processed_messages += len(batch)
            self._stats.batch_count += 1
            self._stats.total_processing_time += processing_time
            self._stats.avg_processing_time = (
                self._stats.total_processing_time / self._stats.batch_count
            )
            self._stats.last_batch_time = time.time()
            
        except Exception as e:
            print(f"Error processing batch: {e}", file=sys.stderr)
    
    async def _process_remaining(self) -> None:
        """Process any remaining messages in the batch."""
        if self._current_batch:
            await self._process_batch()
    
    async def _default_processor(self, messages: List[Any]) -> None:
        """
        Default batch processor.
        
        Args:
            messages (List[Any]): List of messages to process
        """
        # Default implementation processes messages in parallel
        tasks = []
        for message in messages:
            if isinstance(message, logging.LogRecord):
                task = asyncio.create_task(self._process_log_record(message))
                tasks.append(task)
            else:
                task = asyncio.create_task(self._process_message(message))
                tasks.append(task)
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_log_record(self, record: logging.LogRecord) -> None:
        """
        Process a log record.
        
        Args:
            record (logging.LogRecord): Log record to process
        """
        # Default log record processing
        msg = f"{record.levelname}: {record.getMessage()}"
        print(msg)
    
    async def _process_message(self, message: Any) -> None:
        """
        Process a generic message.
        
        Args:
            message (Any): Message to process
        """
        # Default message processing
        print(f"Processing message: {message}")
    
    def get_stats(self) -> QueueStats:
        """
        Get current processing statistics.
        
        Returns:
            QueueStats: Current processing statistics
        """
        return QueueStats(
            total_messages=self._stats.total_messages,
            processed_messages=self._stats.processed_messages,
            dropped_messages=self._stats.dropped_messages,
            queue_size=len(self._current_batch),
            max_queue_size=self._stats.max_queue_size,
            avg_processing_time=self._stats.avg_processing_time,
            total_processing_time=self._stats.total_processing_time,
            batch_count=self._stats.batch_count,
            last_batch_time=self._stats.last_batch_time
        )
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._stats = QueueStats()


class AsyncBackpressureHandler:
    """
    Async backpressure handler for managing high load scenarios.
    
    This class provides intelligent backpressure handling to prevent
    system overload during high-throughput logging scenarios.
    
    Attributes:
        max_queue_size (int): Maximum queue size before backpressure
        drop_threshold (float): Threshold for dropping messages
        slow_down_threshold (float): Threshold for slowing down processing
        stats (QueueStats): Backpressure statistics
    """
    
    def __init__(self, max_queue_size: int = 1000, drop_threshold: float = 0.9,
                 slow_down_threshold: float = 0.7):
        """
        Initialize async backpressure handler.
        
        Args:
            max_queue_size (int): Maximum queue size before backpressure
            drop_threshold (float): Threshold for dropping messages (0.0-1.0)
            slow_down_threshold (float): Threshold for slowing down (0.0-1.0)
        """
        self.max_queue_size = max_queue_size
        self.drop_threshold = drop_threshold
        self.slow_down_threshold = slow_down_threshold
        
        self._queue_size = 0
        self._lock = asyncio.Lock()
        self._stats = QueueStats()
        self._slow_down_factor = 1.0
    
    async def should_accept_message(self, current_queue_size: int) -> bool:
        """
        Determine if a message should be accepted.
        
        Args:
            current_queue_size (int): Current queue size
            
        Returns:
            bool: True if message should be accepted
        """
        queue_ratio = current_queue_size / self.max_queue_size
        
        if queue_ratio >= self.drop_threshold:
            # Drop messages when queue is too full
            async with self._lock:
                self._stats.dropped_messages += 1
            return False
        
        return True
    
    async def get_processing_delay(self, current_queue_size: int) -> float:
        """
        Get processing delay based on queue size.
        
        Args:
            current_queue_size (int): Current queue size
            
        Returns:
            float: Delay in seconds
        """
        queue_ratio = current_queue_size / self.max_queue_size
        
        if queue_ratio >= self.slow_down_threshold:
            # Increase delay as queue fills up
            delay = (queue_ratio - self.slow_down_threshold) * 0.1
            return min(delay, 1.0)  # Max 1 second delay
        
        return 0.0
    
    async def update_queue_size(self, size: int) -> None:
        """
        Update current queue size.
        
        Args:
            size (int): Current queue size
        """
        async with self._lock:
            self._queue_size = size
            self._stats.queue_size = size
            self._stats.max_queue_size = max(
                self._stats.max_queue_size, 
                size
            )
    
    def get_stats(self) -> QueueStats:
        """
        Get current backpressure statistics.
        
        Returns:
            QueueStats: Current backpressure statistics
        """
        return QueueStats(
            total_messages=self._stats.total_messages,
            processed_messages=self._stats.processed_messages,
            dropped_messages=self._stats.dropped_messages,
            queue_size=self._queue_size,
            max_queue_size=self._stats.max_queue_size,
            avg_processing_time=self._stats.avg_processing_time,
            total_processing_time=self._stats.total_processing_time,
            batch_count=self._stats.batch_count,
            last_batch_time=self._stats.last_batch_time
        )
    
    def reset_stats(self) -> None:
        """Reset backpressure statistics."""
        self._stats = QueueStats()
        self._queue_size = 0 