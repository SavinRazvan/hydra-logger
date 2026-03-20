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
from ...extensions.extension_base import SecurityExtension
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

    def apply_non_data_protection_extensions(
        self,
        record: LogRecord,
        extension_manager: Optional[Any],
        data_protection_extension: Optional[Any],
    ) -> LogRecord:
        """Apply enabled non-security extensions in configured manager order."""
        if extension_manager is None:
            return record

        processing_order = extension_manager.get_processing_order()
        for extension_name in processing_order:
            extension = extension_manager.get_extension(extension_name)
            if extension is None or not extension.is_enabled():
                continue
            if extension is data_protection_extension:
                continue
            if isinstance(extension, SecurityExtension):
                continue
            try:
                record.message = extension.process(record.message)
                if record.context:
                    record.context = extension.process(record.context)
                if record.extra:
                    record.extra = extension.process(record.extra)
            except Exception as error:
                if self._owner is not None and hasattr(
                    self._owner, "_handle_internal_failure"
                ):
                    try:
                        self._owner._handle_internal_failure(
                            f"extension_{extension_name}", error
                        )
                    except HydraLoggerError:
                        raise
                else:
                    _logger.exception(
                        "Extension processing failed for extension=%s type=%s",
                        extension_name,
                        type(extension).__name__,
                    )
        return record
