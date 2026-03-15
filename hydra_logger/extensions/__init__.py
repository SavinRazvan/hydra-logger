"""
Role: Init implementation.
Used By:
 - (update when known)
Depends On:
 - extension_base
 - extension_manager
Notes:
 - Header standardized by slim-header migration.
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
