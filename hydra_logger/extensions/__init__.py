"""
Role: Public extension package exports.
Used By:
 - hydra_logger/factories/logger_factory.py for extension manager import.
 - examples/04_runtime_control.py for user-facing extension APIs.
Depends On:
 - extension_base
 - extension_manager
Notes:
 - Re-exports extension primitives for stable import paths.
"""

from .extension_base import (
    ExtensionBase,
    FormattingExtension,
    PerformanceExtension,
    SecurityExtension,
)
from .extension_manager import ExtensionManager

# Exports
__all__ = [
    # Base classes
    "ExtensionBase",
    # Extension implementations
    "SecurityExtension",
    "FormattingExtension",
    "PerformanceExtension",
    # Management
    "ExtensionManager",
]
