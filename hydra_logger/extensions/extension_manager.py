"""
Extension Manager for Hydra-Logger

Extension management system with user control.
Users can enable/disable, configure, and manage all extensions dynamically.

ARCHITECTURE:
- ExtensionManager: Central management for all extensions
- Dynamic loading and configuration
- Zero overhead when extensions are disabled
- User-controllable via LoggingConfig

NAMING CONVENTIONS:
- ExtensionManager: Clear, descriptive management class
- Descriptive naming
- Consistent with project standards
"""

from typing import Any, Dict, List, Optional, Type
from .extension_base import (
    ExtensionBase,
    SecurityExtension,
    FormattingExtension,
    PerformanceExtension,
)


class ExtensionManager:
    """
    Extension manager with user control.

    Users can:
    - Enable/disable any extension
    - Configure extension parameters
    - Add custom extensions
    - Control extension processing order
    - Monitor extension performance
    """

    def __init__(self):
        """Initialize extension manager."""
        self.extensions: Dict[str, ExtensionBase] = {}
        self._available_types = {
            "security": SecurityExtension,
            "formatting": FormattingExtension,
            "performance": PerformanceExtension,
        }
        self._processing_order: List[str] = []

    def register_extension_type(
        self, name: str, extension_class: Type[ExtensionBase]
    ) -> None:
        """Register a new extension type."""
        self._available_types[name] = extension_class

    def create_extension(
        self, name: str, extension_type: str, enabled: bool = False, **config
    ) -> ExtensionBase:
        """
        Create extension by type with user configuration.

        Args:
            name: Extension name
            extension_type: Type of extension to create
            enabled: Whether extension is enabled
            **config: User configuration for extension

        Returns:
            Created extension instance
        """
        if extension_type not in self._available_types:
            raise ValueError(f"Unknown extension type: {extension_type}")

        extension_class = self._available_types[extension_type]
        extension = extension_class(enabled=enabled, **config)
        self.extensions[name] = extension

        # Add to processing order if enabled
        if enabled and name not in self._processing_order:
            self._processing_order.append(name)

        return extension

    def add_extension(self, name: str, extension: ExtensionBase) -> None:
        """Add existing extension directly."""
        self.extensions[name] = extension
        if extension.is_enabled() and name not in self._processing_order:
            self._processing_order.append(name)

    def get_extension(self, name: str) -> Optional[ExtensionBase]:
        """Get extension by name."""
        return self.extensions.get(name)

    def enable_extension(self, name: str) -> None:
        """Enable extension."""
        extension = self.get_extension(name)
        if extension:
            extension.enable()
            if name not in self._processing_order:
                self._processing_order.append(name)

    def disable_extension(self, name: str) -> None:
        """Disable extension."""
        extension = self.get_extension(name)
        if extension:
            extension.disable()
            if name in self._processing_order:
                self._processing_order.remove(name)

    def configure_extension(self, name: str, **config) -> None:
        """Configure extension with user settings."""
        extension = self.get_extension(name)
        if extension:
            extension.update_config(**config)

    def process_data(self, data: Any) -> Any:
        """
        Process data through all enabled extensions in order.

        Args:
            data: Data to process

        Returns:
            Processed data
        """
        if not self.extensions or not self._processing_order:
            return data

        result = data
        for extension_name in self._processing_order:
            extension = self.extensions.get(extension_name)
            if extension and extension.is_enabled():
                try:
                    result = extension.process(result)
                except Exception:
                    # If extension fails, continue with current data
                    continue

        return result

    def set_processing_order(self, order: List[str]) -> None:
        """Set processing order for extensions."""
        # Validate all names exist
        for name in order:
            if name not in self.extensions:
                raise ValueError(f"Extension '{name}' not found")

        self._processing_order = order

    def get_processing_order(self) -> List[str]:
        """Get current processing order."""
        return self._processing_order.copy()

    def list_enabled_extensions(self) -> List[str]:
        """List enabled extensions."""
        return [name for name, ext in self.extensions.items() if ext.is_enabled()]

    def list_all_extensions(self) -> List[str]:
        """List all extensions."""
        return list(self.extensions.keys())

    def get_extension_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all extensions."""
        status = {}
        for name, extension in self.extensions.items():
            status[name] = {
                "enabled": extension.is_enabled(),
                "type": extension.__class__.__name__,
                "config": extension.get_config(),
            }
        return status

    def clear_extensions(self) -> None:
        """Clear all extensions."""
        self.extensions.clear()
        self._processing_order.clear()

    def remove_extension(self, name: str) -> None:
        """Remove extension."""
        if name in self.extensions:
            del self.extensions[name]
        if name in self._processing_order:
            self._processing_order.remove(name)

    def get_available_types(self) -> List[str]:
        """Get available extension types."""
        return list(self._available_types.keys())

    def get_extension_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from all extensions."""
        metrics = {}
        for name, extension in self.extensions.items():
            if hasattr(extension, "get_metrics"):
                metrics[name] = extension.get_metrics()
        return metrics
