"""
Role: Pytest coverage for extension base contracts.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates enable/disable lifecycle and config update hooks.
"""

import sys
import types

from hydra_logger.extensions.base import Extension, ExtensionConfig
from hydra_logger.extensions.extension_base import (
    ExtensionBase,
    FormattingExtension,
    PerformanceExtension,
    SecurityExtension,
)


class DummyExtension(Extension):
    def _initialize_config(self) -> None:
        self.init_calls = getattr(self, "init_calls", 0) + 1
        self.mode = self.config.get("mode", "safe")

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False


class SetupTrackingExtension(ExtensionBase):
    def __init__(self, enabled: bool = False, **config):
        self.setup_calls = 0
        super().__init__(enabled=enabled, **config)

    def _setup(self) -> None:
        self.setup_calls += 1

    def process(self, data):
        return data


class SuperProcessExtension(ExtensionBase):
    def process(self, data):
        return super().process(data)


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


def test_extension_base_get_config_copy_and_setup_lifecycle() -> None:
    extension = SetupTrackingExtension(enabled=False, mode="safe")
    assert extension.setup_calls == 1

    config_copy = extension.get_config()
    config_copy["mode"] = "mutated"
    assert extension.get_config()["mode"] == "safe"

    extension.update_config(mode="strict")
    assert extension.setup_calls == 1
    assert extension.get_config()["mode"] == "strict"

    extension.enable()
    assert extension.setup_calls == 2
    extension.update_config(flag=True)
    assert extension.setup_calls == 3
    extension.disable()
    assert extension.is_enabled() is False


def test_extension_base_super_process_method_returns_none() -> None:
    extension = SuperProcessExtension(enabled=True)
    assert extension.process("payload") is None


def test_security_extension_process_variants_and_nested_dict() -> None:
    ext = SecurityExtension(enabled=False)
    payload = {"nested": {"phone": "123-456-7890"}, "count": 1}
    assert ext.process(payload) == payload
    assert ext.process(123) == 123

    enabled = SecurityExtension(enabled=True, patterns=["email", "unknown"])
    assert enabled.process(42) == 42
    processed = enabled.process(
        {"nested": {"email": "person@example.com"}, "plain": "ok", "num": 7}
    )
    assert processed["nested"]["email"] == "[REDACTED_EMAIL]"
    assert processed["num"] == 7


def test_security_extension_sanitization_and_redaction_toggles() -> None:
    ext = SecurityExtension(
        enabled=True,
        patterns=["email"],
        redaction_enabled=False,
        sanitization_enabled=True,
    )
    text = "x <script>alert(1)</script> person@example.com"
    result = ext.process(text)
    assert "[SANITIZED_SCRIPT]" in result
    assert "person@example.com" in result

    ext.update_config(sanitization_enabled=False)
    ext.sanitization_enabled = False
    assert ext._process_string("javascript:alert(1)") == "javascript:alert(1)"


def test_formatting_extension_string_and_dict_paths() -> None:
    disabled = FormattingExtension(enabled=False, add_timestamp=True)
    assert disabled.process("hello") == "hello"

    enabled = FormattingExtension(enabled=True, add_timestamp=True)
    formatted = enabled.process("hello")
    assert formatted.startswith("[")
    assert formatted.endswith(" hello")

    dict_ext = FormattingExtension(enabled=True, add_context=True)
    output = dict_ext.process({"message": "hi"})
    assert output["context"]["formatted"] is True
    assert output["context"]["timestamp"] is None
    assert dict_ext.process(9) == 9


def test_performance_extension_sampling_collects_memory_metrics(monkeypatch) -> None:
    class _FakeProcess:
        def memory_info(self):
            return object()

    fake_psutil = types.SimpleNamespace(Process=lambda: _FakeProcess())
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)

    ext = PerformanceExtension(
        enabled=True, sample_rate=1, monitor_latency=True, monitor_memory=True
    )
    payload = {"k": "v"}
    assert ext.process(payload) == payload
    metrics = ext.get_metrics()
    assert metrics["operations_processed"] == 1
    assert metrics["sample_rate"] == 1
    assert metrics["enabled"] is True


def test_performance_extension_disabled_does_not_increment_counter() -> None:
    ext = PerformanceExtension(enabled=False, sample_rate=1)
    assert ext.process("x") == "x"
    assert ext.get_metrics()["operations_processed"] == 0
