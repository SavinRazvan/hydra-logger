"""
Role: Init implementation.
Used By:
 - (update when known)
Depends On:
 - logger_factory
Notes:
 - Header standardized by slim-header migration.
"""

from .logger_factory import (
    create_async_logger,
    create_composite_async_logger,
    create_composite_logger,
    create_custom_logger,
    create_default_logger,
    create_development_logger,
    create_logger,
    create_production_logger,
    create_sync_logger,
)

__all__ = [
    # Factory functions
    "create_logger",
    "create_sync_logger",
    "create_async_logger",
    "create_composite_logger",
    "create_composite_async_logger",
    # Magic configuration functions
    "create_default_logger",
    "create_development_logger",
    "create_production_logger",
    "create_custom_logger",
]
