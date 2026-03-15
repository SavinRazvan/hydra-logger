"""
Role: Enums implementation.
Used By:
 - hydra_logger/handlers/rotating_handler.py for time-unit rotation policies.
 - hydra_logger/handlers/__init__.py for re-exported enum usage.
 - hydra_logger/utils/time_utility.py for time conversion and interval helpers.
 - hydra_logger/types/__init__.py for package exports.
Depends On:
 - enum
 - typing
Notes:
 - Central enum definitions for handlers, formats, destinations, and runtime policies.
"""

from enum import Enum
from typing import Any, List


class HandlerType(Enum):
    """Types of log handlers."""

    CONSOLE = "console"
    FILE = "file"
    STREAM = "stream"
    ROTATING = "rotating"
    NETWORK = "network"
    SYSTEM = "system"
    DATABASE = "database"
    QUEUE = "queue"
    CLOUD = "cloud"
    COMPOSITE = "composite"
    FALLBACK = "fallback"
    CUSTOM = "custom"


class FormatterType(Enum):
    """Types of log formatters."""

    PLAIN_TEXT = "plain_text"
    JSON = "json"
    JSON_LINES = "json_lines"
    CSV = "csv"
    SYSLOG = "syslog"
    GELF = "gelf"
    LOGSTASH = "logstash"
    DETAILED = "detailed"
    COLORED = "colored"
    CUSTOM = "custom"


class PluginType(Enum):
    """Types of plugins."""

    ANALYTICS = "analytics"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MONITORING = "monitoring"
    INTEGRATION = "integration"
    FORMATTER = "formatter"
    HANDLER = "handler"
    CUSTOM = "custom"


class LogLayer(Enum):
    """Standard log layers."""

    DEFAULT = "default"
    APP = "APP"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    AUDIT = "AUDIT"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    CUSTOM = "CUSTOM"


class SecurityLevel(Enum):
    """Security levels for data protection."""

    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


class QueuePolicy(Enum):
    """Queue backpressure policies."""

    DROP_OLDEST = "drop_oldest"
    BLOCK = "block"
    ERROR = "error"
    RETRY = "retry"


class ShutdownPhase(Enum):
    """Shutdown phases for graceful termination."""

    RUNNING = "running"
    FLUSHING = "flushing"
    CLEANING = "cleaning"
    DONE = "done"


class RotationStrategy(Enum):
    """File rotation strategies."""

    TIME = "time"
    SIZE = "size"
    HYBRID = "hybrid"
    MANUAL = "manual"


class CompressionType(Enum):
    """Compression types for log files."""

    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZMA = "lzma"
    ZSTD = "zstd"


class EncryptionType(Enum):
    """Encryption types for secure logging."""

    NONE = "none"
    AES = "aes"
    RSA = "rsa"
    CHACHA20 = "chacha20"


class NetworkProtocol(Enum):
    """Network protocols for remote logging."""

    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    WEBSOCKET = "websocket"
    GRPC = "grpc"


class DatabaseType(Enum):
    """Database types for log storage."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"


class CloudProvider(Enum):
    """Cloud service providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITALOCEAN = "digitalocean"
    HEROKU = "heroku"


class LogFormat(Enum):
    """Standard log formats."""

    PLAIN = "plain"
    JSON = "json"
    JSON_LINES = "json_lines"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"
    TOML = "toml"
    INI = "ini"


class ColorMode(Enum):
    """Color output modes."""

    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"
    FORCE = "force"


class ValidationLevel(Enum):
    """Configuration validation levels."""

    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"


class MonitoringLevel(Enum):
    """Monitoring detail levels."""

    NONE = "none"
    BASIC = "basic"
    DETAILED = "detailed"
    VERBOSE = "verbose"


class ErrorHandling(Enum):
    """Error handling strategies."""

    IGNORE = "ignore"
    LOG = "log"
    RAISE = "raise"
    RETRY = "retry"
    FALLBACK = "fallback"


class AsyncMode(Enum):
    """Asynchronous operation modes."""

    SYNC = "sync"
    ASYNC = "async"
    AUTO = "auto"
    HYBRID = "hybrid"


class CacheStrategy(Enum):
    """Caching strategies."""

    NONE = "none"
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"
    DISTRIBUTED = "distributed"


class BackupStrategy(Enum):
    """Backup strategies."""

    NONE = "none"
    COPY = "copy"
    MOVE = "move"
    COMPRESS = "compress"
    ENCRYPT = "encrypt"


class HealthCheckType(Enum):
    """Health check types."""

    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TimeUnit(Enum):
    """time units for all Hydra-Logger operations.

    Supports both high-precision measurements and rotation intervals.
    Values are standardized for consistency across the codebase.
    """

    # High-precision units (for measurements)
    NANOSECONDS = "ns"
    MICROSECONDS = "μs"
    MILLISECONDS = "ms"

    # Standard time units (for rotation and intervals)
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"

    @property
    def is_precision_unit(self) -> bool:
        """Check if this is a high-precision measurement unit."""
        return self in {
            TimeUnit.NANOSECONDS,
            TimeUnit.MICROSECONDS,
            TimeUnit.MILLISECONDS,
        }

    @property
    def is_rotation_unit(self) -> bool:
        """Check if this unit is suitable for file rotation."""
        return self in {
            TimeUnit.SECONDS,
            TimeUnit.MINUTES,
            TimeUnit.HOURS,
            TimeUnit.DAYS,
            TimeUnit.WEEKS,
            TimeUnit.MONTHS,
            TimeUnit.YEARS,
        }

    def to_seconds(self) -> float:
        """Convert this time unit to seconds (for calculations)."""
        conversion_map = {
            TimeUnit.NANOSECONDS: 1e-9,
            TimeUnit.MICROSECONDS: 1e-6,
            TimeUnit.MILLISECONDS: 1e-3,
            TimeUnit.SECONDS: 1.0,
            TimeUnit.MINUTES: 60.0,
            TimeUnit.HOURS: 3600.0,
            TimeUnit.DAYS: 86400.0,
            TimeUnit.WEEKS: 604800.0,
            TimeUnit.MONTHS: 2592000.0,  # ~30 days
            TimeUnit.YEARS: 31536000.0,  # ~365 days
        }
        return conversion_map.get(self, 1.0)

    def get_short_name(self) -> str:
        """Get short abbreviation for this time unit."""
        short_map = {
            TimeUnit.NANOSECONDS: "ns",
            TimeUnit.MICROSECONDS: "μs",
            TimeUnit.MILLISECONDS: "ms",
            TimeUnit.SECONDS: "s",
            TimeUnit.MINUTES: "m",
            TimeUnit.HOURS: "h",
            TimeUnit.DAYS: "d",
            TimeUnit.WEEKS: "w",
            TimeUnit.MONTHS: "M",
            TimeUnit.YEARS: "y",
        }
        return short_map.get(self, self.value)


class SizeUnit(Enum):
    """Size units for measurements."""

    BYTES = "B"
    KILOBYTES = "KB"
    MEGABYTES = "MB"
    GIGABYTES = "GB"
    TERABYTES = "TB"


# Utility functions for enum operations
def get_enum_values(enum_class: type[Enum]) -> List[Any]:
    """Get all values from an enum class."""
    return [e.value for e in enum_class]


def get_enum_names(enum_class: type[Enum]) -> List[str]:
    """Get all names from an enum class."""
    return [e.name for e in enum_class]


def get_enum_by_value(enum_class: type[Enum], value: Any) -> Any:
    """Get enum member by value."""
    for member in enum_class:
        if member.value == value:
            return member
    return None


def get_enum_by_name(enum_class: type[Enum], name: str) -> Any:
    """Get enum member by name."""
    try:
        return enum_class[name]
    except KeyError:
        return None


def is_valid_enum_value(enum_class: type[Enum], value: Any) -> bool:
    """Check if a value is valid for an enum class."""
    return value in [e.value for e in enum_class]


def is_valid_enum_name(enum_class: type[Enum], name: str) -> bool:
    """Check if a name is valid for an enum class."""
    return name in [e.name for e in enum_class]


# Export all enums and utility functions
__all__ = [
    # Handler types
    "HandlerType",
    # Formatter types
    "FormatterType",
    # Plugin types
    "PluginType",
    # Log layers
    "LogLayer",
    # Security levels
    "SecurityLevel",
    # Queue policies
    "QueuePolicy",
    # Shutdown phases
    "ShutdownPhase",
    # Rotation strategies
    "RotationStrategy",
    # Compression types
    "CompressionType",
    # Encryption types
    "EncryptionType",
    # Network protocols
    "NetworkProtocol",
    # Database types
    "DatabaseType",
    # Cloud providers
    "CloudProvider",
    # Log formats
    "LogFormat",
    # Color modes
    "ColorMode",
    # Validation levels
    "ValidationLevel",
    # Monitoring levels
    "MonitoringLevel",
    # Error handling
    "ErrorHandling",
    # Async modes
    "AsyncMode",
    # Cache strategies
    "CacheStrategy",
    # Backup strategies
    "BackupStrategy",
    # Health check types
    "HealthCheckType",
    # Alert severity
    "AlertSeverity",
    # Metric types
    "MetricType",
    # Time units
    "TimeUnit",
    # Size units
    "SizeUnit",
    # Utility functions
    "get_enum_values",
    "get_enum_names",
    "get_enum_by_value",
    "get_enum_by_name",
    "is_valid_enum_value",
    "is_valid_enum_name",
]
