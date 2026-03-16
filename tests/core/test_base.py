"""
Role: Pytest coverage for core base component abstractions.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates shared lifecycle/config behavior across base abstractions.
"""

from hydra_logger.core.base import BaseFormatter, BaseHandler, BaseLogger, BaseMonitor, BasePlugin


class DummyLogger(BaseLogger):
    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def log(self, level: str, message: str, **kwargs) -> None:
        self._last = (level, message, kwargs)


class DummyHandler(BaseHandler):
    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def emit(self, record) -> None:
        self._record = record


class DummyFormatter(BaseFormatter):
    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def format(self, record) -> str:
        return str(record)


class DummyPlugin(BasePlugin):
    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def process_event(self, event) -> None:
        self._event = event


class DummyMonitor(BaseMonitor):
    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._initialized = False

    def collect_metrics(self):
        return {"ok": 1}


def test_base_logger_and_handler_state_and_collections() -> None:
    logger = DummyLogger("x", enabled=False, config={"a": 1})
    assert logger.is_enabled() is False
    logger.enable()
    assert logger.is_enabled() is True
    logger.update_config({"b": 2})
    assert logger.get_config()["b"] == 2

    handler = DummyHandler("h", level="ERROR")
    logger.add_handler("h", handler)
    assert "h" in logger.get_handlers()
    logger.remove_handler("h")
    assert logger.get_handlers() == {}


def test_base_formatter_plugin_monitor_helpers() -> None:
    formatter = DummyFormatter("fmt", format_string="{message}")
    assert formatter.get_format_string() == "{message}"
    formatter.set_format_string("{level}:{message}")
    assert formatter.get_format_string() == "{level}:{message}"

    plugin = DummyPlugin("p", plugin_type="security")
    assert plugin.get_plugin_type() == "security"

    monitor = DummyMonitor("m")
    monitor.update_metric("count", 3)
    assert monitor.get_metrics()["count"] == 3


def test_base_component_logs_config_update_failures(caplog) -> None:
    logger = DummyLogger("x")
    logger._config = None  # force update failure path
    with caplog.at_level("ERROR", logger="hydra_logger.core.base"):
        try:
            logger.update_config({"a": 1})
        except Exception:
            pass
    assert "Component config update failed for component=x" in caplog.text
