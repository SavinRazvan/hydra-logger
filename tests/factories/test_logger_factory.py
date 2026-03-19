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

from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer
from hydra_logger.factories.logger_factory import (
    LoggerFactory,
    create_async_logger,
    create_composite_async_logger,
    create_composite_logger,
    create_custom_logger,
    create_default_logger,
    create_development_logger,
    create_logger,
    create_production_logger,
    create_sync_logger,
)
from hydra_logger.loggers.async_logger import AsyncLogger
from hydra_logger.loggers.composite_logger import CompositeAsyncLogger, CompositeLogger
from hydra_logger.loggers.sync_logger import SyncLogger


def test_logger_factory_dispatches_sync_and_async_types() -> None:
    factory = LoggerFactory()
    sync_logger = factory.create_logger(logger_type="sync")
    async_logger = factory.create_logger(logger_type="async")
    composite_logger = factory.create_logger(logger_type="composite")
    composite_async_logger = factory.create_logger(logger_type="composite-async")
    assert isinstance(sync_logger, SyncLogger)
    assert isinstance(async_logger, AsyncLogger)
    assert isinstance(composite_logger, CompositeLogger)
    assert isinstance(composite_async_logger, CompositeAsyncLogger)


def test_logger_factory_rejects_unknown_logger_type() -> None:
    factory = LoggerFactory()
    with pytest.raises(ValueError, match="Unknown logger type"):
        factory.create_logger(logger_type="invalid")


def test_logger_factory_rejects_invalid_dict_config() -> None:
    factory = LoggerFactory()
    with pytest.raises(Exception):
        factory.create_logger(config={"layers": {"default": {"destinations": "bad"}}})


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


def test_convenience_logger_creators_accept_name_strings() -> None:
    sync_logger = create_sync_logger("sync-name")
    async_logger = create_async_logger("async-name")
    composite_logger = create_composite_logger("composite-name")
    composite_async_logger = create_composite_async_logger("composite-async-name")

    assert isinstance(sync_logger, SyncLogger)
    assert sync_logger.name == "sync-name"
    assert isinstance(async_logger, AsyncLogger)
    assert async_logger.name == "async-name"
    assert isinstance(composite_logger, CompositeLogger)
    assert composite_logger.name == "composite-name"
    assert isinstance(composite_async_logger, CompositeAsyncLogger)
    assert composite_async_logger.name == "composite-async-name"


def test_template_convenience_functions_create_sync_loggers() -> None:
    assert isinstance(create_default_logger(logger_type="sync"), SyncLogger)
    assert isinstance(create_development_logger(logger_type="sync"), SyncLogger)
    assert isinstance(create_production_logger(logger_type="sync"), SyncLogger)
    assert isinstance(create_custom_logger(logger_type="sync"), SyncLogger)


def test_convenience_logger_creators_accept_config_objects() -> None:
    cfg = LoggingConfig()
    assert isinstance(create_sync_logger(cfg), SyncLogger)
    assert isinstance(create_async_logger(cfg), AsyncLogger)
    assert isinstance(create_composite_logger(cfg), CompositeLogger)
    assert isinstance(create_composite_async_logger(cfg), CompositeAsyncLogger)


def test_factory_cache_and_default_config_setters() -> None:
    factory = LoggerFactory()
    cfg = LoggingConfig()
    logger = factory.create_sync_logger(config=cfg, name="cached")
    factory.set_default_config(cfg)
    assert factory._get_default_config() is cfg
    factory.cache_logger("cache-key", logger)
    assert factory.get_cached_logger("cache-key") is logger
    factory.clear_cache()
    assert factory.get_cached_logger("cache-key") is None


def test_setup_extensions_handles_import_error(
    caplog, monkeypatch: pytest.MonkeyPatch
) -> None:
    import hydra_logger.extensions as extensions_mod

    factory = LoggerFactory()
    cfg = LoggingConfig(
        extensions={"security_ext": {"type": "security", "enabled": True}}
    )

    monkeypatch.delattr(extensions_mod, "ExtensionManager", raising=False)
    with caplog.at_level("WARNING", logger="hydra_logger.factories.logger_factory"):
        factory._setup_extensions(cfg)
    assert "Extension system not available" in caplog.text


def test_setup_extensions_handles_runtime_error(
    caplog, monkeypatch: pytest.MonkeyPatch
) -> None:
    import hydra_logger.extensions as extensions_mod

    class _BrokenManager:
        def create_extension(self, *args, **kwargs):
            raise RuntimeError("extension create failed")

    factory = LoggerFactory()
    cfg = LoggingConfig(extensions={"broken": {"enabled": True}})
    monkeypatch.setattr(extensions_mod, "ExtensionManager", _BrokenManager)
    with caplog.at_level("ERROR", logger="hydra_logger.factories.logger_factory"):
        factory._setup_extensions(cfg)
    assert "Error setting up extensions" in caplog.text


def test_setup_extensions_logs_disabled_extension_info(caplog) -> None:
    factory = LoggerFactory()
    cfg = LoggingConfig(
        extensions={
            "security_ext": {
                "type": "security",
                "enabled": False,
                "patterns": ["email"],
            }
        }
    )
    with caplog.at_level("INFO", logger="hydra_logger.factories.logger_factory"):
        factory._setup_extensions(cfg)
    assert "created but disabled" in caplog.text


def test_composite_async_requires_explicit_file_destination_for_file_output(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    monkeypatch.chdir(tmp_path)
    cfg = LoggingConfig(
        layers={
            "default": LogLayer(
                destinations=[LogDestination(type="console", format="plain-text")]
            )
        }
    )
    logger = create_logger(cfg, logger_type="composite-async")
    assert isinstance(logger, CompositeAsyncLogger)
    asyncio.run(logger.log("INFO", "no-file-destination"))
    asyncio.run(logger.aclose())
    assert not (
        tmp_path / "logs" / "composite_logger_compositeasynclogger.log"
    ).exists()


def test_composite_async_writes_when_explicit_file_destination_is_configured(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    monkeypatch.chdir(tmp_path)
    cfg = LoggingConfig(
        layers={
            "default": LogLayer(
                destinations=[
                    LogDestination(
                        type="file", path="explicit-composite.log", format="plain-text"
                    )
                ]
            )
        }
    )
    logger = create_logger(cfg, logger_type="composite-async")
    assert isinstance(logger, CompositeAsyncLogger)
    asyncio.run(logger.log("INFO", "explicit-destination"))
    asyncio.run(logger.aclose())
    output_path = tmp_path / "logs" / "explicit-composite.log"
    assert output_path.exists()
    assert "explicit-destination" in output_path.read_text(encoding="utf-8")


def test_default_config_does_not_create_files_across_logger_modes(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    monkeypatch.chdir(tmp_path)

    sync_logger = create_logger("default-sync-safety", logger_type="sync")
    sync_logger.log("INFO", "sync-default")

    async_logger = create_logger("default-async-safety", logger_type="async")
    asyncio.run(async_logger.log_async("INFO", "async-default"))
    asyncio.run(async_logger.aclose())

    composite_logger = create_logger(
        "default-composite-safety", logger_type="composite"
    )
    composite_logger.log("INFO", "composite-default")
    composite_logger.close()

    composite_async_logger = create_logger(
        "default-composite-async-safety", logger_type="composite-async"
    )
    asyncio.run(composite_async_logger.log("INFO", "composite-async-default"))
    asyncio.run(composite_async_logger.aclose())

    assert not (tmp_path / "logs").exists()


def test_network_destination_does_not_create_local_log_files(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = LoggingConfig(
        layers={
            "default": LogLayer(
                destinations=[
                    LogDestination(type="async_cloud", service_type="websocket")
                ]
            )
        }
    )
    logger = create_logger(cfg, logger_type="sync", name="network-only-safety")
    logger.log("INFO", "network-only")
    assert not (tmp_path / "logs").exists()
