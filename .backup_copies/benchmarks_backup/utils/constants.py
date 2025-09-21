"""
Constants for benchmark configuration.
"""

# Default benchmark parameters
DEFAULT_ITERATIONS = 100000
DEFAULT_WARMUP_ITERATIONS = 0

# Directory paths
RESULTS_DIR = "benchmarks/_results"
LOGS_DIR = "benchmarks/_logs"

# Performance thresholds
TARGET_MSG_PER_SEC = 50000  # Target messages per second
HIGH_PERFORMANCE_THRESHOLD = 100000  # High performance threshold
ULTRA_HIGH_PERFORMANCE_THRESHOLD = 500000  # Ultra high performance threshold

# Memory thresholds
MEMORY_WARNING_THRESHOLD_MB = 100  # Warning if memory usage exceeds this
MEMORY_CRITICAL_THRESHOLD_MB = 500  # Critical if memory usage exceeds this

# Timeout settings
DEFAULT_TIMEOUT_SECONDS = 30  # Default timeout for async operations
HIGH_ITERATION_TIMEOUT_SECONDS = 60  # Timeout for high iteration tests

# File validation settings
MIN_FILE_SIZE_BYTES = 100  # Minimum expected file size
MAX_FILE_SIZE_MB = 100  # Maximum expected file size (MB)

# Error handling
MAX_ERROR_COUNT = 100  # Maximum errors before stopping test
ERROR_TOLERANCE_PERCENT = 5  # Maximum error percentage allowed
