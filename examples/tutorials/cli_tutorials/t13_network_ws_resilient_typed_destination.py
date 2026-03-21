#!/usr/bin/env python3
"""
Role: Enterprise tutorial for resilient typed WebSocket destination onboarding.
Used By:
 - Engineers following `examples/tutorials/README.md` network tracks.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates retry-aware WebSocket destination configuration via deterministic stubs.
 - Adds console + file sinks for visible Hydra output; stub JSON records synthetic WS payloads.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

from hydra_logger import LogDestination, LogLayer, LoggingConfig, create_logger
from hydra_logger.handlers.network_handler import NetworkHandlerFactory

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


class _StubWsHandler:
    sent: int = 0
    emitted_events: list[dict[str, Any]] = []

    def setFormatter(self, _formatter: Any) -> None:  # noqa: N802
        return None

    def setLevel(self, _level: int) -> None:  # noqa: N802
        return None

    def emit(self, _record: Any) -> None:
        self.sent += 1
        _StubWsHandler.emitted_events.append(
            {
                "level": getattr(_record, "level_name", "UNKNOWN"),
                "message": getattr(_record, "message", ""),
                "layer": getattr(_record, "layer", "unknown"),
            }
        )

    def close(self) -> None:
        return None


def _install_ws_stub() -> Callable[[], None]:
    original_ws = NetworkHandlerFactory.create_websocket_handler
    NetworkHandlerFactory.create_websocket_handler = staticmethod(
        lambda **_kwargs: _StubWsHandler()
    )

    def _restore() -> None:
        NetworkHandlerFactory.create_websocket_handler = original_ws

    return _restore


def main() -> None:
    restore = _install_ws_stub()
    try:
        _StubWsHandler.emitted_events = []
        config = LoggingConfig(
            base_log_dir="examples/logs",
            log_dir_name="cli-tutorials",
            layers={
                "stream": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="plain-text",
                            use_colors=False,
                        ),
                        LogDestination(
                            type="file",
                            path="t13_network_ws_layer",
                            format="json-lines",
                        ),
                        LogDestination(
                            type="network_ws",
                            url="wss://stream.example.com/events",
                            timeout=10.0,
                            retry_count=5,
                            retry_delay=1.0,
                        ),
                    ],
                )
            }
        )

        with create_logger(config, logger_type="sync") as logger:
            logger.info("[T13] WebSocket destination initialized", layer="stream")
            logger.error(
                "[T13] WebSocket resilient retry path simulation", layer="stream"
            )

        if len(_StubWsHandler.emitted_events) < 2:
            raise RuntimeError("Expected at least 2 WebSocket stub events for T13")

        output_dir = Path("examples/logs/cli-tutorials")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "t13_network_ws_stub_results.json"
        payload = {
            "tutorial": "t13_network_ws_resilient_typed_destination",
            "stub_sent_count": len(_StubWsHandler.emitted_events),
            "events": _StubWsHandler.emitted_events,
        }
        output_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

        print_cli_tutorial_footer(
            code="T13",
            title="Resilient WebSocket destination (stub transport)",
            console=(
                "Hydra console + JSONL above; WebSocket traffic uses a stub (no real socket). "
                "Stub capture is also saved as JSON below."
            ),
            artifacts=[
                "examples/logs/cli-tutorials/t13_network_ws_layer.jsonl",
                output_file,
            ],
            extra_lines=[f"captured events: {len(_StubWsHandler.emitted_events)}"],
            takeaway="Retry knobs live on the destination; this script proves the wiring with a stub.",
            notebook_rel="examples/tutorials/notebooks/t13_network_ws_resilient_typed_destination.ipynb",
        )
    finally:
        restore()


if __name__ == "__main__":
    main()
