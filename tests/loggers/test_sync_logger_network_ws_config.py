"""
Role: Tests that network_ws LogDestination maps WebSocket transport flags to handlers.
Used By:
 - pytest for sync logger network wiring.
Depends On:
 - hydra_logger
 - pytest
Notes:
 - Does not open real sockets; only inspects handler configuration. Uses
   _create_network_handler_from_destination so tests stay isolated from
   NetworkHandlerFactory monkeypatches elsewhere in the suite.
"""

from __future__ import annotations

from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer
from hydra_logger.loggers.sync_logger import SyncLogger


def test_sync_logger_network_ws_uses_real_transport_from_destination() -> None:
    logger = SyncLogger(
        config=LoggingConfig(
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[LogDestination(type="console")],
                )
            }
        )
    )
    handler = logger._create_network_handler_from_destination(
        LogDestination(
            type="network_ws",
            url="wss://example.invalid/stream",
            use_real_websocket_transport=True,
        )
    )
    assert getattr(handler, "_use_real_websocket_transport", False) is True
