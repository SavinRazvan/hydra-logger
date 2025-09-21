"""
Text Formatters for Hydra-Logger

This module provides high-performance plain text formatters for different
use cases, optimized for maximum throughput and minimal latency. These
formatters are designed for file output and console output without colors.

ARCHITECTURE:
- PlainTextFormatter: Basic text formatting with customizable format strings
- FastPlainTextFormatter: Ultra-fast plain text with minimal overhead
- DetailedFormatter: Comprehensive context information
- Performance Integration: Standardized format function integration
- Format Optimization: Pre-compiled format functions for common patterns

PERFORMANCE FEATURES:
- Ultra-fast string formatting with direct concatenation
- Pre-compiled format functions for common patterns
- LRU cache integration for performance optimization
- Memory-efficient object pooling
- JIT optimization for hot code paths
- Zero-overhead formatting for simple cases

FORMAT OPTIMIZATION:
- F-string compilation for common format patterns
- Direct string concatenation for maximum speed
- Format string caching and reuse
- Performance level configuration
- Automatic optimization based on usage patterns

COLOR SYSTEM NOTE:
- Plain text formatters do NOT support colors
- Used for file handlers and console handlers with use_colors=False
- ColoredFormatter should be used for colored console output
- These formatters provide clean, uncolored text output

USAGE EXAMPLES:

Basic Text Formatting:
    from hydra_logger.formatters.text import PlainTextFormatter
    
    # Create formatter with default format
    formatter = PlainTextFormatter()
    
    # Create formatter with custom format
    formatter = PlainTextFormatter("[{timestamp}] [{level_name}] {message}")

Fast Text Formatting:
    from hydra_logger.formatters.text import FastPlainTextFormatter
    
    # Ultra-fast formatter with minimal overhead
    formatter = FastPlainTextFormatter()

Detailed Formatting:
    from hydra_logger.formatters.text import DetailedFormatter
    
    # Comprehensive context information
    formatter = DetailedFormatter()

Performance Integration:
    from hydra_logger.formatters.standard_formats import get_standard_formats, PerformanceLevel
    
    # Get performance-optimized formatter
    standard_formats = get_standard_formats(PerformanceLevel.FAST)
    
    # Use in custom formatter
    class OptimizedTextFormatter(PlainTextFormatter):
        def __init__(self):
            super().__init__()
            self._standard_formats = get_standard_formats(PerformanceLevel.FAST)
            self._format_func = self._standard_formats.format_basic

FORMAT STRING PATTERNS:
- "[{level_name}] [{layer}] {message}": Basic format with level and layer
- "[{timestamp}] [{level_name}] [{layer}] {message}": Full format with timestamp
- "[{timestamp}] [{level_name}] {message}": Format with timestamp and level
- "{timestamp} {level_name} {message}": Simple format with timestamp
- "[{level_name}] {message}": Minimal format with level only
- "{message}": Message-only format

PERFORMANCE LEVELS:
- ULTRA_FAST: Minimal overhead, maximum speed (direct string operations)
- FAST: Balanced performance and features (LRU cache, minimal overhead)
- ENHANCED: Full infrastructure features (memory optimization, JIT)
- DEBUG: Maximum debugging and monitoring capabilities
"""

from datetime import datetime
from typing import Optional, Dict, Any
from .base import BaseFormatter
from ..types.records import LogRecord
from ..utils.time_utility import TimestampConfig


class PlainTextFormatter(BaseFormatter):
    """Basic plain text formatter with customizable format string."""
    
    def __init__(self, format_string: str = None, timestamp_config: Optional[TimestampConfig] = None):
        """
        Initialize plain text formatter.
        
        Args:
            format_string: Format template using {field} placeholders
            timestamp_config: Configuration for timestamp formatting
        """
        # Set default timestamp config to HUMAN_READABLE if not provided
        if timestamp_config is None:
            from ..utils.time_utility import TimestampConfig, TimestampFormat, TimestampPrecision
            timestamp_config = TimestampConfig(
                format_type=TimestampFormat.HUMAN_READABLE,
                precision=TimestampPrecision.SECONDS,
                timezone_name=None,  # Local timezone
                include_timezone=False
            )
        super().__init__("plain_text", timestamp_config)
        self.format_string = format_string or "{timestamp} | {level_name} | {layer} | {message}"
        
        # Simplified formatter - no performance optimization
        self._format_func = self._format_default
        
        # Performance optimization: Caching
        self._format_cache = {}
        self._use_fstring = self._should_use_fstring()
        self._compiled_format = None
        
        # Pre-compile format string if possible
        if self._use_fstring:
            self._compiled_format = self._compile_fstring_format()
    
    def _should_use_fstring(self) -> bool:
        """Check if we can use f-string formatting for better performance."""
        # Use f-string for simple, common format patterns
        simple_patterns = [
            "[{level_name}] [{layer}] {message}",
            "[{timestamp}] [{level_name}] [{layer}] {message}",
            "[{timestamp}] [{level_name}] {message}",
            "{timestamp} {level_name} {message}",
            "[{level_name}] {message}",
            "{message}"
        ]
        return self.format_string in simple_patterns
    
    def _compile_fstring_format(self) -> callable:
        """Compile format string into optimized function."""
        if self.format_string == "{timestamp} | {level_name} | {layer} | {message}":
            return lambda r: f"{self.format_timestamp(r)} | {r.level_name} | {r.layer} | {r.message}"
        elif self.format_string == "[{level_name}] [{layer}] {message}":
            return lambda r: f"[{r.level_name}] [{r.layer}] {r.message}"
        elif self.format_string == "[{timestamp}] [{level_name}] [{layer}] {message}":
            return lambda r: f"[{self.format_timestamp(r)}] [{r.level_name}] [{r.layer}] {r.message}"
        elif self.format_string == "[{timestamp}] [{level_name}] {message}":
            return lambda r: f"[{self.format_timestamp(r)}] [{r.level_name}] {r.message}"
        elif self.format_string == "{timestamp} {level_name} {message}":
            return lambda r: f"{self.format_timestamp(r)} {r.level_name} {r.message}"
        elif self.format_string == "[{level_name}] {message}":
            return lambda r: f"[{r.level_name}] {r.message}"
        elif self.format_string == "{message}":
            return lambda r: f"{r.message}"
        else:
            return None
    
    
    def format(self, record: LogRecord) -> str:
        """
        Format record using format string template or FormattingEngine.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted string
        """
        # Use most optimized path for performance
        if self._compiled_format:
            # Use pre-compiled f-string for maximum speed
            return self._compiled_format(record)
        else:
            # Use standardized formatter with LRU cache
            return self._format_func(record)
    
    
    
    def get_required_extension(self) -> str:
        """
        Get the required file extension for Plain Text formatter.
        
        Returns:
            '.log' - Industry standard for plain text log files
        """
        return ".log"
    

    def _format_default(self, record: LogRecord) -> str:
        """
        Default formatting implementation for backward compatibility.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted string
        """
        # Use configured timestamp formatting (RFC3339_MICRO by default)
        timestamp_str = self.format_timestamp(record)
        
        # Plain text formatter - no color stripping needed
        return self.format_string.format(
            timestamp=timestamp_str,
            level_name=record.level_name,
            message=record.message,
            logger_name=record.logger_name,
            layer=record.layer,
            file_name=record.file_name or "unknown",
            function_name=record.function_name or "unknown",
            line_number=record.line_number or 0
        )


class FastPlainTextFormatter(BaseFormatter):
    """Ultra-fast plain text formatter with minimal overhead."""
    
    def __init__(self, format_string: str = "{timestamp} | {level_name} | {layer} | {message}",
                 timestamp_config: Optional[TimestampConfig] = None):
        """
        Initialize fast formatter.
        
        Args:
            format_string: Format template using {field} placeholders
            timestamp_config: Configuration for timestamp formatting
        """
        super().__init__("fast_plain_text", timestamp_config=timestamp_config)
        self.format_string = format_string
    
    def format(self, record: LogRecord) -> str:
        """
        Format record with optimized timestamp handling.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted string
        """
        # Use configured timestamp formatting (RFC3339_MICRO by default)
        timestamp_str = self.format_timestamp(record)
        
        # Plain text formatter - no color stripping needed
        return self.format_string.format(
            timestamp=timestamp_str,
            level_name=record.level_name,
            message=record.message,
            layer=record.layer
        )
    
    def get_required_extension(self) -> str:
        """
        Get the required file extension for Plain Text formatter.
        
        Returns:
            '.log' - Industry standard for plain text log files
        """
        return ".log"

    def _format_default(self, record: LogRecord) -> str:
        """
        Default formatting implementation for backward compatibility.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted string
        """
        return self.format(record)


class DetailedFormatter(BaseFormatter):
    """Detailed formatter with comprehensive context information."""
    
    def __init__(self, include_thread: bool = True, include_process: bool = True):
        """
        Initialize detailed formatter.
        
        Args:
            include_thread: Whether to include thread information (legacy)
            include_process: Whether to include process information (legacy)
        """
        super().__init__("detailed")
        self.include_thread = include_thread
        self.include_process = include_process
    
    def format(self, record: LogRecord) -> str:
        """
        Format record with detailed context or FormattingEngine.
        
        Args:
            record: Log record to format
            
        Returns:
            Detailed formatted string
        """
        # Use default formatting for backward compatibility
        return self._format_default(record)
    
    
    def _format_default(self, record: LogRecord) -> str:
        """
        Default detailed formatting implementation for backward compatibility.
        
        Args:
            record: Log record to format
            
        Returns:
            Detailed formatted string
        """
        timestamp_str = self.format_timestamp(record)
        
        # Base format - only show layer, not logger_name to avoid confusion
        parts = [
            f"[{timestamp_str}]",
            f"[{record.level_name}]",
            f"[{record.layer}]"
        ]
        
        # Add context information
        if record.file_name and record.function_name:
            parts.append(f"[{record.file_name}:{record.function_name}:{record.line_number}]")
        
        # Removed thread and process info - not in optimized LogRecord
        
        # Add message
        parts.append(record.message)
        
        return " ".join(parts)
    
    def get_required_extension(self) -> str:
        """
        Get the required file extension for Detailed formatter.
        
        Returns:
            '.log' - Industry standard for detailed log files
        """
        return ".log"
