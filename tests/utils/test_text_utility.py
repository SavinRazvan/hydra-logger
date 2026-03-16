"""
Role: Pytest coverage for text utility behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates processing, formatting, validation, sanitization, and analysis helpers.
"""

from hydra_logger.utils.text_utility import (
    TextAnalyzer,
    TextCase,
    TextFormatter,
    TextProcessor,
    TextSanitizer,
    TextValidator,
)


def test_text_processor_normalization_extraction_and_pattern_helpers() -> None:
    processor = TextProcessor()
    assert processor.remove_accents("cafe deja vu") == "cafe deja vu"
    assert processor.clean_whitespace(" a\t b \r\n\r\n c ") == "a b \n\n c"
    assert processor.extract_words("One two three", min_length=3) == ["one", "two", "three"]
    assert processor.count_occurrences("aaa", "a") == 3
    assert processor.extract_emails("user@example.com") == ["user@example.com"]
    assert processor.extract_ips("host 127.0.0.1") == ["127.0.0.1"]


def test_text_formatter_case_padding_wrap_and_template() -> None:
    assert TextFormatter.change_case("hello world", TextCase.UPPER) == "HELLO WORLD"
    assert TextFormatter.change_case("hello_world", TextCase.CAMEL) == "helloWorld"
    assert TextFormatter.change_case("helloWorld", TextCase.SNAKE) == "hello_world"
    assert TextFormatter.truncate("abcdef", 4) == "a..."
    assert TextFormatter.pad("x", 3, char="0", align="right") == "00x"
    assert TextFormatter.wrap("one two three", 6) == ["one", "two", "three"]
    assert TextFormatter.format_template("hi {name}", name="bob") == "hi bob"


def test_text_validator_rules_and_custom_validator() -> None:
    validator = TextValidator()
    assert validator.validate("user@example.com", "email")
    assert validator.validate("+1 (555) 123-4567", "phone")
    assert validator.validate("127.0.0.1", "ip_address")
    assert validator.validate("Abcdef1!", "strong_password")
    validator.add_custom_validator("starts_with_a", lambda text: text.startswith("a"))
    assert validator.validate("apple", "starts_with_a")


def test_text_sanitizer_redact_mask_hash_and_exclude() -> None:
    sanitizer = TextSanitizer()
    text = "email user@example.com phone 123-456-7890"
    redacted = sanitizer.sanitize(text, strategy="redact", replacement="[X]")
    assert "[X]" in redacted
    masked = sanitizer.sanitize("token=abcdef1234567890", strategy="mask")
    assert "*" in masked
    hashed = sanitizer.sanitize("password=Secret123!", strategy="hash")
    assert hashed != "password=Secret123!"
    unchanged = sanitizer.sanitize(text, strategy="redact", exclude=["email", "phone"])
    assert unchanged == text


def test_text_analyzer_metrics_summary_and_language_detection() -> None:
    analyzer = TextAnalyzer()
    text = "The quick brown fox jumps. And the dog waits.\n\nAnother paragraph."
    metrics = analyzer.analyze_text(text)
    assert metrics.word_count > 0
    assert metrics.sentence_count >= 2
    assert metrics.to_dict()["character_count"] == len(text)
    summary = analyzer.get_text_summary(text, max_words=5)
    assert len(summary.split()) <= 5
    assert analyzer.detect_language("the and in on with") == "en"
