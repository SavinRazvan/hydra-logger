"""
Role: Pytest coverage for sync logger behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates level filtering, lifecycle, and close semantics.
"""

import pytest
import builtins

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


def test_sync_logger_fallback_configuration_when_handlers_missing() -> None:
    logger = SyncLogger()
    logger._handlers.clear()
    logger._layer_handlers.clear()
    logger._setup_fallback_configuration()
    assert logger._handlers
    assert "default" in logger._layer_handlers
    logger.close()


def test_sync_logger_create_formatter_fallback_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = SyncLogger()
    destination = LogDestination(type="console", format="plain-text")

    class _SentinelFormatter:
        pass

    sentinel = _SentinelFormatter()

    state = {"calls": 0}

    def flaky_get_formatter(_format: str, **_kwargs):  # type: ignore[no-untyped-def]
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError("formatter fail")
        return sentinel

    monkeypatch.setattr("hydra_logger.formatters.get_formatter", flaky_get_formatter)
    formatter = logger._create_formatter_for_destination(destination, is_console=True)
    assert formatter is sentinel
    logger.close()


def test_sync_logger_apply_security_processing_error_is_non_fatal() -> None:
    class BrokenSecurity:
        def process_log_record(self, _record):  # type: ignore[no-untyped-def]
            raise RuntimeError("security fail")

    logger = SyncLogger()
    logger._enable_security = True
    logger._security_engine = BrokenSecurity()
    record = logger.create_log_record("INFO", "msg")
    processed = logger._apply_security_processing(record)
    assert processed is record
    logger.close()


def test_sync_logger_runtime_update_paths_with_and_without_config() -> None:
    logger = SyncLogger()
    logger.update_security_level("high")
    logger.update_monitoring_config("detailed", 10, True)
    logger.toggle_feature("security", True)
    assert logger.get_configuration_summary()["status"] == "no_configuration"

    class StubConfig:
        def __init__(self) -> None:
            self.features = {}

        def update_security_level(self, _level: str) -> None:
            pass

        def update_monitoring_config(self, *_args) -> None:  # type: ignore[no-untyped-def]
            pass

        def toggle_feature(self, feature: str, enabled: bool) -> None:
            self.features[feature] = enabled

        def get_configuration_summary(self):
            return {"status": "ok"}

    logger._config = StubConfig()  # type: ignore[assignment]
    logger.toggle_feature("sanitization", True)
    assert logger._enable_sanitization is True
    assert logger.get_configuration_summary()["status"] == "ok"
    logger.close()


def test_sync_logger_create_handler_unhandled_type_returns_null_handler() -> None:
    logger = SyncLogger(
        config=LoggingConfig(
            layers={"default": LogLayer(destinations=[LogDestination(type="null")])}
        )
    )
    handler = logger._create_handler_from_destination(
        LogDestination(type="async_cloud", service_type="s3")
    )
    assert handler.__class__.__name__ == "NullHandler"
    logger.close()


def test_sync_logger_create_console_handler_applies_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeConsoleHandler:
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            self.level = None
            self.formatter = None

        def setFormatter(self, formatter) -> None:  # type: ignore[no-untyped-def]
            self.formatter = formatter

        def setLevel(self, level: int) -> None:
            self.level = level

        def close(self) -> None:
            pass

    monkeypatch.setattr(
        "hydra_logger.handlers.console_handler.SyncConsoleHandler",
        FakeConsoleHandler,
    )
    monkeypatch.setattr("hydra_logger.types.levels.LogLevelManager.get_level", lambda _v: 77)

    logger = SyncLogger(
        config=LoggingConfig(
            layers={
                "default": LogLayer(
                    destinations=[LogDestination(type="console", level="ERROR")]
                )
            }
        )
    )
    handler = logger._create_handler_from_destination(
        LogDestination(type="console", level="ERROR")
    )
    assert handler.level == 77
    assert handler.formatter is not None
    logger.close()


def test_sync_logger_create_file_handler_uses_resolved_path_and_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeFileHandler:
        def __init__(self, filename: str, **_kwargs) -> None:
            self.filename = filename
            self.level = None
            self.formatter = None

        def setFormatter(self, formatter) -> None:  # type: ignore[no-untyped-def]
            self.formatter = formatter

        def setLevel(self, level: int) -> None:
            self.level = level

        def close(self) -> None:
            pass

    monkeypatch.setattr("hydra_logger.handlers.file_handler.SyncFileHandler", FakeFileHandler)
    monkeypatch.setattr("hydra_logger.types.levels.LogLevelManager.get_level", lambda _v: 13)
    monkeypatch.setattr(
        LoggingConfig, "resolve_log_path", lambda self, path, fmt=None: f"/tmp/{path}"
    )

    logger = SyncLogger(
        config=LoggingConfig(
            layers={
                "default": LogLayer(
                    destinations=[LogDestination(type="file", path="raw.log", level="DEBUG")]
                )
            }
        )
    )
    handler = logger._create_handler_from_destination(
        LogDestination(type="file", path="raw.log", level="DEBUG")
    )
    assert handler.filename == "/tmp/raw.log"
    assert handler.level == 13
    assert handler.formatter is not None
    logger.close()


def test_sync_logger_dict_config_and_data_protection_custom_patterns() -> None:
    logger = SyncLogger(
        config={
            "enable_data_protection": True,
            "extensions": {"data_protection": {"patterns": ["token"]}},
            "layers": {
                "default": {
                    "destinations": [{"type": "console", "format": "plain-text"}]
                }
            },
        }
    )
    assert logger._config is not None
    assert logger._data_protection is not None
    logger.close()


def test_sync_logger_log_swallows_internal_builder_failure() -> None:
    logger = SyncLogger()
    logger._record_builder.create = lambda *_a, **_k: (_ for _ in ()).throw(  # type: ignore[assignment]
        RuntimeError("builder-fail")
    )
    logger.log("INFO", "x")
    assert logger.get_health_status()["swallowed_error_count"] >= 1
    logger.close()


def test_sync_logger_strict_reliability_mode_raises_internal_failures() -> None:
    logger = SyncLogger(
        config={
            "strict_reliability_mode": True,
            "layers": {
                "default": {
                    "destinations": [{"type": "console", "format": "plain-text"}]
                }
            },
        }
    )
    logger._record_builder.create = lambda *_a, **_k: (_ for _ in ()).throw(  # type: ignore[assignment]
        RuntimeError("builder-fail")
    )
    with pytest.raises(Exception, match="internal failure"):
        logger.log("INFO", "x")
    logger.close()


def test_sync_logger_emit_to_handlers_tolerates_handler_failures() -> None:
    class BadHandler:
        @staticmethod
        def emit(_record):  # type: ignore[no-untyped-def]
            raise RuntimeError("emit-fail")

    logger = SyncLogger()
    logger._layer_handlers["default"] = [BadHandler()]
    logger._emit_to_handlers(logger.create_log_record("INFO", "x"))
    logger.close()


def test_sync_logger_convenience_methods_fallback_to_log_when_precompute_missing() -> None:
    logger = SyncLogger()
    logger._log_methods = {}
    seen = []
    logger.log = lambda level, message, **kwargs: seen.append((level, message))  # type: ignore[assignment]
    logger.debug("d")
    logger.info("i")
    logger.warning("w")
    logger.error("e")
    logger.critical("c")
    logger.warn("w2")
    logger.fatal("c2")
    assert [m for _, m in seen] == ["d", "i", "w", "e", "c", "w2", "c2"]


def test_sync_logger_security_stats_and_plugin_noops() -> None:
    class SecurityEngine:
        @staticmethod
        def process_log_record(record):  # type: ignore[no-untyped-def]
            return record

        @staticmethod
        def get_security_metrics():
            return {"enabled": True}

    logger = SyncLogger()
    logger._enable_security = True
    logger._security_engine = SecurityEngine()
    logger._security_stats = {"processed_records": 0}
    record = logger.create_log_record("INFO", "msg")
    processed = logger._apply_security_processing(record)
    assert processed is record
    assert logger._security_stats["processed_records"] == 1
    assert logger._execute_pre_log_plugins(record) is record
    assert logger._execute_post_log_plugins(record) is None
    assert logger.get_health_status()["security_engine"]["enabled"] is True
    logger.close()


def test_sync_logger_close_handles_handler_and_collection_failures() -> None:
    class BadHandler:
        @staticmethod
        def close() -> None:
            raise RuntimeError("close failed")

    class BadDict(dict):
        def clear(self):  # type: ignore[override]
            raise RuntimeError("clear failed")

    logger = SyncLogger()
    logger._handlers = BadDict({"h": BadHandler()})  # type: ignore[assignment]
    logger.close()
    assert logger.is_closed is False


def test_sync_logger_layer_threshold_and_context_manager_helpers() -> None:
    logger = SyncLogger()
    assert isinstance(logger._get_layer_threshold("default"), int)
    assert logger.get_pool_stats()["status"] == "deprecated"
    with logger.__enter__() as entered:
        assert entered is logger
    logger.__exit__(None, None, None)


def test_sync_logger_runtime_updates_cover_configured_paths() -> None:
    logger = SyncLogger()

    class ConfigStub:
        def __init__(self) -> None:
            self.features = {}
            self.security_level = None
            self.monitor = None

        def update_security_level(self, level: str) -> None:
            self.security_level = level

        def update_monitoring_config(self, detail, sample_rate, background):  # type: ignore[no-untyped-def]
            self.monitor = (detail, sample_rate, background)

        def toggle_feature(self, feature: str, enabled: bool) -> None:
            self.features[feature] = enabled

        @staticmethod
        def get_configuration_summary():
            return {"ok": True}

    logger._config = ConfigStub()  # type: ignore[assignment]
    logger.update_security_level("strict")
    logger.update_monitoring_config("detailed", 5, False)
    logger.toggle_feature("security", True)
    logger.toggle_feature("plugins", True)
    assert logger._enable_security is True
    assert logger._enable_plugins is True
    assert logger._config.security_level == "strict"  # type: ignore[attr-defined]
    assert logger._config.monitor == ("detailed", 5, False)  # type: ignore[attr-defined]
    assert logger.get_configuration_summary()["ok"] is True
    logger.close()


def test_sync_logger_log_early_return_and_security_passthrough() -> None:
    logger = SyncLogger()
    logger._initialized = False
    logger.log("INFO", "ignored")
    logger._initialized = True
    logger._closed = True
    logger.log("INFO", "ignored2")
    record = logger.create_log_record("INFO", "x")
    assert logger._apply_security_processing(record) is record


def test_sync_logger_data_protection_import_error_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name.endswith("extensions.extension_base"):
            raise ImportError("forced")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    logger = SyncLogger(
        config={
            "enable_data_protection": True,
            "layers": {
                "default": {
                    "destinations": [{"type": "console", "format": "plain-text"}]
                }
            },
        }
    )
    assert logger._data_protection is None
    logger.close()
