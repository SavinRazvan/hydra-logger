"""
Role: Pytest coverage for extension manager behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates registration, ordering, and failure isolation.
"""

from hydra_logger.extensions.extension_base import ExtensionBase
from hydra_logger.extensions.extension_manager import ExtensionManager


class PrefixExtension(ExtensionBase):
    def process(self, data):
        return f"prefix:{data}" if self.enabled else data


class FailingExtension(ExtensionBase):
    def process(self, data):
        raise RuntimeError("boom")


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
