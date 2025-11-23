"""
Base Extension Class for Hydra Logger Extensions.

This module provides the abstract base class that all extensions must implement.
Extensions follow a plug-in/plug-out design with zero overhead when disabled.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ExtensionConfig:
    """Base configuration for extensions."""

    enabled: bool = False
    name: str = ""
    version: str = "0.4.0"
    description: str = ""


class Extension(ABC):
    """
    Abstract base class for all Hydra Logger extensions.

    Extensions follow a plug-in/plug-out design:
    - Default disabled for zero overhead
    - Dynamic loading via configuration
    - Sensible defaults when enabled
    - Clear enable/disable semantics
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the extension with configuration.

        Args:
            config: Extension-specific configuration dictionary
        """
        self.config = config or {}
        self._enabled = self.config.get("enabled", False)
        self._name = self.config.get("name", self.__class__.__name__)
        self._version = self.config.get("version", "0.4.0")
        self._description = self.config.get("description", "")

        # Initialize extension-specific configuration
        self._initialize_config()

    def _initialize_config(self) -> None:
        """Initialize extension-specific configuration. Override in subclasses."""
        pass

    @abstractmethod
    def enable(self) -> None:
        """Enable the extension. Override in subclasses."""
        self._enabled = True

    @abstractmethod
    def disable(self) -> None:
        """Disable the extension. Override in subclasses."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if the extension is enabled."""
        return self._enabled

    def get_name(self) -> str:
        """Get the extension name."""
        return self._name

    def get_version(self) -> str:
        """Get the extension version."""
        return self._version

    def get_description(self) -> str:
        """Get the extension description."""
        return self._description

    def validate_config(self) -> None:
        """
        Validate the extension configuration.
        Override in subclasses to add specific validation.
        """
        if not isinstance(self.config, dict):
            raise ValueError(
                f"Extension config must be a dictionary, got {type(self.config)}"
            )

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the extension configuration."""
        self.config.update(new_config)
        self._initialize_config()

    def __str__(self) -> str:
        """String representation of the extension."""
        status = "enabled" if self._enabled else "disabled"
        return f"{self._name} v{self._version} ({status})"

    def __repr__(self) -> str:
        """Detailed string representation of the extension."""
        return (
            f"{self.__class__.__name__}(name='{self._name}', enabled={self._enabled})"
        )
