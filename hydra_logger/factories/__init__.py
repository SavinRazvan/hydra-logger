"""
Role: Public exports for hydra_logger.factories; no runtime logic besides import wiring.
Used By:
 - Importers of `hydra_logger.factories` public API.
Depends On:
 - hydra_logger
Notes:
 - Re-exports the hydra_logger.factories public API with stable import paths.
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
