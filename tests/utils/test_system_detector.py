"""
Role: Pytest coverage for system detector behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates safe defaults and adaptive configuration behavior.
"""

from hydra_logger.utils.system_detector import (
    SystemDetector,
    SystemProfile,
    get_optimal_buffer_config,
)


def test_detector_returns_conservative_values_without_psutil() -> None:
    detector = SystemDetector()
    detector._psutil_available = False
    detector._system_profile = SystemProfile.RESOURCE_CONSTRAINED
    assert detector.get_optimal_buffer_size("console", min_size=123) == 123
    assert detector.get_optimal_buffer_size("file", min_size=100) == 1000
    assert detector.get_safe_max_buffer_size() == 10000
    assert detector.should_use_aggressive_buffering() is False


def test_detector_adapts_buffer_interval_and_memory_recommendations() -> None:
    detector = SystemDetector()
    detector._psutil_available = True
    detector._available_memory_mb = 16000
    detector._safe_memory_limit_mb = 1600
    detector._system_profile = SystemProfile.HIGH_PERFORMANCE
    detector._cpu_count = 8

    file_buffer = detector.get_optimal_buffer_size("file", min_size=100, max_size=1_000_000)
    assert file_buffer >= 500000
    interval = detector.get_optimal_flush_interval("file", min_interval=0.1, max_interval=10.0)
    assert interval == 7.5

    status = detector.monitor_memory_usage(current_usage_mb=14000)
    assert status["warning"] is True
    assert status["recommendation"] == "reduce_buffers"


def test_global_optimal_buffer_config_has_required_keys() -> None:
    config = get_optimal_buffer_config("console")
    assert "buffer_size" in config
    assert "flush_interval" in config
    assert "max_buffer_size" in config
