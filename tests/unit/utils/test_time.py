"""
Tests for hydra_logger.utils.time module.

This module tests the standardized timestamp system including:
- TimeUnit enum
- TimeUtility class
- TimestampFormatter class
- TimestampConfig class
- TimeRange and TimeInterval classes
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from typing import Tuple
from hydra_logger.utils.time import (
    TimeUnit, TimeUtility, TimestampFormatter, TimestampConfig,
    TimeRange, TimeInterval, TimestampFormat, TimestampPrecision
)
from hydra_logger.types.records import LogRecord


class TestTimeUnit:
    """Test TimeUnit enum functionality."""
    
    def test_time_unit_values(self):
        """Test TimeUnit enum values."""
        assert TimeUnit.NANOSECONDS.value == "ns"
        assert TimeUnit.MICROSECONDS.value == "μs"
        assert TimeUnit.MILLISECONDS.value == "ms"
        assert TimeUnit.SECONDS.value == "seconds"
        assert TimeUnit.MINUTES.value == "minutes"
        assert TimeUnit.HOURS.value == "hours"
        assert TimeUnit.DAYS.value == "days"
        assert TimeUnit.WEEKS.value == "weeks"
        assert TimeUnit.MONTHS.value == "months"
        assert TimeUnit.YEARS.value == "years"
    
    def test_time_unit_properties(self):
        """Test TimeUnit properties."""
        # Test precision units
        assert TimeUnit.NANOSECONDS.is_precision_unit
        assert TimeUnit.MICROSECONDS.is_precision_unit
        assert TimeUnit.MILLISECONDS.is_precision_unit
        assert not TimeUnit.SECONDS.is_precision_unit
        assert not TimeUnit.MINUTES.is_precision_unit
        
        # Test rotation units
        assert TimeUnit.SECONDS.is_rotation_unit
        assert TimeUnit.MINUTES.is_rotation_unit
        assert TimeUnit.HOURS.is_rotation_unit
        assert TimeUnit.DAYS.is_rotation_unit
        assert TimeUnit.WEEKS.is_rotation_unit
        assert TimeUnit.MONTHS.is_rotation_unit
        assert TimeUnit.YEARS.is_rotation_unit
        assert not TimeUnit.NANOSECONDS.is_rotation_unit
    
    def test_time_unit_to_seconds(self):
        """Test TimeUnit to_seconds conversion."""
        assert TimeUnit.SECONDS.to_seconds() == 1
        assert TimeUnit.MINUTES.to_seconds() == 60
        assert TimeUnit.HOURS.to_seconds() == 3600
        assert TimeUnit.DAYS.to_seconds() == 86400
        assert TimeUnit.WEEKS.to_seconds() == 604800
        assert TimeUnit.MONTHS.to_seconds() == 2592000  # ~30 days
        assert TimeUnit.YEARS.to_seconds() == 31536000  # ~365 days
    
    def test_time_unit_short_names(self):
        """Test TimeUnit short names."""
        assert TimeUnit.NANOSECONDS.get_short_name() == "ns"
        assert TimeUnit.MICROSECONDS.get_short_name() == "μs"
        assert TimeUnit.MILLISECONDS.get_short_name() == "ms"
        assert TimeUnit.SECONDS.get_short_name() == "s"
        assert TimeUnit.MINUTES.get_short_name() == "m"
        assert TimeUnit.HOURS.get_short_name() == "h"
        assert TimeUnit.DAYS.get_short_name() == "d"
        assert TimeUnit.WEEKS.get_short_name() == "w"
        assert TimeUnit.MONTHS.get_short_name() == "M"
        assert TimeUnit.YEARS.get_short_name() == "y"


class TestTimeUtility:
    """Test TimeUtility class functionality."""
    
    def test_convert_time(self):
        """Test time conversion between units."""
        # Convert seconds to other units
        assert TimeUtility.convert_time(60, TimeUnit.SECONDS, TimeUnit.MINUTES) == 1
        assert TimeUtility.convert_time(3600, TimeUnit.SECONDS, TimeUnit.HOURS) == 1
        assert TimeUtility.convert_time(86400, TimeUnit.SECONDS, TimeUnit.DAYS) == 1
        
        # Convert minutes to other units
        assert TimeUtility.convert_time(60, TimeUnit.MINUTES, TimeUnit.HOURS) == 1
        assert TimeUtility.convert_time(1440, TimeUnit.MINUTES, TimeUnit.DAYS) == 1
    
    def test_validate_rotation_interval(self):
        """Test rotation interval validation."""
        # Valid intervals
        assert TimeUtility.validate_rotation_interval(1, TimeUnit.HOURS) is True
        assert TimeUtility.validate_rotation_interval(24, TimeUnit.HOURS) is True
        assert TimeUtility.validate_rotation_interval(7, TimeUnit.DAYS) is True
        
        # Invalid intervals
        assert TimeUtility.validate_rotation_interval(0, TimeUnit.HOURS) is False
        assert TimeUtility.validate_rotation_interval(-1, TimeUnit.HOURS) is False
    
    def test_get_optimal_rotation_unit(self):
        """Test optimal rotation unit selection."""
        assert TimeUtility.get_optimal_rotation_unit(30) == TimeUnit.SECONDS
        assert TimeUtility.get_optimal_rotation_unit(300) == TimeUnit.MINUTES
        assert TimeUtility.get_optimal_rotation_unit(3600) == TimeUnit.HOURS
        assert TimeUtility.get_optimal_rotation_unit(86400) == TimeUnit.DAYS
        assert TimeUtility.get_optimal_rotation_unit(604800) == TimeUnit.WEEKS
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert TimeUtility.format_duration(30) == "30.00s"
        assert TimeUtility.format_duration(90) == "1m 30.00s"
        assert TimeUtility.format_duration(3661) == "1h 1m 1.00s"
        assert TimeUtility.format_duration(90061) == "25h 1m 1.00s"  # 25 hours, not 1 day
    
    def test_parse_time_interval(self):
        """Test time interval parsing."""
        assert TimeUtility.parse_time_interval("1h") == (1, TimeUnit.HOURS)
        assert TimeUtility.parse_time_interval("30m") == (30, TimeUnit.MINUTES)
        assert TimeUtility.parse_time_interval("7d") == (7, TimeUnit.DAYS)
        assert TimeUtility.parse_time_interval("2w") == (2, TimeUnit.WEEKS)
        
        # Invalid formats
        with pytest.raises(ValueError):
            TimeUtility.parse_time_interval("invalid")
        
        with pytest.raises(ValueError):
            TimeUtility.parse_time_interval("1x")


class TestTimestampFormatter:
    """Test TimestampFormatter class functionality."""
    
    def test_format_timestamp_rfc3339_standard(self):
        """Test RFC3339 standard formatting."""
        dt = datetime(2025, 9, 10, 16, 30, 45, tzinfo=timezone.utc)
        formatted = TimestampFormatter.format_timestamp(dt, TimestampFormat.RFC3339)
        assert formatted == "2025-09-10T16:30:45Z"
    
    def test_format_timestamp_rfc3339_micro(self):
        """Test RFC3339 with microseconds formatting."""
        dt = datetime(2025, 9, 10, 16, 30, 45, 123456, tzinfo=timezone.utc)
        formatted = TimestampFormatter.format_timestamp(dt, TimestampFormat.RFC3339_MICRO, TimestampPrecision.MICROSECONDS)
        assert formatted == "2025-09-10T16:30:45.123456Z"
    
    def test_format_timestamp_unix_seconds(self):
        """Test Unix timestamp formatting."""
        dt = datetime(2025, 9, 10, 16, 30, 45, tzinfo=timezone.utc)
        formatted = TimestampFormatter.format_timestamp(dt, TimestampFormat.UNIX_SECONDS)
        assert formatted == str(int(dt.timestamp()))
    
    def test_format_timestamp_unix_millis(self):
        """Test Unix milliseconds formatting."""
        dt = datetime(2025, 9, 10, 16, 30, 45, 123456, tzinfo=timezone.utc)
        formatted = TimestampFormatter.format_timestamp(dt, TimestampFormat.UNIX_MILLIS)
        assert formatted == str(int(dt.timestamp() * 1000))
    
    def test_format_timestamp_human_readable(self):
        """Test human readable formatting."""
        dt = datetime(2025, 9, 10, 16, 30, 45, tzinfo=timezone.utc)
        formatted = TimestampFormatter.format_timestamp(dt, TimestampFormat.HUMAN_READABLE)
        assert formatted == "2025-09-10 16:30:45"
    
    def test_format_timestamp_compact(self):
        """Test compact formatting."""
        dt = datetime(2025, 9, 10, 16, 30, 45, tzinfo=timezone.utc)
        formatted = TimestampFormatter.format_timestamp(dt, TimestampFormat.COMPACT)
        assert formatted == "20250910T163045Z"
    
    def test_format_timestamp_legacy(self):
        """Test legacy formatting."""
        dt = datetime(2025, 9, 10, 16, 30, 45, 123456, tzinfo=timezone.utc)
        formatted = TimestampFormatter.format_timestamp(dt, TimestampFormat.LEGACY)
        assert formatted == "2025-09-10 16:30:45,123456"
    
    def test_format_timestamp_syslog(self):
        """Test syslog formatting."""
        dt = datetime(2025, 9, 10, 16, 30, 45, tzinfo=timezone.utc)
        formatted = TimestampFormatter.format_timestamp(dt, TimestampFormat.SYSLOG)
        assert formatted == "Sep 10 16:30:45"
    
    def test_parse_timestamp_rfc3339(self):
        """Test RFC3339 timestamp parsing."""
        timestamp_str = "2025-09-10T16:30:45Z"
        dt = TimestampFormatter.parse_timestamp(timestamp_str)
        assert dt.year == 2025
        assert dt.month == 9
        assert dt.day == 10
        assert dt.hour == 16
        assert dt.minute == 30
        assert dt.second == 45
        assert dt.tzinfo == timezone.utc
    
    def test_parse_timestamp_unix(self):
        """Test Unix timestamp parsing."""
        timestamp = 1757521845  # 2025-09-10 16:30:45 UTC
        dt = TimestampFormatter.parse_timestamp(str(timestamp), TimestampFormat.UNIX_SECONDS)
        assert dt.year == 2025
        assert dt.month == 9
        assert dt.day == 10
    
    def test_get_current_timestamp(self):
        """Test current timestamp generation."""
        timestamp = TimestampFormatter.get_current_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        
        # Should be in RFC3339 format by default
        assert "T" in timestamp
        assert timestamp.endswith("Z")


class TestTimestampConfig:
    """Test TimestampConfig class functionality."""
    
    def test_timestamp_config_creation(self):
        """Test TimestampConfig creation."""
        config = TimestampConfig(
            format_type=TimestampFormat.RFC3339,
            precision=TimestampPrecision.SECONDS,
            timezone_name="UTC"
        )
        assert config.format_type == TimestampFormat.RFC3339
        assert config.precision == TimestampPrecision.SECONDS
        assert config.timezone_name == "UTC"
        assert config.include_timezone is True
    
    def test_timestamp_config_presets(self):
        """Test TimestampConfig preset methods."""
        # RFC3339 Standard
        config = TimestampConfig.rfc3339_standard()
        assert config.format_type == TimestampFormat.RFC3339
        assert config.precision == TimestampPrecision.SECONDS
        
        # RFC3339 High Precision
        config = TimestampConfig.rfc3339_high_precision()
        assert config.format_type == TimestampFormat.RFC3339_MICRO
        assert config.precision == TimestampPrecision.MICROSECONDS
        
        # Unix Timestamp
        config = TimestampConfig.unix_timestamp()
        assert config.format_type == TimestampFormat.UNIX_SECONDS
        assert config.precision == TimestampPrecision.SECONDS
        
        # Unix Milliseconds
        config = TimestampConfig.unix_millis()
        assert config.format_type == TimestampFormat.UNIX_MILLIS
        assert config.precision == TimestampPrecision.MILLISECONDS
        
        # Human Readable
        config = TimestampConfig.human_readable()
        assert config.format_type == TimestampFormat.HUMAN_READABLE
        assert config.precision == TimestampPrecision.SECONDS
        
        # Compact
        config = TimestampConfig.compact()
        assert config.format_type == TimestampFormat.COMPACT
        assert config.precision == TimestampPrecision.SECONDS
        
        # Legacy
        config = TimestampConfig.legacy()
        assert config.format_type == TimestampFormat.LEGACY
        assert config.precision == TimestampPrecision.MILLISECONDS
    
    def test_timestamp_config_format_timestamp(self):
        """Test TimestampConfig format_timestamp method."""
        config = TimestampConfig.rfc3339_standard()
        dt = datetime(2025, 9, 10, 16, 30, 45, tzinfo=timezone.utc)
        formatted = config.format_timestamp(dt)
        assert formatted == "2025-09-10T16:30:45Z"
    
    def test_timestamp_config_get_current_timestamp(self):
        """Test TimestampConfig get_current_timestamp method."""
        config = TimestampConfig.rfc3339_standard()
        timestamp = config.get_current_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        assert "T" in timestamp
        assert timestamp.endswith("Z")
    
    def test_timestamp_config_serialization(self):
        """Test TimestampConfig serialization."""
        config = TimestampConfig.rfc3339_standard()
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict['format_type'] == 'rfc3339'
        assert config_dict['precision'] == 'seconds'
        assert config_dict['timezone_name'] == 'UTC'
        assert config_dict['include_timezone'] is True
        
        # Test from_dict
        new_config = TimestampConfig.from_dict(config_dict)
        assert new_config.format_type == config.format_type
        assert new_config.precision == config.precision
        assert new_config.timezone_name == config.timezone_name
        assert new_config.include_timezone == config.include_timezone


class TestTimeRange:
    """Test TimeRange class functionality."""
    
    def test_time_range_creation(self):
        """Test TimeRange creation."""
        start = datetime(2025, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 9, 10, 18, 0, 0, tzinfo=timezone.utc)
        time_range = TimeRange(start, end)
        
        assert time_range.start == start
        assert time_range.end == end
        assert time_range.duration == timedelta(hours=8)
    
    def test_time_range_split_by_unit(self):
        """Test TimeRange split_by_unit method."""
        start = datetime(2025, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
        time_range = TimeRange(start, end)
        
        # Split by hours
        intervals = time_range.split_by_unit(TimeUnit.HOURS)
        assert len(intervals) == 2
        assert intervals[0].start == start
        assert intervals[0].end == datetime(2025, 9, 10, 11, 0, 0, tzinfo=timezone.utc)
        assert intervals[1].start == datetime(2025, 9, 10, 11, 0, 0, tzinfo=timezone.utc)
        assert intervals[1].end == end


class TestTimeInterval:
    """Test TimeInterval class functionality."""
    
    def test_time_interval_creation(self):
        """Test TimeInterval creation."""
        interval = TimeInterval(2, TimeUnit.HOURS)
        assert interval.value == 2
        assert interval.unit == TimeUnit.HOURS
    
    def test_time_interval_to_timedelta(self):
        """Test TimeInterval to_timedelta method."""
        interval = TimeInterval(2, TimeUnit.HOURS)
        td = interval.to_timedelta()
        assert td == timedelta(hours=2)
        
        interval = TimeInterval(30, TimeUnit.MINUTES)
        td = interval.to_timedelta()
        assert td == timedelta(minutes=30)
    
    def test_time_interval_to_timedelta_conversion(self):
        """Test TimeInterval to_timedelta method."""
        interval = TimeInterval(2, TimeUnit.HOURS)
        td = interval.to_timedelta()
        assert td.total_seconds() == 7200
        
        interval = TimeInterval(30, TimeUnit.MINUTES)
        td = interval.to_timedelta()
        assert td.total_seconds() == 1800


class TestTimestampIntegration:
    """Integration tests for timestamp system."""
    
    def test_timestamp_config_with_handlers(self):
        """Test timestamp config integration with handlers."""
        from hydra_logger.handlers.console import ConsoleHandler
        from hydra_logger.handlers.file import FileHandler
        
        # Test console handler with timestamp config
        console_handler = ConsoleHandler(timestamp_config=TimestampConfig.human_readable())
        assert console_handler.timestamp_config.format_type == TimestampFormat.HUMAN_READABLE
        
        # Test file handler with timestamp config
        file_handler = FileHandler("test.log", timestamp_config=TimestampConfig.rfc3339_standard())
        assert file_handler.timestamp_config.format_type == TimestampFormat.RFC3339
    
    def test_timestamp_config_with_formatters(self):
        """Test timestamp config integration with formatters."""
        from hydra_logger.formatters.text import PlainTextFormatter
        from hydra_logger.formatters.json import JsonLinesFormatter
        
        # Test text formatter with timestamp config
        text_formatter = PlainTextFormatter(timestamp_config=TimestampConfig.human_readable())
        assert text_formatter.timestamp_config.format_type == TimestampFormat.HUMAN_READABLE
        
        # Test JSON formatter with timestamp config
        json_formatter = JsonLinesFormatter(timestamp_config=TimestampConfig.rfc3339_standard())
        assert json_formatter.timestamp_config.format_type == TimestampFormat.RFC3339
    
    def test_timestamp_formatting_workflow(self):
        """Test complete timestamp formatting workflow."""
        # Create a log record
        record = LogRecord(
            message="Test message",
            level=20,
            level_name="INFO",
            logger_name="test_logger",
            layer="test",
            timestamp=datetime.now(timezone.utc).timestamp()
        )
        
        # Test different timestamp configs
        configs = [
            TimestampConfig.human_readable(),
            TimestampConfig.rfc3339_standard(),
            TimestampConfig.rfc3339_high_precision(),
            TimestampConfig.unix_timestamp(),
            TimestampConfig.compact()
        ]
        
        for config in configs:
            # Format timestamp using config
            dt = datetime.fromtimestamp(record.timestamp, tz=timezone.utc)
            formatted = config.format_timestamp(dt)
            
            # Verify formatting worked
            assert isinstance(formatted, str)
            assert len(formatted) > 0
            
            # Verify format matches expected type
            if config.format_type == TimestampFormat.HUMAN_READABLE:
                assert " " in formatted  # Should have space between date and time
            elif config.format_type == TimestampFormat.RFC3339:
                assert "T" in formatted  # Should have T separator
                assert formatted.endswith("Z")  # Should end with Z for UTC
            elif config.format_type == TimestampFormat.UNIX_SECONDS:
                assert formatted.isdigit()  # Should be numeric
            elif config.format_type == TimestampFormat.COMPACT:
                assert "T" in formatted  # Should have T separator
                assert len(formatted) >= 15  # Should be compact format


class TestTimestampErrorHandling:
    """Test error handling in timestamp system."""
    
    def test_invalid_timestamp_format(self):
        """Test handling of invalid timestamp formats."""
        with pytest.raises(ValueError):
            TimestampFormatter.parse_timestamp("invalid-timestamp")
    
    def test_invalid_time_unit(self):
        """Test handling of invalid time units."""
        with pytest.raises(AttributeError):
            TimeUtility.convert_time(60, TimeUnit.SECONDS, "invalid_unit")
    
    def test_invalid_rotation_interval(self):
        """Test handling of invalid rotation intervals."""
        # The method returns False for invalid intervals, doesn't raise
        assert TimeUtility.validate_rotation_interval(-1, TimeUnit.HOURS) is False
    
    def test_invalid_timestamp_config(self):
        """Test handling of invalid timestamp config."""
        # The dataclass will accept any values, validation happens at usage time
        config = TimestampConfig(
            format_type="invalid_format",  # This will be a string, not enum
            precision=TimestampPrecision.SECONDS
        )
        assert config.format_type == "invalid_format"


class TestTimestampPerformance:
    """Test timestamp system performance."""
    
    def test_timestamp_formatting_performance(self):
        """Test timestamp formatting performance."""
        dt = datetime.now(timezone.utc)
        config = TimestampConfig.rfc3339_standard()
        
        # Time multiple formatting operations
        start_time = time.perf_counter()
        for _ in range(1000):
            config.format_timestamp(dt)
        end_time = time.perf_counter()
        
        # Should be fast (less than 0.1 seconds for 1000 operations)
        duration = end_time - start_time
        assert duration < 0.1
    
    def test_timestamp_parsing_performance(self):
        """Test timestamp parsing performance."""
        timestamp_str = "2025-09-10T16:30:45Z"
        
        # Time multiple parsing operations
        start_time = time.perf_counter()
        for _ in range(1000):
            TimestampFormatter.parse_timestamp(timestamp_str)
        end_time = time.perf_counter()
        
        # Should be fast (less than 0.1 seconds for 1000 operations)
        duration = end_time - start_time
        assert duration < 0.1
