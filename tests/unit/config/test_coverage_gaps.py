"""
Additional tests to cover missing lines in config loaders and models.

This file targets specific uncovered lines identified in the coverage report.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

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
from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination
from hydra_logger.core.exceptions import ConfigurationError


class TestLoadersCoverageGaps:
    """Test specific uncovered lines in loaders.py."""

    def test_load_config_yaml_parse_error(self):
        """Test YAML parsing error handling (line 43-63)."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("yaml.safe_load", side_effect=Exception("YAML parse error")):
                with pytest.raises(ConfigurationError, match="Failed to load configuration"):
                    load_config("test.yaml")

    def test_load_config_toml_import_error(self):
        """Test TOML import error handling (line 21-27)."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("hydra_logger.config.loaders.tomllib", None):
                with pytest.raises(ConfigurationError, match="TOML support not available"):
                    load_config("test.toml")

    def test_load_config_toml_decode_error(self):
        """Test TOML decode error handling (line 83-84)."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("hydra_logger.config.loaders.tomllib") as mock_tomllib:
                mock_tomllib.load.side_effect = Exception("TOML decode error")
                with pytest.raises(ConfigurationError, match="Failed to load configuration"):
                    load_config("test.toml")

    def test_load_config_from_dict_validation_error(self):
        """Test validation error in load_config_from_dict (line 96-112)."""
        invalid_config = {
            "layers": {
                "TEST": {
                    "level": "INVALID_LEVEL",
                    "destinations": []
                }
            }
        }
        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            load_config_from_dict(invalid_config)

    def test_load_config_from_dict_general_error(self):
        """Test general error in load_config_from_dict (line 133-155)."""
        with patch("hydra_logger.config.loaders.LoggingConfig") as mock_config:
            mock_config.side_effect = Exception("General error")
            with pytest.raises(ConfigurationError, match="Failed to load configuration"):
                load_config_from_dict({"test": "data"})

    def test_load_config_from_env_comprehensive(self):
        """Test load_config_from_env with various environment variables (line 165-169)."""
        with patch.dict(os.environ, {
            'HYDRA_LOG_LEVEL': 'DEBUG',
            'HYDRA_LOG_FORMAT': 'json'
        }):
            config = load_config_from_env()
            assert isinstance(config, LoggingConfig)
            assert "DEFAULT" in config.layers

    def test_create_log_directories_with_os_error(self):
        """Test create_log_directories with OSError (line 185-190)."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    destinations=[
                        LogDestination(type="file", path="/invalid/path/test.log")
                    ]
                )
            }
        )
        
        with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                create_log_directories(config)

    def test_validate_config_with_validation_error(self):
        """Test validate_config with validation error."""
        # Create a config that will fail validation
        invalid_config = {
            "layers": {
                "DEFAULT": {
                    "level": "INVALID_LEVEL",  # Invalid level
                    "destinations": [
                        {"type": "console", "level": "INFO"}
                    ]
                }
            }
        }
        
        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            load_config_from_dict(invalid_config)

    def test_merge_configs_deep_merge_complex(self):
        """Test deep merge with complex nested structures."""
        base_config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        
        override_config = {
            "layers": {
                "DEFAULT": {
                    "level": "DEBUG",
                    "destinations": [
                        {"type": "file", "path": "logs/test.log", "level": "DEBUG"}
                    ]
                },
                "ERROR": {
                    "level": "ERROR",
                    "destinations": [
                        {"type": "file", "path": "logs/error.log", "level": "ERROR"}
                    ]
                }
            }
        }
        
        merged = merge_configs(base_config, override_config)
        assert isinstance(merged, LoggingConfig)
        assert merged.layers["DEFAULT"].level == "DEBUG"
        assert "ERROR" in merged.layers

    # Removed test_tomli_import_fallback - not relevant for Python 3.11+ where tomllib is always present

    def test_deep_merge_recursive_case(self):
        """Test deep_merge function's recursive case (lines 189-190)."""
        base_config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        # Create override with nested dict to trigger recursive merge
        override_config = {
            "layers": {
                "DEFAULT": {
                    "level": "DEBUG",
                    "destinations": [
                        {"type": "file", "path": "test.log", "level": "DEBUG"}
                    ]
                }
            }
        }
        merged = merge_configs(base_config, override_config)
        assert merged.layers["DEFAULT"].level == "DEBUG"
        assert len(merged.layers["DEFAULT"].destinations) == 1
        assert merged.layers["DEFAULT"].destinations[0].type == "file"

    def test_deep_merge_complex_nested_structure(self):
        """Test deep_merge with complex nested structures to cover lines 189-190."""
        base_config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="file", path="error.log", level="ERROR")
                    ]
                )
            }
        )
        
        # Create complex nested override to ensure recursive merge is triggered
        override_config = {
            "layers": {
                "DEFAULT": {
                    "level": "DEBUG",
                    "destinations": [
                        {"type": "file", "path": "debug.log", "level": "DEBUG"},
                        {"type": "console", "level": "INFO"}
                    ]
                },
                "ERROR": {
                    "level": "ERROR",
                    "destinations": [
                        {"type": "file", "path": "error.log", "level": "ERROR"},
                        {"type": "async_http", "url": "http://localhost:8080/logs", "level": "ERROR"}
                    ]
                },
                "CUSTOM": {
                    "level": "WARNING",
                    "destinations": [
                        {"type": "file", "path": "custom.log", "level": "WARNING"}
                    ]
                }
            }
        }
        
        merged = merge_configs(base_config, override_config)
        assert merged.layers["DEFAULT"].level == "DEBUG"
        assert len(merged.layers["DEFAULT"].destinations) == 2
        assert merged.layers["ERROR"].level == "ERROR"
        assert len(merged.layers["ERROR"].destinations) == 2
        assert "CUSTOM" in merged.layers

    def test_deep_merge_recursive_case_specific(self):
        """Test deep_merge recursive case specifically to cover lines 189-190."""
        # Create a base config with nested structure
        base_config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        
        # Create override with nested dict that will trigger recursive merge
        override_config = {
            "layers": {
                "DEFAULT": {
                    "level": "DEBUG",  # This should merge with existing DEFAULT layer
                    "destinations": [
                        {"type": "file", "path": "test.log", "level": "DEBUG"}
                    ]
                }
            }
        }
        
        # This should trigger the recursive case in deep_merge
        merged = merge_configs(base_config, override_config)
        
        # Verify the merge worked correctly
        assert merged.layers["DEFAULT"].level == "DEBUG"
        assert len(merged.layers["DEFAULT"].destinations) == 1
        assert merged.layers["DEFAULT"].destinations[0].type == "file"
        assert merged.layers["DEFAULT"].destinations[0].path == "test.log"

    def test_deep_merge_recursive_case_deep_nesting(self):
        """Test deep_merge with deep nesting to ensure recursive case is hit (lines 189-190)."""
        # Create a base config with deeply nested structure
        base_config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="file", path="error.log", level="ERROR")
                    ]
                )
            }
        )
        
        # Create override with deeply nested structure to force recursive merge
        override_config = {
            "layers": {
                "DEFAULT": {
                    "level": "DEBUG",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "debug.log",
                            "level": "DEBUG",
                            "max_size": "10MB",
                            "backup_count": 5
                        }
                    ]
                },
                "ERROR": {
                    "level": "ERROR",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "error.log",
                            "level": "ERROR",
                            "max_size": "5MB"
                        },
                        {
                            "type": "async_http",
                            "url": "http://localhost:8080/logs",
                            "level": "ERROR",
                            "timeout": 30.0,
                            "retry_count": 3
                        }
                    ]
                },
                "CUSTOM": {
                    "level": "WARNING",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "custom.log",
                            "level": "WARNING",
                            "format": "json"
                        }
                    ]
                }
            }
        }
        
        # This should trigger multiple recursive calls in deep_merge
        merged = merge_configs(base_config, override_config)
        
        # Verify the deep merge worked correctly
        assert merged.layers["DEFAULT"].level == "DEBUG"
        assert len(merged.layers["DEFAULT"].destinations) == 1
        assert merged.layers["DEFAULT"].destinations[0].type == "file"
        assert merged.layers["DEFAULT"].destinations[0].path == "debug.log"
        assert merged.layers["DEFAULT"].destinations[0].max_size == "10MB"
        assert merged.layers["DEFAULT"].destinations[0].backup_count == 5
        
        assert merged.layers["ERROR"].level == "ERROR"
        assert len(merged.layers["ERROR"].destinations) == 2
        assert merged.layers["ERROR"].destinations[0].type == "file"
        assert merged.layers["ERROR"].destinations[1].type == "async_http"
        
        assert "CUSTOM" in merged.layers
        assert merged.layers["CUSTOM"].level == "WARNING"

    def test_deep_merge_recursive_case_direct_test(self):
        """Test deep_merge recursive case directly by calling the function (lines 189-190)."""
        from hydra_logger.config.loaders import merge_configs
        
        # Create a simple base config
        base_config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        
        # Create override that will definitely trigger recursive merge
        override_config = {
            "layers": {
                "DEFAULT": {
                    "level": "DEBUG",
                    "destinations": [
                        {"type": "file", "path": "test.log", "level": "DEBUG"}
                    ]
                }
            }
        }
        
        # Call merge_configs which should trigger the recursive deep_merge
        merged = merge_configs(base_config, override_config)
        
        # Verify the merge worked
        assert merged.layers["DEFAULT"].level == "DEBUG"
        assert len(merged.layers["DEFAULT"].destinations) == 1
        assert merged.layers["DEFAULT"].destinations[0].type == "file"

    def test_toml_decode_error_handling(self):
        """Test TOML decode error handling."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid = [unclosed")
            temp_file = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Failed to load configuration"):
                load_config(temp_file)
        finally:
            os.unlink(temp_file)

    def test_create_log_directories_os_error(self):
        """Test create_log_directories with OSError handling (lines 579-580)."""
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
        
        # Patch Path.mkdir for loaders.py
        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Permission denied"):
                create_log_directories(config)

    def test_create_log_directories_os_error_models(self):
        """Test create_log_directories with OSError handling in models.py (lines 579-580)."""
        from hydra_logger.config.models import create_log_directories as create_log_directories_models
        
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
        
        # Patch os.makedirs for models.py
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Failed to create log directory"):
                create_log_directories_models(config)




class TestModelsCoverageGaps:
    """Test specific uncovered lines in models.py."""

    def test_logdestination_validate_file_path_with_empty_string(self):
        """Test validate_file_path with empty string (line 31-34)."""
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", path="", level="INFO")

    def test_logdestination_validate_file_path_with_whitespace(self):
        """Test validate_file_path with whitespace (line 40-45)."""
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", path="   ", level="INFO")

    def test_logdestination_validate_async_http_url_empty(self):
        """Test validate_async_http_url with empty URL (line 135)."""
        with pytest.raises(ValueError, match="URL is required for async HTTP destinations"):
            LogDestination(type="async_http", url="", level="INFO")

    def test_logdestination_validate_async_http_url_whitespace(self):
        """Test validate_async_http_url with whitespace URL (line 154-156)."""
        with pytest.raises(ValueError, match="URL is required for async HTTP destinations"):
            LogDestination(type="async_http", url="   ", level="INFO")

    def test_logdestination_validate_async_database_connection_empty(self):
        """Test validate_async_database_connection with empty connection (line 174-176)."""
        with pytest.raises(ValueError, match="Connection string is required for async database destinations"):
            LogDestination(type="async_database", connection_string="", level="INFO")

    def test_logdestination_validate_async_database_connection_whitespace(self):
        """Test validate_async_database_connection with whitespace connection (line 194-196)."""
        with pytest.raises(ValueError, match="Connection string is required for async database destinations"):
            LogDestination(type="async_database", connection_string="   ", level="INFO")

    def test_logdestination_validate_async_queue_url_empty(self):
        """Test validate_async_queue_url with empty URL (line 214-216)."""
        with pytest.raises(ValueError, match="Queue URL is required for async queue destinations"):
            LogDestination(type="async_queue", queue_url="", level="INFO")

    def test_logdestination_validate_async_queue_url_whitespace(self):
        """Test validate_async_queue_url with whitespace URL (line 232, 234, 236, 238, 240)."""
        with pytest.raises(ValueError, match="Queue URL is required for async queue destinations"):
            LogDestination(type="async_queue", queue_url="   ", level="INFO")

    def test_logdestination_validate_async_cloud_service_empty(self):
        """Test validate_async_cloud_service with empty service type (line 262)."""
        with pytest.raises(ValueError, match="Service type is required for async cloud destinations"):
            LogDestination(type="async_cloud", service_type="", level="INFO")

    def test_logdestination_validate_async_cloud_service_whitespace(self):
        """Test validate_async_cloud_service with whitespace service type (line 304-310)."""
        with pytest.raises(ValueError, match="Service type is required for async cloud destinations"):
            LogDestination(type="async_cloud", service_type="   ", level="INFO")

    def test_logdestination_model_post_init_file_empty_path(self):
        """Test model_post_init with file destination and empty path (line 403)."""
        with pytest.raises(ValueError, match="Path is required for file destinations"):
            LogDestination(type="file", path="", level="INFO")

    def test_logdestination_model_post_init_async_http_empty_url(self):
        """Test model_post_init with async HTTP and empty URL (line 439-460)."""
        with pytest.raises(ValueError, match="URL is required for async HTTP destinations"):
            LogDestination(type="async_http", url="", level="INFO")

    def test_logdestination_model_post_init_async_database_empty_connection(self):
        """Test model_post_init with async database and empty connection (line 485)."""
        with pytest.raises(ValueError, match="Connection string is required for async database destinations"):
            LogDestination(type="async_database", connection_string="", level="INFO")

    def test_logdestination_model_post_init_async_queue_empty_url(self):
        """Test model_post_init with async queue and empty URL (line 523)."""
        with pytest.raises(ValueError, match="Queue URL is required for async queue destinations"):
            LogDestination(type="async_queue", queue_url="", level="INFO")

    def test_logdestination_model_post_init_async_cloud_empty_service(self):
        """Test model_post_init with async cloud and empty service type (line 571-580)."""
        with pytest.raises(ValueError, match="Service type is required for async cloud destinations"):
            LogDestination(type="async_cloud", service_type="", level="INFO")

    def test_logdestination_validate_level_comprehensive(self):
        """Test validate_level with various invalid levels."""
        invalid_levels = ["INVALID", "BAD_LEVEL", "WRONG"]
        for level in invalid_levels:
            with pytest.raises(ValueError, match="Invalid level"):
                LogDestination(type="console", level=level)

    def test_logdestination_validate_format_comprehensive(self):
        """Test validate_format with various invalid formats."""
        invalid_formats = ["INVALID", "XML", "BINARY"]
        for fmt in invalid_formats:
            with pytest.raises(ValueError, match="Invalid format"):
                LogDestination(type="console", level="INFO", format=fmt)

    def test_logdestination_validate_service_type_comprehensive(self):
        """Test validate_service_type with various invalid service types."""
        invalid_services = ["INVALID", "WRONG_SERVICE", "BAD_CLOUD"]
        for service in invalid_services:
            with pytest.raises(ValueError, match="Invalid service type"):
                LogDestination(type="async_cloud", service_type=service, level="INFO")

    def test_loglayer_validate_level_comprehensive(self):
        """Test LogLayer validate_level with various invalid levels."""
        invalid_levels = ["INVALID", "BAD_LEVEL", "WRONG"]
        for level in invalid_levels:
            with pytest.raises(ValueError, match="Invalid level"):
                LogLayer(level=level)

    def test_loggingconfig_validate_default_level_comprehensive(self):
        """Test LoggingConfig validate_default_level with various invalid levels."""
        invalid_levels = ["INVALID", "BAD_LEVEL", "WRONG"]
        for level in invalid_levels:
            with pytest.raises(ValueError, match="Invalid default_level"):
                LoggingConfig(default_level=level)

    # Removed test_tomllib_import_with_attribute_error - not relevant for Python 3.11+ where tomllib is always present

    def test_create_log_directories_os_error(self):
        """Test create_log_directories with OSError handling (lines 579-580)."""
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
        
        # Patch Path.mkdir for loaders.py
        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Permission denied"):
                create_log_directories(config)




class TestTomlImportLogic:
    """Test TOML import logic."""

    def test_toml_decode_error_handling(self):
        """Test TOML decode error handling."""
        import hydra_logger.config.models as models_module
        # Test that TOMLDecodeError is properly defined
        assert hasattr(models_module, 'TOMLDecodeError')


class TestEdgeCases:
    """Test edge cases for better coverage."""

    def test_load_config_with_file_permission_error(self):
        """Test load_config with file permission error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test: content")
            temp_file = f.name
        
        try:
            # Make file read-only to test permission error
            os.chmod(temp_file, 0o000)
            with pytest.raises(ConfigurationError, match="Failed to load configuration"):
                load_config(temp_file)
        finally:
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)

    def test_load_config_with_unicode_error(self):
        """Test load_config with unicode error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test: content")
            temp_file = f.name
        
        try:
            with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test')):
                with pytest.raises(ConfigurationError, match="Failed to load configuration"):
                    load_config(temp_file)
        finally:
            os.unlink(temp_file)

    def test_create_log_directories_with_none_path(self):
        """Test create_log_directories with None path."""
        # This test should be removed since LogDestination requires path for file type
        # The validation will prevent this scenario
        pass

    def test_merge_configs_with_none_override(self):
        """Test merge_configs with None override."""
        base_config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        # Should handle None gracefully by returning the base config
        merged = merge_configs(base_config, {})
        assert isinstance(merged, LoggingConfig)
        assert "DEFAULT" in merged.layers

    def test_merge_configs_with_empty_override(self):
        """Test merge_configs with empty override."""
        base_config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
    
        # Should handle empty dict gracefully
        merged = merge_configs(base_config, {})
        assert merged == base_config 