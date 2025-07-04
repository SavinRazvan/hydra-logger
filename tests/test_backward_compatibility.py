"""
Backward Compatibility Tests for Hydra-Logger.

This module tests that all existing configurations, APIs, and usage patterns
continue to work correctly with the new zero-configuration and enhanced features.
"""

import os
import tempfile
import pytest
from unittest.mock import patch

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.compatibility import setup_logging, migrate_to_hydra


class TestBackwardCompatibility:
    """Test backward compatibility of all existing APIs and configurations."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    def test_old_config_constructor_still_works(self, temp_dir):
        """Test that old LoggingConfig constructor still works."""
        # Old way of creating config
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
                        LogDestination(
                            type="console",
                            level="WARNING",
                            format="json"
                        )
                    ]
                )
            },
            default_level="INFO"
        )
        
        logger = HydraLogger(config)
        
        # Test that logging works
        logger.info("APP", "Test message")
        
        # Verify file was created
        assert os.path.exists(os.path.join(temp_dir, "app.log"))
        
        # Verify content
        with open(os.path.join(temp_dir, "app.log"), "r") as f:
            content = f.read()
            assert "Test message" in content

    def test_old_from_config_method_still_works(self, temp_dir):
        """Test that from_config method still works with old config files."""
        # Create old-style config file
        config_content = """
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: {temp_dir}/app.log
        format: text
      - type: console
        level: WARNING
        format: json
default_level: INFO
""".format(temp_dir=temp_dir)
        
        config_file = os.path.join(temp_dir, "config.yaml")
        with open(config_file, "w") as f:
            f.write(config_content)
        
        # Test old from_config method
        logger = HydraLogger.from_config(config_file)
        
        # Test that logging works
        logger.info("APP", "Test message from config file")
        
        # Verify file was created
        assert os.path.exists(os.path.join(temp_dir, "app.log"))
        
        # Verify content
        with open(os.path.join(temp_dir, "app.log"), "r") as f:
            content = f.read()
            assert "Test message from config file" in content

    def test_old_logging_methods_still_work(self, temp_dir):
        """Test that all old logging methods still work."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "app.log"),
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Test all old logging methods
        logger.debug("APP", "Debug message")
        logger.info("APP", "Info message")
        logger.warning("APP", "Warning message")
        logger.error("APP", "Error message")
        logger.critical("APP", "Critical message")
        
        # Test old log method
        logger.log("APP", "INFO", "Log method message")
        
        # Verify file was created and contains messages
        assert os.path.exists(os.path.join(temp_dir, "app.log"))
        
        with open(os.path.join(temp_dir, "app.log"), "r") as f:
            content = f.read()
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
            assert "Critical message" in content
            assert "Log method message" in content

    def test_old_get_logger_method_still_works(self, temp_dir):
        """Test that get_logger method still works."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "app.log"),
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Test get_logger method
        app_logger = logger.get_logger("APP")
        assert app_logger is not None
        assert hasattr(app_logger, "info")
        assert hasattr(app_logger, "debug")
        assert hasattr(app_logger, "warning")
        assert hasattr(app_logger, "error")
        assert hasattr(app_logger, "critical")
        
        # Test that the underlying logger works
        app_logger.info("Test message from underlying logger")
        
        # Verify file was created
        assert os.path.exists(os.path.join(temp_dir, "app.log"))
        
        with open(os.path.join(temp_dir, "app.log"), "r") as f:
            content = f.read()
            assert "Test message from underlying logger" in content

    def test_old_compatibility_functions_still_work(self, temp_dir):
        """Test that old compatibility functions still work."""
        # Test setup_logging function (should not raise)
        try:
            setup_logging(
                root_level=20,  # INFO
                file_level=10,   # DEBUG
                console_level=20, # INFO
                enable_file_logging=True,
                enable_console_logging=True
            )
        except Exception as e:
            pytest.fail(f"setup_logging raised an exception: {e}")
        
        # Test migrate_to_hydra function (should not raise)
        try:
            migrate_to_hydra(
                enable_file_logging=True,
                console_level=20,
                file_level=10,
                log_file_path=os.path.join(temp_dir, "migrated.log")
            )
        except Exception as e:
            pytest.fail(f"migrate_to_hydra raised an exception: {e}")

    def test_old_config_file_formats_still_work(self, temp_dir):
        """Test that old config file formats still work."""
        # Test YAML format
        yaml_config = """
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: {temp_dir}/yaml_app.log
        format: text
default_level: INFO
""".format(temp_dir=temp_dir)
        
        yaml_file = os.path.join(temp_dir, "config.yaml")
        with open(yaml_file, "w") as f:
            f.write(yaml_config)
        
        logger = HydraLogger.from_config(yaml_file)
        logger.info("APP", "YAML config test")
        
        assert os.path.exists(os.path.join(temp_dir, "yaml_app.log"))
        
        # Test TOML format
        toml_config = """
default_level = "INFO"

[layers.APP]
level = "INFO"

[[layers.APP.destinations]]
type = "file"
path = "{temp_dir}/toml_app.log"
format = "text"
""".format(temp_dir=temp_dir)
        
        toml_file = os.path.join(temp_dir, "config.toml")
        with open(toml_file, "w") as f:
            f.write(toml_config)
        
        logger = HydraLogger.from_config(toml_file)
        logger.info("APP", "TOML config test")
        
        assert os.path.exists(os.path.join(temp_dir, "toml_app.log"))

    def test_old_destination_types_still_work(self, temp_dir):
        """Test that all old destination types still work."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "file.log"),
                            format="text"
                        ),
                        LogDestination(
                            type="console",
                            level="WARNING",
                            format="json"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Test that both destinations work
        logger.info("APP", "File and console test")
        logger.warning("APP", "Warning for console")
        
        # Verify file was created
        assert os.path.exists(os.path.join(temp_dir, "file.log"))
        
        with open(os.path.join(temp_dir, "file.log"), "r") as f:
            content = f.read()
            assert "File and console test" in content
            assert "Warning for console" in content

    def test_old_format_types_still_work(self, temp_dir):
        """Test that all old format types still work."""
        config = LoggingConfig(
            layers={
                "TEXT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "text.log"),
                            format="text"
                        )
                    ]
                ),
                "JSON": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "json.json"),
                            format="json"
                        )
                    ]
                ),
                "CSV": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "csv.csv"),
                            format="csv"
                        )
                    ]
                ),
                "SYSLOG": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "syslog.log"),
                            format="syslog"
                        )
                    ]
                ),
                "GELF": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "gelf.gelf"),
                            format="gelf"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Test all formats
        logger.info("TEXT", "Text format test")
        logger.info("JSON", "JSON format test")
        logger.info("CSV", "CSV format test")
        logger.info("SYSLOG", "Syslog format test")
        logger.info("GELF", "GELF format test")
        
        # Verify all files were created
        assert os.path.exists(os.path.join(temp_dir, "text.log"))
        assert os.path.exists(os.path.join(temp_dir, "json.json"))
        assert os.path.exists(os.path.join(temp_dir, "csv.csv"))
        assert os.path.exists(os.path.join(temp_dir, "syslog.log"))
        assert os.path.exists(os.path.join(temp_dir, "gelf.gelf"))

    def test_old_parameter_names_still_work(self, temp_dir):
        """Test that old parameter names still work."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "app.log"),
                            max_size="5MB",
                            backup_count=3,
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        logger.info("APP", "Parameter test")
        
        # Verify file was created
        assert os.path.exists(os.path.join(temp_dir, "app.log"))
        
        with open(os.path.join(temp_dir, "app.log"), "r") as f:
            content = f.read()
            assert "Parameter test" in content

    def test_old_error_handling_still_works(self):
        """Test that old error handling patterns still work."""
        # Test with invalid config
        with pytest.raises(ValueError):
            LoggingConfig(
                layers={
                    "APP": LogLayer(
                        level="INVALID_LEVEL",
                        destinations=[]
                    )
                }
            )
        
        # Test with invalid destination type
        with pytest.raises(ValueError):
            LogDestination(type="invalid_type", path="test.log")
        
        # Test with missing required parameters
        with pytest.raises(ValueError):
            LogDestination(type="file")  # Missing path

    def test_old_default_config_still_works(self):
        """Test that old default config still works."""
        # Test default constructor
        logger = HydraLogger()
        
        # Test that logging works
        logger.info("DEFAULT", "Default config test")
        
        # Test that get_logger works
        default_logger = logger.get_logger("DEFAULT")
        assert default_logger is not None

    def test_old_layer_fallback_still_works(self, temp_dir):
        """Test that old layer fallback still works."""
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "default.log"),
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Test logging to non-existent layer (should fallback to DEFAULT)
        logger.info("NONEXISTENT", "Fallback test")
        
        # Verify file was created
        assert os.path.exists(os.path.join(temp_dir, "default.log"))
        
        with open(os.path.join(temp_dir, "default.log"), "r") as f:
            content = f.read()
            assert "Fallback test" in content

    def test_old_level_validation_still_works(self):
        """Test that old level validation still works."""
        # Test valid levels
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            config = LoggingConfig(
                layers={
                    "APP": LogLayer(
                        level=level,
                        destinations=[]
                    )
                }
            )
            assert config.layers["APP"].level == level
        
        # Test invalid level
        with pytest.raises(ValueError):
            LoggingConfig(
                layers={
                    "APP": LogLayer(
                        level="INVALID",
                        destinations=[]
                    )
                }
            )

    def test_old_size_parsing_still_works(self):
        """Test that old size parsing still works."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path="test.log",
                            max_size="5MB",
                            backup_count=3
                        )
                    ]
                )
            }
        )
        
        # Test various size formats
        size_tests = ["5MB", "10KB", "1GB", "100B"]
        for size in size_tests:
            LogDestination(
                type="file",
                path="test.log",
                max_size=size
            )

    def test_old_imports_still_work(self):
        """Test that all old imports still work."""
        # Test main imports
        from hydra_logger import HydraLogger
        from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
        from hydra_logger.compatibility import setup_logging, migrate_to_hydra
        
        # Test that classes can be instantiated
        config = LoggingConfig()
        layer = LogLayer(level="INFO", destinations=[])
        destination = LogDestination(type="console")
        
        assert config is not None
        assert layer is not None
        assert destination is not None

    def test_old_api_signatures_still_work(self):
        """Test that old API signatures still work."""
        # Test HydraLogger constructor
        logger = HydraLogger()  # No parameters
        logger = HydraLogger(None)  # None config
        
        # Test logging methods
        logger.info("DEFAULT", "Test")
        logger.debug("DEFAULT", "Test")
        logger.warning("DEFAULT", "Test")
        logger.error("DEFAULT", "Test")
        logger.critical("DEFAULT", "Test")
        logger.log("DEFAULT", "INFO", "Test")
        
        # Test get_logger
        default_logger = logger.get_logger("DEFAULT")
        assert default_logger is not None

    def test_old_config_validation_still_works(self):
        """Test that old config validation still works."""
        # Test valid config
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console")
                    ]
                )
            }
        )
        assert config is not None
        
        # Test invalid config
        with pytest.raises(ValueError):
            LoggingConfig(
                layers={
                    "APP": LogLayer(
                        level="INVALID",
                        destinations=[]
                    )
                }
            )

    def test_old_file_operations_still_work(self, temp_dir):
        """Test that old file operations still work."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "test.log"),
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Test file creation
        logger.info("APP", "File operation test")
        
        # Verify file exists and is writable
        file_path = os.path.join(temp_dir, "test.log")
        assert os.path.exists(file_path)
        assert os.access(file_path, os.W_OK)
        
        # Test file content
        with open(file_path, "r") as f:
            content = f.read()
            assert "File operation test" in content

    def test_old_console_output_still_works(self, capsys):
        """Test that old console output still works."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            level="INFO",
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Test console output
        logger.info("APP", "Console output test")
        
        captured = capsys.readouterr()
        assert "Console output test" in captured.out

    def test_old_error_handling_patterns_still_work(self, temp_dir):
        """Test that old error handling patterns still work."""
        # Test with invalid file path
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path="/invalid/path/test.log",
                            format="text"
                        )
                    ]
                )
            }
        )
        
        # Should not crash, should fallback gracefully
        logger = HydraLogger(config)
        logger.info("APP", "Error handling test")
        
        # Test with invalid console config (should raise validation error)
        with pytest.raises(ValueError):
            LoggingConfig(
                layers={
                    "APP": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(
                                type="console",
                                level="INVALID",
                                format="text"
                            )
                        ]
                    )
                }
            )

    def test_old_performance_patterns_still_work(self, temp_dir):
        """Test that old performance patterns still work."""
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "perf.log"),
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Test multiple rapid log calls
        for i in range(100):
            logger.info("APP", f"Performance test {i}")
        
        # Verify all messages were logged
        with open(os.path.join(temp_dir, "perf.log"), "r") as f:
            content = f.read()
            for i in range(100):
                assert f"Performance test {i}" in content

    def test_old_threading_patterns_still_work(self, temp_dir):
        """Test that old threading patterns still work."""
        import threading
        import time
        
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "thread.log"),
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        def log_messages(thread_id):
            for i in range(10):
                logger.info("APP", f"Thread {thread_id} message {i}")
                time.sleep(0.01)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all messages were logged
        with open(os.path.join(temp_dir, "thread.log"), "r") as f:
            content = f.read()
            for thread_id in range(5):
                for i in range(10):
                    assert f"Thread {thread_id} message {i}" in content 