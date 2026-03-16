"""
Role: Public exports for hydra_logger.extensions; no runtime logic besides import wiring.
Used By:
 - Importers of `hydra_logger.extensions` public API.
Depends On:
 - hydra_logger
Notes:
 - Re-exports the hydra_logger.extensions public API with stable import paths.
"""

from .extension_base import (
    ExtensionBase,
    FormattingExtension,
    PerformanceExtension,
    SecurityExtension,
)
from .base import Extension, ExtensionConfig
from .extension_manager import ExtensionManager

# Exports
__all__ = [
    # Base classes
    "ExtensionBase",
    "Extension",
    "ExtensionConfig",
    # Extension implementations
    "SecurityExtension",
    "FormattingExtension",
    "PerformanceExtension",
    # Management
    "ExtensionManager",
]
