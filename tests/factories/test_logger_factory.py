"""
Role: Pytest coverage for logger factory behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates logger dispatch, template lookup, and extension wiring.
"""

import pytest

from hydra_logger.factories.logger_factory import LoggerFactory, create_logger
from hydra_logger.loggers.async_logger import AsyncLogger
from hydra_logger.loggers.sync_logger import SyncLogger


def test_logger_factory_dispatches_sync_and_async_types() -> None:
    factory = LoggerFactory()
    sync_logger = factory.create_logger(logger_type="sync")
    async_logger = factory.create_logger(logger_type="async")
    assert isinstance(sync_logger, SyncLogger)
    assert isinstance(async_logger, AsyncLogger)


def test_logger_factory_rejects_unknown_logger_type() -> None:
    factory = LoggerFactory()
    with pytest.raises(ValueError, match="Unknown logger type"):
        factory.create_logger(logger_type="invalid")


def test_logger_factory_logs_unknown_template_request(caplog) -> None:
    factory = LoggerFactory()
    with caplog.at_level("ERROR", logger="hydra_logger.factories.logger_factory"):
        with pytest.raises(ValueError, match="Unknown configuration template"):
            factory.create_logger_with_template("missing-template")
    assert "Unknown configuration template requested: missing-template" in caplog.text


def test_logger_factory_applies_extension_config_and_attaches_manager() -> None:
    factory = LoggerFactory()
    config = {
        "extensions": {
            "security_ext": {
                "type": "security",
                "enabled": True,
                "patterns": ["email"],
            }
        }
    }
    logger = factory.create_logger(config=config, logger_type="sync")
    cfg = logger.get_config()
    assert cfg is not None
    assert hasattr(cfg, "_extension_manager")


def test_create_logger_convenience_accepts_name_string() -> None:
    logger = create_logger("unit-logger", logger_type="sync")
    assert isinstance(logger, SyncLogger)
    assert logger.name == "unit-logger"
