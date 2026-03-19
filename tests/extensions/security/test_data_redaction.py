"""
Role: Pytest coverage for data redaction utility behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates enable/disable lifecycle and nested dict redaction fallbacks.
"""

from hydra_logger.extensions.security.data_redaction import DataRedaction


def test_data_redaction_enable_disable_and_non_string_dict_values() -> None:
    redaction = DataRedaction(enabled=False, patterns=["email"])
    assert redaction.is_enabled() is False
    assert redaction.redact({"count": 1}) == {"count": 1}

    redaction.enable()
    assert redaction.is_enabled() is True

    nested = {"user": {"email": "a@b.com"}, "count": 42}
    result = redaction.redact(nested)
    assert result["user"]["email"] == "[REDACTED_EMAIL]"
    assert result["count"] == 42
    assert redaction.redact(12345) == 12345

    redaction.disable()
    assert redaction.is_enabled() is False


def test_data_redaction_private_dict_and_depth_guard_paths() -> None:
    redaction = DataRedaction(enabled=True, patterns=["email"])

    redacted = redaction._redact_dict(  # pylint: disable=protected-access
        {"email": "person@example.com", "count": 1}
    )
    assert redacted["email"] == "[REDACTED_EMAIL]"
    assert redacted["count"] == 1

    redaction._max_depth = 0  # pylint: disable=protected-access
    original = {"email": "x@y.com"}
    assert (
        redaction._redact_value(original, depth=1) is original
    )  # pylint: disable=protected-access
