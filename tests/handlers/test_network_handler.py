"""
Role: Pytest coverage for network handler retry and factory behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates retry delay policies and factory error paths.
"""

from hydra_logger.handlers.network_handler import (
    BaseNetworkHandler,
    DatagramHandler,
    NetworkConfig,
    NetworkHandlerFactory,
    RetryPolicy,
    SocketHandler,
)
from hydra_logger.handlers import network_handler as network_module
from hydra_logger.types.records import LogRecord


class DummyNetworkHandler(BaseNetworkHandler):
    def _establish_connection(self) -> bool:
        self._connection = object()
        self._connected = True
        return True

    def _close_connection(self) -> None:
        self._connection = None
        self._connected = False

    def emit(self, record) -> None:
        return None


def test_network_handler_retry_delay_policies() -> None:
    config = NetworkConfig(host="localhost", port=8080, max_retries=5)
    handler = DummyNetworkHandler(config)

    handler._config.retry_policy = RetryPolicy.LINEAR
    handler._retry_count = 3
    assert handler._get_retry_delay() == 3.0

    handler._config.retry_policy = RetryPolicy.EXPONENTIAL
    assert handler._get_retry_delay() == 4.0

    handler._config.retry_policy = RetryPolicy.FIBONACCI
    assert handler._get_retry_delay() == 2.0


def test_network_handler_factory_rejects_unknown_type() -> None:
    try:
        NetworkHandlerFactory.create_handler("unknown")
    except ValueError as exc:
        assert "Unknown handler type" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown network handler type")


def test_network_handler_retry_guardrails_and_stats_snapshot() -> None:
    config = NetworkConfig(
        host="localhost",
        port=8080,
        max_retries=2,
        retry_delay=1.0,
        max_retry_delay=10.0,
    )
    handler = DummyNetworkHandler(config)

    handler._retry_count = 2
    assert handler._should_retry(RuntimeError("boom")) is False

    handler._retry_count = 1
    handler._last_retry = 10.0
    original_time = network_module.time.time
    try:
        network_module.time.time = lambda: 10.5
        assert handler._should_retry(RuntimeError("too-soon")) is False
        assert handler._should_retry(ValueError("non-retryable")) is False
    finally:
        network_module.time.time = original_time

    stats = handler.get_network_stats()
    assert stats["config"]["host"] == "localhost"
    assert "failed" in stats["stats"]


def test_datagram_handler_truncates_payload_before_send() -> None:
    class DummyConn:
        def __init__(self) -> None:
            self.sent = b""
            self.addr = ("", 0)

        def settimeout(self, _timeout: float) -> None:
            return None

        def sendto(self, data: bytes, addr) -> None:
            self.sent = data
            self.addr = addr

        def close(self) -> None:
            return None

    handler = DatagramHandler(host="localhost", port=514, max_packet_size=8)
    conn = DummyConn()
    handler._connection = conn
    handler._connected = True
    record = LogRecord(level=20, level_name="INFO", message="abcdefghijk")
    handler.emit(record)
    assert conn.sent.decode("utf-8") == "INFO:..."


def test_network_handler_factory_creates_socket_without_real_connection(
    monkeypatch,
) -> None:
    monkeypatch.setattr(SocketHandler, "_establish_connection", lambda self: True)
    handler = NetworkHandlerFactory.create_handler(
        "socket", host="127.0.0.1", port=7001, protocol="udp"
    )
    assert isinstance(handler, SocketHandler)
