"""
Role: Shared validation helpers for config model consumers.
Used By:
 - `hydra_logger.config`
Depends On:
 - hydra_logger
Notes:
 - Provides common validation constants to avoid duplicated level checks.
"""

VALID_LOG_LEVELS = ("NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def normalize_level(level: str) -> str:
    """Normalize and validate a log level name."""
    normalized = str(level).upper()
    if normalized not in VALID_LOG_LEVELS:
        raise ValueError(f"Invalid level: {level}. Must be one of {list(VALID_LOG_LEVELS)}")
    return normalized
