"""
Role: Fan-out dispatch helper for composite logger components.
Used By:
 - `hydra_logger.loggers.composite_logger`
Depends On:
 - asyncio
 - typing
Notes:
 - Provides resilient fan-out for sync and async component loggers.
"""

import asyncio
import logging
from typing import Any, Iterable

_logger = logging.getLogger(__name__)


class ComponentDispatcher:
    """Dispatch log calls across component logger lists."""

    def dispatch_sync(
        self, components: Iterable[Any], level: Any, message: str, **kwargs
    ) -> None:
        """Fan-out synchronous log call to component loggers."""
        for component in components:
            try:
                if hasattr(component, "log"):
                    component.log(level, message, **kwargs)
            except Exception:
                _logger.exception(
                    "Sync component dispatch failed for component type=%s",
                    type(component).__name__,
                )

    async def dispatch_async(
        self, components: Iterable[Any], level: Any, message: str, **kwargs
    ) -> None:
        """Fan-out async-aware log call to component loggers."""
        for component in components:
            try:
                if hasattr(component, "log") and asyncio.iscoroutinefunction(
                    component.log
                ):
                    await component.log(level, message, **kwargs)
                elif hasattr(component, "log"):
                    component.log(level, message, **kwargs)
            except Exception:
                _logger.exception(
                    "Async component dispatch failed for component type=%s",
                    type(component).__name__,
                )
