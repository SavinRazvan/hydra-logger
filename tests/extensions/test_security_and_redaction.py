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


def test_security_extension_default_patterns_include_secret_credentials() -> None:
    ext = SecurityExtension(enabled=True)
    text = "password=abc token=xyz secret=mysecret"
    result = ext.process(text)
    assert 'password="[REDACTED]"' in result
    assert 'token="[REDACTED]"' in result
    assert 'secret="[REDACTED]"' in result


def test_data_redaction_redacts_nested_list_and_tuple_structures() -> None:
    redactor = DataRedaction(enabled=True, patterns=["token"])
    payload = {
        "items": ["token=abc", {"inner": ("ok", "token=xyz")}],
        "plain": "token=top",
    }
    redacted = redactor.redact(payload)
    assert redacted["items"][0] == 'token="[REDACTED]"'
    assert redacted["items"][1]["inner"][1] == 'token="[REDACTED]"'
    assert redacted["plain"] == 'token="[REDACTED]"'


def test_security_extension_processes_nested_container_payloads() -> None:
    ext = SecurityExtension(enabled=True, patterns=["password"])
    payload = {
        "events": [{"message": "password=abc"}],
        "tuple_data": ("keep", {"nested": "password=xyz"}),
    }
    result = ext.process(payload)
    assert result["events"][0]["message"] == 'password="[REDACTED]"'
    assert result["tuple_data"][1]["nested"] == 'password="[REDACTED]"'
