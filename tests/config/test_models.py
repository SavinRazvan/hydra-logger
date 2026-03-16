"""
Role: Pytest coverage for configuration model validation behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates model defaults, validators, and path resolution.
"""

from pathlib import Path

import pytest

from hydra_logger.config.models import LogDestination, LogLayer, LoggingConfig
from hydra_logger.config.validation import normalize_level


def test_logging_config_auto_creates_default_layer_when_missing() -> None:
    config = LoggingConfig(layers={})
    assert "default" in config.layers
    assert config.layers["default"].destinations[0].type == "console"


def test_logging_config_validates_core_ranges() -> None:
    with pytest.raises(ValueError, match="Buffer size must be positive"):
        LoggingConfig(buffer_size=0)
    with pytest.raises(ValueError, match="Flush interval cannot be negative"):
        LoggingConfig(flush_interval=-1)
    with pytest.raises(ValueError, match="Monitoring sample rate must be at least 1"):
        LoggingConfig(monitoring_sample_rate=0)


def test_logging_config_resolve_log_path_applies_format_extension(tmp_path: Path) -> None:
    config = LoggingConfig(base_log_dir=str(tmp_path))
    resolved = config.resolve_log_path("service.log", format_type="json-lines")
    assert resolved.endswith(".jsonl")
    assert Path(resolved).parent.exists()


def test_log_destination_requires_path_for_file_destinations() -> None:
    with pytest.raises(ValueError, match="Path is required for file destinations"):
        LogDestination(type="file")


def test_normalize_level_logs_invalid_values(caplog) -> None:
    with caplog.at_level("ERROR", logger="hydra_logger.config.validation"):
        with pytest.raises(ValueError, match="Invalid level"):
            normalize_level("not-a-level")
    assert "Invalid log level received" in caplog.text
