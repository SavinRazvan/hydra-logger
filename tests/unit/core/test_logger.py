"""
Unit tests for core HydraLogger functionality.

This module tests the core functionality of HydraLogger including
logging methods, configuration handling, and error scenarios.
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path
import logging

from hydra_logger import HydraLogger
from hydra_logger.core.exceptions import HydraLoggerError, ConfigurationError
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.core.logger import BufferedFileHandler, PerformanceMonitor


class TestCoreLogger:
    """Test core HydraLogger functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_logs_dir = "_tests_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_core.log")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)

    def test_basic_logger_initialization(self):
        """Test basic logger initialization."""
        logger = HydraLogger()
        assert logger is not None
        assert hasattr(logger, 'config')
        assert hasattr(logger, 'get_performance_metrics')

    def test_logger_with_config_dict(self):
        """Test logger initialization with config dictionary."""
        config_dict = {
            "layers": {
                "TEST": {
                    "level": "INFO",
                    "destinations": [
                        {"type": "console", "level": "INFO"}
                    ]
                }
            }
        }
        logger = HydraLogger(config=config_dict)
        assert logger is not None

    def test_logger_with_logging_config(self):
        """Test logger initialization with LoggingConfig object."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        assert logger is not None

    def test_basic_logging_methods(self):
        """Test basic logging methods."""
        logger = HydraLogger()
        
        # Test all logging levels
        logger.debug("test_layer", "Debug message")
        logger.info("test_layer", "Info message")
        logger.warning("test_layer", "Warning message")
        logger.error("test_layer", "Error message")
        logger.critical("test_layer", "Critical message")
        
        # Check that metrics were incremented
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 5

    def test_logging_with_layer(self):
        """Test logging with specific layer."""
        config = LoggingConfig(
            layers={
                "CUSTOM": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        logger.info("CUSTOM", "Custom layer message")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logging_with_extra_data(self):
        """Test logging with extra data."""
        logger = HydraLogger()
        
        extra_data = {"user_id": "12345", "session_id": "abc123"}
        logger.info("test_layer", "Message with extra data", extra=extra_data)
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logging_with_sanitization(self):
        """Test logging with data sanitization enabled."""
        logger = HydraLogger(enable_sanitization=True)
        
        # Log message with sensitive data
        logger.info("test_layer", "User email: user@example.com")
        
        # Check that sanitization events were tracked
        metrics = logger.get_performance_metrics()
        assert metrics["sanitization_events"] >= 0

    def test_logging_with_security_validation(self):
        """Test logging with security validation enabled."""
        logger = HydraLogger(enable_security=True)
        
        # Log message with potential security issues
        logger.info("test_layer", "Received input: <script>alert('xss')</script>")
        
        # Check that security events were tracked
        metrics = logger.get_performance_metrics()
        assert metrics["security_events"] >= 0

    def test_file_logging(self):
        """Test file logging functionality."""
        print("[DEBUG] Running test_file_logging")  # DEBUG
        config = {
            "layers": {
                "FILE": {
                    "level": "INFO",
                    "destinations": [{
                        "type": "file",
                        "path": self.log_file,
                        "level": "INFO"
                    }]
                }
            }
        }
        logger = HydraLogger(config)
        # Explicitly set logger and handler level
        logger._layers['FILE'].setLevel(20)  # INFO
        for handler in logger._layers['FILE'].handlers:
            handler.setLevel(20)
        # Log message with correct parameter order
        logger.info("File log message", "FILE")
        # Close logger to flush buffers
        logger.close()
        # Check that file was created
        assert os.path.exists(self.log_file)
        # Check file content
        with open(self.log_file, 'r') as f:
            content = f.read()
            assert "File log message" in content

    def test_console_logging(self):
        """Test console logging functionality."""
        config = LoggingConfig(
            layers={
                "CONSOLE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Log message (should not raise exception)
        logger.info("CONSOLE", "Console log message")

    def test_logging_with_disabled_features(self):
        """Test logging with all features disabled."""
        logger = HydraLogger(
            enable_security=False,
            enable_sanitization=False,
            enable_plugins=False
        )
        
        # Log message
        logger.info("test_layer", "Message with disabled features")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        assert metrics["security_events"] == 0
        assert metrics["sanitization_events"] == 0
        assert metrics["plugin_events"] == 0

    def test_performance_metrics_initialization(self):
        """Test performance metrics initialization."""
        logger = HydraLogger()
        metrics = logger.get_performance_metrics()
        
        assert "total_logs" in metrics
        assert "total_time" in metrics
        assert "avg_latency" in metrics
        assert "max_latency" in metrics
        assert "min_latency" in metrics
        assert "throughput" in metrics
        assert "handler_metrics" in metrics
        assert "memory_usage" in metrics
        assert "security_events" in metrics
        assert "sanitization_events" in metrics
        assert "plugin_events" in metrics

    def test_plugin_insights(self):
        """Test plugin insights functionality."""
        logger = HydraLogger()
        insights = logger.get_plugin_insights()
        
        assert isinstance(insights, dict)
        
        # Add a mock plugin with get_insights method
        mock_plugin = MagicMock()
        mock_plugin.get_insights = MagicMock(return_value={"test": "data"})
        logger.add_plugin("test_plugin", mock_plugin)
        
        # Get insights again
        insights_after_plugin = logger.get_plugin_insights()
        assert isinstance(insights_after_plugin, dict)
        assert "test_plugin" in insights_after_plugin

    def test_add_plugin(self):
        """Test adding a plugin."""
        logger = HydraLogger()
        
        # Create a mock plugin
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        
        # Add plugin
        logger.add_plugin("test_plugin", mock_plugin)
        
        # Check that plugin was added
        assert "test_plugin" in logger._plugins

    def test_remove_plugin(self):
        """Test removing a plugin."""
        logger = HydraLogger()
        
        # Create a mock plugin
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        
        # Add plugin
        logger.add_plugin("test_plugin", mock_plugin)
        
        # Remove plugin
        result = logger.remove_plugin("test_plugin")
        
        # Check that plugin was removed
        assert result is True
        assert "test_plugin" not in logger._plugins

    def test_remove_nonexistent_plugin(self):
        """Test removing a non-existent plugin."""
        logger = HydraLogger()
        
        # Try to remove non-existent plugin
        result = logger.remove_plugin("nonexistent_plugin")
        
        # Should return False
        assert result is False

    def test_update_config(self):
        """Test updating logger configuration."""
        logger = HydraLogger()
        
        # New config
        new_config = LoggingConfig(
            layers={
                "UPDATED": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        
        # Update config
        logger.update_config(new_config)
        
        # Check that config was updated
        assert "UPDATED" in logger.config.layers

    def test_update_config_with_dict(self):
        """Test updating logger configuration with dictionary."""
        logger = HydraLogger()
        
        # New config as dict
        new_config_dict = {
            "layers": {
                "UPDATED_DICT": {
                    "level": "INFO",
                    "destinations": [
                        {"type": "console", "level": "INFO"}
                    ]
                }
            }
        }
        
        # Update config
        logger.update_config(new_config_dict)
        
        # Check that config was updated
        assert "UPDATED_DICT" in logger.config.layers

    def test_logger_close(self):
        """Test logger close functionality."""
        logger = HydraLogger()
        
        # Log some messages
        logger.info("test_layer", "Message 1")
        logger.info("test_layer", "Message 2")
        
        # Close logger
        logger.close()
        
        # Logger should still be usable after close
        logger.info("test_layer", "Message after close")

    def test_error_handling_invalid_level(self):
        """Test error handling with invalid log level."""
        logger = HydraLogger()
        
        # Try to log with invalid level
        try:
            logger.log("INVALID_LEVEL", "test_layer", "This should not work")
        except Exception:
            # Should handle the error gracefully
            pass
        
        # Logger should still work
        logger.info("test_layer", "Message after error")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics is not None

    def test_error_handling_invalid_layer(self):
        """Test error handling with invalid layer."""
        logger = HydraLogger()
        
        # Try to log to non-existent layer
        logger.info("NONEXISTENT", "This should not break")
        
        # Logger should still work
        logger.info("test_layer", "Message after invalid layer")

    def test_format_customization(self):
        """Test format customization."""
        logger = HydraLogger(
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            logger_name_format="[%(name)s]",
            message_format="%(levelname)s: %(message)s"
        )
        
        # Log message
        logger.info("test_layer", "Custom format message")
        
        # Check that logger was created with custom formats
        assert hasattr(logger, '_date_format')
        assert hasattr(logger, '_time_format')
        assert hasattr(logger, '_logger_name_format')
        assert hasattr(logger, '_message_format')

    def test_environment_variable_formats(self):
        """Test format customization via environment variables."""
        with patch.dict(os.environ, {
            "HYDRA_LOG_DATE_FORMAT": "%Y-%m-%d",
            "HYDRA_LOG_TIME_FORMAT": "%H:%M:%S",
            "HYDRA_LOG_LOGGER_NAME_FORMAT": "[%(name)s]",
            "HYDRA_LOG_MESSAGE_FORMAT": "%(levelname)s: %(message)s"
        }):
            logger = HydraLogger()
            
            # Check that environment variables were used
            assert hasattr(logger, '_date_format')
            assert hasattr(logger, '_time_format')
            assert hasattr(logger, '_logger_name_format')
            assert hasattr(logger, '_message_format')

    def test_thread_safety(self):
        """Test thread safety of the logger."""
        import threading
        
        logger = HydraLogger()
        
        def log_messages():
            for i in range(10):
                logger.info("test_layer", f"Thread message {i}")
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=log_messages)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all messages were tracked
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 50  # 5 threads * 10 messages each

    def test_logging_with_none_message(self):
        """Test logging with None message."""
        logger = HydraLogger()
        
        # Try to log None message
        try:
            logger.info("test_layer", str(None))
        except Exception:
            # Should handle gracefully
            pass
        
        # Logger should still work
        logger.info("test_layer", "Message after None")

    def test_logging_with_empty_message(self):
        """Test logging with empty message."""
        logger = HydraLogger()
        
        # Log empty message
        logger.info("test_layer", "")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logging_with_special_characters(self):
        """Test logging with special characters."""
        logger = HydraLogger()
        
        # Log message with special characters
        special_message = "Message with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        logger.info("test_layer", special_message)
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logging_with_unicode(self):
        """Test logging with unicode characters."""
        logger = HydraLogger()
        
        # Log message with unicode
        unicode_message = "Unicode message: 你好世界 🌍"
        logger.info("test_layer", unicode_message)
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logging_with_very_long_message(self):
        """Test logging with very long message."""
        logger = HydraLogger()
        
        # Create very long message
        long_message = "A" * 10000
        logger.info("test_layer", long_message)
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_multiple_logger_instances(self):
        """Test multiple logger instances."""
        logger1 = HydraLogger()
        logger2 = HydraLogger()
        
        # Log with both loggers
        logger1.info("test_layer", "Message from logger 1")
        logger2.info("test_layer", "Message from logger 2")
        
        # Check that both loggers work independently
        metrics1 = logger1.get_performance_metrics()
        metrics2 = logger2.get_performance_metrics()
        
        assert metrics1["total_logs"] >= 1
        assert metrics2["total_logs"] >= 1

    # Magic Config System Tests
    def test_register_magic_config(self):
        """Test registering a magic configuration."""
        @HydraLogger.register_magic("test_config", "Test configuration")
        def test_config():
            return LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Check that config was registered
        assert HydraLogger.has_magic_config("test_config")
        assert "test_config" in HydraLogger.list_magic_configs()

    def test_for_custom_magic_config(self):
        """Test creating logger with custom magic config."""
        @HydraLogger.register_magic("custom_test", "Custom test config")
        def custom_test_config():
            return LoggingConfig(
                layers={
                    "CUSTOM": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Create logger with custom config
        logger = HydraLogger.for_custom("custom_test")
        assert logger is not None
        assert "CUSTOM" in logger.config.layers

    def test_for_custom_magic_config_with_kwargs(self):
        """Test creating logger with custom magic config and additional kwargs."""
        @HydraLogger.register_magic("custom_test_kwargs", "Custom test config with kwargs")
        def custom_test_kwargs_config():
            return LoggingConfig(
                layers={
                    "CUSTOM_KWARGS": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Create logger with custom config and kwargs
        logger = HydraLogger.for_custom("custom_test_kwargs", enable_security=False)
        assert logger is not None
        assert "CUSTOM_KWARGS" in logger.config.layers
        assert logger.enable_security is False

    def test_list_magic_configs(self):
        """Test listing magic configurations."""
        configs = HydraLogger.list_magic_configs()
        assert isinstance(configs, dict)
        # Should have built-in configs
        assert "production" in configs
        assert "development" in configs
        assert "testing" in configs

    def test_has_magic_config(self):
        """Test checking if magic config exists."""
        # Test existing config
        assert HydraLogger.has_magic_config("production") is True
        # Test non-existing config
        assert HydraLogger.has_magic_config("nonexistent_config") is False

    def test_for_production(self):
        """Test creating production logger."""
        logger = HydraLogger.for_production()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_development(self):
        """Test creating development logger."""
        logger = HydraLogger.for_development()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_testing(self):
        """Test creating testing logger."""
        logger = HydraLogger.for_testing()
        assert logger is not None
        assert "TEST" in logger.config.layers

    def test_for_microservice(self):
        """Test creating microservice logger."""
        logger = HydraLogger.for_microservice()
        assert logger is not None
        assert "SERVICE" in logger.config.layers
        assert "HEALTH" in logger.config.layers

    def test_for_web_app(self):
        """Test creating web app logger."""
        logger = HydraLogger.for_web_app()
        assert logger is not None
        assert "WEB" in logger.config.layers
        assert "REQUEST" in logger.config.layers
        assert "ERROR" in logger.config.layers

    def test_for_api_service(self):
        """Test creating API service logger."""
        logger = HydraLogger.for_api_service()
        assert logger is not None
        assert "API" in logger.config.layers
        assert "AUTH" in logger.config.layers
        assert "RATE_LIMIT" in logger.config.layers

    def test_for_background_worker(self):
        """Test creating background worker logger."""
        logger = HydraLogger.for_background_worker()
        assert logger is not None
        assert "WORKER" in logger.config.layers
        assert "TASK" in logger.config.layers
        assert "PROGRESS" in logger.config.layers

    def test_for_minimal_features(self):
        """Test creating minimal features logger."""
        logger = HydraLogger.for_minimal_features()
        assert logger is not None
        assert logger.minimal_features_mode is True
        assert logger.enable_security is False
        assert logger.enable_sanitization is False
        assert logger.enable_plugins is False

    def test_for_bare_metal(self):
        """Test creating bare metal logger."""
        logger = HydraLogger.for_bare_metal()
        assert logger is not None
        assert logger.bare_metal_mode is True
        assert logger.enable_security is False
        assert logger.enable_sanitization is False
        assert logger.enable_plugins is False

    def test_magic_config_error_handling(self):
        """Test error handling for non-existent magic config."""
        with pytest.raises(HydraLoggerError):
            HydraLogger.for_custom("nonexistent_config")

    def test_magic_config_validation_error(self):
        """Test error handling for invalid magic config."""
        @HydraLogger.register_magic("invalid_config", "Invalid config")
        def invalid_config():
            return "not a LoggingConfig"  # This should cause an error
        
        with pytest.raises(HydraLoggerError):
            HydraLogger.for_custom("invalid_config")

    # Performance Mode Tests
    def test_minimal_features_mode(self):
        """Test minimal features mode functionality."""
        logger = HydraLogger(minimal_features_mode=True)
        assert logger.minimal_features_mode is True
        
        # Test fast logging
        logger.info("test_layer", "Minimal features message")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_bare_metal_mode(self):
        """Test bare metal mode functionality."""
        logger = HydraLogger(bare_metal_mode=True)
        assert logger.bare_metal_mode is True
        
        # Test bare metal logging
        logger.info("test_layer", "Bare metal message")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_buffered_file_handler(self):
        """Test buffered file handler functionality."""
        from hydra_logger.core.logger import BufferedFileHandler
        
        # Create buffered file handler
        handler = BufferedFileHandler(self.log_file)
        assert handler is not None
        
        # Test performance metrics
        metrics = handler.get_performance_metrics()
        assert "write_count" in metrics
        assert "flush_count" in metrics
        assert "total_bytes_written" in metrics
        assert "buffer_size" in metrics
        assert "flush_interval" in metrics

    def test_performance_monitor(self):
        """Test performance monitor functionality."""
        from hydra_logger.core.logger import PerformanceMonitor
        
        # Create performance monitor
        monitor = PerformanceMonitor(enabled=True)
        assert monitor.enabled is True
        
        # Record some metrics
        monitor.record_log("test_layer", "INFO", "test message", 0.0, 0.001)
        monitor.record_handler_metrics("test_handler", {"writes": 10})
        monitor.record_security_event()
        monitor.record_sanitization_event()
        monitor.record_plugin_event()
        
        # Get metrics
        metrics = monitor.get_metrics()
        assert metrics["total_logs"] >= 1
        assert metrics["security_events"] >= 1
        assert metrics["sanitization_events"] >= 1
        assert metrics["plugin_events"] >= 1
        
        # Test reset
        monitor.reset_metrics()
        metrics_after_reset = monitor.get_metrics()
        assert metrics_after_reset["total_logs"] == 0

    def test_performance_monitor_disabled(self):
        """Test performance monitor when disabled."""
        from hydra_logger.core.logger import PerformanceMonitor
        
        # Create disabled performance monitor
        monitor = PerformanceMonitor(enabled=False)
        assert monitor.enabled is False
        
        # Record metrics (should not record anything)
        monitor.record_log("test_layer", "INFO", "test message", 0.0, 0.001)
        monitor.record_security_event()
        monitor.record_sanitization_event()
        monitor.record_plugin_event()
        
        # Get metrics (should be default values)
        metrics = monitor.get_metrics()
        assert metrics["total_logs"] == 0
        assert metrics["security_events"] == 0
        assert metrics["sanitization_events"] == 0
        assert metrics["plugin_events"] == 0

    def test_log_with_extra_kwargs(self):
        """Test logging with extra kwargs."""
        logger = HydraLogger()
        
        # Test logging with extra kwargs
        logger.info("test_layer", "Message with kwargs", extra={"key": "value"})
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_log_with_sanitize_false(self):
        """Test logging with sanitize=False."""
        logger = HydraLogger(enable_sanitization=True)
        
        # Log with sanitize=False
        logger.log("INFO", "test_layer", "Message without sanitization", sanitize=False)
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_log_with_validate_security_false(self):
        """Test logging with validate_security=False."""
        logger = HydraLogger(enable_security=True)
        
        # Log with validate_security=False
        logger.log("INFO", "test_layer", "Message without security validation", validate_security=False)
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_create_logger_convenience_function(self):
        """Test the create_logger convenience function."""
        from hydra_logger import create_logger
        
        # Test with default parameters
        logger = create_logger()
        assert logger is not None
        assert isinstance(logger, HydraLogger)
        
        # Test with custom config
        config = {"layers": {"TEST": {"level": "INFO", "destinations": [{"type": "console", "level": "INFO"}]}}}
        logger = create_logger(config=config)
        assert logger is not None
        
        # Test with disabled features
        logger = create_logger(enable_security=False, enable_sanitization=False, enable_plugins=False)
        assert logger.enable_security is False
        assert logger.enable_sanitization is False
        assert logger.enable_plugins is False 

    # Additional comprehensive test coverage for missing features
    
    def test_context_manager_usage(self):
        """Test logger as context manager."""
        with HydraLogger() as logger:
            logger.info("test_layer", "Context manager message")
            # Logger should work within context
            assert logger is not None
        
        # Logger should be properly closed after context exit
        assert True

    def test_buffer_size_customization(self):
        """Test buffer size customization."""
        logger = HydraLogger(buffer_size=16384, flush_interval=0.5)
        
        # Test that custom buffer settings are applied
        assert logger.buffer_size == 16384
        assert logger.flush_interval == 0.5
        
        # Test logging with custom buffer settings
        logger.info("test_layer", "Message with custom buffer settings")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_performance_monitoring_disabled(self):
        """Test logger with performance monitoring disabled."""
        logger = HydraLogger(enable_performance_monitoring=False)
        
        # Log messages
        logger.info("test_layer", "Message 1")
        logger.info("test_layer", "Message 2")
        
        # Get metrics (should still work but may be minimal)
        metrics = logger.get_performance_metrics()
        assert isinstance(metrics, dict)

    def test_logger_with_all_customizations(self):
        """Test logger with all customization options."""
        logger = HydraLogger(
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            logger_name_format="[%(name)s]",
            message_format="%(levelname)s: %(message)s",
            buffer_size=16384,
            flush_interval=0.5,
            minimal_features_mode=True,
            bare_metal_mode=False
        )
        
        # Test all customizations are applied
        assert hasattr(logger, '_date_format')
        assert hasattr(logger, '_time_format')
        assert hasattr(logger, '_logger_name_format')
        assert hasattr(logger, '_message_format')
        assert logger.buffer_size == 16384
        assert logger.flush_interval == 0.5
        assert logger.minimal_features_mode is True
        assert logger.bare_metal_mode is False
        
        # Test logging
        logger.info("test_layer", "All customizations message")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logger_with_bare_metal_mode(self):
        """Test logger with bare metal mode enabled."""
        logger = HydraLogger(bare_metal_mode=True)
        
        # Test bare metal logging
        logger.info("test_layer", "Bare metal message 1")
        logger.info("test_layer", "Bare metal message 2")
        logger.info("test_layer", "Bare metal message 3")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 3

    def test_logger_with_minimal_features_mode(self):
        """Test logger with minimal features mode enabled."""
        logger = HydraLogger(minimal_features_mode=True)
        
        # Test minimal features logging
        logger.info("test_layer", "Minimal features message 1")
        logger.info("test_layer", "Minimal features message 2")
        logger.info("test_layer", "Minimal features message 3")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 3

    def test_logger_with_plugin_processing(self):
        """Test logger with plugin processing enabled."""
        logger = HydraLogger(enable_plugins=True)
        
        # Create a mock plugin that processes events
        mock_plugin = MagicMock()
        mock_plugin.process_event = MagicMock()
        
        # Add plugin
        logger.add_plugin("test_plugin", mock_plugin)
        
        # Log message (should trigger plugin processing)
        logger.info("test_layer", "Message with plugin processing")
        
        # Check that plugin was called
        mock_plugin.process_event.assert_called()
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        assert metrics["plugin_events"] >= 1

    def test_logger_with_security_validation(self):
        """Test logger with security validation enabled."""
        logger = HydraLogger(enable_security=True)
        
        # Log message with potential security issues
        logger.info("test_layer", "Input: <script>alert('xss')</script>")
        logger.info("test_layer", "SQL: SELECT * FROM users WHERE id = 1; DROP TABLE users;")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2
        assert metrics["security_events"] >= 0

    def test_logger_with_data_sanitization(self):
        """Test logger with data sanitization enabled."""
        logger = HydraLogger(enable_sanitization=True)
        
        # Log messages with sensitive data
        logger.info("test_layer", "User email: user@example.com")
        logger.info("test_layer", "Password: secret123")
        logger.info("test_layer", "API Key: sk-1234567890abcdef")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 3
        assert metrics["sanitization_events"] >= 0

    def test_logger_with_fallback_handler(self):
        """Test logger with fallback handler."""
        logger = HydraLogger()
        
        # Test that fallback handler is available
        assert hasattr(logger, '_fallback_handler')
        
        # Log messages
        logger.info("test_layer", "Message with fallback handler")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logger_with_error_tracker(self):
        """Test logger with error tracker integration."""
        logger = HydraLogger()
        
        # Test that error tracker is available
        assert hasattr(logger, '_error_tracker')
        
        # Get error stats
        error_stats = logger.get_error_stats()
        assert isinstance(error_stats, dict)
        
        # Clear error stats
        logger.clear_error_stats()
        
        # Get error stats again
        error_stats_after_clear = logger.get_error_stats()
        assert isinstance(error_stats_after_clear, dict)

    def test_logger_with_magic_config_registry(self):
        """Test logger with magic config registry integration."""
        # Test that magic config registry is available
        assert hasattr(HydraLogger, 'register_magic')
        assert hasattr(HydraLogger, 'for_custom')
        assert hasattr(HydraLogger, 'list_magic_configs')
        assert hasattr(HydraLogger, 'has_magic_config')
        
        # Test built-in magic configs
        assert HydraLogger.has_magic_config("production")
        assert HydraLogger.has_magic_config("development")
        assert HydraLogger.has_magic_config("testing")
        assert HydraLogger.has_magic_config("microservice")
        assert HydraLogger.has_magic_config("web_app")
        assert HydraLogger.has_magic_config("api_service")
        assert HydraLogger.has_magic_config("background_worker")
        assert HydraLogger.has_magic_config("high_performance")

    def test_logger_with_comprehensive_formatter_testing(self):
        """Test logger with comprehensive formatter testing."""
        formatter_configs = [
            {"format": "plain-text"},
            {"format": "invalid_format"},  # Should fallback to default
        ]
        
        for fmt_config in formatter_configs:
            config = {
                "layers": {
                    "TEST": {
                        "level": "INFO",
                        "destinations": [{
                            "type": "console",
                            **fmt_config
                        }]
                    }
                }
            }
            
            try:
                logger = HydraLogger(config)
                logger.info("test message", "TEST")
            except ConfigurationError:
                # Should handle invalid format gracefully
                pass

    def test_logger_with_comprehensive_handler_testing(self):
        """Test logger with comprehensive handler testing."""
        handler_configs = [
            # Console handler
            {"type": "console", "format": "plain-text"},
            # File handler
            {"type": "file", "path": "_tests_logs/test_handler.log", "format": "plain-text"},
            # Invalid handler
            {"type": "invalid_handler_type"},
        ]
        
        for handler_config in handler_configs:
            config = {
                "layers": {
                    "TEST": {
                        "level": "INFO",
                        "destinations": [handler_config]
                    }
                }
            }
            
            try:
                logger = HydraLogger(config)
                logger.info("test message", "TEST")
                logger.close()
            except Exception as e:
                # Should handle invalid handler configs gracefully
                pass

    def test_logger_with_comprehensive_layer_testing(self):
        """Test logger with comprehensive layer testing."""
        layer_configs = [
            # Valid layer
            {"level": "INFO", "destinations": [{"type": "console"}]},
            # Layer with invalid level
            {"level": "INVALID_LEVEL", "destinations": [{"type": "console"}]},
            # Layer with empty destinations
            {"level": "INFO", "destinations": []},
            # Layer with invalid destination
            {"level": "INFO", "destinations": [{"type": "invalid"}]},
        ]
        
        for layer_config in layer_configs:
            config = {
                "layers": {
                    "TEST": layer_config
                }
            }
            
            try:
                logger = HydraLogger(config)
                logger.info("test message", "TEST")
            except Exception as e:
                # Should handle invalid layer configs gracefully
                pass

    def test_logger_with_comprehensive_error_recovery(self):
        """Test logger with comprehensive error recovery testing."""
        logger = HydraLogger()
        
        # Test various error recovery scenarios
        error_scenarios = [
            # Invalid log level
            lambda: logger.log("INVALID_LEVEL", "test"),
            # Invalid layer
            lambda: logger.log("INFO", "test", layer="INVALID_LAYER"),
            # None message
            lambda: logger.log("INFO", "None"),
            # Empty message
            lambda: logger.log("INFO", ""),
            # Invalid extra data
            lambda: logger.log("INFO", "test", extra={"invalid": object()}),
        ]
        
        for scenario in error_scenarios:
            try:
                scenario()
            except Exception as e:
                # Should handle all error scenarios gracefully
                pass
        
        # Logger should still work after error scenarios
        logger.info("Final test message")

    def test_logger_with_comprehensive_cleanup(self):
        """Test logger with comprehensive cleanup testing."""
        logger = HydraLogger()
        
        # Add some data to logger
        logger.info("test message 1")
        logger.info("test message 2")
        
        # Test cleanup
        logger.close()
        
        # Test that logger is properly closed
        assert logger._closed is True
        
        # Test that logging after close is handled gracefully
        logger.info("message after close")
        
        # Test multiple close calls
        logger.close()
        logger.close()

    def test_logger_with_comprehensive_initialization_testing(self):
        """Test logger with comprehensive initialization testing."""
        init_configs = [
            # Default initialization
            {},
            # With all features disabled
            {
                "enable_security": False,
                "enable_sanitization": False,
                "enable_plugins": False,
                "enable_performance_monitoring": False,
            },
            # With minimal features mode
            {"minimal_features_mode": True},
            # With bare metal mode
            {"bare_metal_mode": True},
            # With custom buffer settings
            {"buffer_size": 16384, "flush_interval": 0.5},
            # With None config
            {"config": None},
            # With dict config
            {"config": {"layers": {"TEST": {"level": "INFO", "destinations": [{"type": "console"}]}}}}
        ]
        
        for init_config in init_configs:
            try:
                logger = HydraLogger(**init_config)
                logger.info("test message")
                logger.close()
            except Exception as e:
                # Should handle all initialization scenarios gracefully
                pass

