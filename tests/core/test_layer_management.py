"""
Role: Pytest coverage for layer manager behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates setup fallback, layer lifecycle, and threshold/handler lookup.
"""

import pytest

from hydra_logger.core import layer_management as layer_management_module
from hydra_logger.core.layer_management import LayerConfiguration, LayerManager
from hydra_logger.types.levels import LogLevel


def test_layer_manager_setup_default_when_empty_config() -> None:
    manager = LayerManager()
    manager.setup_layers({})
    names = manager.get_layer_names()
    assert "default" in names
    handlers = manager.get_handlers_for_layer("missing")
    assert handlers


def test_layer_manager_add_remove_and_stats() -> None:
    manager = LayerManager()
    manager.setup_layers({"default": {"level": "INFO", "destinations": [{"type": "null"}]}})
    manager.add_layer("api", level="ERROR")
    assert manager.has_layer("api") is True
    assert manager.get_layer_threshold("api") == LogLevel.ERROR
    stats = manager.get_multi_layer_stats()
    assert stats["layer_count"] >= 2
    assert manager.remove_layer("api") is True


def test_layer_manager_cannot_remove_default_layer() -> None:
    manager = LayerManager()
    manager.setup_layers({"default": {"level": "INFO", "destinations": [{"type": "null"}]}})
    with pytest.raises(ValueError, match="Cannot remove default layer"):
        manager.remove_layer("default")


def test_layer_configuration_basic_mutators() -> None:
    layer = LayerConfiguration("api", "DEBUG")
    layer.add_destination({"type": "null"})
    layer.set_handlers([])
    layer.set_formatter(None)  # type: ignore[arg-type]
    assert layer.destinations == [{"type": "null"}]
    assert layer.get_level_numeric() == LogLevel.DEBUG


def test_layer_manager_setup_and_fallback_paths(monkeypatch) -> None:
    manager = LayerManager()

    monkeypatch.setattr(
        manager,
        "_create_layer",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    manager.setup_layers({"broken": {"level": "INFO", "destinations": []}})
    assert manager.get_layer_names() == []

    manager._handlers = {"other": ["h1"]}  # type: ignore[assignment]
    assert manager.get_handlers_for_layer("unknown") == ["h1"]
    manager.clear_all()
    assert manager.get_handlers_for_layer("unknown") == []
    assert manager.get_layer_threshold("unknown") == LogLevel.INFO


def test_layer_manager_create_handler_from_all_destination_types(tmp_path) -> None:
    manager = LayerManager()
    console = manager._create_handler_from_config(
        {"type": "console", "format": "plain-text", "use_colors": False, "stream": "stdout"}
    )
    assert console is not None

    file_handler = manager._create_handler_from_config(
        {"type": "file", "path": str(tmp_path / "app.log")}
    )
    assert file_handler is not None

    assert manager._create_handler_from_config({"type": "file"}) is None
    assert manager._create_handler_from_config({"type": "null"}) is not None
    assert manager._create_handler_from_config({"type": "unsupported"}) is not None

    class ObjDest:
        type = "console"

        @staticmethod
        def get(key, default=None):
            return default

    assert manager._create_handler_from_config(ObjDest()) is not None


def test_layer_manager_handler_creation_failure_and_default_setup_failure(monkeypatch) -> None:
    manager = LayerManager()
    from hydra_logger.formatters import get_formatter as real_get_formatter
    from hydra_logger.handlers import console_handler as console_handler_module

    class BadDestination:
        @property
        def type(self):
            raise RuntimeError("bad destination")

    assert manager._create_handler_from_config(BadDestination()) is None

    # Force console-handler creation failure branch in _create_handler_from_config.
    def broken_get_formatter(*_args, **_kwargs):
        raise RuntimeError("formatter failure")

    monkeypatch.setattr("hydra_logger.formatters.get_formatter", broken_get_formatter)
    assert manager._create_handler_from_config({"type": "console"}) is None
    monkeypatch.setattr("hydra_logger.formatters.get_formatter", real_get_formatter)

    # Force _setup_default_layer failure branch and verify graceful handling.
    class BrokenConsoleHandler:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("console init failed")

    monkeypatch.setattr(console_handler_module, "SyncConsoleHandler", BrokenConsoleHandler)
    monkeypatch.setattr(
        layer_management_module,
        "stdout",
        None,
    )
    manager._setup_default_layer()


def test_layer_manager_add_duplicate_remove_missing_and_object_config() -> None:
    manager = LayerManager()
    manager._create_layer(
        "obj",
        type("Cfg", (), {"level": "ERROR", "destinations": [{"type": "null"}]})(),
    )
    assert manager.has_layer("obj") is True
    assert manager.get_layer_config("obj") is not None

    manager.add_layer("unique", level="WARNING")
    with pytest.raises(ValueError, match="already exists"):
        manager.add_layer("unique", level="INFO")
    assert manager.remove_layer("missing") is False


def test_layer_manager_create_layer_runtime_failure_and_direct_lookup() -> None:
    manager = LayerManager()

    class BrokenCfg:
        @property
        def level(self):
            raise RuntimeError("bad layer")

        destinations = []

    with pytest.raises(RuntimeError, match="Failed to create layer"):
        manager._create_layer("broken", BrokenCfg())

    manager._handlers["api"] = ["h-api"]  # type: ignore[assignment]
    assert manager.get_handlers_for_layer("api") == ["h-api"]
