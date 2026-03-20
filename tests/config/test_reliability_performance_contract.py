"""
Role: Contract tests for default reliability and performance posture.
Used By:
 - CI to guard accidental default flips.
Depends On:
 - hydra_logger.config.defaults
 - hydra_logger.config.models
Notes:
 - Library defaults favor compatibility; enterprise presets tighten policy explicitly.
"""

from __future__ import annotations

from hydra_logger.config.defaults import get_named_config
from hydra_logger.config.models import LoggingConfig
from hydra_logger.loggers.sync_logger import SyncLogger


def test_logging_config_default_reliability_is_permissive() -> None:
    cfg = LoggingConfig()
    assert cfg.strict_reliability_mode is False
    assert cfg.reliability_error_policy == "silent"


def test_enterprise_named_config_tightens_reliability() -> None:
    enterprise = get_named_config("enterprise")
    assert enterprise.strict_reliability_mode is True
    assert enterprise.reliability_error_policy == "warn"


def test_sync_logger_default_performance_profile_is_convenient() -> None:
    logger = SyncLogger()
    try:
        assert logger.get_performance_profile() == "convenient"
    finally:
        logger.close()
