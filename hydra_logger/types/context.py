"""
Context Types for Hydra-Logger

This module provides  context type definitions for managing
logging context, caller information, and distributed tracing throughout
the system. It includes context management, caller detection, and system
information tracking.

FEATURES:
- LogContext: Main context container with metadata management
- ContextType: Different types of logging contexts
- CallerInfo: Information about calling code and functions
- SystemInfo: System-level information (thread, process, hostname)
- ContextManager: Context management and thread-local storage
- ContextDetector: Automatic caller information detection

CONTEXT TYPES:
- REQUEST: HTTP request context
- SESSION: User session context
- TRANSACTION: Database transaction context
- TRACE: Distributed tracing context
- USER: User-specific context
- ENVIRONMENT: Environment-specific context
- CUSTOM: Custom application context

USAGE:
    from hydra_logger.types import LogContext, ContextType, ContextManager

    # Create a new context
    context = LogContext(
        context_type=ContextType.REQUEST,
        metadata={"user_id": "123", "request_id": "req_456"}
    )

    # Set current context
    ContextManager.set_current_context(context)

    # Get current context
    current = ContextManager.get_current_context()

    # Add metadata
    context.update_metadata({"action": "login", "ip": "192.168.1.1"})

    # Get caller information
    from hydra_logger.types import get_caller_info
    caller = get_caller_info(depth=2)
    print(f"Called from: {caller.filename}:{caller.line_number}")
"""

import time
import threading
import contextvars
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ContextType(Enum):
    """Types of logging context."""

    REQUEST = "request"
    SESSION = "session"
    TRANSACTION = "transaction"
    TRACE = "trace"
    USER = "user"
    ENVIRONMENT = "environment"
    CUSTOM = "custom"


@dataclass
class CallerInfo:
    """Information about the calling code."""

    filename: str
    function_name: str
    line_number: int
    module_name: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.filename}:{self.line_number} in {self.function_name}"


@dataclass
class SystemInfo:
    """System information for context."""

    thread_id: int
    process_id: int
    hostname: Optional[str] = None
    pid: Optional[int] = None

    def __post_init__(self):
        if self.pid is None:
            import os

            self.pid = os.getpid()


@dataclass
class LogContext:
    """Main logging context container."""

    # Core context information
    context_id: str = field(default_factory=lambda: f"ctx_{int(time.time() * 1000)}")
    context_type: ContextType = ContextType.CUSTOM
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    # Caller information
    caller_info: Optional[CallerInfo] = None
    system_info: Optional[SystemInfo] = None

    # Context metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Usage tracking
    access_count: int = 0
    log_count: int = 0

    def __post_init__(self):
        """Initialize system info if not provided."""
        if self.system_info is None:
            self.system_info = SystemInfo(
                thread_id=threading.get_ident(),
                process_id=threading.current_thread().ident or 0,
            )

    def update_metadata(self, key: str, value: Any) -> None:
        """Update context metadata."""
        self.metadata[key] = value
        self._update_access()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get context metadata."""
        self._update_access()
        return self.metadata.get(key, default)

    def add_metadata(self, metadata: Dict[str, Any]) -> None:
        """Add multiple metadata items."""
        self.metadata.update(metadata)
        self._update_access()

    def has_metadata(self, key: str) -> bool:
        """Check if metadata key exists."""
        return key in self.metadata

    def remove_metadata(self, key: str) -> Any:
        """Remove metadata key and return its value."""
        self._update_access()
        return self.metadata.pop(key, None)

    def clear_metadata(self) -> None:
        """Clear all metadata."""
        self.metadata.clear()
        self._update_access()

    def increment_log_count(self) -> None:
        """Increment the log count for this context."""
        self.log_count += 1
        self._update_access()

    def _update_access(self) -> None:
        """Update last access time and count."""
        self.last_accessed = time.time()
        self.access_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get context usage statistics."""
        return {
            "context_id": self.context_id,
            "context_type": self.context_type.value,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "log_count": self.log_count,
            "metadata_count": len(self.metadata),
            "age_seconds": time.time() - self.created_at,
            "idle_seconds": time.time() - self.last_accessed,
        }

    def is_active(self, max_idle_seconds: float = 3600) -> bool:
        """Check if context is still active."""
        return (time.time() - self.last_accessed) < max_idle_seconds


class ContextManager:
    """Manages logging context throughout the system."""

    # Context variable for async operations
    _context_var = contextvars.ContextVar("log_context", default=None)

    # Thread-local storage for sync operations
    _thread_local = threading.local()

    @classmethod
    def get_current_context(cls) -> Optional[LogContext]:
        """Get the current logging context."""
        try:
            # Try async context first
            return cls._context_var.get()
        except LookupError:
            # Fall back to thread-local storage
            return getattr(cls._thread_local, "current_context", None)

    @classmethod
    def set_current_context(cls, context: LogContext) -> None:
        """Set the current logging context."""
        try:
            # Set async context
            cls._context_var.set(context)
        except RuntimeError:
            # Fall back to thread-local storage
            cls._thread_local.current_context = context

    @classmethod
    def clear_current_context(cls) -> None:
        """Clear the current logging context."""
        try:
            # Clear async context
            cls._context_var.set(None)
        except RuntimeError:
            # Clear thread-local storage
            if hasattr(cls._thread_local, "current_context"):
                delattr(cls._thread_local, "current_context")

    @classmethod
    def create_context(
        cls,
        context_type: ContextType = ContextType.CUSTOM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LogContext:
        """Create a new logging context."""
        context = LogContext(context_type=context_type, metadata=metadata or {})
        return context

    @classmethod
    def get_or_create_context(
        cls,
        context_type: ContextType = ContextType.CUSTOM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LogContext:
        """Get current context or create a new one."""
        current = cls.get_current_context()
        if current is None:
            current = cls.create_context(context_type, metadata)
            cls.set_current_context(current)
        return current


class ContextDetector:
    """Detects and extracts context information from the call stack."""

    _cache = {}
    _cache_enabled = True
    _cache_size = 1000

    @classmethod
    def get_caller_info(cls, depth: int = 2) -> CallerInfo:
        """Get information about the calling code."""
        if not cls._cache_enabled:
            return cls._get_caller_info_uncached(depth)

        cache_key = f"{threading.get_ident()}:{depth}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        caller_info = cls._get_caller_info_uncached(depth)
        cls._cache[cache_key] = caller_info

        # Maintain cache size
        if len(cls._cache) > cls._cache_size:
            cls._clear_cache()

        return caller_info

    @classmethod
    def _get_caller_info_uncached(cls, depth: int) -> CallerInfo:
        """Get caller info without caching."""
        import inspect

        try:
            frame = inspect.currentframe()
            for _ in range(depth):
                if frame is None:
                    break
                frame = frame.f_back

            if frame is None:
                return CallerInfo(
                    filename="<unknown>", function_name="<unknown>", line_number=0
                )

            filename = frame.f_code.co_filename
            function_name = frame.f_code.co_name
            line_number = frame.f_lineno

            # Extract module name if possible
            module_name = None
            if frame.f_globals and "__name__" in frame.f_globals:
                module_name = frame.f_globals["__name__"]

            return CallerInfo(
                filename=filename,
                function_name=function_name,
                line_number=line_number,
                module_name=module_name,
            )

        except Exception:
            return CallerInfo(
                filename="<error>", function_name="<error>", line_number=0
            )

    @classmethod
    def _clear_cache(cls) -> None:
        """Clear the caller info cache."""
        cls._cache.clear()

    @classmethod
    def disable_cache(cls) -> None:
        """Disable caller info caching."""
        cls._cache_enabled = False
        cls._clear_cache()

    @classmethod
    def enable_cache(cls) -> None:
        """Enable caller info caching."""
        cls._cache_enabled = True

    @classmethod
    def set_cache_size(cls, size: int) -> None:
        """Set the maximum cache size."""
        cls._cache_size = size
        if len(cls._cache) > size:
            cls._clear_cache()


# Convenience functions
def get_current_context() -> Optional[LogContext]:
    """Get the current logging context."""
    return ContextManager.get_current_context()


def set_current_context(context: LogContext) -> None:
    """Set the current logging context."""
    ContextManager.set_current_context(context)


def clear_current_context() -> None:
    """Clear the current logging context."""
    ContextManager.clear_current_context()


def create_context(
    context_type: ContextType = ContextType.CUSTOM,
    metadata: Optional[Dict[str, Any]] = None,
) -> LogContext:
    """Create a new logging context."""
    return ContextManager.create_context(context_type, metadata)


def get_caller_info(depth: int = 2) -> CallerInfo:
    """Get information about the calling code."""
    return ContextDetector.get_caller_info(depth)


# Export the main classes and functions
__all__ = [
    "ContextType",
    "CallerInfo",
    "SystemInfo",
    "LogContext",
    "ContextManager",
    "ContextDetector",
    "get_current_context",
    "set_current_context",
    "clear_current_context",
    "create_context",
    "get_caller_info",
]
