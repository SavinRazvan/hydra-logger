"""
Role: Pytest coverage for logger manager behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates caching, removal, and default configuration lifecycle.
"""

from types import SimpleNamespace

import pytest

from hydra_logger.config.defaults import get_default_config
from hydra_logger.core import logger_management as logger_management_module
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


def test_logger_manager_create_and_config_failure_paths(monkeypatch) -> None:
    manager = LoggerManager()

    class Factory:
        @staticmethod
        def create_logger(**_kwargs):
            return SimpleNamespace(name="old")

    manager._factory = Factory()
    created = manager._create_logger("svc", config=None, logger_type="sync")
    assert created.name == "svc"

    class BrokenFactory:
        @staticmethod
        def create_logger(**_kwargs):
            raise RuntimeError("factory boom")

    manager._factory = BrokenFactory()
    with pytest.raises(Exception, match="Failed to create logger"):
        manager._create_logger("svc", config=None, logger_type="sync")


def test_logger_manager_remove_close_and_get_config_branches() -> None:
    manager = LoggerManager()
    closed = {"count": 0}

    class Closable:
        @staticmethod
        def close():
            closed["count"] += 1

        @staticmethod
        def get_config():
            return "cfg"

    manager._loggers["x"] = Closable()
    assert manager.getLoggerConfig("x") == "cfg"
    assert manager.removeLogger("x") is True
    assert closed["count"] == 1

    class BadClose:
        @staticmethod
        def close():
            raise RuntimeError("close failed")

    manager._loggers["y"] = BadClose()
    assert manager.removeLogger("y") is True
    assert manager.getLoggerConfig("missing") is None

    manager._loggers["z"] = object()
    assert manager.getLoggerConfig("z") is None


def test_logger_manager_create_config_for_dotted_name_branch() -> None:
    manager = LoggerManager()
    cfg = manager._create_config_for_logger("svc.api")
    assert cfg is manager.getDefaultConfig()


def test_module_level_logger_management_wrappers(monkeypatch) -> None:
    class DummyManager:
        def __init__(self):
            self.default = "default"

        def getLogger(self, name=None, config=None, logger_type="sync", **kwargs):
            return {
                "name": name,
                "type": logger_type,
                "config": config,
                "kwargs": kwargs,
            }

        def hasLogger(self, name):
            return name == "exists"

        def removeLogger(self, name):
            return name == "exists"

        def listLoggers(self):
            return ["a", "b"]

        def clearLoggers(self):
            return None

        def setDefaultConfig(self, config):
            self.default = config

        def getDefaultConfig(self):
            return self.default

    dummy = DummyManager()
    monkeypatch.setattr(logger_management_module, "_logger_manager", dummy)

    assert logger_management_module.getLogger("n")["name"] == "n"
    assert logger_management_module.hasLogger("exists") is True
    assert logger_management_module.removeLogger("missing") is False
    assert logger_management_module.listLoggers() == ["a", "b"]
    logger_management_module.clearLoggers()
    logger_management_module.setDefaultConfig("cfg")
    assert logger_management_module.getDefaultConfig() == "cfg"
    assert logger_management_module.getSyncLogger("sync")["type"] == "sync"
    assert logger_management_module.getAsyncLogger("async")["type"] == "async"


def test_logger_manager_get_logger_double_checked_lock_branch() -> None:
    manager = LoggerManager()

    class InjectOnEnterLock:
        def __init__(self, callback) -> None:
            self._callback = callback

        def __enter__(self):
            self._callback()
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    manager._locks["race"] = InjectOnEnterLock(
        lambda: manager._loggers.setdefault("race", "created-by-race")
    )
    assert manager.getLogger("race") == "created-by-race"
