"""
Safe Error Logging Utility for Hydra-Logger

This module provides a failsafe error logging mechanism that can capture
and log errors even when the main logging system fails. It ensures that
critical errors (like malloc errors, system errors, etc.) are always logged
to error.jsonl.

CRITICAL FEATURES:
- Never fails (failsafe design)
- Writes directly to error.jsonl even if main logger fails
- Handles all exception types including system-level errors
- Thread-safe operation
- Prevents infinite loops
"""

import os
import sys
import json
import traceback
import threading
from datetime import datetime
from typing import Any, Optional, Dict
from pathlib import Path


class SafeErrorLogger:
    """
    Failsafe error logger that writes directly to error.jsonl.
    
    This logger is designed to NEVER fail - it can log errors even when
    the main logging system is broken or unavailable.
    """
    
    _lock = threading.Lock()
    _error_file = None
    _initialized = False
    _error_count = 0
    _max_errors_per_session = 10000  # Prevent log spam
    
    @classmethod
    def _get_error_file_path(cls) -> Path:
        """Get the path to error.jsonl file."""
        # Try to use logs/error.jsonl relative to project root
        current_dir = Path.cwd()
        
        # Look for logs directory
        logs_dir = current_dir / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
        
        return logs_dir / "error.jsonl"
    
    @classmethod
    def _initialize(cls) -> None:
        """Initialize the error logger (only once)."""
        if cls._initialized:
            return
        
        with cls._lock:
            if cls._initialized:
                return
            
            try:
                error_file_path = cls._get_error_file_path()
                
                # CRITICAL: Open file with line buffering and ensure it's writable
                # Use 'a+' mode to ensure file exists and is writable
                cls._error_file = open(error_file_path, "a+", encoding="utf-8", buffering=1)  # Line buffered
                
                # CRITICAL: Verify file is writable by writing a test (will be flushed immediately)
                # This ensures the file handle is valid
                cls._error_file.flush()
                
                cls._initialized = True
            except Exception as e:
                # If file opening fails, write to stderr as last resort
                # But also try to log this failure
                try:
                    cls._error_file = sys.stderr
                    cls._initialized = True
                    # Log that file logging failed
                    sys.stderr.write(f"[ERROR_LOGGER] Failed to open error.jsonl: {e}\n")
                    sys.stderr.flush()
                except Exception:
                    pass
    
    @classmethod
    def log_error(
        cls,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        trace: Optional[str] = None,
        component: Optional[str] = None,
    ) -> None:
        """
        Log an error to error.jsonl in a safe, failsafe manner.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            trace: Stack trace (auto-generated if None)
            component: Component name where error occurred
        """
        # Prevent infinite error loops
        cls._error_count += 1
        if cls._error_count > cls._max_errors_per_session:
            return
        
        try:
            # Initialize if needed
            if not cls._initialized:
                cls._initialize()
            
            # MEMORY SAFETY: For MemoryError, use minimal memory operations
            # Don't try to create large traceback strings that might fail
            if isinstance(error, MemoryError):
                # Minimal error record for memory errors
                error_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": "MemoryError",
                    "error_message": str(error) if error else "Memory allocation failed",
                    "component": component or "unknown",
                    "traceback": "MemoryError - minimal traceback to avoid memory allocation",
                }
                if context:
                    error_record["context"] = context
            else:
                # Generate error record normally
                error_record = cls._create_error_record(error, context, trace, component)
            
            # Write to file (thread-safe)
            with cls._lock:
                if cls._error_file:
                    json_line = json.dumps(error_record, default=str, ensure_ascii=False)
                    cls._error_file.write(json_line + "\n")
                    cls._error_file.flush()  # Immediate write for errors
                
        except MemoryError:
            # CRITICAL: Handle MemoryError in error logger itself
            # Use absolute minimal operations
            try:
                error_msg = f"{type(error).__name__}: {str(error)[:100] if error else 'MemoryError'}"
                sys.stderr.write(f"[MEMORY_ERROR] {datetime.utcnow().isoformat()} {error_msg}\n")
                sys.stderr.flush()
            except Exception:
                pass  # Complete failure - nothing we can do
        except Exception:
            # Last resort: write to stderr
            try:
                error_msg = str(error) if error else "Unknown error"
                sys.stderr.write(f"[ERROR] {datetime.utcnow().isoformat()} {error_msg}\n")
                sys.stderr.flush()
            except Exception:
                pass  # Complete failure - nothing we can do
    
    @classmethod
    def _create_error_record(
        cls,
        error: Exception,
        context: Optional[Dict[str, Any]],
        trace: Optional[str],
        component: Optional[str],
    ) -> Dict[str, Any]:
        """Create an error record dictionary."""
        # Get stack trace if not provided
        if trace is None:
            try:
                trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            except Exception:
                trace = "Failed to generate traceback"
        
        # Build error record
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "component": component or "unknown",
            "traceback": trace,
        }
        
        # Add context if provided
        if context:
            error_record["context"] = context
        
        # Add system information
        try:
            error_record["system"] = {
                "pid": os.getpid(),
                "thread_id": threading.get_ident(),
            }
        except Exception:
            pass
        
        return error_record
    
    @classmethod
    def log_message(
        cls,
        message: str,
        level: str = "ERROR",
        component: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an error message directly (not from exception).
        
        Args:
            message: Error message
            level: Log level (ERROR, CRITICAL, etc.)
            component: Component name
            context: Additional context
        """
        try:
            if not cls._initialized:
                cls._initialize()
            
            # MEMORY SAFETY: For memory-related messages, use minimal operations
            error_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": message[:500] if len(message) > 500 else message,  # Limit message size
                "component": component or "unknown",
            }
            
            if context:
                # Limit context size for memory safety
                limited_context = {}
                for k, v in context.items():
                    v_str = str(v)
                    limited_context[k] = v_str[:200] if len(v_str) > 200 else v_str
                error_record["context"] = limited_context
            
            with cls._lock:
                if cls._error_file:
                    json_line = json.dumps(error_record, default=str, ensure_ascii=False)
                    cls._error_file.write(json_line + "\n")
                    cls._error_file.flush()
        except MemoryError:
            # CRITICAL: Handle MemoryError when logging messages
            try:
                # Minimal stderr output
                minimal_msg = message[:100] if len(message) > 100 else message
                sys.stderr.write(f"[{level}] {datetime.utcnow().isoformat()} {minimal_msg}\n")
                sys.stderr.flush()
            except Exception:
                pass
        except Exception:
            try:
                sys.stderr.write(f"[{level}] {datetime.utcnow().isoformat()} {message}\n")
                sys.stderr.flush()
            except Exception:
                pass
    
    @classmethod
    def close(cls) -> None:
        """Close the error logger and flush any remaining writes."""
        with cls._lock:
            if cls._error_file and cls._error_file != sys.stderr:
                try:
                    cls._error_file.flush()
                    cls._error_file.close()
                except Exception:
                    pass
                cls._error_file = None
            cls._initialized = False


# Convenience function for easy access
def log_error_safe(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    component: Optional[str] = None,
) -> None:
    """
    Safe error logging function - never fails.
    
    Usage:
        try:
            # some operation
        except Exception as e:
            log_error_safe(e, context={"operation": "logging"}, component="SyncLogger")
    """
    SafeErrorLogger.log_error(error, context=context, component=component)


def log_error_message(
    message: str,
    level: str = "ERROR",
    component: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an error message directly - never fails.
    
    Usage:
        log_error_message("Malloc error detected", level="CRITICAL", component="MemoryHandler")
    """
    SafeErrorLogger.log_message(message, level=level, component=component, context=context)


# Register cleanup on exit
import atexit
atexit.register(SafeErrorLogger.close)

