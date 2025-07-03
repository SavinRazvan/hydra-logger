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

These tests verify that Hydra-Logger works correctly in realistic
application environments with complex logging requirements.
"""

import logging
import os
import shutil
import tempfile

import pytest

from hydra_logger import HydraLogger
from hydra_logger.config import LogDestination, LoggingConfig, LogLayer


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
        from hydra_logger.compatibility import migrate_to_hydra

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
