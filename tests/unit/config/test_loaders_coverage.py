"""
Comprehensive tests for config/loaders.py to achieve 100% coverage.

This module tests all edge cases, error conditions, and configuration loading
scenarios to ensure complete test coverage.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest
import yaml
from pydantic import ValidationError

from hydra_logger.config.loaders import (
    load_config,
    load_config_from_dict,
    load_config_from_env,
    get_default_config,
    get_async_default_config,
    create_log_directories,
    validate_config,
    merge_configs
)
from hydra_logger.config.models import LoggingConfig
from hydra_logger.core.exceptions import ConfigurationError


class TestLoadConfig:
    """Test load_config function with comprehensive coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.yaml_config = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "console",
                            "level": "INFO",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_config_yaml_success(self):
        """Test load_config with YAML file."""
        config_file = Path(self.temp_dir) / "test.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(self.yaml_config, f)
        
        config = load_config(config_file)
        
        assert isinstance(config, LoggingConfig)
        assert config.default_level == "INFO"
        assert "DEFAULT" in config.layers
    
    def test_load_config_yaml_uppercase_extension(self):
        """Test load_config with uppercase YAML extension."""
        config_file = Path(self.temp_dir) / "test.YAML"
        
        with open(config_file, 'w') as f:
            yaml.dump(self.yaml_config, f)
        
        config = load_config(config_file)
        
        assert isinstance(config, LoggingConfig)
        assert config.default_level == "INFO"
    
    def test_load_config_yml_extension(self):
        """Test load_config with .yml extension."""
        config_file = Path(self.temp_dir) / "test.yml"
        
        with open(config_file, 'w') as f:
            yaml.dump(self.yaml_config, f)
        
        config = load_config(config_file)
        
        assert isinstance(config, LoggingConfig)
        assert config.default_level == "INFO"
    
    def test_load_config_toml_success(self):
        """Test load_config with TOML file."""
        config_file = Path(self.temp_dir) / "test.toml"
        
        toml_content = """
default_level = "INFO"
[layers.DEFAULT]
level = "INFO"
[[layers.DEFAULT.destinations]]
type = "console"
level = "INFO"
format = "plain-text"
"""
        
        with open(config_file, 'w') as f:
            f.write(toml_content)
        
        config = load_config(config_file)
        
        assert isinstance(config, LoggingConfig)
        assert config.default_level == "INFO"
    
    def test_load_config_file_not_found(self):
        """Test load_config with non-existent file."""
        config_file = Path(self.temp_dir) / "nonexistent.yaml"
        
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            load_config(config_file)
    
    def test_load_config_unsupported_format(self):
        """Test load_config with unsupported format."""
        config_file = Path(self.temp_dir) / "test.json"
        
        with open(config_file, 'w') as f:
            f.write('{"test": "data"}')
        
        with pytest.raises(ConfigurationError, match="Unsupported configuration format"):
            load_config(config_file)
    
    def test_load_config_yaml_parse_error(self):
        """Test load_config with YAML parse error."""
        config_file = Path(self.temp_dir) / "invalid.yaml"
        
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(ConfigurationError, match="Failed to load configuration"):
            load_config(config_file)
    
    def test_load_config_toml_parse_error(self):
        """Test load_config with TOML parse error."""
        config_file = Path(self.temp_dir) / "invalid.toml"
        
        with open(config_file, 'w') as f:
            f.write("invalid toml content [")
        
        with pytest.raises(ConfigurationError, match="Failed to load configuration"):
            load_config(config_file)
    
    def test_load_config_toml_not_available(self):
        """Test load_config with TOML not available."""
        config_file = Path(self.temp_dir) / "test.toml"
        
        with open(config_file, 'w') as f:
            f.write("test = true")
        
        with patch('hydra_logger.config.loaders.tomllib', None):
            with pytest.raises(ConfigurationError, match="TOML support not available"):
                load_config(config_file)
    
    def test_load_config_validation_error(self):
        """Test load_config with validation error."""
        config_file = Path(self.temp_dir) / "invalid.yaml"
        
        # Create truly invalid config that will fail validation
        invalid_config = {
            "default_level": "INVALID_LEVEL",  # Invalid log level
            "layers": {
                "DEFAULT": {
                    "level": "INVALID_LEVEL",  # Invalid log level
                    "destinations": [
                        {
                            "type": "invalid_type",  # Invalid destination type
                            "level": "INVALID_LEVEL",
                            "format": "invalid_format"  # Invalid format
                        }
                    ]
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        with pytest.raises(ConfigurationError, match="Failed to load configuration"):
            load_config(config_file)


class TestLoadConfigFromDict:
    """Test load_config_from_dict function with comprehensive coverage."""
    
    def test_load_config_from_dict_success(self):
        """Test load_config_from_dict with valid data."""
        config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "console",
                            "level": "INFO",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
        
        config = load_config_from_dict(config_data)
        
        assert isinstance(config, LoggingConfig)
        assert config.default_level == "INFO"
        assert "DEFAULT" in config.layers
    
    def test_load_config_from_dict_validation_error(self):
        """Test load_config_from_dict with validation error."""
        invalid_config = {
            "default_level": "INVALID_LEVEL",  # Invalid log level
            "layers": {
                "DEFAULT": {
                    "level": "INVALID_LEVEL",  # Invalid log level
                    "destinations": [
                        {
                            "type": "invalid_type",  # Invalid destination type
                            "level": "INVALID_LEVEL",
                            "format": "invalid_format"  # Invalid format
                        }
                    ]
                }
            }
        }
        
        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            load_config_from_dict(invalid_config)
    
    def test_load_config_from_dict_general_exception(self):
        """Test load_config_from_dict with general exception."""
        # Mock LoggingConfig to raise a general exception
        with patch('hydra_logger.config.loaders.LoggingConfig', side_effect=Exception("General error")):
            with pytest.raises(ConfigurationError, match="Failed to load configuration"):
                load_config_from_dict({"test": "data"})


class TestLoadConfigFromEnv:
    """Test load_config_from_env function with comprehensive coverage."""
    
    def test_load_config_from_env_default_values(self):
        """Test load_config_from_env with default environment."""
        config = load_config_from_env()
        
        assert isinstance(config, LoggingConfig)
        assert config.default_level == "DEBUG"  # Default value
        assert "DEFAULT" in config.layers
    
    def test_load_config_from_env_custom_values(self):
        """Test load_config_from_env with custom environment variables."""
        with patch.dict(os.environ, {
            "HYDRA_LOG_LEVEL": "WARNING",
            "HYDRA_LOG_FORMAT": "json"
        }):
            config = load_config_from_env()
            
            assert isinstance(config, LoggingConfig)
            assert config.default_level == "WARNING"
            assert config.layers["DEFAULT"].destinations[0].format == "json"


class TestGetDefaultConfig:
    """Test get_default_config function."""
    
    def test_get_default_config(self):
        """Test get_default_config returns valid config."""
        config = get_default_config()
        
        assert isinstance(config, LoggingConfig)
        assert config.default_level is not None
        assert len(config.layers) > 0


class TestGetAsyncDefaultConfig:
    """Test get_async_default_config function."""
    
    def test_get_async_default_config(self):
        """Test get_async_default_config returns valid config."""
        config = get_async_default_config()
        
        assert isinstance(config, LoggingConfig)
        assert config.default_level == "INFO"
        assert "DEFAULT" in config.layers
        
        # Check that it has both console and file destinations
        destinations = config.layers["DEFAULT"].destinations
        destination_types = [d.type for d in destinations]
        assert "console" in destination_types
        assert "file" in destination_types


class TestCreateLogDirectories:
    """Test create_log_directories function with comprehensive coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_log_directories_with_file_destinations(self):
        """Test create_log_directories with file destinations."""
        config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "file",
                            "path": f"{self.temp_dir}/logs/app.log",
                            "format": "plain-text"
                        },
                        {
                            "type": "file",
                            "path": f"{self.temp_dir}/nested/deep/logs/debug.log",
                            "format": "json"
                        }
                    ]
                }
            }
        }
        
        config = LoggingConfig(**config_data)
        
        create_log_directories(config)
        
        # Check that directories were created
        assert os.path.exists(f"{self.temp_dir}/logs")
        assert os.path.exists(f"{self.temp_dir}/nested/deep/logs")
    
    def test_create_log_directories_without_file_destinations(self):
        """Test create_log_directories without file destinations."""
        config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "console",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
        
        config = LoggingConfig(**config_data)
        
        # Should not raise exception
        create_log_directories(config)
    
    def test_create_log_directories_with_file_destination_no_path(self):
        """Test create_log_directories with file destination but no path."""
        # This test is not possible with current Pydantic validation
        # File destinations require a path, so we'll test a different scenario
        config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "console",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
        
        config = LoggingConfig(**config_data)
        
        # Should not raise exception
        create_log_directories(config)


class TestValidateConfig:
    """Test validate_config function with comprehensive coverage."""
    
    def test_validate_config_valid(self):
        """Test validate_config with valid config."""
        config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "console",
                            "level": "INFO",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
        
        config = LoggingConfig(**config_data)
        
        result = validate_config(config)
        assert result is True
    
    def test_validate_config_invalid(self):
        """Test validate_config with invalid config."""
        # Create a mock config with invalid model_dump data that will cause ValidationError
        mock_config = MagicMock()
        # Return data that's missing required fields to trigger ValidationError
        mock_config.model_dump.return_value = {
            "default_level": "INVALID_LEVEL",  # Invalid enum value
            "layers": {
                "DEFAULT": {
                    "level": "INVALID_LEVEL",  # Invalid enum value
                    "destinations": [
                        {
                            "type": "invalid_type",  # Invalid enum value
                            "level": "INVALID_LEVEL",
                            "format": "invalid_format"  # Invalid enum value
                        }
                    ]
                }
            }
        }
        
        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            validate_config(mock_config)


class TestMergeConfigs:
    """Test merge_configs function with comprehensive coverage."""
    
    def test_merge_configs_success(self):
        """Test merge_configs with valid configs."""
        base_config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "console",
                            "level": "INFO",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
        
        base_config = LoggingConfig(**base_config_data)
        
        override_config = {
            "default_level": "DEBUG",
            "layers": {
                "DEFAULT": {
                    "level": "DEBUG",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/debug.log",
                            "format": "json"
                        }
                    ]
                }
            }
        }
        
        merged_config = merge_configs(base_config, override_config)
        
        assert isinstance(merged_config, LoggingConfig)
        assert merged_config.default_level == "DEBUG"
        assert merged_config.layers["DEFAULT"].level == "DEBUG"
        assert merged_config.layers["DEFAULT"].destinations[0].type == "file"
    
    def test_merge_configs_with_nested_structures(self):
        """Test merge_configs with nested structures."""
        base_config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "console",
                            "level": "INFO",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
        
        base_config = LoggingConfig(**base_config_data)
        
        override_config = {
            "layers": {
                "DEFAULT": {
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/app.log",
                            "format": "json"
                        }
                    ]
                },
                "SECURITY": {
                    "level": "WARNING",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/security.log",
                            "format": "json"
                        }
                    ]
                }
            }
        }
        
        merged_config = merge_configs(base_config, override_config)
        
        assert "DEFAULT" in merged_config.layers
        assert "SECURITY" in merged_config.layers
        assert merged_config.layers["SECURITY"].level == "WARNING"
    
    def test_merge_configs_with_empty_override(self):
        """Test merge_configs with empty override."""
        base_config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "console",
                            "level": "INFO",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
        
        base_config = LoggingConfig(**base_config_data)
        
        merged_config = merge_configs(base_config, {})
        
        assert isinstance(merged_config, LoggingConfig)
        assert merged_config.default_level == "INFO"
        assert "DEFAULT" in merged_config.layers


class TestConfigLoadersIntegration:
    """Integration tests for config loaders."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_config_workflow(self):
        """Test full configuration workflow."""
        # Create a config file
        config_file = Path(self.temp_dir) / "test.yaml"
        config_data = {
            "default_level": "INFO",
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "file",
                            "path": f"{self.temp_dir}/logs/app.log",
                            "format": "plain-text"
                        }
                    ]
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load config
        config = load_config(config_file)
        
        # Validate config
        assert validate_config(config) is True
        
        # Create directories
        create_log_directories(config)
        
        # Check that directory was created
        assert os.path.exists(f"{self.temp_dir}/logs")
    
    def test_config_merging_workflow(self):
        """Test configuration merging workflow."""
        # Start with default config
        base_config = get_default_config()
        
        # Create override
        override = {
            "default_level": "DEBUG",
            "layers": {
                "DEBUG": {
                    "level": "DEBUG",
                    "destinations": [
                        {
                            "type": "console",
                            "format": "json"
                        }
                    ]
                }
            }
        }
        
        # Merge configs
        merged_config = merge_configs(base_config, override)
        
        # Validate merged config
        assert validate_config(merged_config) is True
        
        # Check that override was applied
        assert merged_config.default_level == "DEBUG"
        assert "DEBUG" in merged_config.layers 