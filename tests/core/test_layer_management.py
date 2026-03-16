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

from hydra_logger.core.layer_management import LayerManager
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
