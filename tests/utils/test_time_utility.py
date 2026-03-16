"""
Role: Pytest coverage for time utility behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates conversion, parsing, and timestamp formatting edge behavior.
"""

from datetime import datetime, timedelta, timezone

import pytest

from hydra_logger.types.enums import TimeUnit
from hydra_logger.utils.time_utility import (
    TimeRange,
    TimestampFormat,
    TimestampFormatter,
    TimeUtility,
)


def test_convert_time_and_rotation_interval_validation() -> None:
    assert TimeUtility.convert_time(60, TimeUnit.SECONDS, TimeUnit.MINUTES) == 1
    assert not TimeUtility.validate_rotation_interval(0, TimeUnit.SECONDS)
    assert not TimeUtility.validate_rotation_interval(1, TimeUnit.MILLISECONDS)
    assert TimeUtility.validate_rotation_interval(5, TimeUnit.MINUTES)


def test_parse_time_interval_and_invalid_input() -> None:
    assert TimeUtility.parse_time_interval("15s") == (15, TimeUnit.SECONDS)
    assert TimeUtility.parse_time_interval("2 hours") == (2, TimeUnit.HOURS)
    with pytest.raises(ValueError, match="Invalid time interval format"):
        TimeUtility.parse_time_interval("oops")
    with pytest.raises(ValueError, match="Unknown time unit"):
        TimeUtility.parse_time_interval("10fortnights")


def test_parse_time_interval_logs_invalid_input(caplog) -> None:
    with caplog.at_level("ERROR", logger="hydra_logger.utils.time_utility"):
        with pytest.raises(ValueError):
            TimeUtility.parse_time_interval("oops")
    assert "Invalid time interval format" in caplog.text


def test_time_range_split_intersection_and_union() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(hours=3)
    full_range = TimeRange(start=start, end=end)
    split = full_range.split_by_unit(TimeUnit.HOURS, count=1)
    assert len(split) == 3
    assert split[0].duration_seconds == 3600

    overlap = TimeRange(start + timedelta(hours=2), end + timedelta(hours=1))
    intersection = full_range.intersection(overlap)
    assert intersection is not None
    assert intersection.duration_seconds == 3600
    assert full_range.union(overlap).duration_seconds == 4 * 3600


def test_timestamp_formatter_roundtrip_for_rfc3339_and_unix() -> None:
    dt = datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)
    rfc = TimestampFormatter.format_timestamp(
        dt, TimestampFormat.RFC3339_MICRO, timezone_name="UTC"
    )
    parsed = TimestampFormatter.parse_timestamp(rfc, TimestampFormat.RFC3339_MICRO)
    assert parsed.tzinfo is not None
    assert parsed.year == 2026

    unix = TimestampFormatter.format_timestamp(dt, TimestampFormat.UNIX_MILLIS)
    parsed_unix = TimestampFormatter.parse_timestamp(unix, TimestampFormat.UNIX_MILLIS)
    assert parsed_unix.tzinfo == timezone.utc
