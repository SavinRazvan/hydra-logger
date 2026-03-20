"""
Role: Apply optional extension processing in logger pipeline.
Used By:
 - `hydra_logger.loggers.sync_logger`
 - `hydra_logger.loggers.async_logger`
Depends On:
 - hydra_logger
Notes:
 - Keeps extension handling isolated from logger orchestration flow.
"""

import logging
from typing import Any, Optional

from ...core.exceptions import HydraLoggerError
from ...types.records import LogRecord

_logger = logging.getLogger(__name__)


class ExtensionProcessor:
    """Apply enabled extension processors to log records."""

    def __init__(self, owner: Optional[Any] = None) -> None:
        """Optional logger owner for reliability policy on extension failures."""
        self._owner = owner

    def apply_data_protection(self, record: LogRecord, data_protection) -> LogRecord:
        """Apply data-protection extension to record message when enabled."""
        if data_protection and data_protection.is_enabled():
            try:
                record.message = data_protection.process(record.message)
                if record.context:
                    record.context = data_protection.process(record.context)
                if record.extra:
                    record.extra = data_protection.process(record.extra)
            except Exception as error:
                if self._owner is not None and hasattr(
                    self._owner, "_handle_internal_failure"
                ):
                    try:
                        self._owner._handle_internal_failure(
                            "extension_data_protection", error
                        )
                    except HydraLoggerError:
                        raise
                else:
                    _logger.exception(
                        "Data protection extension failed for type=%s",
                        type(data_protection).__name__,
                    )
        return record
