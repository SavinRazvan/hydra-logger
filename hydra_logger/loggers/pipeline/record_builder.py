"""
Role: Build standardized log records for logger runtimes.
Used By:
 - `hydra_logger.loggers.sync_logger`
 - `hydra_logger.loggers.async_logger`
Depends On:
 - hydra_logger
 - typing
Notes:
 - Wraps logger record creation to keep hot-path logic centralized.
"""

from typing import Any, Dict, Union

from ...types.levels import LogLevelManager
from ...types.records import LogRecord


class RecordBuilder:
    """Shared record builder for logger pipeline paths."""

    def __init__(self, logger: Any) -> None:
        self._logger = logger

    def normalize_level(self, level: Union[str, int]) -> int:
        """Normalize level input into numeric representation."""
        if isinstance(level, str):
            return LogLevelManager.get_level(level)
        return int(level)

    def create(
        self, level: Union[str, int], message: str, **kwargs: Dict[str, Any]
    ) -> LogRecord:
        """Create a `LogRecord` using logger's standardized strategy."""
        normalized = self.normalize_level(level)
        return self._logger.create_log_record(normalized, message, **kwargs)
