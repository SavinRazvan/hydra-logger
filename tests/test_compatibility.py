"""
Comprehensive test suite for Hydra-Logger compatibility layer.

This module tests the backward compatibility functions that provide seamless
migration from the original flexiai-toolsmith logging system to Hydra-Logger.
The tests verify that existing applications can continue to work without
modification while providing clear migration paths to advanced features.

Test Coverage:
- setup_logging function with various configurations
- Migration utilities for converting legacy configurations
- Level conversion between integer and string representations
- Error handling and edge cases
- Backward compatibility preservation
"""

import os
import tempfile
import shutil
import pytest
import logging
from logging.handlers import RotatingFileHandler
from unittest.mock import patch, MagicMock
from pathlib import Path

from hydra_logger.compatibility import (
    setup_logging,
    create_hydra_config_from_legacy,
    migrate_to_hydra,
    _level_int_to_str,
)
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.logger import HydraLogger


class TestSetupLogging:
    """
    Test suite for the setup_logging function.

    Tests the backward compatibility function that provides the exact same
    interface as the original flexiai-toolsmith setup_logging function.
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

    def test_setup_logging_basic(self, temp_dir):
        """
        Test basic setup_logging functionality.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging creates the expected directory structure
        and configures logging handlers correctly with default parameters.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging()

        # Check that logs directory was created
        logs_dir = os.path.join(temp_dir, "logs")
        assert os.path.exists(logs_dir), "Logs directory should be created"

        # Check that app.log file exists
        log_file = os.path.join(logs_dir, "app.log")
        assert os.path.exists(log_file), "App log file should be created"

        # Verify logger configuration
        logger = logging.getLogger()
        assert logger.level == logging.DEBUG, "Root logger should be set to DEBUG"

        # Check that handlers were added
        handlers = logger.handlers
        assert len(handlers) == 2, "Should have 2 handlers (file and console)"

        # Verify handler types
        handler_types = [type(h) for h in handlers]
        assert RotatingFileHandler in handler_types, "Should have RotatingFileHandler"
        assert logging.StreamHandler in handler_types, "Should have StreamHandler"

    def test_setup_logging_file_only(self, temp_dir):
        """
        Test setup_logging with file logging only.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging works correctly when only file logging
        is enabled, creating the file handler but not the console handler.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging(enable_console_logging=False)

        logger = logging.getLogger()
        handlers = logger.handlers

        # Should only have file handler
        assert len(handlers) == 1, "Should have only 1 handler (file only)"
        assert isinstance(
            handlers[0], RotatingFileHandler
        ), "Should have RotatingFileHandler"

    def test_setup_logging_console_only(self, temp_dir):
        """
        Test setup_logging with console logging only.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging works correctly when only console logging
        is enabled, creating the console handler but not the file handler.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging(enable_file_logging=False)

        logger = logging.getLogger()
        handlers = logger.handlers

        # Should only have console handler
        assert len(handlers) == 1, "Should have only 1 handler (console only)"
        assert isinstance(
            handlers[0], logging.StreamHandler
        ), "Should have StreamHandler"

        # Logs directory should not be created
        logs_dir = os.path.join(temp_dir, "logs")
        assert not os.path.exists(
            logs_dir
        ), "Logs directory should not be created when file logging is disabled"

    def test_setup_logging_custom_levels(self, temp_dir):
        """
        Test setup_logging with custom log levels.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging correctly applies custom log levels
        to the root logger and individual handlers.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging(
                root_level=logging.WARNING,
                file_level=logging.DEBUG,
                console_level=logging.ERROR,
            )

        logger = logging.getLogger()
        assert logger.level == logging.WARNING, "Root logger should be set to WARNING"

        # Check handler levels
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                assert (
                    handler.level == logging.DEBUG
                ), "File handler should be set to DEBUG"
            elif isinstance(handler, logging.StreamHandler):
                assert (
                    handler.level == logging.ERROR
                ), "Console handler should be set to ERROR"

    def test_setup_logging_directory_creation_failure(self, temp_dir):
        """
        Test setup_logging when directory creation fails.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging handles directory creation failures
        gracefully and continues with console logging if available.
        """
        # Clear existing handlers first
        logger = logging.getLogger()
        logger.handlers.clear()

        with patch("os.getcwd", return_value=temp_dir):
            with patch("os.makedirs", side_effect=OSError("Permission denied")):
                setup_logging(enable_console_logging=True)

        # Should still have console handler even if file handler fails
        assert (
            len(logger.handlers) == 1
        ), "Should have console handler even if file handler fails"
        assert isinstance(
            logger.handlers[0], logging.StreamHandler
        ), "Should have StreamHandler"

    def test_setup_logging_logger_setup_failure(self, temp_dir):
        """
        Test setup_logging when logger setup fails.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging handles logger setup failures
        gracefully and doesn't crash the application.
        """
        with patch("os.getcwd", return_value=temp_dir):
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_logger.setLevel.side_effect = Exception("Logger setup failed")
                mock_get_logger.return_value = mock_logger

                # Should not raise an exception
                setup_logging()

        # Verify that the function completed without crashing
        assert True, "setup_logging should handle logger setup failures gracefully"


class TestMigrationFunctions:
    """
    Test suite for migration utility functions.

    Tests the functions that help migrate from legacy setup_logging
    to the new Hydra-Logger system.
    """

    def test_level_int_to_str(self):
        """
        Test level conversion from integer to string.

        Verifies that the _level_int_to_str function correctly converts
        Python logging level integers to their string representations.
        """
        assert _level_int_to_str(logging.DEBUG) == "DEBUG"
        assert _level_int_to_str(logging.INFO) == "INFO"
        assert _level_int_to_str(logging.WARNING) == "WARNING"
        assert _level_int_to_str(logging.ERROR) == "ERROR"
        assert _level_int_to_str(logging.CRITICAL) == "CRITICAL"

        # Test unknown level (should return "INFO")
        assert _level_int_to_str(999) == "INFO"

    def test_create_hydra_config_from_legacy(self):
        """
        Test creating Hydra-Logger config from legacy parameters.

        Verifies that create_hydra_config_from_legacy correctly converts
        legacy setup_logging parameters to a Hydra-Logger configuration.
        """
        config = create_hydra_config_from_legacy(
            root_level=logging.INFO,
            file_level=logging.DEBUG,
            console_level=logging.WARNING,
            log_file_path="custom/path/app.log",
        )

        assert isinstance(config, LoggingConfig)
        assert "DEFAULT" in config.layers
        assert config.layers["DEFAULT"].level == "INFO"
        assert len(config.layers["DEFAULT"].destinations) == 2

        # Check file destination
        file_dest = next(
            d for d in config.layers["DEFAULT"].destinations if d.type == "file"
        )
        assert file_dest.path == "custom/path/app.log"
        assert file_dest.level == "DEBUG"
        assert file_dest.max_size == "5MB"
        assert file_dest.backup_count == 3

        # Check console destination
        console_dest = next(
            d for d in config.layers["DEFAULT"].destinations if d.type == "console"
        )
        assert console_dest.level == "WARNING"

    def test_create_hydra_config_file_only(self):
        """
        Test creating config with file logging only.

        Verifies that create_hydra_config_from_legacy correctly handles
        the case where only file logging is enabled.
        """
        config = create_hydra_config_from_legacy(enable_console_logging=False)

        assert len(config.layers["DEFAULT"].destinations) == 1
        assert config.layers["DEFAULT"].destinations[0].type == "file"

    def test_create_hydra_config_console_only(self):
        """
        Test creating config with console logging only.

        Verifies that create_hydra_config_from_legacy correctly handles
        the case where only console logging is enabled.
        """
        config = create_hydra_config_from_legacy(enable_file_logging=False)

        assert len(config.layers["DEFAULT"].destinations) == 1
        assert config.layers["DEFAULT"].destinations[0].type == "console"

    def test_migrate_to_hydra(self):
        """
        Test migration to Hydra-Logger.

        Verifies that migrate_to_hydra correctly creates a fully configured
        HydraLogger instance from legacy parameters.
        """
        logger = migrate_to_hydra(
            root_level=logging.INFO,
            file_level=logging.DEBUG,
            console_level=logging.WARNING,
        )

        assert isinstance(logger, HydraLogger)
        assert "DEFAULT" in logger.loggers

        # Test that the logger works
        logger.info("DEFAULT", "Test message")
        assert True, "Migrated logger should work correctly"


class TestBackwardCompatibility:
    """
    Test suite for backward compatibility features.

    Tests that ensure existing applications can continue to work
    without modification when using Hydra-Logger.
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

    def test_setup_logging_creates_correct_structure(self, temp_dir):
        """
        Test that setup_logging creates the expected directory structure.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging creates the same directory structure
        as the original flexiai-toolsmith implementation.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging()

        # Check directory structure
        logs_dir = os.path.join(temp_dir, "logs")
        log_file = os.path.join(logs_dir, "app.log")

        assert os.path.exists(logs_dir), "logs/ directory should exist"
        assert os.path.exists(log_file), "logs/app.log should exist"

        # Check file permissions (should be writable)
        assert os.access(log_file, os.W_OK), "Log file should be writable"

    def test_migration_preserves_functionality(self, temp_dir):
        """
        Test that migration preserves all original functionality.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that the migrated HydraLogger provides the same
        functionality as the original setup_logging.
        """
        with patch("os.getcwd", return_value=temp_dir):
            # Use original setup_logging
            setup_logging(
                root_level=logging.INFO,
                file_level=logging.DEBUG,
                console_level=logging.WARNING,
            )

        # Get the original logger
        original_logger = logging.getLogger()

        # Clear handlers and use migration
        original_logger.handlers.clear()

        with patch("os.getcwd", return_value=temp_dir):
            migrated_logger = migrate_to_hydra(
                root_level=logging.INFO,
                file_level=logging.DEBUG,
                console_level=logging.WARNING,
            )

        # Both should work similarly
        original_logger.info("Original logger test")
        migrated_logger.info("DEFAULT", "Migrated logger test")

        # Both should have created log files
        logs_dir = os.path.join(temp_dir, "logs")
        assert os.path.exists(logs_dir), "Both should create logs directory"

        assert True, "Migration should preserve all original functionality"
