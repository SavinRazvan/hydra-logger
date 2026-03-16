"""
Role: Pytest coverage for logger manager behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates caching, removal, and default configuration lifecycle.
"""

from hydra_logger.config.defaults import get_default_config
from hydra_logger.core.logger_management import LoggerManager


def test_logger_manager_caches_loggers_by_name() -> None:
    manager = LoggerManager()
    first = manager.getLogger("service")
    second = manager.getLogger("service")
    assert first is second
    assert manager.hasLogger("service") is True


def test_logger_manager_remove_and_clear() -> None:
    manager = LoggerManager()
    manager.getLogger("a")
    manager.getLogger("b")
    assert set(manager.listLoggers()) == {"a", "b"}
    assert manager.removeLogger("a") is True
    assert manager.removeLogger("missing") is False
    manager.clearLoggers()
    assert manager.listLoggers() == []


def test_logger_manager_default_config_setter_getter() -> None:
    manager = LoggerManager()
    config = get_default_config()
    manager.setDefaultConfig(config)
    assert manager.getDefaultConfig() is config


def test_logger_manager_uses_root_name_when_name_missing() -> None:
    manager = LoggerManager()
    root_logger = manager.getLogger()
    assert root_logger is manager.getLogger("root")
    assert manager.hasLogger("root") is True
