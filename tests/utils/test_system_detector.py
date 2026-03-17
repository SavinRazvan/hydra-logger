"""
Role: Pytest coverage for system detector behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates safe defaults and adaptive configuration behavior.
"""

import builtins
import sys
import types

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


def test_detector_detect_system_capability_profiles_and_importerror_fallback(
    monkeypatch,
) -> None:
    detector = SystemDetector()

    def _set_fake_psutil(available_mb: int):
        fake = types.SimpleNamespace(
            virtual_memory=lambda: types.SimpleNamespace(available=available_mb * 1024 * 1024),
            cpu_count=lambda logical=True: 4,
        )
        monkeypatch.setitem(sys.modules, "psutil", fake)
        detector._detect_system_capabilities()

    _set_fake_psutil(1500)
    assert detector._system_profile == SystemProfile.RESOURCE_CONSTRAINED
    _set_fake_psutil(9000)
    assert detector._system_profile == SystemProfile.HIGH_PERFORMANCE
    _set_fake_psutil(20000)
    assert detector._system_profile == SystemProfile.ULTRA_HIGH_PERFORMANCE

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "psutil":
            raise ImportError("forced")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    detector._detect_system_capabilities()
    assert detector._psutil_available is False
    assert detector._available_memory_mb == 512
    assert detector._safe_memory_limit_mb == 50


def test_detector_aggressive_info_and_monitor_paths() -> None:
    detector = SystemDetector()
    detector._psutil_available = True
    detector._system_profile = SystemProfile.HIGH_PERFORMANCE
    detector._available_memory_mb = 4000
    detector._safe_memory_limit_mb = 400
    assert detector.should_use_aggressive_buffering() is True
    info = detector.get_system_info()
    assert info["system_profile"] == "high_performance"

    detector._psutil_available = False
    fallback = detector.monitor_memory_usage(current_usage_mb=1.0)
    assert fallback["recommendation"] == "unknown"

    detector._psutil_available = True
    detector._available_memory_mb = 1000
    monitor = detector.monitor_memory_usage(current_usage_mb=600.0)
    assert monitor["recommendation"] == "monitor"
