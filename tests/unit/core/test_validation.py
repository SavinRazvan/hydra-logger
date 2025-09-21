"""
Tests for core/validation.py module.

This module tests the input validation utilities for configuration and input data.
"""

import pytest
from unittest.mock import Mock, patch
from hydra_logger.core.validation import (
    ValidationRule, Validator, validator,
    validate_value, validate_config, add_validation_rule, remove_validation_rule
)
from hydra_logger.core.exceptions import ValidationError


class TestValidationRule:
    """Test ValidationRule class."""
    
    def test_validation_rule_init(self):
        """Test ValidationRule initialization."""
        validator_func = lambda x: x > 0
        rule = ValidationRule("positive", validator_func, "Must be positive")
        
        assert rule.name == "positive"
        assert rule.validator is validator_func
        assert rule.message == "Must be positive"
    
    def test_validation_rule_init_default_message(self):
        """Test ValidationRule initialization with default message."""
        validator_func = lambda x: x > 0
        rule = ValidationRule("positive", validator_func)
        
        assert rule.name == "positive"
        assert rule.validator is validator_func
        assert rule.message == "Validation failed for rule: positive"
    
    def test_validate_success(self):
        """Test validate method with success."""
        validator_func = lambda x: x > 0
        rule = ValidationRule("positive", validator_func)
        
        assert rule.validate(5) is True
        assert rule.validate(0.1) is True
        assert rule.validate(100) is True
    
    def test_validate_failure(self):
        """Test validate method with failure."""
        validator_func = lambda x: x > 0
        rule = ValidationRule("positive", validator_func)
        
        assert rule.validate(0) is False
        assert rule.validate(-1) is False
        assert rule.validate(-0.1) is False
    
    def test_validate_exception_handling(self):
        """Test validate method with exception handling."""
        def validator_func(x):
            if x == "error":
                raise Exception("Test error")
            return x > 0
        
        rule = ValidationRule("positive", validator_func)
        
        assert rule.validate(5) is True
        assert rule.validate("error") is False  # Exception caught
    
    def test_get_error_message(self):
        """Test get_error_message method."""
        validator_func = lambda x: x > 0
        rule = ValidationRule("positive", validator_func, "Must be positive")
        
        message = rule.get_error_message(0)
        assert message == "Must be positive"


class TestValidator:
    """Test Validator class."""
    
    def test_validator_init(self):
        """Test Validator initialization."""
        validator = Validator()
        
        assert isinstance(validator._rules, dict)
        assert len(validator._rules) > 0  # Should have default rules
    
    def test_setup_default_rules(self):
        """Test that default rules are set up."""
        validator = Validator()
        
        # Check some default rules exist
        assert "non_empty_string" in validator._rules
        assert "positive_integer" in validator._rules
        assert "positive_float" in validator._rules
        assert "boolean" in validator._rules
        assert "non_empty_list" in validator._rules
        assert "non_empty_dict" in validator._rules
        assert "valid_path" in validator._rules
        assert "valid_url" in validator._rules
    
    def test_add_rule(self):
        """Test add_rule method."""
        validator = Validator()
        validator_func = lambda x: x > 10
        
        validator.add_rule("greater_than_10", validator_func, "Must be greater than 10")
        
        assert "greater_than_10" in validator._rules
        rule = validator._rules["greater_than_10"]
        assert rule.name == "greater_than_10"
        assert rule.validator is validator_func
        assert rule.message == "Must be greater than 10"
    
    def test_remove_rule(self):
        """Test remove_rule method."""
        validator = Validator()
        
        # Add a custom rule
        validator.add_rule("custom_rule", lambda x: True)
        assert "custom_rule" in validator._rules
        
        # Remove it
        validator.remove_rule("custom_rule")
        assert "custom_rule" not in validator._rules
    
    def test_remove_nonexistent_rule(self):
        """Test remove_rule with non-existent rule."""
        validator = Validator()
        
        # Should not raise exception
        validator.remove_rule("nonexistent_rule")
    
    def test_get_rule(self):
        """Test get_rule method."""
        validator = Validator()
        
        # Get existing rule
        rule = validator.get_rule("non_empty_string")
        assert rule is not None
        assert rule.name == "non_empty_string"
        
        # Get non-existent rule
        rule = validator.get_rule("nonexistent")
        assert rule is None
    
    def test_list_rules(self):
        """Test list_rules method."""
        validator = Validator()
        
        rules = validator.list_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0
        assert "non_empty_string" in rules
        assert "positive_integer" in rules
    
    def test_validate_success(self):
        """Test validate method with success."""
        validator = Validator()
        
        assert validator.validate("test", "non_empty_string") is True
        assert validator.validate(5, "positive_integer") is True
        assert validator.validate(3.14, "positive_float") is True
        assert validator.validate(True, "boolean") is True
        assert validator.validate([1, 2, 3], "non_empty_list") is True
        assert validator.validate({"key": "value"}, "non_empty_dict") is True
        assert validator.validate("/path/to/file", "valid_path") is True
        assert validator.validate("https://example.com", "valid_url") is True
    
    def test_validate_failure(self):
        """Test validate method with failure."""
        validator = Validator()
        
        assert validator.validate("", "non_empty_string") is False
        assert validator.validate(-1, "positive_integer") is False
        assert validator.validate(-3.14, "positive_float") is False
        assert validator.validate("not_bool", "boolean") is False
        assert validator.validate([], "non_empty_list") is False
        assert validator.validate({}, "non_empty_dict") is False
        assert validator.validate("", "valid_path") is False
        assert validator.validate("not_a_url", "valid_url") is False
    
    def test_validate_unknown_rule(self):
        """Test validate method with unknown rule."""
        validator = Validator()
        
        with pytest.raises(ValidationError, match="Unknown validation rule: unknown_rule"):
            validator.validate("test", "unknown_rule")
    
    def test_validate_all_success(self):
        """Test validate_all method with success."""
        validator = Validator()
        
        errors = validator.validate_all("test", ["non_empty_string", "valid_path"])
        assert errors == []
    
    def test_validate_all_failure(self):
        """Test validate_all method with failure."""
        validator = Validator()
        
        errors = validator.validate_all("", ["non_empty_string", "valid_path"])
        assert len(errors) == 2
        assert "Value must be a non-empty string" in errors
        assert "Value must be a valid path string" in errors
    
    def test_validate_with_custom_rule_success(self):
        """Test validate_with_custom_rule method with success."""
        validator = Validator()
        
        result = validator.validate_with_custom_rule(5, lambda x: x > 0, "Must be positive")
        assert result is True
    
    def test_validate_with_custom_rule_failure(self):
        """Test validate_with_custom_rule method with failure."""
        validator = Validator()
        
        result = validator.validate_with_custom_rule(-1, lambda x: x > 0, "Must be positive")
        assert result is False
    
    def test_validate_with_custom_rule_exception(self):
        """Test validate_with_custom_rule method with exception."""
        validator = Validator()
        
        def validator_func(x):
            if x == "error":
                raise Exception("Test error")
            return x > 0
        
        result = validator.validate_with_custom_rule("error", validator_func)
        assert result is False
    
    def test_validate_config_simple_success(self):
        """Test validate_config method with simple success."""
        validator = Validator()
        
        config = {
            "name": "test",
            "count": 5,
            "enabled": True
        }
        
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "count": {"rules": ["positive_integer"], "required": True},
            "enabled": {"rules": ["boolean"], "required": True}
        }
        
        errors = validator.validate_config(config, schema)
        assert errors == []
    
    def test_validate_config_simple_failure(self):
        """Test validate_config method with simple failure."""
        validator = Validator()
        
        config = {
            "name": "",
            "count": -1,
            "enabled": "not_bool"
        }
        
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "count": {"rules": ["positive_integer"], "required": True},
            "enabled": {"rules": ["boolean"], "required": True}
        }
        
        errors = validator.validate_config(config, schema)
        assert len(errors) == 3
        assert any("Field 'name': Value must be a non-empty string" in error for error in errors)
        assert any("Field 'count': Value must be a positive integer" in error for error in errors)
        assert any("Field 'enabled': Value must be a boolean" in error for error in errors)
    
    def test_validate_config_missing_required_field(self):
        """Test validate_config method with missing required field."""
        validator = Validator()
        
        config = {
            "name": "test"
        }
        
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "count": {"rules": ["positive_integer"], "required": True}
        }
        
        errors = validator.validate_config(config, schema)
        assert len(errors) == 1
        assert "Required field 'count' is missing" in errors[0]
    
    def test_validate_config_optional_field(self):
        """Test validate_config method with optional field."""
        validator = Validator()
        
        config = {
            "name": "test"
        }
        
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "count": {"rules": ["positive_integer"], "required": False}
        }
        
        errors = validator.validate_config(config, schema)
        assert errors == []
    
    def test_validate_config_nested_object(self):
        """Test validate_config method with nested object."""
        validator = Validator()
        
        config = {
            "name": "test",
            "settings": {
                "timeout": 30,
                "retries": 3
            }
        }
        
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "settings": {
                "type": "object",
                "required": True,
                "properties": {
                    "timeout": {"rules": ["positive_integer"], "required": True},
                    "retries": {"rules": ["positive_integer"], "required": True}
                }
            }
        }
        
        errors = validator.validate_config(config, schema)
        assert errors == []
    
    def test_validate_config_nested_object_failure(self):
        """Test validate_config method with nested object failure."""
        validator = Validator()
        
        config = {
            "name": "test",
            "settings": {
                "timeout": -1,
                "retries": "not_int"
            }
        }
        
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "settings": {
                "type": "object",
                "required": True,
                "properties": {
                    "timeout": {"rules": ["positive_integer"], "required": True},
                    "retries": {"rules": ["positive_integer"], "required": True}
                }
            }
        }
        
        errors = validator.validate_config(config, schema)
        assert len(errors) == 2
        assert any("Field 'settings': Field 'timeout': Value must be a positive integer" in error for error in errors)
        assert any("Field 'settings': Field 'retries': Value must be a positive integer" in error for error in errors)
    
    def test_validate_config_array(self):
        """Test validate_config method with array."""
        validator = Validator()
        
        config = {
            "name": "test",
            "items": [1, 2, 3, 4, 5]
        }
        
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "items": {
                "type": "array",
                "required": True,
                "items": {
                    "rules": ["positive_integer"],
                    "required": True
                }
            }
        }
        
        errors = validator.validate_config(config, schema)
        assert errors == []
    
    def test_validate_config_array_failure(self):
        """Test validate_config method with array failure."""
        validator = Validator()
        
        config = {
            "name": "test",
            "items": [1, -2, 3, "not_int", 5]
        }
        
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "items": {
                "type": "array",
                "required": True,
                "items": {
                    "rules": ["positive_integer"],
                    "required": True
                }
            }
        }
        
        errors = validator.validate_config(config, schema)
        assert len(errors) == 2
        assert any("Field 'items[1]': Value must be a positive integer" in error for error in errors)
        assert any("Field 'items[3]': Value must be a positive integer" in error for error in errors)


class TestGlobalValidator:
    """Test global validator instance and convenience functions."""
    
    def test_global_validator_instance(self):
        """Test global validator instance."""
        assert validator is not None
        assert isinstance(validator, Validator)
    
    def test_validate_value_function(self):
        """Test validate_value convenience function."""
        assert validate_value("test", "non_empty_string") is True
        assert validate_value("", "non_empty_string") is False
    
    def test_validate_config_function(self):
        """Test validate_config convenience function."""
        config = {"name": "test", "count": 5}
        schema = {
            "name": {"rules": ["non_empty_string"], "required": True},
            "count": {"rules": ["positive_integer"], "required": True}
        }
        
        errors = validate_config(config, schema)
        assert errors == []
    
    def test_add_validation_rule_function(self):
        """Test add_validation_rule convenience function."""
        add_validation_rule("even_number", lambda x: x % 2 == 0, "Must be even")
        
        assert "even_number" in validator._rules
        assert validator.validate(4, "even_number") is True
        assert validator.validate(3, "even_number") is False
    
    def test_remove_validation_rule_function(self):
        """Test remove_validation_rule convenience function."""
        add_validation_rule("test_rule", lambda x: True)
        assert "test_rule" in validator._rules
        
        remove_validation_rule("test_rule")
        assert "test_rule" not in validator._rules


class TestDefaultRules:
    """Test default validation rules."""
    
    def test_non_empty_string_rule(self):
        """Test non_empty_string rule."""
        assert validator.validate("test", "non_empty_string") is True
        assert validator.validate("  test  ", "non_empty_string") is True
        assert validator.validate("", "non_empty_string") is False
        assert validator.validate("   ", "non_empty_string") is False
        assert validator.validate(123, "non_empty_string") is False
    
    def test_positive_integer_rule(self):
        """Test positive_integer rule."""
        assert validator.validate(1, "positive_integer") is True
        assert validator.validate(100, "positive_integer") is True
        assert validator.validate(0, "positive_integer") is False
        assert validator.validate(-1, "positive_integer") is False
        assert validator.validate(1.5, "positive_integer") is False
        assert validator.validate("1", "positive_integer") is False
    
    def test_positive_float_rule(self):
        """Test positive_float rule."""
        assert validator.validate(1.0, "positive_float") is True
        assert validator.validate(1, "positive_float") is True
        assert validator.validate(0.1, "positive_float") is True
        assert validator.validate(0, "positive_float") is False
        assert validator.validate(-1.0, "positive_float") is False
        assert validator.validate("1.0", "positive_float") is False
    
    def test_boolean_rule(self):
        """Test boolean rule."""
        assert validator.validate(True, "boolean") is True
        assert validator.validate(False, "boolean") is True
        assert validator.validate(1, "boolean") is False
        assert validator.validate(0, "boolean") is False
        assert validator.validate("true", "boolean") is False
    
    def test_non_empty_list_rule(self):
        """Test non_empty_list rule."""
        assert validator.validate([1, 2, 3], "non_empty_list") is True
        assert validator.validate(["a", "b"], "non_empty_list") is True
        assert validator.validate([], "non_empty_list") is False
        assert validator.validate("not_list", "non_empty_list") is False
    
    def test_non_empty_dict_rule(self):
        """Test non_empty_dict rule."""
        assert validator.validate({"key": "value"}, "non_empty_dict") is True
        assert validator.validate({1: 2, 3: 4}, "non_empty_dict") is True
        assert validator.validate({}, "non_empty_dict") is False
        assert validator.validate("not_dict", "non_empty_dict") is False
    
    def test_valid_path_rule(self):
        """Test valid_path rule."""
        assert validator.validate("/path/to/file", "valid_path") is True
        assert validator.validate("relative/path", "valid_path") is True
        assert validator.validate("", "valid_path") is False
        assert validator.validate("   ", "valid_path") is False
        assert validator.validate(123, "valid_path") is False
    
    def test_valid_url_rule(self):
        """Test valid_url rule."""
        assert validator.validate("http://example.com", "valid_url") is True
        assert validator.validate("https://example.com", "valid_url") is True
        assert validator.validate("ftp://example.com", "valid_url") is False
        assert validator.validate("example.com", "valid_url") is False
        assert validator.validate("", "valid_url") is False
        assert validator.validate(123, "valid_url") is False


class TestComplexValidationScenarios:
    """Test complex validation scenarios."""
    
    def test_nested_validation_complex(self):
        """Test complex nested validation."""
        validator = Validator()
        
        config = {
            "app_name": "MyApp",
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "username": "admin",
                    "password": "secret"
                }
            },
            "features": ["logging", "monitoring", "caching"],
            "settings": {
                "timeout": 30,
                "retries": 3,
                "enabled": True
            }
        }
        
        schema = {
            "app_name": {"rules": ["non_empty_string"], "required": True},
            "database": {
                "type": "object",
                "required": True,
                "properties": {
                    "host": {"rules": ["non_empty_string"], "required": True},
                    "port": {"rules": ["positive_integer"], "required": True},
                    "credentials": {
                        "type": "object",
                        "required": True,
                        "properties": {
                            "username": {"rules": ["non_empty_string"], "required": True},
                            "password": {"rules": ["non_empty_string"], "required": True}
                        }
                    }
                }
            },
            "features": {
                "type": "array",
                "required": True,
                "items": {
                    "rules": ["non_empty_string"],
                    "required": True
                }
            },
            "settings": {
                "type": "object",
                "required": True,
                "properties": {
                    "timeout": {"rules": ["positive_integer"], "required": True},
                    "retries": {"rules": ["positive_integer"], "required": True},
                    "enabled": {"rules": ["boolean"], "required": True}
                }
            }
        }
        
        errors = validator.validate_config(config, schema)
        assert errors == []
    
    def test_validation_with_mixed_types(self):
        """Test validation with mixed data types."""
        validator = Validator()
        
        config = {
            "string_field": "test",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True,
            "list_field": [1, 2, 3],
            "dict_field": {"key": "value"},
            "path_field": "/some/path",
            "url_field": "https://example.com"
        }
        
        schema = {
            "string_field": {"rules": ["non_empty_string"], "required": True},
            "int_field": {"rules": ["positive_integer"], "required": True},
            "float_field": {"rules": ["positive_float"], "required": True},
            "bool_field": {"rules": ["boolean"], "required": True},
            "list_field": {"rules": ["non_empty_list"], "required": True},
            "dict_field": {"rules": ["non_empty_dict"], "required": True},
            "path_field": {"rules": ["valid_path"], "required": True},
            "url_field": {"rules": ["valid_url"], "required": True}
        }
        
        errors = validator.validate_config(config, schema)
        assert errors == []
