"""
Data test fixtures for Hydra-Logger.

Provides sample data and test records for testing.
"""

import pytest
import time
from typing import List, Dict, Any
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


@pytest.fixture
def sample_messages():
    """Sample log messages for testing."""
    return [
        "Simple test message",
        "Message with special chars: !@#$%^&*()",
        "Unicode message: 你好世界 🌍",
        "Very long message " * 100,
        "Message with\nnewlines\nand\ttabs",
        "Message with 'quotes' and \"double quotes\"",
        "Message with numbers: 12345.67890",
        "Empty message:",
        "Message with unicode: café naïve résumé",
        "Message with emoji: 🚀🔥💯"
    ]


@pytest.fixture
def sample_log_levels():
    """Sample log levels for testing."""
    return [
        LogLevel.DEBUG,
        LogLevel.INFO,
        LogLevel.WARNING,
        LogLevel.ERROR,
        LogLevel.CRITICAL
    ]


@pytest.fixture
def sample_log_records():
    """Sample log records for testing."""
    records = []
    base_time = time.time()
    
    for i, level in enumerate([LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]):
        record = LogRecord(
            level=level,
            level_name=level.name,
            message=f"Test message {i}",
            timestamp=base_time + i,
            logger_name="test_logger",
            filename="test_file.py",
            function_name="test_function",
            line_number=10 + i
        )
        records.append(record)
    
    return records


@pytest.fixture
def performance_test_data():
    """Data for performance testing."""
    return {
        'small_batch': list(range(100)),
        'medium_batch': list(range(1000)),
        'large_batch': list(range(10000)),
        'test_messages': [f"Perf test message {i}" for i in range(1000)],
        'test_levels': [LogLevel.INFO] * 1000
    }


@pytest.fixture
def stress_test_data():
    """Data for stress testing."""
    return {
        'high_volume_messages': [f"Stress test {i}" for i in range(100000)],
        'mixed_levels': [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR] * 1000,
        'large_messages': [f"Large message {i} " * 100 for i in range(1000)],
        'concurrent_messages': [f"Concurrent {i}" for i in range(10000)]
    }


@pytest.fixture
def security_test_data():
    """Data for security testing."""
    return {
        'pii_data': [
            "User email: john.doe@example.com",
            "Phone number: +1-555-123-4567",
            "SSN: 123-45-6789",
            "Credit card: 4111-1111-1111-1111",
            "Password: mySecretPassword123"
        ],
        'sensitive_data': [
            "API key: sk-1234567890abcdef",
            "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "Database URL: postgresql://user:pass@localhost:5432/db",
            "Secret: super_secret_value_123"
        ],
        'safe_data': [
            "Regular log message",
            "System status: OK",
            "User logged in successfully",
            "Processing completed"
        ]
    }


@pytest.fixture
def error_test_data():
    """Data for error handling testing."""
    return {
        'invalid_inputs': [
            None,
            "",
            123,
            [],
            {},
            object()
        ],
        'edge_cases': [
            "x" * 1000000,  # Very long string
            "\x00\x01\x02",  # Binary data
            "🚀" * 1000,     # Many emojis
            "a" * 0,         # Empty string
        ],
        'malformed_data': [
            {"invalid": "json"},
            "Unclosed string",
            "Invalid unicode: \udcff",
            "Null byte: \x00"
        ]
    }
