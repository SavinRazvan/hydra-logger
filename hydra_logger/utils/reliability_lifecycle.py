"""
Role: Policy-governed handling for logger lifecycle failures (close, flush).
Used By:
 - SyncLogger, AsyncLogger, CompositeLogger close and cleanup paths.
Depends On:
 - hydra_logger.core.exceptions
 - hydra_logger.utils.internal_diagnostics
Notes:
 - Surfaces errors via internal diagnostics; honors strict_reliability_mode and
   reliability_error_policy without swallowing exceptions silently when raise is set.
"""

from __future__ import annotations

from typing import Callable

from ..core.exceptions import HydraLoggerError
from . import internal_diagnostics as diagnostics


def handle_lifecycle_failure(
    *,
    context: str,
    error: Exception,
    logger_name: str,
    strict_reliability_mode: bool,
    reliability_error_policy: str,
    failure_warning_interval: int,
    increment_close_failures: Callable[[], None],
    get_close_failure_count: Callable[[], int],
    set_last_error: Callable[[str], None],
) -> None:
    """
    Record a lifecycle failure and apply reliability policy.

    Always emits an internal diagnostics error line for operator visibility.
    Increments the caller's close-failure counter before policy checks.
    """
    increment_close_failures()
    count = get_close_failure_count()
    detail = f"Logger {logger_name!r} lifecycle failure [{context}]: {error}"
    set_last_error(detail)
    diagnostics.error("%s", detail)
    policy = (reliability_error_policy or "silent").lower()
    if strict_reliability_mode or policy == "raise":
        raise HydraLoggerError(f"Logger lifecycle failure [{context}]") from error
    if policy == "warn" and (
        count == 1 or count % max(1, int(failure_warning_interval)) == 0
    ):
        diagnostics.warning("%s", detail)
