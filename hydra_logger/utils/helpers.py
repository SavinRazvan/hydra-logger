"""
General Helper Functions for Hydra-Logger

This module provides comprehensive helper functions for data manipulation,
mathematical operations, collection handling, and object management.
It includes utilities for common operations and data transformations.

FEATURES:
- GeneralHelpers: ID generation, hashing, data validation
- DataHelpers: Type detection, conversion, validation, sanitization
- MathHelpers: Mathematical operations and calculations
- CollectionHelpers: List and collection manipulation
- ObjectHelpers: Object introspection and manipulation
- Data type detection and conversion
- Dictionary and list operations
- String and number utilities

HELPER CATEGORIES:
- General: ID generation, UUID creation, string hashing
- Data: Type detection, data conversion, validation
- Math: Rounding, clamping, normalization, percentages
- Collections: Chunking, deduplication, grouping, filtering
- Objects: Attribute access, method discovery, comparison

USAGE:
    from hydra_logger.utils import GeneralHelpers, DataHelpers, MathHelpers
    
    # General utilities
    id = GeneralHelpers.generate_id(length=8)
    uuid = GeneralHelpers.generate_uuid()
    hash_value = GeneralHelpers.hash_string("text", "sha256")
    
    # Data manipulation
    data_type = DataHelpers.detect_type(value)
    converted = DataHelpers.convert_type(value, DataType.STRING)
    is_valid, errors = DataHelpers.validate_data(data, schema)
    
    # Math operations
    rounded = MathHelpers.round_to_precision(3.14159, 2)
    clamped = MathHelpers.clamp(value, 0, 100)
    percentage = MathHelpers.calculate_percentage(25, 100)
    
    # Collection operations
    from hydra_logger.utils import CollectionHelpers
    chunks = CollectionHelpers.chunk_list(items, 10)
    unique = CollectionHelpers.remove_duplicates(items)
    grouped = CollectionHelpers.group_by(items, key_func)
"""

import random
import string
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Callable, TypeVar
from dataclasses import asdict
from enum import Enum
from collections import defaultdict
import uuid


T = TypeVar('T')


class DataType(Enum):
    """Data type categories."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    OBJECT = "object"
    NONE = "none"
    UNKNOWN = "unknown"


class GeneralHelpers:
    """General utility helper functions."""

    @staticmethod
    def generate_id(length: int = 8, prefix: str = "") -> str:
        """Generate a random ID string."""
        chars = string.ascii_letters + string.digits
        random_id = ''.join(random.choice(chars) for _ in range(length))
        return f"{prefix}{random_id}" if prefix else random_id

    @staticmethod
    def generate_uuid() -> str:
        """Generate a UUID string."""
        return str(uuid.uuid4())

    @staticmethod
    def hash_string(text: str, algorithm: str = "sha256") -> str:
        """Hash a string using specified algorithm."""
        hash_func = getattr(hashlib, algorithm)
        return hash_func(text.encode()).hexdigest()

    @staticmethod
    def is_empty(value: Any) -> bool:
        """Check if value is empty."""
        if value is None:
            return True
        elif isinstance(value, (str, list, tuple, dict, set)):
            return len(value) == 0
        elif isinstance(value, (int, float)):
            return value == 0
        elif isinstance(value, bool):
            return not value
        else:
            return False

    @staticmethod
    def is_not_empty(value: Any) -> bool:
        """Check if value is not empty."""
        return not GeneralHelpers.is_empty(value)

    @staticmethod
    def safe_get(obj: Any, key: str, default: Any = None) -> Any:
        """Safely get value from object/dict."""
        try:
            if isinstance(obj, dict):
                return obj.get(key, default)
            elif hasattr(obj, key):
                return getattr(obj, key, default)
            else:
                return default
        except Exception:
            return default

    @staticmethod
    def safe_set(obj: Any, key: str, value: Any) -> bool:
        """Safely set value in object/dict."""
        try:
            if isinstance(obj, dict):
                obj[key] = value
                return True
            elif hasattr(obj, key):
                setattr(obj, key, value)
                return True
            else:
                return False
        except Exception:
            return False

    @staticmethod
    def deep_copy(obj: Any) -> Any:
        """Create a deep copy of an object."""
        try:
            return json.loads(json.dumps(obj))
        except Exception:
            # Fallback for non-serializable objects
            return obj

    @staticmethod
    def flatten_dict(
        d: Dict[str, Any], parent_key: str = '', sep: str = '.'
    ) -> Dict[str, Any]:
        """Flatten a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(
                    GeneralHelpers.flatten_dict(v, new_key, sep=sep).items()
                )
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
        """Unflatten a flattened dictionary."""
        result = {}
        for key, value in d.items():
            keys = key.split(sep)
            current = result
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        return result

    @staticmethod
    def merge_dicts(*dicts: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """Merge multiple dictionaries."""
        if not dicts:
            return {}

        result = dicts[0].copy()

        for d in dicts[1:]:
            for key, value in d.items():
                if (deep and key in result and isinstance(result[key], dict) and
                        isinstance(value, dict)):
                    result[key] = GeneralHelpers.merge_dicts(
                        result[key], value, deep=True
                    )
                else:
                    result[key] = value

        return result

    @staticmethod
    def filter_dict(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """Filter dictionary to include only specified keys."""
        return {k: v for k, v in d.items() if k in keys}

    @staticmethod
    def exclude_dict(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """Filter dictionary to exclude specified keys."""
        return {k: v for k, v in d.items() if k not in keys}

    @staticmethod
    def rename_dict_keys(
        d: Dict[str, Any], key_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Rename dictionary keys according to mapping."""
        result = {}
        for old_key, value in d.items():
            new_key = key_mapping.get(old_key, old_key)
            result[new_key] = value
        return result


class DataHelpers:
    """Data manipulation helper functions."""

    @staticmethod
    def detect_type(value: Any) -> DataType:
        """Detect the type of a value."""
        if value is None:
            return DataType.NONE
        elif isinstance(value, str):
            return DataType.STRING
        elif isinstance(value, (int, float)):
            return DataType.NUMBER
        elif isinstance(value, bool):
            return DataType.BOOLEAN
        elif isinstance(value, (list, tuple)):
            return DataType.LIST
        elif isinstance(value, dict):
            return DataType.DICT
        elif hasattr(value, '__dict__'):
            return DataType.OBJECT
        else:
            return DataType.UNKNOWN

    @staticmethod
    def convert_type(value: Any, target_type: DataType) -> Any:
        """Convert value to target type."""
        try:
            if target_type == DataType.STRING:
                return str(value)
            elif target_type == DataType.NUMBER:
                if isinstance(value, bool):
                    return 1 if value else 0
                return float(value)
            elif target_type == DataType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif target_type == DataType.LIST:
                if isinstance(value, (str, bytes)):
                    return list(value)
                elif (hasattr(value, '__iter__') and
                      not isinstance(value, (dict, str))):
                    return list(value)
                else:
                    return [value]
            elif target_type == DataType.DICT:
                if isinstance(value, dict):
                    return value
                elif hasattr(value, '__dict__'):
                    return asdict(value)
                else:
                    return {'value': value}
            else:
                return value
        except Exception:
            return value

    @staticmethod
    def validate_data(
        data: Any, schema: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate data against a schema."""
        errors = []

        if not isinstance(schema, dict):
            return False, ["Invalid schema format"]

        for field, rules in schema.items():
            if field not in data:
                if rules.get('required', False):
                    errors.append(f"Required field '{field}' is missing")
                continue

            value = data[field]
            field_type = rules.get('type')

            if field_type:
                expected_type = DataType(field_type)
                actual_type = DataHelpers.detect_type(value)

                if actual_type != expected_type:
                    errors.append(
                        f"Field '{field}' should be {field_type}, "
                        f"got {actual_type.value}"
                    )

            # Validate range for numbers
            if isinstance(value, (int, float)):
                if 'min' in rules and value < rules['min']:
                    errors.append(
                        f"Field '{field}' value {value} is below "
                        f"minimum {rules['min']}"
                    )
                if 'max' in rules and value > rules['max']:
                    errors.append(
                        f"Field '{field}' value {value} is above "
                        f"maximum {rules['max']}"
                    )

            # Validate length for strings/lists
            if isinstance(value, (str, list)):
                if 'min_length' in rules and len(value) < rules['min_length']:
                    errors.append(
                        f"Field '{field}' length {len(value)} is below "
                        f"minimum {rules['min_length']}"
                    )
                if 'max_length' in rules and len(value) > rules['max_length']:
                    errors.append(
                        f"Field '{field}' length {len(value)} is above "
                        f"maximum {rules['max_length']}"
                    )

            # Validate pattern for strings
            if isinstance(value, str) and 'pattern' in rules:
                if not re.match(rules['pattern'], value):
                    errors.append(
                        f"Field '{field}' value does not match "
                        f"pattern {rules['pattern']}"
                    )

        return len(errors) == 0, errors

    @staticmethod
    def sanitize_data(data: Any, sensitive_fields: List[str] = None) -> Any:
        """Sanitize sensitive data."""
        if sensitive_fields is None:
            sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']

        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = DataHelpers.sanitize_data(
                        value, sensitive_fields
                    )
            return sanitized
        elif isinstance(data, list):
            return [DataHelpers.sanitize_data(item, sensitive_fields)
                    for item in data]
        else:
            return data

    @staticmethod
    def mask_sensitive_data(
        data: Any, sensitive_fields: List[str] = None, mask_char: str = '*'
    ) -> Any:
        """Mask sensitive data with specified character."""
        if sensitive_fields is None:
            sensitive_fields = ['password', 'token', 'secret', 'key', 'auth']

        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    if isinstance(value, str):
                        masked[key] = mask_char * len(value)
                    else:
                        masked[key] = mask_char * 8
                else:
                    masked[key] = DataHelpers.mask_sensitive_data(
                        value, sensitive_fields, mask_char
                    )
            return masked
        elif isinstance(data, list):
            return [DataHelpers.mask_sensitive_data(
                item, sensitive_fields, mask_char
            ) for item in data]
        else:
            return data


class MathHelpers:
    """Mathematical helper functions."""

    @staticmethod
    def round_to_precision(value: float, precision: int = 2) -> float:
        """Round value to specified precision."""
        return round(value, precision)

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max."""
        return max(min_val, min(value, max_val))

    @staticmethod
    def normalize(value: float, min_val: float, max_val: float) -> float:
        """Normalize value to range [0, 1]."""
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)

    @staticmethod
    def denormalize(value: float, min_val: float, max_val: float) -> float:
        """Denormalize value from range [0, 1] to [min_val, max_val]."""
        return value * (max_val - min_val) + min_val

    @staticmethod
    def is_between(value: float, min_val: float, max_val: float) -> bool:
        """Check if value is between min and max (inclusive)."""
        return min_val <= value <= max_val

    @staticmethod
    def calculate_percentage(part: float, total: float) -> float:
        """Calculate percentage."""
        if total == 0:
            return 0.0
        return (part / total) * 100

    @staticmethod
    def calculate_ratio(part: float, total: float) -> float:
        """Calculate ratio."""
        if total == 0:
            return 0.0
        return part / total


class CollectionHelpers:
    """Collection manipulation helper functions."""

    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split list into chunks of specified size."""
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    def remove_duplicates(items: List[Any], preserve_order: bool = True) -> List[Any]:
        """Remove duplicate items from list."""
        if preserve_order:
            seen = set()
            result = []
            for item in items:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
        else:
            return list(set(items))

    @staticmethod
    def group_by(items: List[Any], key_func: Callable) -> Dict[Any, List[Any]]:
        """Group items by key function."""
        grouped = defaultdict(list)
        for item in items:
            key = key_func(item)
            grouped[key].append(item)
        return dict(grouped)

    @staticmethod
    def sort_by_multiple(
        items: List[Any], key_funcs: List[Callable], reverse: bool = False
    ) -> List[Any]:
        """Sort items by multiple key functions."""
        def multi_key(item):
            return tuple(key_func(item) for key_func in key_funcs)

        return sorted(items, key=multi_key, reverse=reverse)

    @staticmethod
    def filter_by_condition(items: List[Any], condition: Callable) -> List[Any]:
        """Filter items by condition function."""
        return [item for item in items if condition(item)]

    @staticmethod
    def transform_items(items: List[Any], transform_func: Callable) -> List[Any]:
        """Transform items using transform function."""
        return [transform_func(item) for item in items]

    @staticmethod
    def find_item(items: List[Any], condition: Callable) -> Optional[Any]:
        """Find first item matching condition."""
        for item in items:
            if condition(item):
                return item
        return None

    @staticmethod
    def find_all_items(items: List[Any], condition: Callable) -> List[Any]:
        """Find all items matching condition."""
        return [item for item in items if condition(item)]

    @staticmethod
    def count_by_condition(items: List[Any], condition: Callable) -> int:
        """Count items matching condition."""
        return sum(1 for item in items if condition(item))

    @staticmethod
    def any_match(items: List[Any], condition: Callable) -> bool:
        """Check if any item matches condition."""
        return any(condition(item) for item in items)

    @staticmethod
    def all_match(items: List[Any], condition: Callable) -> bool:
        """Check if all items match condition."""
        return all(condition(item) for item in items)


class ObjectHelpers:
    """Object manipulation helper functions."""

    @staticmethod
    def get_object_attributes(obj: Any) -> Dict[str, Any]:
        """Get all attributes of an object."""
        if hasattr(obj, '__dict__'):
            return obj.__dict__.copy()
        elif hasattr(obj, '__slots__'):
            return {attr: getattr(obj, attr, None) for attr in obj.__slots__}
        else:
            return {}

    @staticmethod
    def set_object_attributes(obj: Any, attributes: Dict[str, Any]) -> bool:
        """Set multiple attributes on an object."""
        try:
            for key, value in attributes.items():
                setattr(obj, key, value)
            return True
        except Exception:
            return False

    @staticmethod
    def has_attributes(obj: Any, attributes: List[str]) -> bool:
        """Check if object has all specified attributes."""
        return all(hasattr(obj, attr) for attr in attributes)

    @staticmethod
    def get_methods(obj: Any) -> List[str]:
        """Get all method names of an object."""
        return [name for name in dir(obj)
                if callable(getattr(obj, name)) and not name.startswith('_')]

    @staticmethod
    def is_callable(obj: Any) -> bool:
        """Check if object is callable."""
        return callable(obj)

    @staticmethod
    def get_class_hierarchy(obj: Any) -> List[str]:
        """Get class hierarchy of an object."""
        hierarchy = []
        current_class = obj.__class__

        while current_class:
            hierarchy.append(current_class.__name__)
            current_class = (current_class.__bases__[0]
                             if current_class.__bases__ else None)

        return hierarchy

    @staticmethod
    def create_instance(class_name: str, *args, **kwargs) -> Any:
        """Create instance of class by name."""
        try:
            # Try to get class from globals
            if class_name in globals():
                cls = globals()[class_name]
                return cls(*args, **kwargs)
            else:
                raise ValueError(f"Class '{class_name}' not found")
        except Exception as e:
            raise ValueError(f"Cannot create instance of '{class_name}': {e}")

    @staticmethod
    def copy_object(obj: Any, deep: bool = False) -> Any:
        """Copy an object."""
        if deep:
            return GeneralHelpers.deep_copy(obj)
        else:
            if hasattr(obj, 'copy'):
                return obj.copy()
            elif hasattr(obj, '__copy__'):
                return obj.__copy__()
            else:
                return obj

    @staticmethod
    def compare_objects(obj1: Any, obj2: Any, ignore_private: bool = True) -> bool:
        """Compare two objects for equality."""
        if obj1 is obj2:
            return True

        if not isinstance(obj1, type(obj2)):
            return False

        if hasattr(obj1, '__eq__'):
            return obj1 == obj2

        # Compare attributes
        attrs1 = ObjectHelpers.get_object_attributes(obj1)
        attrs2 = ObjectHelpers.get_object_attributes(obj2)

        if ignore_private:
            attrs1 = {k: v for k, v in attrs1.items()
                      if not k.startswith('_')}
            attrs2 = {k: v for k, v in attrs2.items()
                      if not k.startswith('_')}

        return attrs1 == attrs2
