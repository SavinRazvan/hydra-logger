"""
Role: Pytest coverage for extension manager behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates registration, ordering, and failure isolation.
"""

import pytest

from hydra_logger.extensions.extension_base import ExtensionBase
from hydra_logger.extensions.extension_manager import ExtensionManager


class PrefixExtension(ExtensionBase):
    def process(self, data):
        return f"prefix:{data}" if self.enabled else data


class FailingExtension(ExtensionBase):
    def process(self, data):
        raise RuntimeError("boom")


class MetricsExtension(ExtensionBase):
    def process(self, data):
        return data

    def get_metrics(self):
        return {"hits": 1}


def test_extension_manager_register_create_and_process_order() -> None:
    manager = ExtensionManager()
    manager.register_extension_type("prefix", PrefixExtension)
    manager.create_extension("prefix_ext", "prefix", enabled=True)
    assert manager.get_processing_order() == ["prefix_ext"]
    assert manager.process_data("msg") == "prefix:msg"


def test_extension_manager_enable_disable_and_remove() -> None:
    manager = ExtensionManager()
    manager.create_extension("fmt", "formatting", enabled=False, add_context=True)
    assert manager.list_enabled_extensions() == []
    manager.enable_extension("fmt")
    assert manager.list_enabled_extensions() == ["fmt"]
    manager.disable_extension("fmt")
    assert manager.list_enabled_extensions() == []
    manager.remove_extension("fmt")
    assert manager.list_all_extensions() == []


def test_extension_manager_continues_when_one_extension_fails() -> None:
    manager = ExtensionManager()
    manager.register_extension_type("prefix", PrefixExtension)
    manager.register_extension_type("fail", FailingExtension)
    manager.create_extension("a", "prefix", enabled=True)
    manager.create_extension("b", "fail", enabled=True)
    manager.create_extension("c", "prefix", enabled=True)
    manager.set_processing_order(["a", "b", "c"])
    assert manager.process_data("msg") == "prefix:prefix:msg"


def test_extension_manager_unknown_extension_type_raises() -> None:
    manager = ExtensionManager()
    with pytest.raises(ValueError, match="Unknown extension type"):
        manager.create_extension("x", "unknown")


def test_extension_manager_add_extension_and_configure_missing_name_noop() -> None:
    manager = ExtensionManager()
    ext = PrefixExtension(enabled=True)
    manager.add_extension("prefix_ext", ext)
    manager.configure_extension("prefix_ext", custom="v")
    manager.configure_extension("missing", mode="strict")
    assert manager.get_extension("prefix_ext") is ext
    assert ext.get_config()["custom"] == "v"
    assert manager.get_extension("missing") is None


def test_extension_manager_process_data_early_return_and_skip_missing_or_disabled() -> None:
    manager = ExtensionManager()
    assert manager.process_data("noop") == "noop"

    manager.register_extension_type("prefix", PrefixExtension)
    manager.create_extension("enabled", "prefix", enabled=True)
    manager.create_extension("disabled", "prefix", enabled=False)
    manager.set_processing_order(["enabled", "disabled"])
    del manager.extensions["disabled"]
    assert manager.process_data("msg") == "prefix:msg"


def test_extension_manager_set_processing_order_validates_names() -> None:
    manager = ExtensionManager()
    manager.create_extension("fmt", "formatting", enabled=True)
    with pytest.raises(ValueError, match="not found"):
        manager.set_processing_order(["missing"])


def test_extension_manager_status_clear_remove_and_available_types() -> None:
    manager = ExtensionManager()
    manager.create_extension("perf", "performance", enabled=False, sample_rate=3)
    status = manager.get_extension_status()
    assert status["perf"]["enabled"] is False
    assert status["perf"]["type"] == "PerformanceExtension"
    assert status["perf"]["config"]["sample_rate"] == 3

    available = manager.get_available_types()
    assert "security" in available
    assert "formatting" in available
    assert "performance" in available

    manager.enable_extension("perf")
    manager.remove_extension("perf")
    manager.remove_extension("missing")
    manager.clear_extensions()
    assert manager.list_all_extensions() == []
    assert manager.get_processing_order() == []


def test_extension_manager_enable_disable_missing_extension_noop() -> None:
    manager = ExtensionManager()
    manager.enable_extension("ghost")
    manager.disable_extension("ghost")
    assert manager.list_all_extensions() == []


def test_extension_manager_collects_metrics_only_from_extensions_with_method() -> None:
    manager = ExtensionManager()
    manager.add_extension("with_metrics", MetricsExtension(enabled=True))
    manager.add_extension("without_metrics", PrefixExtension(enabled=True))
    assert manager.get_extension_metrics() == {"with_metrics": {"hits": 1}}
