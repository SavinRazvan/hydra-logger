"""
Role: Implements hydra_logger.handlers.network_handler functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - asyncio
 - dataclasses
 - enum
 - hydra_logger
 - importlib
 - requests
 - socket
 - ssl
 - ...
Notes:
 - Implements log destination handling and I/O flow for network handler.
"""

# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
# pyright: reportCallIssue=false, reportArgumentType=false

import asyncio
import logging
import socket
import ssl
import time
import warnings
from dataclasses import dataclass, field
from enum import Enum
from importlib.util import find_spec
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from ..types.levels import LogLevel
from ..types.records import LogRecord
from ..utils import slo_metrics
from .base_handler import BaseHandler

_logger = logging.getLogger(__name__)

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

WEBSOCKETS_AVAILABLE = find_spec("websockets") is not None

# NetworkUtils removed - simplified network handler


class NetworkProtocol(Enum):
    """Network protocols supported."""

    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"
    TCP = "tcp"
    UDP = "udp"


class RetryPolicy(Enum):
    """Retry policies for network operations."""

    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


@dataclass
class NetworkConfig:
    """Configuration for network handlers."""

    # Connection settings
    host: str = "localhost"
    port: int = 80
    protocol: NetworkProtocol = NetworkProtocol.HTTP
    timeout: float = 30.0
    max_retries: int = 3

    # Authentication
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    token: Optional[str] = None

    # HTTP specific
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None

    # WebSocket specific
    ws_path: str = "/ws"
    ws_subprotocols: List[str] = field(default_factory=list)

    # Socket specific
    buffer_size: int = 8192
    keep_alive: bool = True

    # Retry and fallback
    retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL
    retry_delay: float = 1.0
    max_retry_delay: float = 60.0

    # Batch settings
    batch_size: int = 100
    batch_timeout: float = 5.0

    # HTTP connectivity probe (separate from emit `method`, which defaults to POST)
    connection_probe: bool = True
    probe_method: str = "GET"

    # Security
    use_ssl: bool = False
    ssl_context: Optional[ssl.SSLContext] = None


class BaseNetworkHandler(BaseHandler):
    """Base class for network-based handlers."""

    def __init__(self, config: NetworkConfig, **kwargs):
        """
        Initialize base network handler.

        Args:
            config: Network configuration
            **kwargs: Additional arguments
        """
        super().__init__(name="network", level=LogLevel.NOTSET)
        self._config = config
        self._connection: Optional[socket.socket] = None
        self._connected = False
        self._retry_count = 0
        self._last_retry = 0.0
        self._stats = {
            "sent": 0,
            "failed": 0,
            "retries": 0,
            "reconnect_attempts": 0,
            "retry_backoff_events": 0,
            "bytes_sent": 0,
            "connection_errors": 0,
        }

        # Formatter-aware handling
        self._is_csv_formatter = False
        self._is_json_formatter = False
        self._is_streaming_formatter = False
        self._needs_special_handling = False

        # Initialize connection
        self._connect()

    def setFormatter(self, formatter):
        """
        Set formatter and detect if it needs special handling.

        Args:
            formatter: Formatter instance
        """
        super().setFormatter(formatter)

        # Detect formatter type for optimal handling
        if formatter:
            self._is_csv_formatter = hasattr(formatter, "format_headers") and hasattr(
                formatter, "should_write_headers"
            )
            self._is_json_formatter = hasattr(formatter, "write_header")
            self._is_streaming_formatter = hasattr(formatter, "format_for_streaming")

            # Determine if special handling is needed
            self._needs_special_handling = (
                self._is_csv_formatter
                or self._is_json_formatter
                or self._is_streaming_formatter
            )
        else:
            # Reset flags if no formatter
            self._is_csv_formatter = False
            self._is_json_formatter = False
            self._is_streaming_formatter = False
            self._needs_special_handling = False

    def _validate_network_config(self) -> None:
        """Validate network configuration."""
        if not self._is_valid_hostname(self._config.host):
            raise ValueError(f"Invalid hostname: {self._config.host}")

        if not self._is_valid_port(self._config.port):
            raise ValueError(f"Invalid port: {self._config.port}")

        if self._config.timeout <= 0:
            raise ValueError("Timeout must be positive")

        if self._config.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

    def _is_valid_hostname(self, hostname: str) -> bool:
        """Simple hostname validation."""
        if not hostname or len(hostname) > 253:
            return False
        # Basic validation - allow localhost, IP addresses, and domain names
        return True

    def _is_valid_port(self, port: int) -> bool:
        """Simple port validation."""
        return isinstance(port, int) and 1 <= port <= 65535

    def _connect(self) -> bool:
        """Establish network connection."""
        try:
            if self._connected and self._connection:
                return True

            self._establish_connection()
            return self._connected
        except Exception:
            _logger.exception(
                "Network connect failed for %s:%s (%s)",
                self._config.host,
                self._config.port,
                self._config.protocol.value,
            )
            self._stats["connection_errors"] += 1
            return False

    def _establish_connection(self) -> bool:
        """Establish the actual connection."""
        raise NotImplementedError("Subclasses must implement this method")

    def _disconnect(self) -> None:
        """Disconnect from network."""
        try:
            if self._connection:
                self._close_connection()
                self._connection = None
            self._connected = False
        except Exception:
            _logger.exception("Network disconnect failed")

    def _close_connection(self) -> None:
        """Close the connection."""
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def _safe_url_for_logs(raw_url: str) -> str:
        """Return sanitized URL for diagnostics without credentials/query values."""
        try:
            parsed = urlparse(raw_url)
            scheme = parsed.scheme or "unknown"
            host = parsed.hostname or "unknown-host"
            path = parsed.path or ""
            return f"{scheme}://{host}{path}"
        except Exception:
            return "[invalid-url]"

    def _should_retry(self, error: Exception) -> bool:
        """Check if operation should be retried."""
        if self._retry_count >= self._config.max_retries:
            return False

        # Don't retry on certain errors
        if isinstance(error, (ValueError, TypeError)):
            return False

        # Check retry delay
        current_time = time.time()
        if current_time - self._last_retry < self._get_retry_delay():
            return False

        return True

    def _get_retry_delay(self) -> float:
        """Get retry delay based on policy."""
        if self._retry_count == 0:
            return 0

        if self._config.retry_policy == RetryPolicy.LINEAR:
            delay = self._config.retry_delay * self._retry_count
        elif self._config.retry_policy == RetryPolicy.EXPONENTIAL:
            delay = self._config.retry_delay * (2 ** (self._retry_count - 1))
        elif self._config.retry_policy == RetryPolicy.FIBONACCI:
            delay = self._config.retry_delay * self._fibonacci(self._retry_count)
        else:
            delay = self._config.retry_delay

        return min(delay, self._config.max_retry_delay)

    def _fibonacci(self, n: int) -> int:
        """Calculate Fibonacci number."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    def _handle_network_error(self, error: Exception) -> None:
        """Handle network errors with retry logic."""
        self._stats["failed"] += 1
        slo_metrics.record_handler_error(self.__class__.__name__)

        if self._should_retry(error):
            self._retry_count += 1
            self._last_retry = time.time()
            self._stats["retries"] += 1

            # Reconnect without blocking the caller path.
            retry_delay = self._get_retry_delay()
            if retry_delay > 0:
                self._stats["retry_backoff_events"] += 1
            self._disconnect()
            self._stats["reconnect_attempts"] += 1
            self._connect()
        else:
            # Give up after max retries
            self._disconnect()

    def get_network_stats(self) -> Dict[str, Any]:
        """
        Get network statistics.

        Returns:
            Dictionary with network statistics
        """
        return {
            "connected": self._connected,
            "retry_count": self._retry_count,
            "last_retry": self._last_retry,
            "stats": self._stats.copy(),
            "config": {
                "host": self._config.host,
                "port": self._config.port,
                "protocol": self._config.protocol.value,
                "timeout": self._config.timeout,
                "max_retries": self._config.max_retries,
            },
        }

    def close(self) -> None:
        """Close the handler."""
        self._disconnect()
        super().close()


class HTTPHandler(BaseNetworkHandler):
    """HTTP-based network handler."""

    def __init__(
        self,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[tuple] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        connection_probe: bool = True,
        probe_method: str = "GET",
        **kwargs,
    ):
        """
        Initialize HTTP handler.

        Args:
            url: Target URL
            method: HTTP method
            headers: HTTP headers
            auth: Authentication tuple
            timeout: Request timeout
            verify_ssl: Whether to verify SSL
            connection_probe: When True, verify connectivity with `probe_method` before use
            probe_method: Probe verb: GET, HEAD, OPTIONS, or none (skip probe)
            **kwargs: Additional arguments
        """
        parsed_url = urlparse(url)
        config = NetworkConfig(
            host=parsed_url.hostname or "localhost",
            port=parsed_url.port or (443 if parsed_url.scheme == "https" else 80),
            protocol=(
                NetworkProtocol.HTTPS
                if parsed_url.scheme == "https"
                else NetworkProtocol.HTTP
            ),
            timeout=timeout,
            method=method,
            headers=headers or {},
            verify_ssl=verify_ssl,
            connection_probe=connection_probe,
            probe_method=probe_method,
        )

        self._url = url
        self._auth = auth
        self._session: Any = None  # requests.Session when connected
        super().__init__(config, **kwargs)

    def _establish_connection(self) -> bool:
        """Establish HTTP connection."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library is required for HTTP handler")

        try:
            session = requests.Session()
            self._session = session
            if self._auth:
                session.auth = self._auth

            if not self._config.connection_probe:
                self._connected = True
                return True

            probe = (self._config.probe_method or "GET").upper()
            if probe == "NONE":
                self._connected = True
                return True

            probe_kwargs: Dict[str, Any] = {
                "timeout": self._config.timeout,
                "verify": self._config.verify_ssl,
            }
            if probe == "GET":
                response = session.get(self._url, **probe_kwargs)
            elif probe == "HEAD":
                response = session.head(self._url, **probe_kwargs)
            elif probe == "OPTIONS":
                response = session.options(self._url, **probe_kwargs)
            else:
                raise ValueError(
                    f"Unsupported HTTP probe_method {self._config.probe_method!r}; "
                    "expected GET, HEAD, OPTIONS, or none"
                )
            response.raise_for_status()
            self._connected = True
            return True
        except Exception:
            _logger.exception(
                "HTTP connection establishment failed for url=%s",
                self._safe_url_for_logs(self._url),
            )
            self._connected = False
            return False

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record via HTTP.

        Args:
            record: Log record to emit
        """
        if not self._connect():
            return

        session = self._session
        if session is None:
            return

        try:
            # Enhanced formatter handling
            if self.formatter:
                # Check if this is a streaming formatter that needs special handling
                if hasattr(self.formatter, "format_for_streaming"):
                    message = self.formatter.format_for_streaming(record)
                else:
                    message = self.formatter.format(record)
            else:
                message = f"{record.level_name}: {record.message}"

            # Prepare data with enhanced record information
            data = {
                "message": message,
                "level": record.level_name,
                "timestamp": self.format_timestamp(record),
                "layer": record.layer,
                "filename": record.filename,
                "function_name": record.function_name,
                "line_number": record.line_number,
                "thread_id": record.thread_id,
                "process_id": record.process_id,
                "agent_id": record.agent_id,
                "user_id": record.user_id,
                "request_id": record.request_id,
                "correlation_id": record.correlation_id,
                "environment": record.environment,
                "event_id": record.event_id,
                "device_id": record.device_id,
            }

            response = session.request(
                method=self._config.method,
                url=self._url,
                json=data,
                headers=self._config.headers,
                timeout=self._config.timeout,
                verify=self._config.verify_ssl,
            )
            response.raise_for_status()
            self._stats["sent"] += 1
            self._stats["bytes_sent"] += len(str(data).encode("utf-8"))
        except Exception as error:
            _logger.exception(
                "HTTP emit failed for url=%s", self._safe_url_for_logs(self._url)
            )
            self._handle_network_error(error)

    def _close_connection(self) -> None:
        """Close HTTP connection."""
        if self._session:
            self._session.close()
            self._session = None


class WebSocketHandler(BaseNetworkHandler):
    """WebSocket-based network handler."""

    _simulation_notice_issued: bool = False

    def __init__(
        self,
        url: str,
        path: str = "/ws",
        subprotocols: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Initialize WebSocket handler.

        Args:
            url: WebSocket URL
            path: WebSocket path
            subprotocols: WebSocket subprotocols
            **kwargs: Additional arguments
        """
        parsed_url = urlparse(url)
        config = NetworkConfig(
            host=parsed_url.hostname or "localhost",
            port=parsed_url.port or (443 if parsed_url.scheme == "wss" else 80),
            protocol=(
                NetworkProtocol.WSS
                if parsed_url.scheme == "wss"
                else NetworkProtocol.WS
            ),
            ws_path=path,
            ws_subprotocols=subprotocols or [],
        )

        super().__init__(config, **kwargs)
        self._url = url
        self._websocket = None
        self._ws_transport_simulated = True
        self._websockets_installed = WEBSOCKETS_AVAILABLE

    def _establish_connection(self) -> bool:
        """Establish WebSocket connection (simulated transport today)."""
        try:
            # Real `websockets` client integration may be added later; emit path is
            # intentionally non-network for backward compatibility.
            self._connected = True
            self._ws_transport_simulated = True
            return True
        except Exception:
            _logger.exception(
                "WebSocket connection establishment failed for url=%s",
                self._safe_url_for_logs(self._url),
            )
            self._connected = False
            return False

    def _warn_simulated_transport_once(self) -> None:
        if not self._ws_transport_simulated:
            return
        if WebSocketHandler._simulation_notice_issued:
            return
        warnings.warn(
            "WebSocketHandler uses a simulated transport; log records are not sent "
            "over the network. Install and configure a real client when available.",
            UserWarning,
            stacklevel=2,
        )
        WebSocketHandler._simulation_notice_issued = True

    async def _connection_worker(self) -> None:
        """Background connection worker."""
        while self._connected:
            try:
                await asyncio.sleep(1)
            except Exception:
                _logger.exception("WebSocket background worker failed")
                break

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record via WebSocket.

        Args:
            record: Log record to emit
        """
        if not self._connect():
            return

        try:
            self._warn_simulated_transport_once()
            if self.formatter:
                message = self.formatter.format(record)
            else:
                message = f"{record.level_name}: {record.message}"

            data = {"message": message, "level": record.level_name}
            if record.layer:
                data["layer"] = record.layer

            # In a real implementation, this would send via WebSocket
            # For now, we'll just simulate success
            self._stats["sent"] += 1
        except Exception as error:
            _logger.exception(
                "WebSocket emit failed for url=%s", self._safe_url_for_logs(self._url)
            )
            self._handle_network_error(error)

    def _close_connection(self) -> None:
        """Close WebSocket connection."""
        if self._websocket:
            self._websocket.close()
            self._websocket = None


class SocketHandler(BaseNetworkHandler):
    """Socket-based network handler."""

    def __init__(
        self, host: str = "localhost", port: int = 514, protocol: str = "tcp", **kwargs
    ):
        """
        Initialize socket handler.

        Args:
            host: Target host
            port: Target port
            protocol: Protocol (tcp/udp)
            **kwargs: Additional arguments
        """
        config = NetworkConfig(
            host=host,
            port=port,
            protocol=NetworkProtocol.TCP if protocol == "tcp" else NetworkProtocol.UDP,
        )

        super().__init__(config, **kwargs)
        self._protocol = protocol

    def _establish_connection(self) -> bool:
        """Establish socket connection."""
        try:
            if self._protocol == "tcp":
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._connection.settimeout(self._config.timeout)
                self._connection.connect((self._config.host, self._config.port))
            else:
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self._connected = True
            return True
        except Exception:
            _logger.exception(
                "Socket connection establishment failed for %s:%s",
                self._config.host,
                self._config.port,
            )
            self._connected = False
            return False

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record via socket.

        Args:
            record: Log record to emit
        """
        if not self._connect():
            return

        conn = self._connection
        if conn is None:
            return

        try:
            if self.formatter:
                message = self.formatter.format(record)
            else:
                message = f"{record.level_name}: {record.message}"

            data = message.encode("utf-8")
            if self._protocol == "tcp":
                conn.send(data)
            else:
                conn.sendto(data, (self._config.host, self._config.port))

            self._stats["sent"] += 1
        except Exception as error:
            _logger.exception(
                "Socket emit failed for %s:%s", self._config.host, self._config.port
            )
            self._handle_network_error(error)

    def _close_connection(self) -> None:
        """Close socket connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


class DatagramHandler(BaseNetworkHandler):
    """Datagram-based network handler."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 514,
        max_packet_size: int = 1024,
        **kwargs,
    ):
        """
        Initialize datagram handler.

        Args:
            host: Target host
            port: Target port
            max_packet_size: Packet size limit
            **kwargs: Additional arguments
        """
        config = NetworkConfig(host=host, port=port, protocol=NetworkProtocol.UDP)

        super().__init__(config, **kwargs)
        self._max_packet_size = max_packet_size

    def _establish_connection(self) -> bool:
        """Establish datagram connection."""
        try:
            self._connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._connection.settimeout(self._config.timeout)
            self._connected = True
            return True
        except Exception:
            _logger.exception(
                "Datagram connection establishment failed for %s:%s",
                self._config.host,
                self._config.port,
            )
            self._connected = False
            return False

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record via datagram.

        Args:
            record: Log record to emit
        """
        if not self._connect():
            return

        conn = self._connection
        if conn is None:
            return

        try:
            if self.formatter:
                message = self.formatter.format(record)
            else:
                message = f"{record.level_name}: {record.message}"

            # Truncate message if too long
            if len(message) > self._max_packet_size:
                message = message[: self._max_packet_size - 3] + "..."

            data = message.encode("utf-8")
            conn.sendto(data, (self._config.host, self._config.port))
            self._stats["sent"] += 1
        except Exception as error:
            _logger.exception(
                "Datagram emit failed for %s:%s", self._config.host, self._config.port
            )
            self._handle_network_error(error)

    def _close_connection(self) -> None:
        """Close datagram connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


class NetworkHandlerFactory:
    """Factory for creating network handlers."""

    @staticmethod
    def create_handler(handler_type: str, **kwargs) -> BaseNetworkHandler:
        """
        Create a network handler by type.

        Args:
            handler_type: Type of handler to create
            **kwargs: Handler-specific arguments

        Returns:
            Configured network handler
        """
        if handler_type.lower() == "http":
            return HTTPHandler(**kwargs)
        elif handler_type.lower() == "websocket":
            return WebSocketHandler(**kwargs)
        elif handler_type.lower() == "socket":
            return SocketHandler(**kwargs)
        elif handler_type.lower() == "datagram":
            return DatagramHandler(**kwargs)
        else:
            raise ValueError(f"Unknown handler type: {handler_type}")

    @staticmethod
    def create_http_handler(url: str, **kwargs) -> HTTPHandler:
        """Create HTTP handler."""
        return HTTPHandler(url, **kwargs)

    @staticmethod
    def create_websocket_handler(url: str, **kwargs) -> WebSocketHandler:
        """Create WebSocket handler."""
        return WebSocketHandler(url, **kwargs)

    @staticmethod
    def create_socket_handler(host: str, port: int, **kwargs) -> SocketHandler:
        """Create socket handler."""
        return SocketHandler(host, port, **kwargs)

    @staticmethod
    def create_datagram_handler(host: str, port: int, **kwargs) -> DatagramHandler:
        """Create datagram handler."""
        return DatagramHandler(host, port, **kwargs)
