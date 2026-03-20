"""
Role: Black-box HTTP handler test against a local threaded HTTPServer.
Used By:
 - pytest for hydra_logger.handlers.network_handler HTTP path.
Depends On:
 - hydra_logger
 - pytest
Notes:
 - Validates default JSON POST body reaches the wire without external services.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from hydra_logger.handlers.network_handler import HTTPHandler
from hydra_logger.types.records import LogRecord


def test_http_handler_emit_posts_json_to_local_server() -> None:
    collected: dict[str, bytes] = {}

    class _ReqHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            collected["body"] = self.rfile.read(length)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *_args, **_kwargs) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), _ReqHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        handler = HTTPHandler(
            f"http://{host}:{port}/ingest",
            connection_probe=False,
        )
        handler.emit(LogRecord(level=20, level_name="INFO", message="hello-ingest"))
        assert "body" in collected
        payload = json.loads(collected["body"].decode("utf-8"))
        assert "message" in payload
        assert "hello-ingest" in payload["message"]
    finally:
        server.shutdown()
        thread.join(timeout=5)
