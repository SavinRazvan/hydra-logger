from typing import Optional

"""
Role: Init implementation.
Used By:
 - (update when known)
Depends On:
 - base
 - sync_logger
 - async_logger
 - composite_logger
 - types
Notes:
 - Header standardized by slim-header migration.
"""

# Standardized record creation
from ..types.records import (
    AUTO_CONTEXT_STRATEGY,
    CONTEXT_STRATEGY,
    MINIMAL_STRATEGY,
    RecordCreationStrategy,
    create_log_record,
    get_record_creation_strategy,
)
from .async_logger import AsyncLogger
from .base import BaseLogger, PerformanceProfiles
from .composite_logger import CompositeAsyncLogger, CompositeLogger
from .sync_logger import SyncLogger

# No factory imports to avoid circular imports


# Convenience function for Python logging style
def getLogger(name: Optional[str] = None):
    """Get a logger instance (Python logging style)."""
    # Import here to avoid circular imports
    from ..factories.logger_factory import create_logger

    return create_logger(name=name)


# Public API
__all__ = [
    # Base classes
    "BaseLogger",
    "PerformanceProfiles",
    # Logger implementations
    "SyncLogger",
    "AsyncLogger",
    "CompositeLogger",
    "CompositeAsyncLogger",
    # Standardized record creation
    "RecordCreationStrategy",
    "get_record_creation_strategy",
    "create_log_record",
    "MINIMAL_STRATEGY",
    "CONTEXT_STRATEGY",
    "AUTO_CONTEXT_STRATEGY",
    # Factory functions (imported separately to avoid circular imports)
    # Python logging style
    "getLogger",
]

# Version info
__version__ = "0.4.0"
__author__ = "Savin Ionut Razvan"
