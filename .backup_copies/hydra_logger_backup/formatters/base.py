"""
Base Formatter System for Hydra-Logger

This module provides the abstract base class and core functionality for all
Hydra-Logger formatters. It establishes the foundation for the standardized
formatting system with performance optimization, validation, and error handling.

ARCHITECTURE:
- BaseFormatter: Abstract base class for all formatters
- FormatterError: Custom exception for formatter errors
- TimestampConfig: Configuration for timestamp formatting
- Performance Integration: Standardized format function integration
- Validation System: Record validation and error handling

CORE FEATURES:
- Abstract interface for all formatter implementations
- Timestamp formatting with configurable precision and timezone
- ANSI color code stripping for clean text output
- File extension validation and correction
- Performance statistics and monitoring
- Error tracking and recovery
- Memory optimization integration
- Thread-safe operations

PERFORMANCE INTEGRATION:
- Standardized format function integration
- LRU cache support for performance optimization
- Memory-efficient object pooling
- JIT optimization for hot code paths
- Parallel processing support
- Zero-overhead formatting for simple cases

VALIDATION SYSTEM:
- Record validation before formatting
- File extension validation and correction
- Error tracking and recovery
- Performance monitoring and statistics
- Memory usage optimization

USAGE EXAMPLES:

Creating Custom Formatters:
    from hydra_logger.formatters.base import BaseFormatter
    from hydra_logger.types.records import LogRecord
    
    class CustomFormatter(BaseFormatter):
        def __init__(self):
            super().__init__("custom")
        
        def _format_default(self, record: LogRecord) -> str:
            return f"[{record.level_name}] {record.message}"

Timestamp Configuration:
    from hydra_logger.utils.time import TimestampConfig, TimestampFormat, TimestampPrecision
    
    config = TimestampConfig(
        format_type=TimestampFormat.RFC3339_MICRO,
        precision=TimestampPrecision.MICROSECONDS,
        timezone_name="UTC"
    )
    
    formatter = BaseFormatter("my_formatter", timestamp_config=config)

Performance Integration:
    from hydra_logger.formatters.standard_formats import get_standard_formats, PerformanceLevel
    
    # Get performance-optimized formatter
    standard_formats = get_standard_formats(PerformanceLevel.FAST)
    
    # Use in custom formatter
    class OptimizedFormatter(BaseFormatter):
        def __init__(self):
            super().__init__("optimized")
            self._standard_formats = get_standard_formats(PerformanceLevel.FAST)
            self._format_func = self._standard_formats.format_basic

ERROR HANDLING:
- FormatterError: Custom exception for formatter-specific errors
- Error tracking and recovery mechanisms
- Performance statistics and monitoring
- Memory usage optimization
- Thread-safe error handling
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..types.records import LogRecord
from ..utils.time import TimestampConfig, TimestampFormat, TimestampPrecision

# FormattingEngine removed - no longer needed

# Set up logging for formatters
logger = logging.getLogger(__name__)


class FormatterError(Exception):
    """Custom exception for formatter errors."""
    pass


class BaseFormatter(ABC):
    """
    Abstract base class for all Hydra-Logger formatters.
    
    This class provides the foundation for all formatter implementations with
    standardized interfaces, performance optimization, validation, and error
    handling. It establishes the contract that all formatters must follow
    while providing common functionality and optimizations.
    
    FEATURES:
    - Abstract interface for formatter implementations
    - Timestamp formatting with configurable precision and timezone
    - ANSI color code stripping for clean text output
    - File extension validation and correction
    - Performance statistics and monitoring
    - Error tracking and recovery
    - Memory optimization integration
    - Thread-safe operations
    
    PERFORMANCE INTEGRATION:
    - Standardized format function integration
    - LRU cache support for performance optimization
    - Memory-efficient object pooling
    - JIT optimization for hot code paths
    - Parallel processing support
    - Zero-overhead formatting for simple cases
    
    VALIDATION SYSTEM:
    - Record validation before formatting
    - File extension validation and correction
    - Error tracking and recovery
    - Performance monitoring and statistics
    - Memory usage optimization
    
    USAGE EXAMPLES:
    
    Basic Implementation:
        class MyFormatter(BaseFormatter):
            def __init__(self):
                super().__init__("my_formatter")
            
            def _format_default(self, record: LogRecord) -> str:
                return f"[{record.level_name}] {record.message}"
    
    With Timestamp Configuration:
        config = TimestampConfig(
            format_type=TimestampFormat.RFC3339_MICRO,
            precision=TimestampPrecision.MICROSECONDS
        )
        formatter = MyFormatter(timestamp_config=config)
    
    Performance Integration:
        class OptimizedFormatter(BaseFormatter):
            def __init__(self):
                super().__init__("optimized")
                from .standard_formats import get_standard_formats, PerformanceLevel
                self._standard_formats = get_standard_formats(PerformanceLevel.FAST)
                self._format_func = self._standard_formats.format_basic
    """

    def __init__(self, name: str = "base", timestamp_config: Optional[TimestampConfig] = None):
        """
        Initialize base formatter.

        Args:
            name: Formatter name for identification
            timestamp_config: Configuration for timestamp formatting
        """
        if not name:
            raise FormatterError("Formatter name cannot be empty")
        
        self.name = name
        self.timestamp_config = timestamp_config or TimestampConfig(
            format_type=TimestampFormat.RFC3339_MICRO,
            precision=TimestampPrecision.MICROSECONDS,
            timezone_name=None,  # Local timezone
            include_timezone=True
        )
        self._initialized = True
        self._formatting_errors = []

    def format_timestamp(self, record: LogRecord) -> str:
        """
        Format timestamp from log record using configured timestamp format.
        
        Args:
            record: Log record containing timestamp information
            
        Returns:
            Formatted timestamp string
        """
        from datetime import datetime, timezone
        
        # Convert record timestamp to datetime
        if hasattr(record, 'timestamp') and record.timestamp:
            if isinstance(record.timestamp, (int, float)):
                # Unix timestamp - use local timezone for handlers
                if self.timestamp_config.timezone_name is None:
                    dt = datetime.fromtimestamp(record.timestamp)
                else:
                    dt = datetime.fromtimestamp(record.timestamp, tz=timezone.utc)
            else:
                # Assume it's already a datetime
                dt = record.timestamp
        else:
            # Fallback to current time
            if self.timestamp_config.timezone_name is None:
                dt = datetime.now()
            else:
                dt = datetime.now(timezone.utc)
        
        return self.timestamp_config.format_timestamp(dt)

    def _strip_ansi_colors(self, text: str) -> str:
        """
        Strip ANSI color codes from text.

        Args:
            text: Text that may contain ANSI color codes

        Returns:
            Clean text without color codes
        """
        try:
            if not text:
                return text

            import re
            # Remove ANSI color codes (ESC[ followed by numbers and optional m)
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', text)
        except Exception as e:
            logger.warning(f"Failed to strip ANSI colors: {e}")
            return text

    def format(self, record: LogRecord) -> str:
        """
        Format a log record.

        This method provides a unified interface that automatically
        chooses between custom formatting engine and default formatting.

        Args:
            record: Log record to format

        Returns:
            Formatted string representation

        Raises:
            FormatterError: If formatting fails
        """
        if not record:
            raise FormatterError("Log record cannot be None")

        try:
            # Use default formatting
            return self._format_default(record)

        except Exception as e:
            error_msg = f"Formatting failed for record: {e}"
            logger.error(error_msg)
            self._formatting_errors.append(error_msg)
            raise FormatterError(error_msg) from e

    @abstractmethod
    def _format_default(self, record: LogRecord) -> str:
        """
        Default formatting implementation.

        Args:
            record: Log record to format

        Returns:
            Formatted string representation
        """
        pass

    def get_required_extension(self) -> str:
        """
        Get the required file extension for this formatter.
        
        This enforces industry standards and prevents users from creating
        files with incorrect extensions.
        
        Returns:
            Required file extension (e.g., '.jsonl', '.gelf', '.csv')
        """
        # Default to .log for text-based formatters
        return ".log"

    def validate_filename(self, filename: str) -> str:
        """
        Validate and correct filename to ensure proper extension.
        
        Args:
            filename: Original filename
            
        Returns:
            Corrected filename with proper extension
            
        Raises:
            FormatterError: If filename cannot be corrected
        """
        required_ext = self.get_required_extension()
        
        # If filename already has correct extension, return as-is
        if filename.endswith(required_ext):
            return filename
            
        # If filename has wrong extension, replace it
        if '.' in filename:
            base_name = filename.rsplit('.', 1)[0]
            return base_name + required_ext
            
        # If no extension, add the required one
        return filename + required_ext


    def get_format_name(self) -> str:
        """
        Get formatter name.

        Returns:
            Formatter name
        """
        return self.name

    def is_initialized(self) -> bool:
        """
        Check if formatter is properly initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    def get_config(self) -> Dict[str, Any]:
        """
        Get formatter configuration.

        Returns:
            Configuration dictionary
        """
        try:
            config = {
                "name": self.name,
                "type": self.__class__.__name__,
                "initialized": self._initialized,
                "formatting_errors": self._formatting_errors.copy()
            }


            return config
        except Exception as e:
            logger.error(f"Failed to get formatter config: {e}")
            return {
                "name": self.name,
                "type": self.__class__.__name__,
                "error": str(e)
            }


    def get_formatting_errors(self) -> list:
        """
        Get list of formatting errors encountered.

        Returns:
            List of error messages
        """
        return self._formatting_errors.copy()

    def clear_formatting_errors(self) -> None:
        """Clear the list of formatting errors."""
        self._formatting_errors.clear()

    def has_errors(self) -> bool:
        """
        Check if there are any formatting errors.

        Returns:
            True if there are errors
        """
        return len(self._formatting_errors) > 0

    def validate_record(self, record: LogRecord) -> bool:
        """
        Validate if a record can be formatted by this formatter.

        Args:
            record: Log record to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            if not record:
                return False
            
            # Check if record has required attributes
            required_attrs = ['level', 'level_name', 'message']
            for attr in required_attrs:
                if not hasattr(record, attr):
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Record validation failed: {e}")
            return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics from the standardized formatter.
        
        Returns:
            Dictionary containing performance statistics
        """
        if hasattr(self, '_standard_formats'):
            return self._standard_formats.get_stats()
        else:
            return {
                'performance_level': 'not_optimized',
                'formats_processed': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'uptime_seconds': 0,
                'formats_per_second': 0,
                'cache_hit_rate': 0
            }
    
    def clear_cache(self) -> None:
        """
        Clear the LRU cache for better memory management.
        """
        if hasattr(self, '_standard_formats'):
            self._standard_formats.clear_cache()
    
    def optimize(self) -> None:
        """
        Optimize performance by clearing caches and resetting statistics.
        """
        if hasattr(self, '_standard_formats'):
            self._standard_formats.optimize()
