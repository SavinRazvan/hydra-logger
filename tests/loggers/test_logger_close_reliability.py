"""
Role: Tests for policy-governed logger close lifecycle failures.
Used By:
 - pytest discovery for hydra_logger.loggers close paths.
Depends On:
 - hydra_logger
 - pytest
Notes:
 - Uses failing handlers to assert diagnostics, counters, and strict mode raises.
"""

from __future__ import annotations

import asyncio

import pytest

from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer
from hydra_logger.core.exceptions import HydraLoggerError
from hydra_logger.loggers.async_logger import AsyncLogger
from hydra_logger.loggers.sync_logger import SyncLogger


class _CloseRaises:
    def close(self) -> None:
        raise OSError("handler close failed")


def test_sync_logger_close_records_handler_failure_and_health() -> None:
    cfg = LoggingConfig(
        layers={
            "default": LogLayer(
                level="INFO",
                destinations=[LogDestination(type="console")],
            )
        }
    )
    logger = SyncLogger(config=cfg)
    logger._handlers["bad"] = _CloseRaises()  # type: ignore[assignment]
    logger.close()
    health = logger.get_health_status()
    assert health["handler_close_failures"] >= 1
    assert health["close_completed"] is True
    assert "last_lifecycle_error" in health


def test_sync_logger_close_strict_mode_raises() -> None:
    cfg = LoggingConfig(
        strict_reliability_mode=True,
        layers={
            "default": LogLayer(
                level="INFO",
                destinations=[LogDestination(type="console")],
            )
        },
    )
    logger = SyncLogger(config=cfg)
    logger._handlers["bad"] = _CloseRaises()  # type: ignore[assignment]
    with pytest.raises(HydraLoggerError, match="lifecycle failure"):
        logger.close()
    assert logger.get_health_status()["handler_close_failures"] >= 1


def test_async_logger_aclose_records_handler_failure() -> None:
    cfg = LoggingConfig(
        layers={
            "default": LogLayer(
                level="INFO",
                destinations=[LogDestination(type="console")],
            )
        }
    )
    logger = AsyncLogger(config=cfg)
    logger._handlers["bad"] = _CloseRaises()  # type: ignore[assignment]

    async def _run() -> None:
        await logger.aclose()

    asyncio.run(_run())
    health = logger.get_health_status()
    assert health["handler_close_failures"] >= 1
    assert health["close_completed"] is True


def test_async_logger_aclose_strict_mode_raises_on_handler_close_failure() -> None:
    cfg = LoggingConfig(
        strict_reliability_mode=True,
        layers={
            "default": LogLayer(
                level="INFO",
                destinations=[LogDestination(type="console")],
            )
        },
    )
    logger = AsyncLogger(config=cfg)
    logger._handlers["bad"] = _CloseRaises()  # type: ignore[assignment]

    async def _run() -> None:
        with pytest.raises(HydraLoggerError, match="lifecycle failure"):
            await logger.aclose()

    asyncio.run(_run())
