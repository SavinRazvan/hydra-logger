"""
Main HydraLogger class for multi-layered, multi-destination logging.

This module provides a sophisticated, dynamic logging system that can route different
types of logs across multiple destinations (files, console) with custom folder paths.
The system supports multi-layered logging where each layer can have its own
configuration, destinations, and log levels, enabling complex logging scenarios for
enterprise applications.

Key Features:
- Multi-layered logging with custom folder paths for each layer
- Multiple destinations per layer (file, console) with independent configurations
- Configurable file rotation and backup counts with size-based rotation
- Graceful error handling and fallback mechanisms for robust operation
- Thread-safe logging operations for concurrent applications
- Backward compatibility with standard Python logging module
- Automatic directory creation for custom log file paths
- Comprehensive log level filtering and message routing

The HydraLogger class is the core component that orchestrates all logging operations,
managing multiple logging layers, handling configuration validation, and providing
a unified interface for complex logging requirements.

Example:
    >>> from hydra_logger import HydraLogger
    >>> logger = HydraLogger()
    >>> logger.info("CONFIG", "Configuration loaded successfully")
    >>> logger.error("SECURITY", "Authentication failed")
    >>> logger.debug("EVENTS", "Event stream started")
"""

import logging
import os
import sys
import time
import threading
import psutil
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional, Union, List, Any

from hydra_logger.config import (
    LogDestination,
    LoggingConfig,
    LogLayer,
    create_log_directories,
    get_default_config,
    load_config,
)

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

# Named color presets for easier customization
NAMED_COLORS = {
    "red": Colors.RED,
    "green": Colors.GREEN,
    "yellow": Colors.YELLOW,
    "blue": Colors.BLUE,
    "magenta": Colors.MAGENTA,
    "cyan": Colors.CYAN,
    "white": Colors.WHITE,
    "bright_red": Colors.BRIGHT_RED,
    "bright_green": Colors.BRIGHT_GREEN,
    "bright_yellow": Colors.BRIGHT_YELLOW,
    "bright_blue": Colors.BRIGHT_BLUE,
    "bright_magenta": Colors.BRIGHT_MAGENTA,
    "bright_cyan": Colors.BRIGHT_CYAN,
}

# Default color mapping for log levels (professional standard)
DEFAULT_COLORS = {
    "DEBUG": Colors.CYAN,
    "INFO": Colors.GREEN,
    "WARNING": Colors.YELLOW,
    "ERROR": Colors.RED,
    "CRITICAL": Colors.BRIGHT_RED,
}

# PII Detection Patterns
PII_PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "password": re.compile(r'\b(?:password|passwd|pwd)\s*[=:]\s*[^\s]+', re.IGNORECASE),
    "api_key": re.compile(r'\b(?:api[_-]?key|apikey)\s*[=:]\s*[^\s]+', re.IGNORECASE),
    "token": re.compile(r'\b(?:token|access_token|bearer)\s*[=:]\s*[^\s]+', re.IGNORECASE),
    "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "phone": re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    "ip_address": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
    "url_with_auth": re.compile(r'https?://[^/]+@[^\s]+'),
}

# Redaction replacement patterns
REDACTION_REPLACEMENTS = {
    "email": "[EMAIL_REDACTED]",
    "password": "[PASSWORD_REDACTED]",
    "api_key": "[API_KEY_REDACTED]",
    "token": "[TOKEN_REDACTED]",
    "credit_card": "[CREDIT_CARD_REDACTED]",
    "ssn": "[SSN_REDACTED]",
    "phone": "[PHONE_REDACTED]",
    "ip_address": "[IP_REDACTED]",
    "url_with_auth": "[URL_WITH_AUTH_REDACTED]",
}

def redact_sensitive_data(message: str) -> str:
    """
    Redact sensitive information from log messages.
    
    Args:
        message (str): Original log message
        
    Returns:
        str: Message with sensitive data redacted
    """
    redacted_message = message
    
    # URL with auth redaction (run first)
    redacted_message = re.sub(r'https?://[^/]+@[\S]+', '[URL_WITH_AUTH_REDACTED]', redacted_message)
    
    # API key redaction (case-insensitive, allow space/underscore/hyphen)
    redacted_message = re.sub(r'\b(?:api[ _-]?key)\b\s*[=:]?\s*[^\s]+', 'api_key=[API_KEY_REDACTED]', redacted_message, flags=re.IGNORECASE)
    
    # Password redaction (allow just 'password secret123')
    redacted_message = re.sub(r'\b(?:password|passwd|pwd)\b\s*[=:]?\s*[^\s]+', 'password=[PASSWORD_REDACTED]', redacted_message, flags=re.IGNORECASE)
    
    # Email redaction
    redacted_message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', redacted_message)
    
    # Token redaction (replace 'Bearer token: <value>' or 'token: <value>')
    redacted_message = re.sub(r'(Bearer\s+)?(token|access_token|bearer)\s*[:=]?\s*[^\s]+', 'token=[TOKEN_REDACTED]', redacted_message, flags=re.IGNORECASE)
    
    # Credit card redaction
    redacted_message = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CREDIT_CARD_REDACTED]', redacted_message)
    
    # SSN redaction
    redacted_message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', redacted_message)
    
    # Phone redaction
    redacted_message = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE_REDACTED]', redacted_message)
    
    # IP address redaction
    redacted_message = re.sub(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[IP_REDACTED]', redacted_message)
    
    return redacted_message

class BufferedRotatingFileHandler(RotatingFileHandler):
    """
    Buffered rotating file handler for improved performance.
    
    This handler extends RotatingFileHandler with buffering capabilities
    to reduce I/O operations and improve throughput for high-frequency logging.
    """
    
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, 
                 buffer_size=8192, flush_interval=1.0):
        """
        Initialize buffered rotating file handler.
        
        Args:
            filename (str): Log file path
            maxBytes (int): Maximum file size before rotation
            backupCount (int): Number of backup files to keep
            encoding (str): File encoding
            buffer_size (int): Buffer size in bytes
            flush_interval (float): Flush interval in seconds
        """
        # Ensure backupCount is an integer
        backup_count = int(backupCount) if backupCount is not None else 0
        super().__init__(filename, maxBytes=maxBytes, backupCount=backup_count, encoding=encoding)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self._buffer = []
        self._buffer_size = 0
        self._last_flush = time.time()
        self._lock = threading.Lock()
    
    def emit(self, record):
        """
        Emit a log record with buffering.
        
        Args:
            record (LogRecord): Log record to emit
        """
        try:
            # Format the record
            msg = self.format(record)
            
            with self._lock:
                # Add to buffer
                self._buffer.append(msg)
                # Use safe encoding
                encoding = self.encoding or 'utf-8'
                if encoding == 'locale':
                    encoding = 'utf-8'
                self._buffer_size += len(msg.encode(encoding))
                
                # Check if we need to flush
                current_time = time.time()
                should_flush = (
                    self._buffer_size >= self.buffer_size or
                    current_time - self._last_flush >= self.flush_interval
                )
                
                if should_flush:
                    self._flush_buffer()
                    
        except Exception:
            self.handleError(record)
    
    def _flush_buffer(self):
        """Flush the buffer to the file."""
        if not self._buffer:
            return
            
        try:
            # Write all buffered messages
            for msg in self._buffer:
                self.stream.write(msg + '\n')
            
            # Flush the stream
            self.stream.flush()
            
            # Clear buffer
            self._buffer.clear()
            self._buffer_size = 0
            self._last_flush = time.time()
            
        except Exception as e:
            # Log the error but don't raise to avoid breaking logging
            print(f"Error flushing buffer: {e}", file=sys.stderr)
    
    def close(self):
        """Close the handler and flush any remaining buffer."""
        with self._lock:
            self._flush_buffer()
        super().close()
    
    def flush(self):
        """Flush the buffer immediately."""
        with self._lock:
            self._flush_buffer()
        super().flush()
    
class PerformanceMonitor:
    """
    Performance monitoring for HydraLogger.
    
    Tracks timing, memory usage, and log message processing performance.
    Thread-safe and designed for minimal overhead.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._handler_creation_times: List[float] = []
        self._log_processing_times: List[float] = []
        self._memory_usage: List[float] = []
        self._message_count = 0
        self._error_count = 0
        self._last_memory_check = 0
        self._memory_check_interval = 60  # Check memory every 60 seconds
        
    def start_handler_creation_timer(self) -> float:
        """Start timing handler creation."""
        return time.time()
    
    def end_handler_creation_timer(self, start_time: float) -> None:
        """End timing handler creation and record the duration."""
        duration = time.time() - start_time
        with self._lock:
            self._handler_creation_times.append(duration)
    
    def start_log_processing_timer(self) -> float:
        """Start timing log message processing."""
        return time.time()
    
    def end_log_processing_timer(self, start_time: float) -> None:
        """End timing log message processing and record the duration."""
        duration = time.time() - start_time
        with self._lock:
            self._log_processing_times.append(duration)
            self._message_count += 1
    
    def record_error(self) -> None:
        """Record an error occurrence."""
        with self._lock:
            self._error_count += 1
    
    def check_memory_usage(self) -> float:
        """Check current memory usage and record it."""
        current_time = time.time()
        if current_time - self._last_memory_check >= self._memory_check_interval:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                with self._lock:
                    self._memory_usage.append(memory_mb)
                    self._last_memory_check = current_time
                return memory_mb
            except (ImportError, AttributeError):
                # psutil not available or not working
                return 0.0
        return 0.0
    
    def get_statistics(self) -> Dict[str, float]:
        """Get current performance statistics."""
        with self._lock:
            stats = {
                "uptime_seconds": time.time() - self._start_time,
                "total_messages": self._message_count,
                "total_errors": self._error_count,
                "error_rate": (self._error_count / max(self._message_count, 1)) * 100,
            }
            
            if self._handler_creation_times:
                stats.update({
                    "avg_handler_creation_time": sum(self._handler_creation_times) / len(self._handler_creation_times),
                    "max_handler_creation_time": max(self._handler_creation_times),
                    "min_handler_creation_time": min(self._handler_creation_times),
                })
            
            if self._log_processing_times:
                stats.update({
                    "avg_log_processing_time": sum(self._log_processing_times) / len(self._log_processing_times),
                    "max_log_processing_time": max(self._log_processing_times),
                    "min_log_processing_time": min(self._log_processing_times),
                    "messages_per_second": len(self._log_processing_times) / max(stats["uptime_seconds"], 1),
                })
            
            if self._memory_usage:
                stats.update({
                    "current_memory_mb": self._memory_usage[-1],
                    "avg_memory_mb": sum(self._memory_usage) / len(self._memory_usage),
                    "max_memory_mb": max(self._memory_usage),
                    "min_memory_mb": min(self._memory_usage),
                })
            
            return stats
    
    def reset_statistics(self) -> None:
        """Reset all performance statistics."""
        with self._lock:
            self._start_time = time.time()
            self._handler_creation_times.clear()
            self._log_processing_times.clear()
            self._memory_usage.clear()
            self._message_count = 0
            self._error_count = 0
            self._last_memory_check = 0

def get_color_config() -> Dict[str, str]:
    """
    Get color configuration from environment variables.
    
    Supports both ANSI codes and named colors:
    - ANSI codes: HYDRA_LOG_COLOR_ERROR='\033[31m'
    - Named colors: HYDRA_LOG_COLOR_ERROR='red'
    
    Returns:
        Dict[str, str]: Color mapping for log levels.
    """
    colors = DEFAULT_COLORS.copy()
    
    # Allow user to override colors via environment variables
    env_colors = {
        "DEBUG": os.getenv("HYDRA_LOG_COLOR_DEBUG"),
        "INFO": os.getenv("HYDRA_LOG_COLOR_INFO"),
        "WARNING": os.getenv("HYDRA_LOG_COLOR_WARNING"),
        "ERROR": os.getenv("HYDRA_LOG_COLOR_ERROR"),
        "CRITICAL": os.getenv("HYDRA_LOG_COLOR_CRITICAL"),
    }
    
    # Update with user-defined colors
    for level, color in env_colors.items():
        if color:
            # Support named colors (e.g., 'red', 'bright_cyan')
            if color in NAMED_COLORS:
                colors[level] = NAMED_COLORS[color]
            else:
                # Assume it's an ANSI code
                colors[level] = color
    
    return colors

def get_layer_color() -> str:
    """
    Get the color for layer names.
    
    Supports both ANSI codes and named colors:
    - ANSI codes: HYDRA_LOG_LAYER_COLOR='\033[35m'
    - Named colors: HYDRA_LOG_LAYER_COLOR='magenta'
    
    Returns:
        str: ANSI color code for layer names.
    """
    layer_color = os.getenv("HYDRA_LOG_LAYER_COLOR", "magenta")
    
    # Support named colors
    if layer_color in NAMED_COLORS:
        return NAMED_COLORS[layer_color]
    
    # Assume it's an ANSI code
    return layer_color

def get_smart_formatter(destination_type: str = "auto", force_colors: Optional[str] = None) -> logging.Formatter:
    """
    Get the appropriate formatter based on destination type and environment.
    
    Args:
        destination_type (str): "console", "file", "jupyter", or "auto"
        force_colors (Optional[str]): Force color mode: "ansi", "html", "none", or None
    
    Returns:
        logging.Formatter: Appropriate formatter for the context
    """
    if force_colors == "none" or destination_type == "file":
        return PlainTextFormatter()
    elif force_colors == "ansi":
        return AnsiColorFormatter()
    elif force_colors == "html" or destination_type == "jupyter":
        return HtmlColorFormatter()
    else:
        # Use smart auto-detecting formatter
        return ColoredTextFormatter(force_colors=force_colors, destination_type=destination_type)


def should_use_colors() -> bool:
    """
    Determine if colors should be used based on environment.
    
    Returns:
        bool: True if colors should be used, False otherwise.
    """
    # Check if colors are explicitly disabled
    if os.getenv("HYDRA_LOG_NO_COLOR", "").lower() in ("1", "true", "yes"):
        return False
    
    # Check if colors are explicitly enabled (this overrides everything else)
    if os.getenv("HYDRA_LOG_FORCE_COLOR", "").lower() in ("1", "true", "yes"):
        return True
    
    # Check if we're in a Jupyter notebook environment
    try:
        import IPython  # type: ignore
        if IPython.get_ipython() is not None:
            return True
    except ImportError:
        pass
    
    # Check if we're in a TTY (terminal)
    if sys.stdout.isatty():
        # Check if we're in a CI environment (usually no colors)
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or os.getenv("GITLAB_CI"):
            return False
        return True
    
    # Check if we're in a rich environment (like Jupyter)
    if os.getenv("JUPYTER_RUNTIME_DIR") or os.getenv("IPYTHON_ENABLE"):
        return True
    
    # Check if we're in a VS Code terminal
    if os.getenv("TERM_PROGRAM") == "vscode":
        return True
    
    return False

class HydraLoggerError(Exception):
    """
    Base exception for HydraLogger errors.

    This exception is raised when critical errors occur during logger
    initialization, configuration, or operation that cannot be handled
    gracefully by the system.
    """

    pass

class ColoredTextFormatter(logging.Formatter):
    """
    Smart formatter that automatically detects the environment and applies appropriate colors.
    
    This formatter intelligently chooses between ANSI codes (terminal), HTML (Jupyter),
    or no colors (files) based on the destination and environment detection.
    """
    
    def __init__(self, force_colors: Optional[str] = None, destination_type: str = "auto"):
        """
        Initialize the formatter with smart color detection.
        
        Args:
            force_colors (Optional[str]): Force color mode: "ansi", "html", "none", or None for auto-detect
            destination_type (str): Destination type hint: "console", "file", "jupyter", or "auto"
        """
        super().__init__(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.colors = get_color_config()
        self.layer_color = get_layer_color()
        self.destination_type = destination_type
        self.force_colors = force_colors
        
        # Determine color mode
        self.color_mode = self._determine_color_mode()
    
    def _determine_color_mode(self) -> str:
        """
        Determine the appropriate color mode based on environment and destination.
        
        Returns:
            str: "ansi", "html", or "none"
        """
        # If colors are forced, use that
        if self.force_colors:
            return self.force_colors
        
        # If destination is explicitly file, no colors
        if self.destination_type == "file":
            return "none"
        
        # If destination is explicitly jupyter, use HTML
        if self.destination_type == "jupyter":
            return "html"
        
        # Check if colors are explicitly disabled
        if os.getenv("HYDRA_LOG_NO_COLOR", "").lower() in ("1", "true", "yes"):
            return "none"
        
        # Check if colors are explicitly enabled
        if os.getenv("HYDRA_LOG_FORCE_COLOR", "").lower() in ("1", "true", "yes"):
            # Detect environment for forced colors
            if self._detect_jupyter():
                return "html"
            return "ansi"
        
        # Auto-detect environment
        if self._detect_jupyter():
            return "html"
        
        # Check if we're in a TTY (terminal)
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            # Check if we're in a CI environment (usually no colors)
            if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or os.getenv("GITLAB_CI"):
                return "none"
            return "ansi"
        
        # Check if we're in a rich environment
        if os.getenv("JUPYTER_RUNTIME_DIR") or os.getenv("IPYTHON_ENABLE"):
            return "html"
        
        # Check if we're in a VS Code terminal
        if os.getenv("TERM_PROGRAM") == "vscode":
            return "ansi"
        
        return "none"
    
    def _detect_jupyter(self) -> bool:
        """Detect if we're running in a Jupyter environment."""
        try:
            import IPython  # type: ignore
            return IPython.get_ipython() is not None
        except ImportError:
            return False
    
    def _get_html_color(self, ansi_color: str) -> str:
        """Convert ANSI color to HTML color for Jupyter notebooks."""
        color_map = {
            Colors.RED: "#ff0000",
            Colors.GREEN: "#00ff00", 
            Colors.YELLOW: "#ffff00",
            Colors.BLUE: "#0000ff",
            Colors.MAGENTA: "#ff00ff",
            Colors.CYAN: "#00ffff",
            Colors.WHITE: "#ffffff",
            Colors.BRIGHT_RED: "#ff4444",
            Colors.BRIGHT_GREEN: "#44ff44",
            Colors.BRIGHT_YELLOW: "#ffff44",
            Colors.BRIGHT_BLUE: "#4444ff",
            Colors.BRIGHT_MAGENTA: "#ff44ff",
            Colors.BRIGHT_CYAN: "#44ffff",
        }
        return color_map.get(ansi_color, "#ffffff")
    
    def format(self, record):
        # Get the original formatted message
        formatted = super().format(record)
        
        # If no colors, return as-is
        if self.color_mode == "none":
            return formatted
        
        # Split the formatted string into parts
        parts = formatted.split(" - ")
        # Defensive: ensure we have enough parts (timestamp, layer, level, ...)
        if len(parts) >= 3:
            # Color the layer name (index 1) and level name (index 2) independently
            if self.color_mode == "html":
                # Use HTML colors for Jupyter
                html_layer = self._get_html_color(self.layer_color) if self.layer_color else "#ffffff"
                html_level = self._get_html_color(self.colors.get(record.levelname, "")) or "#ffffff"
                if self.layer_color:
                    parts[1] = f'<span style="color: {html_layer}">{parts[1]}</span>'
                if record.levelname in self.colors:
                    parts[2] = f'<span style="color: {html_level}">{parts[2]}</span>'
            elif self.color_mode == "ansi":
                # Use ANSI colors for terminal
                # Color only if color is set (layer_color may be empty)
                if self.layer_color:
                    parts[1] = f"{self.layer_color}{parts[1]}{Colors.RESET}"
                if record.levelname in self.colors:
                    parts[2] = f"{self.colors[record.levelname]}{parts[2]}{Colors.RESET}"
            formatted = " - ".join(parts)
        return formatted


class PlainTextFormatter(logging.Formatter):
    """Plain text formatter without any colors - for files and non-color environments."""
    
    def __init__(self):
        super().__init__(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


class AnsiColorFormatter(logging.Formatter):
    """ANSI color formatter specifically for terminal environments."""
    
    def __init__(self):
        super().__init__(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.colors = get_color_config()
        self.layer_color = get_layer_color()
    
    def format(self, record):
        formatted = super().format(record)
        parts = formatted.split(" - ")
        if len(parts) >= 3:
            if self.layer_color:
                parts[1] = f"{self.layer_color}{parts[1]}{Colors.RESET}"
            if record.levelname in self.colors:
                parts[2] = f"{self.colors[record.levelname]}{parts[2]}{Colors.RESET}"
            formatted = " - ".join(parts)
        return formatted


class HtmlColorFormatter(logging.Formatter):
    """HTML color formatter specifically for Jupyter notebooks."""
    
    def __init__(self):
        super().__init__(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.colors = get_color_config()
        self.layer_color = get_layer_color()
    
    def _get_html_color(self, ansi_color: str) -> str:
        """Convert ANSI color to HTML color."""
        color_map = {
            Colors.RED: "#ff0000",
            Colors.GREEN: "#00ff00", 
            Colors.YELLOW: "#ffff00",
            Colors.BLUE: "#0000ff",
            Colors.MAGENTA: "#ff00ff",
            Colors.CYAN: "#00ffff",
            Colors.WHITE: "#ffffff",
            Colors.BRIGHT_RED: "#ff4444",
            Colors.BRIGHT_GREEN: "#44ff44",
            Colors.BRIGHT_YELLOW: "#ffff44",
            Colors.BRIGHT_BLUE: "#4444ff",
            Colors.BRIGHT_MAGENTA: "#ff44ff",
            Colors.BRIGHT_CYAN: "#44ffff",
        }
        return color_map.get(ansi_color, "#ffffff")
    
    def format(self, record):
        formatted = super().format(record)
        parts = formatted.split(" - ")
        if len(parts) >= 3:
            if self.layer_color:
                html_color = self._get_html_color(self.layer_color)
                parts[1] = f'<span style="color: {html_color}">{parts[1]}</span>'
            if record.levelname in self.colors:
                html_color = self._get_html_color(self.colors[record.levelname])
                parts[2] = f'<span style="color: {html_color}">{parts[2]}</span>'
            formatted = " - ".join(parts)
        return formatted

class HydraLogger:
    """
    Dynamic multi-headed logging system with layer-based routing.

    This class provides a sophisticated logging system that can route different types
    of logs to different destinations with custom folder paths. Each layer can have
    its own configuration, including multiple destinations (files, console) with
    different log levels and file rotation settings.

    The HydraLogger manages multiple logging layers simultaneously, each with its
    own configuration and destinations. It automatically creates necessary directories,
    handles file rotation, and provides fallback mechanisms for error recovery.

    Attributes:
        config (LoggingConfig): The logging configuration for this instance.
        loggers (Dict[str, logging.Logger]): Dictionary of configured loggers by
            layer name.
    """

    def __init__(self, config: Optional[LoggingConfig] = None, 
                 auto_detect: bool = False,
                 enable_performance_monitoring: bool = False,
                 redact_sensitive: bool = False,
                 lazy_initialization: bool = False,
                 date_format: Optional[str] = None,
                 time_format: Optional[str] = None,
                 logger_name_format: Optional[str] = None,
                 message_format: Optional[str] = None):
        """
        Initialize HydraLogger with configuration.

        Args:
            config (Optional[LoggingConfig]): LoggingConfig object. If None,
                uses default config.
            auto_detect (bool): Auto-detect environment and configure accordingly.
                Defaults to False for backward compatibility.
            enable_performance_monitoring (bool): Enable performance monitoring.
                Defaults to False.
            redact_sensitive (bool): Auto-redact sensitive information (emails, 
                passwords, tokens). Defaults to False.
            lazy_initialization (bool): Defer handler creation until first use.
                Defaults to False for backward compatibility.
            date_format (Optional[str]): Custom date format string. If None,
                uses environment variable HYDRA_LOG_DATE_FORMAT or default.
            time_format (Optional[str]): Custom time format string. If None,
                uses environment variable HYDRA_LOG_TIME_FORMAT or default.
            logger_name_format (Optional[str]): Custom logger name format string.
                If None, uses environment variable HYDRA_LOG_LOGGER_NAME_FORMAT or default.
            message_format (Optional[str]): Custom message format string. If None,
                uses environment variable HYDRA_LOG_MESSAGE_FORMAT or default.

        Raises:
            HydraLoggerError: If logger setup fails due to configuration issues.

        The initialization process includes:
        - Configuration validation and default setup
        - Directory creation for all file destinations (unless lazy initialization)
        - Logger setup for each configured layer (unless lazy initialization)
        - Handler creation and configuration (unless lazy initialization)
        """
        def _env_or_default(var, default):
            val = os.getenv(var)
            return val if val else default

        try:
            # Store format customization settings, treat empty env as unset
            self.date_format = date_format or _env_or_default("HYDRA_LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
            self.time_format = time_format or _env_or_default("HYDRA_LOG_TIME_FORMAT", "%H:%M:%S")
            self.logger_name_format = logger_name_format or _env_or_default("HYDRA_LOG_LOGGER_NAME_FORMAT", "%(name)s")
            self.message_format = message_format or _env_or_default("HYDRA_LOG_MESSAGE_FORMAT", "%(levelname)s - %(message)s")
            
            # Auto-detect configuration if enabled and no config provided
            if config is None and auto_detect:
                config = self._auto_detect_config()
            
            # Use provided config, auto-detected config, or default config
            if config is None:
                self.config = get_default_config()
            else:
                self.config = config
                
            self.loggers: Dict[str, logging.Logger] = {}
            self._logger_init_lock = threading.Lock()
            self.performance_monitoring = enable_performance_monitoring
            self.redact_sensitive = redact_sensitive
            self.lazy_initialization = lazy_initialization
            self._initialized = False
            
            # Initialize performance monitor if enabled
            self._performance_monitor = PerformanceMonitor() if enable_performance_monitoring else None
            
            # Create log directories and setup loggers immediately (unless lazy initialization)
            if not lazy_initialization:
                self._setup_loggers()
                self._initialized = True
            else:
                # For lazy initialization, only create directories
                try:
                    create_log_directories(self.config)
                except OSError as dir_err:
                    self._log_warning(f"Directory creation failed: {dir_err}. Will retry during first log.")
                except Exception as e:
                    self._log_error(f"Failed to create directories: {e}")
        except Exception as e:
            raise HydraLoggerError(f"Failed to initialize HydraLogger: {e}") from e

    @classmethod
    def from_config(cls, config_path: Union[str, Path]) -> "HydraLogger":
        """
        Create HydraLogger from configuration file.

        Args:
            config_path (Union[str, Path]): Path to YAML or TOML configuration
                file.

        Returns:
            HydraLogger: Instance configured from file.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the configuration file is invalid or malformed.
            HydraLoggerError: If logger initialization fails after config loading.

        This method provides a convenient way to create a HydraLogger instance
        directly from a configuration file, handling all the loading and validation
        automatically.
        """
        try:
            config = load_config(config_path)
            return cls(config)
        except (FileNotFoundError, ValueError):
            # Re-raise FileNotFoundError and ValueError as-is
            raise
        except Exception as e:
            raise HydraLoggerError(
                f"Failed to create HydraLogger from config: {e}"
            ) from e

    def _setup_loggers(self) -> None:
        """
        Setup all loggers for configured layers.
        
        This method creates loggers and handlers for all configured layers
        during initialization. It handles directory creation and error recovery.
        """
        try:
            # Create log directories at startup (for file destinations)
            create_log_directories(self.config)
        except OSError as dir_err:
            self._log_warning(f"Directory creation failed: {dir_err}. Falling back to console logging for all layers.")
            for layer in self.config.layers.values():
                layer.destinations = [
                    d if d.type == "console" else LogDestination(type="console", level=d.level, format=getattr(d, "format", "text"))
                    for d in layer.destinations
                ]
        except Exception as e:
            # Handle any other exceptions during directory creation
            self._log_error(f"Failed to setup loggers: {e}")
            raise HydraLoggerError(f"Failed to setup loggers: {e}") from e
        
        # Setup each configured layer
        for layer_name, layer_config in self.config.layers.items():
            self._setup_single_layer(layer_name, layer_config)

    def _setup_single_layer(self, layer_name: str, layer_config: LogLayer) -> None:
        """
        Setup a single logging layer.
        
        Args:
            layer_name (str): Name of the layer to setup.
            layer_config (LogLayer): Configuration for the layer.
        """
        try:
            # Create and configure logger for this layer
            logger = logging.getLogger(layer_name)
            logger.setLevel(getattr(logging, layer_config.level))
            
            # Clear existing handlers
            if logger.hasHandlers():
                logger.handlers.clear()
            
            # Create handlers for each destination
            valid_handlers = 0
            for destination in layer_config.destinations:
                handler = self._create_handler(destination, layer_config.level)
                if handler:
                    logger.addHandler(handler)
                    valid_handlers += 1
            
            if valid_handlers == 0:
                self._log_warning(
                    f"No valid handlers created for layer '{layer_name}'. Layer will not log to any destination."
                )
            
            # Store the logger
            self.loggers[layer_name] = logger
            
        except Exception as e:
            self._log_error(f"Failed to setup layer '{layer_name}': {e}")
            # Create a fallback logger
            try:
                fallback_logger = logging.getLogger(layer_name)
                fallback_logger.setLevel(getattr(logging, layer_config.level))
                if not fallback_logger.handlers:
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setLevel(getattr(logging, layer_config.level))
                    console_handler.setFormatter(self._get_formatter())
                    fallback_logger.addHandler(console_handler)
                self.loggers[layer_name] = fallback_logger
            except Exception as fallback_error:
                # If even the fallback fails, create a minimal logger
                self._log_error(f"Fallback logger creation failed for '{layer_name}': {fallback_error}")
                try:
                    minimal_logger = logging.getLogger(layer_name)
                    minimal_logger.setLevel(getattr(logging, layer_config.level))
                    self.loggers[layer_name] = minimal_logger  # Store with original name
                except Exception as final_error:
                    # If even the minimal logger fails, create a dummy logger object
                    self._log_error(f"Minimal logger creation failed for '{layer_name}': {final_error}")
                    # Create a minimal logger object that won't fail
                    class DummyLogger:
                        def __init__(self, name, default_level="INFO"):
                            self.name = name
                            self.level = getattr(logging, default_level)
                            self.handlers = []
                        
                        def setLevel(self, level):
                            self.level = level
                        
                        def addHandler(self, handler):
                            self.handlers.append(handler)
                        
                        def hasHandlers(self):
                            return len(self.handlers) > 0
                        
                        def debug(self, msg):
                            pass
                        
                        def info(self, msg):
                            pass
                        
                        def warning(self, msg):
                            pass
                        
                        def error(self, msg):
                            pass
                        
                        def critical(self, msg):
                            pass
                    
                    dummy_logger = DummyLogger(layer_name, layer_config.level)
                    self.loggers[layer_name] = dummy_logger  # type: ignore

    def _create_handler(
        self, destination: LogDestination, layer_level: str
    ) -> Optional[logging.Handler]:
        """
        Create a logging handler for a destination.

        Args:
            destination (LogDestination): LogDestination configuration.
            layer_level (str): The level of the layer this handler belongs to.

        Returns:
            Optional[logging.Handler]: Configured logging handler or None if
                creation fails.

        This method creates the appropriate handler type based on the destination
        configuration. It includes comprehensive error handling and fallback
        mechanisms to ensure robust operation even when individual handlers fail.
        """
        # Start performance monitoring if enabled
        start_time = None
        if self._performance_monitor:
            start_time = self._performance_monitor.start_handler_creation_timer()
        
        try:
            if destination.type == "file":
                file_handler = self._create_file_handler(destination, layer_level)
                return file_handler
            elif destination.type == "console":
                console_handler = self._create_console_handler(destination, layer_level)
                return console_handler
        except ValueError as e:
            self._log_warning(f"Invalid destination configuration: {e}")
            if self._performance_monitor:
                self._performance_monitor.record_error()
            return None
        except Exception as e:
            self._log_warning(f"Failed to create {destination.type} handler: {e}")
            if self._performance_monitor:
                self._performance_monitor.record_error()
            if destination.type == "file":
                try:
                    fallback_handler = self._create_console_handler(destination, layer_level)
                    fmt = getattr(destination, "format", "text")
                    fallback_handler.setFormatter(self._get_formatter(fmt))
                    return fallback_handler
                except Exception as fallback_error:
                    self._log_error(
                        f"Fallback console handler creation failed: {fallback_error}"
                    )
                    if self._performance_monitor:
                        self._performance_monitor.record_error()
            return None
        finally:
            # End performance monitoring if enabled
            if self._performance_monitor and start_time:
                self._performance_monitor.end_handler_creation_timer(start_time)

    def _create_file_handler(
        self, destination: LogDestination, layer_level: str
    ) -> RotatingFileHandler:
        """
        Create a rotating file handler.

        Args:
            destination (LogDestination): File destination configuration.
            layer_level (str): The level of the layer this handler belongs to.

        Returns:
            RotatingFileHandler: Configured rotating file handler.

        Raises:
            ValueError: If path is None or invalid for file destinations.
            OSError: If file system operations fail.

        This method creates a RotatingFileHandler with the specified configuration,
        including file size limits, backup counts, and proper encoding. It handles
        path validation and provides detailed error messages for troubleshooting.
        """
        # Validate that path is provided for file destinations
        if not destination.path:
            raise ValueError("Path is required for file destinations")

        # Ensure the path is a string
        file_path = str(destination.path)

        # Parse max_size (e.g., "5MB" -> 5 * 1024 * 1024)
        max_bytes = self._parse_size(destination.max_size or "5MB")

        # Create the handler with proper error handling
        try:
            # Use buffered handler if performance monitoring is enabled
            if self.performance_monitoring:
                handler = BufferedRotatingFileHandler(
                    file_path,
                    maxBytes=max_bytes,
                    backupCount=destination.backup_count or 3,
                    encoding="utf-8",  # Ensure consistent encoding
                    buffer_size=getattr(destination, 'buffer_size', 8192),
                    flush_interval=getattr(destination, 'flush_interval', 1.0)
                )
            else:
                handler = RotatingFileHandler(
                    file_path,
                    maxBytes=max_bytes,
                    backupCount=destination.backup_count or 3,
                    encoding="utf-8",  # Ensure consistent encoding
                )

            # Use the layer level, not the destination level for file handlers
            handler.setLevel(getattr(logging, layer_level))
            
            # File handlers should never use colored formatters to keep text clean
            fmt = getattr(destination, "format", "text")
            if fmt == "text":
                # Use plain text formatter for files (no colors)
                handler.setFormatter(PlainTextFormatter())
            else:
                handler.setFormatter(self._get_formatter(fmt))

            return handler

        except OSError as e:
            raise OSError(
                f"Failed to create file handler for '{file_path}': {e}"
            ) from e

    def _create_console_handler(
        self, destination: LogDestination, layer_level: str
    ) -> logging.StreamHandler:
        """
        Create a console handler.

        Args:
            destination (LogDestination): Console destination configuration.
            layer_level (str): The level of the layer this handler belongs to.

        Returns:
            logging.StreamHandler: Configured console stream handler.

        Raises:
            ValueError: If the log level is invalid or handler creation fails.

        This method creates a StreamHandler that outputs to stdout with the
        specified log level and smart formatting for console output.
        """
        try:
            # Use JupyterHandler for Jupyter environments to properly render HTML colors
            try:
                import IPython  # type: ignore
                if IPython.get_ipython() is not None:
                    handler = JupyterHandler(sys.stdout)
                else:
                    handler = logging.StreamHandler(sys.stdout)
            except ImportError:
                handler = logging.StreamHandler(sys.stdout)
            
            handler.setLevel(getattr(logging, layer_level))
            
            # Use smart colored formatter for console output
            fmt = getattr(destination, "format", "text")
            if fmt == "text":
                # Use smart formatter that auto-detects environment
                handler.setFormatter(ColoredTextFormatter(destination_type="console"))
            else:
                handler.setFormatter(self._get_formatter(fmt))

            return handler

        except Exception as e:
            raise ValueError(f"Failed to create console handler: {e}") from e

    def _get_formatter(self, fmt: str = "text") -> logging.Formatter:
        """
        Get the appropriate formatter based on the specified format.

        Args:
            fmt (str): Format type ('text', 'json', 'csv', 'syslog', 'gelf').

        Returns:
            logging.Formatter: Configured logging formatter.

        Raises:
            ValueError: If the format is not supported or dependencies are missing.
        """
        fmt = fmt.lower()

        if fmt == "json":
            try:
                from pythonjsonlogger.json import JsonFormatter

                # Use the proper JsonFormatter from python-json-logger
                return JsonFormatter(
                    fmt="%(asctime)s %(levelname)s %(name)s %(message)s "
                    "%(filename)s %(lineno)d",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    rename_fields={
                        "asctime": "timestamp",
                        "levelname": "level",
                        "name": "logger",
                    },
                )
            except ImportError:
                self._log_warning(
                    "python-json-logger not installed, falling back to text format."
                )
                return self._get_text_formatter()

        elif fmt == "csv":
            return self._get_csv_formatter()

        elif fmt == "syslog":
            return self._get_syslog_formatter()

        elif fmt == "gelf":
            try:
                # Import graypy to check if it's available
                import graypy  # noqa: F401

                # GELF uses a special handler, but we can create a formatter for it
                return self._get_gelf_formatter()
            except ImportError:
                self._log_warning("graypy not installed, falling back to text format.")
                return self._get_text_formatter()

        else:  # text or unknown
            return self._get_text_formatter()

    def _get_structured_json_formatter(self) -> logging.Formatter:
        """Get a structured JSON formatter that creates valid JSON output."""
        return logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s", '
            '"file": "%(filename)s", "line": %(lineno)d}',
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _get_text_formatter(self) -> logging.Formatter:
        """Get the standard text formatter with custom format support."""
        # Use custom formats if available, otherwise use defaults
        date_format = getattr(self, 'date_format', "%Y-%m-%d %H:%M:%S")
        logger_name_format = getattr(self, 'logger_name_format', "%(name)s")
        message_format = getattr(self, 'message_format', "%(levelname)s - %(message)s")
        
        # Build the format string using custom components
        format_string = f"%(asctime)s - {logger_name_format} - {message_format} - %(filename)s:%(lineno)d"
        
        return logging.Formatter(format_string, datefmt=date_format)

    def _get_csv_formatter(self) -> logging.Formatter:
        """Get CSV formatter for structured log output."""
        date_format = getattr(self, 'date_format', "%Y-%m-%d %H:%M:%S")
        return logging.Formatter(
            "%(asctime)s,%(name)s,%(levelname)s,%(filename)s,%(lineno)d,%(message)s",
            datefmt=date_format,
        )

    def _get_syslog_formatter(self) -> logging.Formatter:
        """Get syslog-compatible formatter."""
        return logging.Formatter("%(name)s[%(process)d]: %(levelname)s: %(message)s")

    def _get_gelf_formatter(self) -> logging.Formatter:
        """Get GELF-compatible formatter (basic structure)."""
        return logging.Formatter("%(message)s")  # GELF handler will add the structure
    
    def _get_colored_file_formatter(self) -> logging.Formatter:
        """Get a formatter that includes ANSI colors for file output."""
        return ColoredTextFormatter()

    def _get_calling_module_name(self) -> str:
        """
        Get the name of the calling module for automatic module name detection.
        
        Returns:
            str: The name of the calling module or 'DEFAULT' as fallback.
        """
        try:
            import inspect
            # Get the frame of the calling function (2 levels up: current -> logging method -> caller)
            frame = inspect.currentframe()
            if frame:
                # Go up 2 levels to get the caller's frame
                caller_frame = frame.f_back
                if caller_frame:
                    caller_frame = caller_frame.f_back
                    if caller_frame:
                        module_name = caller_frame.f_globals.get('__name__', 'DEFAULT')
                        # Clean up the module name (remove package prefixes if desired)
                        if module_name != '__main__':
                            return module_name
        except Exception:
            pass
        return 'DEFAULT'

    def _log_with_auto_detection(self, level: str, layer_or_message: str, message: Optional[str] = None) -> None:
        """
        Log with automatic module name detection.
        
        Args:
            level (str): Log level (debug, info, warning, error, critical)
            layer_or_message (str): Either layer name or message (if no layer provided)
            message (Optional[str]): Message (if layer was provided in layer_or_message)
        """
        if message is None:
            # Single argument: use automatic module name detection
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            # Two arguments: explicit layer and message
            layer = layer_or_message
            
        # Call the appropriate logging method
        log_method = getattr(self, level.lower())
        log_method(layer, message)

    def _parse_size(self, size_str: str) -> int:
        """
        Parse size string to bytes.

        Args:
            size_str (str): Size string like "5MB", "1GB", "1024", etc.

        Returns:
            int: Size in bytes.

        Raises:
            ValueError: If the size string format is invalid or empty.

        This method supports various size formats:
        - KB: Kilobytes (e.g., "1KB" = 1024 bytes)
        - MB: Megabytes (e.g., "5MB" = 5,242,880 bytes)
        - GB: Gigabytes (e.g., "1GB" = 1,073,741,824 bytes)
        - B: Bytes (e.g., "1024B" = 1024 bytes)
        - Raw numbers: Assumed to be bytes (e.g., "1024" = 1024 bytes)
        """
        if not size_str:
            raise ValueError("Size string cannot be empty")

        size_str = size_str.upper().strip()

        try:
            if size_str.endswith("KB"):
                return int(size_str[:-2]) * 1024
            elif size_str.endswith("MB"):
                return int(size_str[:-2]) * 1024 * 1024
            elif size_str.endswith("GB"):
                return int(size_str[:-2]) * 1024 * 1024 * 1024
            elif size_str.endswith("B"):
                return int(size_str[:-1])
            else:
                # Assume bytes if no unit specified
                return int(size_str)
        except ValueError as e:
            raise ValueError(f"Invalid size format '{size_str}': {e}") from e

    def log(self, layer: str, level: str, message: str) -> None:
        """
        Log a message to a specific layer.

        Args:
            layer (str): Layer name to log to.
            level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            message (str): Message to log.

        Raises:
            ValueError: If the log level is invalid.

        This method provides the core logging functionality, routing messages
        to the appropriate layer and handling log level validation. It includes
        fallback mechanisms to ensure messages are logged even if the specific
        level method fails.
        """
        if not message:
            return  # Skip empty messages

        # Redact sensitive data if enabled
        if self.redact_sensitive:
            message = redact_sensitive_data(message)

        # Start performance monitoring if enabled
        start_time = None
        if self._performance_monitor:
            start_time = self._performance_monitor.start_log_processing_timer()

        try:
            # Normalize the level
            level = level.upper()

            # Validate the level
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if level not in valid_levels:
                raise ValueError(
                    f"Invalid log level '{level}'. Must be one of {valid_levels}"
                )

            # Get or create logger for the layer
            logger = self._get_or_create_logger(layer)

            # Log the message
            try:
                log_method = getattr(logger, level.lower())
                log_method(message)
            except Exception as e:
                # Fallback to info level if the specific level fails
                self._log_error(f"Failed to log {level} message to layer '{layer}': {e}")
                if self._performance_monitor:
                    self._performance_monitor.record_error()
                logger.info(message)
            
            # Record error if this was an error level message
            if self._performance_monitor and level == "ERROR":
                self._performance_monitor.record_error()
        finally:
            # End performance monitoring if enabled
            if self._performance_monitor and start_time:
                self._performance_monitor.end_log_processing_timer(start_time)
                # Check memory usage periodically
                self._performance_monitor.check_memory_usage()

    def debug(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "DEBUG", message)

    def info(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "INFO", message)

    def warning(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "WARNING", message)

    def error(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "ERROR", message)

    def critical(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "CRITICAL", message)

    def security(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """
        Log a security event with automatic redaction.
        
        Args:
            layer_or_message (str): Layer name or message
            message (Optional[str]): Message if layer was provided
        """
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None or message.strip() == "":
            return
        
        # Always redact sensitive data for security events
        redacted_message = redact_sensitive_data(message)
        self.log(layer, "WARNING", f"[SECURITY] {redacted_message}")

    def audit(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """
        Log an audit event with comprehensive tracking.
        
        Args:
            layer_or_message (str): Layer name or message
            message (Optional[str]): Message if layer was provided
        """
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None or message.strip() == "":
            return
        
        # Add audit context
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        audit_message = f"[AUDIT] {timestamp} - {message}"
        
        # Audit events are always redacted
        original_redact_setting = self.redact_sensitive
        self.redact_sensitive = True
        try:
            self.log(layer, "INFO", audit_message)
        finally:
            self.redact_sensitive = original_redact_setting

    def compliance(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """
        Log a compliance event with regulatory tracking.
        
        Args:
            layer_or_message (str): Layer name or message
            message (Optional[str]): Message if layer was provided
        """
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None or message.strip() == "":
            return
        
        # Add compliance context
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        compliance_message = f"[COMPLIANCE] {timestamp} - {message}"
        
        # Compliance events are always redacted
        original_redact_setting = self.redact_sensitive
        self.redact_sensitive = True
        try:
            self.log(layer, "INFO", compliance_message)
        finally:
            self.redact_sensitive = original_redact_setting

    def get_logger(self, layer: str) -> logging.Logger:
        """
        Get the underlying logging.Logger for a layer.

        Args:
            layer (str): Layer name.

        Returns:
            logging.Logger: Configured logging.Logger instance.

        This method provides access to the underlying Python logging.Logger
        instance for advanced usage scenarios where direct access to the
        logger is needed.
        """
        return self.loggers.get(layer, logging.getLogger(layer))

    def get_performance_statistics(self) -> Optional[Dict[str, float]]:
        """
        Get current performance statistics if performance monitoring is enabled.

        Returns:
            Optional[Dict[str, float]]: Performance statistics or None if monitoring is disabled.

        This method provides access to performance metrics including:
        - Uptime in seconds
        - Total messages processed
        - Error rate
        - Average/max/min processing times
        - Memory usage statistics
        - Messages per second
        """
        if self._performance_monitor:
            return self._performance_monitor.get_statistics()
        return None

    def reset_performance_statistics(self) -> None:
        """
        Reset all performance statistics if performance monitoring is enabled.
        
        This method clears all collected performance data and starts fresh.
        """
        if self._performance_monitor:
            self._performance_monitor.reset_statistics()

    def _log_warning(self, message: str) -> None:
        """
        Log a warning message to stderr.

        Args:
            message (str): Warning message to log.

        This internal method provides a simple way to log warnings
        during logger setup and operation when the logging system
        itself may not be fully initialized.
        """
        print(f"WARNING: {message}", file=sys.stderr)

    def _log_error(self, message: str) -> None:
        """
        Log an error message to stderr.

        Args:
            message (str): Error message to log.

        This internal method provides a simple way to log errors
        during logger setup and operation when the logging system
        itself may not be fully initialized.
        """
        print(f"ERROR: {message}", file=sys.stderr)

    def _auto_detect_config(self) -> LoggingConfig:
        """
        Auto-detect environment and create appropriate configuration.
        
        Returns:
            LoggingConfig: Configuration based on detected environment.
            
        This method detects the current environment (development, production, 
        testing) and creates an appropriate configuration with sensible defaults.
        """
        import platform
        
        # Detect environment
        env = os.getenv('ENVIRONMENT', '').lower()
        if not env:
            if os.getenv('FLASK_ENV') == 'development':
                env = 'development'
            elif os.getenv('DJANGO_SETTINGS_MODULE'):
                env = 'production' if os.getenv('DJANGO_DEBUG') != 'True' else 'development'
            elif os.getenv('NODE_ENV'):
                node_env = os.getenv('NODE_ENV')
                env = node_env.lower() if node_env else 'development'
            else:
                # Default to development if no clear indicators
                env = 'development'
        
        # Detect if running in container
        is_container = os.path.exists('/.dockerenv') or os.getenv('KUBERNETES_SERVICE_HOST')
        
        # Detect if running in CI/CD
        is_ci = bool(os.getenv('CI') or os.getenv('GITHUB_ACTIONS') or 
                     os.getenv('GITLAB_CI') or os.getenv('TRAVIS'))
        
        # Detect cloud environments
        is_aws = bool(os.getenv('AWS_REGION') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'))
        is_gcp = bool(os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('K_SERVICE'))
        is_azure = bool(os.getenv('AZURE_FUNCTIONS_ENVIRONMENT') or os.getenv('WEBSITE_SITE_NAME'))
        is_cloud = is_aws or is_gcp or is_azure
        
        # Create base configuration
        config = LoggingConfig(
            layers={}
        )
        
        # Environment-specific configurations
        if env == 'development':
            config.layers = {
                "DEFAULT": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/app.log", format="text")
                    ]
                ),
                "debug": LogLayer(
                    level="DEBUG", 
                    destinations=[
                        LogDestination(type="file", path="logs/debug.log", format="json")
                    ]
                )
            }
        elif env == 'production':
            # Production configuration with cloud awareness
            app_destinations = []
            
            # In cloud environments, prefer console output for better log aggregation
            if is_cloud:
                app_destinations.append(LogDestination(type="console", format="json"))
            else:
                app_destinations.append(LogDestination(type="file", path="logs/app.log", format="json"))
                if not is_container:
                    app_destinations.append(LogDestination(type="file", path="logs/app.log", format="gelf"))
            
            config.layers = {
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=app_destinations
                ),
                "error": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console" if is_cloud else "file", 
                                     path="logs/error.log" if not is_cloud else None, 
                                     format="json")
                    ]
                ),
                "security": LogLayer(
                    level="WARNING",
                    destinations=[
                        LogDestination(type="console" if is_cloud else "file", 
                                     path="logs/security.log" if not is_cloud else None, 
                                     format="json")
                    ]
                )
            }
        elif env == 'testing':
            config.layers = {
                "DEFAULT": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="file", path="logs/test.log", format="json")
                    ]
                )
            }
        else:
            # Fallback configuration
            config.layers = {
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/app.log", format="text")
                    ]
                )
            }
        
        # Adjust for container environments
        if is_container:
            # In containers, prefer console output and structured formats
            for layer in config.layers.values():
                for dest in layer.destinations:
                    if dest.type == "file" and dest.format == "text":
                        dest.format = "json"
        
        # Adjust for CI environments
        if is_ci:
            # In CI, prefer console output and minimal file logging
            for layer in config.layers.values():
                layer.destinations = [d for d in layer.destinations if d.type == "console"]
                if not layer.destinations:
                    layer.destinations = [LogDestination(type="console", format="text")]
        
        return config

    def _ensure_initialized(self) -> None:
        """
        Ensure loggers are initialized (for lazy initialization).
        
        This method is called before the first log operation to ensure
        all loggers and handlers are properly set up.
        """
        if not self.lazy_initialization or self._initialized:
            return
            
        with self._logger_init_lock:
            if self._initialized:
                return
                
            try:
                # Create directories if they don't exist
                create_log_directories(self.config)
            except OSError as dir_err:
                self._log_warning(f"Directory creation failed: {dir_err}. Falling back to console logging for all layers.")
                for layer in self.config.layers.values():
                    layer.destinations = [
                        d if d.type == "console" else LogDestination(type="console", level=d.level, format=getattr(d, "format", "text"))
                        for d in layer.destinations
                    ]
            except Exception as e:
                self._log_error(f"Failed to setup loggers: {e}")
                raise HydraLoggerError(f"Failed to setup loggers: {e}") from e
            
            # Setup each configured layer
            for layer_name, layer_config in self.config.layers.items():
                self._setup_single_layer(layer_name, layer_config)
                
            self._initialized = True

    def _get_or_create_logger(self, layer: str) -> logging.Logger:
        """
        Get existing logger or create a new one for unknown layers.
        Lazily initializes loggers and handlers for the layer on first use.
        Thread-safe.
        """
        # Ensure initialization for lazy initialization mode
        self._ensure_initialized()
        
        if layer in self.loggers:
            return self.loggers[layer]
        with self._logger_init_lock:
            if layer in self.loggers:
                return self.loggers[layer]
            
            # Create a minimal logger object that won't fail
            class DummyLogger:
                def __init__(self, name, default_level="INFO"):
                    self.name = name
                    self.level = getattr(logging, default_level)
                    self.handlers = []
                
                def setLevel(self, level):
                    self.level = level
                
                def addHandler(self, handler):
                    self.handlers.append(handler)
                
                def hasHandlers(self):
                    return len(self.handlers) > 0
                
                def debug(self, msg):
                    pass
                
                def info(self, msg):
                    pass
                
                def warning(self, msg):
                    pass
                
                def error(self, msg):
                    pass
                
                def critical(self, msg):
                    pass
            
            # Find layer config or fallback
            layer_config = self.config.layers.get(layer)
            original_layer = layer  # Keep track of original layer name
            if not layer_config and "DEFAULT" in self.config.layers:
                layer_config = self.config.layers["DEFAULT"]
                layer = "DEFAULT"
            if not layer_config:
                # Create a simple logger for unknown layers
                try:
                    logger = logging.getLogger(original_layer)  # Use original layer name
                    logger.setLevel(getattr(logging, self.config.default_level))
                    if not logger.handlers:
                        console_handler = logging.StreamHandler(sys.stdout)
                        console_handler.setLevel(getattr(logging, self.config.default_level))
                        console_handler.setFormatter(self._get_formatter())
                        logger.addHandler(console_handler)
                    self.loggers[original_layer] = logger  # Store with original name
                    return logger
                except Exception as e:
                    # If logger creation fails, create a minimal fallback
                    self._log_error(f"Failed to create logger for '{original_layer}': {e}")
                    try:
                        minimal_logger = logging.getLogger(original_layer)
                        minimal_logger.setLevel(getattr(logging, layer_config.level if layer_config else self.config.default_level))
                        self.loggers[original_layer] = minimal_logger  # Store with original name
                        return minimal_logger
                    except Exception as fallback_error:
                        # If even the fallback fails, create a dummy logger object
                        self._log_error(f"Fallback logger creation failed for '{original_layer}': {fallback_error}")
                        dummy_logger = DummyLogger(original_layer, layer_config.level if layer_config else self.config.default_level)
                        self.loggers[original_layer] = dummy_logger  # type: ignore
                        return dummy_logger  # type: ignore
            # Create and configure logger for this layer
            try:
                logger = logging.getLogger(original_layer)  # Use original layer name
                logger.setLevel(getattr(logging, layer_config.level))
                if logger.hasHandlers():
                    logger.handlers.clear()
                valid_handlers = 0
                for destination in layer_config.destinations:
                    handler = self._create_handler(destination, layer_config.level)
                    if handler:
                        logger.addHandler(handler)
                        valid_handlers += 1
                if valid_handlers == 0:
                    self._log_warning(
                        f"No valid handlers created for layer '{original_layer}'. Layer will not log to any destination."
                    )
                self.loggers[original_layer] = logger  # Store with original name
                return logger
            except Exception as e:
                # If logger creation fails, create a minimal fallback
                self._log_error(f"Failed to create logger for '{original_layer}': {e}")
                try:
                    minimal_logger = logging.getLogger(original_layer)
                    minimal_logger.setLevel(getattr(logging, layer_config.level))
                    self.loggers[original_layer] = minimal_logger  # Store with original name
                    return minimal_logger
                except Exception as fallback_error:
                    # If even the fallback fails, create a dummy logger object
                    self._log_error(f"Fallback logger creation failed for '{original_layer}': {fallback_error}")
                    dummy_logger = DummyLogger(original_layer, layer_config.level)
                    self.loggers[original_layer] = dummy_logger  # type: ignore
                    return dummy_logger  # type: ignore

    @classmethod
    def for_fastapi(cls, app=None, **kwargs) -> 'HydraLogger':
        """
        One-line FastAPI setup with magic configuration.
        
        Args:
            app: FastAPI app instance (optional)
            **kwargs: Additional logger configuration
        
        Returns:
            HydraLogger: Configured logger instance
        """
        from hydra_logger.framework_integration import MagicConfig, FrameworkDetector
        logger = MagicConfig._setup_fastapi(FrameworkDetector.detect_environment())
        
        # Apply additional configuration
        for key, value in kwargs.items():
            setattr(logger, key, value)
        
        # Setup middleware if app is provided
        if app is not None:
            logger.setup_fastapi_middleware(app)
        
        return logger
    
    @classmethod
    def for_django(cls, settings_module=None, **kwargs) -> 'HydraLogger':
        """
        One-line Django setup with magic configuration.
        
        Args:
            settings_module: Django settings module (optional)
            **kwargs: Additional logger configuration
        
        Returns:
            HydraLogger: Configured logger instance
        """
        from hydra_logger.framework_integration import MagicConfig, FrameworkDetector
        logger = MagicConfig._setup_django(FrameworkDetector.detect_environment())
        
        # Apply additional configuration
        for key, value in kwargs.items():
            setattr(logger, key, value)
        
        # Setup settings if module is provided
        if settings_module is not None:
            logger.setup_django_settings(settings_module)
        
        return logger
    
    @classmethod
    def for_flask(cls, app=None, **kwargs) -> 'HydraLogger':
        """
        One-line Flask setup with magic configuration.
        
        Args:
            app: Flask app instance (optional)
            **kwargs: Additional logger configuration
        
        Returns:
            HydraLogger: Configured logger instance
        """
        from hydra_logger.framework_integration import MagicConfig, FrameworkDetector
        logger = MagicConfig._setup_flask(FrameworkDetector.detect_environment())
        
        # Apply additional configuration
        for key, value in kwargs.items():
            setattr(logger, key, value)
        
        # Setup extension if app is provided
        if app is not None:
            logger.setup_flask_extension(app)
        
        return logger
    
    @classmethod
    def for_web_app(cls, **kwargs) -> 'HydraLogger':
        """
        One-line web application setup with magic configuration.
        
        Args:
            **kwargs: Additional logger configuration
        
        Returns:
            HydraLogger: Configured logger instance
        """
        from hydra_logger.framework_integration import FrameworkDetector
        
        framework = FrameworkDetector.detect_framework()
        
        if framework == 'fastapi':
            return cls.for_fastapi(**kwargs)
        elif framework == 'django':
            return cls.for_django(**kwargs)
        elif framework == 'flask':
            return cls.for_flask(**kwargs)
        else:
            # Generic web app configuration
            config = LoggingConfig(
                layers={
                    "WEB": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", format="text"),
                            LogDestination(type="file", path="logs/_tests_logs/web.log", format="json")
                        ]
                    ),
                    "REQUEST": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", format="text"),
                            LogDestination(type="file", path="logs/_tests_logs/request.log", format="json")
                        ]
                    ),
                                    "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/error.log", format="json")
                    ]
                )
                }
            )
            
            return cls(config=config, **kwargs)
    
    @classmethod
    def for_microservice(cls, **kwargs) -> 'HydraLogger':
        """
        One-line microservice setup with magic configuration.
        
        Args:
            **kwargs: Additional logger configuration
        
        Returns:
            HydraLogger: Configured logger instance
        """
        config = LoggingConfig(
            layers={
                "SERVICE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="json"),
                        LogDestination(type="file", path="logs/_tests_logs/service.log", format="json")
                    ]
                ),
                "METRICS": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="json"),
                        LogDestination(type="file", path="logs/_tests_logs/metrics.log", format="json")
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console", format="json"),
                        LogDestination(type="file", path="logs/_tests_logs/error.log", format="json")
                    ]
                )
            }
        )
        
        return cls(config=config, **kwargs)
    
    @classmethod
    def for_cli_tool(cls, **kwargs) -> 'HydraLogger':
        """
        One-line CLI tool setup with magic configuration.
        
        Args:
            **kwargs: Additional logger configuration
        
        Returns:
            HydraLogger: Configured logger instance
        """
        config = LoggingConfig(
            layers={
                "CLI": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text")
                    ]
                ),
                "DEBUG": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/debug.log", format="text")
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/error.log", format="text")
                    ]
                )
            }
        )
        
        return cls(config=config, **kwargs)
    
    def setup_fastapi_middleware(self, app):
        """Setup FastAPI middleware for automatic request logging."""
        try:
            # Only import if FastAPI is available
            import fastapi  # type: ignore
            from fastapi import Request, Response  # type: ignore
            from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore
            
            class FastAPILoggingMiddleware(BaseHTTPMiddleware):
                def __init__(self, app, logger):
                    super().__init__(app)
                    self.logger = logger
                
                async def dispatch(self, request: Request, call_next):
                    # Log request start
                    self.logger.info("HTTP", f"Request started: {request.method} {request.url.path}")
                    
                    # Process request
                    response = await call_next(request)
                    
                    # Log response
                    self.logger.info("HTTP", f"Response completed: {request.method} {request.url.path} - {response.status_code}")
                    
                    return response
            
            # Add middleware to app
            app.add_middleware(FastAPILoggingMiddleware, logger=self)
            
        except ImportError:
            # FastAPI not available, skip middleware setup
            pass
    
    def setup_django_settings(self, settings_module):
        """Setup Django settings for automatic logging configuration."""
        try:
            # Only import if Django is available
            import django  # type: ignore
            
            # Configure Django logging
            settings_module.LOGGING = {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'hydra': {
                        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        'datefmt': '%Y-%m-%d %H:%M:%S',
                    },
                },
                'handlers': {
                    'hydra_console': {
                        'class': 'logging.StreamHandler',
                        'formatter': 'hydra',
                        'level': 'INFO',
                    },
                    'hydra_file': {
                        'class': 'logging.handlers.RotatingFileHandler',
                        'filename': 'django.log',
                        'maxBytes': 1024 * 1024,  # 1MB
                        'backupCount': 5,
                        'formatter': 'hydra',
                        'level': 'INFO',
                    },
                },
                'loggers': {
                    'django': {
                        'handlers': ['hydra_console', 'hydra_file'],
                        'level': 'INFO',
                        'propagate': False,
                    },
                    'django.request': {
                        'handlers': ['hydra_console', 'hydra_file'],
                        'level': 'WARNING',
                        'propagate': False,
                    },
                },
                'root': {
                    'handlers': ['hydra_console', 'hydra_file'],
                    'level': 'INFO',
                },
            }
            
        except ImportError:
            # Django not available, skip settings setup
            pass
    
    def setup_flask_extension(self, app):
        """Setup Flask extension for automatic request logging."""
        try:
            # Only import if Flask is available
            import flask  # type: ignore
            from flask import request, g  # type: ignore
            
            @app.before_request
            def before_request():
                self.info("HTTP", f"Request started: {request.method} {request.path}")
            
            @app.after_request
            def after_request(response):
                self.info("HTTP", f"Response completed: {request.method} {request.path} - {response.status_code}")
                return response
            
            @app.errorhandler(Exception)
            def error_handler(error):
                self.error("HTTP", f"Error in {request.method} {request.path}: {str(error)}")
                return error
            
        except ImportError:
            # Flask not available, skip extension setup
            pass

class JupyterHandler(logging.StreamHandler):
    """
    Custom handler for Jupyter notebooks that renders HTML colors properly.
    
    This handler detects when it's running in a Jupyter environment and uses
    IPython.display.HTML() to render colored output instead of plain text.
    """
    
    def __init__(self, stream=None):
        super().__init__(stream)
        self._in_jupyter = self._detect_jupyter()
        self._display_html = None
        
        if self._in_jupyter:
            try:
                from IPython.display import display, HTML  # type: ignore
                self._display_html = lambda html: display(HTML(html))
            except ImportError:
                self._in_jupyter = False
    
    def _detect_jupyter(self) -> bool:
        """Detect if we're running in a Jupyter environment."""
        try:
            import IPython  # type: ignore
            return IPython.get_ipython() is not None
        except ImportError:
            return False
    
    def emit(self, record):
        """
        Emit a record. If in Jupyter and the formatter produces HTML, render it as HTML.
        Otherwise, fall back to normal stream handling.
        """
        try:
            msg = self.format(record)
            
            # Check if the message contains HTML color codes
            if (self._in_jupyter and self._display_html and 
                '<span style="color:' in msg):
                # Render as HTML in Jupyter
                self._display_html(msg)
            else:
                # Fall back to normal stream output
                stream = self.stream
                stream.write(msg + self.terminator)
                self.flush()
                
        except Exception:
            self.handleError(record)
