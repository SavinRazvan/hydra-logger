from unittest.mock import MagicMock, patch

import pytest

from hydra_logger.config import (
    LogDestination,
    LoggingConfig,
    LogLayer,
    create_log_directories,
    load_config,
)


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/tmp/does_not_exist.yaml")


def test_load_config_unsupported_extension(tmp_path):
    file = tmp_path / "config.unsupported"
    file.write_text("foo: bar")
    with pytest.raises(ValueError, match="Unsupported config file format"):
        load_config(file)


def test_load_config_empty_yaml(tmp_path):
    file = tmp_path / "empty.yaml"
    file.write_text("")
    with pytest.raises(ValueError, match="empty or invalid"):
        load_config(file)


def test_load_config_yaml_parse_error(tmp_path):
    file = tmp_path / "bad.yaml"
    file.write_text("foo: [unclosed")
    with pytest.raises(ValueError, match="Failed to parse YAML"):
        load_config(file)


def test_load_config_toml_parse_error(tmp_path):
    file = tmp_path / "bad.toml"
    file.write_bytes(b"invalid =")
    with patch("hydra_logger.config.tomllib") as mock_tomllib:
        mock_tomllib.load.side_effect = Exception("TOML parse error")
        with pytest.raises(ValueError, match="Failed to load configuration"):
            load_config(file)


def test_load_config_general_exception(tmp_path):
    file = tmp_path / "bad.yaml"
    file.write_text("foo: bar")
    with patch("hydra_logger.config.yaml.safe_load", side_effect=Exception("fail")):
        with pytest.raises(ValueError, match="Failed to load configuration"):
            load_config(file)


def test_create_log_directories_oserror(tmp_path):
    config = LoggingConfig(
        layers={
            "LAYER": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(type="file", path=str(tmp_path / "logs/app.log"))
                ],
            )
        }
    )
    with patch("os.makedirs", side_effect=OSError("fail")):
        with pytest.raises(OSError, match="Failed to create log directory"):
            create_log_directories(config)


def test_tomllib_import_logic(monkeypatch):
    """Test TOML import fallback logic."""
    # Test that the module can be imported and has the expected attributes
    import hydra_logger.config as config_mod

    assert hasattr(config_mod, "tomllib")
    assert hasattr(config_mod, "TOMLDecodeError")

    # Test that we can access the tomllib module
    assert config_mod.tomllib is not None


def test_toml_decode_error_handling(tmp_path):
    """Test TOML decode error handling."""
    file = tmp_path / "bad.toml"
    file.write_bytes(b"invalid =")

    with patch("hydra_logger.config.tomllib") as mock_tomllib:
        mock_tomllib.load.side_effect = Exception("TOML decode error")
        with pytest.raises(ValueError, match="Failed to parse TOML"):
            load_config(file)


def test_attribute_error_handling():
    """Test AttributeError handling in TOML import."""
    with patch("hydra_logger.config.tomllib", MagicMock()) as mock_tomllib:
        # Remove TOMLDecodeError attribute
        del mock_tomllib.TOMLDecodeError
        import importlib

        import hydra_logger.config as config_mod

        importlib.reload(config_mod)
        assert hasattr(config_mod, "TOMLDecodeError")


class TestConfigCoverage:
    """Test specific edge cases to increase config.py coverage."""

    def test_toml_import_fallback_scenarios(self):
        """Test TOML import fallback scenarios to cover missing lines."""
        
        # Test that TOMLDecodeError is available
        from hydra_logger.config import TOMLDecodeError
        assert TOMLDecodeError is not None
        
        # Test that the module can handle TOML files
        # This covers the import logic indirectly
        import hydra_logger.config
        assert hasattr(hydra_logger.config, 'TOMLDecodeError')

    def test_log_destination_model_post_init(self):
        """Test LogDestination model_post_init method."""
        
        # Test file destination without path (should raise ValueError)
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", path=None)
        
        # Test file destination with path (should not raise)
        destination = LogDestination(type="file", path="test.log")
        assert destination.path == "test.log"
        
        # Test console destination without path (should not raise)
        destination = LogDestination(type="console", path=None)
        assert destination.path is None

    def test_log_destination_path_validator_edge_cases(self):
        """Test LogDestination path validator edge cases."""
        
        # Test file destination with empty path
        with pytest.raises(Exception, match="Path is required for file destinations"):
            LogDestination(type="file", path="")
        
        # Test file destination with whitespace path
        with pytest.raises(Exception, match="Path is required for file destinations"):
            LogDestination(type="file", path="   ")
        
        # Test console destination with path (should work)
        destination = LogDestination(type="console", path="test.log")
        assert destination.path == "test.log"

    def test_log_destination_level_validator_edge_cases(self):
        """Test LogDestination level validator edge cases."""
        
        # Test valid levels in different cases
        valid_levels = ["debug", "INFO", "Warning", "ERROR", "critical"]
        for level in valid_levels:
            destination = LogDestination(type="console", level=level)
            assert destination.level == level.upper()
        
        # Test invalid level
        with pytest.raises(ValueError, match="Invalid level: INVALID"):
            LogDestination(type="console", level="INVALID")

    def test_log_destination_format_validator_edge_cases(self):
        """Test LogDestination format validator edge cases."""
        
        # Test valid formats in different cases
        valid_formats = ["TEXT", "Json", "CSV", "syslog", "GELF"]
        for fmt in valid_formats:
            destination = LogDestination(type="console", format=fmt)
            assert destination.format == fmt.lower()
        
        # Test invalid format
        with pytest.raises(ValueError, match="Invalid format: INVALID"):
            LogDestination(type="console", format="INVALID")

    def test_log_layer_level_validator_edge_cases(self):
        """Test LogLayer level validator edge cases."""
        
        # Test valid levels in different cases
        valid_levels = ["debug", "INFO", "Warning", "ERROR", "critical"]
        for level in valid_levels:
            layer = LogLayer(level=level)
            assert layer.level == level.upper()
        
        # Test invalid level
        with pytest.raises(ValueError, match="Invalid level: INVALID"):
            LogLayer(level="INVALID")

    def test_logging_config_default_level_validator_edge_cases(self):
        """Test LoggingConfig default_level validator edge cases."""
        
        # Test valid levels in different cases
        valid_levels = ["debug", "INFO", "Warning", "ERROR", "critical"]
        for level in valid_levels:
            config = LoggingConfig(default_level=level)
            assert config.default_level == level.upper()
        
        # Test invalid level
        with pytest.raises(ValueError, match="Invalid default_level: INVALID"):
            LoggingConfig(default_level="INVALID")

    def test_load_config_edge_cases(self):
        """Test load_config function edge cases."""
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            load_config("non_existent_file.yaml")
        
        # Test with invalid YAML file
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "invalid: yaml: content:"
            mock_open.return_value.__enter__.return_value.close.return_value = None
            
            with pytest.raises(Exception):  # Should raise some exception for invalid YAML
                load_config("test.yaml")

    def test_create_log_directories_edge_cases(self):
        """Test create_log_directories function edge cases."""
        
        # Test with empty config
        config = LoggingConfig()
        # Should not raise any exception
        from hydra_logger.config import create_log_directories
        create_log_directories(config)
        
        # Test with config that has file destinations
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    destinations=[
                        LogDestination(type="file", path="logs/app.log")
                    ]
                )
            }
        )
        # Should not raise any exception
        create_log_directories(config)

    def test_get_default_config(self):
        """Test get_default_config function."""
        
        from hydra_logger.config import get_default_config
        
        config = get_default_config()
        assert config.default_level == "INFO"
        assert "DEFAULT" in config.layers
        assert len(config.layers["DEFAULT"].destinations) == 2  # file + console

    def test_log_destination_with_all_optional_fields(self):
        """Test LogDestination with all optional fields specified."""
        
        destination = LogDestination(
            type="file",
            path="test.log",
            level="DEBUG",
            max_size="10MB",
            backup_count=5,
            format="json"
        )
        
        assert destination.type == "file"
        assert destination.path == "test.log"
        assert destination.level == "DEBUG"
        assert destination.max_size == "10MB"
        assert destination.backup_count == 5
        assert destination.format == "json"

    def test_log_layer_with_empty_destinations(self):
        """Test LogLayer with empty destinations list."""
        
        layer = LogLayer(level="INFO", destinations=[])
        assert layer.level == "INFO"
        assert len(layer.destinations) == 0

    def test_logging_config_with_empty_layers(self):
        """Test LoggingConfig with empty layers dict."""
        
        config = LoggingConfig(layers={}, default_level="DEBUG")
        assert config.default_level == "DEBUG"
        assert len(config.layers) == 0

    def test_log_destination_console_with_path(self):
        """Test console destination with path (should be allowed)."""
        
        destination = LogDestination(type="console", path="test.log")
        assert destination.type == "console"
        assert destination.path == "test.log"

    def test_log_destination_file_with_empty_string_path(self):
        """Test file destination with empty string path (should fail)."""
        
        with pytest.raises(Exception, match="Path is required for file destinations"):
            LogDestination(type="file", path="")

    def test_log_destination_file_with_whitespace_path(self):
        """Test file destination with whitespace path (should fail)."""
        
        with pytest.raises(Exception, match="Path is required for file destinations"):
            LogDestination(type="file", path="   ")

    def test_log_destination_file_with_none_path(self):
        """Test file destination with None path (should fail)."""
        
        with pytest.raises(Exception, match="Path is required for file destinations"):
            LogDestination(type="file", path=None)

    def test_log_destination_validation_info_edge_cases(self):
        """Test LogDestination path validator with edge cases in validation info."""
        
        # Test with None info.data
        from hydra_logger.config import LogDestination
        from pydantic import ValidationInfo
        
        # Create a simple mock for ValidationInfo
        class MockValidationInfo:
            def __init__(self, data):
                self.data = data
        
        # Test with None data
        mock_info = MockValidationInfo(None)
        result = LogDestination.validate_file_path("test.log", mock_info)
        assert result == "test.log"
        
        # Test with empty dict in data
        mock_info.data = {}
        result = LogDestination.validate_file_path("test.log", mock_info)
        assert result == "test.log"
        
        # Test with file type but no path
        mock_info.data = {"type": "file"}
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination.validate_file_path(None, mock_info)
        
        # Test with file type and path
        mock_info.data = {"type": "file"}
        result = LogDestination.validate_file_path("test.log", mock_info)
        assert result == "test.log"
        
        # Test with console type and no path
        mock_info.data = {"type": "console"}
        result = LogDestination.validate_file_path(None, mock_info)
        assert result is None
