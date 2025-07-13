"""
Professional CoroutineManager for task tracking and cleanup.

This module provides professional task tracking and cleanup mechanisms
to prevent unawaited coroutines, memory leaks, and ensure proper
async resource management.
"""

import asyncio
import time
from typing import Set, Optional, List
from contextlib import asynccontextmanager


class CoroutineManager:
    """
    Professional task tracking and cleanup manager.
    
    Features:
    - Track all background tasks with automatic cleanup
    - Timeout-based shutdown to prevent hangs
    - Thread-safe operations with locks
    - Professional error handling
    - Comprehensive task statistics
    """
    
    def __init__(self, shutdown_timeout: float = 2.0):
        """
        Initialize CoroutineManager.
        
        Args:
            shutdown_timeout: Timeout for shutdown operations in seconds
        """
        self._tasks: Set[asyncio.Task] = set()
        self._shutdown_timeout = shutdown_timeout
        self._shutdown_event = asyncio.Event()
        self._cleanup_lock = asyncio.Lock()
        self._start_time = time.time()
        self._stats = {
            'tasks_created': 0,
            'tasks_completed': 0,
            'tasks_cancelled': 0,
            'shutdowns': 0,
            'timeout_shutdowns': 0
        }
    
    def track(self, coro) -> asyncio.Task:
        """
        Track a coroutine with automatic cleanup.
        
        Args:
            coro: Coroutine to track
            
        Returns:
            asyncio.Task: The created task
        """
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        self._stats['tasks_created'] += 1
        
        # Add callback to automatically remove completed tasks
        task.add_done_callback(self._task_done_callback)
        
        return task
    
    def _task_done_callback(self, task: asyncio.Task) -> None:
        """Callback when a task is done."""
        self._tasks.discard(task)
        self._stats['tasks_completed'] += 1
    
    async def shutdown(self) -> None:
        """
        Professional shutdown with proper timeout handling.
        
        This method:
        1. Signals shutdown to all tasks
        2. Cancels all tasks immediately
        3. Waits for completion with timeout
        4. Logs warnings for tasks that don't complete
        """
        async with self._cleanup_lock:
            if not self._tasks:
                return
            
            self._stats['shutdowns'] += 1
            
            # Signal shutdown to all tasks
            self._shutdown_event.set()
            
            # Get a copy of tasks to avoid modification during iteration
            tasks_to_cancel = list(self._tasks)
            
            # Cancel all tasks immediately
            for task in tasks_to_cancel:
                if not task.done():
                    task.cancel()
                    self._stats['tasks_cancelled'] += 1
            
            # Wait for all tasks to complete with timeout
            if tasks_to_cancel:
                try:
                    # Use gather with return_exceptions to handle cancelled tasks
                    await asyncio.wait_for(
                        asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                        timeout=self._shutdown_timeout
                    )
                except asyncio.TimeoutError:
                    self._stats['timeout_shutdowns'] += 1
                    remaining = len([t for t in tasks_to_cancel if not t.done()])
                    if remaining > 0:
                        print(f"WARNING: {remaining} tasks did not complete within {self._shutdown_timeout}s")
                except Exception as e:
                    # Handle any other exceptions during shutdown
                    print(f"WARNING: Exception during task shutdown: {e}")
            
            # Clear all tasks
            self._tasks.clear()
    
    def get_active_tasks(self) -> List[asyncio.Task]:
        """Get list of active tasks."""
        return list(self._tasks)
    
    def cancel_all(self) -> None:
        """Cancel all tracked tasks."""
        for task in list(self._tasks):
            task.cancel()
            self._stats['tasks_cancelled'] += 1
    
    def get_stats(self) -> dict:
        """Get comprehensive task statistics."""
        return {
            'active_tasks': len(self._tasks),
            'stats': self._stats.copy(),
            'uptime': time.time() - self._start_time,
            'shutdown_timeout': self._shutdown_timeout
        }
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_event.is_set()
    
    @asynccontextmanager
    async def managed_task(self, coro):
        """
        Context manager for managed task lifecycle.
        
        Args:
            coro: Coroutine to manage
            
        Yields:
            asyncio.Task: The managed task
        """
        task = self.track(coro)
        try:
            yield task
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass 