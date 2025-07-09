"""
Comprehensive tests for data protection security module.

This module tests all functionality in hydra_logger.data_protection.security
to achieve 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock

from hydra_logger.data_protection.security import (
    DataSanitizer,
    SecurityValidator,
    DataHasher
)
from hydra_logger.core.exceptions import DataProtectionError


class TestDataSanitizer:
    """Test DataSanitizer class."""

    def test_data_sanitizer_init_default(self):
        """Test DataSanitizer initialization with default patterns."""
        sanitizer = DataSanitizer()
        assert sanitizer.redact_patterns is not None
        assert sanitizer._compiled_patterns is not None

    def test_data_sanitizer_init_custom(self):
        """Test DataSanitizer initialization with custom patterns."""
        custom_patterns = {"custom": r"custom_pattern"}
        sanitizer = DataSanitizer(custom_patterns)
        assert sanitizer.redact_patterns == custom_patterns

    def test_sanitize_data_string(self):
        """Test sanitizing string data."""
        sanitizer = DataSanitizer()
        result = sanitizer.sanitize_data("test@example.com")
        assert "[REDACTED_EMAIL]" in result

    def test_sanitize_data_dict(self):
        """Test sanitizing dictionary data."""
        sanitizer = DataSanitizer()
        data = {"email": "test@example.com", "password": "secret123"}
        result = sanitizer.sanitize_data(data)
        assert result["email"] == "[REDACTED]"
        assert result["password"] == "[REDACTED]"

    def test_sanitize_data_list(self):
        """Test sanitizing list data."""
        sanitizer = DataSanitizer()
        data = ["test@example.com", "password123"]
        result = sanitizer.sanitizer_data(data)
        assert any("[REDACTED" in str(item) for item in result)

    def test_sanitize_data_other(self):
        """Test sanitizing other data types."""
        sanitizer = DataSanitizer()
        result = sanitizer.sanitize_data(123)
        assert result == 123

    def test_sanitize_string_with_email(self):
        """Test sanitizing string with email."""
        sanitizer = DataSanitizer()
        result = sanitizer._sanitize_string("Contact us at test@example.com")
        assert "[REDACTED_EMAIL]" in result

    def test_sanitize_string_with_credit_card(self):
        """Test sanitizing string with credit card."""
        sanitizer = DataSanitizer()
        result = sanitizer._sanitize_string("Card: 1234-5678-9012-3456")
        assert "[REDACTED_CREDIT_CARD]" in result

    def test_sanitize_string_with_ssn(self):
        """Test sanitizing string with SSN."""
        sanitizer = DataSanitizer()
        result = sanitizer._sanitize_string("SSN: 123-45-6789")
        assert "[REDACTED_SSN]" in result

    def test_sanitize_string_with_phone(self):
        """Test sanitizing string with phone number."""
        sanitizer = DataSanitizer()
        result = sanitizer._sanitize_string("Call: (555) 123-4567")
        assert "[REDACTED_PHONE]" in result

    def test_sanitize_dict_with_sensitive_keys(self):
        """Test sanitizing dict with sensitive keys."""
        sanitizer = DataSanitizer()
        data = {"password": "secret", "api_key": "key123", "normal": "value"}
        result = sanitizer._sanitize_dict(data)
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"
        assert result["normal"] == "value"

    def test_sanitize_dict_nested(self):
        """Test sanitizing nested dictionary."""
        sanitizer = DataSanitizer()
        data = {
            "user": {
                "email": "test@example.com",
                "profile": {"password": "secret"}
            }
        }
        result = sanitizer._sanitize_dict(data)
        assert result["user"]["email"] == "[REDACTED]"
        assert result["user"]["profile"]["password"] == "[REDACTED]"

    def test_sanitize_list(self):
        """Test sanitizing list."""
        sanitizer = DataSanitizer()
        data = ["test@example.com", {"password": "secret"}]
        result = sanitizer._sanitize_list(data)
        assert any("[REDACTED" in str(item) for item in result)

    def test_is_sensitive_key_true(self):
        """Test sensitive key detection."""
        sanitizer = DataSanitizer()
        assert sanitizer._is_sensitive_key("password") is True
        assert sanitizer._is_sensitive_key("api_key") is True
        assert sanitizer._is_sensitive_key("secret_token") is True

    def test_is_sensitive_key_false(self):
        """Test non-sensitive key detection."""
        sanitizer = DataSanitizer()
        assert sanitizer._is_sensitive_key("name") is False
        assert sanitizer._is_sensitive_key("email") is False

    def test_add_pattern(self):
        """Test adding custom pattern."""
        sanitizer = DataSanitizer()
        sanitizer.add_pattern("custom", r"custom_pattern")
        assert "custom" in sanitizer.redact_patterns
        assert "custom" in sanitizer._compiled_patterns

    def test_remove_pattern_existing(self):
        """Test removing existing pattern."""
        sanitizer = DataSanitizer()
        result = sanitizer.remove_pattern("email")
        assert result is True
        assert "email" not in sanitizer.redact_patterns

    def test_remove_pattern_non_existing(self):
        """Test removing non-existing pattern."""
        sanitizer = DataSanitizer()
        result = sanitizer.remove_pattern("non_existing")
        assert result is False


class TestSecurityValidator:
    """Test SecurityValidator class."""

    def test_security_validator_init(self):
        """Test SecurityValidator initialization."""
        validator = SecurityValidator()
        assert validator._threat_patterns is not None
        assert validator._compiled_threat_patterns is not None

    def test_get_threat_patterns(self):
        """Test getting threat patterns."""
        validator = SecurityValidator()
        patterns = validator._get_threat_patterns()
        assert "sql_injection" in patterns
        assert "xss" in patterns
        assert "path_traversal" in patterns

    def test_compile_threat_patterns(self):
        """Test compiling threat patterns."""
        validator = SecurityValidator()
        patterns = validator._compile_threat_patterns()
        assert "sql_injection" in patterns
        assert "xss" in patterns

    def test_validate_input_string_safe(self):
        """Test validating safe string input."""
        validator = SecurityValidator()
        result = validator.validate_input("safe string")
        assert result["valid"] is True
        assert result["threats"] == []

    def test_validate_input_string_sql_injection(self):
        """Test validating string with SQL injection."""
        validator = SecurityValidator()
        result = validator.validate_input("SELECT * FROM users")
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(t["type"] == "sql_injection" for t in result["threats"])

    def test_validate_input_string_xss(self):
        """Test validating string with XSS."""
        validator = SecurityValidator()
        result = validator.validate_input("<script>alert('xss')</script>")
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(t["type"] == "xss" for t in result["threats"])

    def test_validate_input_string_path_traversal(self):
        """Test validating string with path traversal."""
        validator = SecurityValidator()
        result = validator.validate_input("../../../etc/passwd")
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(t["type"] == "path_traversal" for t in result["threats"])

    def test_validate_input_string_command_injection(self):
        """Test validating string with command injection."""
        validator = SecurityValidator()
        result = validator.validate_input("; rm -rf /")
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(t["type"] == "command_injection" for t in result["threats"])

    def test_validate_input_dict_safe(self):
        """Test validating safe dictionary input."""
        validator = SecurityValidator()
        data = {"name": "safe", "value": "data"}
        result = validator.validate_input(data)
        assert result["valid"] is True

    def test_validate_input_dict_threat(self):
        """Test validating dictionary with threat."""
        validator = SecurityValidator()
        data = {"name": "safe", "query": "SELECT * FROM users"}
        result = validator.validate_input(data)
        assert result["valid"] is False

    def test_validate_input_list_safe(self):
        """Test validating safe list input."""
        validator = SecurityValidator()
        data = ["safe", "data"]
        result = validator.validate_input(data)
        assert result["valid"] is True

    def test_validate_input_list_threat(self):
        """Test validating list with threat."""
        validator = SecurityValidator()
        data = ["safe", "<script>alert('xss')</script>"]
        result = validator.validate_input(data)
        assert result["valid"] is False

    def test_validate_input_other(self):
        """Test validating other input types."""
        validator = SecurityValidator()
        result = validator.validate_input(123)
        assert result["valid"] is True

    def test_validate_string_multiple_threats(self):
        """Test validating string with multiple threats."""
        validator = SecurityValidator()
        result = validator.validate_input("SELECT * FROM users; <script>alert('xss')</script>")
        assert result["valid"] is False
        assert len(result["threats"]) >= 2

    def test_validate_dict_nested_threat(self):
        """Test validating nested dictionary with threat."""
        validator = SecurityValidator()
        data = {
            "user": {
                "name": "safe",
                "query": "SELECT * FROM users"
            }
        }
        result = validator.validate_input(data)
        assert result["valid"] is False

    def test_validate_list_nested_threat(self):
        """Test validating nested list with threat."""
        validator = SecurityValidator()
        data = ["safe", ["nested", "SELECT * FROM users"]]
        result = validator.validate_input(data)
        assert result["valid"] is False

    def test_get_threat_severity_high(self):
        """Test getting high severity threat."""
        validator = SecurityValidator()
        severity = validator._get_threat_severity("sql_injection")
        assert severity == "high"

    def test_get_threat_severity_medium(self):
        """Test getting medium severity threat."""
        validator = SecurityValidator()
        severity = validator._get_threat_severity("path_traversal")
        assert severity == "medium"

    def test_get_threat_severity_low(self):
        """Test getting low severity threat."""
        validator = SecurityValidator()
        severity = validator._get_threat_severity("unknown_threat")
        assert severity == "low"

    def test_add_threat_pattern(self):
        """Test adding custom threat pattern."""
        validator = SecurityValidator()
        validator.add_threat_pattern("custom", r"custom_threat")
        assert "custom" in validator._threat_patterns
        assert "custom" in validator._compiled_threat_patterns


class TestDataHasher:
    """Test DataHasher class."""

    def test_data_hasher_init_default(self):
        """Test DataHasher initialization with default algorithm."""
        hasher = DataHasher()
        assert hasher.algorithm == "sha256"

    def test_data_hasher_init_custom(self):
        """Test DataHasher initialization with custom algorithm."""
        hasher = DataHasher("md5")
        assert hasher.algorithm == "md5"

    def test_hash_data_sha256(self):
        """Test hashing data with SHA256."""
        hasher = DataHasher("sha256")
        result = hasher.hash_data("test data")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length

    def test_hash_data_md5(self):
        """Test hashing data with MD5."""
        hasher = DataHasher("md5")
        result = hasher.hash_data("test data")
        assert isinstance(result, str)
        assert len(result) == 32  # MD5 hex length

    def test_hash_data_sha1(self):
        """Test hashing data with SHA1."""
        hasher = DataHasher("sha1")
        result = hasher.hash_data("test data")
        assert isinstance(result, str)
        assert len(result) == 40  # SHA1 hex length

    def test_hash_data_sha512(self):
        """Test hashing data with SHA512."""
        hasher = DataHasher("sha512")
        result = hasher.hash_data("test data")
        assert isinstance(result, str)
        assert len(result) == 128  # SHA512 hex length

    def test_hash_data_unsupported_algorithm(self):
        """Test hashing with unsupported algorithm."""
        hasher = DataHasher("unsupported")
        with pytest.raises(DataProtectionError, match="Unsupported hash algorithm"):
            hasher.hash_data("test data")

    def test_hash_sensitive_fields(self):
        """Test hashing sensitive fields in dictionary."""
        hasher = DataHasher()
        data = {
            "name": "John Doe",
            "password": "secret123",
            "email": "john@example.com",
            "token": "abc123"
        }
        sensitive_fields = ["password", "token"]
        
        result = hasher.hash_sensitive_fields(data, sensitive_fields)
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["password"] != "secret123"
        assert result["token"] != "abc123"
        assert isinstance(result["password"], str)
        assert isinstance(result["token"], str)

    def test_hash_sensitive_fields_non_string(self):
        """Test hashing sensitive fields with non-string values."""
        hasher = DataHasher()
        data = {
            "name": "John Doe",
            "password": 123,
            "token": None
        }
        sensitive_fields = ["password", "token"]
        
        result = hasher.hash_sensitive_fields(data, sensitive_fields)
        assert result["name"] == "John Doe"
        assert result["password"] == 123  # Should not hash non-string
        assert result["token"] is None  # Should not hash None

    def test_hash_sensitive_fields_missing_fields(self):
        """Test hashing sensitive fields with missing fields."""
        hasher = DataHasher()
        data = {"name": "John Doe"}
        sensitive_fields = ["password", "token"]
        
        result = hasher.hash_sensitive_fields(data, sensitive_fields)
        assert result["name"] == "John Doe"
        assert "password" not in result
        assert "token" not in result

    def test_verify_hash_success(self):
        """Test successful hash verification."""
        hasher = DataHasher()
        data = "test data"
        hash_value = hasher.hash_data(data)
        result = hasher.verify_hash(data, hash_value)
        assert result is True

    def test_verify_hash_failure(self):
        """Test failed hash verification."""
        hasher = DataHasher()
        data = "test data"
        wrong_hash = "wrong_hash_value"
        result = hasher.verify_hash(data, wrong_hash)
        assert result is False

    def test_verify_hash_different_data(self):
        """Test hash verification with different data."""
        hasher = DataHasher()
        original_data = "test data"
        different_data = "different data"
        hash_value = hasher.hash_data(original_data)
        result = hasher.verify_hash(different_data, hash_value)
        assert result is False 