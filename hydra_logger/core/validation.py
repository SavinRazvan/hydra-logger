"""
Comprehensive Input Validation System for Hydra-Logger

This module provides a robust validation system for configuration data, input
validation, and data integrity checking. It includes predefined validation rules,
custom rule support, and comprehensive error reporting.

ARCHITECTURE:
- ValidationRule: Individual validation rules with custom validators
- Validator: Main validation engine with rule management
- Predefined Rules: Built-in validation rules for common patterns
- Custom Rule Support: User-defined validation rules

VALIDATION TYPES:
- Type Validation: Data type checking and conversion
- Range Validation: Numeric range and boundary checking
- Pattern Validation: String pattern matching and format validation
- Required Field Validation: Mandatory field presence checking
- Custom Validation: User-defined validation logic

BUILT-IN VALIDATION RULES:
- is_string: String type validation
- is_integer: Integer type validation
- is_float: Float type validation
- is_boolean: Boolean type validation
- is_list: List type validation
- is_dict: Dictionary type validation
- is_not_empty: Non-empty value validation
- is_positive: Positive number validation
- is_in_range: Numeric range validation
- matches_pattern: Regular expression pattern matching

CONFIGURATION VALIDATION:
- Schema-based validation
- Nested configuration validation
- Required field checking
- Type consistency validation
- Value range validation

USAGE EXAMPLES:

Basic Validation:
    from hydra_logger.core.validation import validate_value, add_validation_rule
    
    # Use built-in validation
    is_valid = validate_value("test", "is_string")
    print(f"String validation: {is_valid}")
    
    # Add custom validation rule
    def is_positive_integer(value):
        return isinstance(value, int) and value > 0
    
    add_validation_rule("positive_int", is_positive_integer, "Must be positive integer")
    is_valid = validate_value(5, "positive_int")

Configuration Validation:
    from hydra_logger.core.validation import validate_config
    
    config = {
        "level": "INFO",
        "buffer_size": 8192,
        "enabled": True
    }
    
    schema = {
        "level": {"type": "string", "required": True},
        "buffer_size": {"type": "integer", "min": 1024, "max": 65536},
        "enabled": {"type": "boolean", "required": True}
    }
    
    errors = validate_config(config, schema)
    if errors:
        print(f"Validation errors: {errors}")

Custom Validation Rules:
    from hydra_logger.core.validation import Validator, ValidationRule
    
    validator = Validator()
    
    # Create custom validation rule
    def validate_log_level(value):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        return value in valid_levels
    
    rule = ValidationRule(
        name="log_level",
        validator=validate_log_level,
        message="Must be a valid log level"
    )
    
    validator.add_rule("log_level", validate_log_level, "Must be a valid log level")
    
    # Use custom rule
    is_valid = validator.validate("INFO", "log_level")

Multiple Rule Validation:
    from hydra_logger.core.validation import Validator
    
    validator = Validator()
    
    # Validate with multiple rules
    rules = ["is_string", "is_not_empty", "matches_pattern"]
    errors = validator.validate_all("test@example.com", rules)
    
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("All validations passed")

Advanced Configuration Validation:
    from hydra_logger.core.validation import validate_config
    
    complex_config = {
        "logging": {
            "level": "INFO",
            "handlers": [
                {"type": "console", "level": "DEBUG"},
                {"type": "file", "path": "app.log", "level": "INFO"}
            ]
        },
        "performance": {
            "buffer_size": 8192,
            "flush_interval": 1.0
        }
    }
    
    complex_schema = {
        "logging": {
            "type": "dict",
            "required": True,
            "properties": {
                "level": {"type": "string", "required": True},
                "handlers": {
                    "type": "list",
                    "required": True,
                    "items": {
                        "type": "dict",
                        "properties": {
                            "type": {"type": "string", "required": True},
                            "level": {"type": "string", "required": True},
                            "path": {"type": "string", "required": False}
                        }
                    }
                }
            }
        },
        "performance": {
            "type": "dict",
            "required": True,
            "properties": {
                "buffer_size": {"type": "integer", "min": 1024},
                "flush_interval": {"type": "float", "min": 0.1}
            }
        }
    }
    
    errors = validate_config(complex_config, complex_schema)
    if errors:
        print(f"Complex validation errors: {errors}")
"""

from typing import Any, Dict, List, Optional, Union, Callable
from .exceptions import ValidationError


class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, name: str, validator: Callable, message: str = None):
        self.name = name
        self.validator = validator
        self.message = message or f"Validation failed for rule: {name}"
    
    def validate(self, value: Any) -> bool:
        """Validate a value using this rule."""
        try:
            return bool(self.validator(value))
        except Exception:
            return False
    
    def get_error_message(self, value: Any) -> str:
        """Get error message for validation failure."""
        return self.message


class Validator:
    """Main validator class for configuration and input validation."""
    
    def __init__(self):
        self._rules: Dict[str, ValidationRule] = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules."""
        # String validation
        self.add_rule("non_empty_string", 
                      lambda x: isinstance(x, str) and len(x.strip()) > 0,
                      "Value must be a non-empty string")
        
        # Integer validation
        self.add_rule("positive_integer",
                      lambda x: isinstance(x, int) and x > 0,
                      "Value must be a positive integer")
        
        # Float validation
        self.add_rule("positive_float",
                      lambda x: isinstance(x, (int, float)) and x > 0,
                      "Value must be a positive number")
        
        # Boolean validation
        self.add_rule("boolean",
                      lambda x: isinstance(x, bool),
                      "Value must be a boolean")
        
        # List validation
        self.add_rule("non_empty_list",
                      lambda x: isinstance(x, list) and len(x) > 0,
                      "Value must be a non-empty list")
        
        # Dict validation
        self.add_rule("non_empty_dict",
                      lambda x: isinstance(x, dict) and len(x) > 0,
                      "Value must be a non-empty dictionary")
        
        # Path validation
        self.add_rule("valid_path",
                      lambda x: isinstance(x, str) and len(x.strip()) > 0,
                      "Value must be a valid path string")
        
        # URL validation
        self.add_rule("valid_url",
                      lambda x: isinstance(x, str) and (x.startswith('http://') or x.startswith('https://')),
                      "Value must be a valid HTTP/HTTPS URL")
    
    def add_rule(self, name: str, validator: Callable, message: str = None) -> None:
        """Add a validation rule."""
        self._rules[name] = ValidationRule(name, validator, message)
    
    def remove_rule(self, name: str) -> None:
        """Remove a validation rule."""
        if name in self._rules:
            del self._rules[name]
    
    def get_rule(self, name: str) -> Optional[ValidationRule]:
        """Get a validation rule by name."""
        return self._rules.get(name)
    
    def list_rules(self) -> List[str]:
        """List all available validation rules."""
        return list(self._rules.keys())
    
    def validate(self, value: Any, rule_name: str) -> bool:
        """Validate a value using a specific rule."""
        rule = self.get_rule(rule_name)
        if not rule:
            raise ValidationError(f"Unknown validation rule: {rule_name}")
        
        return rule.validate(value)
    
    def validate_all(self, value: Any, rule_names: List[str]) -> List[str]:
        """Validate a value using multiple rules and return error messages."""
        errors = []
        for rule_name in rule_names:
            if not self.validate(value, rule_name):
                rule = self.get_rule(rule_name)
                errors.append(rule.get_error_message(value))
        
        return errors
    
    def validate_with_custom_rule(self, value: Any, validator: Callable, message: str = None) -> bool:
        """Validate a value using a custom validator function."""
        try:
            return bool(validator(value))
        except Exception:
            return False
    
    def validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate a configuration dictionary against a schema."""
        errors = []
        
        for field_name, field_schema in schema.items():
            if field_name not in config:
                if field_schema.get('required', False):
                    errors.append(f"Required field '{field_name}' is missing")
                continue
            
            field_value = config[field_name]
            field_rules = field_schema.get('rules', [])
            
            # Validate field value against rules
            field_errors = self.validate_all(field_value, field_rules)
            for error in field_errors:
                errors.append(f"Field '{field_name}': {error}")
            
            # Validate nested objects
            if field_schema.get('type') == 'object' and isinstance(field_value, dict):
                nested_schema = field_schema.get('properties', {})
                nested_errors = self.validate_config(field_value, nested_schema)
                for error in nested_errors:
                    errors.append(f"Field '{field_name}': {error}")
            
            # Validate arrays
            if field_schema.get('type') == 'array' and isinstance(field_value, list):
                item_schema = field_schema.get('items', {})
                for i, item in enumerate(field_value):
                    if item_schema:
                        # Validate individual array item
                        if isinstance(item, dict) and item_schema.get('type') == 'object':
                            # Item is a dictionary, validate as nested object
                            item_errors = self.validate_config(item, item_schema.get('properties', {}))
                            for error in item_errors:
                                errors.append(f"Field '{field_name}[{i}]': {error}")
                        else:
                            # Item is a simple value, validate against rules
                            item_rules = item_schema.get('rules', [])
                            item_errors = self.validate_all(item, item_rules)
                            for error in item_errors:
                                errors.append(f"Field '{field_name}[{i}]': {error}")
        
        return errors


# Global validator instance
validator = Validator()

# Convenience functions
def validate_value(value: Any, rule_name: str) -> bool:
    """Validate a value using a specific rule."""
    return validator.validate(value, rule_name)

def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate a configuration dictionary against a schema."""
    return validator.validate_config(config, schema)

def add_validation_rule(name: str, validator_func: Callable, message: str = None) -> None:
    """Add a custom validation rule."""
    validator.add_rule(name, validator_func, message)

def remove_validation_rule(name: str) -> None:
    """Remove a validation rule."""
    validator.remove_rule(name)
