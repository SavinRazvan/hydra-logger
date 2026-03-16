"""
Role: Pytest coverage for extension base contracts.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates enable/disable lifecycle and config update hooks.
"""

from hydra_logger.extensions.base import Extension, ExtensionConfig


class DummyExtension(Extension):
    def _initialize_config(self) -> None:
        self.init_calls = getattr(self, "init_calls", 0) + 1
        self.mode = self.config.get("mode", "safe")

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False


def test_extension_config_defaults() -> None:
    cfg = ExtensionConfig()
    assert cfg.enabled is False
    assert cfg.version == "0.4.0"


def test_extension_lifecycle_str_repr_and_update_config() -> None:
    extension = DummyExtension({"enabled": True, "name": "Redactor", "mode": "strict"})
    assert extension.is_enabled() is True
    assert extension.get_name() == "Redactor"
    assert extension.mode == "strict"

    extension.disable()
    assert "disabled" in str(extension)
    assert "DummyExtension" in repr(extension)

    extension.update_config({"enabled": False, "mode": "lenient"})
    assert extension.mode == "lenient"
    assert extension.init_calls >= 2
    assert extension.get_config()["mode"] == "lenient"


def test_extension_validate_config_rejects_non_dict() -> None:
    extension = DummyExtension()
    extension.config = "invalid"  # type: ignore[assignment]
    try:
        extension.validate_config()
    except ValueError as exc:
        assert "must be a dictionary" in str(exc)
    else:
        raise AssertionError("Expected ValueError when config is not a dict")
