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
from typing import Any, Awaitable, Callable, Iterable

from ...types.records import LogRecord

_logger = logging.getLogger(__name__)


class HandlerDispatcher:
    """Shared handler dispatch for logger runtimes."""

    def __init__(self) -> None:
        # Cache dispatch strategy per handler instance to avoid repeated
        # capability inspection on every emitted record.
        self._sync_dispatch_cache: dict[
            int, tuple[tuple[bool, bool], Callable[[LogRecord], None] | None]
        ] = {}
        self._async_dispatch_cache: dict[
            int,
            tuple[
                tuple[int, int, int],
                Callable[[LogRecord], Awaitable[None] | None],
            ],
        ] = {}

    @staticmethod
    def _callable_token(value: Any) -> int:
        """Build stable token for callables (including bound methods)."""
        if value is None:
            return 0
        func = getattr(value, "__func__", None)
        owner = getattr(value, "__self__", None)
        if func is not None and owner is not None:
            return hash((id(owner), id(func)))
        return id(value)

    def _resolve_sync_dispatch(
        self, handler: Any
    ) -> Callable[[LogRecord], None] | None:
        handler_id = id(handler)
        signature = (hasattr(handler, "handle"), hasattr(handler, "emit"))
        cached = self._sync_dispatch_cache.get(handler_id)
        if cached and cached[0] == signature:
            return cached[1]

        dispatch_fn: Callable[[LogRecord], None] | None = None
        if signature[0]:
            dispatch_fn = handler.handle
        elif signature[1]:
            dispatch_fn = handler.emit

        self._sync_dispatch_cache[handler_id] = (signature, dispatch_fn)
        return dispatch_fn

    def _resolve_async_dispatch(
        self, handler: Any
    ) -> Callable[[LogRecord], Awaitable[None] | None]:
        handler_id = id(handler)
        emit_async = getattr(handler, "emit_async", None)
        handle = getattr(handler, "handle", None)
        emit = getattr(handler, "emit", None)
        signature = (
            self._callable_token(emit_async),
            self._callable_token(handle),
            self._callable_token(emit),
        )
        cached = self._async_dispatch_cache.get(handler_id)
        if cached and cached[0] == signature:
            return cached[1]

        if emit_async is not None and asyncio.iscoroutinefunction(emit_async):

            async def _dispatch(record: LogRecord) -> None:
                await emit_async(record)

        elif handle is not None:

            async def _dispatch(record: LogRecord) -> None:
                handle(record)

        elif emit is not None and asyncio.iscoroutinefunction(emit):

            async def _dispatch(record: LogRecord) -> None:
                await emit(record)

        elif emit is not None:

            async def _dispatch(record: LogRecord) -> None:
                emit(record)

        else:

            async def _dispatch(_record: LogRecord) -> None:
                return None

        self._async_dispatch_cache[handler_id] = (signature, _dispatch)
        return _dispatch

    def dispatch_sync(self, record: LogRecord, handlers: Iterable[Any]) -> None:
        """Dispatch record through synchronous handler path."""
        for handler in handlers:
            try:
                dispatch_fn = self._resolve_sync_dispatch(handler)
                if dispatch_fn is not None:
                    dispatch_fn(record)
            except Exception:
                _logger.exception(
                    "Sync handler dispatch failed for handler type=%s",
                    type(handler).__name__,
                )

    async def dispatch_async(self, record: LogRecord, handlers: Iterable[Any]) -> None:
        """Dispatch record through async-aware handler path."""
        for handler in handlers:
            try:
                dispatch_fn = self._resolve_async_dispatch(handler)
                await dispatch_fn(record)
            except Exception:
                _logger.exception(
                    "Async handler dispatch failed for handler type=%s",
                    type(handler).__name__,
                )
