"""
Time and Date Utilities for Hydra-Logger

This module provides comprehensive time and date utility functions including
timestamp formatting, timezone handling, duration calculations, and time
range operations. It follows industry standards (RFC 3339/ISO 8601) and
provides extensive configuration options.

FEATURES:
- TimeUtils: General time utility functions
- TimestampFormatter: Comprehensive timestamp formatting (RFC 3339/ISO 8601)
- DateFormatter: Date formatting and relative time display
- TimeZoneManager: Timezone handling and conversion
- TimeRange: Time range operations and calculations
- TimeInterval: Recurring time interval management
- TimeUtility: Time conversion and validation utilities
- Business day calculations and date arithmetic

TIMESTAMP FORMATS:
- RFC3339: Industry standard (2023-12-25T15:30:45Z)
- Unix timestamps: Seconds, milliseconds, microseconds, nanoseconds
- Human-readable: Various readable formats
- Compact: High-volume logging formats
- Legacy: Backward compatibility formats

TIMEZONE SUPPORT:
- UTC and local timezone handling
- Timezone conversion and offset calculation
- DST (Daylight Saving Time) detection
- Common timezone management
- Timezone information and metadata

USAGE:
    from hydra_logger.utils import TimeUtils, TimestampFormatter, TimeZoneManager
    
    # General time utilities
    now = TimeUtils.now()
    timestamp = TimeUtils.timestamp()
    formatted = TimeUtils.format_duration(3600)
    
    # Timestamp formatting
    rfc3339 = TimestampFormatter.get_current_timestamp(TimestampFormat.RFC3339)
    unix_ms = TimestampFormatter.get_current_timestamp(TimestampFormat.UNIX_MILLIS)
    custom = TimestampFormatter.format_timestamp(now, TimestampFormat.HUMAN_READABLE)
    
    # Timezone management
    tz_manager = TimeZoneManager()
    utc_time = tz_manager.convert_timezone(local_time, "UTC")
    offset = tz_manager.get_current_timezone_offset("America/New_York")
    
    # Time ranges and intervals
    from hydra_logger.utils import TimeRange, TimeInterval
    range_obj = TimeRange(start_time, end_time)
    duration = range_obj.duration_seconds
    interval = TimeInterval(1, TimeUnit.HOUR)
    delta = interval.to_timedelta()
"""

import time
import calendar
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union, Literal
from dataclasses import dataclass
from enum import Enum
import pytz


# Import the centralized TimeUnit from types
from hydra_logger.types.enums import TimeUnit


class TimestampFormat(Enum):
    """Standardized timestamp formats following industry standards.
    
    Based on RFC 3339/ISO 8601 standards used by major logging systems.
    """
    # RFC 3339 / ISO 8601 formats (industry standard)
    RFC3339 = "rfc3339"                    # 2023-12-25T15:30:45Z
    RFC3339_TZ = "rfc3339_tz"              # 2023-12-25T15:30:45+00:00
    RFC3339_MICRO = "rfc3339_micro"        # 2023-12-25T15:30:45.123456Z
    RFC3339_NANO = "rfc3339_nano"          # 2023-12-25T15:30:45.123456789Z
    
    # Unix timestamp formats
    UNIX_SECONDS = "unix_seconds"          # 1703514645
    UNIX_MILLIS = "unix_millis"            # 1703514645123
    UNIX_MICROS = "unix_micros"            # 1703514645123456
    UNIX_NANOS = "unix_nanos"              # 1703514645123456789
    
    # Human-readable formats
    HUMAN_READABLE = "human"               # 2023-12-25 15:30:45
    HUMAN_READABLE_TZ = "human_tz"         # 2023-12-25 15:30:45 UTC
    HUMAN_READABLE_MICRO = "human_micro"   # 2023-12-25 15:30:45.123456
    
    # Compact formats for high-volume logging
    COMPACT = "compact"                    # 20231225T153045Z
    COMPACT_MICRO = "compact_micro"        # 20231225T153045.123456Z
    
    # Legacy formats for compatibility
    LEGACY = "legacy"                      # 2023-12-25 15:30:45,123
    SYSLOG = "syslog"                      # Dec 25 15:30:45


class TimestampPrecision(Enum):
    """Timestamp precision levels."""
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds" 
    MICROSECONDS = "microseconds"
    NANOSECONDS = "nanoseconds"


@dataclass
class TimestampConfig:
    """Configuration for timestamp formatting.
    
    Provides easy configuration for users to choose their preferred
    timestamp format and precision across the entire logging system.
    """
    format_type: TimestampFormat = TimestampFormat.RFC3339
    precision: TimestampPrecision = TimestampPrecision.SECONDS
    timezone_name: Optional[str] = None
    include_timezone: bool = True
    
    # Preset configurations for common use cases
    @classmethod
    def rfc3339_standard(cls) -> "TimestampConfig":
        """Standard RFC3339 format (recommended for most use cases)."""
        return cls(
            format_type=TimestampFormat.RFC3339,
            precision=TimestampPrecision.SECONDS,
            timezone_name="UTC"
        )
    
    @classmethod
    def rfc3339_high_precision(cls) -> "TimestampConfig":
        """RFC3339 with microsecond precision (for performance monitoring)."""
        return cls(
            format_type=TimestampFormat.RFC3339_MICRO,
            precision=TimestampPrecision.MICROSECONDS,
            timezone_name="UTC"
        )
    
    @classmethod
    def unix_timestamp(cls) -> "TimestampConfig":
        """Unix timestamp format (for system integration)."""
        return cls(
            format_type=TimestampFormat.UNIX_SECONDS,
            precision=TimestampPrecision.SECONDS,
            timezone_name="UTC"
        )
    
    @classmethod
    def unix_millis(cls) -> "TimestampConfig":
        """Unix timestamp in milliseconds (for JavaScript compatibility)."""
        return cls(
            format_type=TimestampFormat.UNIX_MILLIS,
            precision=TimestampPrecision.MILLISECONDS,
            timezone_name="UTC"
        )
    
    @classmethod
    def human_readable(cls) -> "TimestampConfig":
        """Human-readable format (for development/debugging)."""
        return cls(
            format_type=TimestampFormat.HUMAN_READABLE,
            precision=TimestampPrecision.SECONDS,
            timezone_name="UTC"
        )
    
    @classmethod
    def compact(cls) -> "TimestampConfig":
        """Compact format (for high-volume logging)."""
        return cls(
            format_type=TimestampFormat.COMPACT,
            precision=TimestampPrecision.SECONDS,
            timezone_name="UTC"
        )
    
    @classmethod
    def legacy(cls) -> "TimestampConfig":
        """Legacy format (for backward compatibility)."""
        return cls(
            format_type=TimestampFormat.LEGACY,
            precision=TimestampPrecision.MILLISECONDS,
            timezone_name="UTC"
        )
    
    def format_timestamp(self, dt: datetime) -> str:
        """Format a datetime using this configuration."""
        return TimestampFormatter.format_timestamp(
            dt, 
            self.format_type, 
            self.precision, 
            self.timezone_name
        )
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp using this configuration."""
        return TimestampFormatter.get_current_timestamp(
            self.format_type,
            self.precision,
            self.timezone_name
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "format_type": self.format_type.value,
            "precision": self.precision.value,
            "timezone_name": self.timezone_name,
            "include_timezone": self.include_timezone
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TimestampConfig":
        """Create configuration from dictionary."""
        return cls(
            format_type=TimestampFormat(config_dict.get("format_type", "rfc3339")),
            precision=TimestampPrecision(config_dict.get("precision", "seconds")),
            timezone_name=config_dict.get("timezone_name"),
            include_timezone=config_dict.get("include_timezone", True)
        )


class DateFormat(Enum):
    """Common date format patterns (legacy - use TimestampFormat instead)."""

    ISO = "iso"
    ISO_SHORT = "iso_short"
    US = "us"
    EU = "eu"
    CUSTOM = "custom"


@dataclass
class TimeRange:
    """Represents a time range with start and end times."""

    start: datetime
    end: datetime

    def __post_init__(self):
        """Validate time range."""
        if self.start >= self.end:
            raise ValueError("Start time must be before end time")

    @property
    def duration(self) -> timedelta:
        """Get the duration of the time range."""
        return self.end - self.start

    @property
    def duration_seconds(self) -> float:
        """Get the duration in seconds."""
        return self.duration.total_seconds()

    @property
    def duration_minutes(self) -> float:
        """Get the duration in minutes."""
        return self.duration_seconds / 60

    @property
    def duration_hours(self) -> float:
        """Get the duration in hours."""
        return self.duration_seconds / 3600

    @property
    def duration_days(self) -> float:
        """Get the duration in days."""
        return self.duration_seconds / 86400

    def contains(self, dt: datetime) -> bool:
        """Check if a datetime is within this range."""
        return self.start <= dt <= self.end

    def overlaps(self, other: "TimeRange") -> bool:
        """Check if this range overlaps with another range."""
        return not (self.end <= other.start or other.end <= self.start)

    def intersection(self, other: "TimeRange") -> Optional["TimeRange"]:
        """Get the intersection of two time ranges."""
        if not self.overlaps(other):
            return None

        start = max(self.start, other.start)
        end = min(self.end, other.end)
        return TimeRange(start, end)

    def union(self, other: "TimeRange") -> "TimeRange":
        """Get the union of two time ranges."""
        start = min(self.start, other.start)
        end = max(self.end, other.end)
        return TimeRange(start, end)

    def split_by_unit(self, unit: TimeUnit, count: int = 1) -> List["TimeRange"]:
        """Split the time range into smaller ranges by time unit."""
        ranges = []
        current = self.start

        while current < self.end:
            # Use the centralized conversion method
            seconds_per_unit = unit.to_seconds()
            next_time = current + timedelta(seconds=seconds_per_unit * count)

            # Ensure we don't exceed the end time
            if next_time > self.end:
                next_time = self.end

            ranges.append(TimeRange(current, next_time))
            current = next_time

        return ranges

    def to_dict(self) -> Dict[str, Any]:
        """Convert time range to dictionary."""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_seconds": self.duration_seconds,
            "duration_minutes": self.duration_minutes,
            "duration_hours": self.duration_hours,
            "duration_days": self.duration_days,
        }


@dataclass
class TimeInterval:
    """Represents a time interval for recurring operations."""

    value: int
    unit: TimeUnit

    def to_timedelta(self) -> timedelta:
        """Convert interval to timedelta."""
        # Use the centralized conversion method
        seconds_per_unit = self.unit.to_seconds()
        return timedelta(seconds=seconds_per_unit * self.value)

    def __str__(self) -> str:
        """String representation of the interval."""
        unit_name = self.unit.value
        if self.value != 1:
            unit_name += "s"
        return f"{self.value} {unit_name}"


class TimeUtility:
    """Comprehensive time utility class for Hydra-Logger.
    
    Provides standardized time operations, conversions, and validations
    across the entire codebase.
    """
    
    @staticmethod
    def convert_time(value: float, from_unit: TimeUnit, to_unit: TimeUnit) -> float:
        """Convert time value from one unit to another.
        
        Args:
            value: The time value to convert
            from_unit: Source time unit
            to_unit: Target time unit
            
        Returns:
            Converted time value
            
        Example:
            >>> TimeUtility.convert_time(60, TimeUnit.SECONDS, TimeUnit.MINUTES)
            1.0
        """
        if from_unit == to_unit:
            return value
        
        # Convert to seconds first, then to target unit
        seconds = value * from_unit.to_seconds()
        return seconds / to_unit.to_seconds()
    
    @staticmethod
    def validate_rotation_interval(interval: int, unit: TimeUnit) -> bool:
        """Validate if a time interval is suitable for file rotation.
        
        Args:
            interval: The interval value
            unit: The time unit
            
        Returns:
            True if valid for rotation, False otherwise
        """
        if not unit.is_rotation_unit:
            return False
        
        if interval <= 0:
            return False
        
        # Check for reasonable rotation intervals
        min_seconds = 1  # Minimum 1 second
        max_seconds = 365 * 24 * 3600  # Maximum 1 year
        
        total_seconds = interval * unit.to_seconds()
        return min_seconds <= total_seconds <= max_seconds
    
    @staticmethod
    def get_optimal_rotation_unit(interval_seconds: float) -> TimeUnit:
        """Get the most appropriate time unit for a given interval in seconds.
        
        Args:
            interval_seconds: Interval in seconds
            
        Returns:
            Most appropriate TimeUnit
        """
        if interval_seconds < 60:
            return TimeUnit.SECONDS
        elif interval_seconds < 3600:
            return TimeUnit.MINUTES
        elif interval_seconds < 86400:
            return TimeUnit.HOURS
        elif interval_seconds < 604800:
            return TimeUnit.DAYS
        elif interval_seconds < 2592000:
            return TimeUnit.WEEKS
        elif interval_seconds < 31536000:
            return TimeUnit.MONTHS
        else:
            return TimeUnit.YEARS
    
    @staticmethod
    def format_duration(seconds: float, precision: int = 2) -> str:
        """Format a duration in seconds to a human-readable string.
        
        Args:
            seconds: Duration in seconds
            precision: Number of decimal places
            
        Returns:
            Formatted duration string
            
        Example:
            >>> TimeUtility.format_duration(3661.5)
            '1h 1m 1.5s'
        """
        if seconds < 1:
            return f"{seconds:.{precision}f}s"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if remaining_seconds > 0 or not parts:
            parts.append(f"{remaining_seconds:.{precision}f}s")
        
        return " ".join(parts)
    
    @staticmethod
    def parse_time_interval(interval_str: str) -> Tuple[int, TimeUnit]:
        """Parse a time interval string into value and unit.
        
        Args:
            interval_str: String like "5m", "2h", "1d"
            
        Returns:
            Tuple of (value, TimeUnit)
            
        Raises:
            ValueError: If string format is invalid
        """
        interval_str = interval_str.strip().lower()
        
        # Extract number and unit
        import re
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([a-z]+)$', interval_str)
        if not match:
            raise ValueError(f"Invalid time interval format: {interval_str}")
        
        value_str, unit_str = match.groups()
        value = float(value_str)
        
        # Map unit strings to TimeUnit
        unit_map = {
            'ns': TimeUnit.NANOSECONDS,
            'μs': TimeUnit.MICROSECONDS,
            'ms': TimeUnit.MILLISECONDS,
            's': TimeUnit.SECONDS,
            'sec': TimeUnit.SECONDS,
            'second': TimeUnit.SECONDS,
            'seconds': TimeUnit.SECONDS,
            'm': TimeUnit.MINUTES,
            'min': TimeUnit.MINUTES,
            'minute': TimeUnit.MINUTES,
            'minutes': TimeUnit.MINUTES,
            'h': TimeUnit.HOURS,
            'hour': TimeUnit.HOURS,
            'hours': TimeUnit.HOURS,
            'd': TimeUnit.DAYS,
            'day': TimeUnit.DAYS,
            'days': TimeUnit.DAYS,
            'w': TimeUnit.WEEKS,
            'week': TimeUnit.WEEKS,
            'weeks': TimeUnit.WEEKS,
            'M': TimeUnit.MONTHS,
            'month': TimeUnit.MONTHS,
            'months': TimeUnit.MONTHS,
            'y': TimeUnit.YEARS,
            'year': TimeUnit.YEARS,
            'years': TimeUnit.YEARS,
        }
        
        unit = unit_map.get(unit_str)
        if not unit:
            raise ValueError(f"Unknown time unit: {unit_str}")
        
        return int(value), unit


class TimestampFormatter:
    """Comprehensive timestamp formatter following industry standards.
    
    Supports multiple formats, precision levels, and timezone handling
    following RFC 3339/ISO 8601 standards used by major logging systems.
    """
    
    # Format templates for different timestamp formats
    FORMAT_TEMPLATES = {
        TimestampFormat.RFC3339: "%Y-%m-%dT%H:%M:%S%z",
        TimestampFormat.RFC3339_TZ: "%Y-%m-%dT%H:%M:%S%z",
        TimestampFormat.RFC3339_MICRO: "%Y-%m-%dT%H:%M:%S.%f%z",
        TimestampFormat.RFC3339_NANO: "%Y-%m-%dT%H:%M:%S.%f%z",  # Will be handled specially
        TimestampFormat.HUMAN_READABLE: "%Y-%m-%d %H:%M:%S",
        TimestampFormat.HUMAN_READABLE_TZ: "%Y-%m-%d %H:%M:%S %Z",
        TimestampFormat.HUMAN_READABLE_MICRO: "%Y-%m-%d %H:%M:%S.%f",
        TimestampFormat.COMPACT: "%Y%m%dT%H%M%SZ",
        TimestampFormat.COMPACT_MICRO: "%Y%m%dT%H%M%S.%fZ",
        TimestampFormat.LEGACY: "%Y-%m-%d %H:%M:%S,%f",
        TimestampFormat.SYSLOG: "%b %d %H:%M:%S",
    }
    
    @staticmethod
    def format_timestamp(
        dt: datetime, 
        format_type: TimestampFormat = TimestampFormat.RFC3339,
        precision: TimestampPrecision = TimestampPrecision.SECONDS,
        timezone_name: Optional[str] = None
    ) -> str:
        """Format a datetime object using standardized timestamp formats.
        
        Args:
            dt: Datetime object to format
            format_type: Type of timestamp format to use
            precision: Precision level for fractional seconds
            timezone_name: Timezone name (e.g., 'UTC', 'America/New_York')
            
        Returns:
            Formatted timestamp string
            
        Examples:
            >>> dt = datetime(2023, 12, 25, 15, 30, 45, 123456, tzinfo=timezone.utc)
            >>> TimestampFormatter.format_timestamp(dt, TimestampFormat.RFC3339)
            '2023-12-25T15:30:45Z'
            >>> TimestampFormatter.format_timestamp(dt, TimestampFormat.RFC3339_MICRO)
            '2023-12-25T15:30:45.123456Z'
        """
        # Handle timezone conversion if specified
        if timezone_name:
            if timezone_name.upper() == 'UTC':
                dt = dt.astimezone(timezone.utc)
            else:
                try:
                    tz = pytz.timezone(timezone_name)
                    dt = dt.astimezone(tz)
                except pytz.exceptions.UnknownTimeZoneError:
                    raise ValueError(f"Unknown timezone: {timezone_name}")
        
        # Ensure we have timezone info
        if dt.tzinfo is None:
            if timezone_name is None:
                # Local timezone - assume it's already in local time
                import time
                local_tz = timezone(timedelta(seconds=time.timezone if time.daylight == 0 else time.altzone))
                dt = dt.replace(tzinfo=local_tz)
            else:
                dt = dt.replace(tzinfo=timezone.utc)
        
        # Handle Unix timestamp formats
        if format_type in {TimestampFormat.UNIX_SECONDS, TimestampFormat.UNIX_MILLIS, 
                          TimestampFormat.UNIX_MICROS, TimestampFormat.UNIX_NANOS}:
            return TimestampFormatter._format_unix_timestamp(dt, format_type, precision)
        
        # Handle RFC3339_NANO format (special case for nanosecond precision)
        if format_type == TimestampFormat.RFC3339_NANO:
            return TimestampFormatter._format_nanosecond_timestamp(dt)
        
        # Get the format template
        template = TimestampFormatter.FORMAT_TEMPLATES.get(format_type)
        if not template:
            raise ValueError(f"Unsupported timestamp format: {format_type}")
        
        # Adjust precision for fractional seconds
        if precision == TimestampPrecision.SECONDS and '.%f' in template:
            template = template.replace('.%f', '')
        elif precision == TimestampPrecision.MILLISECONDS and '.%f' in template:
            # Keep only 3 digits for milliseconds
            formatted = dt.strftime(template)
            if '.' in formatted:
                parts = formatted.split('.')
                if len(parts[1]) > 3:
                    parts[1] = parts[1][:3]
                formatted = '.'.join(parts)
            return formatted
        
        # Format the timestamp
        formatted = dt.strftime(template)
        
        # Handle microsecond formatting for RFC3339_MICRO
        if format_type == TimestampFormat.RFC3339_MICRO:
            # The template should include .%f, but let's ensure proper formatting
            if '.%f' in template:
                # strftime should handle this, but let's ensure 6 digits
                if '.' in formatted:
                    parts = formatted.split('.')
                    if len(parts[1]) < 6:
                        parts[1] = parts[1].ljust(6, '0')
                    formatted = '.'.join(parts)
            else:
                # Add microseconds manually
                microseconds = dt.microsecond
                formatted = formatted.replace('Z', f'.{microseconds:06d}Z')
        
        # Handle timezone formatting for all RFC3339 formats
        if format_type in {TimestampFormat.RFC3339, TimestampFormat.RFC3339_TZ, TimestampFormat.RFC3339_MICRO}:
            # Convert +0000 to Z for UTC
            if dt.tzinfo == timezone.utc:
                formatted = formatted.replace('+0000', 'Z')
            else:
                # Ensure proper timezone format
                tz_offset = dt.strftime('%z')
                if len(tz_offset) == 5:  # +0000 format
                    formatted = formatted.replace(tz_offset, f"{tz_offset[:3]}:{tz_offset[3:]}")
        
        return formatted
    
    @staticmethod
    def _format_unix_timestamp(
        dt: datetime, 
        format_type: TimestampFormat, 
        precision: TimestampPrecision
    ) -> str:
        """Format datetime as Unix timestamp."""
        timestamp = dt.timestamp()
        
        if format_type == TimestampFormat.UNIX_SECONDS:
            return str(int(timestamp))
        elif format_type == TimestampFormat.UNIX_MILLIS:
            return str(int(timestamp * 1000))
        elif format_type == TimestampFormat.UNIX_MICROS:
            return str(int(timestamp * 1000000))
        elif format_type == TimestampFormat.UNIX_NANOS:
            return str(int(timestamp * 1000000000))
        else:
            raise ValueError(f"Unsupported Unix format: {format_type}")
    
    @staticmethod
    def _format_nanosecond_timestamp(dt: datetime) -> str:
        """Format datetime with nanosecond precision."""
        # Python's datetime only supports microsecond precision
        # For nanosecond precision, we need to use time.time_ns()
        timestamp_ns = int(dt.timestamp() * 1000000000)
        nanoseconds = timestamp_ns % 1000000000
        
        # Format with nanosecond precision
        base_format = dt.strftime("%Y-%m-%dT%H:%M:%S")
        return f"{base_format}.{nanoseconds:09d}Z"
    
    @staticmethod
    def get_current_timestamp(
        format_type: TimestampFormat = TimestampFormat.RFC3339,
        precision: TimestampPrecision = TimestampPrecision.SECONDS,
        timezone_name: Optional[str] = None
    ) -> str:
        """Get current timestamp in specified format.
        
        Args:
            format_type: Type of timestamp format to use
            precision: Precision level for fractional seconds
            timezone_name: Timezone name (e.g., 'UTC', 'America/New_York')
            
        Returns:
            Current timestamp formatted string
        """
        now = datetime.now(timezone.utc)
        return TimestampFormatter.format_timestamp(now, format_type, precision, timezone_name)
    
    @staticmethod
    def parse_timestamp(
        timestamp_str: str, 
        format_type: TimestampFormat = TimestampFormat.RFC3339
    ) -> datetime:
        """Parse a timestamp string back to datetime object.
        
        Args:
            timestamp_str: Timestamp string to parse
            format_type: Expected format of the timestamp string
            
        Returns:
            Parsed datetime object
            
        Raises:
            ValueError: If timestamp string cannot be parsed
        """
        # Handle Unix timestamp formats
        if format_type in {TimestampFormat.UNIX_SECONDS, TimestampFormat.UNIX_MILLIS, 
                          TimestampFormat.UNIX_MICROS, TimestampFormat.UNIX_NANOS}:
            return TimestampFormatter._parse_unix_timestamp(timestamp_str, format_type)
        
        # Handle RFC3339 formats
        if format_type in {TimestampFormat.RFC3339, TimestampFormat.RFC3339_TZ, 
                          TimestampFormat.RFC3339_MICRO, TimestampFormat.RFC3339_NANO}:
            return TimestampFormatter._parse_rfc3339_timestamp(timestamp_str)
        
        # Handle other formats with strptime
        template = TimestampFormatter.FORMAT_TEMPLATES.get(format_type)
        if not template:
            raise ValueError(f"Unsupported timestamp format: {format_type}")
        
        try:
            return datetime.strptime(timestamp_str, template)
        except ValueError as e:
            raise ValueError(f"Failed to parse timestamp '{timestamp_str}' with format '{format_type}': {e}")
    
    @staticmethod
    def _parse_unix_timestamp(timestamp_str: str, format_type: TimestampFormat) -> datetime:
        """Parse Unix timestamp string."""
        try:
            timestamp = float(timestamp_str)
        except ValueError:
            raise ValueError(f"Invalid Unix timestamp: {timestamp_str}")
        
        if format_type == TimestampFormat.UNIX_SECONDS:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif format_type == TimestampFormat.UNIX_MILLIS:
            return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        elif format_type == TimestampFormat.UNIX_MICROS:
            return datetime.fromtimestamp(timestamp / 1000000, tz=timezone.utc)
        elif format_type == TimestampFormat.UNIX_NANOS:
            return datetime.fromtimestamp(timestamp / 1000000000, tz=timezone.utc)
        else:
            raise ValueError(f"Unsupported Unix format: {format_type}")
    
    @staticmethod
    def _parse_rfc3339_timestamp(timestamp_str: str) -> datetime:
        """Parse RFC3339 timestamp string."""
        # Handle Z suffix
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        # Handle timezone offset
        if '+' in timestamp_str or timestamp_str.count('-') > 2:
            # Has timezone info
            try:
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                # Try parsing with different formats
                for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z']:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Failed to parse RFC3339 timestamp: {timestamp_str}")
        else:
            # No timezone info, assume UTC
            try:
                dt = datetime.fromisoformat(timestamp_str)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError(f"Failed to parse RFC3339 timestamp: {timestamp_str}")


class TimeUtility:
    """General time utility functions."""

    @staticmethod
    def now() -> datetime:
        """Get current UTC datetime."""
        return datetime.now(timezone.utc)

    @staticmethod
    def now_local() -> datetime:
        """Get current local datetime."""
        return datetime.now()

    @staticmethod
    def timestamp() -> float:
        """Get current Unix timestamp."""
        return time.time()

    @staticmethod
    def from_timestamp(timestamp: float) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(timestamp, timezone.utc)

    @staticmethod
    def to_timestamp(dt: datetime) -> float:
        """Convert datetime to Unix timestamp."""
        return dt.timestamp()

    @staticmethod
    def parse_datetime(
        date_string: str, format_string: Optional[str] = None
    ) -> datetime:
        """Parse datetime string with automatic format detection."""
        if format_string:
            return datetime.strptime(date_string, format_string)

        # Common formats to try
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%H:%M:%S",
            "%H:%M",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

        # Try ISO format parsing
        try:
            return datetime.fromisoformat(date_string)
        except ValueError:
            pass

        raise ValueError(f"Unable to parse date string: {date_string}")

    @staticmethod
    def is_weekend(dt: datetime) -> bool:
        """Check if datetime is on a weekend."""
        return dt.weekday() >= 5

    @staticmethod
    def is_business_day(dt: datetime) -> bool:
        """Check if datetime is on a business day."""
        return not TimeUtility.is_weekend(dt)

    @staticmethod
    def next_business_day(dt: datetime) -> datetime:
        """Get the next business day."""
        current = dt + timedelta(days=1)
        while TimeUtility.is_weekend(current):
            current += timedelta(days=1)
        return current

    @staticmethod
    def previous_business_day(dt: datetime) -> datetime:
        """Get the previous business day."""
        current = dt - timedelta(days=1)
        while TimeUtility.is_weekend(current):
            current -= timedelta(days=1)
        return current

    @staticmethod
    def business_days_between(start: datetime, end: datetime) -> int:
        """Count business days between two dates."""
        if start > end:
            start, end = end, start

        business_days = 0
        current = start

        while current <= end:
            if TimeUtility.is_business_day(current):
                business_days += 1
            current += timedelta(days=1)

        return business_days

    @staticmethod
    def add_business_days(dt: datetime, days: int) -> datetime:
        """Add business days to a datetime."""
        current = dt
        remaining_days = abs(days)
        direction = 1 if days > 0 else -1

        while remaining_days > 0:
            current += timedelta(days=direction)
            if TimeUtility.is_business_day(current):
                remaining_days -= 1

        return current

    @staticmethod
    def start_of_day(dt: datetime) -> datetime:
        """Get start of day (00:00:00)."""
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def end_of_day(dt: datetime) -> datetime:
        """Get end of day (23:59:59.999999)."""
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    @staticmethod
    def start_of_week(dt: datetime) -> datetime:
        """Get start of week (Monday)."""
        days_since_monday = dt.weekday()
        return TimeUtility.start_of_day(dt - timedelta(days=days_since_monday))

    @staticmethod
    def end_of_week(dt: datetime) -> datetime:
        """Get end of week (Sunday)."""
        days_until_sunday = 6 - dt.weekday()
        return TimeUtility.end_of_day(dt + timedelta(days=days_until_sunday))

    @staticmethod
    def start_of_month(dt: datetime) -> datetime:
        """Get start of month."""
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def end_of_month(dt: datetime) -> datetime:
        """Get end of month."""
        if dt.month == 12:
            next_month = dt.replace(year=dt.year + 1, month=1, day=1)
        else:
            next_month = dt.replace(month=dt.month + 1, day=1)

        return TimeUtility.end_of_day(next_month - timedelta(days=1))

    @staticmethod
    def start_of_year(dt: datetime) -> datetime:
        """Get start of year."""
        return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def end_of_year(dt: datetime) -> datetime:
        """Get end of year."""
        return dt.replace(
            month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
        )

    @staticmethod
    def format_duration(seconds: float, include_seconds: bool = True) -> str:
        """Format duration in human-readable format."""
        if seconds < 0:
            return "0 seconds"

        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if include_seconds and secs > 0:
            parts.append(f"{secs} second{'s' if secs != 1 else ''}")

        if not parts:
            return "0 seconds"

        return ", ".join(parts)

    @staticmethod
    def human_readable_time(dt: datetime, now: Optional[datetime] = None) -> str:
        """Get human-readable relative time."""
        if now is None:
            now = TimeUtility.now()

        diff = now - dt
        seconds = abs(diff.total_seconds())

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 2592000:  # 30 days
            days = int(seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 31536000:  # 365 days
            months = int(seconds // 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(seconds // 31536000)
            return f"{years} year{'s' if years != 1 else ''} ago"


class DateFormatter:
    """Date formatting utilities."""

    @staticmethod
    def format_date(
        dt: datetime, format_type: DateFormat, custom_format: Optional[str] = None
    ) -> str:
        """Format date according to specified format."""
        if format_type == DateFormat.ISO:
            return dt.isoformat()
        elif format_type == DateFormat.ISO_SHORT:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == DateFormat.US:
            return dt.strftime("%m/%d/%Y %I:%M %p")
        elif format_type == DateFormat.EU:
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        elif format_type == DateFormat.CUSTOM and custom_format:
            return dt.strftime(custom_format)
        else:
            return dt.isoformat()

    @staticmethod
    def format_relative(dt: datetime, now: Optional[datetime] = None) -> str:
        """Format date in relative terms."""
        return TimeUtility.human_readable_time(dt, now)

    @staticmethod
    def format_interval(start: datetime, end: datetime) -> str:
        """Format a time interval."""
        if start.date() == end.date():
            # Same day
            start_time = start.strftime('%I:%M %p')
            end_time = end.strftime('%I:%M %p')
            date_str = start.strftime('%B %d, %Y')
            return f"{date_str} from {start_time} to {end_time}"
        else:
            # Different days
            start_str = start.strftime('%B %d, %Y %I:%M %p')
            end_str = end.strftime('%B %d, %Y %I:%M %p')
            return f"from {start_str} to {end_str}"

    @staticmethod
    def get_month_name(month: int) -> str:
        """Get month name from month number."""
        return calendar.month_name[month]

    @staticmethod
    def get_weekday_name(weekday: int) -> str:
        """Get weekday name from weekday number (0=Monday)."""
        weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        return weekdays[weekday]

    @staticmethod
    def get_quarter(dt: datetime) -> int:
        """Get quarter of the year (1-4)."""
        return (dt.month - 1) // 3 + 1


class TimeZoneUtility:
    """Time zone management utilities."""

    def __init__(self):
        """Initialize timezone manager."""
        self._common_timezones = {
            "UTC": "UTC",
            "EST": "America/New_York",
            "CST": "America/Chicago",
            "MST": "America/Denver",
            "PST": "America/Los_Angeles",
            "GMT": "Europe/London",
            "CET": "Europe/Paris",
            "JST": "Asia/Tokyo",
            "IST": "Asia/Kolkata",
            "AEST": "Australia/Sydney",
        }

    def get_timezone(self, timezone_name: str) -> timezone:
        """Get timezone object by name."""
        try:
            if timezone_name.upper() in self._common_timezones:
                timezone_name = self._common_timezones[timezone_name.upper()]

            return pytz.timezone(timezone_name)
        except Exception:
            # Fallback to UTC
            return timezone.utc

    def convert_timezone(self, dt: datetime, target_timezone: str) -> datetime:
        """Convert datetime to target timezone."""
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = dt.replace(tzinfo=timezone.utc)

        target_tz = self.get_timezone(target_timezone)
        return dt.astimezone(target_tz)

    def get_current_timezone_offset(self, timezone_name: str) -> timedelta:
        """Get current timezone offset from UTC."""
        tz = self.get_timezone(timezone_name)
        now = datetime.now(tz)
        return now.utcoffset() or timedelta(0)

    def is_dst(self, timezone_name: str) -> bool:
        """Check if timezone is currently in daylight saving time."""
        tz = self.get_timezone(timezone_name)
        now = datetime.now(tz)
        return bool(now.dst())

    def get_timezone_info(self, timezone_name: str) -> Dict[str, Any]:
        """Get comprehensive timezone information."""
        tz = self.get_timezone(timezone_name)
        now = datetime.now(tz)

        return {
            "name": timezone_name,
            "offset": str(now.utcoffset() or timedelta(0)),
            "is_dst": bool(now.dst()),
            "dst_offset": str(now.dst() or timedelta(0)),
            "abbreviation": now.strftime("%Z"),
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        }

    def list_common_timezones(self) -> List[str]:
        """List common timezone names."""
        return list(self._common_timezones.keys())

    def search_timezones(self, query: str) -> List[str]:
        """Search timezones by query string."""
        query_lower = query.lower()
        results = []

        for abbrev, full_name in self._common_timezones.items():
            if query_lower in abbrev.lower() or query_lower in full_name.lower():
                results.append(abbrev)

        return results
