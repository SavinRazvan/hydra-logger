"""
Role: Pytest coverage for base and console handler behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates level filtering and buffered console flush lifecycle.
"""

import io

from hydra_logger.handlers.base_handler import BaseHandler
from hydra_logger.handlers.console_handler import SyncConsoleHandler
from hydra_logger.types.records import LogRecord


class DummyHandler(BaseHandler):
    def __init__(self):
        super().__init__(name="dummy", level=30)
        self.records = []

    def emit(self, record: LogRecord) -> None:
        self.records.append(record)


def test_base_handler_filters_by_level() -> None:
    handler = DummyHandler()
    low = LogRecord(level=20, level_name="INFO", message="low")
    high = LogRecord(level=40, level_name="ERROR", message="high")
    handler.handle(low)
    handler.handle(high)
    assert len(handler.records) == 1
    assert handler.records[0].message == "high"


def test_sync_console_handler_flushes_buffer_to_stream() -> None:
    stream = io.StringIO()
    handler = SyncConsoleHandler(stream=stream, buffer_size=1, flush_interval=60)
    handler.emit(LogRecord(level=20, level_name="INFO", message="hello"))
    output = stream.getvalue()
    assert "hello" in output
    stats = handler.get_stats()
    assert stats["messages_processed"] == 1
