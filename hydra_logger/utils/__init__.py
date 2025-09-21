"""
Utility Functions and Helpers for Hydra-Logger

This module provides comprehensive utility functions and helper classes for
various operations including text processing, time management, file operations,
network utilities, serialization, compression, caching, and debugging support.

UTILITY CATEGORIES:
- Text Processing: String manipulation, validation, sanitization, analysis
- Time Management: Timestamp formatting, timezone handling, duration calculations
- File Operations: File utilities, path management, directory scanning
- Network Utilities: Connection testing, URL processing, IP validation
- Serialization: JSON, YAML, TOML, Pickle, MessagePack support
- Compression: GZIP, BZIP2, LZMA compression utilities
- Caching: Memory and file-based caching with multiple policies
- Debugging: Performance profiling, object inspection, debug logging
- Async/Sync: Asynchronous and synchronous execution utilities
- General Helpers: Data manipulation, math utilities, collection helpers

USAGE:
    from hydra_logger.utils import TextProcessor, TimeUtils, FileUtils
    
    # Text processing
    processor = TextProcessor()
    normalized = processor.normalize_text("Hello World")
    
    # Time utilities
    timestamp = TimeUtils.now()
    formatted = TimeUtils.format_duration(3600)
    
    # File operations
    exists = FileUtils.exists("/path/to/file")
    info = FileUtils.get_file_info("/path/to/file")
"""

from .text import (
    TextProcessor,
    StringFormatter,
    TextValidator,
    TextSanitizer,
    TextAnalyzer
)

from .time import (
    TimeUtils,
    TimeUtility,
    TimestampFormatter,
    TimestampFormat,
    TimestampPrecision,
    TimestampConfig,
    DateFormatter,
    TimeZoneManager,
    TimeRange,
    TimeInterval
)

from .file import (
    FileUtils,
    PathManager,
    FileValidator,
    FileProcessor,
    DirectoryScanner
)

from .network import (
    NetworkUtils,
    URLProcessor,
    IPValidator,
    ConnectionTester,
    NetworkMonitor
)

from .async_utils import (
    AsyncUtils,
    AsyncExecutor,
    AsyncQueue,
    AsyncRetry,
    AsyncTimeout
)

from .sync_utils import (
    SyncUtils,
    ThreadManager,
    ProcessManager,
    ResourcePool,
    LockManager
)

from .helpers import (
    GeneralHelpers,
    DataHelpers,
    MathHelpers,
    CollectionHelpers,
    ObjectHelpers
)

from .serialization import (
    SerializationUtils,
    SerializationFormat,
    JSONProcessor,
    YAMLProcessor,
    PickleProcessor,
    MessagePackProcessor
)

# Import centralized types
from hydra_logger.types.enums import CompressionType

from .compression import (
    CompressionUtils,
    CompressionManager,
    GzipProcessor,
    Bzip2Processor,
    LzmaProcessor,
    CompressionOptions,
    CompressionResult
)

from .caching import (
    CacheManager,
    MemoryCache,
    FileCache,
    CachePolicy,
    CacheEntry,
    CacheStats,
    CacheBackend
)

from .debugging import (
    DebugUtils,
    DebugDecorator,
    PerformanceProfiler,
    DebugInspector,
    DebugLogger,
    DebugLevel,
    DebugMode,
    DebugContext,
    DebugInfo
)

__all__ = [
    # Text utilities
    "TextProcessor",
    "StringFormatter",
    "TextValidator",
    "TextSanitizer",
    "TextAnalyzer",

    # Time utilities
    "TimeUtils",
    "DateFormatter",
    "TimeZoneManager",
    "TimeRange",
    "TimeInterval",

    # File utilities
    "FileUtils",
    "PathManager",
    "FileValidator",
    "FileProcessor",
    "DirectoryScanner",

    # Network utilities
    "NetworkUtils",
    "URLProcessor",
    "IPValidator",
    "ConnectionTester",
    "NetworkMonitor",

    # Async utilities
    "AsyncUtils",
    "AsyncExecutor",
    "AsyncQueue",
    "AsyncRetry",
    "AsyncTimeout",

    # Sync utilities
    "SyncUtils",
    "ThreadManager",
    "ProcessManager",
    "ResourcePool",
    "LockManager",

    # General helpers
    "GeneralHelpers",
    "DataHelpers",
    "MathHelpers",
    "CollectionHelpers",
    "ObjectHelpers",

    # Serialization utilities
    "SerializationUtils",
    "SerializationFormat",
    "JSONProcessor",
    "YAMLProcessor",
    "PickleProcessor",
    "MessagePackProcessor",
    "CompressionType",

    # Compression utilities
    "CompressionUtils",
    "CompressionManager",
    "GzipProcessor",
    "Bzip2Processor",
    "LzmaProcessor",
    "CompressionOptions",
    "CompressionResult",

    # Caching utilities
    "CacheManager",
    "MemoryCache",
    "FileCache",
    "CachePolicy",
    "CacheEntry",
    "CacheStats",
    "CacheBackend",

    # Debugging utilities
    "DebugUtils",
    "DebugDecorator",
    "PerformanceProfiler",
    "DebugInspector",
    "DebugLogger",
    "DebugLevel",
    "DebugMode",
    "DebugContext",
    "DebugInfo"
]
