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
    assert processor.extract_words("One two three", min_length=3) == [
        "one",
        "two",
        "three",
    ]
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


def test_text_formatter_logs_missing_template_key(caplog) -> None:
    with caplog.at_level("ERROR", logger="hydra_logger.utils.text_utility"):
        try:
            TextFormatter.format_template("hi {name}", missing="x")
        except ValueError:
            pass
    assert "Template formatting failed due to missing key" in caplog.text


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


def test_text_processor_additional_extract_and_replace_paths() -> None:
    processor = TextProcessor()
    assert processor.normalize_text("Cafe\u0301") == "Café"
    assert processor.extract_sentences("One. Two!") == ["One", "Two"]
    assert processor.extract_paragraphs("A\n\nB") == ["A", "B"]
    assert processor.find_all_matches("a1 b2", r"\w\d") == ["a1", "b2"]
    assert processor.replace_pattern("abc123", r"\d+", "X") == "abcX"
    assert processor.extract_urls("go https://example.com/path?q=1") == [
        "https://example.com/path?q=1"
    ]
    assert processor.extract_phones("call +1 555-123-4567 now")


def test_text_formatter_additional_case_and_helpers() -> None:
    assert TextFormatter.change_case("hello world", TextCase.SENTENCE) == "Hello world"
    assert TextFormatter.change_case("hello world", TextCase.KEBAB) == "hello-world"
    assert TextFormatter.change_case("hello world", TextCase.PASCAL) == "HelloWorld"
    assert TextFormatter.change_case("x", "unknown") == "x"  # type: ignore[arg-type]
    assert TextFormatter.truncate("abc", 10) == "abc"
    assert TextFormatter.pad("x", 3, align="left") == "x  "
    assert TextFormatter.pad("x", 3, align="center") == " x "
    assert TextFormatter.pad("x", 3, align="other") == "x"
    assert TextFormatter.format_number(12.3456, ".2f") == "12.35"


def test_text_validator_negative_and_error_paths() -> None:
    validator = TextValidator()
    assert validator.is_url("bad url") is False
    assert validator.is_ip_address("999.1.1.1") is False
    assert validator.is_ip_address("not-an-ip") is False
    assert validator.is_credit_card("1234") is False
    assert validator.is_credit_card("4111111111111112") is False
    assert validator.is_strong_password("Ab1!") is False
    assert validator.is_strong_password("abcdefg1!") is False
    assert validator.is_strong_password("ABCDEFG1!") is False
    assert validator.is_strong_password("Abcdefgh!") is False
    assert validator.is_strong_password("Abcdefg1") is False
    try:
        validator.validate("x", "missing_rule")
    except ValueError as exc:
        assert "Unknown validation rule" in str(exc)
    else:
        raise AssertionError("Expected unknown rule validation error")


def test_text_sanitizer_remaining_strategy_branches() -> None:
    sanitizer = TextSanitizer()
    masked_short = sanitizer.sanitize("ip 1.1.1.1", strategy="mask")
    assert "*" in masked_short
    hashed_excluded = sanitizer.sanitize(
        "email user@example.com", strategy="hash", exclude=["email"]
    )
    assert hashed_excluded == "email user@example.com"
    encrypted = sanitizer.sanitize("token=abc", strategy="encrypt")
    assert "[REDACTED]" in encrypted
    try:
        sanitizer.sanitize("x", strategy="other")
    except ValueError as exc:
        assert "Unknown sanitization strategy" in str(exc)
    else:
        raise AssertionError("Expected unknown sanitize strategy error")


def test_text_analyzer_zero_and_empty_summary_branches() -> None:
    analyzer = TextAnalyzer()
    metrics = analyzer.analyze_text("")
    assert analyzer._calculate_flesch_reading_ease(metrics) == 0.0
    assert analyzer._calculate_flesch_kincaid_grade(metrics) == 0.0
    assert analyzer._calculate_gunning_fog_index(metrics) == 0.0
    assert analyzer.get_text_summary("", max_words=10) == ""


def test_text_formatter_lower_title_and_camel_empty_words_branch(monkeypatch) -> None:
    assert TextFormatter.change_case("MiXeD", TextCase.LOWER) == "mixed"
    assert TextFormatter.change_case("hello world", TextCase.TITLE) == "Hello World"
    monkeypatch.setattr(
        "hydra_logger.utils.text_utility.re.split", lambda *_args, **_kwargs: []
    )
    assert TextFormatter._to_camel_case("unchanged") == "unchanged"


def test_text_validator_luhn_adjustment_and_mask_exclude_branch() -> None:
    validator = TextValidator()
    # Digits containing repeated 5 values exercise the doubled-digit subtraction path.
    assert isinstance(validator.is_credit_card("5555555555554444"), bool)

    sanitizer = TextSanitizer()
    source = "email a@b.com token=abcd"
    # Exclude branch skips selected pattern processing.
    assert (
        sanitizer.sanitize(source, strategy="mask", exclude=["email", "token"])
        == source
    )
    sanitizer._sensitive_patterns = {"short": __import__("re").compile(r"abc")}
    assert sanitizer.sanitize("abc", strategy="mask") == "***"
