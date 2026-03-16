"""
Role: Pytest coverage for security extension and data redaction behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates redaction/sanitization and nested structure handling.
"""

from hydra_logger.extensions.extension_base import SecurityExtension
from hydra_logger.extensions.security.data_redaction import DataRedaction


def test_security_extension_redacts_sensitive_values_and_scripts() -> None:
    ext = SecurityExtension(enabled=True, patterns=["email", "api_key"])
    text = "contact test@example.com token sk-12345678901234567890 <script>alert(1)</script>"
    result = ext.process(text)
    assert "[REDACTED_EMAIL]" in result
    assert "[REDACTED_API_KEY]" in result
    assert "[SANITIZED_SCRIPT]" in result


def test_data_redaction_handles_nested_dicts_and_disable() -> None:
    redactor = DataRedaction(enabled=True, patterns=["phone"])
    payload = {"user": {"phone": "123-456-7890"}, "note": "ok"}
    redacted = redactor.redact(payload)
    assert redacted["user"]["phone"] == "[REDACTED_PHONE]"
    redactor.disable()
    assert redactor.redact("123-456-7890") == "123-456-7890"


def test_data_redaction_add_custom_pattern() -> None:
    redactor = DataRedaction(enabled=True, patterns=[])
    redactor.add_pattern(r"secret-\d+", "[HIDDEN]")
    assert redactor.redact("value secret-123") == "value [HIDDEN]"
