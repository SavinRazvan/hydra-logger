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

from .text_utility import (
    TextProcessor,
    TextFormatter,
    TextValidator,
    TextSanitizer,
    TextAnalyzer
)

from .time_utility import (
    TimeUtility,
    TimestampFormatter,
    TimestampFormat,
    TimestampPrecision,
    TimestampConfig,
    DateFormatter,
    TimeZoneUtility,
    TimeRange,
    TimeInterval
)

from .file_utility import (
    FileUtility,
    PathUtility,
    FileValidator,
    FileProcessor,
    DirectoryScanner
)

# Removed over-engineered utilities: network, async_utils

# Removed over-engineered utilities: sync_utils, helpers, serialization, compression, caching

# Removed over-engineered utilities: debugging

__all__ = [
    # Text utilities
    "TextProcessor",
    "TextFormatter",
    "TextValidator",
    "TextSanitizer",
    "TextAnalyzer",

    # Time utilities
    "TimeUtility",
    "TimestampFormatter",
    "TimestampFormat",
    "TimestampPrecision",
    "TimestampConfig",
    "DateFormatter",
    "TimeZoneUtility",
    "TimeRange",
    "TimeInterval",

    # File utilities
    "FileUtility",
    "PathUtility",
    "FileValidator",
    "FileProcessor",
    "DirectoryScanner",

    # Removed over-engineered utilities

    # Removed over-engineered utilities: serialization, compression, caching, debugging
]
