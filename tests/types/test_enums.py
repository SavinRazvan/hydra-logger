"""
Role: Pytest coverage for test enums behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates test enums behavior, edge cases, and regression safety.
"""

from hydra_logger.types.enums import (
    HandlerType,
    TimeUnit,
    get_enum_by_name,
    get_enum_by_value,
    get_enum_names,
    get_enum_values,
    is_valid_enum_name,
    is_valid_enum_value,
)


def test_enum_utility_helpers_for_names_and_values() -> None:
    names = get_enum_names(HandlerType)
    values = get_enum_values(HandlerType)

    assert "CONSOLE" in names
    assert "console" in values
    assert get_enum_by_name(HandlerType, "FILE") == HandlerType.FILE
    assert get_enum_by_value(HandlerType, "network") == HandlerType.NETWORK


def test_enum_utility_helpers_handle_invalid_lookups() -> None:
    assert get_enum_by_name(HandlerType, "DOES_NOT_EXIST") is None
    assert get_enum_by_value(HandlerType, "not-a-value") is None
    assert not is_valid_enum_name(HandlerType, "DOES_NOT_EXIST")
    assert not is_valid_enum_value(HandlerType, "not-a-value")


def test_time_unit_precision_and_rotation_flags() -> None:
    assert TimeUnit.NANOSECONDS.is_precision_unit
    assert TimeUnit.MICROSECONDS.is_precision_unit
    assert TimeUnit.MILLISECONDS.is_precision_unit
    assert not TimeUnit.SECONDS.is_precision_unit

    assert TimeUnit.SECONDS.is_rotation_unit
    assert TimeUnit.DAYS.is_rotation_unit
    assert not TimeUnit.MILLISECONDS.is_rotation_unit


def test_time_unit_conversion_and_short_names() -> None:
    assert TimeUnit.SECONDS.to_seconds() == 1.0
    assert TimeUnit.MINUTES.to_seconds() == 60.0
    assert TimeUnit.HOURS.to_seconds() == 3600.0
    assert TimeUnit.NANOSECONDS.to_seconds() < TimeUnit.MICROSECONDS.to_seconds()

    assert TimeUnit.NANOSECONDS.get_short_name() == "ns"
    assert TimeUnit.MICROSECONDS.get_short_name() == "μs"
    assert TimeUnit.MILLISECONDS.get_short_name() == "ms"
    assert TimeUnit.YEARS.get_short_name() == "y"


def test_enum_name_lookup_is_case_sensitive() -> None:
    assert get_enum_by_name(HandlerType, "FILE") == HandlerType.FILE
    assert get_enum_by_name(HandlerType, "file") is None
