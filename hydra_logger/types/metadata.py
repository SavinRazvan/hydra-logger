"""
Metadata Types for Hydra-Logger

This module provides comprehensive metadata type definitions for managing
additional information associated with log records. It includes metadata
containers, validation schemas, and field definitions for structured
data handling.

FEATURES:
- LogMetadata: Main metadata container with key-value storage
- MetadataSchema: Schema definition for metadata validation
- MetadataField: Field definition with type validation
- Metadata management utilities and convenience functions

METADATA CONTAINER:
- Key-value storage with type safety
- Metadata classification and prioritization
- Source tracking and validation status
- Encryption and checksum support
- Dictionary-like interface for easy access

SCHEMA VALIDATION:
- Field type validation and constraints
- Required and optional field definitions
- Custom validator functions
- Schema-based metadata validation

FIELD DEFINITIONS:
- Type checking and validation
- Default value support
- Custom validator functions
- Field description and documentation

USAGE:
    from hydra_logger.types import LogMetadata, MetadataSchema, MetadataField
    
    # Create metadata container
    metadata = LogMetadata(
        category="user_action",
        priority=1,
        source="auth_service"
    )
    
    # Add metadata
    metadata.set("user_id", "12345")
    metadata.set("action", "login")
    metadata.set("ip_address", "192.168.1.1")
    
    # Get metadata
    user_id = metadata.get("user_id")
    if metadata.has("action"):
        action = metadata.get("action")
    
    # Create schema for validation
    schema = MetadataSchema(
        name="user_action_schema",
        fields={
            "user_id": MetadataField("user_id", str, description="User identifier"),
            "action": MetadataField("action", str, description="Action performed"),
            "timestamp": MetadataField("timestamp", float, description="Action timestamp")
        },
        required_fields=["user_id", "action"]
    )
    
    # Validate metadata against schema
    if schema.validate(metadata):
        print("Metadata is valid")
    
    # Merge metadata
    from hydra_logger.types import merge_metadata
    merged = merge_metadata(metadata1, metadata2, metadata3)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
import time


@dataclass
class LogMetadata:
    """Container for log metadata information."""
    
    # Core metadata
    metadata_id: str = field(default_factory=lambda: f"meta_{int(time.time() * 1000)}")
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # Metadata content
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata classification
    category: str = "general"
    priority: int = 0  # Higher numbers = higher priority
    
    # Metadata source
    source: Optional[str] = None
    source_type: str = "unknown"
    
    # Validation and security
    validated: bool = False
    encrypted: bool = False
    checksum: Optional[str] = None
    
    def __post_init__(self):
        """Initialize metadata after creation."""
        self.updated_at = self.created_at
    
    def set(self, key: str, value: Any) -> None:
        """Set a metadata value."""
        self.data[key] = value
        self.updated_at = time.time()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a metadata value."""
        return self.data.get(key, default)
    
    def has(self, key: str) -> bool:
        """Check if metadata key exists."""
        return key in self.data
    
    def remove(self, key: str) -> Any:
        """Remove a metadata key and return its value."""
        self.updated_at = time.time()
        return self.data.pop(key, None)
    
    def clear(self) -> None:
        """Clear all metadata."""
        self.data.clear()
        self.updated_at = time.time()
    
    def update(self, metadata: Dict[str, Any]) -> None:
        """Update metadata with new values."""
        self.data.update(metadata)
        self.updated_at = time.time()
    
    def merge(self, other: 'LogMetadata') -> None:
        """Merge metadata from another LogMetadata instance."""
        self.update(other.data)
        if other.category != "general":
            self.category = other.category
        if other.priority > self.priority:
            self.priority = other.priority
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'metadata_id': self.metadata_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'data': self.data,
            'category': self.category,
            'priority': self.priority,
            'source': self.source,
            'source_type': self.source_type,
            'validated': self.validated,
            'encrypted': self.encrypted,
            'checksum': self.checksum
        }
    
    def __len__(self) -> int:
        """Return number of metadata items."""
        return len(self.data)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in metadata."""
        return key in self.data
    
    def __getitem__(self, key: str) -> Any:
        """Get metadata value by key."""
        return self.data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set metadata value by key."""
        self.set(key, value)


@dataclass
class MetadataSchema:
    """Schema definition for metadata validation."""
    
    name: str
    version: str = "1.0"
    fields: Dict[str, 'MetadataField'] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize schema after creation."""
        if not self.optional_fields:
            self.optional_fields = [f for f in self.fields.keys() 
                                  if f not in self.required_fields]
    
    def validate(self, metadata: LogMetadata) -> bool:
        """Validate metadata against schema."""
        # Check required fields
        for field_name in self.required_fields:
            if not metadata.has(field_name):
                return False
        
        # Validate field types and values
        for field_name, field_def in self.fields.items():
            if metadata.has(field_name):
                if not field_def.validate(metadata.get(field_name)):
                    return False
        
        return True
    
    def add_field(self, field_name: str, field_def: 'MetadataField', 
                  required: bool = False) -> None:
        """Add a field to the schema."""
        self.fields[field_name] = field_def
        if required:
            self.required_fields.append(field_name)
        else:
            self.optional_fields.append(field_name)
    
    def remove_field(self, field_name: str) -> None:
        """Remove a field from the schema."""
        if field_name in self.fields:
            del self.fields[field_name]
            if field_name in self.required_fields:
                self.required_fields.remove(field_name)
            if field_name in self.optional_fields:
                self.optional_fields.remove(field_name)


@dataclass
class MetadataField:
    """Definition of a metadata field."""
    
    name: str
    field_type: type
    default_value: Any = None
    validator: Optional[callable] = None
    description: Optional[str] = None
    
    def validate(self, value: Any) -> bool:
        """Validate a field value."""
        # Type check
        if not isinstance(value, self.field_type):
            return False
        
        # Custom validator
        if self.validator and not self.validator(value):
            return False
        
        return True
    
    def get_default(self) -> Any:
        """Get the default value for this field."""
        return self.default_value


# Convenience functions
def create_metadata(data: Optional[Dict[str, Any]] = None, 
                   category: str = "general",
                   source: Optional[str] = None) -> LogMetadata:
    """Create a new LogMetadata instance."""
    metadata = LogMetadata(category=category, source=source)
    if data:
        metadata.update(data)
    return metadata


def merge_metadata(*metadata_list: LogMetadata) -> LogMetadata:
    """Merge multiple metadata instances into one."""
    if not metadata_list:
        return create_metadata()
    
    result = metadata_list[0].copy()
    for metadata in metadata_list[1:]:
        result.merge(metadata)
    
    return result


# Export the main classes and functions
__all__ = [
    "LogMetadata",
    "MetadataSchema", 
    "MetadataField",
    "create_metadata",
    "merge_metadata"
]
