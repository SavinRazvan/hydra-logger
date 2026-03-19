"""
Role: Internal diagnostics observer for runtime operational messages.
Used By:
 - hydra_logger runtime modules replacing ad-hoc `print` calls.
Depends On:
 - logging
Notes:
 - Provides a centralized, low-overhead diagnostics channel.
"""

import logging
from typing import Any

_logger = logging.getLogger("hydra_logger.internal")
_logger.addHandler(logging.NullHandler())


def debug(message: str, *args: Any) -> None:
    """Emit an internal debug diagnostic."""
    _logger.debug(message, *args)


def info(message: str, *args: Any) -> None:
    """Emit an internal info diagnostic."""
    _logger.info(message, *args)


def warning(message: str, *args: Any) -> None:
    """Emit an internal warning diagnostic."""
    _logger.warning(message, *args)


def error(message: str, *args: Any) -> None:
    """Emit an internal error diagnostic."""
    _logger.error(message, *args)
