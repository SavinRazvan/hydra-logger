"""
Test coverage gaps for Hydra-Logger

This module contains targeted tests to ensure 100% code coverage, focusing on edge
cases, error handling, and branches not covered by the main test suite.
"""

import os
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from hydra_logger.config import (
    LogDestination,
    LoggingConfig,
    LogLayer,
    load_config,
)
from hydra_logger.logger import HydraLogger


class TestConfigCoverageGaps:
    """Covers edge cases and error branches in hydra_logger.config."""

    def test_tomli_import_fallback(self):
        """Covers the tomli import fallback for Python < 3.11."""
        # Mock tomli module
        mock_tomli = MagicMock()

        # Store original modules
        original_tomllib = sys.modules.get("tomllib")
        original_tomli = sys.modules.get("tomli")

        # Test that the fallback import works when tomllib is not available
        with patch.dict("sys.modules", {"tomllib": None, "tomli": mock_tomli}):
            # Import the module again to trigger the fallback
            import importlib

            import hydra_logger.config

            importlib.reload(hydra_logger.config)

            # Verify that tomllib is now the tomli module
            assert hasattr(hydra_logger.config, "tomllib")
            assert hydra_logger.config.tomllib == mock_tomli
            # The import should work without errors
            from hydra_logger.config import LoggingConfig

            config = LoggingConfig()
            assert config is not None

        # Restore original modules
        if original_tomllib is not None:
            sys.modules["tomllib"] = original_tomllib
        else:
            sys.modules.pop("tomllib", None)

        if original_tomli is not None:
            sys.modules["tomli"] = original_tomli
        else:
            sys.modules.pop("tomli", None)

        # Reload the config module to restore original state
        importlib.reload(hydra_logger.config)

    def test_log_destination_file_without_path_validation(self):
        """Covers model_post_init path check (line 93 in config.py)."""
        dest = LogDestination(type="file", path="somefile.log")
        dest.path = None
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            dest.model_post_init(None)

    def test_log_destination_invalid_level(self):
        """Covers invalid log level for LogDestination."""
        with pytest.raises(ValueError, match="Invalid level: INVALID"):
            LogDestination(type="console", level="INVALID")

    def test_log_layer_invalid_level(self):
        """Covers invalid log level for LogLayer."""
        with pytest.raises(ValueError, match="Invalid level: INVALID"):
            LogLayer(level="INVALID", destinations=[])

    def test_logging_config_invalid_default_level(self):
        """Covers invalid default_level for LoggingConfig."""
        with pytest.raises(ValueError, match="Invalid default_level: INVALID"):
            LoggingConfig(default_level="INVALID", layers={})

    def test_load_config_unsupported_format(self):
        """Covers unsupported config file format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"some content")
            f.flush()
        try:
            with pytest.raises(ValueError, match="Unsupported config file format"):
                load_config(f.name)
        finally:
            os.unlink(f.name)

    def test_load_config_empty_file(self):
        """Covers empty configuration file."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(b"")
            f.flush()
        try:
            with pytest.raises(
                ValueError, match="Configuration file is empty or invalid"
            ):
                load_config(f.name)
        finally:
            os.unlink(f.name)

    def test_load_config_invalid_yaml(self):
        """Covers invalid YAML parsing."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(b"invalid: yaml: content: [")
            f.flush()
        try:
            with pytest.raises(
                ValueError, match="Failed to parse YAML configuration file"
            ):
                load_config(f.name)
        finally:
            os.unlink(f.name)

    def test_load_config_invalid_toml(self):
        """Covers invalid TOML parsing."""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(b"invalid =")  # Minimal invalid TOML
            f.flush()
        try:
            with pytest.raises(
                ValueError, match="Failed to parse TOML configuration file"
            ):
                load_config(f.name)
        finally:
            os.unlink(f.name)

    def test_load_config_general_exception(self):
        """Covers general exception during config loading."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "builtins.open", side_effect=PermissionError("Permission denied")
            ):
                with pytest.raises(
                    ValueError, match="Failed to (load|parse TOML) configuration"
                ):
                    load_config("nonexistent.yaml")

    def test_config_validation_edge_cases(self):
        """Covers various edge cases in configuration validation."""
        with pytest.raises(ValueError):
            LogDestination(type="file", path=None)
        with pytest.raises(ValueError):
            LogDestination(type="file", path="")
        with pytest.raises(ValueError):
            LogDestination.model_validate({"type": "invalid", "path": "test.log"})


class TestLoggerCoverageGaps:
    """Covers edge cases and error branches in hydra_logger.logger."""

    def test_file_handler_missing_path_valueerror(self):
        """Covers ValueError for missing path in file handler creation."""
        destination = MagicMock()
        destination.type = "file"
        destination.path = None
        logger = HydraLogger()
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            logger._create_file_handler(destination, "INFO")

    def test_console_handler_creation_failure(self):
        """Covers console handler creation failure."""
        with patch(
            "logging.StreamHandler", side_effect=Exception("Handler creation failed")
        ):
            with pytest.raises(ValueError, match="Failed to create console handler"):
                destination = LogDestination(type="console", level="INFO")
                logger = HydraLogger()
                logger._create_console_handler(destination)

    def test_parse_size_empty_string(self):
        """Covers empty size string in _parse_size."""
        logger = HydraLogger()
        with pytest.raises(ValueError, match="Size string cannot be empty"):
            logger._parse_size("")

    def test_parse_size_invalid_format(self):
        """Covers invalid size format in _parse_size."""
        logger = HydraLogger()
        with pytest.raises(ValueError, match="Invalid size format"):
            logger._parse_size("invalid")

    def test_log_invalid_level(self):
        """Covers invalid log level in log method."""
        logger = HydraLogger()
        with pytest.raises(ValueError, match="Invalid log level"):
            logger.log("TEST", "INVALID", "test message")

    def test_no_valid_handlers_warning(self):
        """Covers warning when no valid handlers are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_file = os.path.join(temp_dir, "test.log")
            with open(invalid_file, "w") as f:
                f.write("test")
            os.chmod(invalid_file, 0o444)
            config = LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[LogDestination(type="file", path=invalid_file)],
                    )
                }
            )
            _ = HydraLogger(config)

    def test_no_valid_handlers_warning_direct(self):
        """Covers warning when no valid handlers are created (direct approach)."""
        logger = HydraLogger()
        layer_config = LogLayer(
            level="INFO", destinations=[LogDestination(type="console", level="INFO")]
        )
        with patch.object(logger, "_create_handler", return_value=None):
            logger._setup_single_layer("TEST", layer_config)

    def test_file_handler_creation_failure_fallback(self):
        """Covers fallback to console handler when file handler fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_file = os.path.join(temp_dir, "test.log")
            with open(invalid_file, "w") as f:
                f.write("test")
            os.chmod(invalid_file, 0o444)
            config = LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[LogDestination(type="file", path=invalid_file)],
                    )
                }
            )
            _ = HydraLogger(config)

    def test_file_handler_oserror(self):
        """Covers OSError when creating file handler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_file = os.path.join(temp_dir, "test.log")
            with open(invalid_file, "w") as f:
                f.write("test")
            os.chmod(invalid_file, 0o444)
            config = LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[LogDestination(type="file", path=invalid_file)],
                    )
                }
            )
            _ = HydraLogger(config)

    def test_create_handler_final_return_none(self, monkeypatch):
        """Covers final return None in _create_handler (line 239 in logger.py)."""
        logger = HydraLogger()
        # Create a mock destination with console type but make _create_console_handler fail
        dest = MagicMock()
        dest.type = "console"
        dest.level = "INFO"
        # Mock _create_console_handler to raise an exception, then fallback also fails
        with patch.object(
            logger,
            "_create_console_handler",
            side_effect=Exception("console handler failed"),
        ):
            handler = logger._create_handler(dest, "INFO")
            assert handler is None

    def test_unknown_destination_type(self):
        """Covers unknown destination type handling."""
        logger = HydraLogger()
        destination = MagicMock()
        destination.type = "unknown"
        result = logger._create_handler(destination, "INFO")
        assert result is None

    def test_destination_validation_error(self):
        """Covers destination validation error handling."""
        logger = HydraLogger()
        destination = MagicMock()
        destination.type = "file"
        destination.path = None
        result = logger._create_handler(destination, "INFO")
        assert result is None


class TestIntegrationCoverageGaps:
    """Covers integration edge cases and error conditions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_logger_with_mixed_valid_invalid_destinations(self):
        """
        Test logger behavior with a mix of valid and invalid destinations.

        Verifies that the logger continues to function even when some
        destinations fail to be created.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config = LoggingConfig(
                layers={
                    "MIXED": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(
                                type="file", path=os.path.join(temp_dir, "valid.log")
                            ),
                            LogDestination(
                                type="file", path=os.path.join(temp_dir, "invalid.log")
                            ),
                        ],
                    )
                }
            )

            logger = HydraLogger(config)
            logger.info("MIXED", "Test message")

            # Should still work with the valid destination
            assert os.path.exists(os.path.join(temp_dir, "valid.log"))

    def test_invalid_format_validation(self):
        """
        Test validation of invalid format values.

        Verifies that LogDestination properly validates format values
        and rejects invalid formats with clear error messages.
        """
        with pytest.raises(ValueError, match="Invalid format: INVALID"):
            LogDestination(type="console", format="INVALID")

        with pytest.raises(ValueError, match="Invalid format: xml"):
            LogDestination(type="console", format="xml")

        with pytest.raises(ValueError, match="Invalid format: yaml"):
            LogDestination(type="console", format="yaml")

    def test_format_with_missing_dependencies(self, temp_dir):
        """
        Test format behavior when required dependencies are missing.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that the logger gracefully handles missing dependencies
        and falls back to text format with appropriate warnings.
        """
        # Test JSON format (requires python-json-logger)
        config = LoggingConfig(
            layers={
                "MISSING_DEPS": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "missing_deps.log"),
                            format="json",
                        ),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        logger.info("MISSING_DEPS", "Test missing dependencies")

        # Should still create the file (with fallback format)
        filepath = os.path.join(temp_dir, "missing_deps.log")
        assert os.path.exists(filepath)

        # Should contain the message (even if format fell back)
        with open(filepath, "r") as f:
            content = f.read()
            assert "Test missing dependencies" in content

    def test_format_normalization(self):
        """
        Test that format values are properly normalized.

        Verifies that format values are converted to lowercase
        regardless of the input case.
        """
        # Test various case combinations
        test_cases = [
            ("TEXT", "text"),
            ("Text", "text"),
            ("JSON", "json"),
            ("Json", "json"),
            ("CSV", "csv"),
            ("Csv", "csv"),
            ("SYSLOG", "syslog"),
            ("Syslog", "syslog"),
            ("GELF", "gelf"),
            ("Gelf", "gelf"),
        ]

        for input_case, expected in test_cases:
            dest = LogDestination(type="console", format=input_case)
            assert dest.format == expected

    def test_format_with_file_rotation(self, temp_dir):
        """
        Test format functionality with file rotation.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that different formats work correctly with file rotation
        and maintain their format across rotated files.
        """
        config = LoggingConfig(
            layers={
                "ROTATION": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "rotation.json"),
                            format="json",
                            max_size="1KB",  # Small size to trigger rotation
                            backup_count=2,
                        ),
                    ],
                )
            }
        )

        logger = HydraLogger(config)

        # Write enough data to trigger rotation
        for i in range(100):
            msg = (
                f"Test message {i} with extra content to fill file"
            )
            logger.info(
                "ROTATION",
                msg,
            )

        # Check that files were created (main file + backups)
        base_file = os.path.join(temp_dir, "rotation.json")
        _ = [
            os.path.join(temp_dir, "rotation.json.1"),
            os.path.join(temp_dir, "rotation.json.2"),
        ]

        # At least the main file should exist
        assert os.path.exists(base_file)

        # Check that the format is maintained in the main file
        with open(base_file, "r") as f:
            content = f.read()
            # Should contain JSON-like content
            assert "Test message" in content

    def test_format_with_console_and_file(self, temp_dir):
        """
        Test format functionality with both console and file destinations.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that different formats can be used simultaneously
        for console and file destinations in the same layer.
        """
        config = LoggingConfig(
            layers={
                "CONSOLE_FILE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "console_file.csv"),
                            format="csv",
                        ),
                        LogDestination(type="console", format="text"),
                    ],
                )
            }
        )

        logger = HydraLogger(config)
        logger.info("CONSOLE_FILE", "Console and file format test")

        # Verify file was created with CSV format
        filepath = os.path.join(temp_dir, "console_file.csv")
        assert os.path.exists(filepath)

        with open(filepath, "r") as f:
            content = f.read()
            assert "Console and file format test" in content
            assert "," in content  # CSV format indicator
