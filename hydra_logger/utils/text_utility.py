"""
Text Processing Utilities for Hydra-Logger

This module provides  text processing utilities including
string manipulation, validation, sanitization, analysis, and formatting.
It supports various text operations with performance optimization and
extensive pattern matching capabilities.

FEATURES:
- TextProcessor:  text processing and pattern matching
- StringFormatter: String formatting and case transformation
- TextValidator: Text validation and format checking
- TextSanitizer: Text sanitization and sensitive data protection
- TextAnalyzer: Text analysis and metrics calculation
- Unicode normalization and encoding handling
- Pattern extraction (emails, URLs, phones, IPs)
- Readability analysis and language detection

TEXT PROCESSING:
- Unicode normalization and accent removal
- Whitespace cleaning and normalization
- Word, sentence, and paragraph extraction
- Pattern matching and replacement
- Case transformation (camel, snake, kebab, pascal)
- Text truncation and padding

VALIDATION FEATURES:
- Email, URL, and phone number validation
- IP address and credit card validation
- Password strength checking
- Custom validation rule support
- Format-specific validation

USAGE:
    from hydra_logger.utils import TextProcessor, StringFormatter, TextValidator

    # Text processing
    processor = TextProcessor()
    normalized = processor.normalize_text("Héllo Wörld")
    words = processor.extract_words("Hello world from Hydra-Logger")
    emails = processor.extract_emails("Contact: user@example.com")

    # String formatting
    camel_case = StringFormatter.change_case("hello_world", TextCase.CAMEL)
    truncated = StringFormatter.truncate("Long text", 10, "...")
    wrapped = StringFormatter.wrap("Long text", width=20)

    # Text validation
    validator = TextValidator()
    is_email = validator.is_email("user@example.com")
    is_url = validator.is_url("https://example.com")
    is_strong = validator.is_strong_password("MyStr0ng!Pass")

    # Text analysis
    from hydra_logger.utils import TextAnalyzer
    analyzer = TextAnalyzer()
    metrics = analyzer.analyze_text("Your text here")
    summary = analyzer.get_text_summary("Long text", max_words=50)
"""

import re
import hashlib
import unicodedata
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
from collections import Counter


class TextCase(Enum):
    """Text case transformation options."""

    LOWER = "lower"
    UPPER = "upper"
    TITLE = "title"
    SENTENCE = "sentence"
    CAMEL = "camel"
    SNAKE = "snake"
    KEBAB = "kebab"
    PASCAL = "pascal"


class TextEncoding(Enum):
    """Text encoding options."""

    UTF8 = "utf-8"
    ASCII = "ascii"
    LATIN1 = "latin-1"
    UTF16 = "utf-16"
    UTF32 = "utf-32"


@dataclass
class TextMetrics:
    """Text analysis metrics."""

    # Basic metrics
    character_count: int
    word_count: int
    line_count: int
    sentence_count: int
    paragraph_count: int

    #  metrics
    average_word_length: float
    average_sentence_length: float
    average_paragraph_length: float

    # Character distribution
    character_frequency: Dict[str, int]
    word_frequency: Dict[str, int]

    # Readability scores
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None
    gunning_fog_index: Optional[float] = None

    # Language detection
    detected_language: Optional[str] = None
    language_confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "character_count": self.character_count,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "sentence_count": self.sentence_count,
            "paragraph_count": self.paragraph_count,
            "average_word_length": self.average_word_length,
            "average_sentence_length": self.average_sentence_length,
            "average_paragraph_length": self.average_paragraph_length,
            "character_frequency": self.character_frequency,
            "word_frequency": self.word_frequency,
            "flesch_reading_ease": self.flesch_reading_ease,
            "flesch_kincaid_grade": self.flesch_kincaid_grade,
            "gunning_fog_index": self.gunning_fog_index,
            "detected_language": self.detected_language,
            "language_confidence": self.language_confidence,
        }


class TextProcessor:
    """ text processing utilities."""

    def __init__(self):
        """Initialize text processor."""
        self._cache = {}
        self._patterns = {}
        self._normalizers = {}

        # Common patterns
        self._compile_patterns()

    def normalize_text(self, text: str, form: str = "NFC") -> str:
        """Normalize Unicode text."""
        return unicodedata.normalize(form, text)

    def remove_accents(self, text: str) -> str:
        """Remove diacritical marks from text."""
        return "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if not unicodedata.combining(c)
        )

    def clean_whitespace(self, text: str, normalize_newlines: bool = True) -> str:
        """Clean and normalize whitespace."""
        # Normalize newlines
        if normalize_newlines:
            text = re.sub(r"\r\n|\r", "\n", text)

        # Remove extra whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)

        return text.strip()

    def extract_words(self, text: str, min_length: int = 1) -> List[str]:
        """Extract words from text."""
        words = re.findall(r"\b\w+\b", text.lower())
        return [word for word in words if len(word) >= min_length]

    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting (can be enhanced with NLP libraries)
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text."""
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    def count_occurrences(self, text: str, pattern: str, flags: int = 0) -> int:
        """Count occurrences of a pattern in text."""
        return len(re.findall(pattern, text, flags))

    def find_all_matches(self, text: str, pattern: str, flags: int = 0) -> List[str]:
        """Find all matches of a pattern in text."""
        return re.findall(pattern, text, flags)

    def replace_pattern(
        self, text: str, pattern: str, replacement: str, count: int = 0, flags: int = 0
    ) -> str:
        """Replace pattern matches in text."""
        return re.sub(pattern, replacement, text, count, flags)

    def _compile_patterns(self):
        """Compile common regex patterns."""
        self._patterns = {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "url": re.compile(
                r"https?://(?:[-\w.])+(?:[:\d]+)?"
                r"(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?"
            ),
            "phone": re.compile(
                r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
            ),
            "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
            "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "date": re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
            "time": re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?\b"),
        }

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        return self._patterns["email"].findall(text)

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        return self._patterns["url"].findall(text)

    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        return self._patterns["phone"].findall(text)

    def extract_ips(self, text: str) -> List[str]:
        """Extract IP addresses from text."""
        return self._patterns["ip_address"].findall(text)


class TextFormatter:
    """String formatting and transformation utilities."""

    @staticmethod
    def change_case(text: str, case: TextCase) -> str:
        """Change text case according to specified format."""
        if case == TextCase.LOWER:
            return text.lower()
        elif case == TextCase.UPPER:
            return text.upper()
        elif case == TextCase.TITLE:
            return text.title()
        elif case == TextCase.SENTENCE:
            return text.capitalize()
        elif case == TextCase.CAMEL:
            return TextFormatter._to_camel_case(text)
        elif case == TextCase.SNAKE:
            return TextFormatter._to_snake_case(text)
        elif case == TextCase.KEBAB:
            return TextFormatter._to_kebab_case(text)
        elif case == TextCase.PASCAL:
            return TextFormatter._to_pascal_case(text)
        else:
            return text

    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Convert text to camelCase."""
        words = re.split(r"[_\s-]+", text)
        if not words:
            return text
        return words[0].lower() + "".join(word.capitalize() for word in words[1:])

    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert text to snake_case."""
        text = re.sub(r"([a-z])([A-Z])", r"\1_\2", text)
        text = re.sub(r"[-\s]+", "_", text)
        return text.lower()

    @staticmethod
    def _to_kebab_case(text: str) -> str:
        """Convert text to kebab-case."""
        text = re.sub(r"([a-z])([A-Z])", r"\1-\2", text)
        text = re.sub(r"[_\s]+", "-", text)
        return text.lower()

    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert text to PascalCase."""
        words = re.split(r"[_\s-]+", text)
        return "".join(word.capitalize() for word in words)

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to specified length."""
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def pad(text: str, width: int, char: str = " ", align: str = "left") -> str:
        """Pad text to specified width."""
        if align == "left":
            return text.ljust(width, char)
        elif align == "right":
            return text.rjust(width, char)
        elif align == "center":
            return text.center(width, char)
        else:
            return text

    @staticmethod
    def wrap(text: str, width: int, break_long_words: bool = True) -> List[str]:
        """Wrap text to specified width."""
        import textwrap

        wrapper = textwrap.TextWrapper(
            width=width, break_long_words=break_long_words, break_on_hyphens=False
        )
        return wrapper.wrap(text)

    @staticmethod
    def format_template(template: str, **kwargs) -> str:
        """Format string template with keyword arguments."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

    @staticmethod
    def format_number(number: Union[int, float], format_spec: str = "") -> str:
        """Format number according to specification."""
        return format(number, format_spec)


class TextValidator:
    """Text validation utilities."""

    def __init__(self):
        """Initialize text validator."""
        self._validation_rules = {}
        self._custom_validators = {}

        # Initialize built-in rules
        self._init_validation_rules()

    def validate(self, text: str, rule_name: str, **kwargs) -> bool:
        """Validate text according to specified rule."""
        if rule_name in self._validation_rules:
            return self._validation_rules[rule_name](text, **kwargs)
        elif rule_name in self._custom_validators:
            return self._custom_validators[rule_name](text, **kwargs)
        else:
            raise ValueError(f"Unknown validation rule: {rule_name}")

    def add_custom_validator(self, name: str, validator: Callable[[str], bool]):
        """Add custom validation rule."""
        self._custom_validators[name] = validator

    def is_email(self, text: str) -> bool:
        """Check if text is a valid email address."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, text))

    def is_url(self, text: str) -> bool:
        """Check if text is a valid URL."""
        pattern = (
            r"^https?://(?:[-\w.])+(?:[:\d]+)?"
            r"(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$"
        )
        return bool(re.match(pattern, text))

    def is_phone(self, text: str) -> bool:
        """Check if text is a valid phone number."""
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", text)
        return len(digits) >= 10 and len(digits) <= 15

    def is_ip_address(self, text: str) -> bool:
        """Check if text is a valid IP address."""
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, text):
            return False

        # Check each octet
        octets = text.split(".")
        for octet in octets:
            if not (0 <= int(octet) <= 255):
                return False
        return True

    def is_credit_card(self, text: str) -> bool:
        """Check if text is a valid credit card number (Luhn algorithm)."""
        # Remove all non-digit characters
        digits = re.sub(r"\D", "", text)

        if len(digits) < 13 or len(digits) > 19:
            return False

        # Luhn algorithm
        total = 0
        for i, digit in enumerate(reversed(digits)):
            d = int(digit)
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            total += d

        return total % 10 == 0

    def is_strong_password(self, text: str, min_length: int = 8) -> bool:
        """Check if text is a strong password."""
        if len(text) < min_length:
            return False

        # Check for at least one lowercase letter
        if not re.search(r"[a-z]", text):
            return False

        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", text):
            return False

        # Check for at least one digit
        if not re.search(r"\d", text):
            return False

        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', text):
            return False

        return True

    def _init_validation_rules(self):
        """Initialize built-in validation rules."""
        self._validation_rules = {
            "email": self.is_email,
            "url": self.is_url,
            "phone": self.is_phone,
            "ip_address": self.is_ip_address,
            "credit_card": self.is_credit_card,
            "strong_password": self.is_strong_password,
            "not_empty": lambda text: bool(text and text.strip()),
            "min_length": lambda text, min_len: len(text) >= min_len,
            "max_length": lambda text, max_len: len(text) <= max_len,
            "exact_length": lambda text, length: len(text) == length,
            "alphanumeric": lambda text: text.isalnum(),
            "alphabetic": lambda text: text.isalpha(),
            "numeric": lambda text: text.isdigit(),
            "lowercase": lambda text: text.islower(),
            "uppercase": lambda text: text.isupper(),
        }


class TextSanitizer:
    """Text sanitization utilities."""

    def __init__(self):
        """Initialize text sanitizer."""
        self._sensitive_patterns = {}
        self._replacement_strategies = {}

        # Initialize sensitive patterns
        self._init_sensitive_patterns()

    def sanitize(self, text: str, strategy: str = "redact", **kwargs) -> str:
        """Sanitize text according to specified strategy."""
        if strategy == "redact":
            return self._redact_sensitive_data(text, **kwargs)
        elif strategy == "mask":
            return self._mask_sensitive_data(text, **kwargs)
        elif strategy == "hash":
            return self._hash_sensitive_data(text, **kwargs)
        elif strategy == "encrypt":
            return self._encrypt_sensitive_data(text, **kwargs)
        else:
            raise ValueError(f"Unknown sanitization strategy: {strategy}")

    def _redact_sensitive_data(self, text: str, **kwargs) -> str:
        """Redact sensitive data from text."""
        sanitized = text

        for pattern_name, pattern in self._sensitive_patterns.items():
            if pattern_name in kwargs.get("exclude", []):
                continue

            replacement = kwargs.get("replacement", "[REDACTED]")
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized

    def _mask_sensitive_data(self, text: str, **kwargs) -> str:
        """Mask sensitive data in text."""
        sanitized = text

        for pattern_name, pattern in self._sensitive_patterns.items():
            if pattern_name in kwargs.get("exclude", []):
                continue

            def mask_match(match):
                matched_text = match.group(0)
                if len(matched_text) <= 4:
                    return "*" * len(matched_text)
                else:
                    return (
                        matched_text[:2]
                        + "*" * (len(matched_text) - 4)
                        + matched_text[-2:]
                    )

            sanitized = pattern.sub(mask_match, sanitized)

        return sanitized

    def _hash_sensitive_data(self, text: str, **kwargs) -> str:
        """Hash sensitive data in text."""
        sanitized = text

        for pattern_name, pattern in self._sensitive_patterns.items():
            if pattern_name in kwargs.get("exclude", []):
                continue

            def hash_match(match):
                matched_text = match.group(0)
                return hashlib.sha256(matched_text.encode()).hexdigest()[:8]

            sanitized = pattern.sub(hash_match, sanitized)

        return sanitized

    def _encrypt_sensitive_data(self, text: str, **kwargs) -> str:
        """Encrypt sensitive data in text (placeholder implementation)."""
        # This would require proper encryption implementation
        return self._redact_sensitive_data(text, **kwargs)

    def _init_sensitive_patterns(self):
        """Initialize patterns for sensitive data."""
        self._sensitive_patterns = {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(
                r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
            ),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
            "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
            "api_key": re.compile(r"\b[A-Za-z0-9]{32,}\b"),
            "password": re.compile(r"\bpassword\s*[=:]\s*\S+", re.IGNORECASE),
            "token": re.compile(r"\btoken\s*[=:]\s*\S+", re.IGNORECASE),
        }


class TextAnalyzer:
    """Text analysis and metrics utilities."""

    def __init__(self):
        """Initialize text analyzer."""
        self._language_detector = None
        self._readability_calculator = None

    def analyze_text(self, text: str) -> TextMetrics:
        """Analyze text and return  metrics."""
        # Basic metrics
        character_count = len(text)
        word_count = len(self._extract_words(text))
        line_count = text.count("\n") + 1
        sentence_count = len(self._extract_sentences(text))
        paragraph_count = len(self._extract_paragraphs(text))

        # Calculate averages
        average_word_length = character_count / max(word_count, 1)
        average_sentence_length = word_count / max(sentence_count, 1)
        average_paragraph_length = sentence_count / max(paragraph_count, 1)

        # Character and word frequency
        character_frequency = Counter(text.lower())
        word_frequency = Counter(self._extract_words(text))

        # Create metrics object
        metrics = TextMetrics(
            character_count=character_count,
            word_count=word_count,
            line_count=line_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            average_word_length=round(average_word_length, 2),
            average_sentence_length=round(average_sentence_length, 2),
            average_paragraph_length=round(average_paragraph_length, 2),
            character_frequency=dict(character_frequency),
            word_frequency=dict(word_frequency),
        )

        # Calculate readability scores
        metrics.flesch_reading_ease = self._calculate_flesch_reading_ease(metrics)
        metrics.flesch_kincaid_grade = self._calculate_flesch_kincaid_grade(metrics)
        metrics.gunning_fog_index = self._calculate_gunning_fog_index(metrics)

        return metrics

    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text."""
        return re.findall(r"\b\w+\b", text.lower())

    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text."""
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]

    def _calculate_flesch_reading_ease(self, metrics: TextMetrics) -> float:
        """Calculate Flesch Reading Ease score."""
        if metrics.sentence_count == 0 or metrics.word_count == 0:
            return 0.0

        # Simplified calculation
        avg_sentence_length = metrics.average_sentence_length
        avg_syllables_per_word = 1.5  # Approximation

        score = (
            206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        )
        return max(0.0, min(100.0, score))

    def _calculate_flesch_kincaid_grade(self, metrics: TextMetrics) -> float:
        """Calculate Flesch-Kincaid Grade Level."""
        if metrics.sentence_count == 0 or metrics.word_count == 0:
            return 0.0

        # Simplified calculation
        avg_sentence_length = metrics.average_sentence_length
        avg_syllables_per_word = 1.5  # Approximation

        score = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        return max(0.0, score)

    def _calculate_gunning_fog_index(self, metrics: TextMetrics) -> float:
        """Calculate Gunning Fog Index."""
        if metrics.sentence_count == 0 or metrics.word_count == 0:
            return 0.0

        # Simplified calculation
        avg_sentence_length = metrics.average_sentence_length
        complex_words = sum(1 for word in metrics.word_frequency if len(word) > 6)
        complex_word_ratio = complex_words / max(metrics.word_count, 1)

        score = 0.4 * (avg_sentence_length + complex_word_ratio * 100)
        return max(0.0, score)

    def get_text_summary(self, text: str, max_words: int = 100) -> str:
        """Generate a summary of the text."""
        sentences = self._extract_sentences(text)
        if not sentences:
            return ""

        # Simple extractive summarization
        word_freq = Counter(self._extract_words(text))

        # Score sentences based on word frequency
        sentence_scores = {}
        for sentence in sentences:
            score = sum(word_freq.get(word.lower(), 0) for word in sentence.split())
            sentence_scores[sentence] = score

        # Get top sentences
        top_sentences = sorted(
            sentence_scores.items(), key=lambda x: x[1], reverse=True
        )

        # Build summary
        summary_words = 0
        summary_sentences = []

        for sentence, _ in top_sentences:
            sentence_words = len(sentence.split())
            if summary_words + sentence_words <= max_words:
                summary_sentences.append(sentence)
                summary_words += sentence_words
            else:
                break

        return " ".join(summary_sentences)

    def detect_language(self, text: str) -> str:
        """Detect the language of the text (simplified implementation)."""
        # This is a simplified language detection
        # In practice, you'd use libraries like langdetect or polyglot

        # Simple heuristics based on common words
        text_lower = text.lower()

        # English common words
        english_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        english_count = sum(1 for word in english_words if word in text_lower)

        # Spanish common words
        spanish_words = {
            "el",
            "la",
            "de",
            "que",
            "y",
            "a",
            "en",
            "un",
            "es",
            "se",
            "no",
            "te",
            "lo",
            "le",
        }
        spanish_count = sum(1 for word in spanish_words if word in text_lower)

        # French common words
        french_words = {
            "le",
            "la",
            "de",
            "et",
            "à",
            "en",
            "un",
            "une",
            "est",
            "son",
            "sa",
            "ses",
            "dans",
            "sur",
        }
        french_count = sum(1 for word in french_words if word in text_lower)

        # German common words
        german_words = {
            "der",
            "die",
            "das",
            "und",
            "in",
            "den",
            "von",
            "zu",
            "mit",
            "sich",
            "auf",
            "ist",
            "es",
            "an",
        }
        german_count = sum(1 for word in german_words if word in text_lower)

        # Return language with highest count
        counts = {
            "en": english_count,
            "es": spanish_count,
            "fr": french_count,
            "de": german_count,
        }

        detected = max(counts, key=counts.get)
        return detected if counts[detected] > 0 else "en"  # Default to English
