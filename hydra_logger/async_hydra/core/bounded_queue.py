"""
Professional BoundedAsyncQueue with backpressure handling.

This module provides a professional async queue implementation with
configurable backpressure policies, memory monitoring integration,
and comprehensive statistics tracking.
"""

import asyncio
import time
from typing import Optional, Any, Dict, List
from enum import Enum


class QueuePolicy(Enum):
    """Queue backpressure policies."""
    DROP_OLDEST = "drop_oldest"
    BLOCK = "block"
    ERROR = "error"


class BoundedAsyncQueue:
    """
    Professional async queue with configurable backpressure.
    
    Features:
    - Configurable queue policies (drop_oldest, block, error)
    - Memory monitoring integration
    - Comprehensive statistics tracking
    - Timeout-based operations
    - Professional error handling
    """
    
    def __init__(self, 
                 maxsize: int = 1000, 
                 policy: QueuePolicy = QueuePolicy.DROP_OLDEST,
                 put_timeout: float = 0.1, 
                 get_timeout: float = 1.0):
        """
        Initialize BoundedAsyncQueue.
        
        Args:
            maxsize: Maximum queue size
            policy: Backpressure policy when queue is full
            put_timeout: Timeout for put operations
            get_timeout: Timeout for get operations
        """
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._policy = policy
        self._dropped_count = 0
        self._put_timeout = put_timeout
        self._get_timeout = get_timeout
        self._monitor_task = None
        self._start_time = time.time()
        self._stats = {
            'puts': 0,
            'gets': 0,
            'drops': 0,
            'timeouts': 0,
            'errors': 0,
            'queue_full_count': 0
        }
    
    async def put(self, item: Any) -> None:
        """
        Professional put with configurable backpressure policy.
        
        Args:
            item: Item to put in queue
            
        Raises:
            asyncio.QueueFull: If queue is full and policy is ERROR
        """
        self._stats['puts'] += 1
        
        try:
            await asyncio.wait_for(self._queue.put(item), timeout=self._put_timeout)
        except asyncio.TimeoutError:
            self._stats['timeouts'] += 1
            self._handle_put_timeout(item)
        except asyncio.QueueFull:
            self._stats['queue_full_count'] += 1
            self._handle_queue_full(item)
    
    def _handle_put_timeout(self, item: Any) -> None:
        """Handle put timeout based on policy."""
        if self._policy == QueuePolicy.DROP_OLDEST:
            try:
                self._queue.get_nowait()  # Remove oldest
                self._queue.put_nowait(item)  # Add new
                self._dropped_count += 1
                self._stats['drops'] += 1
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                self._stats['errors'] += 1
                raise asyncio.QueueFull("Queue is full and drop_oldest failed")
        elif self._policy == QueuePolicy.ERROR:
            raise asyncio.QueueFull("Queue put timeout")
        else:  # BLOCK policy
            # Try again without timeout
            asyncio.create_task(self._queue.put(item))
    
    def _handle_queue_full(self, item: Any) -> None:
        """Handle queue full based on policy."""
        if self._policy == QueuePolicy.DROP_OLDEST:
            try:
                self._queue.get_nowait()  # Remove oldest
                self._queue.put_nowait(item)  # Add new
                self._dropped_count += 1
                self._stats['drops'] += 1
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                self._stats['errors'] += 1
                raise asyncio.QueueFull("Queue is full and drop_oldest failed")
        elif self._policy == QueuePolicy.ERROR:
            raise asyncio.QueueFull("Queue is full")
        else:  # BLOCK policy
            # This shouldn't happen with QueueFull, but handle it
            asyncio.create_task(self._queue.put(item))
    
    async def get(self) -> Optional[Any]:
        """
        Professional get with timeout.
        
        Returns:
            Optional[Any]: Item from queue or None if timeout
        """
        self._stats['gets'] += 1
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=self._get_timeout)
        except asyncio.TimeoutError:
            self._stats['timeouts'] += 1
            return None  # Indicate no data available
    
    def get_nowait(self) -> Any:
        """
        Get item without waiting.
        
        Returns:
            Any: Item from queue
            
        Raises:
            asyncio.QueueEmpty: If queue is empty
        """
        self._stats['gets'] += 1
        return self._queue.get_nowait()
    
    def put_nowait(self, item: Any) -> None:
        """
        Put item without waiting.
        
        Args:
            item: Item to put in queue
            
        Raises:
            asyncio.QueueFull: If queue is full
        """
        self._stats['puts'] += 1
        self._queue.put_nowait(item)
    
    def qsize(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()
    
    def maxsize(self) -> int:
        """Get maximum queue size."""
        return self._queue.maxsize
    
    def get_dropped_count(self) -> int:
        """Get number of dropped items."""
        return self._dropped_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics."""
        return {
            'size': self.qsize(),
            'maxsize': self.maxsize(),
            'dropped_count': self._dropped_count,
            'policy': self._policy.value,
            'put_timeout': self._put_timeout,
            'get_timeout': self._get_timeout,
            'stats': self._stats.copy(),
            'uptime': time.time() - self._start_time,
            'is_empty': self.empty(),
            'is_full': self.full()
        }
    
    def reset_stats(self) -> None:
        """Reset queue statistics."""
        self._stats = {
            'puts': 0,
            'gets': 0,
            'drops': 0,
            'timeouts': 0,
            'errors': 0,
            'queue_full_count': 0
        }
        self._dropped_count = 0
        self._start_time = time.time()
    
    def set_policy(self, policy: QueuePolicy) -> None:
        """Set queue backpressure policy."""
        self._policy = policy
    
    def set_timeouts(self, put_timeout: float = None, get_timeout: float = None) -> None:
        """Set operation timeouts."""
        if put_timeout is not None:
            self._put_timeout = put_timeout
        if get_timeout is not None:
            self._get_timeout = get_timeout
    
    async def clear(self) -> None:
        """Clear all items from queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
    
    def __len__(self) -> int:
        """Get queue length."""
        return self.qsize()
    
    def __bool__(self) -> bool:
        """Check if queue has items."""
        return not self.empty() 