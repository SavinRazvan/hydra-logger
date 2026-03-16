"""
Role: Pytest coverage for test levels behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates test levels behavior, edge cases, and regression safety.
"""

from hydra_logger.types.levels import (
    LogLevel,
    LogLevelManager,
    all_level_names,
    all_levels,
    get_level,
    get_level_name,
    is_valid_level,
)


def test_get_level_name_handles_known_and_unknown_values() -> None:
    assert get_level_name(LogLevel.INFO) == "INFO"
    assert get_level_name(30) == "WARNING"
    assert get_level_name(12345) == "UNKNOWN"


def test_get_level_supports_aliases_and_default_fallback() -> None:
    assert get_level("warn") == int(LogLevel.WARNING)
    assert get_level("fatal") == int(LogLevel.CRITICAL)
    assert get_level("not-a-real-level") == int(LogLevel.INFO)
    assert get_level(object()) == int(LogLevel.INFO)


def test_is_valid_level_accepts_only_known_values() -> None:
    assert is_valid_level("INFO")
    assert is_valid_level("warn")
    assert is_valid_level(LogLevel.ERROR)
    assert not is_valid_level("INVALID")
    assert not is_valid_level(25)


def test_level_manager_enablement_and_normalization() -> None:
    assert LogLevelManager.is_enabled("INFO", "ERROR")
    assert not LogLevelManager.is_enabled("ERROR", "INFO")
    assert LogLevelManager.normalize_level(40) == LogLevel.ERROR
    assert LogLevelManager.normalize_level("invalid") == LogLevel.INFO


def test_level_color_and_catalog_helpers() -> None:
    assert LogLevelManager.get_color("WARNING") == "yellow"
    assert LogLevelManager.get_color("NOTSET") is None
    assert int(LogLevel.DEBUG) in all_levels()
    assert "WARN" in all_level_names()


def test_level_name_and_normalization_edge_values() -> None:
    assert LogLevelManager.get_name("custom") == "CUSTOM"
    assert LogLevelManager.get_name(LogLevel.CRITICAL) == "CRITICAL"
    assert LogLevelManager.normalize_level(999) == LogLevel.INFO
