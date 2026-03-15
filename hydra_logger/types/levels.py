"""
Role: Levels implementation.
Used By:
 - (update when known)
Depends On:
 - enum
 - typing
 - functools
Notes:
 - Header standardized by slim-header migration.
"""

from enum import IntEnum
from functools import lru_cache
from typing import Dict, List, Optional, Union


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
    LEVEL_NAMES: Dict[int, str] = {
        int(LogLevel.NOTSET): "NOTSET",
        int(LogLevel.DEBUG): "DEBUG",
        int(LogLevel.INFO): "INFO",
        int(LogLevel.WARNING): "WARNING",
        int(LogLevel.ERROR): "ERROR",
        int(LogLevel.CRITICAL): "CRITICAL",
    }

    # String to level mapping
    NAME_TO_LEVEL: Dict[str, int] = {
        "NOTSET": LogLevel.NOTSET,
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL,
        # Aliases for compatibility
        "WARN": LogLevel.WARNING,
        "FATAL": LogLevel.CRITICAL,
    }

    # Level to color mapping (for console output)
    LEVEL_COLORS: Dict[int, str] = {
        int(LogLevel.DEBUG): "cyan",
        int(LogLevel.INFO): "green",
        int(LogLevel.WARNING): "yellow",
        int(LogLevel.ERROR): "red",
        int(LogLevel.CRITICAL): "bright_red",
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
            return int(cls.NAME_TO_LEVEL.get(level.upper(), LogLevel.INFO))
        else:
            return int(LogLevel.INFO)

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
    def all_levels(cls) -> List[int]:
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
    def is_enabled(
        cls,
        current_level: Union[str, int, LogLevel],
        message_level: Union[str, int, LogLevel],
    ) -> bool:
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


def all_levels() -> List[int]:
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
    "all_level_names",
]
