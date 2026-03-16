"""
Role: Emit log records through sync and async handlers.
Used By:
 - `hydra_logger.loggers.sync_logger`
 - `hydra_logger.loggers.async_logger`
Depends On:
 - asyncio
 - hydra_logger
 - typing
Notes:
 - Centralizes resilient handler dispatch logic.
"""

import asyncio
import logging
from typing import Any, Iterable

from ...types.records import LogRecord


_logger = logging.getLogger(__name__)


class HandlerDispatcher:
    """Shared handler dispatch for logger runtimes."""

    def dispatch_sync(self, record: LogRecord, handlers: Iterable[Any]) -> None:
        """Dispatch record through synchronous handler path."""
        for handler in handlers:
            try:
                if hasattr(handler, "handle"):
                    handler.handle(record)
                elif hasattr(handler, "emit"):
                    handler.emit(record)
            except Exception:
                _logger.exception(
                    "Sync handler dispatch failed for handler type=%s",
                    type(handler).__name__,
                )

    async def dispatch_async(self, record: LogRecord, handlers: Iterable[Any]) -> None:
        """Dispatch record through async-aware handler path."""
        for handler in handlers:
            try:
                if hasattr(handler, "emit_async") and asyncio.iscoroutinefunction(
                    handler.emit_async
                ):
                    await handler.emit_async(record)
                elif hasattr(handler, "handle"):
                    handler.handle(record)
                elif hasattr(handler, "emit"):
                    emit = handler.emit
                    if asyncio.iscoroutinefunction(emit):
                        await emit(record)
                    else:
                        emit(record)
            except Exception:
                _logger.exception(
                    "Async handler dispatch failed for handler type=%s",
                    type(handler).__name__,
                )
