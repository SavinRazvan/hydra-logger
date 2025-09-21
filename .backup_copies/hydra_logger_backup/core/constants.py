"""
System Constants and Enums for Hydra-Logger

This module defines all the core constants, enums, and configuration values
used throughout the Hydra-Logger system. It provides a centralized location
for all system-wide constants and ensures consistency across all components.

CONSTANT CATEGORIES:
- Color Codes: ANSI escape sequences for terminal output
- Log Levels: Numeric and string representations of log levels
- Queue Policies: Backpressure handling strategies
- Shutdown Phases: Component lifecycle phases
- System Constants: Buffer sizes, timeouts, thresholds
- Format Constants: Supported format types and configurations
- Security Constants: Sensitive data patterns and threat detection
- Monitoring Constants: Performance and health thresholds

COLOR SYSTEM:
- Comprehensive ANSI color code support
- Basic, bright, and background colors
- Layer-specific color mappings
- Consistent with ColoredFormatter color scheme
- Cross-platform terminal compatibility

FORMAT SUPPORT:
- 13 standardized format types
- Consistent format names across all loggers
- Unified column system for structured formats
- Format validation and compatibility checking

SECURITY FEATURES:
- Sensitive data pattern detection
- Threat pattern recognition
- Security level configurations
- Data sanitization patterns

USAGE EXAMPLES:

Color Usage:
    from hydra_logger.core.constants import Colors
    
    # Basic colors
    print(Colors.RED + "Error" + Colors.RESET)
    print(Colors.GREEN + "Success" + Colors.RESET)
    
    # Layer-specific colors
    color = Colors.get_layer_color('api')  # Returns API-specific color
    
    # Color by name
    color = Colors.get_color_code('bright_blue')

Format Validation:
    from hydra_logger.core.constants import SUPPORTED_FORMATS
    
    if 'json-lines' in SUPPORTED_FORMATS:
        formatter = get_formatter('json-lines')

System Constants:
    from hydra_logger.core.constants import DEFAULT_BUFFER_SIZE, DEFAULT_FLUSH_INTERVAL
    
    processor = BatchProcessor(
        buffer_size=DEFAULT_BUFFER_SIZE,
        flush_interval=DEFAULT_FLUSH_INTERVAL
    )

Queue Policies:
    from hydra_logger.core.constants import QueuePolicy
    
    if policy == QueuePolicy.DROP_OLDEST:
        # Handle backpressure by dropping oldest messages
        pass
"""

from enum import Enum, IntEnum
from typing import Dict, Any

# =============================================================================
# COLOR CODES
# =============================================================================

class Colors:
    """
    ANSI color codes for terminal output.
    
    Usage:
        Colors.RED + "Error message" + Colors.RESET
        Colors.BRIGHT_GREEN + "Success" + Colors.RESET
        Colors.BG_RED + "Background" + Colors.RESET
    """
    
    # Reset
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Basic colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Bright background colors
    BG_BRIGHT_BLACK = "\033[100m"
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"
    
    @classmethod
    def get_color_code(cls, color_name: str) -> str:
        """
        Get ANSI color code from color name.
        
        Args:
            color_name: Color name (e.g., 'red', 'bright_blue', 'cyan')
            
        Returns:
            ANSI color code string
        """
        color_map = {
            # Basic colors
            "black": cls.BLACK,
            "red": cls.RED,
            "green": cls.GREEN,
            "yellow": cls.YELLOW,
            "blue": cls.BLUE,
            "magenta": cls.MAGENTA,
            "cyan": cls.CYAN,
            "white": cls.WHITE,
            
            # Bright colors
            "bright_black": cls.BRIGHT_BLACK,
            "bright_red": cls.BRIGHT_RED,
            "bright_green": cls.BRIGHT_GREEN,
            "bright_yellow": cls.BRIGHT_YELLOW,
            "bright_blue": cls.BRIGHT_BLUE,
            "bright_magenta": cls.BRIGHT_MAGENTA,
            "bright_cyan": cls.BRIGHT_CYAN,
            "bright_white": cls.BRIGHT_WHITE,
        }
        
        return color_map.get(color_name.lower(), cls.WHITE)  # Default to white
    
    @classmethod
    def get_layer_color(cls, layer_name: str) -> str:
        """
        Get default color for common layer types.
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            ANSI color code string
        """
        layer_colors = {
            "DEFAULT": cls.MAGENTA,  # FIXED: Match ColoredFormatter default
            "APP": cls.CYAN,
            "API": cls.BRIGHT_BLUE,  # FIXED: Match ColoredFormatter (94m)
            "DATABASE": cls.BLUE,
            "SECURITY": cls.RED,
            "PERFORMANCE": cls.YELLOW,
            "ERROR": cls.BRIGHT_RED,
            "AUDIT": cls.GREEN,
            "NETWORK": cls.BRIGHT_BLUE,
            "CACHE": cls.BRIGHT_YELLOW,
            "QUEUE": cls.MAGENTA,  # FIXED: Match ColoredFormatter
            "WORKER": cls.CYAN,
            "WEB": cls.GREEN,  # FIXED: Match ColoredFormatter
            "MICROSERVICE": cls.BRIGHT_BLACK,
            "BATCH": cls.RED,  # FIXED: Match ColoredFormatter
            "TEST": cls.BRIGHT_WHITE,
        }
        
        return layer_colors.get(layer_name.upper(), cls.WHITE)

# =============================================================================
# LOG LEVELS
# =============================================================================

# Log levels are now defined in hydra_logger.types.levels
# Import LogLevel and LogLevelManager from there instead

# =============================================================================
# QUEUE POLICIES
# =============================================================================

class QueuePolicy(Enum):
    """Queue backpressure policies."""
    
    DROP_OLDEST = "drop_oldest"
    BLOCK = "block"
    ERROR = "error"
    DISCARD = "discard"

# =============================================================================
# SHUTDOWN PHASES
# =============================================================================

class ShutdownPhase(Enum):
    """Shutdown phases for graceful shutdown."""
    
    RUNNING = "running"
    FLUSHING = "flushing"
    CLEANING = "cleaning"
    DONE = "done"



# =============================================================================
# SYSTEM CONSTANTS
# =============================================================================

# Buffer sizes
DEFAULT_BUFFER_SIZE = 8192
MIN_BUFFER_SIZE = 1024
MAX_BUFFER_SIZE = 1024 * 1024  # 1MB

# Flush intervals
DEFAULT_FLUSH_INTERVAL = 1.0
MIN_FLUSH_INTERVAL = 0.1
MAX_FLUSH_INTERVAL = 60.0

# Queue sizes
DEFAULT_QUEUE_SIZE = 1000
MIN_QUEUE_SIZE = 100
MAX_QUEUE_SIZE = 100000

# Timeouts
DEFAULT_TIMEOUT = 30.0
MIN_TIMEOUT = 1.0
MAX_TIMEOUT = 300.0

# Retry settings
DEFAULT_RETRY_COUNT = 3
MIN_RETRY_COUNT = 0
MAX_RETRY_COUNT = 10

# Memory thresholds
DEFAULT_MEMORY_THRESHOLD = 80.0  # 80%
MIN_MEMORY_THRESHOLD = 50.0
MAX_MEMORY_THRESHOLD = 95.0

# File rotation
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 5
MIN_BACKUP_COUNT = 1
MAX_BACKUP_COUNT = 100

# Health check intervals
DEFAULT_HEALTH_CHECK_INTERVAL = 30.0
MIN_HEALTH_CHECK_INTERVAL = 5.0
MAX_HEALTH_CHECK_INTERVAL = 300.0

# Plugin discovery
DEFAULT_PLUGIN_DISCOVERY_INTERVAL = 60.0
MIN_PLUGIN_DISCOVERY_INTERVAL = 10.0
MAX_PLUGIN_DISCOVERY_INTERVAL = 3600.0

# =============================================================================
# FORMAT CONSTANTS
# =============================================================================

# Supported formats
SUPPORTED_FORMATS = [
    "plain-text",
    "fast-plain",
    "json",
    "json-lines",
    "csv",
    "syslog",
    "gelf",
    "logstash",
    "binary",
    "binary-compact",
    "binary-extended",
    "detailed",
    "colored"
]

# CSV Headers - Centralized for all CSV formatters (using your unified LogColumn system)
# These headers match the LogColumn enum values exactly
# Each comment explains what logic/data is actually printed for that column:
# 
# IMPORTANT: All formatters (not just CSV) can use the same unified column system
# through the FormattingEngine. Users can customize which columns they want using:
# - create_minimal_engine() - timestamp, level_name, message only
# - create_standard_engine() - timestamp, level_name, layer, message, file_name
# - create_detailed_engine() - all core fields (timestamp, level_name, layer, file_name, function_name, message, level, logger_name, line_number, extra)
# - create_custom_engine(columns) - custom column selection
#
CSV_HEADERS = [
    "timestamp",      # record.timestamp - Unix timestamp (float) when log was created (e.g., 1234567890.123)
    "level_name",     # record.level_name - Human-readable log level from LogLevelManager (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    "layer",          # record.layer - Application layer string (default: "default", can be "API", "DATABASE", "BUSINESS", etc.)
    "file_name",      # record.file_name - Auto-detected from inspect.currentframe() call stack, or manually set
    "function_name",  # record.function_name - Auto-detected from inspect.currentframe() call stack, or manually set
    "message",        # record.message - The actual log message text passed by the user
    "level",          # record.level - Numeric log level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL)
    "logger_name",    # record.logger_name - Name of the logger instance
    "line_number",    # record.line_number - Auto-detected from inspect.currentframe() call stack, or manually set
    "extra"           # record.extra - Additional structured data as JSON string (e.g., {"user": "john", "action": "login"})
]

# Default format strings
DEFAULT_FORMAT_STRING = "[{timestamp}] [{level_name}] [{layer}] {message}"
DEFAULT_JSON_FORMAT = {
    "timestamp": True,
    "level_name": True,
    "layer": True,
    "file_name": True,
    "function_name": True,
    "message": True,
    "level": True,
    "logger_name": True,
    "line_number": True,
    "extra": True
}

# =============================================================================
# SECURITY CONSTANTS
# =============================================================================

# Sensitive data patterns
SENSITIVE_PATTERNS = [
    r"password\s*[:=]\s*\S+",
    r"api_key\s*[:=]\s*\S+",
    r"secret\s*[:=]\s*\S+",
    r"token\s*[:=]\s*\S+",
    r"key\s*[:=]\s*\S+"
]

# Threat patterns
THREAT_PATTERNS = [
    r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
    r"javascript:",
    r"vbscript:",
    r"onload\s*=",
    r"onerror\s*="
]

# =============================================================================
# MONITORING CONSTANTS
# =============================================================================

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "slow_operation": 1.0,              # seconds
    "high_memory": 512 * 1024 * 1024,   # 512MB
    "queue_backup": 1000,               # logs
    "error_rate": 0.05,                 # 5%
    "response_time": 0.1                # 100ms
}

# Health thresholds
HEALTH_THRESHOLDS = {
    "memory_usage": 80.0,              # 80%
    "error_rate": 0.1,                 # 10%
    "response_time": 1.0,              # 1 second
    "throughput": 100000               # logs per second
}
