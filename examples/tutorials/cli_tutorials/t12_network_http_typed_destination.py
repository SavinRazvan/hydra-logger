#!/usr/bin/env python3
"""
Role: Enterprise tutorial for typed HTTP network destination onboarding.
Used By:
 - Engineers following `examples/tutorials/README.md` network tracks.
Depends On:
 - hydra_logger
Notes:
 - Uses local handler stubs to keep runtime deterministic and CI-safe.
 - Adds console + file sinks so output matches other tutorials; stub JSON records synthetic HTTP payloads.
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


class _StubHttpHandler:
    sent: int = 0
    emitted_events: list[dict[str, Any]] = []

    def setFormatter(self, _formatter: Any) -> None:  # noqa: N802
        return None

    def setLevel(self, _level: int) -> None:  # noqa: N802
        return None

    def emit(self, _record: Any) -> None:
        self.sent += 1
        _StubHttpHandler.emitted_events.append(
            {
                "level": getattr(_record, "level_name", "UNKNOWN"),
                "message": getattr(_record, "message", ""),
                "layer": getattr(_record, "layer", "unknown"),
            }
        )

    def close(self) -> None:
        return None


def _install_http_stub() -> Callable[[], None]:
    original_http = NetworkHandlerFactory.create_http_handler
    NetworkHandlerFactory.create_http_handler = staticmethod(
        lambda **_kwargs: _StubHttpHandler()
    )

    def _restore() -> None:
        NetworkHandlerFactory.create_http_handler = original_http

    return _restore


def main() -> None:
    restore = _install_http_stub()
    try:
        _StubHttpHandler.emitted_events = []
        config = LoggingConfig(
            base_log_dir="examples/logs",
            log_dir_name="cli-tutorials",
            layers={
                "http": LogLayer(
                    level="INFO",
                    destinations=[
                        # Mirror to console + file like other tutorials (network sink is silent).
                        LogDestination(
                            type="console",
                            format="plain-text",
                            use_colors=False,
                        ),
                        LogDestination(
                            type="file",
                            path="t12_network_http_layer",
                            format="json-lines",
                        ),
                        LogDestination(
                            type="network_http",
                            url="https://logs.example.com/ingest",
                            timeout=5.0,
                            retry_count=3,
                            retry_delay=0.5,
                            credentials={"X-API-Key": "demo-key"},
                        ),
                    ],
                )
            }
        )

        with create_logger(config, logger_type="sync") as logger:
            logger.info("[T12] HTTP destination initialized", layer="http")
            logger.warning("[T12] HTTP destination warning event", layer="http")

        if len(_StubHttpHandler.emitted_events) < 2:
            raise RuntimeError("Expected at least 2 HTTP stub events for T12")

        output_dir = Path("examples/logs/cli-tutorials")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "t12_network_http_stub_results.json"
        payload = {
            "tutorial": "t12_network_http_typed_destination",
            "stub_sent_count": len(_StubHttpHandler.emitted_events),
            "events": _StubHttpHandler.emitted_events,
        }
        output_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

        print_cli_tutorial_footer(
            code="T12",
            title="Typed HTTP network destination (stub transport)",
            console=(
                "Hydra console + JSONL above; HTTP traffic goes to a stub (no real network). "
                "Stub capture is also saved as JSON below."
            ),
            artifacts=[
                "examples/logs/cli-tutorials/t12_network_http_layer.jsonl",
                output_file,
            ],
            extra_lines=[
                f"captured events: {len(_StubHttpHandler.emitted_events)}",
            ],
            takeaway="network_http destinations batch through the factory; inspect the JSON artifact for payloads.",
            notebook_rel="examples/tutorials/notebooks/t12_network_http_typed_destination.ipynb",
        )
    finally:
        restore()


if __name__ == "__main__":
    main()
