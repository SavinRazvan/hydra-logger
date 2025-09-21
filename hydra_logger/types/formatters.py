"""
Formatting Configuration Types for Hydra-Logger

This module provides comprehensive configuration models for the centralized
formatting system, including column definitions, templates, and formatting
options. It supports both modern centralized formatting and legacy
formatter configurations for backward compatibility.

FEATURES:
- LogColumn: Available log columns for formatting
- ColumnTemplates: Predefined column sets for common use cases
- FormattingConfig: Centralized formatting engine configuration
- TimestampFormat: Timestamp formatting options
- FilenameFormat: Filename display formatting
- FormatterConfig: Legacy formatter configuration
- FormatOptions: Formatting options and customization
- ColorScheme: Color scheme for console output
- FormatTemplate: Template system for log formatting
- FormatResult: Result of formatting operations

COLUMN TEMPLATES:
- minimal(): Timestamp, level, message
- standard(): Standard logging columns
- detailed(): All core fields
- preferred_default(): Custom default columns
- multi_agent(): All fields for multi-agent systems
- custom(): Custom column selection

FORMATTING OPTIONS:
- Text formatting: Case, alignment, width, truncation
- Number formatting: Decimal, hex, octal, binary
- Date/time options: Relative time, timezone, 24-hour format
- Special options: HTML/JSON/CSV escaping, whitespace normalization
- Color options: Console color schemes and customization

USAGE:
    from hydra_logger.types import (
        LogColumn, ColumnTemplates, FormattingConfig, 
        TimestampFormat, FilenameFormat
    )
    
    # Create formatting configuration
    config = FormattingConfig(
        enabled_columns=ColumnTemplates.standard(),
        timestamp_format=TimestampFormat(
            format_type="ISO",
            include_milliseconds=True
        ),
        filename_format=FilenameFormat(
            format_type="filename_only"
        )
    )
    
    # Use column templates
    minimal_cols = ColumnTemplates.minimal()
    detailed_cols = ColumnTemplates.detailed()
    
    # Create custom column set
    custom_cols = ColumnTemplates.custom(
        LogColumn.TIMESTAMP,
        LogColumn.LEVEL,
        LogColumn.AGENT_ID,
        LogColumn.MESSAGE
    )
    
    # Legacy formatter configuration
    from hydra_logger.types import FormatterConfig, FormatOptions
    formatter_config = FormatterConfig(
        formatter_type="json",
        format_string="[{timestamp}] [{level}] {message}",
        include_timestamp=True,
        include_level=True
    )
"""

from enum import Enum
from typing import Set, Optional, Literal, Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import time
from pydantic import BaseModel, Field, field_validator


# NEW: Centralized formatting system
class LogColumn(Enum):
    """Available log columns for formatting."""

    # Core fields (existing)
    TIMESTAMP = "timestamp"
    LEVEL = "level"
    MESSAGE = "message"
    LAYER = "layer"
    FILENAME = "filename"
    FUNCTION_NAME = "function_name"
    LINE_NUMBER = "line_number"
    THREAD_ID = "thread_id"
    PROCESS_ID = "process_id"

    # NEW: Multi-agent fields
    AGENT_ID = "agent_id"
    USER_ID = "user_id"
    REQUEST_ID = "request_id"
    CORRELATION_ID = "correlation_id"
    ENVIRONMENT = "environment"
    EVENT_ID = "event_id"
    DEVICE_ID = "device_id"


class ColumnTemplates:
    """Predefined column sets for common use cases."""

    @staticmethod
    def minimal() -> Set[LogColumn]:
        """Minimal logging: timestamp, level, message"""
        return {LogColumn.TIMESTAMP, LogColumn.LEVEL, LogColumn.MESSAGE}

    @staticmethod
    def standard() -> Set[LogColumn]:
        """Standard logging: your preferred default columns"""
        return {LogColumn.TIMESTAMP, LogColumn.LEVEL, LogColumn.LAYER,
                LogColumn.MESSAGE, LogColumn.FILENAME, LogColumn.FUNCTION_NAME}

    @staticmethod
    def detailed() -> Set[LogColumn]:
        """Detailed logging: all core fields"""
        return {LogColumn.TIMESTAMP, LogColumn.LEVEL, LogColumn.MESSAGE,
                LogColumn.LAYER, LogColumn.FILENAME, LogColumn.FUNCTION_NAME,
                LogColumn.LINE_NUMBER, LogColumn.THREAD_ID,
                LogColumn.PROCESS_ID}

    @staticmethod
    def preferred_default() -> Set[LogColumn]:
        """Your preferred default: timestamp, level, layer, filename, function_name, message"""
        return {LogColumn.TIMESTAMP, LogColumn.LEVEL, LogColumn.LAYER,
                LogColumn.FILENAME, LogColumn.FUNCTION_NAME, LogColumn.MESSAGE}

    @staticmethod
    def multi_agent() -> Set[LogColumn]:
        """Multi-agent system logging: all fields"""
        return set(LogColumn)

    @staticmethod
    def custom(*columns: LogColumn) -> Set[LogColumn]:
        """Custom column selection"""
        return set(columns)


class TimestampFormat(BaseModel):
    """Timestamp formatting configuration."""

    format_type: Literal["EU", "ISO", "UNIX", "CUSTOM"] = Field(
        default="EU", description="Timestamp format type"
    )
    custom_format: Optional[str] = Field(
        default=None, description="Custom strftime format string"
    )
    include_milliseconds: bool = Field(
        default=False, description="Include milliseconds in timestamp"
    )


class FilenameFormat(BaseModel):
    """Filename formatting configuration."""

    format_type: Literal["filename_only", "relative_path",
                         "absolute_path"] = Field(
        default="filename_only", description="Filename display format"
    )
    base_path: Optional[str] = Field(
        default=None, description="Base path for relative path calculation"
    )


class FormattingConfig(BaseModel):
    """Configuration for the formatting engine."""
    
    enabled_columns: Set[LogColumn] = Field(
        description="Set of columns to enable in formatting"
    )
    
    ordered_columns: Optional[List[LogColumn]] = Field(
        default=None,
        description="Optional ordered list of columns. If provided, this order will be used instead of the default order."
    )
    
    timestamp_format: TimestampFormat = Field(
        default_factory=TimestampFormat,
        description="Timestamp formatting configuration"
    )
    
    filename_format: FilenameFormat = Field(
        default_factory=FilenameFormat,
        description="Filename formatting configuration"
    )
    
    enable_caching: bool = Field(
        default=True,
        description="Enable formatting result caching"
    )
    
    cache_size: int = Field(
        default=1000,
        description="Maximum number of cached formatting results"
    )
    
    @field_validator('enabled_columns')
    def validate_required_columns(cls, v):
        """Ensure required columns are always enabled."""
        required = {LogColumn.TIMESTAMP, LogColumn.LEVEL, LogColumn.MESSAGE}
        if not required.issubset(v):
            raise ValueError(f"Required columns {required} must always be enabled")
        return v
    
    @field_validator('ordered_columns')
    def validate_ordered_columns(cls, v, info):
        """Validate that ordered_columns is a subset of enabled_columns."""
        if v is not None:
            enabled = info.data.get('enabled_columns', set())
            if not set(v).issubset(enabled):
                raise ValueError("ordered_columns must be a subset of enabled_columns")
        return v


# LEGACY: Backward compatibility classes (keeping existing imports working)
@dataclass
class FormatterConfig:
    """Base configuration for log formatters."""

    # Core configuration
    formatter_id: str = field(default_factory=lambda: f"formatter_{int(time.time() * 1000)}")
    formatter_type: str = "unknown"
    enabled: bool = True

    # Format settings
    format_string: str = "[{timestamp}] [{level_name}] [{layer}] {message}"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    timezone: Optional[str] = None

    # Output settings
    include_timestamp: bool = True
    include_level: bool = True
    include_layer: bool = True
    include_message: bool = True
    include_context: bool = False
    include_extra: bool = False

    # Context settings
    include_filename: bool = False
    include_function: bool = False
    include_line_number: bool = False
    include_thread_id: bool = False
    include_process_id: bool = False

    # Performance settings
    enable_caching: bool = True
    cache_size: int = 1000
    enable_optimization: bool = True

    # Customization
    custom_fields: Dict[str, str] = field(default_factory=dict)
    field_processors: Dict[str, Callable] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize formatter config after creation."""
        if not self.formatter_id:
            self.formatter_id = f"formatter_{int(time.time() * 1000)}"

    def get_custom_field(self, key: str, default: str = "") -> str:
        """Get a custom field value."""
        return self.custom_fields.get(key, default)

    def set_custom_field(self, key: str, value: str) -> None:
        """Set a custom field value."""
        self.custom_fields[key] = value

    def has_custom_field(self, key: str) -> bool:
        """Check if a custom field exists."""
        return key in self.custom_fields

    def remove_custom_field(self, key: str) -> str:
        """Remove a custom field and return its value."""
        return self.custom_fields.pop(key, "")

    def get_field_processor(self, field_name: str) -> Optional[Callable]:
        """Get a field processor function."""
        return self.field_processors.get(field_name)

    def set_field_processor(self, field_name: str, processor: Callable) -> None:
        """Set a field processor function."""
        self.field_processors[field_name] = processor

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'formatter_id': self.formatter_id,
            'formatter_type': self.formatter_type,
            'enabled': self.enabled,
            'format_string': self.format_string,
            'date_format': self.date_format,
            'timezone': self.timezone,
            'include_timestamp': self.include_timestamp,
            'include_level': self.include_level,
            'include_layer': self.include_layer,
            'include_message': self.include_message,
            'include_context': self.include_context,
            'include_extra': self.include_extra,
            'include_filename': self.include_filename,
            'include_function': self.include_function,
            'include_line_number': self.include_line_number,
            'include_thread_id': self.include_thread_id,
            'include_process_id': self.include_process_id,
            'enable_caching': self.enable_caching,
            'cache_size': self.cache_size,
            'enable_optimization': self.enable_optimization,
            'custom_fields': self.custom_fields
        }


@dataclass
class FormatOptions:
    """Options for formatting log records."""

    # Basic options
    show_colors: bool = True
    show_emoji: bool = False
    show_icons: bool = False

    # Text options
    text_case: str = "normal"  # normal, upper, lower, title
    text_align: str = "left"   # left, center, right
    text_width: Optional[int] = None
    text_truncate: bool = False

    # Number formatting
    number_format: str = "decimal"  # decimal, hex, octal, binary
    float_precision: int = 2
    use_scientific_notation: bool = False

    # Date/time options
    use_relative_time: bool = False
    show_timezone: bool = False
    use_24_hour: bool = True

    # Special options
    escape_html: bool = False
    escape_json: bool = False
    escape_csv: bool = False
    normalize_whitespace: bool = True

    # Custom options
    custom_options: Dict[str, Any] = field(default_factory=dict)

    def get_option(self, key: str, default: Any = None) -> Any:
        """Get a custom option value."""
        return self.custom_options.get(key, default)

    def set_option(self, key: str, value: Any) -> None:
        """Set a custom option value."""
        self.custom_options[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert options to dictionary."""
        return {
            'show_colors': self.show_colors,
            'show_emoji': self.show_emoji,
            'show_icons': self.show_icons,
            'text_case': self.text_case,
            'text_align': self.text_align,
            'text_width': self.text_width,
            'text_truncate': self.text_truncate,
            'number_format': self.number_format,
            'float_precision': self.float_precision,
            'use_scientific_notation': self.use_scientific_notation,
            'use_relative_time': self.use_relative_time,
            'show_timezone': self.show_timezone,
            'use_24_hour': self.use_24_hour,
            'escape_html': self.escape_html,
            'escape_json': self.escape_json,
            'escape_csv': self.escape_csv,
            'normalize_whitespace': self.normalize_whitespace,
            'custom_options': self.custom_options
        }


@dataclass
class ColorScheme:
    """Color scheme for formatted output."""

    # Level colors
    debug_color: str = "cyan"
    info_color: str = "green"
    warning_color: str = "yellow"
    error_color: str = "red"
    critical_color: str = "bright_red"

    # Context colors
    timestamp_color: str = "blue"
    level_color: str = "white"
    layer_color: str = "magenta"
    message_color: str = "white"
    filename_color: str = "cyan"
    function_color: str = "yellow"

    # Special colors
    highlight_color: str = "bright_white"
    muted_color: str = "dim"
    border_color: str = "white"
    separator_color: str = "dim"

    # Custom colors
    custom_colors: Dict[str, str] = field(default_factory=dict)

    def get_level_color(self, level: str) -> str:
        """Get color for a specific log level."""
        level_colors = {
            "DEBUG": self.debug_color,
            "INFO": self.info_color,
            "WARNING": self.warning_color,
            "ERROR": self.error_color,
            "CRITICAL": self.critical_color
        }
        return level_colors.get(level.upper(), self.level_color)

    def get_context_color(self, context: str) -> str:
        """Get color for a specific context element."""
        context_colors = {
            "timestamp": self.timestamp_color,
            "level": self.level_color,
            "layer": self.layer_color,
            "message": self.message_color,
            "filename": self.filename_color,
            "function": self.function_color
        }
        return context_colors.get(context, self.muted_color)

    def get_custom_color(self, key: str, default: str = "white") -> str:
        """Get a custom color value."""
        return self.custom_colors.get(key, default)

    def set_custom_color(self, key: str, color: str) -> None:
        """Set a custom color value."""
        self.custom_colors[key] = color

    def to_dict(self) -> Dict[str, Any]:
        """Convert color scheme to dictionary."""
        return {
            'debug_color': self.debug_color,
            'info_color': self.info_color,
            'warning_color': self.warning_color,
            'error_color': self.error_color,
            'critical_color': self.critical_color,
            'timestamp_color': self.timestamp_color,
            'level_color': self.level_color,
            'layer_color': self.layer_color,
            'message_color': self.message_color,
            'filename_color': self.filename_color,
            'function_color': self.function_color,
            'highlight_color': self.highlight_color,
            'muted_color': self.muted_color,
            'border_color': self.border_color,
            'separator_color': self.separator_color,
            'custom_colors': self.custom_colors
        }


@dataclass
class FormatTemplate:
    """Template for log formatting."""

    # Template information
    template_id: str = field(default_factory=lambda: f"template_{int(time.time() * 1000)}")
    name: str = "default"
    description: str = ""
    version: str = "1.0"

    # Template content
    template_string: str = "[{timestamp}] [{level_name}] [{layer}] {message}"
    template_type: str = "string"  # string, jinja2, mako, custom

    # Template variables
    variables: Dict[str, Any] = field(default_factory=dict)
    required_variables: List[str] = field(default_factory=list)
    optional_variables: List[str] = field(default_factory=list)

    # Template metadata
    author: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize template after creation."""
        if not self.template_id:
            self.template_id = f"template_{int(time.time() * 1000)}"
        self.updated_at = self.created_at

    def add_variable(self, name: str, value: Any, required: bool = False) -> None:
        """Add a template variable."""
        self.variables[name] = value
        if required and name not in self.required_variables:
            self.required_variables.append(name)
        elif not required and name not in self.optional_variables:
            self.optional_variables.append(name)
        self.updated_at = datetime.now()

    def remove_variable(self, name: str) -> Any:
        """Remove a template variable."""
        value = self.variables.pop(name, None)
        if name in self.required_variables:
            self.required_variables.remove(name)
        if name in self.optional_variables:
            self.optional_variables.remove(name)
        self.updated_at = datetime.now()
        return value

    def has_variable(self, name: str) -> bool:
        """Check if a variable exists."""
        return name in self.variables

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a template variable."""
        return self.variables.get(name, default)

    def validate_variables(self, provided_vars: Dict[str, Any]) -> bool:
        """Validate that all required variables are provided."""
        for var_name in self.required_variables:
            if var_name not in provided_vars:
                return False
        return True

    def add_tag(self, tag: str) -> None:
        """Add a tag to the template."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the template."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'template_string': self.template_string,
            'template_type': self.template_type,
            'variables': self.variables,
            'required_variables': self.required_variables,
            'optional_variables': self.optional_variables,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags
        }


@dataclass
class FormatResult:
    """Result of formatting a log record."""

    # Formatting result
    formatted_text: str
    original_record: Any
    format_time: float = field(default_factory=time.time)

    # Formatting metadata
    formatter_id: str = ""
    formatter_type: str = ""
    format_duration: float = 0.0

    # Formatting options
    options_used: FormatOptions = field(default_factory=FormatOptions)
    color_scheme: Optional[ColorScheme] = None

    # Formatting statistics
    text_length: int = 0
    color_count: int = 0
    field_count: int = 0

    def __post_init__(self):
        """Initialize format result after creation."""
        self.text_length = len(self.formatted_text)
        self.format_time = time.time()

    def get_text(self, strip_colors: bool = False) -> str:
        """Get formatted text, optionally stripping colors."""
        if strip_colors:
            # Simple color stripping (basic ANSI codes)
            import re
            return re.sub(r'\033\[[0-9;]*m', '', self.formatted_text)
        return self.formatted_text

    def get_length(self) -> int:
        """Get the length of formatted text."""
        return self.text_length

    def has_colors(self) -> bool:
        """Check if the formatted text contains colors."""
        return '\033[' in self.formatted_text

    def to_dict(self) -> Dict[str, Any]:
        """Convert format result to dictionary."""
        return {
            'formatted_text': self.formatted_text,
            'formatter_id': self.formatter_id,
            'formatter_type': self.formatter_type,
            'format_time': self.format_time,
            'format_duration': self.format_duration,
            'text_length': self.text_length,
            'color_count': self.color_count,
            'field_count': self.field_count,
            'has_colors': self.has_colors()
        }


# Convenience functions
def create_formatter_config(formatter_type: str, **kwargs) -> FormatterConfig:
    """Create a new formatter configuration."""
    return FormatterConfig(formatter_type=formatter_type, **kwargs)


def create_format_options(**kwargs) -> FormatOptions:
    """Create new format options."""
    return FormatOptions(**kwargs)


def create_color_scheme(**kwargs) -> ColorScheme:
    """Create a new color scheme."""
    return ColorScheme(**kwargs)


def create_format_template(name: str, template_string: str, **kwargs) -> FormatTemplate:
    """Create a new format template."""
    return FormatTemplate(name=name, template_string=template_string, **kwargs)
