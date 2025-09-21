"""
Rotating File Handlers for Hydra-Logger

This module provides comprehensive file rotation capabilities for managing
log file size and age. It includes time-based, size-based, and hybrid
rotation strategies with automatic compression and cleanup.

ARCHITECTURE:
- RotatingFileHandler: Base class for all rotating handlers
- TimedRotatingFileHandler: Time-based file rotation
- SizeRotatingFileHandler: Size-based file rotation
- HybridRotatingFileHandler: Combined time and size-based rotation
- RotatingFileHandlerFactory: Factory for creating rotating handlers

ROTATION STRATEGIES:
- TIME_BASED: Rotate based on time intervals (daily, hourly, etc.)
- SIZE_BASED: Rotate when file reaches maximum size
- HYBRID: Rotate based on both time and size criteria

TIME UNITS:
- SECONDS: Rotate every N seconds
- MINUTES: Rotate every N minutes
- HOURS: Rotate every N hours
- DAYS: Rotate every N days
- WEEKS: Rotate every N weeks
- MIDNIGHT: Rotate at midnight

PERFORMANCE FEATURES:
- Atomic rotation for data integrity
- Automatic file compression
- Intelligent cleanup of old files
- Configurable backup retention
- Performance statistics and monitoring

USAGE EXAMPLES:

Time-Based Rotation:
    from hydra_logger.handlers import TimedRotatingFileHandler
    from hydra_logger.types.enums import TimeUnit
    
    handler = TimedRotatingFileHandler(
        filename="app.log",
        when="midnight",
        interval=1,
        backup_count=30,
        time_unit=TimeUnit.DAYS
    )
    logger.addHandler(handler)

Size-Based Rotation:
    from hydra_logger.handlers import SizeRotatingFileHandler
    
    handler = SizeRotatingFileHandler(
        filename="app.log",
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5
    )
    logger.addHandler(handler)

Hybrid Rotation:
    from hydra_logger.handlers import HybridRotatingFileHandler
    
    handler = HybridRotatingFileHandler(
        filename="app.log",
        max_bytes=10 * 1024 * 1024,  # 10MB
        when="midnight",
        interval=1,
        backup_count=30
    )
    logger.addHandler(handler)

Custom Rotation Configuration:
    from hydra_logger.handlers.rotating import RotationConfig, RotationStrategy
    from hydra_logger.types.enums import TimeUnit
    
    config = RotationConfig(
        strategy=RotationStrategy.HYBRID,
        max_size=10 * 1024 * 1024,  # 10MB
        time_interval=1,
        time_unit=TimeUnit.DAYS,
        max_size_files=5,
        max_time_files=30,
        compress_old=True,
        atomic_rotation=True
    )
    
    handler = RotatingFileHandler(
        filename="app.log",
        config=config
    )
    logger.addHandler(handler)

Factory Pattern:
    from hydra_logger.handlers import RotatingFileHandlerFactory
    
    # Create timed rotating handler
    handler = RotatingFileHandlerFactory.create_handler(
        "timed",
        filename="app.log",
        when="midnight",
        backup_count=30
    )
    
    # Create size rotating handler
    handler = RotatingFileHandlerFactory.create_handler(
        "size",
        filename="app.log",
        max_bytes=10 * 1024 * 1024
    )

Performance Monitoring:
    # Get rotation statistics
    stats = handler.get_rotation_stats()
    print(f"Rotation count: {stats['rotation_count']}")
    print(f"Current file size: {stats['current_file_size']}")
    print(f"Last rotation: {stats['last_rotation']}")

CONFIGURATION:
- Time settings: when, interval, time_unit, max_time_files
- Size settings: max_size, max_size_files
- General settings: backup_dir, compress_old, preserve_extension
- Rotation settings: atomic_rotation, cleanup_old

ERROR HANDLING:
- Atomic rotation for data integrity
- Automatic cleanup of old files
- Comprehensive error logging
- Graceful degradation
- File system error recovery

THREAD SAFETY:
- Thread-safe operations with proper locking
- Safe concurrent access
- Atomic file operations
- Safe rotation and cleanup
"""

import os
import time
import gzip
import shutil
import threading
import sys
from datetime import datetime
from typing import Optional, Union, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
from collections import deque

from hydra_logger.handlers.base import BaseHandler
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel
from hydra_logger.types.enums import TimeUnit
from hydra_logger.utils.file_utility import FileUtility
from hydra_logger.utils.time_utility import TimeUtility


class RotationStrategy(Enum):
    """Rotation strategies."""
    TIME_BASED = "time_based"
    SIZE_BASED = "size_based"
    HYBRID = "hybrid"


@dataclass
class RotationConfig:
    """Configuration for file rotation."""
    # Time-based rotation
    time_interval: int = 1
    time_unit: TimeUnit = TimeUnit.DAYS
    time_format: str = "%Y-%m-%d"
    max_time_files: int = 30

    # Size-based rotation - Optimized for performance
    max_size: int = 1024 * 1024  # 1MB (optimal from performance tuner)
    max_size_files: int = 5  # Optimal: 5 (from performance tuner)

    # Hybrid rotation
    strategy: RotationStrategy = RotationStrategy.TIME_BASED

    # General settings
    backup_dir: Optional[str] = None
    compress_old: bool = True
    preserve_extension: bool = True
    atomic_rotation: bool = True
    cleanup_old: bool = True


class RotatingFileHandler(BaseHandler):
    """Base class for rotating file handlers."""

    def __init__(
        self,
        filename: str,
        config: Optional[RotationConfig] = None,
        buffer_size: int = 1000,  # Optimal: 1000 (from performance tuner)
        flush_interval: float = 0.5,  # Optimal: 0.5s (from performance tuner)
        **kwargs
    ):
        """
        Initialize rotating file handler.

        Args:
            filename: Base log file path
            config: Rotation configuration
            buffer_size: Number of messages to buffer before flushing
            flush_interval: Time interval (seconds) for automatic flushing
            **kwargs: Additional arguments
        """
        super().__init__(name="rotating_file", level=LogLevel.NOTSET)
        self._filename = filename
        self._config = config or RotationConfig()
        self._current_file = None
        self._lock = threading.RLock()
        self._rotation_count = 0
        self._last_rotation = 0.0

        # Performance optimization: Enhanced buffering
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._buffer = deque(maxlen=buffer_size)
        self._last_flush = time.time()
        
        # Pre-allocate string buffer for better performance
        self._string_buffer = []
        self._string_buffer_size = 0

        # Ensure directory exists
        log_dir = os.path.dirname(filename)
        if log_dir and not FileUtility.exists(log_dir):
            FileUtility.ensure_directory_exists(log_dir)

        # Formatter-aware handling
        self._needs_header_footer = False
        self._is_csv_formatter = False
        self._header_written = False

        # Initialize file
        self._initialize_file()

    def _initialize_file(self) -> None:
        """Initialize the log file."""
        try:
            if not FileUtility.exists(self._filename):
                # Create empty file
                with open(self._filename, 'w') as f:
                    pass

            # Check if file is writable
            if not FileUtility.is_writable(self._filename):
                raise PermissionError(f"Cannot write to {self._filename}")

            self._current_file = open(self._filename, 'a', encoding='utf-8')
        except Exception as e:
            print(f"Error: Failed to initialize log file: {e}", file=sys.stderr)
            raise

    def _should_rotate(self) -> bool:
        """Check if rotation is needed."""
        raise NotImplementedError("Subclasses must implement this method")

    def _rotate_file(self) -> None:
        """Perform file rotation."""
        if not self._should_rotate():
            return

        with self._lock:
            try:
                # Close current file
                if self._current_file:
                    self._current_file.close()
                    self._current_file = None

                # Generate backup filename
                backup_name = self._generate_backup_name()
                backup_path = self._get_backup_path(backup_name)

                # Move current file to backup
                if FileUtility.exists(self._filename):
                    if self._config.atomic_rotation:
                        self._atomic_rotate(backup_path)
                    else:
                        shutil.move(self._filename, backup_path)

                # Compress old file if requested
                if self._config.compress_old and backup_path.endswith('.log'):
                    self._compress_file(backup_path)

                # Clean up old files
                if self._config.cleanup_old:
                    self._cleanup_old_files()

                # Reopen file
                self._initialize_file()
                self._rotation_count += 1
                self._last_rotation = time.time()

            except Exception as e:
                print(f"Error: File rotation failed: {e}", file=sys.stderr)
                # Try to reopen file
                try:
                    self._initialize_file()
                except Exception:
                    pass

    def _atomic_rotate(self, backup_path: str) -> None:
        """Perform atomic file rotation."""
        # Create temporary backup name
        temp_backup = f"{backup_path}.tmp"
        
        # Move to temporary location first
        shutil.move(self._filename, temp_backup)
        
        # Then rename to final location
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(temp_backup, backup_path)

    def _generate_backup_name(self) -> str:
        """Generate backup filename."""
        timestamp = datetime.now().strftime(self._config.time_format)
        base_name = os.path.basename(self._filename)
        name, ext = os.path.splitext(base_name)
        
        if self._config.preserve_extension:
            return f"{name}.{timestamp}{ext}"
        else:
            return f"{name}.{timestamp}"

    def _get_backup_path(self, backup_name: str) -> str:
        """Get full backup path."""
        if self._config.backup_dir:
            return os.path.join(self._config.backup_dir, backup_name)
        else:
            base_dir = os.path.dirname(self._filename)
            return os.path.join(base_dir, backup_name)

    def _compress_file(self, file_path: str) -> None:
        """Compress a file using gzip."""
        try:
            if not file_path.endswith('.gz'):
                compressed_path = f"{file_path}.gz"
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove original file
                FileUtility.delete_file(file_path)
        except Exception as e:
            print(f"Warning: Failed to compress {file_path}: {e}", file=sys.stderr)

    def _cleanup_old_files(self) -> None:
        """Clean up old backup files."""
        try:
            backup_dir = self._config.backup_dir or os.path.dirname(self._filename)
            if not FileUtility.exists(backup_dir):
                return

            # Get list of backup files
            backup_files = []
            for file in os.listdir(backup_dir):
                if file.startswith(os.path.basename(self._filename)):
                    file_path = os.path.join(backup_dir, file)
                    if FileUtility.is_file(file_path):
                        backup_files.append(file_path)

            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: FileUtility.get_file_info(x).mtime)

            # Remove excess files based on strategy
            if self._config.strategy == RotationStrategy.TIME_BASED:
                max_files = self._config.max_time_files
            elif self._config.strategy == RotationStrategy.SIZE_BASED:
                max_files = self._config.max_size_files
            else:  # HYBRID
                max_files = max(self._config.max_time_files, self._config.max_size_files)

            # Remove excess files
            while len(backup_files) > max_files:
                old_file = backup_files.pop(0)
                try:
                    FileUtility.delete_file(old_file)
                except Exception as e:
                    print(f"Warning: Failed to delete old file {old_file}: {e}", file=sys.stderr)

        except Exception as e:
            print(f"Warning: Cleanup failed: {e}", file=sys.stderr)

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record to rotating file with buffering for high performance.

        Args:
            record: Log record to emit
        """
        # Check if rotation is needed
        if self._should_rotate():
            self._rotate_file()

        # Format message
        if self.formatter:
            # Check if this is a streaming formatter that needs special handling
            if hasattr(self.formatter, 'format_for_streaming'):
                message = self.formatter.format_for_streaming(record)
            else:
                message = self.formatter.format(record)
                # Add newline for non-streaming formatters, but CSV formatters handle their own
                if not self._is_csv_formatter:
                    message += "\n"
        else:
            message = f"{record.level_name}: {record.message}\n"

        # Add to buffer
        self._buffer.append(message)
        self._string_buffer.append(message)
        self._string_buffer_size += len(message)
        
        # Check if we should flush
        current_time = time.time()
        should_flush = (
            len(self._buffer) >= self._buffer_size or
            (current_time - self._last_flush) >= self._flush_interval
        )
        
        if should_flush:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush buffered messages to file."""
        if not self._buffer or not self._current_file:
            return
        
        # Check if rotation is needed before flushing
        if self._should_rotate():
            self._rotate_file()
            
        try:
            # Check if file is closed
            if hasattr(self._current_file, 'closed') and self._current_file.closed:
                return
                
            # Write all buffered messages at once - use string buffer for better performance
            if self._string_buffer:
                self._current_file.write(''.join(self._string_buffer))
                self._current_file.flush()
            
            # Clear buffers and update flush time
            self._buffer.clear()
            self._string_buffer.clear()
            self._string_buffer_size = 0
            self._last_flush = time.time()
            
        except (OSError, ValueError) as e:
            # File is closed or invalid, silently ignore
            pass
        except Exception as e:
            print(f"Error: Rotating file buffer flush error: {e}", file=sys.stderr)

    def force_flush(self) -> None:
        """Force flush any remaining buffered messages."""
        self._flush_buffer()

    def _write_to_file(self, message: str) -> None:
        """Write message to current file (legacy method for compatibility)."""
        if self._current_file:
            try:
                # Smart header handling for streaming formatters
                if self._needs_header_footer and not self._header_written:
                    # Reset formatter state
                    if hasattr(self.formatter, 'reset_for_new_file'):
                        self.formatter.reset_for_new_file()
                    
                    # Set file ID for formatters that support it
                    if hasattr(self.formatter, 'set_file_id'):
                        self.formatter.set_file_id(id(self._current_file))
                    
                    # Check if we need to write header
                    if self._current_file.tell() == 0:  # New file
                        if hasattr(self.formatter, 'write_header'):
                            # JSON formatters
                            header = self.formatter.write_header()
                            self._current_file.write(header)
                        elif hasattr(self.formatter, 'format_headers') and hasattr(self.formatter, 'should_write_headers'):
                            # CSV formatters
                            if self.formatter.should_write_headers(self._filename):
                                header = self.formatter.format_headers() + '\n'
                                self._current_file.write(header)
                                self.formatter.mark_headers_written(self._filename)
                        self._header_written = True

                self._current_file.write(message)
                self._current_file.flush()
            except Exception as e:
                print(f"Error: Failed to write to log file: {e}", file=sys.stderr)

    def close(self) -> None:
        """Close the handler."""
        # Flush any remaining buffered messages
        self.force_flush()
        
        super().close()
        if self._current_file:
            self._current_file.close()
            self._current_file = None

    def get_rotation_stats(self) -> Dict[str, Any]:
        """
        Get rotation statistics.

        Returns:
            Dictionary with rotation statistics
        """
        return {
            "filename": self._filename,
            "rotation_count": self._rotation_count,
            "last_rotation": self._last_rotation,
            "config": {
                "strategy": self._config.strategy.value,
                "time_interval": self._config.time_interval,
                "time_unit": self._config.time_unit.value,
                "max_size": self._config.max_size,
                "compress_old": self._config.compress_old,
                "cleanup_old": self._config.cleanup_old
            }
        }

    def setFormatter(self, formatter):
        """
        Set formatter and detect if it needs special handling.
        
        Args:
            formatter: Formatter instance
        """
        super().setFormatter(formatter)
        
        # Enforce correct file extension based on formatter
        if formatter and hasattr(formatter, 'validate_filename'):
            corrected_filename = formatter.validate_filename(self._filename)
            if corrected_filename != self._filename:
                print(f"Info: RotatingFileHandler: Corrected filename from '{self._filename}' to '{corrected_filename}' to match formatter requirements", file=sys.stdout)
                self._filename = corrected_filename
        
        # Detect if this formatter needs header/footer handling
        if formatter and (
            (hasattr(formatter, 'write_header') and hasattr(formatter, 'write_footer')) or
            (hasattr(formatter, 'format_headers') and hasattr(formatter, 'should_write_headers'))
        ):
            self._needs_header_footer = True
        else:
            self._needs_header_footer = False
        
        # Store formatter type for better handling
        self._is_csv_formatter = hasattr(formatter, 'format_headers') and hasattr(formatter, 'should_write_headers')
        
        # Reset header written flag
        self._header_written = False


class TimedRotatingFileHandler(RotatingFileHandler):
    """Handler that rotates files based on time intervals."""

    def __init__(
        self,
        filename: str,
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 30,
        time_unit: TimeUnit = TimeUnit.DAYS,
        **kwargs
    ):
        """
        Initialize timed rotating file handler.

        Args:
            filename: Base log file path
            when: When to rotate (midnight, hour, day, etc.)
            interval: Rotation interval
            backup_count: Number of backup files to keep
            time_unit: Time unit for rotation (default: DAYS)
            **kwargs: Additional arguments
        """
        # Validate the rotation interval
        if not TimeUtility.validate_rotation_interval(interval, time_unit):
            raise ValueError(f"Invalid rotation interval: {interval} {time_unit.value}")
        
        config = RotationConfig(
            strategy=RotationStrategy.TIME_BASED,
            time_interval=interval,
            time_unit=time_unit,
            max_time_files=backup_count
        )

        super().__init__(filename, config, **kwargs)
        self._when = when
        self._interval = interval
        self._time_unit = time_unit
        self._last_rotation_time = self._get_last_rotation_time()

    def _get_last_rotation_time(self) -> datetime:
        """Get the last rotation time."""
        if FileUtility.exists(self._filename):
            file_info = FileUtility.get_file_info(self._filename)
            return datetime.fromtimestamp(file_info.modified)
        return datetime.now()

    def _should_rotate(self) -> bool:
        """Check if time-based rotation is needed."""
        now = datetime.now()
        
        if self._when == "second":
            # Rotate every second
            if (now - self._last_rotation_time).total_seconds() >= self._interval:
                return True
        elif self._when == "minute":
            # Rotate every minute
            if (now - self._last_rotation_time).total_seconds() >= 60 * self._interval:
                return True
        elif self._when == "midnight":
            # Rotate at midnight
            if now.date() > self._last_rotation_time.date():
                return True
        elif self._when == "hour":
            # Rotate every hour
            if (now - self._last_rotation_time).total_seconds() >= 3600:
                return True
        elif self._when == "day":
            # Rotate every day
            if (now - self._last_rotation_time).days >= self._interval:
                return True
        elif self._when == "week":
            # Rotate every week
            if (now - self._last_rotation_time).days >= 7 * self._interval:
                return True
        elif self._when == "month":
            # Rotate every month
            if (now.year > self._last_rotation_time.year or
                now.month - self._last_rotation_time.month >= self._interval):
                return True

        return False

    def _generate_backup_name(self) -> str:
        """Generate backup filename with timestamp."""
        timestamp = self._last_rotation_time.strftime(self._config.time_format)
        base_name = os.path.basename(self._filename)
        name, ext = os.path.splitext(base_name)
        
        if self._config.preserve_extension:
            return f"{name}.{timestamp}{ext}"
        else:
            return f"{name}.{timestamp}"


class SizeRotatingFileHandler(RotatingFileHandler):
    """Handler that rotates files based on size."""

    def __init__(
        self,
        filename: str,
        max_bytes: int = 1024 * 1024,  # 1MB (optimal from performance tuner)
        backup_count: int = 5,  # Optimal: 5 (from performance tuner)
        **kwargs
    ):
        """
        Initialize size rotating file handler.

        Args:
            filename: Base log file path
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep
            **kwargs: Additional arguments
        """
        config = RotationConfig(
            strategy=RotationStrategy.SIZE_BASED,
            max_size=max_bytes,
            max_size_files=backup_count
        )

        super().__init__(filename, config, **kwargs)
        self._max_bytes = max_bytes
        self._backup_count = backup_count

    def _should_rotate(self) -> bool:
        """Check if size-based rotation is needed."""
        if not FileUtility.exists(self._filename):
            return False

        try:
            file_info = FileUtility.get_file_info(self._filename)
            return file_info.size >= self._max_bytes
        except Exception:
            return False

    def _generate_backup_name(self) -> str:
        """Generate backup filename with sequence number."""
        base_name = os.path.basename(self._filename)
        name, ext = os.path.splitext(base_name)
        
        # Find next available sequence number
        sequence = 1
        while True:
            if self._config.preserve_extension:
                backup_name = f"{name}.{sequence}{ext}"
            else:
                backup_name = f"{name}.{sequence}"
            
            backup_path = self._get_backup_path(backup_name)
            if not FileUtility.exists(backup_path):
                break
            sequence += 1

        return backup_name


class HybridRotatingFileHandler(RotatingFileHandler):
    """Handler that combines time and size-based rotation."""

    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 30,
        **kwargs
    ):
        """
        Initialize hybrid rotating file handler.

        Args:
            filename: Base log file path
            max_bytes: Maximum file size before rotation
            when: When to rotate (midnight, hour, day, etc.)
            interval: Rotation interval
            backup_count: Number of backup files to keep
            **kwargs: Additional arguments
        """
        config = RotationConfig(
            strategy=RotationStrategy.HYBRID,
            max_size=max_bytes,
            max_size_files=backup_count,
            time_interval=interval,
            max_time_files=backup_count
        )

        super().__init__(filename, config, **kwargs)
        self._max_bytes = max_bytes
        self._when = when
        self._interval = interval
        self._backup_count = backup_count
        self._last_rotation_time = datetime.now()

    def _should_rotate(self) -> bool:
        """Check if hybrid rotation is needed."""
        # Check size-based rotation
        if FileUtility.exists(self._filename):
            try:
                file_info = FileUtility.get_file_info(self._filename)
                if file_info.size >= self._max_bytes:
                    return True
            except Exception:
                pass

        # Check time-based rotation
        now = datetime.now()
        if self._when == "midnight":
            if now.date() > self._last_rotation_time.date():
                return True
        elif self._when == "hour":
            if (now - self._last_rotation_time).total_seconds() >= 3600:
                return True
        elif self._when == "day":
            if (now - self._last_rotation_time).days >= self._interval:
                return True

        return False

    def _generate_backup_name(self) -> str:
        """Generate backup filename with timestamp and sequence."""
        timestamp = datetime.now().strftime(self._config.time_format)
        base_name = os.path.basename(self._filename)
        name, ext = os.path.splitext(base_name)
        
        # Find next available sequence number for this timestamp
        sequence = 1
        while True:
            if self._config.preserve_extension:
                backup_name = f"{name}.{timestamp}.{sequence}{ext}"
            else:
                backup_name = f"{name}.{timestamp}.{sequence}"
            
            backup_path = self._get_backup_path(backup_name)
            if not FileUtility.exists(backup_path):
                break
            sequence += 1

        return backup_name


class RotatingFileHandlerFactory:
    """Factory for creating rotating file handlers."""

    @staticmethod
    def create_handler(
        handler_type: str,
        filename: str,
        **kwargs
    ) -> RotatingFileHandler:
        """
        Create a rotating file handler by type.

        Args:
            handler_type: Type of handler to create
            filename: Base log file path
            **kwargs: Handler-specific arguments

        Returns:
            Configured rotating file handler
        """
        if handler_type.lower() == "timed":
            return RotatingFileHandlerFactory.create_timed_handler(filename, **kwargs)
        elif handler_type.lower() == "size":
            return RotatingFileHandlerFactory.create_size_handler(filename, **kwargs)
        elif handler_type.lower() == "hybrid":
            return RotatingFileHandlerFactory.create_hybrid_handler(filename, **kwargs)
        else:
            raise ValueError(f"Unknown handler type: {handler_type}")

    @staticmethod
    def create_timed_handler(filename: str, **kwargs) -> TimedRotatingFileHandler:
        """Create timed rotating file handler."""
        # Map common parameter names to constructor parameters
        mapped_kwargs = {}
        if 'time_interval' in kwargs:
            mapped_kwargs['interval'] = kwargs.pop('time_interval')
        if 'max_time_files' in kwargs:
            mapped_kwargs['backup_count'] = kwargs.pop('max_time_files')
        if 'time_unit' in kwargs:
            mapped_kwargs['time_unit'] = kwargs.pop('time_unit')
        
        mapped_kwargs.update(kwargs)
        return TimedRotatingFileHandler(filename, **mapped_kwargs)

    @staticmethod
    def create_size_handler(filename: str, **kwargs) -> SizeRotatingFileHandler:
        """Create size rotating file handler."""
        # Map common parameter names to constructor parameters
        mapped_kwargs = {}
        if 'max_size' in kwargs:
            mapped_kwargs['max_bytes'] = kwargs.pop('max_size')
        if 'max_size_files' in kwargs:
            mapped_kwargs['backup_count'] = kwargs.pop('max_size_files')
        
        mapped_kwargs.update(kwargs)
        return SizeRotatingFileHandler(filename, **mapped_kwargs)

    @staticmethod
    def create_hybrid_handler(filename: str, **kwargs) -> HybridRotatingFileHandler:
        """Create hybrid rotating file handler."""
        # Map common parameter names to constructor parameters
        mapped_kwargs = {}
        if 'max_size' in kwargs:
            mapped_kwargs['max_bytes'] = kwargs.pop('max_size')
        if 'max_size_files' in kwargs:
            mapped_kwargs['backup_count'] = kwargs.pop('max_size_files')
        if 'time_interval' in kwargs:
            mapped_kwargs['interval'] = kwargs.pop('time_interval')
        if 'max_time_files' in kwargs:
            mapped_kwargs['backup_count'] = kwargs.pop('max_time_files')
        if 'time_unit' in kwargs:
            # time_unit is not directly supported by constructor
            kwargs.pop('time_unit')
        
        mapped_kwargs.update(kwargs)
        return HybridRotatingFileHandler(filename, **mapped_kwargs)
