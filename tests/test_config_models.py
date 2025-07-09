"""
Comprehensive tests for config models module.

This module tests all functionality in hydra_logger.config.models
to achieve 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock

from hydra_logger.config.models import (
    LogDestination,
    LogLayer,
    LoggingConfig,
    load_config,
    get_default_config,
    get_async_default_config,
    create_log_directories
)
from hydra_logger.core.exceptions import ConfigurationError


class TestLogDestination:
    """Test LogDestination model."""

    def test_log_destination_basic(self):
        """Test basic LogDestination creation."""
        destination = LogDestination(type="console", level="INFO")
        assert destination.type == "console"
        assert destination.level == "INFO"

    def test_log_destination_file_with_path(self):
        """Test file destination with path."""
        destination = LogDestination(
            type="file",
            path="logs/test.log",
            level="DEBUG",
            max_size="5MB",
            backup_count=3
        )
        assert destination.type == "file"
        assert destination.path == "logs/test.log"
        assert destination.max_size == "5MB"
        assert destination.backup_count == 3

    def test_log_destination_file_without_path(self):
        """Test file destination without path."""
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", level="INFO")

    def test_log_destination_file_empty_path(self):
        """Test file destination with empty path."""
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", path="", level="INFO")

    def test_log_destination_file_whitespace_path(self):
        """Test file destination with whitespace path."""
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", path="   ", level="INFO")

    def test_log_destination_async_http_with_url(self):
        """Test async HTTP destination with URL."""
        destination = LogDestination(
            type="async_http",
            url="http://localhost:8080/logs",
            level="INFO",
            format="json"
        )
        assert destination.type == "async_http"
        assert destination.url == "http://localhost:8080/logs"

    def test_log_destination_async_http_without_url(self):
        """Test async HTTP destination without URL."""
        with pytest.raises(ValueError, match="URL is required for async HTTP destinations"):
            LogDestination(type="async_http", level="INFO")

    def test_log_destination_async_database_with_connection(self):
        """Test async database destination with connection string."""
        destination = LogDestination(
            type="async_database",
            connection_string="postgresql://user:pass@localhost/db",
            level="INFO"
        )
        assert destination.type == "async_database"
        assert destination.connection_string == "postgresql://user:pass@localhost/db"

    def test_log_destination_async_database_without_connection(self):
        """Test async database destination without connection string."""
        with pytest.raises(ValueError, match="Connection string is required for async database destinations"):
            LogDestination(type="async_database", level="INFO")

    def test_log_destination_async_queue_with_url(self):
        """Test async queue destination with queue URL."""
        destination = LogDestination(
            type="async_queue",
            queue_url="redis://localhost:6379/0",
            level="INFO"
        )
        assert destination.type == "async_queue"
        assert destination.queue_url == "redis://localhost:6379/0"

    def test_log_destination_async_queue_without_url(self):
        """Test async queue destination without queue URL."""
        with pytest.raises(ValueError, match="Queue URL is required for async queue destinations"):
            LogDestination(type="async_queue", level="INFO")

    def test_log_destination_async_cloud_with_service(self):
        """Test async cloud destination with service type."""
        destination = LogDestination(
            type="async_cloud",
            service_type="aws",
            level="INFO",
            credentials={"access_key": "test", "secret_key": "test"}
        )
        assert destination.type == "async_cloud"
        assert destination.service_type == "aws"

    def test_log_destination_async_cloud_without_service(self):
        """Test async cloud destination without service type."""
        with pytest.raises(ValueError, match="Service type is required for async cloud destinations"):
            LogDestination(type="async_cloud", level="INFO")

    def test_log_destination_invalid_level(self):
        """Test destination with invalid level."""
        with pytest.raises(ValueError, match="Invalid level"):
            LogDestination(type="console", level="INVALID")

    def test_log_destination_invalid_format(self):
        """Test destination with invalid format."""
        with pytest.raises(ValueError, match="Invalid format"):
            LogDestination(type="console", level="INFO", format="invalid")

    def test_log_destination_invalid_service_type(self):
        """Test destination with invalid service type."""
        with pytest.raises(ValueError, match="Invalid service type"):
            LogDestination(type="async_cloud", service_type="invalid", level="INFO")

    def test_log_destination_level_normalization(self):
        """Test level normalization."""
        destination = LogDestination(type="console", level="debug")
        assert destination.level == "DEBUG"

    def test_log_destination_format_normalization(self):
        """Test format normalization."""
        destination = LogDestination(type="console", level="INFO", format="JSON")
        assert destination.format == "json"

    def test_log_destination_service_type_normalization(self):
        """Test service type normalization."""
        destination = LogDestination(type="async_cloud", service_type="AWS", level="INFO")
        assert destination.service_type == "aws"

    def test_log_destination_post_init_validation(self):
        """Test post-init validation."""
        # Test file destination without path
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", level="INFO")

        # Test async HTTP without URL
        with pytest.raises(ValueError, match="URL is required for async HTTP destinations"):
            LogDestination(type="async_http", level="INFO")

        # Test async database without connection string
        with pytest.raises(ValueError, match="Connection string is required for async database destinations"):
            LogDestination(type="async_database", level="INFO")

        # Test async queue without queue URL
        with pytest.raises(ValueError, match="Queue URL is required for async queue destinations"):
            LogDestination(type="async_queue", level="INFO")

        # Test async cloud without service type
        with pytest.raises(ValueError, match="Service type is required for async cloud destinations"):
            LogDestination(type="async_cloud", level="INFO")


class TestLogLayer:
    """Test LogLayer model."""

    def test_log_layer_basic(self):
        """Test basic LogLayer creation."""
        layer = LogLayer(level="INFO")
        assert layer.level == "INFO"
        assert layer.destinations == []

    def test_log_layer_with_destinations(self):
        """Test LogLayer with destinations."""
        destinations = [
            LogDestination(type="console", level="INFO"),
            LogDestination(type="file", path="logs/test.log", level="DEBUG")
        ]
        layer = LogLayer(level="INFO", destinations=destinations)
        assert layer.level == "INFO"
        assert len(layer.destinations) == 2

    def test_log_layer_invalid_level(self):
        """Test LogLayer with invalid level."""
        with pytest.raises(ValueError, match="Invalid level"):
            LogLayer(level="INVALID")

    def test_log_layer_level_normalization(self):
        """Test level normalization."""
        layer = LogLayer(level="debug")
        assert layer.level == "DEBUG"


class TestLoggingConfig:
    """Test LoggingConfig model."""

    def test_logging_config_basic(self):
        """Test basic LoggingConfig creation."""
        config = LoggingConfig()
        assert config.default_level == "INFO"
        assert config.layers == {}

    def test_logging_config_with_layers(self):
        """Test LoggingConfig with layers."""
        layers = {
            "DEFAULT": LogLayer(level="INFO"),
            "ERROR": LogLayer(level="ERROR")
        }
        config = LoggingConfig(layers=layers, default_level="DEBUG")
        assert config.default_level == "DEBUG"
        assert len(config.layers) == 2

    def test_logging_config_invalid_default_level(self):
        """Test LoggingConfig with invalid default level."""
        with pytest.raises(ValueError, match="Invalid default_level"):
            LoggingConfig(default_level="INVALID")

    def test_logging_config_default_level_normalization(self):
        """Test default level normalization."""
        config = LoggingConfig(default_level="debug")
        assert config.default_level == "DEBUG"


class TestConfigFunctions:
    """Test configuration functions."""

    def test_load_config_yaml_success(self):
        """Test loading YAML configuration successfully."""
        import yaml
        import tempfile
        import os
        
        config_data = {
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {"type": "console", "level": "INFO"}
                    ]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            config = load_config(config_file)
            assert isinstance(config, LoggingConfig)
            assert "DEFAULT" in config.layers
        finally:
            os.unlink(config_file)

    def test_load_config_yaml_not_found(self):
        """Test loading non-existent YAML file."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")

    def test_load_config_yaml_invalid(self):
        """Test loading invalid YAML file."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Failed to parse YAML"):
                load_config(config_file)
        finally:
            os.unlink(config_file)

    def test_load_config_yaml_empty(self):
        """Test loading empty YAML file."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            config_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Configuration file is empty"):
                load_config(config_file)
        finally:
            os.unlink(config_file)

    def test_load_config_unsupported_format(self):
        """Test loading unsupported file format."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test")
            config_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported config file format"):
                load_config(config_file)
        finally:
            os.unlink(config_file)

    def test_load_config_toml_success(self):
        """Test loading TOML configuration successfully."""
        import tempfile
        import os
        
        config_data = """
[layers.DEFAULT]
level = "INFO"

[[layers.DEFAULT.destinations]]
type = "console"
level = "INFO"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_data)
            config_file = f.name
        
        try:
            config = load_config(config_file)
            assert isinstance(config, LoggingConfig)
            assert "DEFAULT" in config.layers
        finally:
            os.unlink(config_file)

    def test_load_config_toml_invalid(self):
        """Test loading invalid TOML file."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content [")
            config_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Failed to parse TOML"):
                load_config(config_file)
        finally:
            os.unlink(config_file)

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        assert isinstance(config, LoggingConfig)
        assert "DEFAULT" in config.layers

    def test_get_async_default_config(self):
        """Test getting async default configuration."""
        config = get_async_default_config()
        assert isinstance(config, LoggingConfig)
        assert "DEFAULT" in config.layers

    def test_create_log_directories_success(self):
        """Test creating log directories successfully."""
        import os
        import tempfile
        import shutil
        
        test_dir = tempfile.mkdtemp()
        try:
            config = LoggingConfig(
                layers={
                    "DEFAULT": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="file", path=os.path.join(test_dir, "logs/test.log"))
                        ]
                    )
                }
            )
            
            create_log_directories(config)
            assert os.path.exists(os.path.join(test_dir, "logs"))
        finally:
            shutil.rmtree(test_dir)

    def test_create_log_directories_permission_error(self):
        """Test creating log directories with permission error."""
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path="/root/test.log")
                    ]
                )
            }
        )
        
        with pytest.raises(OSError):
            create_log_directories(config)

    def test_create_log_directories_no_file_destinations(self):
        """Test creating log directories with no file destinations."""
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        
        # Should not raise any error
        create_log_directories(config)

    def test_create_log_directories_no_path(self):
        """Test creating log directories with destination without path."""
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path=None)
                    ]
                )
            }
        )
        
        # Should not raise any error
        create_log_directories(config)

    def test_load_config_toml_import_error(self):
        """Test loading TOML when tomllib is not available."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("test = true")
            config_file = f.name
        
        try:
            with patch('hydra_logger.config.models.tomllib', None):
                with pytest.raises(ValueError, match="Failed to parse TOML"):
                    load_config(config_file)
        finally:
            os.unlink(config_file)

    def test_load_config_with_file_error(self):
        """Test loading config with file system error."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test: data")
            config_file = f.name
        
        try:
            with patch('builtins.open', side_effect=OSError("Permission denied")):
                with pytest.raises(ValueError, match="Failed to load configuration"):
                    load_config(config_file)
        finally:
            os.unlink(config_file)

    def test_load_config_with_encoding_error(self):
        """Test loading config with encoding error."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test: data")
            config_file = f.name
        
        try:
            with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test')):
                with pytest.raises(ValueError, match="Failed to load configuration"):
                    load_config(config_file)
        finally:
            os.unlink(config_file) 