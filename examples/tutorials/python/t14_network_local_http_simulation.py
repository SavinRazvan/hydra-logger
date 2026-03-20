#!/usr/bin/env python3
"""
Role: Enterprise tutorial for local HTTP route simulation of network logging.
Used By:
 - Engineers validating typed `network_http` behavior with deterministic local routes.
Depends On:
 - hydra_logger
 - http.server
 - threading
Notes:
 - Starts an in-process local HTTP server to simulate `/ingest` route behavior.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

from hydra_logger import LogDestination, LogLayer, LoggingConfig, create_logger


class _IngestHandler(BaseHTTPRequestHandler):
    """Simple route simulation for deterministic network logger validation."""

    payloads: list[dict[str, Any]] = []

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
            if isinstance(payload, dict):
                _IngestHandler.payloads.append(payload)
        except Exception:
            pass
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"accepted":true}')

    def log_message(self, _format: str, *_args: Any) -> None:
        # Keep tutorial output clean and deterministic.
        return None


def main() -> None:
    server = HTTPServer(("127.0.0.1", 0), _IngestHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port

    try:
        config = LoggingConfig(
            layers={
                "http": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="network_http",
                            url=f"http://127.0.0.1:{port}/ingest",
                            timeout=2.0,
                            retry_count=2,
                            retry_delay=0.2,
                        )
                    ],
                )
            }
        )

        with create_logger(config, logger_type="sync") as logger:
            logger.info("[T14] local route simulation started", layer="http")
            logger.warning("[T14] local route simulation warning", layer="http")
            logger.error("[T14] local route simulation error", layer="http")

        if not _IngestHandler.payloads:
            raise RuntimeError("No payloads received by local ingest simulation route")

        output_dir = Path("examples/logs/tutorials")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "t14_network_ingest_payloads.json"
        output_file.write_text(
            json.dumps(_IngestHandler.payloads, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

        print("T14 completed: local HTTP route simulation")
        print(f" - route: http://127.0.0.1:{port}/ingest")
        print(f" - captured payloads: {len(_IngestHandler.payloads)}")
        print(f" - artifact: {output_file}")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
