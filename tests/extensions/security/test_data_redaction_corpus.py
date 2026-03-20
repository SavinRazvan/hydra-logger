"""
Role: Corpus-style tests for regex redaction limits (false negatives/positives).
Used By:
 - Security posture validation; documents non-DLP expectations.
Depends On:
 - hydra_logger.extensions.security.data_redaction
Notes:
 - Built-in patterns are defense-in-depth helpers, not exhaustive DLP.
"""

from __future__ import annotations

from hydra_logger.extensions.security.data_redaction import DataRedaction


def test_false_negative_obfuscated_email_not_redacted() -> None:
    """Human-obfuscated addresses often bypass simple email regex."""
    redaction = DataRedaction(enabled=True, patterns=["email"])
    text = "reach me at user [at] example [dot] com"
    assert redaction.redact(text) == text


def test_false_positive_digit_sequence_matches_phone_pattern() -> None:
    """Ten grouped digits can match the phone regex outside telephony context."""
    redaction = DataRedaction(enabled=True, patterns=["phone"])
    text = "order id 123-456-7890 confirmed"
    out = redaction.redact(text)
    assert "[REDACTED_PHONE]" in out
    assert "123-456-7890" not in out


def test_credit_card_pattern_redacts_common_groups() -> None:
    redaction = DataRedaction(enabled=True, patterns=["credit_card"])
    text = "pan 4111 1111 1111 1111 end"
    out = redaction.redact(text)
    assert "4111" not in out
    assert "[REDACTED_CARD]" in out


def test_openai_style_api_key_redacted_when_enabled() -> None:
    redaction = DataRedaction(enabled=True, patterns=["api_key"])
    text = "key sk-abcdefghijklmnopqrstuvwx"
    out = redaction.redact(text)
    assert "sk-abc" not in out
    assert "[REDACTED_API_KEY]" in out
