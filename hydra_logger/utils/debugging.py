"""
Debugging and Development Utilities for Hydra-Logger

This module provides comprehensive debugging and development utilities including
performance profiling, object inspection, debug logging, and execution monitoring.
It supports multiple debug levels and modes for different development scenarios.

FEATURES:
- DebugUtils: General debugging utility functions
- DebugDecorator: Function decoration for automatic debugging
- PerformanceProfiler: Performance measurement and profiling
- DebugInspector: Object inspection and analysis
- DebugLogger: Specialized logging for debug information
- Call stack analysis and context tracking
- Memory usage monitoring and statistics
- Thread and execution information

DEBUG LEVELS:
- BASIC: Basic function execution tracking
- DETAILED: Execution time and memory usage
- VERBOSE: Module, line, and thread information
- EXTREME: Full context including variables and stack

DEBUG MODES:
- DISABLED: No debugging output
- ENABLED: Always enable debugging
- CONDITIONAL: Enable based on condition
- PERFORMANCE: Enable only for performance monitoring

USAGE:
    from hydra_logger.utils import DebugDecorator, PerformanceProfiler, DebugLogger
    from hydra_logger.utils import DebugLevel

    # Function debugging decorator
    @DebugDecorator(level=DebugLevel.DETAILED)
    def my_function():
        return "result"
    
    # Performance profiling
    profiler = PerformanceProfiler("my_operation")
    profiler.start("data_processing")
    # ... do work ...
    profiler.stop(processed_items=100)
    stats = profiler.get_stats()
    
    # Debug logging
    debug_logger = DebugLogger(level=DebugLevel.VERBOSE)
    debug_logger.log_context(context, "Processing started")
    
    # Object inspection
    from hydra_logger.utils import DebugInspector
    inspector = DebugInspector(my_object)
    info = inspector.inspect(max_depth=3)
"""

import os
import sys
import time
import traceback
import inspect
import functools
import threading
import weakref
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import pprint
import logging


class DebugLevel(Enum):
    """Debug levels for different types of debugging information."""

    BASIC = "basic"
    DETAILED = "detailed"
    VERBOSE = "verbose"
    EXTREME = "extreme"


class DebugMode(Enum):
    """Debug operation modes."""

    DISABLED = "disabled"
    ENABLED = "enabled"
    CONDITIONAL = "conditional"
    PERFORMANCE = "performance"


@dataclass
class DebugContext:
    """Debug context information."""

    function_name: str
    module_name: str
    line_number: int
    timestamp: float
    thread_id: int
    call_stack: List[str] = field(default_factory=list)
    local_vars: Dict[str, Any] = field(default_factory=dict)
    global_vars: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DebugInfo:
    """Debug information for a function or operation."""

    context: DebugContext
    execution_time: Optional[float] = None
    memory_usage: Optional[int] = None
    return_value: Optional[Any] = None
    exception: Optional[Exception] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


class DebugUtils:
    """General debugging utility functions."""

    @staticmethod
    def get_call_stack(depth: int = 10) -> List[str]:
        """Get current call stack as list of strings."""
        try:
            stack = traceback.extract_stack()
            # Remove the current function call
            stack = stack[:-1]
            # Limit depth
            stack = stack[-depth:] if len(stack) > depth else stack
            
            return [f"{frame.filename}:{frame.lineno} in {frame.name}" for frame in stack]
        except Exception:
            return []

    @staticmethod
    def get_function_info(func: Callable) -> Dict[str, Any]:
        """Get detailed information about a function."""
        try:
            info = {
                "name": func.__name__,
                "module": func.__module__,
                "qualname": getattr(func, "__qualname__", func.__name__),
                "doc": func.__doc__,
                "annotations": getattr(func, "__annotations__", {}),
                "defaults": getattr(func, "__defaults__", None),
                "kwdefaults": getattr(func, "__kwdefaults__", None),
                "code": getattr(func, "__code__", None),
            }
            
            if info["code"]:
                info.update({
                    "arg_count": info["code"].co_argcount,
                    "var_names": info["code"].co_varnames,
                    "filename": info["code"].co_filename,
                    "first_line": info["code"].co_firstlineno,
                })
            
            return info
        except Exception:
            return {"name": str(func), "error": "Could not inspect function"}

    @staticmethod
    def get_object_info(obj: Any, max_depth: int = 3) -> Dict[str, Any]:
        """Get detailed information about an object."""
        info = {
            "type": type(obj).__name__,
            "module": getattr(type(obj), "__module__", "unknown"),
            "id": id(obj),
            "size": sys.getsizeof(obj),
        }
        
        if max_depth > 0:
            try:
                if hasattr(obj, "__dict__"):
                    info["attributes"] = {}
                    for key, value in obj.__dict__.items():
                        if max_depth > 1:
                            info["attributes"][key] = DebugUtils.get_object_info(
                                value, max_depth - 1
                            )
                        else:
                            info["attributes"][key] = f"{type(value).__name__}: {value}"
                
                if hasattr(obj, "__slots__"):
                    info["slots"] = obj.__slots__
                    info["slot_values"] = {}
                    for slot in obj.__slots__:
                        try:
                            value = getattr(obj, slot, None)
                            if max_depth > 1:
                                info["slot_values"][slot] = DebugUtils.get_object_info(
                                    value, max_depth - 1
                                )
                            else:
                                info["slot_values"][slot] = f"{type(value).__name__}: {value}"
                        except Exception:
                            info["slot_values"][slot] = "Error accessing slot"
                
                if hasattr(obj, "__class__"):
                    info["class"] = DebugUtils.get_object_info(
                        obj.__class__, max_depth - 1
                    )
                    
            except Exception as e:
                info["error"] = f"Error inspecting object: {e}"
        
        return info

    @staticmethod
    def format_value(value: Any, max_length: int = 100) -> str:
        """Format a value for debugging output."""
        try:
            if isinstance(value, str):
                if len(value) > max_length:
                    return f"'{value[:max_length]}...' ({len(value)} chars)"
                return f"'{value}'"
            elif isinstance(value, bytes):
                if len(value) > max_length:
                    return f"b'{value[:max_length]}...' ({len(value)} bytes)"
                return f"b'{value}'"
            elif isinstance(value, (list, tuple)):
                if len(value) > max_length:
                    return f"{type(value).__name__}[{len(value)} items]"
                return str(value)
            elif isinstance(value, dict):
                if len(value) > max_length:
                    return f"dict({len(value)} items)"
                return str(value)
            else:
                return str(value)
        except Exception:
            return f"<{type(value).__name__} object>"

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get current memory usage information."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "percent": process.memory_percent(),
                "available": psutil.virtual_memory().available,
                "total": psutil.virtual_memory().total,
            }
        except ImportError:
            return {"error": "psutil not available"}

    @staticmethod
    def get_thread_info() -> Dict[str, Any]:
        """Get current thread information."""
        current_thread = threading.current_thread()
        return {
            "name": current_thread.name,
            "ident": current_thread.ident,
            "daemon": current_thread.daemon,
            "alive": current_thread.is_alive(),
        }

    @staticmethod
    def create_debug_context() -> DebugContext:
        """Create debug context for current execution."""
        frame = inspect.currentframe()
        if frame:
            try:
                return DebugContext(
                    function_name=frame.f_code.co_name,
                    module_name=frame.f_globals.get("__name__", "unknown"),
                    line_number=frame.f_lineno,
                    timestamp=time.time(),
                    thread_id=threading.current_thread().ident or 0,
                    call_stack=DebugUtils.get_call_stack(),
                    local_vars=dict(frame.f_locals),
                    global_vars=dict(frame.f_globals),
                )
            finally:
                del frame
        
        return DebugContext(
            function_name="unknown",
            module_name="unknown",
            line_number=0,
            timestamp=time.time(),
            thread_id=threading.current_thread().ident or 0,
        )


class DebugDecorator:
    """Decorator for adding debugging to functions."""

    def __init__(
        self,
        level: DebugLevel = DebugLevel.BASIC,
        mode: DebugMode = DebugMode.ENABLED,
        condition: Optional[Callable[[], bool]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize debug decorator."""
        self.level = level
        self.mode = mode
        self.condition = condition
        self.logger = logger or logging.getLogger(__name__)

    def __call__(self, func: Callable) -> Callable:
        """Apply debug decorator to function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if debugging should be enabled
            if not self._should_debug():
                return func(*args, **kwargs)
            
            start_time = time.time()
            start_memory = self._get_memory_usage()
            debug_context = DebugUtils.create_debug_context()
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Create debug info
                debug_info = DebugInfo(
                    context=debug_context,
                    execution_time=time.time() - start_time,
                    memory_usage=self._get_memory_delta(start_memory),
                    return_value=result,
                )
                
                # Log debug information
                self._log_debug_info(debug_info, "SUCCESS")
                
                return result
                
            except Exception as e:
                # Create debug info for exception
                debug_info = DebugInfo(
                    context=debug_context,
                    execution_time=time.time() - start_time,
                    memory_usage=self._get_memory_delta(start_memory),
                    exception=e,
                )
                
                # Log debug information
                self._log_debug_info(debug_info, "EXCEPTION")
                
                # Re-raise exception
                raise
        
        return wrapper

    def _should_debug(self) -> bool:
        """Check if debugging should be enabled."""
        if self.mode == DebugMode.DISABLED:
            return False
        elif self.mode == DebugMode.ENABLED:
            return True
        elif self.mode == DebugMode.CONDITIONAL and self.condition:
            return self.condition()
        elif self.mode == DebugMode.PERFORMANCE:
            # Only enable in performance-critical scenarios
            return os.environ.get("DEBUG_PERFORMANCE", "false").lower() == "true"
        return False

    def _get_memory_usage(self) -> Optional[int]:
        """Get current memory usage."""
        try:
            import psutil
            return psutil.Process().memory_info().rss
        except ImportError:
            return None

    def _get_memory_delta(self, start_memory: Optional[int]) -> Optional[int]:
        """Calculate memory usage delta."""
        if start_memory is None:
            return None
        current_memory = self._get_memory_usage()
        if current_memory is None:
            return None
        return current_memory - start_memory

    def _log_debug_info(self, debug_info: DebugInfo, status: str):
        """Log debug information."""
        message = f"[DEBUG] {status} - {debug_info.context.function_name}"
        
        if self.level in [DebugLevel.DETAILED, DebugLevel.VERBOSE, DebugLevel.EXTREME]:
            message += f" (execution_time={debug_info.execution_time:.4f}s"
            if debug_info.memory_usage is not None:
                message += f", memory_delta={debug_info.memory_usage} bytes"
            message += ")"
        
        if self.level in [DebugLevel.VERBOSE, DebugLevel.EXTREME]:
            message += f" - Module: {debug_info.context.module_name}"
            message += f" - Line: {debug_info.context.line_number}"
        
        if self.level == DebugLevel.EXTREME:
            message += f" - Thread: {debug_info.context.thread_id}"
            message += f" - Stack depth: {len(debug_info.context.call_stack)}"
        
        self.logger.debug(message)
        
        # Log additional details for extreme level
        if self.level == DebugLevel.EXTREME:
            self._log_extreme_details(debug_info)

    def _log_extreme_details(self, debug_info: DebugInfo):
        """Log extreme level debugging details."""
        if debug_info.context.local_vars:
            self.logger.debug(f"Local variables: {debug_info.context.local_vars}")
        
        if debug_info.context.call_stack:
            self.logger.debug(f"Call stack: {debug_info.context.call_stack}")
        
        if debug_info.return_value is not None:
            self.logger.debug(f"Return value: {debug_info.return_value}")
        
        if debug_info.exception:
            self.logger.debug(f"Exception: {debug_info.exception}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")


class PerformanceProfiler:
    """Performance profiling utility."""

    def __init__(self, name: str = "default"):
        """Initialize performance profiler."""
        self.name = name
        self.measurements: List[Dict[str, Any]] = []
        self.current_measurement: Optional[Dict[str, Any]] = None

    def start(self, operation: str, **kwargs):
        """Start timing an operation."""
        self.current_measurement = {
            "operation": operation,
            "start_time": time.time(),
            "start_memory": self._get_memory_usage(),
            "kwargs": kwargs,
        }

    def stop(self, **result_data):
        """Stop timing an operation and record results."""
        if self.current_measurement is None:
            return
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        measurement = {
            **self.current_measurement,
            "end_time": end_time,
            "end_memory": end_memory,
            "duration": end_time - self.current_measurement["start_time"],
            "memory_delta": (
                end_memory - self.current_measurement["start_memory"]
                if end_memory is not None and self.current_measurement["start_memory"] is not None
                else None
            ),
            "result_data": result_data,
        }
        
        self.measurements.append(measurement)
        self.current_measurement = None

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.measurements:
            return {"total_operations": 0}
        
        durations = [m["duration"] for m in self.measurements]
        memory_deltas = [m["memory_delta"] for m in self.measurements if m["memory_delta"] is not None]
        
        stats = {
            "total_operations": len(self.measurements),
            "total_duration": sum(durations),
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "operations": self.measurements,
        }
        
        if memory_deltas:
            stats.update({
                "total_memory_delta": sum(memory_deltas),
                "average_memory_delta": sum(memory_deltas) / len(memory_deltas),
                "min_memory_delta": min(memory_deltas),
                "max_memory_delta": max(memory_deltas),
            })
        
        return stats

    def reset(self):
        """Reset all measurements."""
        self.measurements.clear()
        self.current_measurement = None

    def _get_memory_usage(self) -> Optional[int]:
        """Get current memory usage."""
        try:
            import psutil
            return psutil.Process().memory_info().rss
        except ImportError:
            return None


class DebugInspector:
    """Object inspection and debugging utility."""

    def __init__(self, obj: Any):
        """Initialize inspector with object."""
        self.obj = obj
        self.obj_type = type(obj)

    def inspect(self, max_depth: int = 3) -> Dict[str, Any]:
        """Perform comprehensive inspection of object."""
        return DebugUtils.get_object_info(self.obj, max_depth)

    def get_attributes(self) -> Dict[str, Any]:
        """Get all attributes of the object."""
        attributes = {}
        
        # Regular attributes
        if hasattr(self.obj, "__dict__"):
            for key, value in self.obj.__dict__.items():
                attributes[key] = {
                    "value": value,
                    "type": type(value).__name__,
                    "size": sys.getsizeof(value),
                }
        
        # Slot attributes
        if hasattr(self.obj, "__slots__"):
            for slot in self.obj.__slots__:
                try:
                    value = getattr(self.obj, slot, None)
                    attributes[f"slot_{slot}"] = {
                        "value": value,
                        "type": type(value).__name__,
                        "size": sys.getsizeof(value),
                        "is_slot": True,
                    }
                except Exception as e:
                    attributes[f"slot_{slot}"] = {
                        "error": str(e),
                        "is_slot": True,
                    }
        
        # Properties
        properties = {}
        for name in dir(self.obj_type):
            try:
                attr = getattr(self.obj_type, name)
                if isinstance(attr, property):
                    properties[name] = {
                        "fget": attr.fget is not None,
                        "fset": attr.fset is not None,
                        "fdel": attr.fdel is not None,
                        "doc": attr.__doc__,
                    }
            except Exception:
                pass
        
        if properties:
            attributes["_properties"] = properties
        
        return attributes

    def get_methods(self) -> Dict[str, Any]:
        """Get all methods of the object."""
        methods = {}
        
        for name in dir(self.obj_type):
            try:
                attr = getattr(self.obj_type, name)
                if callable(attr) and not name.startswith("_"):
                    methods[name] = {
                        "type": "method",
                        "signature": str(inspect.signature(attr)),
                        "doc": attr.__doc__,
                        "module": getattr(attr, "__module__", "unknown"),
                    }
            except Exception:
                pass
        
        return methods

    def get_inheritance(self) -> List[str]:
        """Get inheritance hierarchy."""
        hierarchy = []
        current_class = self.obj_type
        
        while current_class:
            hierarchy.append(current_class.__name__)
            current_class = current_class.__bases__[0] if current_class.__bases__ else None
        
        return hierarchy

    def compare_with(self, other: Any) -> Dict[str, Any]:
        """Compare this object with another object."""
        comparison = {
            "same_type": type(self.obj) == type(other),
            "same_id": id(self.obj) == id(other),
            "same_value": self.obj == other,
            "size_comparison": {
                "self": sys.getsizeof(self.obj),
                "other": sys.getsizeof(other),
            },
        }
        
        if comparison["same_type"]:
            comparison["type_name"] = type(self.obj).__name__
            comparison["attributes_diff"] = self._compare_attributes(other)
        
        return comparison

    def _compare_attributes(self, other: Any) -> Dict[str, Any]:
        """Compare attributes between two objects of the same type."""
        if not hasattr(self.obj, "__dict__") or not hasattr(other, "__dict__"):
            return {"error": "Cannot compare attributes"}
        
        self_attrs = set(self.obj.__dict__.keys())
        other_attrs = set(other.__dict__.keys())
        
        return {
            "only_in_self": list(self_attrs - other_attrs),
            "only_in_other": list(other_attrs - self_attrs),
            "common": list(self_attrs & other_attrs),
            "different_values": [
                attr for attr in self_attrs & other_attrs
                if getattr(self.obj, attr) != getattr(other, attr)
            ],
        }


class DebugLogger:
    """Specialized logger for debugging information."""

    def __init__(
        self,
        name: str = "debug",
        level: DebugLevel = DebugLevel.BASIC,
        output_file: Optional[str] = None,
    ):
        """Initialize debug logger."""
        self.name = name
        self.level = level
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Add file handler if specified
        if output_file:
            file_handler = logging.FileHandler(output_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_context(self, context: DebugContext, message: str = ""):
        """Log debug context information."""
        log_message = f"{message} - Function: {context.function_name}"
        
        if self.level in [DebugLevel.DETAILED, DebugLevel.VERBOSE, DebugLevel.EXTREME]:
            log_message += f" - Module: {context.module_name} - Line: {context.line_number}"
        
        if self.level in [DebugLevel.VERBOSE, DebugLevel.EXTREME]:
            log_message += f" - Thread: {context.thread_id}"
        
        self.logger.debug(log_message)
        
        if self.level == DebugLevel.EXTREME:
            self._log_extreme_context(context)

    def log_object(self, obj: Any, name: str = "object"):
        """Log object information."""
        inspector = DebugInspector(obj)
        info = inspector.inspect()
        
        self.logger.debug(f"{name} info: {json.dumps(info, default=str, indent=2)}")

    def log_performance(self, profiler: PerformanceProfiler):
        """Log performance profiling information."""
        stats = profiler.get_stats()
        self.logger.debug(f"Performance stats: {json.dumps(stats, default=str, indent=2)}")

    def _log_extreme_context(self, context: DebugContext):
        """Log extreme level context details."""
        if context.local_vars:
            self.logger.debug(f"Local variables: {context.local_vars}")
        
        if context.call_stack:
            self.logger.debug(f"Call stack: {context.call_stack}")


# Convenience functions
def debug_function(
    level: DebugLevel = DebugLevel.BASIC,
    mode: DebugMode = DebugMode.ENABLED,
    condition: Optional[Callable[[], bool]] = None,
    logger: Optional[logging.Logger] = None,
):
    """Decorator for debugging functions."""
    return DebugDecorator(level, mode, condition, logger)


def inspect_object(obj: Any, max_depth: int = 3) -> Dict[str, Any]:
    """Quick object inspection."""
    return DebugUtils.get_object_info(obj, max_depth)


def get_call_stack(depth: int = 10) -> List[str]:
    """Get current call stack."""
    return DebugUtils.get_call_stack(depth)


def create_profiler(name: str = "default") -> PerformanceProfiler:
    """Create a performance profiler."""
    return PerformanceProfiler(name)


def create_debug_logger(
    name: str = "debug",
    level: DebugLevel = DebugLevel.BASIC,
    output_file: Optional[str] = None,
) -> DebugLogger:
    """Create a debug logger."""
    return DebugLogger(name, level, output_file)
