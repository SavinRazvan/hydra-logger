"""
Synchronous Utility Functions for Hydra-Logger

This module provides comprehensive synchronous utility functions for managing
threads, processes, resource pools, and execution strategies. It includes
retry mechanisms, throttling, and performance monitoring for sync operations.

FEATURES:
- SyncUtils: General synchronous utility functions
- ThreadManager: Thread pool management and execution
- ProcessManager: Process pool management and execution
- ResourcePool: Resource pooling and management
- LockManager: Lock management and synchronization
- SyncExecutor: High-level synchronous task execution
- Retry mechanisms with exponential backoff
- Throttling and debouncing utilities

EXECUTION STRATEGIES:
- THREAD: Thread pool execution for I/O-bound tasks
- PROCESS: Process pool execution for CPU-intensive tasks
- SEQUENTIAL: Sequential execution for simple operations

SYNCHRONOUS FEATURES:
- Thread and process management
- Resource pooling and allocation
- Lock management and synchronization
- Retry mechanisms with configurable backoff
- Throttling and debouncing
- Timeout handling and execution control

USAGE:
    from hydra_logger.utils import SyncUtils, ThreadManager, ProcessManager
    
    # General sync utilities
    future = SyncUtils.run_in_thread(cpu_function, arg1, arg2)
    result = SyncUtils.run_with_timeout(slow_function, timeout=30.0)
    retry_result = SyncUtils.retry(unreliable_function, max_attempts=3)
    
    # Thread management
    thread_manager = ThreadManager(max_workers=4)
    future = thread_manager.submit(cpu_function, arg1, arg2)
    active_threads = thread_manager.get_active_threads()
    
    # Process management
    process_manager = ProcessManager(max_workers=2)
    future = process_manager.submit(cpu_intensive_function, data)
    active_processes = process_manager.get_active_processes()
    
    # Resource pooling
    from hydra_logger.utils import ResourcePool
    pool = ResourcePool(max_resources=10)
    resource_id = pool.acquire(timeout=5.0)
    pool.release(resource_id)
"""

import threading
import multiprocessing
import time
import queue
from typing import Any, Dict, List, Optional, Callable, TypeVar
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
import functools


class ExecutionStrategy(Enum):
    """Execution strategies for sync operations."""

    THREAD = "thread"
    PROCESS = "process"
    SEQUENTIAL = "sequential"


T = TypeVar("T")


@dataclass
class ThreadInfo:
    """Thread information."""

    thread_id: int
    name: str
    daemon: bool
    alive: bool
    start_time: float
    execution_time: Optional[float] = None


class SyncUtils:
    """General sync utility functions."""

    @staticmethod
    def run_in_thread(func: Callable, *args, **kwargs) -> Future:
        """Run function in a separate thread."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(func, *args, **kwargs)

    @staticmethod
    def run_in_process(func: Callable, *args, **kwargs) -> Future:
        """Run function in a separate process."""
        with ProcessPoolExecutor(max_workers=1) as executor:
            return executor.submit(func, *args, **kwargs)

    @staticmethod
    def run_with_timeout(func: Callable, timeout: float, *args, **kwargs) -> Any:
        """Run function with timeout."""
        future = SyncUtils.run_in_thread(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            future.cancel()
            raise e

    @staticmethod
    def retry(
        func: Callable,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,),
        *args,
        **kwargs,
    ) -> Any:
        """Retry function execution with exponential backoff."""
        last_exception = None

        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e

                if attempt == max_attempts:
                    raise last_exception

                time.sleep(delay)
                delay *= backoff

        raise last_exception

    @staticmethod
    def debounce(func: Callable, delay: float) -> Callable:
        """Debounce function calls."""
        timer = None

        def debounced(*args, **kwargs):
            nonlocal timer
            if timer:
                timer.cancel()

            def delayed():
                func(*args, **kwargs)

            timer = threading.Timer(delay, delayed)
            timer.start()

        return debounced

    @staticmethod
    def throttle(func: Callable, max_calls: int, time_window: float) -> Callable:
        """Throttle function calls."""
        calls = []

        def throttled(*args, **kwargs):
            now = time.time()

            # Remove old calls outside the time window
            calls[:] = [
                call_time for call_time in calls if now - call_time < time_window
            ]

            if len(calls) < max_calls:
                calls.append(now)
                return func(*args, **kwargs)
            else:
                # Call is throttled
                return None

        return throttled


class ThreadManager:
    """Thread management utilities."""

    def __init__(self, max_workers: int = 4):
        """Initialize thread manager."""
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._active_threads = {}
        self._lock = threading.Lock()

    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """Submit a function for execution in a thread."""
        future = self._executor.submit(func, *args, **kwargs)

        with self._lock:
            self._active_threads[id(future)] = {
                "future": future,
                "func": func,
                "submitted_at": time.time(),
                "status": "running",
            }

        # Add callback to clean up when done
        future.add_done_callback(self._cleanup_thread)

        return future

    def _cleanup_thread(self, future: Future):
        """Clean up completed thread."""
        with self._lock:
            if id(future) in self._active_threads:
                thread_info = self._active_threads[id(future)]
                thread_info["status"] = "completed"
                thread_info["completed_at"] = time.time()

                # Keep for a short time for monitoring
                threading.Timer(60.0, lambda: self._remove_thread(id(future))).start()

    def _remove_thread(self, thread_id: int):
        """Remove thread from active threads."""
        with self._lock:
            self._active_threads.pop(thread_id, None)

    def get_active_threads(self) -> Dict[int, Dict[str, Any]]:
        """Get information about active threads."""
        with self._lock:
            return {
                tid: {
                    "func_name": info["func"].__name__,
                    "submitted_at": info["submitted_at"],
                    "status": info["status"],
                    "completed_at": info.get("completed_at"),
                    "running_time": time.time() - info["submitted_at"],
                }
                for tid, info in self._active_threads.items()
            }

    def cancel_thread(self, future: Future) -> bool:
        """Cancel a running thread."""
        if future.cancel():
            with self._lock:
                if id(future) in self._active_threads:
                    self._active_threads[id(future)]["status"] = "cancelled"
            return True
        return False

    def shutdown(self, wait: bool = True):
        """Shutdown the thread manager."""
        self._executor.shutdown(wait=wait)

        if not wait:
            # Cancel all running threads
            with self._lock:
                for thread_info in self._active_threads.values():
                    if thread_info["status"] == "running":
                        thread_info["future"].cancel()


class ProcessManager:
    """Process management utilities."""

    def __init__(self, max_workers: int = None):
        """Initialize process manager."""
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()

        self.max_workers = max_workers
        self._executor = ProcessPoolExecutor(max_workers=max_workers)
        self._active_processes = {}
        self._lock = threading.Lock()

    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """Submit a function for execution in a process."""
        future = self._executor.submit(func, *args, **kwargs)

        with self._lock:
            self._active_processes[id(future)] = {
                "future": future,
                "func": func,
                "submitted_at": time.time(),
                "status": "running",
            }

        # Add callback to clean up when done
        future.add_done_callback(self._cleanup_process)

        return future

    def _cleanup_process(self, future: Future):
        """Clean up completed process."""
        with self._lock:
            if id(future) in self._active_processes:
                process_info = self._active_processes[id(future)]
                process_info["status"] = "completed"
                process_info["completed_at"] = time.time()

                # Keep for a short time for monitoring
                threading.Timer(60.0, lambda: self._remove_process(id(future))).start()

    def _remove_process(self, process_id: int):
        """Remove process from active processes."""
        with self._lock:
            self._active_processes.pop(process_id, None)

    def get_active_processes(self) -> Dict[int, Dict[str, Any]]:
        """Get information about active processes."""
        with self._lock:
            return {
                pid: {
                    "func_name": info["func"].__name__,
                    "submitted_at": info["submitted_at"],
                    "status": info["status"],
                    "completed_at": info.get("completed_at"),
                    "running_time": time.time() - info["submitted_at"],
                }
                for pid, info in self._active_processes.items()
            }

    def cancel_process(self, future: Future) -> bool:
        """Cancel a running process."""
        if future.cancel():
            with self._lock:
                if id(future) in self._active_processes:
                    self._active_processes[id(future)]["status"] = "cancelled"
            return True
        return False

    def shutdown(self, wait: bool = True):
        """Shutdown the process manager."""
        self._executor.shutdown(wait=wait)

        if not wait:
            # Cancel all running processes
            with self._lock:
                for process_info in self._active_processes.values():
                    if process_info["status"] == "running":
                        process_info["future"].cancel()


class ResourcePool:
    """Resource pooling utilities."""

    def __init__(self, max_resources: int = 10):
        """Initialize resource pool."""
        self.max_resources = max_resources
        self._available_resources = queue.Queue(maxsize=max_resources)
        self._in_use_resources = set()
        self._lock = threading.Lock()

        # Initialize pool with resource IDs
        for i in range(max_resources):
            self._available_resources.put(i)

    def acquire(self, timeout: Optional[float] = None) -> Optional[int]:
        """Acquire a resource from the pool."""
        try:
            resource_id = self._available_resources.get(timeout=timeout)
            with self._lock:
                self._in_use_resources.add(resource_id)
            return resource_id
        except queue.Empty:
            return None

    def release(self, resource_id: int):
        """Release a resource back to the pool."""
        with self._lock:
            if resource_id in self._in_use_resources:
                self._in_use_resources.remove(resource_id)
                self._available_resources.put(resource_id)

    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status."""
        with self._lock:
            return {
                "max_resources": self.max_resources,
                "available_resources": self._available_resources.qsize(),
                "in_use_resources": len(self._in_use_resources),
                "total_resources": self.max_resources,
            }

    def is_available(self) -> bool:
        """Check if resources are available."""
        return not self._available_resources.empty()

    def wait_for_resource(self, timeout: Optional[float] = None) -> Optional[int]:
        """Wait for a resource to become available."""
        return self.acquire(timeout=timeout)

    def __enter__(self):
        """Context manager entry."""
        self._resource_id = self.acquire()
        if self._resource_id is None:
            raise RuntimeError("No resources available in pool")
        return self._resource_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if hasattr(self, "_resource_id"):
            self.release(self._resource_id)


class LockManager:
    """Lock management utilities."""

    def __init__(self):
        """Initialize lock manager."""
        self._locks = {}
        self._lock = threading.Lock()

    def get_lock(self, name: str) -> threading.Lock:
        """Get or create a named lock."""
        with self._lock:
            if name not in self._locks:
                self._locks[name] = threading.Lock()
            return self._locks[name]

    def acquire_lock(self, name: str, timeout: Optional[float] = None) -> bool:
        """Acquire a named lock."""
        lock = self.get_lock(name)
        return lock.acquire(timeout=timeout)

    def release_lock(self, name: str):
        """Release a named lock."""
        lock = self.get_lock(name)
        try:
            lock.release()
        except RuntimeError:
            # Lock was not acquired
            pass

    def get_lock_status(self) -> Dict[str, bool]:
        """Get status of all locks."""
        with self._lock:
            return {name: lock.locked() for name, lock in self._locks.items()}

    def clear_unused_locks(self):
        """Clear locks that are no longer referenced."""
        with self._lock:
            locks_to_remove = []
            for name, lock in self._locks.items():
                if not lock.locked():
                    locks_to_remove.append(name)

            for name in locks_to_remove:
                del self._locks[name]

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.clear_unused_locks()


class SyncExecutor:
    """Synchronous task executor."""

    def __init__(
        self,
        strategy: ExecutionStrategy = ExecutionStrategy.THREAD,
        max_workers: int = 4,
    ):
        """Initialize sync executor."""
        self.strategy = strategy
        self.max_workers = max_workers

        if strategy == ExecutionStrategy.THREAD:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
        elif strategy == ExecutionStrategy.PROCESS:
            self._executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self._executor = None

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function according to strategy."""
        if self.strategy == ExecutionStrategy.SEQUENTIAL:
            return func(*args, **kwargs)
        else:
            future = self._executor.submit(func, *args, **kwargs)
            return future.result()

    def execute_batch(
        self, tasks: List[tuple], max_concurrent: Optional[int] = None
    ) -> List[Any]:
        """Execute multiple tasks in batch."""
        if self.strategy == ExecutionStrategy.SEQUENTIAL:
            results = []
            for func, args, kwargs in tasks:
                results.append(func(*args, **kwargs))
            return results
        else:
            futures = []
            for func, args, kwargs in tasks:
                future = self._executor.submit(func, *args, **kwargs)
                futures.append(future)

            return [future.result() for future in futures]

    def map(self, func: Callable, iterable, chunksize: int = 1) -> List[Any]:
        """Map function over iterable."""
        if self.strategy == ExecutionStrategy.SEQUENTIAL:
            return [func(item) for item in iterable]
        else:
            return list(self._executor.map(func, iterable, chunksize=chunksize))

    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        if self._executor:
            self._executor.shutdown(wait=wait)


# Utility decorators
def run_in_thread(func: Callable) -> Callable:
    """Decorator to run function in a separate thread."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return SyncUtils.run_in_thread(func, *args, **kwargs)

    return wrapper


def run_in_process(func: Callable) -> Callable:
    """Decorator to run function in a separate process."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return SyncUtils.run_in_process(func, *args, **kwargs)

    return wrapper


def with_timeout(timeout: float):
    """Decorator to run function with timeout."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return SyncUtils.run_with_timeout(func, timeout, *args, **kwargs)

        return wrapper

    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator to retry function execution."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return SyncUtils.retry(func, max_attempts, delay, backoff, exceptions)

        return wrapper

    return decorator


def debounce(delay: float):
    """Decorator to debounce function calls."""

    def decorator(func: Callable) -> Callable:
        return SyncUtils.debounce(func, delay)

    return decorator


def throttle(max_calls: int, time_window: float):
    """Decorator to throttle function calls."""

    def decorator(func: Callable) -> Callable:
        return SyncUtils.throttle(func, max_calls, time_window)

    return decorator
