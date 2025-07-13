"""
Comprehensive tests for security module to achieve 100% coverage.

This module tests all edge cases, error conditions, and security
validation functionality to ensure complete test coverage.
"""

import re
import hashlib
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

import pytest

from hydra_logger.data_protection.security import (
    DataSanitizer,
    SecurityValidator,
    DataHasher
)
from hydra_logger.core.exceptions import DataProtectionError


class TestDataSanitizer:
    """Test DataSanitizer with comprehensive coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = DataSanitizer()
    
    def test_init_with_default_patterns(self):
        """Test DataSanitizer initialization with default patterns."""
        sanitizer = DataSanitizer()
        
        assert sanitizer.redact_patterns is not None
        assert len(sanitizer.redact_patterns) > 0
        assert sanitizer._compiled_patterns is not None
        assert len(sanitizer._compiled_patterns) > 0
    
    def test_init_with_custom_patterns(self):
        """Test DataSanitizer initialization with custom patterns."""
        custom_patterns = {
            "custom_email": r"test@example\.com",
            "custom_phone": r"\d{3}-\d{3}-\d{4}"
        }
        
        sanitizer = DataSanitizer(redact_patterns=custom_patterns)
        
        assert sanitizer.redact_patterns == custom_patterns
        assert "custom_email" in sanitizer._compiled_patterns
        assert "custom_phone" in sanitizer._compiled_patterns
    
    def test_compile_patterns(self):
        """Test _compile_patterns method."""
        patterns = {
            "test_pattern": r"test\d+",
            "email": r"[\w\.-]+@[\w\.-]+\.\w+"
        }
        
        sanitizer = DataSanitizer(redact_patterns=patterns)
        
        assert "test_pattern" in sanitizer._compiled_patterns
        assert "email" in sanitizer._compiled_patterns
        assert isinstance(sanitizer._compiled_patterns["test_pattern"], re.Pattern)
        assert isinstance(sanitizer._compiled_patterns["email"], re.Pattern)
    
    def test_sanitize_data_string(self):
        """Test sanitize_data with string input."""
        test_string = "Contact me at john.doe@example.com or call 555-123-4567"
        sanitized = self.sanitizer.sanitize_data(test_string)
        
        assert "[REDACTED_EMAIL]" in sanitized
        assert "[REDACTED_PHONE]" in sanitized
        assert "john.doe@example.com" not in sanitized
        assert "555-123-4567" not in sanitized
    
    def test_sanitize_data_dict(self):
        """Test sanitize_data with dictionary input."""
        test_dict = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "secret123",
            "phone": "555-123-4567",
            "nested": {
                "ssn": "123-45-6789",
                "credit_card": "4111-1111-1111-1111"
            }
        }
        
        sanitized = self.sanitizer.sanitize_data(test_dict)
        
        assert sanitized["name"] == "John Doe"  # Not sensitive
        assert sanitized["email"] == "[REDACTED_EMAIL]"
        assert sanitized["password"] == "[REDACTED]"  # Sensitive key
        assert sanitized["phone"] == "[REDACTED_PHONE]"
        assert sanitized["nested"]["ssn"] == "[REDACTED_SSN]"
        assert sanitized["nested"]["credit_card"] == "[REDACTED_CREDIT_CARD]"
    
    def test_sanitize_data_list(self):
        """Test sanitize_data with list input."""
        test_list = [
            "john@example.com",
            "555-123-4567",
            {"email": "jane@example.com", "ssn": "987-65-4321"}
        ]
        
        sanitized = self.sanitizer.sanitize_data(test_list)
        
        assert sanitized[0] == "[REDACTED_EMAIL]"
        assert sanitized[1] == "[REDACTED_PHONE]"
        assert sanitized[2]["email"] == "[REDACTED_EMAIL]"
        assert sanitized[2]["ssn"] == "[REDACTED_SSN]"
    
    def test_sanitize_data_tuple(self):
        """Test sanitize_data with tuple input."""
        test_tuple = ("john@example.com", "555-123-4567")
        
        sanitized = self.sanitizer.sanitize_data(test_tuple)
        
        assert isinstance(sanitized, tuple)
        assert sanitized[0] == "[REDACTED_EMAIL]"
        assert sanitized[1] == "[REDACTED_PHONE]"
    
    def test_sanitize_data_other_types(self):
        """Test sanitize_data with other data types."""
        # Test with integer
        assert self.sanitizer.sanitize_data(123) == 123
        
        # Test with float
        assert self.sanitizer.sanitize_data(3.14) == 3.14
        
        # Test with boolean
        assert self.sanitizer.sanitize_data(True) is True
        
        # Test with None
        assert self.sanitizer.sanitize_data(None) is None
    
    def test_sanitize_data_circular_reference(self):
        """Test sanitize_data handles circular references."""
        # Create circular reference
        data: Dict[str, Any] = {"key": "value"}
        data["self"] = data
        
        sanitized = self.sanitizer.sanitize_data(data, depth=15)
        
        assert sanitized == "[REDACTED_CIRCULAR_REFERENCE]"
    
    def test_sanitize_string_specific_patterns(self):
        """Test _sanitize_string with specific patterns."""
        test_string = "Email: test@example.com, Phone: 555-123-4567, SSN: 123-45-6789"
        
        sanitized = self.sanitizer._sanitize_string(test_string)
        
        assert "[REDACTED_EMAIL]" in sanitized
        assert "[REDACTED_PHONE]" in sanitized
        assert "[REDACTED_SSN]" in sanitized
    
    def test_sanitize_string_generic_patterns(self):
        """Test _sanitize_string with generic patterns."""
        # Add a generic pattern
        self.sanitizer.add_pattern("generic", r"generic_pattern")
        
        test_string = "This contains generic_pattern"
        sanitized = self.sanitizer._sanitize_string(test_string)
        
        assert "[REDACTED]" in sanitized
        assert "generic_pattern" not in sanitized
    
    def test_sanitize_dict_sensitive_keys(self):
        """Test _sanitize_dict with sensitive keys."""
        test_dict = {
            "username": "john",
            "password": "secret123",
            "secret_key": "abc123",
            "auth_token": "xyz789",
            "private_data": "sensitive",
            "normal_field": "value"
        }
        
        sanitized = self.sanitizer._sanitize_dict(test_dict)
        
        # Sensitive keys should be redacted
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["secret_key"] == "[REDACTED]"
        assert sanitized["auth_token"] == "[REDACTED]"
        assert sanitized["private_data"] == "[REDACTED]"
        
        # Normal keys should remain
        assert sanitized["username"] == "john"
        assert sanitized["normal_field"] == "value"
    
    def test_sanitize_dict_nested_structures(self):
        """Test _sanitize_dict with nested structures."""
        test_dict = {
            "user": {
                "name": "John",
                "email": "john@example.com",
                "account_info": {
                    "password": "secret",
                    "token": "abc123"
                }
            }
        }
        
        sanitized = self.sanitizer._sanitize_dict(test_dict)
        
        assert sanitized["user"]["name"] == "John"
        assert sanitized["user"]["email"] == "[REDACTED_EMAIL]"
        # The nested account_info should be sanitized recursively
        # Since "account_info" is not a sensitive key, it should be recursively sanitized
        assert isinstance(sanitized["user"]["account_info"], dict)
        assert sanitized["user"]["account_info"]["password"] == "[REDACTED]"
        assert sanitized["user"]["account_info"]["token"] == "[REDACTED]"
    
    def test_sanitize_list_simple(self):
        """Test _sanitize_list with simple list."""
        test_list = ["item1", "john@example.com", "item2"]
        
        sanitized = self.sanitizer._sanitize_list(test_list)
        
        assert sanitized[0] == "item1"
        assert sanitized[1] == "[REDACTED_EMAIL]"
        assert sanitized[2] == "item2"
    
    def test_sanitize_list_nested(self):
        """Test _sanitize_list with nested structures."""
        test_list = [
            "normal_item",
            {"email": "test@example.com", "password": "secret"},
            ["nested", "john@example.com"]
        ]
        
        sanitized = self.sanitizer._sanitize_list(test_list)
        
        assert sanitized[0] == "normal_item"
        assert sanitized[1]["email"] == "[REDACTED_EMAIL]"
        assert sanitized[1]["password"] == "[REDACTED]"
        assert sanitized[2][0] == "nested"
        assert sanitized[2][1] == "[REDACTED_EMAIL]"
    
    def test_sanitize_list_tuple(self):
        """Test _sanitize_list with tuple input."""
        test_tuple = ("item1", "john@example.com", "item2")
        
        sanitized = self.sanitizer._sanitize_list(test_tuple)
        
        assert isinstance(sanitized, tuple)
        assert sanitized[0] == "item1"
        assert sanitized[1] == "[REDACTED_EMAIL]"
        assert sanitized[2] == "item2"
    
    def test_is_sensitive_key(self):
        """Test _is_sensitive_key method."""
        sensitive_keys = [
            "password", "secret", "token", "key", "auth", "credential",
            "private", "sensitive", "confidential", "session_id",
            "user_password", "api_secret", "auth_token", "private_key"
        ]
        
        for key in sensitive_keys:
            assert self.sanitizer._is_sensitive_key(key) is True
        
        normal_keys = ["username", "email", "name", "age", "city"]
        for key in normal_keys:
            assert self.sanitizer._is_sensitive_key(key) is False
    
    def test_add_pattern_success(self):
        """Test add_pattern with valid pattern."""
        self.sanitizer.add_pattern("test_pattern", r"\d{3}-\d{3}-\d{4}")
        
        assert "test_pattern" in self.sanitizer.redact_patterns
        assert "test_pattern" in self.sanitizer._compiled_patterns
        assert isinstance(self.sanitizer._compiled_patterns["test_pattern"], re.Pattern)
    
    def test_add_pattern_invalid_regex(self):
        """Test add_pattern with invalid regex pattern."""
        # This should not raise an exception
        self.sanitizer.add_pattern("invalid_pattern", r"[invalid")
        
        # Pattern should be added to redact_patterns but not to compiled_patterns
        # due to invalid regex
        assert "invalid_pattern" in self.sanitizer.redact_patterns
        assert "invalid_pattern" not in self.sanitizer._compiled_patterns
    
    def test_remove_pattern_existing(self):
        """Test remove_pattern with existing pattern."""
        # Add a pattern first
        self.sanitizer.add_pattern("test_pattern", r"\d+")
        
        # Remove it
        result = self.sanitizer.remove_pattern("test_pattern")
        
        assert result is True
        assert "test_pattern" not in self.sanitizer.redact_patterns
        assert "test_pattern" not in self.sanitizer._compiled_patterns
    
    def test_remove_pattern_nonexistent(self):
        """Test remove_pattern with non-existent pattern."""
        result = self.sanitizer.remove_pattern("nonexistent_pattern")
        
        assert result is False


class TestSecurityValidator:
    """Test SecurityValidator with comprehensive coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SecurityValidator()
    
    def test_init(self):
        """Test SecurityValidator initialization."""
        assert self.validator._threat_patterns is not None
        assert len(self.validator._threat_patterns) > 0
        assert self.validator._compiled_threat_patterns is not None
        assert len(self.validator._compiled_threat_patterns) > 0
    
    def test_get_threat_patterns(self):
        """Test _get_threat_patterns method."""
        patterns = self.validator._get_threat_patterns()
        
        expected_patterns = [
            "sql_injection", "xss", "path_traversal", 
            "command_injection", "ldap_injection", "nosql_injection"
        ]
        
        for pattern in expected_patterns:
            assert pattern in patterns
    
    def test_compile_threat_patterns(self):
        """Test _compile_threat_patterns method."""
        patterns = self.validator._compile_threat_patterns()
        
        for name, pattern in patterns.items():
            assert isinstance(pattern, re.Pattern)
    
    def test_validate_input_string_safe(self):
        """Test validate_input with safe string."""
        safe_string = "This is a safe string with no threats"
        result = self.validator.validate_input(safe_string)
        
        assert result["valid"] is True
        assert result["threats"] == []
    
    def test_validate_input_string_sql_injection(self):
        """Test validate_input with SQL injection attempt."""
        malicious_string = "SELECT * FROM users WHERE id = 1"
        result = self.validator.validate_input(malicious_string)
        
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(threat["type"] == "sql_injection" for threat in result["threats"])
    
    def test_validate_input_string_xss(self):
        """Test validate_input with XSS attempt."""
        malicious_string = "<script>alert('xss')</script>"
        result = self.validator.validate_input(malicious_string)
        
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(threat["type"] == "xss" for threat in result["threats"])
    
    def test_validate_input_string_path_traversal(self):
        """Test validate_input with path traversal attempt."""
        malicious_string = "../../../etc/passwd"
        result = self.validator.validate_input(malicious_string)
        
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(threat["type"] == "path_traversal" for threat in result["threats"])
    
    def test_validate_input_string_command_injection(self):
        """Test validate_input with command injection attempt."""
        malicious_string = "ls; rm -rf /"
        result = self.validator.validate_input(malicious_string)
        
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(threat["type"] == "command_injection" for threat in result["threats"])
    
    def test_validate_input_string_ldap_injection(self):
        """Test validate_input with LDAP injection attempt."""
        malicious_string = "*)(uid=*))(|(uid=*"
        result = self.validator.validate_input(malicious_string)
        
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(threat["type"] == "ldap_injection" for threat in result["threats"])
    
    def test_validate_input_string_nosql_injection(self):
        """Test validate_input with NoSQL injection attempt."""
        malicious_string = '{"$where": "this.username == \'admin\'"}'
        result = self.validator.validate_input(malicious_string)
        
        assert result["valid"] is False
        assert len(result["threats"]) > 0
        assert any(threat["type"] == "nosql_injection" for threat in result["threats"])
    
    def test_validate_input_dict_safe(self):
        """Test validate_input with safe dictionary."""
        safe_dict = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
        result = self.validator.validate_input(safe_dict)
        
        assert result["valid"] is True
        assert result["threats"] == []
    
    def test_validate_input_dict_malicious(self):
        """Test validate_input with malicious dictionary."""
        malicious_dict = {
            "name": "John Doe",
            "query": "SELECT * FROM users",
            "script": "<script>alert('xss')</script>"
        }
        result = self.validator.validate_input(malicious_dict)
        
        assert result["valid"] is False
        assert len(result["threats"]) > 0
    
    def test_validate_input_list_safe(self):
        """Test validate_input with safe list."""
        safe_list = ["item1", "item2", "item3"]
        result = self.validator.validate_input(safe_list)
        
        assert result["valid"] is True
        assert result["threats"] == []
    
    def test_validate_input_list_malicious(self):
        """Test validate_input with malicious list."""
        malicious_list = [
            "normal_item",
            "SELECT * FROM users",
            "<script>alert('xss')</script>"
        ]
        result = self.validator.validate_input(malicious_list)
        
        assert result["valid"] is False
        assert len(result["threats"]) > 0
    
    def test_validate_input_other_types(self):
        """Test validate_input with other data types."""
        # Test with integer
        result = self.validator.validate_input(123)
        assert result["valid"] is True
        assert result["threats"] == []
        
        # Test with float
        result = self.validator.validate_input(3.14)
        assert result["valid"] is True
        assert result["threats"] == []
        
        # Test with boolean
        result = self.validator.validate_input(True)
        assert result["valid"] is True
        assert result["threats"] == []
        
        # Test with None
        result = self.validator.validate_input(None)
        assert result["valid"] is True
        assert result["threats"] == []
    
    def test_validate_string_multiple_threats(self):
        """Test _validate_string with multiple threats."""
        malicious_string = "SELECT * FROM users<script>alert('xss')</script>"
        result = self.validator._validate_string(malicious_string)
        
        assert result["valid"] is False
        assert len(result["threats"]) >= 2
        threat_types = [threat["type"] for threat in result["threats"]]
        assert "sql_injection" in threat_types
        assert "xss" in threat_types
    
    def test_validate_dict_nested(self):
        """Test _validate_dict with nested structures."""
        nested_dict = {
            "user": {
                "name": "John",
                "query": "SELECT * FROM users"
            },
            "script": "<script>alert('xss')</script>"
        }
        result = self.validator._validate_dict(nested_dict)
        
        assert result["valid"] is False
        assert len(result["threats"]) >= 2
    
    def test_validate_list_nested(self):
        """Test _validate_list with nested structures."""
        nested_list = [
            "normal_item",
            {"query": "SELECT * FROM users"},
            ["<script>alert('xss')</script>"]
        ]
        result = self.validator._validate_list(nested_list)
        
        assert result["valid"] is False
        assert len(result["threats"]) >= 2
    
    def test_get_threat_severity(self):
        """Test _get_threat_severity method."""
        # High severity threats
        assert self.validator._get_threat_severity("sql_injection") == "high"
        assert self.validator._get_threat_severity("command_injection") == "high"
        assert self.validator._get_threat_severity("xss") == "high"
        
        # Medium severity threats
        assert self.validator._get_threat_severity("path_traversal") == "medium"
        assert self.validator._get_threat_severity("ldap_injection") == "medium"
        
        # Low severity threats
        assert self.validator._get_threat_severity("nosql_injection") == "low"
        
        # Unknown threats
        assert self.validator._get_threat_severity("unknown_threat") == "low"
    
    def test_add_threat_pattern(self):
        """Test add_threat_pattern method."""
        self.validator.add_threat_pattern("custom_threat", r"custom_pattern")
        
        assert "custom_threat" in self.validator._threat_patterns
        assert "custom_threat" in self.validator._compiled_threat_patterns
        assert isinstance(self.validator._compiled_threat_patterns["custom_threat"], re.Pattern)


class TestDataHasher:
    """Test DataHasher with comprehensive coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.hasher = DataHasher()
    
    def test_init_with_default_algorithm(self):
        """Test DataHasher initialization with default algorithm."""
        assert self.hasher.algorithm == "sha256"
        assert "md5" in self.hasher._hash_functions
        assert "sha1" in self.hasher._hash_functions
        assert "sha256" in self.hasher._hash_functions
        assert "sha512" in self.hasher._hash_functions
    
    def test_init_with_custom_algorithm(self):
        """Test DataHasher initialization with custom algorithm."""
        hasher = DataHasher(algorithm="md5")
        
        assert hasher.algorithm == "md5"
    
    def test_hash_data_success(self):
        """Test hash_data with valid algorithm."""
        test_data = "test_string"
        hash_result = self.hasher.hash_data(test_data)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 produces 64 character hex string
    
    def test_hash_data_md5(self):
        """Test hash_data with MD5 algorithm."""
        hasher = DataHasher(algorithm="md5")
        test_data = "test_string"
        hash_result = hasher.hash_data(test_data)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 32  # MD5 produces 32 character hex string
    
    def test_hash_data_sha1(self):
        """Test hash_data with SHA1 algorithm."""
        hasher = DataHasher(algorithm="sha1")
        test_data = "test_string"
        hash_result = hasher.hash_data(test_data)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 40  # SHA1 produces 40 character hex string
    
    def test_hash_data_sha512(self):
        """Test hash_data with SHA512 algorithm."""
        hasher = DataHasher(algorithm="sha512")
        test_data = "test_string"
        hash_result = hasher.hash_data(test_data)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 128  # SHA512 produces 128 character hex string
    
    def test_hash_data_invalid_algorithm(self):
        """Test hash_data with invalid algorithm."""
        hasher = DataHasher(algorithm="invalid_algorithm")
        
        with pytest.raises(DataProtectionError):
            hasher.hash_data("test_string")
    
    def test_hash_sensitive_fields_string(self):
        """Test hash_sensitive_fields with string values."""
        test_data = {
            "username": "john_doe",
            "password": "secret123",
            "email": "john@example.com",
            "age": 30
        }
        sensitive_fields = ["password", "email"]
        
        hashed_data = self.hasher.hash_sensitive_fields(test_data, sensitive_fields)
        
        assert hashed_data["username"] == "john_doe"  # Not hashed
        assert hashed_data["age"] == 30  # Not hashed
        assert hashed_data["password"] != "secret123"  # Should be hashed
        assert hashed_data["email"] != "john@example.com"  # Should be hashed
        assert isinstance(hashed_data["password"], str)
        assert isinstance(hashed_data["email"], str)
    
    def test_hash_sensitive_fields_dict_value(self):
        """Test hash_sensitive_fields with dictionary values."""
        test_data = {
            "user": {"name": "John", "email": "john@example.com"},
            "config": {"api_key": "secret_key"}
        }
        sensitive_fields = ["user", "config"]
        
        hashed_data = self.hasher.hash_sensitive_fields(test_data, sensitive_fields)
        
        assert hashed_data["user"] != {"name": "John", "email": "john@example.com"}
        assert hashed_data["config"] != {"api_key": "secret_key"}
        assert isinstance(hashed_data["user"], str)
        assert isinstance(hashed_data["config"], str)
    
    def test_hash_sensitive_fields_list_value(self):
        """Test hash_sensitive_fields with list values."""
        test_data = {
            "tokens": ["token1", "token2", "token3"],
            "permissions": ["read", "write", "admin"]
        }
        sensitive_fields = ["tokens", "permissions"]
        
        hashed_data = self.hasher.hash_sensitive_fields(test_data, sensitive_fields)
        
        assert hashed_data["tokens"] != ["token1", "token2", "token3"]
        assert hashed_data["permissions"] != ["read", "write", "admin"]
        assert isinstance(hashed_data["tokens"], str)
        assert isinstance(hashed_data["permissions"], str)
    
    def test_hash_sensitive_fields_other_types(self):
        """Test hash_sensitive_fields with other data types."""
        test_data = {
            "user_id": 12345,
            "is_active": True,
            "score": 95.5,
            "metadata": None
        }
        sensitive_fields = ["user_id", "is_active", "score", "metadata"]
        
        hashed_data = self.hasher.hash_sensitive_fields(test_data, sensitive_fields)
        
        assert hashed_data["user_id"] != 12345
        assert hashed_data["is_active"] != True
        assert hashed_data["score"] != 95.5
        assert hashed_data["metadata"] != None
        assert isinstance(hashed_data["user_id"], str)
        assert isinstance(hashed_data["is_active"], str)
        assert isinstance(hashed_data["score"], str)
        assert isinstance(hashed_data["metadata"], str)
    
    def test_hash_sensitive_fields_missing_fields(self):
        """Test hash_sensitive_fields with missing fields."""
        test_data = {
            "username": "john_doe",
            "email": "john@example.com"
        }
        sensitive_fields = ["password", "email", "ssn"]  # password and ssn don't exist
        
        hashed_data = self.hasher.hash_sensitive_fields(test_data, sensitive_fields)
        
        assert hashed_data["username"] == "john_doe"  # Not in sensitive fields
        assert hashed_data["email"] != "john@example.com"  # Should be hashed
        assert "password" not in hashed_data  # Field doesn't exist
        assert "ssn" not in hashed_data  # Field doesn't exist
    
    def test_verify_hash_success(self):
        """Test verify_hash with matching hash."""
        test_data = "test_string"
        hash_value = self.hasher.hash_data(test_data)
        
        result = self.hasher.verify_hash(test_data, hash_value)
        
        assert result is True
    
    def test_verify_hash_failure(self):
        """Test verify_hash with non-matching hash."""
        test_data = "test_string"
        wrong_hash = "wrong_hash_value"
        
        result = self.hasher.verify_hash(test_data, wrong_hash)
        
        assert result is False
    
    def test_verify_hash_different_data(self):
        """Test verify_hash with different data."""
        original_data = "original_string"
        different_data = "different_string"
        hash_value = self.hasher.hash_data(original_data)
        
        result = self.hasher.verify_hash(different_data, hash_value)
        
        assert result is False


class TestSecurityIntegration:
    """Integration tests for security module."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = DataSanitizer()
        self.validator = SecurityValidator()
        self.hasher = DataHasher()
    
    def test_comprehensive_data_processing(self):
        """Test comprehensive data processing with all security components."""
        # Test data with various security concerns
        test_data = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "secret123",
                "query": "SELECT * FROM users WHERE id = 1"
            },
            "script": "<script>alert('xss')</script>",
            "path": "../../../etc/passwd",
            "tokens": ["token1", "token2"]
        }
        
        # Step 1: Validate for threats
        validation_result = self.validator.validate_input(test_data)
        assert validation_result["valid"] is False
        assert len(validation_result["threats"]) > 0
        
        # Step 2: Sanitize sensitive data
        sanitized_data = self.sanitizer.sanitize_data(test_data)
        assert sanitized_data["user"]["password"] == "[REDACTED]"
        assert sanitized_data["user"]["email"] == "[REDACTED_EMAIL]"
        
        # Step 3: Hash sensitive fields
        hashed_data = self.hasher.hash_sensitive_fields(
            sanitized_data, 
            ["user", "tokens"]
        )
        assert isinstance(hashed_data["user"], str)
        assert isinstance(hashed_data["tokens"], str)
    
    def test_security_components_independence(self):
        """Test that security components work independently."""
        # Test sanitizer without validator
        test_data = {"email": "test@example.com", "password": "secret"}
        sanitized = self.sanitizer.sanitize_data(test_data)
        assert sanitized["email"] == "[REDACTED_EMAIL]"
        assert sanitized["password"] == "[REDACTED]"
        
        # Test validator without sanitizer
        malicious_data = "SELECT * FROM users"
        validation = self.validator.validate_input(malicious_data)
        assert validation["valid"] is False
        
        # Test hasher without other components
        hash_result = self.hasher.hash_data("test_string")
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0 