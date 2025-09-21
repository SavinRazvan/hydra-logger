"""
Async Utility Functions for Hydra-Logger

This module provides comprehensive asynchronous utility functions and classes
for managing async operations, task execution, queuing, retry mechanisms,
and timeout handling. It supports multiple execution modes and provides
robust error handling and performance monitoring.

FEATURES:
- AsyncUtils: General async utility functions and coroutine management
- AsyncExecutor: Multi-mode task execution (async, thread, process)
- AsyncQueue: Async queue with backpressure handling and statistics
- AsyncRetry: Retry mechanism with exponential backoff
- AsyncTimeout: Timeout context managers and decorators
- Task management with status tracking and cleanup
- Performance monitoring and execution statistics

EXECUTION MODES:
- ASYNC: Native async/await execution
- THREAD: Thread pool execution for CPU-bound tasks
- PROCESS: Process pool execution for CPU-intensive operations

USAGE:
    from hydra_logger.utils import AsyncUtils, AsyncExecutor, AsyncQueue
    
    # General async utilities
    result = await AsyncUtils.run_async(sync_function, arg1, arg2)
    task = AsyncUtils.create_task(coroutine_function())
    
    # Task execution
    executor = AsyncExecutor(max_workers=4, mode=ExecutionMode.THREAD)
    result = await executor.execute(cpu_intensive_function, data)
    
    # Async queue with backpressure
    queue = AsyncQueue(maxsize=1000)
    await queue.put(item)
    item = await queue.get()
    
    # Retry mechanism
    retry = AsyncRetry(max_attempts=3, base_delay=1.0)
    result = await retry.execute(unreliable_function)
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Callable, Coroutine, TypeVar
from dataclasses import dataclass
from enum import Enum
import functools
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading


class ExecutionMode(Enum):
    """Async execution modes."""

    ASYNC = "async"
    THREAD = "thread"
    PROCESS = "process"


T = TypeVar("T")


@dataclass
class AsyncTask:
    """Async task information."""

    task_id: str
    coroutine: Coroutine
    created_at: float
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[Exception] = None
    execution_time: Optional[float] = None


class AsyncUtils:
    """General async utility functions."""

    @staticmethod
    def is_coroutine_function(func: Callable) -> bool:
        """Check if function is a coroutine function."""
        return asyncio.iscoroutinefunction(func)

    @staticmethod
    def is_coroutine(obj: Any) -> bool:
        """Check if object is a coroutine."""
        return asyncio.iscoroutine(obj)

    @staticmethod
    def run_sync(coroutine: Coroutine) -> Any:
        """Run coroutine in sync context."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coroutine)

    @staticmethod
    def run_async(func: Callable, *args, **kwargs) -> Any:
        """Run sync function in async context."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

    @staticmethod
    def create_task(coroutine: Coroutine, name: Optional[str] = None) -> asyncio.Task:
        """Create and return an asyncio task."""
        return asyncio.create_task(coroutine, name=name)

    @staticmethod
    def gather(*coroutines: Coroutine, return_exceptions: bool = False) -> Coroutine:
        """Gather multiple coroutines."""
        return asyncio.gather(*coroutines, return_exceptions=return_exceptions)

    @staticmethod
    def wait_for(coroutine: Coroutine, timeout: float) -> Coroutine:
        """Wait for coroutine with timeout."""
        return asyncio.wait_for(coroutine, timeout=timeout)

    @staticmethod
    def sleep(seconds: float) -> Coroutine:
        """Async sleep."""
        return asyncio.sleep(seconds)

    @staticmethod
    def shield(coroutine: Coroutine) -> Coroutine:
        """Shield coroutine from cancellation."""
        return asyncio.shield(coroutine)

    @staticmethod
    def timeout_at(when: float) -> Coroutine:
        """Create timeout context manager."""
        return asyncio.timeout_at(when)

    @staticmethod
    def timeout(seconds: float) -> Coroutine:
        """Create timeout context manager."""
        return asyncio.timeout(seconds)


class AsyncExecutor:
    """Async task executor with multiple execution modes."""

    def __init__(
        self, max_workers: int = 4, mode: ExecutionMode = ExecutionMode.THREAD
    ):
        """Initialize async executor."""
        self.max_workers = max_workers
        self.mode = mode
        self._executor = None
        self._tasks: Dict[str, AsyncTask] = {}
        self._lock = threading.Lock()

        self._setup_executor()

    def _setup_executor(self):
        """Setup the appropriate executor."""
        if self.mode == ExecutionMode.THREAD:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        elif self.mode == ExecutionMode.PROCESS:
            self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self._executor = None

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function in appropriate context."""
        if self.mode == ExecutionMode.ASYNC:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return await AsyncUtils.run_async(func, *args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._executor, functools.partial(func, *args, **kwargs)
            )

    async def execute_batch(
        self, tasks: List[tuple], max_concurrent: Optional[int] = None
    ) -> List[Any]:
        """Execute multiple tasks in batch."""
        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def execute_with_semaphore(task):
                async with semaphore:
                    func, args, kwargs = task
                    return await self.execute(func, *args, kwargs)

            coroutines = [execute_with_semaphore(task) for task in tasks]
        else:
            coroutines = [
                self.execute(func, *args, kwargs) for func, *args, kwargs in tasks
            ]

        return await asyncio.gather(*coroutines, return_exceptions=True)

    def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Submit a task for execution."""
        with self._lock:
            if task_id in self._tasks:
                raise ValueError(f"Task ID already exists: {task_id}")

            # Create task info
            task_info = AsyncTask(
                task_id=task_id,
                coroutine=self.execute(func, *args, **kwargs),
                created_at=time.time(),
            )

            self._tasks[task_id] = task_info

            # Start execution
            asyncio.create_task(self._execute_task(task_info))

            return task_id

    async def _execute_task(self, task: AsyncTask):
        """Execute a submitted task."""
        try:
            start_time = time.time()
            task.status = "running"

            result = await task.coroutine

            task.status = "completed"
            task.result = result
            task.execution_time = time.time() - start_time

        except Exception as e:
            task.status = "failed"
            task.error = e
            task.execution_time = time.time() - task.created_at

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and information."""
        with self._lock:
            if task_id not in self._tasks:
                return None

            task = self._tasks[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status,
                "created_at": task.created_at,
                "execution_time": task.execution_time,
                "result": task.result,
                "error": str(task.error) if task.error else None,
            }

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get status of all tasks."""
        with self._lock:
            return [self.get_task_status(task_id) for task_id in self._tasks.keys()]

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        with self._lock:
            if task_id not in self._tasks:
                return False

            task = self._tasks[task_id]
            if task.status == "running":
                task.coroutine.close()
                task.status = "cancelled"
                return True

            return False

    def cleanup_completed_tasks(self, max_age: float = 3600) -> int:
        """Clean up completed tasks older than max_age seconds."""
        current_time = time.time()
        cleaned_count = 0

        with self._lock:
            task_ids_to_remove = []

            for task_id, task in self._tasks.items():
                if (
                    task.status in ["completed", "failed", "cancelled"]
                    and current_time - task.created_at > max_age
                ):
                    task_ids_to_remove.append(task_id)

            for task_id in task_ids_to_remove:
                del self._tasks[task_id]
                cleaned_count += 1

        return cleaned_count

    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        if self._executor:
            self._executor.shutdown(wait=wait)


class AsyncQueue:
    """Async queue with backpressure handling."""

    def __init__(self, maxsize: int = 0):
        """Initialize async queue."""
        self.maxsize = maxsize
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._stats = {"put_count": 0, "get_count": 0, "size": 0, "max_size": maxsize}

    async def put(self, item: Any, timeout: Optional[float] = None) -> None:
        """Put item in queue with optional timeout."""
        try:
            if timeout:
                await asyncio.wait_for(self._queue.put(item), timeout=timeout)
            else:
                await self._queue.put(item)

            self._stats["put_count"] += 1
            self._stats["size"] = self._queue.qsize()

        except asyncio.TimeoutError:
            raise TimeoutError(f"Queue put timeout after {timeout} seconds")

    async def get(self, timeout: Optional[float] = None) -> Any:
        """Get item from queue with optional timeout."""
        try:
            if timeout:
                item = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            else:
                item = await self._queue.get()

            self._stats["get_count"] += 1
            self._stats["size"] = self._queue.qsize()

            return item

        except asyncio.TimeoutError:
            raise TimeoutError(f"Queue get timeout after {timeout} seconds")

    def put_nowait(self, item: Any) -> None:
        """Put item in queue without waiting."""
        self._queue.put_nowait(item)
        self._stats["put_count"] += 1
        self._stats["size"] = self._queue.qsize()

    def get_nowait(self) -> Any:
        """Get item from queue without waiting."""
        item = self._queue.get_nowait()
        self._stats["get_count"] += 1
        self._stats["size"] = self._queue.qsize()
        return item

    def qsize(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()

    def clear(self) -> None:
        """Clear all items from queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break

        self._stats["size"] = 0

    async def join(self) -> None:
        """Wait until all items are processed."""
        await self._queue.join()

    def task_done(self) -> None:
        """Mark task as done."""
        self._queue.task_done()

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return self._stats.copy()


class AsyncRetry:
    """Async retry mechanism with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """Initialize retry mechanism."""
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return await AsyncUtils.run_async(func, *args, **kwargs)

            except Exception as e:
                last_exception = e

                if attempt == self.max_attempts:
                    raise last_exception

                # Calculate delay with exponential backoff
                delay = min(
                    self.base_delay * (self.exponential_base ** (attempt - 1)),
                    self.max_delay,
                )

                await asyncio.sleep(delay)

        raise last_exception

    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply retry logic to function."""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.execute(func, *args, **kwargs)

        return wrapper


class AsyncTimeout:
    """Async timeout context manager."""

    def __init__(self, timeout: float):
        """Initialize timeout."""
        self.timeout = timeout
        self._timeout_cm = None

    async def __aenter__(self):
        """Enter async context."""
        self._timeout_cm = asyncio.timeout(self.timeout)
        return await self._timeout_cm.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._timeout_cm:
            await self._timeout_cm.__aexit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def timeout(seconds: float):
        """Create timeout context manager."""
        return asyncio.timeout(seconds)

    @staticmethod
    def timeout_at(when: float):
        """Create timeout context manager at specific time."""
        return asyncio.timeout_at(when)


# Utility decorators
def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
):
    """Decorator to apply async retry logic."""

    def decorator(func: Callable) -> Callable:
        retry = AsyncRetry(max_attempts, base_delay, max_delay, exponential_base)
        return retry(func)

    return decorator


def async_timeout(seconds: float):
    """Decorator to apply async timeout."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with asyncio.timeout(seconds):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return await AsyncUtils.run_async(func, *args, **kwargs)

        return wrapper

    return decorator


def to_async(func: Callable) -> Callable:
    """Convert sync function to async."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await AsyncUtils.run_async(func, *args, **kwargs)

    return wrapper


def to_sync(func: Callable) -> Callable:
    """Convert async function to sync."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return AsyncUtils.run_sync(func(*args, **kwargs))

    return wrapper
