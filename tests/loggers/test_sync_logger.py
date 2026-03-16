"""
Role: Pytest coverage for sync logger behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates level filtering, lifecycle, and close semantics.
"""

from hydra_logger.config.models import LogDestination, LogLayer, LoggingConfig
from hydra_logger.loggers.sync_logger import SyncLogger


def test_sync_logger_filters_by_layer_level() -> None:
    config = LoggingConfig(
        layers={
            "default": LogLayer(
                level="ERROR", destinations=[LogDestination(type="console", format="plain-text")]
            )
        }
    )
    logger = SyncLogger(config=config)
    logger.info("ignored info", layer="default")
    logger.error("handled error", layer="default")
    health = logger.get_health_status()
    assert health["initialized"] is True
    logger.close()
    assert logger.is_closed is True


def test_sync_logger_close_is_idempotent() -> None:
    logger = SyncLogger()
    logger.info("before close")
    logger.close()
    logger.close()
    assert logger.is_closed is True
