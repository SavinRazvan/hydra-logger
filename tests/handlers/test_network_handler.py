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
    HTTPHandler,
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


def test_network_handler_validate_config_rejects_invalid_values() -> None:
    handler = DummyNetworkHandler(NetworkConfig(host="ok", port=8080))
    handler._config.host = ""
    try:
        handler._validate_network_config()
    except ValueError as exc:
        assert "Invalid hostname" in str(exc)
    else:
        raise AssertionError("Expected invalid hostname validation error")

    handler._config.host = "localhost"
    handler._config.port = 70000
    try:
        handler._validate_network_config()
    except ValueError as exc:
        assert "Invalid port" in str(exc)
    else:
        raise AssertionError("Expected invalid port validation error")

    handler._config.port = 8080
    handler._config.timeout = 0
    try:
        handler._validate_network_config()
    except ValueError as exc:
        assert "Timeout must be positive" in str(exc)
    else:
        raise AssertionError("Expected timeout validation error")


def test_network_handler_error_handler_retry_and_disconnect_paths(monkeypatch) -> None:
    handler = DummyNetworkHandler(NetworkConfig(host="localhost", port=8080, max_retries=1))
    calls = {"disconnect": 0, "connect": 0, "sleep": 0}
    handler._disconnect = lambda: calls.__setitem__("disconnect", calls["disconnect"] + 1)  # type: ignore[method-assign]
    handler._connect = lambda: calls.__setitem__("connect", calls["connect"] + 1) or True  # type: ignore[method-assign]
    monkeypatch.setattr(network_module.time, "sleep", lambda _s: calls.__setitem__("sleep", calls["sleep"] + 1))

    handler._should_retry = lambda _error: True  # type: ignore[method-assign]
    handler._handle_network_error(RuntimeError("boom"))
    assert handler._stats["retries"] == 1
    assert calls["disconnect"] >= 1
    assert calls["connect"] == 1
    assert calls["sleep"] == 1

    handler._should_retry = lambda _error: False  # type: ignore[method-assign]
    handler._handle_network_error(RuntimeError("stop"))
    assert calls["disconnect"] >= 2


def test_network_handler_close_delegates_to_disconnect() -> None:
    handler = DummyNetworkHandler(NetworkConfig(host="localhost", port=8080))
    marker = {"closed": False}
    handler._disconnect = lambda: marker.__setitem__("closed", True)  # type: ignore[method-assign]
    handler.close()
    assert marker["closed"] is True


def test_network_handler_logs_disconnect_failure(caplog) -> None:
    handler = DummyNetworkHandler(NetworkConfig(host="localhost", port=8080))
    handler._connection = object()

    def _broken_close() -> None:
        raise RuntimeError("disconnect boom")

    handler._close_connection = _broken_close  # type: ignore[method-assign]
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.network_handler"):
        handler._disconnect()

    assert "Network disconnect failed" in caplog.text


def test_network_handler_set_formatter_flags_and_reset() -> None:
    class CsvLikeFormatter:
        def format_headers(self):
            return "h1,h2"

        def should_write_headers(self):
            return True

    class JsonLikeFormatter:
        def write_header(self):
            return "{}"

    class StreamingFormatter:
        def format_for_streaming(self, _record):
            return "stream"

    handler = DummyNetworkHandler(NetworkConfig(host="localhost", port=8080))
    handler.setFormatter(CsvLikeFormatter())
    assert handler._is_csv_formatter is True
    assert handler._needs_special_handling is True

    handler.setFormatter(JsonLikeFormatter())
    assert handler._is_json_formatter is True
    assert handler._needs_special_handling is True

    handler.setFormatter(StreamingFormatter())
    assert handler._is_streaming_formatter is True
    assert handler._needs_special_handling is True

    handler.setFormatter(None)
    assert handler._is_csv_formatter is False
    assert handler._is_json_formatter is False
    assert handler._is_streaming_formatter is False
    assert handler._needs_special_handling is False


def test_http_handler_emit_and_close_with_mock_session(monkeypatch) -> None:
    class _Response:
        def raise_for_status(self) -> None:
            return None

    class _Session:
        def __init__(self) -> None:
            self.auth = None
            self.closed = False
            self.request_payload = None

        def get(self, *_args, **_kwargs):
            return _Response()

        def request(self, **kwargs):
            self.request_payload = kwargs
            return _Response()

        def close(self):
            self.closed = True

    monkeypatch.setattr(network_module, "REQUESTS_AVAILABLE", True)
    monkeypatch.setattr(network_module.requests, "Session", _Session)
    handler = HTTPHandler("https://example.com/logs", headers={"X-Test": "1"})
    record = LogRecord(level=20, level_name="INFO", message="payload")
    handler.emit(record)
    stats = handler.get_network_stats()
    assert stats["stats"]["sent"] == 1
    assert stats["stats"]["bytes_sent"] > 0
    handler.close()


def test_http_handler_emit_network_error_updates_retry_stats(monkeypatch) -> None:
    class _Response:
        def raise_for_status(self) -> None:
            return None

    class _Session:
        def get(self, *_args, **_kwargs):
            return _Response()

        def request(self, **_kwargs):
            raise RuntimeError("request fail")

        def close(self):
            return None

    monkeypatch.setattr(network_module, "REQUESTS_AVAILABLE", True)
    monkeypatch.setattr(network_module.requests, "Session", _Session)
    monkeypatch.setattr(network_module.time, "sleep", lambda _s: None)
    handler = HTTPHandler("http://example.com/logs")
    handler.emit(LogRecord(level=20, level_name="INFO", message="boom"))
    assert handler.get_network_stats()["stats"]["failed"] >= 1


def test_http_handler_connection_fails_when_requests_missing(monkeypatch) -> None:
    monkeypatch.setattr(network_module, "REQUESTS_AVAILABLE", False)
    handler = HTTPHandler("http://example.com/logs")
    assert handler._connect() is False
    assert handler.get_network_stats()["stats"]["connection_errors"] >= 1


def test_network_factory_convenience_builders(monkeypatch) -> None:
    monkeypatch.setattr(SocketHandler, "_establish_connection", lambda self: True)
    monkeypatch.setattr(DatagramHandler, "_establish_connection", lambda self: True)
    monkeypatch.setattr(
        network_module.WebSocketHandler, "_establish_connection", lambda self: True
    )
    monkeypatch.setattr(HTTPHandler, "_establish_connection", lambda self: True)

    assert isinstance(
        NetworkHandlerFactory.create_http_handler("http://example.com"), HTTPHandler
    )
    assert isinstance(
        NetworkHandlerFactory.create_websocket_handler("ws://example.com"),
        network_module.WebSocketHandler,
    )
    assert isinstance(
        NetworkHandlerFactory.create_socket_handler("localhost", 9999), SocketHandler
    )
    assert isinstance(
        NetworkHandlerFactory.create_datagram_handler("localhost", 9999),
        DatagramHandler,
    )


def test_websocket_handler_connection_worker_emit_and_close(monkeypatch) -> None:
    monkeypatch.setattr(network_module, "WEBSOCKETS_AVAILABLE", True)
    handler = network_module.WebSocketHandler("ws://example.com/ws")
    assert handler._establish_connection() is True

    async def _run() -> None:
        class StreamingFormatter:
            def format(self, _record):
                return "msg"

        handler.setFormatter(StreamingFormatter())
        handler.emit(LogRecord(level=20, level_name="INFO", message="ws"))
        assert handler.get_network_stats()["stats"]["sent"] >= 1

        # Cover worker loop normal exit.
        handler._connected = True

        async def _stop_sleep(_seconds):
            handler._connected = False

        monkeypatch.setattr(asyncio, "sleep", _stop_sleep)
        await handler._connection_worker()

    import asyncio

    asyncio.run(_run())

    class DummyWs:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    ws = DummyWs()
    handler._websocket = ws
    handler._close_connection()
    assert ws.closed is True


def test_websocket_handler_error_paths(monkeypatch, caplog) -> None:
    monkeypatch.setattr(network_module, "WEBSOCKETS_AVAILABLE", False)
    handler = network_module.WebSocketHandler("ws://example.com/ws")
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.network_handler"):
        assert handler._connect() is False
    assert handler.get_network_stats()["stats"]["connection_errors"] >= 1

    # Emit failure path should increment failed counter via retry handler.
    handler._connect = lambda: True  # type: ignore[method-assign]

    class BrokenFormatter:
        def format(self, _record):
            raise RuntimeError("ws format fail")

    handler.setFormatter(BrokenFormatter())
    handler.emit(LogRecord(level=20, level_name="INFO", message="x"))
    assert handler.get_network_stats()["stats"]["failed"] >= 1


def test_socket_handler_tcp_udp_and_error_paths(monkeypatch, caplog) -> None:
    class DummySocket:
        def __init__(self) -> None:
            self.connected = False
            self.sent = []
            self.closed = False

        def settimeout(self, _timeout: float) -> None:
            return None

        def connect(self, _addr) -> None:
            self.connected = True

        def send(self, data: bytes) -> None:
            self.sent.append(("send", data))

        def sendto(self, data: bytes, addr) -> None:
            self.sent.append(("sendto", data, addr))

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(network_module.socket, "socket", lambda *_a, **_k: DummySocket())

    tcp = SocketHandler(host="localhost", port=514, protocol="tcp")
    assert tcp._establish_connection() is True
    tcp.emit(LogRecord(level=20, level_name="INFO", message="tcp"))
    assert tcp.get_network_stats()["stats"]["sent"] >= 1
    conn = tcp._connection
    tcp._close_connection()
    assert conn.closed is True

    udp = SocketHandler(host="localhost", port=514, protocol="udp")
    assert udp._establish_connection() is True
    udp.emit(LogRecord(level=20, level_name="INFO", message="udp"))
    assert udp.get_network_stats()["stats"]["sent"] >= 1

    # Establish connection failure path.
    monkeypatch.setattr(
        network_module.socket,
        "socket",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("sock fail")),
    )
    failing = SocketHandler(host="localhost", port=514, protocol="tcp")
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.network_handler"):
        assert failing._establish_connection() is False


def test_datagram_handler_connection_and_emit_error_paths(monkeypatch, caplog) -> None:
    class DummyConn:
        def __init__(self) -> None:
            self.timeout = None
            self.sent = []
            self.closed = False

        def settimeout(self, timeout: float) -> None:
            self.timeout = timeout

        def sendto(self, data: bytes, addr) -> None:
            self.sent.append((data, addr))

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(network_module.socket, "socket", lambda *_a, **_k: DummyConn())
    handler = DatagramHandler(host="localhost", port=9999, max_packet_size=64)
    assert handler._establish_connection() is True
    handler.emit(LogRecord(level=20, level_name="INFO", message="packet"))
    assert handler.get_network_stats()["stats"]["sent"] >= 1
    conn = handler._connection
    handler._close_connection()
    assert conn.closed is True

    # Emit error path
    handler2 = DatagramHandler(host="localhost", port=9999, max_packet_size=64)
    handler2._connected = True
    handler2._connection = DummyConn()
    monkeypatch.setattr(handler2._connection, "sendto", lambda *_a, **_k: (_ for _ in ()).throw(OSError("send fail")))
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.network_handler"):
        handler2.emit(LogRecord(level=20, level_name="INFO", message="boom"))
    assert handler2.get_network_stats()["stats"]["failed"] >= 1
