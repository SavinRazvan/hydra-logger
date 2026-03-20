"""
Role: Tests for logger factory config_path loading integration.
Used By:
 - Pytest discovery and CI.
Depends On:
 - hydra_logger.factories.logger_factory
Notes:
 - Ensures config_path and loader kwargs reach load_logging_config.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hydra_logger import create_sync_logger
from hydra_logger.config.loader import clear_logging_config_cache


@pytest.fixture(autouse=True)
def _clear_config_cache() -> None:
    clear_logging_config_cache()
    yield
    clear_logging_config_cache()


def test_create_sync_logger_from_config_path(tmp_path: Path) -> None:
    p = tmp_path / "l.yaml"
    p.write_text(
        """
default_level: INFO
layers:
  a:
    level: INFO
    destinations:
      - type: console
""",
        encoding="utf-8",
    )
    log = create_sync_logger(config_path=p, name="t")
    assert log._name == "t"
    assert log._config is not None
    assert log._config.default_level == "INFO"


def test_factory_rejects_config_and_config_path_together(tmp_path: Path) -> None:
    from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer
    from hydra_logger.factories.logger_factory import logger_factory

    p = tmp_path / "l.yaml"
    p.write_text(
        """
default_level: INFO
layers:
  a:
    level: INFO
    destinations:
      - type: console
""",
        encoding="utf-8",
    )
    cfg = LoggingConfig(
        layers={
            "a": LogLayer(
                destinations=[LogDestination(type="console")],
            )
        }
    )
    with pytest.raises(ValueError, match="only one"):
        logger_factory.create_sync_logger(config=cfg, config_path=p)


def test_factory_forwards_loader_kwargs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from hydra_logger.factories.logger_factory import LoggerFactory

    captured: dict[str, object] = {}

    def _fake_loader(_path: Path, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer

        return LoggingConfig(
            layers={"default": LogLayer(destinations=[LogDestination(type="null")])}
        )

    monkeypatch.setattr("hydra_logger.config.loader.load_logging_config", _fake_loader)
    fac = LoggerFactory()
    logger = fac.create_sync_logger(
        config_path=tmp_path / "cfg.yaml",
        max_merged_nodes=1234,
    )
    assert captured["max_merged_nodes"] == 1234
    logger.close()
