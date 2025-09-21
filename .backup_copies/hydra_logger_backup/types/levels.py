"""
Log Level Definitions for Hydra-Logger

This module provides comprehensive log level definitions, constants, and
utilities for managing log levels throughout the system. It includes
level validation, conversion, and color mapping for console output.

FEATURES:
- LogLevel: Standard log levels with numeric values
- LogLevelManager: Utility class for level operations and validation
- Level validation and conversion functions
- Color mapping for console output
- Level comparison and filtering utilities

STANDARD LOG LEVELS:
- NOTSET (0): No level set
- DEBUG (10): Detailed information for debugging
- INFO (20): General information messages
- WARNING (30): Warning messages
- ERROR (40): Error messages
- CRITICAL (50): Critical error messages

LEVEL OPERATIONS:
- get_name(): Get string name for numeric level
- get_level(): Get numeric value for string level
- is_valid_level(): Validate level values
- all_levels(): Get all available levels
- all_names(): Get all level names
- get_color(): Get color code for console output
- is_enabled(): Check if message level is enabled
- normalize_level(): Normalize level to LogLevel enum

COLOR SYSTEM INTEGRATION:
- LogLevelManager.get_color() provides color codes for log levels
- Level-to-color mapping for console output
- Used by ColoredFormatter for level-specific colors
- Supports all standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Colors only work with console handlers (not file handlers)

USAGE:
    from hydra_logger.types import LogLevel, LogLevelManager
    
    # Use log levels
    if LogLevel.INFO >= LogLevel.DEBUG:
        print("Debug logging is enabled")
    
    # Convert between formats
    level_name = LogLevelManager.get_name(LogLevel.INFO)
    level_num = LogLevelManager.get_level("WARNING")
    
    # Validate levels
    if LogLevelManager.is_valid_level("ERROR"):
        print("Valid log level")
    
    # Get color for console output
    color = LogLevelManager.get_color(LogLevel.ERROR)
    print(f"Error color: {color}")
    
    # Check if level is enabled
    if LogLevelManager.is_enabled(LogLevel.INFO, LogLevel.DEBUG):
        print("Debug messages will be logged")
"""

from enum import IntEnum
from typing import Union, List, Optional
from functools import lru_cache


class LogLevel(IntEnum):
    """Standard log levels with numeric values."""
    NOTSET = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogLevelManager:
    """Utility class for log level operations and validation."""
    
    # Standard level mappings
    LEVEL_NAMES = {
        LogLevel.NOTSET: "NOTSET",
        LogLevel.DEBUG: "DEBUG", 
        LogLevel.INFO: "INFO",
        LogLevel.WARNING: "WARNING",
        LogLevel.ERROR: "ERROR",
        LogLevel.CRITICAL: "CRITICAL"
    }
    
    # String to level mapping
    NAME_TO_LEVEL = {
        "NOTSET": LogLevel.NOTSET,
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL,
        # Aliases for compatibility
        "WARN": LogLevel.WARNING,
        "FATAL": LogLevel.CRITICAL
    }
    
    # Level to color mapping (for console output)
    LEVEL_COLORS = {
        LogLevel.DEBUG: "cyan",
        LogLevel.INFO: "green", 
        LogLevel.WARNING: "yellow",
        LogLevel.ERROR: "red",
        LogLevel.CRITICAL: "bright_red"
    }
    
    @classmethod
    @lru_cache(maxsize=128)
    def get_name(cls, level: Union[int, LogLevel]) -> str:
        """Get the string name for a log level."""
        if isinstance(level, str):
            return level.upper()
        
        numeric_level = int(level)
        return cls.LEVEL_NAMES.get(numeric_level, "UNKNOWN")
    
    @classmethod
    @lru_cache(maxsize=128)
    def get_level(cls, level: Union[str, int, LogLevel]) -> int:
        """Get the numeric value for a log level."""
        if isinstance(level, int):
            return level
        elif isinstance(level, LogLevel):
            return int(level)
        elif isinstance(level, str):
            return cls.NAME_TO_LEVEL.get(level.upper(), LogLevel.INFO)
        else:
            return LogLevel.INFO
    
    @classmethod
    def is_valid_level(cls, level: Union[str, int, LogLevel]) -> bool:
        """Check if a log level is valid."""
        if isinstance(level, int):
            return level in cls.LEVEL_NAMES
        elif isinstance(level, LogLevel):
            return True
        elif isinstance(level, str):
            return level.upper() in cls.NAME_TO_LEVEL
        else:
            return False
    
    @classmethod
    def all_levels(cls) -> List[LogLevel]:
        """Get all available log levels."""
        return list(cls.LEVEL_NAMES.keys())
    
    @classmethod
    def all_names(cls) -> List[str]:
        """Get all available log level names."""
        return list(cls.NAME_TO_LEVEL.keys())
    
    @classmethod
    def get_color(cls, level: Union[str, int, LogLevel]) -> Optional[str]:
        """Get the color for a log level."""
        numeric_level = cls.get_level(level)
        return cls.LEVEL_COLORS.get(numeric_level)
    
    @classmethod
    def is_enabled(cls, current_level: Union[str, int, LogLevel], 
                   message_level: Union[str, int, LogLevel]) -> bool:
        """Check if a message level is enabled at the current level."""
        current = cls.get_level(current_level)
        message = cls.get_level(message_level)
        return message >= current
    
    @classmethod
    def normalize_level(cls, level: Union[str, int, LogLevel]) -> LogLevel:
        """Normalize a level to a LogLevel enum value."""
        numeric_level = cls.get_level(level)
        for enum_level in LogLevel:
            if int(enum_level) == numeric_level:
                return enum_level
        return LogLevel.INFO


# Convenience functions for backward compatibility
def get_level_name(level: Union[int, LogLevel]) -> str:
    """Get the string name for a log level."""
    return LogLevelManager.get_name(level)


def get_level(level: Union[str, int, LogLevel]) -> int:
    """Get the numeric value for a log level."""
    return LogLevelManager.get_level(level)


def is_valid_level(level: Union[str, int, LogLevel]) -> bool:
    """Check if a log level is valid."""
    return LogLevelManager.is_valid_level(level)


def all_levels() -> List[LogLevel]:
    """Get all available log levels."""
    return LogLevelManager.all_levels()


def all_level_names() -> List[str]:
    """Get all available log level names."""
    return LogLevelManager.all_names()


# Export the main classes and functions
__all__ = [
    "LogLevel",
    "LogLevelManager",
    "get_level_name",
    "get_level", 
    "is_valid_level",
    "all_levels",
    "all_level_names"
]
