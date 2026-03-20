"""
Role: Batched HTTP log delivery using NDJSON bodies for dict payloads.
Used By:
 - Sync and async loggers when LogDestination.http_batch_size is set.
Depends On:
 - hydra_logger.handlers.network_handler.HTTPHandler
Notes:
 - Flushes on batch size or flush interval; mixed str/bytes payloads fall back to single posts.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Union, cast

from ..types.records import LogRecord
from .network_handler import HTTPHandler

_logger = logging.getLogger(__name__)

_Payload = Union[Dict[str, Any], str, bytes]


class BatchedHTTPHandler(HTTPHandler):
    """HTTPHandler that buffers records and sends NDJSON batches (dict payloads)."""

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
        payload_encoder: Optional[Any] = None,
        *,
        batch_size: int = 25,
        flush_interval: float = 1.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            url,
            method=method,
            headers=headers,
            auth=auth,
            timeout=timeout,
            verify_ssl=verify_ssl,
            connection_probe=connection_probe,
            probe_method=probe_method,
            payload_encoder=payload_encoder,
            **kwargs,
        )
        self._batch_size = max(1, int(batch_size))
        self._flush_interval = max(0.0, float(flush_interval))
        self._buf: List[_Payload] = []
        self._lock = threading.Lock()
        self._last_flush = time.monotonic()

    def emit(self, record: LogRecord) -> None:
        if not self._connect():
            return
        if self._session is None:
            return

        try:
            payload = self._compose_payload(record)
            now = time.monotonic()
            to_send: Optional[List[_Payload]] = None
            with self._lock:
                self._buf.append(payload)
                due = self._flush_interval > 0 and (
                    now - self._last_flush >= self._flush_interval
                )
                if len(self._buf) >= self._batch_size or due:
                    to_send = self._buf
                    self._buf = []
                    self._last_flush = now
            if to_send:
                self._flush_batch(to_send)
        except Exception as error:
            _logger.exception(
                "Batched HTTP emit failed for url=%s",
                self._safe_url_for_logs(self._url),
            )
            self._handle_network_error(error)

    def _flush_batch(self, batch: List[_Payload]) -> None:
        if not batch:
            return
        if not self._connect():
            return
        session = self._session
        if session is None:
            return
        try:
            if all(isinstance(p, dict) for p in batch):
                lines = [
                    json.dumps(cast(Dict[str, Any], p), ensure_ascii=False)
                    for p in batch
                ]
                body = "\n".join(lines).encode("utf-8")
                hdrs = dict(self._config.headers)
                if not any(k.lower() == "content-type" for k in hdrs):
                    hdrs["Content-Type"] = "application/x-ndjson"
                response = session.request(
                    method=self._config.method,
                    url=self._url,
                    data=body,
                    headers=hdrs,
                    timeout=self._config.timeout,
                    verify=self._config.verify_ssl,
                )
                response.raise_for_status()
                self._stats["sent"] += len(batch)
                self._stats["bytes_sent"] += len(body)
            else:
                for item in batch:
                    self._emit_single_payload(item)
        except Exception as error:
            _logger.exception(
                "Batched HTTP flush failed for url=%s",
                self._safe_url_for_logs(self._url),
            )
            self._handle_network_error(error)

    def close(self) -> None:
        with self._lock:
            pending = self._buf
            self._buf = []
        if pending:
            self._flush_batch(pending)
        super().close()
