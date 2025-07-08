"""
Comprehensive integration test suite for Hydra-Logger.

This module contains integration tests that demonstrate real-world usage
scenarios across multiple modules and components. The tests simulate
complex applications with various logging requirements including:

- Multi-module logging with custom folder paths
- Different log levels and filtering per module
- Multiple destinations per layer (files, console)
- Backward compatibility with existing code
- Configuration file loading and validation
- Log level filtering and message routing
- Async logging capabilities
- Performance monitoring
- Framework integrations
- Error handling and edge cases

These tests verify that Hydra-Logger works correctly in realistic
application environments with complex logging requirements.
"""

import asyncio
import logging
import os
import shutil
import tempfile
import time
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from hydra_logger import HydraLogger
from hydra_logger.config import LogDestination, LoggingConfig, LogLayer
from hydra_logger.compatibility import migrate_to_hydra


class TestIntegration:
    """
    Integration test suite for real-world Hydra-Logger usage.

    Tests simulate complex application scenarios with multiple modules,
    custom folder structures, and various logging requirements to ensure
    the system works correctly in production environments.
    """

    @pytest.fixture
    def temp_dir(self):
        """
        Create a temporary directory for test logs.

        Returns:
            str: Path to temporary directory.

        Yields:
            str: Path to temporary directory for test use.
        """
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_multi_module_logging_with_custom_paths(self, temp_dir):
        """
        Test logging from multiple modules to different custom paths.

        Args:
            temp_dir: Temporary directory for test files.

        Simulates a real application with multiple modules (APP, AUTH, API, DB, PERF)
        logging to different custom folder paths with various configurations.
        Verifies that all directories are created, log files are written correctly,
        and messages are properly filtered by log level.
        """

        # Create a comprehensive configuration for a real application
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "app", "main.log"),
                            max_size="5MB",
                            backup_count=3,
                        ),
                        LogDestination(type="console", level="WARNING"),
                    ],
                ),
                "AUTH": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "auth", "security.log"),
                            max_size="2MB",
                            backup_count=5,
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "auth", "errors.log"),
                            max_size="1MB",
                            backup_count=10,
                        ),
                    ],
                ),
                "API": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "api", "requests.log"),
                            max_size="10MB",
                            backup_count=3,
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "api", "errors.log"),
                            max_size="2MB",
                            backup_count=5,
                        ),
                    ],
                ),
                "DB": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(
                                temp_dir, "logs", "database", "queries.log"
                            ),
                            max_size="5MB",
                            backup_count=3,
                        )
                    ],
                ),
                "PERF": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(
                                temp_dir, "logs", "performance", "metrics.log"
                            ),
                            max_size="3MB",
                            backup_count=2,
                        )
                    ],
                ),
            }
        )

        # Initialize the logger
        logger = HydraLogger(config)

        # Simulate logging from different modules
        print("\n=== Simulating Multi-Module Logging ===")

        # App module logs
        logger.info("APP", "Application started successfully")
        logger.warning("APP", "Configuration file not found, using defaults")
        logger.error("APP", "Failed to connect to external service")

        # Auth module logs
        logger.debug("AUTH", "User authentication attempt: user123")
        logger.info("AUTH", "User user123 logged in successfully")
        logger.error("AUTH", "Invalid login attempt from IP 192.168.1.100")
        logger.critical(
            "AUTH", "Security breach detected: multiple failed login attempts"
        )

        # API module logs
        logger.info("API", "API request: GET /api/users")
        logger.info("API", "API request: POST /api/users")
        logger.error("API", "API error: 404 Not Found for /api/invalid")
        logger.error("API", "API error: 500 Internal Server Error")

        # Database module logs
        logger.debug("DB", "SQL Query: SELECT * FROM users WHERE id = 123")
        logger.debug("DB", "SQL Query: INSERT INTO logs (message) VALUES ('test')")
        logger.info("DB", "Database connection pool initialized")

        # Performance module logs
        logger.info("PERF", "Response time: 150ms for /api/users")
        logger.info("PERF", "Memory usage: 45MB")
        logger.info("PERF", "CPU usage: 12%")

        # Verify that all directories were created
        expected_dirs = [
            os.path.join(temp_dir, "logs", "app"),
            os.path.join(temp_dir, "logs", "auth"),
            os.path.join(temp_dir, "logs", "api"),
            os.path.join(temp_dir, "logs", "database"),
            os.path.join(temp_dir, "logs", "performance"),
        ]

        for dir_path in expected_dirs:
            assert os.path.exists(dir_path), f"Directory {dir_path} was not created"

        # Verify that all log files were created and contain expected content
        log_files_to_check = [
            (
                os.path.join(temp_dir, "logs", "app", "main.log"),
                [
                    "Application started successfully",
                    "Configuration file not found",
                    "Failed to connect to external service",
                ],
            ),
            (
                os.path.join(temp_dir, "logs", "auth", "security.log"),
                [
                    "User authentication attempt",
                    "User user123 logged in successfully",
                    "Invalid login attempt",
                    "Security breach detected",
                ],
            ),
            (
                os.path.join(temp_dir, "logs", "auth", "errors.log"),
                ["Invalid login attempt", "Security breach detected"],
            ),
            (
                os.path.join(temp_dir, "logs", "api", "requests.log"),
                ["API request: GET /api/users", "API request: POST /api/users"],
            ),
            (
                os.path.join(temp_dir, "logs", "api", "errors.log"),
                ["API error: 404 Not Found", "API error: 500 Internal Server Error"],
            ),
            (
                os.path.join(temp_dir, "logs", "database", "queries.log"),
                [
                    "SQL Query: SELECT * FROM users",
                    "SQL Query: INSERT INTO logs",
                    "Database connection pool initialized",
                ],
            ),
            (
                os.path.join(temp_dir, "logs", "performance", "metrics.log"),
                ["Response time: 150ms", "Memory usage: 45MB", "CPU usage: 12%"],
            ),
        ]

        print("\n=== Verifying Log Files ===")
        for log_file, expected_messages in log_files_to_check:
            assert os.path.exists(log_file), f"Log file {log_file} was not created"

            with open(log_file, "r") as f:
                content = f.read()
                print(
                    f"📄 {os.path.basename(log_file)}: {len(content.splitlines())} lines"
                )

                for message in expected_messages:
                    assert (
                        message in content
                    ), f"Message '{message}' not found in {log_file}"

        print(f"\n✅ All {len(log_files_to_check)} log files created and verified!")

        # Show the final directory structure
        print(f"\n📁 Final log structure in {temp_dir}:")
        for root, dirs, files in os.walk(os.path.join(temp_dir, "logs")):
            level = root.replace(temp_dir, "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}📂 {os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                print(f"{subindent}📄 {file}")

    def test_backward_compatibility_with_custom_path(self, temp_dir):
        """
        Test backward compatibility with custom log path.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that the migration function works correctly with
        custom log file paths, ensuring that legacy code can be
        migrated to Hydra-Logger while maintaining custom paths.
        """

        # Test the migration function with custom path
        logger = migrate_to_hydra(
            enable_file_logging=True,
            console_level=logging.INFO,
            log_file_path=os.path.join(temp_dir, "legacy", "app.log"),
        )

        # Log some messages
        logger.info("DEFAULT", "Legacy migration test - info message")
        logger.debug("DEFAULT", "Legacy migration test - debug message")
        logger.warning("DEFAULT", "Legacy migration test - warning message")

        # Verify the custom path was created
        log_file = os.path.join(temp_dir, "legacy", "app.log")
        assert os.path.exists(log_file), "Custom legacy log file was not created"

        with open(log_file, "r") as f:
            content = f.read()
            assert "Legacy migration test" in content
            assert "info message" in content
            assert "warning message" in content

        print(f"✅ Legacy migration with custom path works: {log_file}")

    def test_config_file_loading_with_custom_paths(self, temp_dir):
        """
        Test loading configuration from file with custom paths.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that Hydra-Logger can load complex configurations
        from YAML files and properly create custom folder structures
        for different modules with various logging requirements.
        """

        # Create a YAML config file
        config_content = f"""
layers:
  WEB:
    level: INFO
    destinations:
      - type: file
        path: "{temp_dir}/logs/web/access.log"
        max_size: "5MB"
        backup_count: 3
      - type: console
        level: ERROR

  EMAIL:
    level: DEBUG
    destinations:
      - type: file
        path: "{temp_dir}/logs/email/outgoing.log"
        max_size: "2MB"
        backup_count: 5

  SYSTEM:
    level: WARNING
    destinations:
      - type: file
        path: "{temp_dir}/logs/system/events.log"
        max_size: "10MB"
        backup_count: 2
"""

        config_file = os.path.join(temp_dir, "test_config.yaml")
        with open(config_file, "w") as f:
            f.write(config_content)

        # Load and use the configuration
        logger = HydraLogger.from_config(config_file)

        # Log from different modules
        logger.info("WEB", "Web request: GET /homepage")
        logger.error("WEB", "Web error: 500 Internal Server Error")

        logger.debug("EMAIL", "Email queued: welcome@example.com")
        logger.info("EMAIL", "Email sent: order@example.com")

        logger.warning("SYSTEM", "System warning: High memory usage")
        logger.error("SYSTEM", "System error: Database connection failed")

        # Verify files were created
        expected_files = [
            os.path.join(temp_dir, "logs", "web", "access.log"),
            os.path.join(temp_dir, "logs", "email", "outgoing.log"),
            os.path.join(temp_dir, "logs", "system", "events.log"),
        ]

        for log_file in expected_files:
            assert os.path.exists(log_file), f"Log file {log_file} was not created"
            with open(log_file, "r") as f:
                content = f.read()
                assert len(content) > 0, f"Log file {log_file} is empty"

        print("✅ Config file loading with custom paths works!")
        print(f"📁 Created {len(expected_files)} log files from config")

    def test_log_level_filtering(self, temp_dir):
        """
        Test that log levels are properly filtered per layer.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that each layer correctly filters log messages
        based on its configured log level, ensuring that only
        appropriate messages are written to each destination.
        """

        config = LoggingConfig(
            layers={
                "DEBUG_LAYER": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "debug", "all.log"),
                        )
                    ],
                ),
                "INFO_LAYER": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "info", "filtered.log"),
                        )
                    ],
                ),
                "ERROR_LAYER": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(
                                temp_dir, "logs", "error", "critical.log"
                            ),
                        )
                    ],
                ),
            }
        )

        logger = HydraLogger(config)

        # Log all levels to each layer
        for layer in ["DEBUG_LAYER", "INFO_LAYER", "ERROR_LAYER"]:
            logger.debug(layer, f"Debug message for {layer}")
            logger.info(layer, f"Info message for {layer}")
            logger.warning(layer, f"Warning message for {layer}")
            logger.error(layer, f"Error message for {layer}")
            logger.critical(layer, f"Critical message for {layer}")

        # Check DEBUG_LAYER (should have all messages)
        debug_file = os.path.join(temp_dir, "logs", "debug", "all.log")
        with open(debug_file, "r") as f:
            content = f.read()
            assert "Debug message for DEBUG_LAYER" in content
            assert "Info message for DEBUG_LAYER" in content
            assert "Warning message for DEBUG_LAYER" in content
            assert "Error message for DEBUG_LAYER" in content
            assert "Critical message for DEBUG_LAYER" in content

        # Check INFO_LAYER (should NOT have debug messages)
        info_file = os.path.join(temp_dir, "logs", "info", "filtered.log")
        with open(info_file, "r") as f:
            content = f.read()
            assert "Debug message for INFO_LAYER" not in content
            assert "Info message for INFO_LAYER" in content
            assert "Warning message for INFO_LAYER" in content
            assert "Error message for INFO_LAYER" in content
            assert "Critical message for INFO_LAYER" in content

        # Check ERROR_LAYER (should only have ERROR and CRITICAL)
        error_file = os.path.join(temp_dir, "logs", "error", "critical.log")
        with open(error_file, "r") as f:
            content = f.read()
            assert "Debug message for ERROR_LAYER" not in content
            assert "Info message for ERROR_LAYER" not in content
            assert "Warning message for ERROR_LAYER" not in content
            assert "Error message for ERROR_LAYER" in content
            assert "Critical message for ERROR_LAYER" in content

        print("✅ Log level filtering works correctly per layer!")

    def test_async_logging_integration(self, temp_dir):
        """
        Test async logging capabilities integration.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that async logging works correctly with the main logger
        and that async handlers are properly integrated.
        """
        
        # Create config with file destination only (avoid async HTTP for testing)
        config = LoggingConfig(
            layers={
                "ASYNC_LAYER": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "async", "async.log"),
                        ),
                    ],
                ),
            }
        )
        
        logger = HydraLogger(config)
        
        # Test async logging
        async def test_async_logging():
            logger.info("ASYNC_LAYER", "Async test message")
            logger.debug("ASYNC_LAYER", "Async debug message")
            logger.error("ASYNC_LAYER", "Async error message")
            
            # Wait a bit for async processing
            await asyncio.sleep(0.1)
        
        # Run async test
        asyncio.run(test_async_logging())
        
        # Verify file was created
        log_file = os.path.join(temp_dir, "logs", "async", "async.log")
        assert os.path.exists(log_file), "Async log file was not created"
        
        with open(log_file, "r") as f:
            content = f.read()
            assert "Async test message" in content
            assert "Async debug message" in content
            assert "Async error message" in content
        
        print("✅ Async logging integration works!")

    def test_performance_monitoring(self, temp_dir):
        """
        Test performance monitoring capabilities.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that performance monitoring works correctly and
        provides useful statistics.
        """
        
        config = LoggingConfig(
            layers={
                "PERF_LAYER": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "perf", "perf.log"),
                        ),
                    ],
                ),
            }
        )
        
        # Enable performance monitoring
        logger = HydraLogger(config, enable_performance_monitoring=True)
        
        # Perform some logging operations
        for i in range(10):
            logger.info("PERF_LAYER", f"Performance test message {i}")
            time.sleep(0.01)  # Small delay to simulate real usage
        
        # Get performance statistics
        stats = logger.get_performance_statistics()
        assert stats is not None, "Performance statistics should be available"
        assert "handler_creation_time" in stats
        assert "log_processing_time" in stats
        assert "memory_usage" in stats
        assert "error_count" in stats
        
        print(f"✅ Performance monitoring works! Stats: {stats}")

    def test_sensitive_data_redaction(self, temp_dir):
        """
        Test sensitive data redaction functionality.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that sensitive information is properly redacted
        from log messages.
        """
        
        config = LoggingConfig(
            layers={
                "SECURITY_LAYER": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "security", "security.log"),
                        ),
                    ],
                ),
            }
        )
        
        # Enable sensitive data redaction
        logger = HydraLogger(config, redact_sensitive=True)
        
        # Log messages with sensitive data
        sensitive_messages = [
            "User login with email: user@example.com",
            "API key: sk-1234567890abcdef",
            "Password: secret123",
            "Token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "Credit card: 1234-5678-9012-3456",
            "SSN: 123-45-6789",
            "Phone: 555-123-4567",
            "IP: 192.168.1.100",
            "URL with auth: https://user:pass@api.example.com/data",
        ]
        
        for message in sensitive_messages:
            logger.info("SECURITY_LAYER", message)
        
        # Verify redaction
        log_file = os.path.join(temp_dir, "logs", "security", "security.log")
        assert os.path.exists(log_file), "Security log file was not created"
        
        with open(log_file, "r") as f:
            content = f.read()
            
            # Check that sensitive data was redacted
            assert "[EMAIL_REDACTED]" in content
            assert "[API_KEY_REDACTED]" in content
            assert "[PASSWORD_REDACTED]" in content
            assert "[TOKEN_REDACTED]" in content
            assert "[CREDIT_CARD_REDACTED]" in content
            assert "[SSN_REDACTED]" in content
            assert "[PHONE_REDACTED]" in content
            assert "[IP_REDACTED]" in content
            assert "[URL_WITH_AUTH_REDACTED]" in content
            
            # Check that original sensitive data is NOT in the log
            assert "user@example.com" not in content
            assert "sk-1234567890abcdef" not in content
            assert "secret123" not in content
            assert "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." not in content
            assert "1234-5678-9012-3456" not in content
            assert "123-45-6789" not in content
            assert "555-123-4567" not in content
            assert "192.168.1.100" not in content
            assert "https://user:pass@api.example.com/data" not in content
        
        print("✅ Sensitive data redaction works correctly!")

    def test_framework_integrations(self, temp_dir):
        """
        Test framework integration methods.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that framework-specific logger configurations
        work correctly.
        """
        
        # Test FastAPI integration (with mock to handle missing dependencies)
        with patch('hydra_logger.framework_integration.FrameworkDetector.detect_environment', return_value='development'):
            with patch('hydra_logger.framework_integration.MagicConfig._setup_fastapi') as mock_setup:
                mock_setup.return_value = HydraLogger()
                fastapi_logger = HydraLogger.for_fastapi()
                assert fastapi_logger is not None
                assert isinstance(fastapi_logger, HydraLogger)
        
        # Test Django integration (with mock to handle missing dependencies)
        with patch('hydra_logger.framework_integration.FrameworkDetector.detect_environment', return_value='development'):
            with patch('hydra_logger.framework_integration.MagicConfig._setup_django') as mock_setup:
                mock_setup.return_value = HydraLogger()
                django_logger = HydraLogger.for_django()
                assert django_logger is not None
                assert isinstance(django_logger, HydraLogger)
        
        # Test Flask integration (with mock to handle missing dependencies)
        with patch('hydra_logger.framework_integration.FrameworkDetector.detect_environment', return_value='development'):
            with patch('hydra_logger.framework_integration.MagicConfig._setup_flask') as mock_setup:
                mock_setup.return_value = HydraLogger()
                flask_logger = HydraLogger.for_flask()
                assert flask_logger is not None
                assert isinstance(flask_logger, HydraLogger)
        
        # Test Web App integration (should work without mocks)
        web_logger = HydraLogger.for_web_app()
        assert web_logger is not None
        assert isinstance(web_logger, HydraLogger)
        
        # Test Microservice integration (should work without mocks)
        microservice_logger = HydraLogger.for_microservice()
        assert microservice_logger is not None
        assert isinstance(microservice_logger, HydraLogger)
        
        # Test CLI Tool integration (should work without mocks)
        cli_logger = HydraLogger.for_cli_tool()
        assert cli_logger is not None
        assert isinstance(cli_logger, HydraLogger)
        
        print("✅ Framework integrations work correctly!")

    def test_error_handling_and_edge_cases(self, temp_dir):
        """
        Test error handling and edge cases.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that the logger handles errors gracefully and
        works correctly in edge cases.
        """
        
        # Test with invalid config
        with pytest.raises(Exception):
            invalid_config = LoggingConfig(
                layers={
                    "INVALID": LogLayer(
                        level="INVALID_LEVEL",
                        destinations=[],
                    ),
                }
            )
            logger = HydraLogger(invalid_config)
        
        # Test with non-existent directory (should create it)
        deep_path = os.path.join(temp_dir, "deep", "nested", "path", "logs")
        config = LoggingConfig(
            layers={
                "DEEP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(deep_path, "deep.log"),
                        ),
                    ],
                ),
            }
        )
        
        logger = HydraLogger(config)
        logger.info("DEEP", "Test message in deep path")
        
        # Verify directory was created
        assert os.path.exists(deep_path), "Deep nested directory was not created"
        log_file = os.path.join(deep_path, "deep.log")
        assert os.path.exists(log_file), "Deep log file was not created"
        
        # Test with empty message
        logger.info("DEEP", "")
        
        # Test with very long message
        long_message = "A" * 10000
        logger.info("DEEP", long_message)
        
        # Test with special characters
        special_message = "Special chars: éñçüöäëïÿ€£¥¢©®™"
        logger.info("DEEP", special_message)
        
        # Test with None message (should handle gracefully)
        logger.info("DEEP", None)
        
        print("✅ Error handling and edge cases work correctly!")

    def test_auto_detection_and_lazy_initialization(self, temp_dir):
        """
        Test auto-detection and lazy initialization features.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that auto-detection works correctly and lazy
        initialization improves performance.
        """
        
        # Test auto-detection
        logger = HydraLogger(auto_detect=True)
        logger.info("Test message with auto-detection")
        
        # Test lazy initialization
        logger = HydraLogger(lazy_initialization=True)
        # Logger should not be fully initialized yet
        
        # Force initialization by logging
        logger.info("Test message with lazy initialization")
        
        # Test with custom date/time formats
        logger = HydraLogger(
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            logger_name_format="%(name)s",
            message_format="%(message)s"
        )
        logger.info("Test message with custom formats")
        
        print("✅ Auto-detection and lazy initialization work correctly!")

    def test_structured_logging_formats(self, temp_dir):
        """
        Test structured logging formats (JSON, CSV, Syslog, GELF).
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that different log formats work correctly.
        """
        
        formats_to_test = ["json", "csv", "syslog", "gelf"]
        
        for fmt in formats_to_test:
            config = LoggingConfig(
                layers={
                    f"FORMAT_{fmt.upper()}": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(
                                type="file",
                                path=os.path.join(temp_dir, "logs", "formats", f"{fmt}.log"),
                                format=fmt,
                            ),
                        ],
                    ),
                }
            )
            
            logger = HydraLogger(config)
            logger.info(f"FORMAT_{fmt.upper()}", f"Test message in {fmt} format")
            
            # Verify file was created
            log_file = os.path.join(temp_dir, "logs", "formats", f"{fmt}.log")
            assert os.path.exists(log_file), f"{fmt} log file was not created"
            
            with open(log_file, "r") as f:
                content = f.read()
                assert len(content) > 0, f"{fmt} log file is empty"
                
                if fmt == "json":
                    # Verify JSON format
                    lines = content.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            json.loads(line)  # Should be valid JSON
                
                elif fmt == "csv":
                    # Verify CSV format
                    assert "," in content, "CSV format should contain commas"
                
                elif fmt == "syslog":
                    # Verify Syslog format
                    assert "Test message in syslog format" in content
                
                elif fmt == "gelf":
                    # Verify GELF format
                    assert "Test message in gelf format" in content
        
        print("✅ Structured logging formats work correctly!")

    def test_concurrent_logging(self, temp_dir):
        """
        Test concurrent logging operations.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that the logger works correctly under concurrent
        access from multiple threads.
        """
        
        import threading
        
        config = LoggingConfig(
            layers={
                "CONCURRENT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "concurrent", "concurrent.log"),
                        ),
                    ],
                ),
            }
        )
        
        logger = HydraLogger(config)
        
        def log_messages(thread_id):
            for i in range(10):
                logger.info("CONCURRENT", f"Thread {thread_id} message {i}")
                time.sleep(0.001)  # Small delay
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all messages were logged
        log_file = os.path.join(temp_dir, "logs", "concurrent", "concurrent.log")
        assert os.path.exists(log_file), "Concurrent log file was not created"
        
        with open(log_file, "r") as f:
            content = f.read()
            # Should have messages from all threads
            for i in range(5):
                assert f"Thread {i} message" in content
        
        print("✅ Concurrent logging works correctly!")

    def test_configuration_validation(self, temp_dir):
        """
        Test configuration validation and error handling.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that configuration validation works correctly
        and provides helpful error messages.
        """
        
        # Test invalid log level
        with pytest.raises(Exception):
            config = LoggingConfig(
                layers={
                    "INVALID": LogLayer(
                        level="INVALID_LEVEL",
                        destinations=[],
                    ),
                }
            )
        
        # Test invalid destination type
        with pytest.raises(Exception):
            config = LoggingConfig(
                layers={
                    "INVALID": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="invalid_type"),
                        ],
                    ),
                }
            )
        
        # Test file destination without path
        with pytest.raises(Exception):
            config = LoggingConfig(
                layers={
                    "INVALID": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="file"),  # Missing path
                        ],
                    ),
                }
            )
        
        # Test valid configuration
        config = LoggingConfig(
            layers={
                "VALID": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "valid", "valid.log"),
                        ),
                    ],
                ),
            }
        )
        
        logger = HydraLogger(config)
        logger.info("VALID", "Valid configuration test")
        
        # Verify it worked
        log_file = os.path.join(temp_dir, "logs", "valid", "valid.log")
        assert os.path.exists(log_file), "Valid log file was not created"
        
        print("✅ Configuration validation works correctly!")

    def test_performance_under_load(self, temp_dir):
        """
        Test performance under high load.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that the logger performs well under high
        message volume.
        """
        
        config = LoggingConfig(
            layers={
                "LOAD": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "load", "load.log"),
                        ),
                    ],
                ),
            }
        )
        
        logger = HydraLogger(config, enable_performance_monitoring=True)
        
        # Log many messages quickly
        start_time = time.time()
        for i in range(1000):
            logger.info("LOAD", f"Load test message {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify performance is reasonable (should complete in under 5 seconds)
        assert duration < 5.0, f"Performance test took too long: {duration:.2f} seconds"
        
        # Verify all messages were logged
        log_file = os.path.join(temp_dir, "logs", "load", "load.log")
        assert os.path.exists(log_file), "Load test log file was not created"
        
        with open(log_file, "r") as f:
            content = f.read()
            lines = content.split('\n')
            # Should have close to 1000 lines (allowing for some overhead)
            assert len(lines) >= 950, f"Expected ~1000 lines, got {len(lines)}"
        
        # Get performance statistics
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert "log_processing_time" in stats
        
        print(f"✅ Performance under load: {duration:.2f} seconds for 1000 messages")

    def test_memory_efficiency(self, temp_dir):
        """
        Test memory efficiency during logging operations.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that the logger doesn't leak memory during
        extended operations.
        """
        
        import gc
        import psutil
        import os
        
        config = LoggingConfig(
            layers={
                "MEMORY": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "memory", "memory.log"),
                        ),
                    ],
                ),
            }
        )
        
        logger = HydraLogger(config, enable_performance_monitoring=True)
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many logging operations
        for i in range(1000):
            logger.info("MEMORY", f"Memory test message {i}")
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        memory_increase_mb = memory_increase / 1024 / 1024
        assert memory_increase_mb < 50, f"Memory increase too high: {memory_increase_mb:.2f} MB"
        
        print(f"✅ Memory efficiency: {memory_increase_mb:.2f} MB increase for 1000 messages")

    def test_error_recovery(self, temp_dir):
        """
        Test error recovery and resilience.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Verifies that the logger recovers gracefully from
        various error conditions.
        """
        
        # Test with invalid file path (should handle gracefully)
        config = LoggingConfig(
            layers={
                "ERROR_RECOVERY": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path="/invalid/path/that/does/not/exist/test.log",
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "recovery", "recovery.log"),
                        ),
                    ],
                ),
            }
        )
        
        logger = HydraLogger(config)
        
        # These should not crash the application
        logger.info("ERROR_RECOVERY", "Test message 1")
        logger.error("ERROR_RECOVERY", "Test message 2")
        logger.warning("ERROR_RECOVERY", "Test message 3")
        
        # Verify that valid destination still works
        log_file = os.path.join(temp_dir, "logs", "recovery", "recovery.log")
        assert os.path.exists(log_file), "Recovery log file was not created"
        
        with open(log_file, "r") as f:
            content = f.read()
            assert "Test message 1" in content
            assert "Test message 2" in content
            assert "Test message 3" in content
        
        print("✅ Error recovery works correctly!")

    def test_comprehensive_integration_scenario(self, temp_dir):
        """
        Test a comprehensive integration scenario.
        
        Args:
            temp_dir: Temporary directory for test files.
            
        Simulates a complex real-world application with multiple
        logging requirements and verifies everything works together.
        """
        
        # Create a complex configuration
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "app", "main.log"),
                            format="json",
                        ),
                        LogDestination(
                            type="console",
                            level="ERROR",
                        ),
                    ],
                ),
                "SECURITY": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "security", "security.log"),
                            format="text",
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "security", "audit.log"),
                            format="csv",
                        ),
                    ],
                ),
                "PERFORMANCE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "performance", "metrics.log"),
                            format="json",
                        ),
                    ],
                ),
            }
        )
        
        # Create logger with all features enabled
        logger = HydraLogger(
            config,
            enable_performance_monitoring=True,
            redact_sensitive=True,
            auto_detect=True,
            lazy_initialization=False,
        )
        
        # Simulate complex application usage
        logger.info("APP", "Application started")
        logger.info("SECURITY", "User login: admin@example.com")
        logger.debug("SECURITY", "Authentication successful")
        logger.info("PERFORMANCE", "Response time: 150ms")
        logger.error("APP", "Database connection failed")
        logger.warning("APP", "High memory usage detected")
        logger.critical("SECURITY", "Security breach detected")
        
        # Verify all log files were created
        expected_files = [
            os.path.join(temp_dir, "logs", "app", "main.log"),
            os.path.join(temp_dir, "logs", "security", "security.log"),
            os.path.join(temp_dir, "logs", "security", "audit.log"),
            os.path.join(temp_dir, "logs", "performance", "metrics.log"),
        ]
        
        for log_file in expected_files:
            assert os.path.exists(log_file), f"Log file {log_file} was not created"
            
            with open(log_file, "r") as f:
                content = f.read()
                assert len(content) > 0, f"Log file {log_file} is empty"
        
        # Test performance statistics
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert "memory_usage" in stats
        
        # Test logger retrieval
        app_logger = logger.get_logger("APP")
        assert app_logger is not None
        assert isinstance(app_logger, logging.Logger)
        
        print("✅ Comprehensive integration scenario works correctly!")
        print(f"📁 Created {len(expected_files)} log files with different formats")
        print(f"📊 Performance stats: {stats}")
