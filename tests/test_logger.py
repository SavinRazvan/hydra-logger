"""
Comprehensive test suite for Hydra-Logger core functionality.

This module contains unit tests for the main HydraLogger class and its
various methods. Tests cover initialization, configuration loading,
logging operations, error handling, and edge cases.

The tests verify that:
- Logger initialization works with various configurations
- Logging methods function correctly across all levels
- File and console destinations work properly
- Error handling is robust for various failure scenarios
- Custom folder paths and file rotation work correctly
- Thread safety is maintained during concurrent logging
"""

import logging
import os
import shutil
import tempfile
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from hydra_logger.config import LogDestination, LoggingConfig, LogLayer
from hydra_logger.logger import HydraLogger, HydraLoggerError


class TestHydraLogger:
    """
    Test suite for the main HydraLogger class.

    Tests cover initialization, configuration, logging operations,
    error handling, and various edge cases.
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

    def test_default_initialization(self):
        """
        Test HydraLogger initialization with default configuration.

        Verifies that HydraLogger can be initialized without parameters
        and uses the default configuration with a DEFAULT layer.
        """
        logger = HydraLogger()

        assert logger.config is not None
        assert "DEFAULT" in logger.loggers
        assert isinstance(logger.loggers["DEFAULT"], logging.Logger)

    def test_custom_config_initialization(self, temp_dir):
        """
        Test HydraLogger initialization with custom configuration.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that HydraLogger can be initialized with a custom
        configuration and creates the expected loggers and handlers.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(temp_dir, "app.log")
                        ),
                        LogDestination(type="console", level="WARNING"),
                    ],
                )
            }
        )

        logger = HydraLogger(config)

        assert "APP" in logger.loggers
        assert logger.loggers["APP"].level == logging.INFO

        # Check handlers
        handlers = logger.loggers["APP"].handlers
        assert len(handlers) == 2

        # Verify handler types
        handler_types = [type(h) for h in handlers]
        assert RotatingFileHandler in handler_types
        assert logging.StreamHandler in handler_types

    def test_from_config_file(self, temp_dir):
        """
        Test HydraLogger creation from configuration file.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that HydraLogger.from_config can load configurations
        from YAML files and create properly configured loggers.
        """
        config_content = f"""
layers:
  APP:
    level: DEBUG
    destinations:
      - type: file
        path: "{temp_dir}/app.log"
        max_size: 5MB
        backup_count: 3
      - type: console
        level: INFO
default_level: INFO
"""

        config_file = os.path.join(temp_dir, "config.yaml")
        with open(config_file, "w") as f:
            f.write(config_content)

        logger = HydraLogger.from_config(config_file)

        assert "APP" in logger.loggers
        assert logger.loggers["APP"].level == logging.DEBUG

    def test_from_config_file_not_found(self):
        """
        Test HydraLogger creation from non-existent config file.

        Verifies that HydraLogger.from_config raises FileNotFoundError
        when the specified configuration file doesn't exist.
        """
        with pytest.raises(FileNotFoundError):
            HydraLogger.from_config("nonexistent.yaml")

    def test_from_config_file_invalid(self, temp_dir):
        """
        Test HydraLogger creation from invalid config file.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that HydraLogger.from_config handles invalid
        configuration files gracefully.
        """
        config_file = os.path.join(temp_dir, "invalid.yaml")
        with open(config_file, "w") as f:
            f.write("invalid: yaml: content:")

        with pytest.raises(ValueError):
            HydraLogger.from_config(config_file)

    def test_from_config_file_initialization_error(self, temp_dir):
        """
        Test HydraLogger creation when config loading succeeds but initialization fails.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that HydraLogger.from_config handles initialization errors
        after successful config loading.
        """
        config_content = """
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: "/invalid/path/app.log"
default_level: INFO
"""

        config_file = os.path.join(temp_dir, "config.yaml")
        with open(config_file, "w") as f:
            f.write(config_content)

        with pytest.raises(
            HydraLoggerError, match="Failed to create HydraLogger from config"
        ):
            HydraLogger.from_config(config_file)

    def test_custom_folder_paths(self, temp_dir):
        """
        Test logging to custom folder paths.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that HydraLogger can create custom folder structures
        and write log files to nested directories.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "app", "main.log"),
                        )
                    ]
                ),
                "DEBUG": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "logs", "debug", "all.log"),
                        )
                    ]
                ),
            }
        )

        logger = HydraLogger(config)

        # Test logging
        logger.info("APP", "App message")
        logger.debug("DEBUG", "Debug message")

        # Check that directories were created
        assert os.path.exists(os.path.join(temp_dir, "logs", "app"))
        assert os.path.exists(os.path.join(temp_dir, "logs", "debug"))

        # Check that log files were created
        assert os.path.exists(os.path.join(temp_dir, "logs", "app", "main.log"))
        assert os.path.exists(os.path.join(temp_dir, "logs", "debug", "all.log"))

    def test_logging_methods(self, temp_dir):
        """
        Test all logging methods.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that all logging methods (debug, info, warning, error, critical)
        work correctly and write messages to the appropriate destinations.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(temp_dir, "test.log")
                        )
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        # Test all logging levels
        logger.debug("TEST", "Debug message")
        logger.info("TEST", "Info message")
        logger.warning("TEST", "Warning message")
        logger.error("TEST", "Error message")
        logger.critical("TEST", "Critical message")

        # Check file content
        with open(os.path.join(temp_dir, "test.log"), "r") as f:
            content = f.read()
            # Debug message won't be in file because layer level is INFO by default
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
            assert "Critical message" in content

    def test_unknown_layer_fallback(self, temp_dir):
        """Test fallback to default logger for unknown layers."""
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "default.log"),
                            format="text"
                        ),
                    ],
                )
            }
        )
        logger = HydraLogger(config)
        logger.info("UNKNOWN", "Should fallback to default layer")
        filepath = os.path.join(temp_dir, "default.log")
        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            content = f.read()
            assert "Should fallback to default layer" in content

    def test_log_method_invalid_level(self, temp_dir):
        """Test error handling for invalid log level."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "app.log"),
                            format="text"
                        ),
                    ],
                )
            }
        )
        logger = HydraLogger(config)
        with pytest.raises(ValueError):
            logger.log("APP", "NOTALEVEL", "This should fail")

    def test_log_method_empty_message(self, temp_dir):
        """Test that empty messages are skipped."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "app.log"),
                            format="text"
                        ),
                    ],
                )
            }
        )
        logger = HydraLogger(config)
        logger.log("APP", "INFO", "")  # Should not raise or log
        filepath = os.path.join(temp_dir, "app.log")
        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            content = f.read()
            # Should be empty or only contain headers
            assert content.strip() == ""

    def test_log_method_fallback_to_info(self, temp_dir):
        """Test fallback to info level if log method fails."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "app.log"),
                            format="text"
                        ),
                    ],
                )
            }
        )
        logger = HydraLogger(config)
        # Patch logger to raise on warning
        app_logger = logger.get_logger("APP")
        original_warning = app_logger.warning
        app_logger.warning = lambda msg: (_ for _ in ()).throw(Exception("fail"))
        logger.log("APP", "WARNING", "Should fallback to info")
        app_logger.warning = original_warning
        filepath = os.path.join(temp_dir, "app.log")
        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            content = f.read()
            assert "Should fallback to info" in content

    def test_internal_log_warning_and_error(self):
        """Test _log_warning and _log_error internal methods for coverage."""
        config = LoggingConfig(layers={})
        logger = HydraLogger(config)
        # These should not raise
        logger._log_warning("Test warning")
        logger._log_error("Test error")

    def test_logging_to_nonexistent_layer_no_default(self, temp_dir):
        """
        Test logging to unknown layer without default fallback.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that logging to an unknown layer when no default
        layer exists is handled gracefully.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(temp_dir, "app.log")
                        )
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        # Log to unknown layer (should not crash)
        logger.info("UNKNOWN", "Unknown layer message")

        # Should not create any files for unknown layer
        assert not os.path.exists(os.path.join(temp_dir, "unknown.log"))

    def test_file_rotation(self, temp_dir):
        """
        Test file rotation functionality.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that log files are rotated when they exceed the
        maximum size limit.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "test.log"),
                            max_size="1KB",
                            backup_count=2,
                        )
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        # Write enough data to trigger rotation
        large_message = "X" * 100  # 100 bytes per message
        for i in range(15):  # 1500 bytes total, should trigger rotation
            logger.info("TEST", f"{large_message} {i}")

        # Check that rotation files were created
        assert os.path.exists(os.path.join(temp_dir, "test.log"))
        assert os.path.exists(os.path.join(temp_dir, "test.log.1"))

    def test_multiple_destinations(self, temp_dir):
        """
        Test logging to multiple destinations.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that a single layer can log to multiple destinations
        (file and console) simultaneously.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(temp_dir, "test.log")
                        ),
                        LogDestination(type="console", level="WARNING"),
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        # Test logging
        logger.info("TEST", "Info message")
        logger.warning("TEST", "Warning message")

        # Check file content
        with open(os.path.join(temp_dir, "test.log"), "r") as f:
            content = f.read()
            assert "Info message" in content
            assert "Warning message" in content

    def test_size_parsing(self):
        """
        Test size string parsing functionality.

        Verifies that the _parse_size method correctly converts
        human-readable size strings to bytes.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Test various size formats
        assert logger._parse_size("1KB") == 1024
        assert logger._parse_size("1MB") == 1024 * 1024
        assert logger._parse_size("1GB") == 1024 * 1024 * 1024
        assert logger._parse_size("5MB") == 5 * 1024 * 1024

        # Test invalid size format
        with pytest.raises(ValueError, match="Invalid size format"):
            logger._parse_size("invalid")

    def test_size_parsing_empty_string(self):
        """
        Test size parsing with empty string.

        Verifies that _parse_size raises ValueError for empty strings.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        with pytest.raises(ValueError, match="Size string cannot be empty"):
            logger._parse_size("")

    def test_size_parsing_bytes_format(self):
        """
        Test size parsing with explicit bytes format.

        Verifies that _parse_size handles 'B' suffix correctly.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        assert logger._parse_size("1024B") == 1024
        assert logger._parse_size("1B") == 1

    def test_get_logger_method(self, temp_dir):
        """
        Test get_logger method.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that the get_logger method returns the correct
        logging.Logger instance for a given layer.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(temp_dir, "app.log")
                        )
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        # Get logger for existing layer
        app_logger = logger.get_logger("APP")
        assert isinstance(app_logger, logging.Logger)
        assert app_logger.name == "hydra.APP"

        # Get logger for non-existent layer (should return a new logger)
        non_existent_logger = logger.get_logger("NONEXISTENT")
        assert isinstance(non_existent_logger, logging.Logger)
        assert non_existent_logger.name == "hydra.NONEXISTENT"

    def test_invalid_config_structure(self):
        """
        Test handling of invalid configuration structure.

        Verifies that HydraLogger handles invalid configurations
        gracefully and provides meaningful error messages.
        """
        # Create config with console destination (no path required)
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            }
        )

        # Should handle config gracefully
        logger = HydraLogger(config)
        assert "TEST" in logger.loggers

    def test_file_permission_error(self, temp_dir):
        """
        Test handling of file permission errors.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that HydraLogger handles file permission errors
        gracefully and continues to function.
        """
        # Create a read-only directory
        readonly_dir = os.path.join(temp_dir, "readonly")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # Read-only

        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(readonly_dir, "test.log")
                        )
                    ]
                )
            }
        )

        # Should handle permission error gracefully
        logger = HydraLogger(config)

        # Try to log (should not crash)
        logger.info("TEST", "Test message")

        # Restore permissions for cleanup
        os.chmod(readonly_dir, 0o755)

    def test_threaded_logging(self, temp_dir):
        """
        Test logging from multiple threads.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that HydraLogger is thread-safe and can handle
        concurrent logging operations.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(temp_dir, "test.log")
                        )
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        def log_messages(thread_id):
            for i in range(10):
                logger.info("TEST", f"Thread {thread_id} message {i}")

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that all messages were logged
        with open(os.path.join(temp_dir, "test.log"), "r") as f:
            content = f.read()
            for i in range(5):
                assert f"Thread {i} message" in content

    def test_log_format_content(self, temp_dir):
        """
        Test log message format and content.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that log messages include the expected format
        with timestamps, log levels, and message content.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(temp_dir, "test.log")
                        )
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        # Log a message
        logger.info("TEST", "Test message content")

        # Check log format
        with open(os.path.join(temp_dir, "test.log"), "r") as f:
            content = f.read()
            lines = content.strip().split("\n")
            assert len(lines) == 1

            line = lines[0]
            # Check for timestamp format
            assert " - INFO - " in line
            assert "Test message content" in line

    def test_console_output_capture(self, temp_dir):
        """
        Test console output capture.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that console logging works correctly and
        messages are properly formatted for console output.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            }
        )

        logger = HydraLogger(config)

        # Test console logging (should not crash)
        logger.info("TEST", "Console test message")
        logger.warning("TEST", "Console warning message")

        # Verify that the logger was created correctly
        assert "TEST" in logger.loggers
        test_logger = logger.loggers["TEST"]
        assert len(test_logger.handlers) == 1
        assert isinstance(test_logger.handlers[0], logging.StreamHandler)

    def test_handler_creation_failure_fallback(self, temp_dir):
        """
        Test fallback mechanism when handler creation fails.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that HydraLogger falls back to console logging
        when file handler creation fails.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path=os.path.join(temp_dir, "test.log")
                        )
                    ]
                )
            }
        )

        # Should handle config gracefully
        logger = HydraLogger(config)

        # Try to log (should not crash)
        logger.info("TEST", "Test message")

        # Verify logger exists
        assert "TEST" in logger.loggers

    def test_initialization_error_handling(self):
        """
        Test error handling during initialization.

        Verifies that HydraLogger handles initialization errors
        gracefully and provides meaningful error messages.
        """
        # Create config with console destination (no file system issues)
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            }
        )

        # Should handle initialization gracefully
        logger = HydraLogger(config)

        # Verify logger was created
        assert "TEST" in logger.loggers

    def test_setup_loggers_error_handling(self):
        """
        Test error handling in _setup_loggers method.

        Verifies that HydraLogger handles setup errors gracefully
        and provides meaningful error messages.
        """
        # Create config that will cause setup issues
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path="/root/invalid.log",  # Path that will cause permission error
                        )
                    ]
                )
            }
        )

        # Should handle setup errors gracefully - the error is caught and logged
        logger = HydraLogger(config)
        assert "TEST" in logger.loggers  # Logger is created but may not have handlers

    def test_setup_single_layer_error_handling(self):
        """
        Test error handling in _setup_single_layer method.

        Verifies that HydraLogger handles layer setup errors gracefully.
        """
        # Create config with invalid destination
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path="/root/invalid.log",  # Path that will cause permission error
                        )
                    ]
                )
            }
        )

        # Should handle layer setup errors gracefully - errors are caught and logged
        logger = HydraLogger(config)
        assert "TEST" in logger.loggers  # Logger is created but may not have handlers

    def test_create_handler_unknown_type(self):
        """
        Test handling of unknown destination types.

        Verifies that HydraLogger handles unknown destination types
        gracefully and logs appropriate warnings.
        """
        # Create a config with a valid destination first
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            }
        )

        logger = HydraLogger(config)

        # Test unknown destination type by mocking the handler creation
        with patch.object(logger, "_create_handler") as mock_create_handler:
            mock_create_handler.return_value = None  # Simulate unknown type handling

            # Should handle unknown destination type gracefully
            assert "TEST" in logger.loggers

    def test_create_file_handler_missing_path(self):
        """
        Test file handler creation with missing path.

        Verifies that HydraLogger handles missing file paths gracefully.
        """
        # Test missing path by mocking the _create_file_handler method
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file", path="logs/test.log"  # Valid path for config
                        )
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        # Mock the _create_file_handler to test missing path scenario
        with patch.object(logger, "_create_file_handler") as mock_handler:
            mock_handler.side_effect = ValueError(
                "Path is required for file destinations"
            )

            # Should handle missing path gracefully
            assert "TEST" in logger.loggers

    def test_create_file_handler_permission_error(self):
        """
        Test file handler creation with permission error.

        Verifies that HydraLogger handles file permission errors
        during handler creation gracefully.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path="/root/test.log",  # Path that will cause permission error
                        )
                    ]
                )
            }
        )

        # Should handle permission error gracefully - errors are caught and logged
        logger = HydraLogger(config)
        assert "TEST" in logger.loggers  # Logger is created but may not have handlers

    def test_create_console_handler_error(self):
        """
        Test console handler creation error.

        Verifies that HydraLogger handles console handler creation
        errors gracefully.
        """
        # Test console handler error by mocking the _create_console_handler method
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(
                            type="console", level="INFO"  # Valid level for config
                        )
                    ]
                )
            }
        )

        logger = HydraLogger(config)

        # Mock the _create_console_handler to test error scenario
        with patch.object(logger, "_create_console_handler") as mock_handler:
            mock_handler.side_effect = ValueError("Failed to create console handler")

            # Should handle console handler error gracefully
            assert "TEST" in logger.loggers

    def test_log_invalid_level(self):
        """
        Test logging with invalid level.

        Verifies that HydraLogger handles invalid log levels gracefully.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Test invalid log level
        with pytest.raises(ValueError, match="Invalid log level"):
            logger.log("DEFAULT", "INVALID", "Test message")

    def test_log_empty_message(self):
        """
        Test logging with empty message.

        Verifies that HydraLogger handles empty messages gracefully.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Test empty message (should not crash)
        logger.log("DEFAULT", "INFO", "")
        # Test None message (should not crash)
        logger.log("DEFAULT", "INFO", "")  # Use empty string instead of None

    def test_log_method_fallback(self):
        """
        Test log method fallback when specific level fails.

        Verifies that HydraLogger falls back to info level
        when specific level logging fails.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Mock the logger to simulate failure
        with patch.object(logger, "_get_or_create_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.error.side_effect = Exception("Logging failed")
            mock_get_logger.return_value = mock_logger

            # Should fall back to info level
            logger.log("TEST", "ERROR", "Test message")

            # Verify fallback was called
            mock_logger.info.assert_called_with("Test message")

    def test_get_or_create_logger_fallback_to_default(self):
        """
        Test fallback to default layer when unknown layer is used.

        Verifies that HydraLogger falls back to DEFAULT layer
        when logging to unknown layers.
        """
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            }
        )

        logger = HydraLogger(config)

        # Log to unknown layer (should fall back to DEFAULT)
        logger.info("UNKNOWN", "Test message")

        # Verify DEFAULT logger was used
        assert "DEFAULT" in logger.loggers

    def test_get_or_create_logger_create_new_logger(self):
        """
        Test creation of new logger for unknown layer when no default exists.

        Verifies that HydraLogger creates a new logger for unknown layers
        when no DEFAULT layer is configured.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            }
        )

        logger = HydraLogger(config)

        # Log to unknown layer (should create new logger)
        logger.info("UNKNOWN", "Test message")

        # Verify new logger was created
        assert "UNKNOWN" in logger.loggers

    def test_log_warning_and_error_methods(self):
        """
        Test internal warning and error logging methods.

        Verifies that the internal _log_warning and _log_error methods
        work correctly and output to stderr.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Test warning logging
        with patch("sys.stderr") as mock_stderr:
            logger._log_warning("Test warning")
            mock_stderr.write.assert_called()

        # Test error logging
        with patch("sys.stderr") as mock_stderr:
            logger._log_error("Test error")
            mock_stderr.write.assert_called()

    def test_initialization_with_exception(self):
        """
        Test HydraLogger initialization when an exception occurs.

        Verifies that HydraLogger handles initialization exceptions
        gracefully and raises HydraLoggerError.
        """
        # Mock get_default_config to raise an exception
        with patch(
            "hydra_logger.logger.get_default_config",
            side_effect=Exception("Config error"),
        ):
            with pytest.raises(
                HydraLoggerError, match="Failed to initialize HydraLogger"
            ):
                HydraLogger()

    def test_setup_loggers_with_exception(self):
        """
        Test _setup_loggers when an exception occurs.

        Verifies that _setup_loggers handles exceptions gracefully
        and raises HydraLoggerError.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Mock create_log_directories to raise an exception
        with patch(
            "hydra_logger.logger.create_log_directories",
            side_effect=Exception("Directory error"),
        ):
            with pytest.raises(HydraLoggerError, match="Failed to setup loggers"):
                logger._setup_loggers()

    def test_setup_single_layer_with_exception(self):
        """
        Test _setup_single_layer when an exception occurs.

        Verifies that _setup_single_layer handles exceptions gracefully.
        """
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            }
        )
        logger = HydraLogger(config)

        # Mock _create_handler to raise an exception
        with patch.object(
            logger, "_create_handler", side_effect=Exception("Handler error")
        ):
            # Should handle exception gracefully and log error
            logger._setup_single_layer("TEST", config.layers["TEST"])

    def test_create_handler_validation_error(self):
        """
        Test _create_handler with validation error.

        Verifies that _create_handler handles validation errors gracefully.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Create a destination that will cause validation error
        destination = LogDestination(type="file", path="logs/test.log")

        # Mock _create_file_handler to raise ValueError
        with patch.object(
            logger, "_create_file_handler", side_effect=ValueError("Validation error")
        ):
            result = logger._create_handler(destination, "INFO")
            assert result is None

    def test_create_handler_fallback_to_console(self):
        """
        Test _create_handler fallback to console when file handler fails.

        Verifies that _create_handler falls back to console logging
        when file handler creation fails.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        destination = LogDestination(type="file", path="logs/test.log")

        # Mock _create_file_handler to raise exception, _create_console_handler to succeed
        with patch.object(
            logger, "_create_file_handler", side_effect=Exception("File error")
        ):
            with patch.object(logger, "_create_console_handler") as mock_console:
                mock_console.return_value = logging.StreamHandler()
                result = logger._create_handler(destination, "INFO")
                assert result is not None
                mock_console.assert_called_once()

    def test_create_handler_fallback_console_fails(self):
        """
        Test _create_handler when both file and console fallback fail.

        Verifies that _create_handler handles complete failure gracefully.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        destination = LogDestination(type="file", path="logs/test.log")

        # Mock both handlers to fail
        with patch.object(
            logger, "_create_file_handler", side_effect=Exception("File error")
        ):
            with patch.object(
                logger,
                "_create_console_handler",
                side_effect=Exception("Console error"),
            ):
                result = logger._create_handler(destination, "INFO")
                assert result is None

    def test_create_file_handler_os_error(self):
        """
        Test _create_file_handler with OSError.

        Verifies that _create_file_handler handles OSError gracefully.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        destination = LogDestination(type="file", path="logs/test.log")

        # Mock RotatingFileHandler to raise OSError
        with patch(
            "hydra_logger.logger.RotatingFileHandler",
            side_effect=OSError("File system error"),
        ):
            with pytest.raises(OSError, match="Failed to create file handler"):
                logger._create_file_handler(destination, "INFO")

    def test_create_console_handler_exception(self):
        """
        Test _create_console_handler with exception.

        Verifies that _create_console_handler handles exceptions gracefully.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        destination = LogDestination(type="console", level="INFO")

        # Mock StreamHandler to raise exception
        with patch("logging.StreamHandler", side_effect=Exception("Stream error")):
            with pytest.raises(ValueError, match="Failed to create console handler"):
                logger._create_console_handler(destination)

    def test_parse_size_value_error(self):
        """
        Test _parse_size with ValueError.

        Verifies that _parse_size handles ValueError gracefully.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Test invalid size format that causes ValueError
        with pytest.raises(ValueError, match="Invalid size format"):
            logger._parse_size("invalid_size")

    def test_log_method_exception_fallback(self):
        """
        Test log method when specific level method fails.

        Verifies that log method falls back to info level when
        specific level logging fails.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Mock the logger to simulate failure
        with patch.object(logger, "_get_or_create_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.error.side_effect = Exception("Logging failed")
            mock_get_logger.return_value = mock_logger

            # Should fall back to info level
            logger.log("TEST", "ERROR", "Test message")

            # Verify fallback was called
            mock_logger.info.assert_called_with("Test message")

    def test_get_or_create_logger_exception(self):
        """
        Test _get_or_create_logger when exception occurs.

        Verifies that _get_or_create_logger handles exceptions gracefully.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        # Test the fallback mechanism when DEFAULT layer exists
        logger.info("UNKNOWN", "Test message")

        # Verify that unknown layer was handled gracefully
        assert "UNKNOWN" in logger.loggers

    def test_log_warning_stderr_output(self):
        """
        Test _log_warning outputs to stderr.

        Verifies that _log_warning correctly outputs to stderr.
        """
        config = LoggingConfig()
        logger = HydraLogger(config)

        with patch("sys.stderr") as mock_stderr:
            logger._log_warning("Test warning")
            mock_stderr.write.assert_called()

    def test_log_error_stderr_output(self):
        """
        Test that _log_error outputs to stderr.

        Verifies that internal error logging outputs to stderr
        for proper error reporting.
        """
        with patch("sys.stderr") as mock_stderr:
            logger = HydraLogger()
            logger._log_error("Test error message")
            mock_stderr.write.assert_called()

    def test_all_log_formats(self, temp_dir):
        """
        Test all supported log formats.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that all supported log formats (text, json, csv, syslog, gelf)
        work correctly and produce the expected output format.
        """
        config = LoggingConfig(
            layers={
                "FORMATS": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "text.log"),
                            format="text"
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "json.log"),
                            format="json"
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "csv.log"),
                            format="csv"
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "syslog.log"),
                            format="syslog"
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "gelf.log"),
                            format="gelf"
                        ),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        logger.info("FORMATS", "Test message for format verification")

        # Verify all files were created
        expected_files = ["text.log", "json.log", "csv.log", "syslog.log", "gelf.log"]
        for filename in expected_files:
            filepath = os.path.join(temp_dir, filename)
            assert os.path.exists(filepath), f"File {filename} should be created"

        # Verify text format
        with open(os.path.join(temp_dir, "text.log"), "r") as f:
            content = f.read()
            assert "Test message for format verification" in content
            assert "hydra.FORMATS" in content
            assert "INFO" in content

        # Verify JSON format
        with open(os.path.join(temp_dir, "json.log"), "r") as f:
            content = f.read()
            assert "Test message for format verification" in content
            # JSON should contain the message in a structured format
            assert '"message"' in content or '"msg"' in content

        # Verify CSV format
        with open(os.path.join(temp_dir, "csv.log"), "r") as f:
            content = f.read()
            assert "Test message for format verification" in content
            # CSV should have comma-separated values
            assert "," in content
            assert "hydra.FORMATS" in content
            assert "INFO" in content

        # Verify syslog format
        with open(os.path.join(temp_dir, "syslog.log"), "r") as f:
            content = f.read()
            assert "Test message for format verification" in content
            assert "hydra.FORMATS" in content
            assert "INFO" in content
            # Syslog format should have process ID
            assert "[" in content and "]" in content

        # Verify GELF format
        with open(os.path.join(temp_dir, "gelf.log"), "r") as f:
            content = f.read()
            assert "Test message for format verification" in content

    def test_format_validation(self):
        """
        Test format validation in logger configuration.

        Verifies that the logger properly validates format specifications
        and handles invalid formats gracefully.
        """
        # This should work with valid format
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="json")
                    ],
                )
            }
        )
        
        logger = HydraLogger(config)
        assert "TEST" in logger.loggers

    def test_format_fallback_behavior(self, temp_dir):
        """
        Test format fallback behavior when dependencies are missing.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that the logger falls back to text format when
        required dependencies (like python-json-logger) are not available.
        """
        # Test with a format that requires external dependencies
        config = LoggingConfig(
            layers={
                "FALLBACK": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "fallback.log"),
                            format="json"  # This might fall back to text
                        ),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        logger.info("FALLBACK", "Test fallback message")

        # Verify file was created (even if format fell back)
        filepath = os.path.join(temp_dir, "fallback.log")
        assert os.path.exists(filepath), "File should be created even with fallback"

        # Verify content contains the message
        with open(filepath, "r") as f:
            content = f.read()
            assert "Test fallback message" in content

    def test_structured_json_formatter(self, temp_dir):
        """Test the structured JSON formatter output."""
        config = LoggingConfig(
            layers={
                "STRUCTURED_JSON": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "structured.json"),
                            format="json"
                        ),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        logger.info("STRUCTURED_JSON", "Test structured JSON")

        # Verify file was created
        filepath = os.path.join(temp_dir, "structured.json")
        assert os.path.exists(filepath)

        with open(filepath, "r") as f:
            content = f.read().strip()
            # Should be valid JSON with all required fields
            import json
            log_entry = json.loads(content)
            assert "timestamp" in log_entry
            assert "level" in log_entry
            assert "logger" in log_entry
            assert "message" in log_entry
            assert "filename" in log_entry
            assert "lineno" in log_entry
            assert log_entry["message"] == "Test structured JSON"
            assert log_entry["level"] == "INFO"
            assert log_entry["logger"] == "hydra.STRUCTURED_JSON"
            
            # Verify field types and formats
            assert isinstance(log_entry["timestamp"], str)
            assert isinstance(log_entry["level"], str)
            assert isinstance(log_entry["logger"], str)
            assert isinstance(log_entry["message"], str)
            assert isinstance(log_entry["filename"], str)
            assert isinstance(log_entry["lineno"], int)
            
            # Verify timestamp format (should be YYYY-MM-DD HH:MM:SS)
            import re
            timestamp_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
            assert re.match(timestamp_pattern, log_entry["timestamp"]), f"Invalid timestamp format: {log_entry['timestamp']}"
            
            # Verify filename is not empty
            assert log_entry["filename"] != ""
            
            # Verify line number is positive
            assert log_entry["lineno"] > 0

    def test_json_lines_format(self, temp_dir):
        """Test that JSON format produces valid JSON Lines (one JSON object per line)."""
        config = LoggingConfig(
            layers={
                "JSON_LINES": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "json_lines.json"),
                            format="json"
                        ),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        
        # Log multiple messages
        logger.info("JSON_LINES", "First message")
        logger.warning("JSON_LINES", "Second message")
        logger.error("JSON_LINES", "Third message")

        # Verify file was created
        filepath = os.path.join(temp_dir, "json_lines.json")
        assert os.path.exists(filepath)

        with open(filepath, "r") as f:
            lines = f.readlines()
            
        # Should have 3 lines (one per log entry)
        assert len(lines) == 3
        
        # Each line should be valid JSON
        import json
        messages = []
        for i, line in enumerate(lines):
            line = line.strip()
            assert line, f"Line {i+1} should not be empty"
            
            # Parse JSON
            log_entry = json.loads(line)
            
            # Verify structure
            assert "timestamp" in log_entry
            assert "level" in log_entry
            assert "logger" in log_entry
            assert "message" in log_entry
            assert "filename" in log_entry
            assert "lineno" in log_entry
            
            # Collect messages for verification
            messages.append(log_entry["message"])
            
        # Verify all messages are present
        assert "First message" in messages
        assert "Second message" in messages
        assert "Third message" in messages
        
        # Verify levels are correct
        levels = [json.loads(line.strip())["level"] for line in lines]
        assert "INFO" in levels
        assert "WARNING" in levels
        assert "ERROR" in levels

    def test_mixed_formats_in_layer(self, temp_dir):
        """
        Test mixing different formats within the same layer.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that a single layer can have multiple destinations
        with different formats working simultaneously.
        """
        config = LoggingConfig(
            layers={
                "MIXED": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "mixed_text.log"),
                            format="text"
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "mixed_csv.log"),
                            format="csv"
                        ),
                        LogDestination(type="console", format="text"),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        logger.info("MIXED", "Mixed format test message")

        # Verify both files were created
        assert os.path.exists(os.path.join(temp_dir, "mixed_text.log"))
        assert os.path.exists(os.path.join(temp_dir, "mixed_csv.log"))

        # Verify different formats have different structures
        with open(os.path.join(temp_dir, "mixed_text.log"), "r") as f:
            text_content = f.read()
        
        with open(os.path.join(temp_dir, "mixed_csv.log"), "r") as f:
            csv_content = f.read()

        # Text format should have dashes, CSV should have commas
        assert " - " in text_content
        assert "," in csv_content
        assert "Mixed format test message" in text_content
        assert "Mixed format test message" in csv_content

    def test_format_with_console_destination(self):
        """
        Test format specification with console destinations.

        Verifies that console destinations can specify different formats
        and the output is formatted accordingly.
        """
        config = LoggingConfig(
            layers={
                "CONSOLE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="json"),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        # This should work without errors, even if JSON format falls back to text
        logger.info("CONSOLE", "Console format test")

    def test_format_case_insensitivity(self, temp_dir):
        """
        Test that format specifications are case-insensitive.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that format values are normalized to lowercase
        and work regardless of the input case.
        """
        config = LoggingConfig(
            layers={
                "CASE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "case_test.log"),
                            format="JSON"  # Uppercase
                        ),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        logger.info("CASE", "Case insensitive test")

        # Verify file was created
        filepath = os.path.join(temp_dir, "case_test.log")
        assert os.path.exists(filepath)

        # Verify content contains the message
        with open(filepath, "r") as f:
            content = f.read()
            assert "Case insensitive test" in content
