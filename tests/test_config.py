"""
Tests for config functionality.

This module tests the LoggingConfig, LogLayer, and LogDestination classes.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open

from hydra_logger.config import (
    LoggingConfig, LogLayer, LogDestination, get_default_config,
    load_config, create_log_directories
)


class TestLogDestination:
    """
    Test suite for LogDestination model.

    Tests the configuration model for individual logging destinations,
    including validation of file paths, log levels, and destination types.
    """

    def test_valid_file_destination(self):
        """
        Test creating a valid file destination.

        Verifies that a LogDestination with type "file" and a valid path
        can be created successfully with all optional parameters.
        """
        dest = LogDestination(
            type="file",
            path="logs/_tests_logs/app.log",
            level="DEBUG",
            max_size="10MB",
            backup_count=5,
        )

        assert dest.type == "file"
        assert dest.path == "logs/app.log"
        assert dest.level == "DEBUG"
        assert dest.max_size == "10MB"
        assert dest.backup_count == 5

    def test_valid_console_destination(self):
        """
        Test creating a valid console destination.

        Verifies that a LogDestination with type "console" can be created
        successfully without requiring a file path.
        """
        dest = LogDestination(type="console", level="INFO")

        assert dest.type == "console"
        assert dest.path is None
        assert dest.level == "INFO"
        assert dest.max_size == "5MB"  # Default value
        assert dest.backup_count == 3  # Default value

    def test_file_destination_requires_path(self):
        """
        Test that file destinations require a path.

        Verifies that creating a file destination without a path raises
        a validation error.
        """
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", path=None)

    def test_invalid_level(self):
        """
        Test validation of invalid log levels.

        Verifies that LogDestination rejects invalid log level values
        and provides clear error messages.
        """
        with pytest.raises(ValueError, match="Invalid level: INVALID"):
            LogDestination(type="console", level="INVALID")

    def test_level_case_insensitive(self):
        """
        Test that log levels are case-insensitive.

        Verifies that log levels are normalized to uppercase regardless
        of the input case.
        """
        dest = LogDestination(type="console", level="debug")
        assert dest.level == "DEBUG"

        dest = LogDestination(type="console", level="Info")
        assert dest.level == "INFO"

    def test_file_destination_without_path_validation(self):
        """
        Test post-initialization validation for file destinations.

        Verifies that the model_post_init method correctly validates
        that file destinations have a path specified.
        """
        # This should trigger the post-init validation
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", path="")

    def test_valid_formats(self):
        """
        Test all supported log formats.

        Verifies that LogDestination accepts all valid format values
        and normalizes them to lowercase.
        """
        valid_formats = ["text", "json", "csv", "syslog", "gelf"]

        for fmt in valid_formats:
            # Test both lowercase and uppercase
            dest = LogDestination(type="console", format=fmt)
            assert dest.format == fmt

            dest = LogDestination(type="console", format=fmt.upper())
            assert dest.format == fmt

    def test_format_default_value(self):
        """
        Test that format defaults to 'text'.

        Verifies that when no format is specified, it defaults to 'text'.
        """
        dest = LogDestination(type="console")
        assert dest.format == "text"

    def test_invalid_format(self):
        """
        Test validation of invalid log formats.

        Verifies that LogDestination rejects invalid format values
        and provides clear error messages.
        """
        with pytest.raises(ValueError, match="Invalid format: INVALID"):
            LogDestination(type="console", format="INVALID")

        with pytest.raises(ValueError, match="Invalid format: xml"):
            LogDestination(type="console", format="xml")

    def test_format_with_file_destination(self):
        """
        Test format specification with file destinations.

        Verifies that format can be specified for file destinations
        and works correctly with other file-specific settings.
        """
        dest = LogDestination(
            type="file",
            path="logs/app.json",
            format="json",
            level="DEBUG",
            max_size="10MB",
        )

        assert dest.type == "file"
        assert dest.path == "logs/app.json"
        assert dest.format == "json"
        assert dest.level == "DEBUG"
        assert dest.max_size == "10MB"

    def test_format_with_console_destination(self):
        """
        Test format specification with console destinations.

        Verifies that format can be specified for console destinations
        and works correctly with console-specific settings.
        """
        dest = LogDestination(type="console", format="json", level="INFO")

        assert dest.type == "console"
        assert dest.format == "json"
        assert dest.level == "INFO"
        assert dest.path is None


class TestLogLayer:
    """
    Test suite for LogLayer model.

    Tests the configuration model for logging layers, which can contain
    multiple destinations with different settings.
    """

    def test_valid_layer(self):
        """
        Test creating a valid logging layer.

        Verifies that a LogLayer can be created with multiple destinations
        and custom log levels.
        """
        layer = LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="file", path="logs/_tests_logs/debug.log"),
                LogDestination(type="console", level="INFO"),
            ],
        )

        assert layer.level == "DEBUG"
        assert len(layer.destinations) == 2
        assert layer.destinations[0].type == "file"
        assert layer.destinations[1].type == "console"

    def test_default_layer(self):
        """
        Test creating a layer with default values.

        Verifies that LogLayer can be created with minimal parameters
        and uses appropriate default values.
        """
        layer = LogLayer()

        assert layer.level == "INFO"  # Default level
        assert layer.destinations == []  # Empty list by default

    def test_invalid_level(self):
        """
        Test validation of invalid log levels in layers.

        Verifies that LogLayer rejects invalid log level values
        and provides clear error messages.
        """
        with pytest.raises(ValueError, match="Invalid level: INVALID"):
            LogLayer(level="INVALID")


class TestLoggingConfig:
    """
    Test suite for LoggingConfig model.

    Tests the main configuration model that defines the complete
    logging setup for an application.
    """

    def test_valid_config(self):
        """
        Test creating a valid logging configuration.

        Verifies that a LoggingConfig can be created with multiple
        layers and custom default settings.
        """
        config = LoggingConfig(
            layers={"APP": LogLayer(level="INFO"), "DEBUG": LogLayer(level="DEBUG")},
            default_level="WARNING",
        )

        assert len(config.layers) == 2
        assert "APP" in config.layers
        assert "DEBUG" in config.layers
        assert config.default_level == "WARNING"

    def test_default_config(self):
        """
        Test creating a configuration with default values.

        Verifies that LoggingConfig can be created with minimal
        parameters and uses appropriate default values.
        """
        config = LoggingConfig()

        assert config.layers == {}  # Empty dict by default
        assert config.default_level == "INFO"  # Default level

    def test_invalid_default_level(self):
        """
        Test validation of invalid default log levels.

        Verifies that LoggingConfig rejects invalid default log level
        values and provides clear error messages.
        """
        with pytest.raises(ValueError, match="Invalid default_level: INVALID"):
            LoggingConfig(default_level="INVALID")


class TestConfigFunctions:
    """
    Test suite for configuration utility functions.

    Tests the functions that load configurations from files and
    create default configurations.
    """

    def test_get_default_config(self):
        """
        Test getting the default configuration.

        Verifies that get_default_config returns a valid LoggingConfig
        with a DEFAULT layer containing both file and console destinations.
        """
        config = get_default_config()

        assert isinstance(config, LoggingConfig)
        assert "DEFAULT" in config.layers
        assert config.default_level == "INFO"

        layer = config.layers["DEFAULT"]
        assert layer.level == "INFO"
        assert len(layer.destinations) == 2

        # Check file destination
        file_dest = next(d for d in layer.destinations if d.type == "file")
        assert file_dest.path == "logs/app.log"
        assert file_dest.max_size == "5MB"
        assert file_dest.backup_count == 3

        # Check console destination
        console_dest = next(d for d in layer.destinations if d.type == "console")
        assert console_dest.level == "INFO"

    def test_load_config_yaml(self):
        """
        Test loading configuration from YAML file.

        Verifies that load_config can parse YAML files and create
        valid LoggingConfig instances.
        """
        yaml_content = """
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        max_size: 5MB
        backup_count: 3
      - type: console
        level: WARNING
default_level: INFO
"""

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                config = load_config("test_config.yaml")

        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert config.default_level == "INFO"

    def test_load_config_toml(self):
        """
        Test loading configuration from TOML file.

        Verifies that load_config can parse TOML files and create
        valid LoggingConfig instances.
        """
        toml_content = """
[layers.APP]
level = "INFO"

[[layers.APP.destinations]]
type = "file"
path = "logs/app.log"
max_size = "5MB"
backup_count = 3

[[layers.APP.destinations]]
type = "console"
level = "WARNING"

default_level = "INFO"
"""

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=toml_content.encode())):
                config = load_config("test_config.toml")

        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert config.default_level == "INFO"

    def test_load_config_file_not_found(self):
        """
        Test loading configuration from non-existent file.

        Verifies that load_config raises FileNotFoundError when
        the specified file doesn't exist.
        """
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            load_config("nonexistent.yaml")

    def test_load_config_unsupported_format(self):
        """
        Test loading configuration with unsupported file format.

        Verifies that load_config raises ValueError when the file
        has an unsupported extension.
        """
        with patch("pathlib.Path.exists", return_value=True):
            with pytest.raises(ValueError, match="Unsupported config file format"):
                load_config("config.txt")

    def test_load_config_empty_file(self):
        """
        Test loading configuration from empty file.

        Verifies that load_config handles empty files gracefully
        and provides clear error messages.
        """
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="")):
                with pytest.raises(
                    ValueError, match="Configuration file is empty or invalid"
                ):
                    load_config("empty.yaml")

    def test_load_config_invalid_yaml(self):
        """
        Test loading configuration from invalid YAML file.

        Verifies that load_config handles YAML parsing errors
        gracefully and provides clear error messages.
        """
        invalid_yaml = """
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        max_size: 5MB
        backup_count: 3
      - type: console
        level: WARNING
default_level: INFO
invalid_key: [unclosed_bracket
"""

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=invalid_yaml)):
                with pytest.raises(
                    ValueError, match="Failed to parse YAML configuration file"
                ):
                    load_config("invalid.yaml")

    def test_create_log_directories(self):
        """
        Test creating log directories for file destinations.

        Verifies that create_log_directories creates all necessary
        directories for file-based log destinations.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[
                                        LogDestination(type="file", path="logs/_tests_logs/app/main.log"),
                LogDestination(type="file", path="logs/_tests_logs/app/errors.log"),
                    ]
                ),
                "DEBUG": LogLayer(
                    destinations=[
                        LogDestination(type="file", path="logs/_tests_logs/debug/all.log")
                    ]
                ),
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory and create directories
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            try:
                create_log_directories(config)

                # Check that directories were created
                assert os.path.exists("logs/app")
                assert os.path.exists("logs/debug")
            finally:
                os.chdir(original_cwd)

    def test_create_log_directories_no_file_destinations(self):
        """
        Test creating directories when no file destinations exist.

        Verifies that create_log_directories handles configurations
        with only console destinations gracefully.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            }
        )

        # Should not raise any exceptions
        create_log_directories(config)

    def test_create_log_directories_existing_directories(self):
        """
        Test creating directories when they already exist.

        Verifies that create_log_directories handles existing
        directories gracefully without errors.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[LogDestination(type="file", path="logs/app.log")]
                )
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("os.getcwd", return_value=temp_dir):
                # Create directory first
                os.makedirs(os.path.join(temp_dir, "logs"), exist_ok=True)

                # Should not raise any exceptions
                create_log_directories(config)

    def test_create_log_directories_permission_error(self):
        """
        Test creating directories when permission is denied.

        Verifies that create_log_directories handles permission
        errors gracefully and provides clear error messages.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[LogDestination(type="file", path="logs/app.log")]
                )
            }
        )

        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Failed to create log directory"):
                create_log_directories(config)

    def test_create_log_directories_empty_path(self):
        """
        Test creating directories with empty path.

        Verifies that create_log_directories handles empty paths
        gracefully and doesn't attempt to create directories.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[
                        LogDestination(type="file", path="logs/app.log")  # Valid path
                    ]
                )
            }
        )

        # Mock os.makedirs to test the empty directory case
        with patch("os.makedirs") as mock_makedirs:
            create_log_directories(config)
            mock_makedirs.assert_called()

    def test_create_log_directories_os_error_handling(self):
        """
        Test create_log_directories with OSError handling.

        Verifies that create_log_directories handles OSError gracefully
        and provides clear error messages.
        """
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[LogDestination(type="file", path="logs/app.log")]
                )
            }
        )

        # Mock os.makedirs to raise OSError
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Failed to create log directory"):
                create_log_directories(config)

# --- MERGED FROM test_config_coverage.py ---

# All test functions and classes from test_config_coverage.py go here, after the last test class in this file.

# === BEGIN GAP TESTS (from test_config_coverage_gaps.py) ===
import sys
import types
from unittest.mock import patch, MagicMock
import hydra_logger.config as config_mod

def test_tomllib_import_logic(monkeypatch):
    # Simulate Python <3.11: no tomllib, fallback to tomli
    monkeypatch.setitem(sys.modules, 'tomllib', None)
    sys.modules.pop('tomllib', None)
    sys.modules.pop('tomli', None)
    import importlib
    importlib.reload(config_mod)
    assert hasattr(config_mod, 'tomllib')
    assert hasattr(config_mod, 'TOMLDecodeError')

    # Simulate tomllib import but missing TOMLDecodeError (AttributeError)
    class DummyTomlLib:
        pass
    monkeypatch.setitem(sys.modules, 'tomllib', DummyTomlLib())
    sys.modules.pop('tomli', None)
    importlib.reload(config_mod)
    assert hasattr(config_mod, 'TOMLDecodeError')


def test_logdestination_path_validation():
    from hydra_logger.config import LogDestination
    with pytest.raises(ValueError, match="Path is required for file destinations"):
        LogDestination(type="file", path=None, level="INFO")
    with pytest.raises(ValueError, match="Path is required for file destinations"):
        LogDestination(type="file", path="   ", level="INFO")


def test_logdestination_level_and_format_validation():
    from hydra_logger.config import LogDestination
    with pytest.raises(ValueError, match="Invalid level"):
        LogDestination(type="console", level="INVALID")
    with pytest.raises(ValueError, match="Invalid format"):
        LogDestination(type="console", level="INFO", format="badformat")


def test_loglayer_level_validation():
    from hydra_logger.config import LogLayer
    with pytest.raises(ValueError, match="Invalid level"):
        LogLayer(level="BADLEVEL", destinations=[])


def test_loggingconfig_default_level_validation():
    from hydra_logger.config import LoggingConfig
    with pytest.raises(ValueError, match="Invalid default_level"):
        LoggingConfig(layers={}, default_level="BADLEVEL")


def test_load_config_file_not_found():
    from hydra_logger.config import load_config
    with pytest.raises(FileNotFoundError):
        load_config("/tmp/this_file_does_not_exist.yaml")


def test_load_config_unsupported_extension(tmp_path):
    from hydra_logger.config import load_config
    file = tmp_path / "config.unsupported"
    file.write_text("irrelevant")
    with pytest.raises(ValueError, match="Unsupported config file format"):
        load_config(file)


def test_load_config_empty_file(tmp_path):
    from hydra_logger.config import load_config
    file = tmp_path / "config.yaml"
    file.write_text("")
    with pytest.raises(ValueError, match="empty or invalid"):
        load_config(file)


def test_load_config_invalid_yaml(tmp_path):
    from hydra_logger.config import load_config
    file = tmp_path / "config.yaml"
    file.write_text(": bad yaml")
    with pytest.raises(ValueError, match="Failed to parse YAML"):
        load_config(file)


def test_load_config_invalid_toml(tmp_path):
    from hydra_logger.config import load_config
    file = tmp_path / "config.toml"
    file.write_text("bad = [unclosed")
    with patch.object(config_mod, 'tomllib', MagicMock()):
        config_mod.tomllib.load.side_effect = Exception("TOML error")
        with pytest.raises(ValueError, match="Failed to parse TOML"):
            load_config(file)


def test_load_config_yaml_parse_error(tmp_path):
    from hydra_logger.config import load_config
    file = tmp_path / "config.yaml"
    file.write_text("bad: [unclosed")
    with patch("hydra_logger.config.yaml.safe_load", side_effect=Exception("YAML error")):
        with pytest.raises(ValueError, match="Failed to load configuration"):
            load_config(file)
# === END GAP TESTS ===
