#!/usr/bin/env python3
"""
Role: Runnable example for typed network destinations with deterministic stubs.
Used By:
 - Developers validating typed network destination wiring without external services.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates `network_http` and `network_ws` destination types with local stubs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from hydra_logger import LogDestination, LogLayer, LoggingConfig, create_logger
from hydra_logger.handlers.network_handler import NetworkHandlerFactory


@dataclass
class _StubNetworkHandler:
    """Minimal handler used to avoid external network dependencies."""

    name: str
    emitted: int = 0

    def setFormatter(self, _formatter: Any) -> None:  # noqa: N802
        return None

    def setLevel(self, _level: int) -> None:  # noqa: N802
        return None

    def emit(self, _record: Any) -> None:
        self.emitted += 1

    def close(self) -> None:
        return None


def _install_stub_factories() -> Callable[[], None]:
    """Install deterministic network handler stubs and return restore callback."""
    original_http = NetworkHandlerFactory.create_http_handler
    original_ws = NetworkHandlerFactory.create_websocket_handler

    NetworkHandlerFactory.create_http_handler = staticmethod(
        lambda **_kwargs: _StubNetworkHandler(name="http")
    )
    NetworkHandlerFactory.create_websocket_handler = staticmethod(
        lambda **_kwargs: _StubNetworkHandler(name="ws")
    )

    def _restore() -> None:
        NetworkHandlerFactory.create_http_handler = original_http
        NetworkHandlerFactory.create_websocket_handler = original_ws

    return _restore


def main() -> None:
    restore = _install_stub_factories()
    try:
        config = LoggingConfig(
            layers={
                "http": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="network_http",
                            url="https://logs.example.com/ingest",
                            timeout=5.0,
                            retry_count=3,
                            retry_delay=0.5,
                        )
                    ],
                ),
                "stream": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="network_ws",
                            url="wss://stream.example.com/events",
                            timeout=10.0,
                            retry_count=5,
                            retry_delay=1.0,
                        )
                    ],
                ),
            }
        )

        with create_logger(config, logger_type="sync") as logger:
            logger.info("[17] HTTP network destination event", layer="http")
            logger.info("[17] WebSocket network destination event", layer="stream")

        print("17 completed: typed network destination example")
    finally:
        restore()


if __name__ == "__main__":
    main()
