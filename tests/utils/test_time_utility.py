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
    DateFormatter,
    TimeRange,
    TimeInterval,
    TimeUtility,
    TimeZoneUtility,
    TimestampConfig,
    TimestampFormat,
    TimestampFormatter,
    TimestampPrecision,
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

    partial_split = full_range.split_by_unit(TimeUnit.HOURS, count=2)
    assert len(partial_split) == 2
    assert partial_split[-1].duration_seconds == 3600


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


def test_timestamp_config_presets_and_roundtrip_dict() -> None:
    presets = [
        TimestampConfig.rfc3339_standard(),
        TimestampConfig.rfc3339_high_precision(),
        TimestampConfig.unix_timestamp(),
        TimestampConfig.unix_millis(),
        TimestampConfig.human_readable(),
        TimestampConfig.compact(),
        TimestampConfig.legacy(),
    ]

    for config in presets:
        payload = config.to_dict()
        restored = TimestampConfig.from_dict(payload)
        assert restored.format_type == config.format_type
        assert restored.precision == config.precision
        assert restored.include_timezone == config.include_timezone
        assert restored.get_current_timestamp()

    dt = datetime(2026, 1, 1, 1, 2, 3, tzinfo=timezone.utc)
    assert TimestampConfig.rfc3339_standard().format_timestamp(dt).startswith("2026-01-01T")


def test_time_range_contains_overlap_false_and_dict() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)
    rng = TimeRange(start=start, end=end)
    outside = start - timedelta(minutes=1)
    far = TimeRange(end + timedelta(hours=1), end + timedelta(hours=2))

    assert rng.contains(start)
    assert not rng.contains(outside)
    assert not rng.overlaps(far)
    assert rng.intersection(far) is None

    payload = rng.to_dict()
    assert payload["duration_seconds"] == 7200
    assert payload["duration_minutes"] == 120
    assert payload["duration_hours"] == 2
    assert payload["duration_days"] == 7200 / 86400


def test_time_range_requires_start_before_end() -> None:
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="Start time must be before end time"):
        TimeRange(start=now, end=now)


def test_time_interval_to_timedelta_and_string_formats() -> None:
    one_second = TimeInterval(1, TimeUnit.SECONDS)
    five_minutes = TimeInterval(5, TimeUnit.MINUTES)
    assert one_second.to_timedelta() == timedelta(seconds=1)
    assert five_minutes.to_timedelta() == timedelta(minutes=5)
    assert str(one_second) == "1 seconds"
    assert str(five_minutes) == "5 minutess"


def test_time_utility_basic_clock_and_duration_helpers() -> None:
    assert TimeUtility.now().tzinfo is not None
    assert TimeUtility.utc_now().tzinfo is not None
    assert isinstance(TimeUtility.local_now(), datetime)
    assert isinstance(TimeUtility.timestamp(), float)
    assert isinstance(TimeUtility.perf_counter(), float)
    assert isinstance(TimeUtility.monotonic(), float)

    assert TimeUtility.get_optimal_rotation_unit(59) == TimeUnit.SECONDS
    assert TimeUtility.get_optimal_rotation_unit(60) == TimeUnit.MINUTES
    assert TimeUtility.get_optimal_rotation_unit(3600) == TimeUnit.HOURS
    assert TimeUtility.get_optimal_rotation_unit(86400) == TimeUnit.DAYS
    assert TimeUtility.get_optimal_rotation_unit(604800) == TimeUnit.WEEKS
    assert TimeUtility.get_optimal_rotation_unit(2592000) == TimeUnit.MONTHS
    assert TimeUtility.get_optimal_rotation_unit(31536000) == TimeUnit.YEARS

    assert TimeUtility.format_duration(0.25, precision=3) == "0.250s"
    assert TimeUtility.format_duration(3661.5, precision=1) == "1h 1m 1.5s"
    assert TimeUtility.format_duration(3600, precision=0) == "1h"
    assert TimeUtility.convert_time(42, TimeUnit.SECONDS, TimeUnit.SECONDS) == 42
    assert not TimeUtility.validate_rotation_interval(2, TimeUnit.YEARS)


def test_timestamp_formatter_timezone_and_precision_variants() -> None:
    dt = datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)

    rfc_utc = TimestampFormatter.format_timestamp(
        dt, TimestampFormat.RFC3339, TimestampPrecision.SECONDS, timezone_name="UTC"
    )
    assert rfc_utc.endswith("Z")

    rfc_micro = TimestampFormatter.format_timestamp(
        dt,
        TimestampFormat.RFC3339_MICRO,
        TimestampPrecision.MICROSECONDS,
        timezone_name="UTC",
    )
    assert ".123456Z" in rfc_micro

    human_millis = TimestampFormatter.format_timestamp(
        dt,
        TimestampFormat.HUMAN_READABLE_MICRO,
        TimestampPrecision.MILLISECONDS,
        timezone_name="UTC",
    )
    assert ".123" in human_millis

    dt_berlin = TimestampFormatter.format_timestamp(
        dt, TimestampFormat.RFC3339_TZ, TimestampPrecision.SECONDS, timezone_name="Europe/Berlin"
    )
    assert "+" in dt_berlin

    nano = TimestampFormatter.format_timestamp(
        dt, TimestampFormat.RFC3339_NANO, TimestampPrecision.NANOSECONDS, timezone_name="UTC"
    )
    assert nano.endswith("Z")
    assert len(nano.split(".")[1].rstrip("Z")) == 9

    local_naive = datetime(2026, 1, 2, 3, 4, 5)
    formatted_local = TimestampFormatter.format_timestamp(
        local_naive, TimestampFormat.RFC3339, TimestampPrecision.SECONDS
    )
    assert "T03:04:05" in formatted_local

    naive_forced_utc = TimestampFormatter.format_timestamp(
        local_naive, TimestampFormat.RFC3339, TimestampPrecision.SECONDS, timezone_name="UTC"
    )
    assert naive_forced_utc.endswith("Z")


def test_timestamp_formatter_raises_for_invalid_timezone_and_unsupported_format() -> None:
    dt = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="Unknown timezone"):
        TimestampFormatter.format_timestamp(
            dt, TimestampFormat.RFC3339, timezone_name="Mars/Phobos"
        )

    with pytest.raises(ValueError, match="Unsupported timestamp format"):
        TimestampFormatter.format_timestamp(dt, "bad-format")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Unsupported Unix format"):
        TimestampFormatter._format_unix_timestamp(
            dt, "bad-format", TimestampPrecision.SECONDS  # type: ignore[arg-type]
        )


def test_timestamp_formatter_parse_variants_and_failures(caplog) -> None:
    parsed_z = TimestampFormatter.parse_timestamp(
        "2026-01-02T03:04:05Z", TimestampFormat.RFC3339
    )
    assert parsed_z.tzinfo is not None

    parsed_no_tz = TimestampFormatter.parse_timestamp(
        "2026-01-02T03:04:05", TimestampFormat.RFC3339
    )
    assert parsed_no_tz.tzinfo == timezone.utc

    parsed_human = TimestampFormatter.parse_timestamp(
        "2026-01-02 03:04:05", TimestampFormat.HUMAN_READABLE
    )
    assert parsed_human.year == 2026

    with pytest.raises(ValueError, match="Failed to parse RFC3339 timestamp"):
        TimestampFormatter._parse_rfc3339_timestamp("not-rfc")

    with pytest.raises(ValueError, match="Invalid Unix timestamp"):
        TimestampFormatter._parse_unix_timestamp("abc", TimestampFormat.UNIX_SECONDS)

    with pytest.raises(ValueError, match="Unsupported Unix format"):
        TimestampFormatter._parse_unix_timestamp("10", "bad-format")  # type: ignore[arg-type]

    with caplog.at_level("ERROR", logger="hydra_logger.utils.time_utility"):
        with pytest.raises(ValueError, match="Failed to parse timestamp"):
            TimestampFormatter.parse_timestamp("bad", TimestampFormat.HUMAN_READABLE)
    assert "Timestamp parse failed" in caplog.text

    with pytest.raises(ValueError, match="Unsupported timestamp format"):
        TimestampFormatter.parse_timestamp("2026", "bad-format")  # type: ignore[arg-type]

    parsed_seconds = TimestampFormatter.parse_timestamp("10", TimestampFormat.UNIX_SECONDS)
    parsed_micros = TimestampFormatter.parse_timestamp("1000000", TimestampFormat.UNIX_MICROS)
    parsed_nanos = TimestampFormatter.parse_timestamp("1000000000", TimestampFormat.UNIX_NANOS)
    assert parsed_seconds.tzinfo == timezone.utc
    assert parsed_micros.tzinfo == timezone.utc
    assert parsed_nanos.tzinfo == timezone.utc

    unix_micro = TimestampFormatter.format_timestamp(
        datetime(2026, 1, 2, tzinfo=timezone.utc), TimestampFormat.UNIX_MICROS
    )
    unix_nano = TimestampFormatter.format_timestamp(
        datetime(2026, 1, 2, tzinfo=timezone.utc), TimestampFormat.UNIX_NANOS
    )
    assert unix_micro.isdigit()
    assert unix_nano.isdigit()

    parsed_offset = TimestampFormatter.parse_timestamp(
        "2026-01-02T03:04:05+0000", TimestampFormat.RFC3339
    )
    assert parsed_offset.tzinfo is not None

    with pytest.raises(ValueError, match="Failed to parse RFC3339 timestamp"):
        TimestampFormatter.parse_timestamp("2026-01-02T03:04:05.bad+0000", TimestampFormat.RFC3339)


def test_date_formatter_and_relative_time_and_timezone_utility() -> None:
    now = datetime.now()
    assert DateFormatter.format_date(now, "%Y") == now.strftime("%Y")
    assert DateFormatter.format_relative_time(now - timedelta(days=2)) == "2 days ago"
    assert DateFormatter.format_relative_time(now - timedelta(hours=2)) == "2 hours ago"
    assert DateFormatter.format_relative_time(now - timedelta(minutes=5)) == "5 minutes ago"
    assert DateFormatter.format_relative_time(now) == "just now"

    local_tz = TimeZoneUtility.get_local_timezone()
    assert local_tz is not None

    naive = datetime(2026, 1, 1, 0, 0, 0)
    converted = TimeZoneUtility.convert_to_timezone(naive, timezone.utc)
    assert converted.tzinfo is not None
