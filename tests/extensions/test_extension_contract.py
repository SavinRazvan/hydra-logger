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


def test_extension_base_contract_accessors_and_validation_paths() -> None:
    extension = LegacyCompatibleExtension({"enabled": False, "name": "legacy", "version": "1.2.3"})
    assert extension.process({"k": "v"}) == {"k": "v"}
    assert extension.get_name() == "legacy"
    assert extension.get_version() == "1.2.3"
    assert extension.get_description() == ""
    assert extension.get_config()["name"] == "legacy"

    extension.enable()
    assert extension.is_enabled() is True
    extension.disable()
    assert extension.is_enabled() is False

    extension.update_config({"description": "desc", "enabled": True})
    assert extension.get_config()["description"] == "desc"
    assert extension.is_enabled() is False
    assert "legacy v1.2.3" in str(extension)
    assert "LegacyCompatibleExtension" in repr(extension)

    # Cover base class no-op initializer hook.
    Extension._initialize_config(extension)

    extension.config = "invalid"  # type: ignore[assignment]
    try:
        Extension.validate_config(extension)
    except ValueError as exc:
        assert "must be a dictionary" in str(exc)
    else:
        raise AssertionError("Expected validate_config to reject non-dict config")

    bare = LegacyCompatibleExtension()
    bare._initialize_config()
    assert bare.mode == "default"
    bare.disable()
    assert "(disabled)" in str(bare)
