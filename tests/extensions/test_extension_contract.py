"""
Role: Pytest coverage for unified extension contract compatibility.
Used By:
 - Pytest discovery and extension API compatibility checks.
Depends On:
 - hydra_logger
Notes:
 - Verifies legacy `Extension` derives from canonical `ExtensionBase`.
"""

from hydra_logger.extensions.base import Extension
from hydra_logger.extensions.extension_base import ExtensionBase


class LegacyCompatibleExtension(Extension):
    def _initialize_config(self) -> None:
        self.mode = self.config.get("mode", "default")


def test_legacy_extension_contract_is_extension_base_compatible() -> None:
    extension = LegacyCompatibleExtension({"enabled": True, "mode": "strict"})
    assert isinstance(extension, ExtensionBase)
    assert extension.is_enabled() is True
    assert extension.mode == "strict"
