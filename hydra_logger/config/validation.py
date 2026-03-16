"""
Role: Shared validation helpers for config model consumers.
Used By:
 - `hydra_logger.config`
Depends On:
 - hydra_logger
Notes:
 - Provides common validation constants to avoid duplicated level checks.
"""

import logging


_logger = logging.getLogger(__name__)


VALID_LOG_LEVELS = ("NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def normalize_level(level: str) -> str:
    """Normalize and validate a log level name."""
    try:
        normalized = str(level).upper()
    except Exception:
        _logger.exception("Failed to normalize log level value: %r", level)
        raise
    if normalized not in VALID_LOG_LEVELS:
        _logger.error("Invalid log level received: %r", level)
        raise ValueError(f"Invalid level: {level}. Must be one of {list(VALID_LOG_LEVELS)}")
    return normalized
