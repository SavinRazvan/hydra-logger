"""
Role: Tests for BatchedHTTPHandler flush behavior.
Used By:
 - Pytest discovery and CI.
Depends On:
 - hydra_logger.handlers.batched_http_handler
Notes:
 - Uses mocked requests session to avoid network I/O.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from hydra_logger.handlers.batched_http_handler import BatchedHTTPHandler
from hydra_logger.types.records import LogRecord


class _Resp:
    def raise_for_status(self) -> None:
        return None


def test_batched_handler_flushes_on_batch_size() -> None:
    session = MagicMock()
    session.request.return_value = _Resp()

    h = BatchedHTTPHandler(
        "http://example.test/ingest",
        connection_probe=False,
        batch_size=2,
        flush_interval=300.0,
    )
    h._session = session
    h._connected = True
    h._connection = object()  # short-circuit BaseNetworkHandler._connect

    rec = LogRecord(message="a", level_name="INFO", layer="L")
    h.emit(rec)
    assert session.request.call_count == 0
    h.emit(rec)
    assert session.request.call_count == 1
    call_kw = session.request.call_args.kwargs
    assert call_kw.get("data") is not None
    assert b"\n" in call_kw["data"]


def test_batched_handler_close_flushes_pending() -> None:
    session = MagicMock()
    session.request.return_value = _Resp()

    h = BatchedHTTPHandler(
        "http://example.test/ingest",
        connection_probe=False,
        batch_size=10,
        flush_interval=300.0,
    )
    h._session = session
    h._connected = True
    h._connection = object()
    h.emit(LogRecord(message="only", level_name="INFO", layer="L"))
    h.close()
    assert session.request.call_count >= 1


def test_batched_mixed_payload_falls_back_to_single_posts() -> None:
    session = MagicMock()
    session.request.return_value = _Resp()

    def enc(rec: LogRecord, fmt: object) -> bytes:
        return b"raw"

    h = BatchedHTTPHandler(
        "http://example.test/ingest",
        connection_probe=False,
        batch_size=2,
        flush_interval=300.0,
        payload_encoder=enc,
    )
    h._session = session
    h._connected = True
    h._connection = object()
    h.emit(LogRecord(message="a", level_name="INFO", layer="L"))
    h.emit(LogRecord(message="b", level_name="INFO", layer="L"))
    assert session.request.call_count == 2
