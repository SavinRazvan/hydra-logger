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

from ...types.records import LogRecord


class ExtensionProcessor:
    """Apply enabled extension processors to log records."""

    def apply_data_protection(self, record: LogRecord, data_protection) -> LogRecord:
        """Apply data-protection extension to record message when enabled."""
        if data_protection and data_protection.is_enabled():
            try:
                record.message = data_protection.process(record.message)
            except Exception:
                pass
        return record
