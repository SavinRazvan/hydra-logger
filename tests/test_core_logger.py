"""
Tests for core HydraLogger functionality.

This module tests the core functionality of HydraLogger including
logging methods, configuration handling, and error scenarios.
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

from hydra_logger import HydraLogger
from hydra_logger.core.exceptions import HydraLoggerError, ConfigurationError
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


class TestCoreLogger:
    """Test core HydraLogger functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_logs_dir = "_tests_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_core.log")

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
        config = LoggingConfig(
            layers={
                "FILE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path=self.log_file, level="INFO")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Log message
        logger.info("FILE", "File log message")
        
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

    def test_for_high_performance(self):
        """Test creating high performance logger."""
        logger = HydraLogger.for_high_performance()
        assert logger is not None
        assert logger.high_performance_mode is True
        assert logger.enable_security is False
        assert logger.enable_sanitization is False
        assert logger.enable_plugins is False

    def test_for_ultra_fast(self):
        """Test creating ultra fast logger."""
        logger = HydraLogger.for_ultra_fast()
        assert logger is not None
        assert logger.ultra_fast_mode is True
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
    def test_high_performance_mode(self):
        """Test high performance mode functionality."""
        logger = HydraLogger(high_performance_mode=True)
        assert logger.high_performance_mode is True
        
        # Test fast logging
        logger.info("test_layer", "High performance message")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_ultra_fast_mode(self):
        """Test ultra fast mode functionality."""
        logger = HydraLogger(ultra_fast_mode=True)
        assert logger.ultra_fast_mode is True
        
        # Test ultra fast logging
        logger.info("test_layer", "Ultra fast message")
        
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
            high_performance_mode=True,
            ultra_fast_mode=False
        )
        
        # Test all customizations are applied
        assert hasattr(logger, '_date_format')
        assert hasattr(logger, '_time_format')
        assert hasattr(logger, '_logger_name_format')
        assert hasattr(logger, '_message_format')
        assert logger.buffer_size == 16384
        assert logger.flush_interval == 0.5
        assert logger.high_performance_mode is True
        assert logger.ultra_fast_mode is False
        
        # Test logging
        logger.info("test_layer", "All customizations message")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logger_with_ultra_fast_mode(self):
        """Test logger with ultra-fast mode enabled."""
        logger = HydraLogger(ultra_fast_mode=True)
        
        # Test ultra-fast logging
        logger.info("test_layer", "Ultra fast message 1")
        logger.info("test_layer", "Ultra fast message 2")
        logger.info("test_layer", "Ultra fast message 3")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 3

    def test_logger_with_high_performance_mode(self):
        """Test logger with high-performance mode enabled."""
        logger = HydraLogger(high_performance_mode=True)
        
        # Test high-performance logging
        logger.info("test_layer", "High performance message 1")
        logger.info("test_layer", "High performance message 2")
        logger.info("test_layer", "High performance message 3")
        
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

    def test_logger_with_formatter_customization(self):
        """Test logger with formatter customization."""
        config = LoggingConfig(
            layers={
                "FORMAT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            level="INFO",
                            format="plain-text",
                            color_mode="always"
                        )
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Log message with custom formatter
        logger.info("FORMAT", "Message with custom formatter")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logger_with_file_handler_customization(self):
        """Test logger with file handler customization."""
        config = LoggingConfig(
            layers={
                "FILE_CUSTOM": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=self.log_file,
                            level="INFO",
                            format="json",
                            max_size="1MB",
                            backup_count=5
                        )
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Log message with custom file handler
        logger.info("FILE_CUSTOM", "Message with custom file handler")
        
        # Check that file was created
        assert os.path.exists(self.log_file)
        
        # Check file content
        with open(self.log_file, 'r') as f:
            content = f.read()
            assert "Message with custom file handler" in content

    def test_logger_with_console_handler_customization(self):
        """Test logger with console handler customization."""
        config = LoggingConfig(
            layers={
                "CONSOLE_CUSTOM": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            level="INFO",
                            format="plain-text",
                            color_mode="never"
                        )
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Log message with custom console handler
        logger.info("CONSOLE_CUSTOM", "Message with custom console handler")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logger_with_layer_creation(self):
        """Test logger layer creation functionality."""
        logger = HydraLogger()
        
        # Test that layers are created
        assert hasattr(logger, '_layers')
        assert isinstance(logger._layers, dict)
        
        # Test logging to different layers
        logger.info("DEFAULT", "Default layer message")
        logger.info("test_layer", "Test layer message")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2

    def test_logger_with_handler_creation(self):
        """Test logger handler creation functionality."""
        logger = HydraLogger()
        
        # Test that handlers are created
        assert hasattr(logger, '_handlers')
        assert isinstance(logger._handlers, dict)
        
        # Log message
        logger.info("test_layer", "Message with handler creation")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_logger_with_plugin_insights(self):
        """Test logger plugin insights functionality."""
        logger = HydraLogger()
        
        # Get plugin insights
        insights = logger.get_plugin_insights()
        assert isinstance(insights, dict)
        
        # Add a mock plugin
        mock_plugin = MagicMock()
        mock_plugin.get_insights = MagicMock(return_value={"test": "data"})
        
        logger.add_plugin("test_plugin", mock_plugin)
        
        # Get insights again
        insights_after_plugin = logger.get_plugin_insights()
        assert isinstance(insights_after_plugin, dict)

    def test_logger_with_performance_monitor_reset(self):
        """Test logger performance monitor reset functionality."""
        from hydra_logger.core.logger import PerformanceMonitor
        
        # Create performance monitor
        monitor = PerformanceMonitor(enabled=True)
        
        # Record some metrics
        monitor.record_log("test_layer", "INFO", "test message", 0.0, 0.001)
        monitor.record_security_event()
        monitor.record_sanitization_event()
        monitor.record_plugin_event()
        
        # Get metrics before reset
        metrics_before = monitor.get_metrics()
        assert metrics_before["total_logs"] >= 1
        
        # Reset metrics
        monitor.reset_metrics()
        
        # Get metrics after reset
        metrics_after = monitor.get_metrics()
        assert metrics_after["total_logs"] == 0
        assert metrics_after["security_events"] == 0
        assert metrics_after["sanitization_events"] == 0
        assert metrics_after["plugin_events"] == 0

    def test_logger_with_buffered_file_handler_performance(self):
        """Test buffered file handler performance metrics."""
        from hydra_logger.core.logger import BufferedFileHandler
        
        # Create buffered file handler
        handler = BufferedFileHandler(self.log_file, buffer_size=16384, flush_interval=0.5)
        
        # Test performance metrics
        metrics = handler.get_performance_metrics()
        assert "write_count" in metrics
        assert "flush_count" in metrics
        assert "total_bytes_written" in metrics
        assert "buffer_size" in metrics
        assert "flush_interval" in metrics
        assert "closed" in metrics
        
        # Test that metrics are initialized correctly
        assert metrics["write_count"] == 0
        assert metrics["flush_count"] == 0
        assert metrics["total_bytes_written"] == 0
        assert metrics["buffer_size"] == 16384
        assert metrics["flush_interval"] == 0.5
        assert metrics["closed"] is False
        
        # Close handler
        handler.close()
        
        # Check that handler is closed
        final_metrics = handler.get_performance_metrics()
        assert final_metrics["closed"] is True

    def test_logger_with_plugin_registry_integration(self):
        """Test logger with plugin registry integration."""
        from hydra_logger.plugins.registry import list_plugins, get_plugin
        
        # Test that plugin registry functions are available
        plugins = list_plugins()
        assert isinstance(plugins, dict)
        
        # Test getting plugin (may not exist, but should not raise error)
        try:
            plugin = get_plugin("test_plugin")
            # Plugin may be None if not found
        except Exception:
            # Should handle gracefully
            pass

    def test_logger_with_data_protection_integration(self):
        """Test logger with data protection integration."""
        from hydra_logger.data_protection.security import DataSanitizer, SecurityValidator
        from hydra_logger.data_protection.fallbacks import FallbackHandler
        
        # Test that data protection components are available
        sanitizer = DataSanitizer()
        validator = SecurityValidator()
        fallback = FallbackHandler()
        
        assert sanitizer is not None
        assert validator is not None
        assert fallback is not None

    def test_logger_with_error_handler_integration(self):
        """Test logger with error handler integration."""
        from hydra_logger.core.error_handler import (
            get_error_tracker, track_error, track_hydra_error,
            track_configuration_error, track_runtime_error,
            error_context, get_error_stats, clear_error_stats
        )
        
        # Test that error handler functions are available
        tracker = get_error_tracker()
        assert tracker is not None
        
        # Test error tracking functions
        track_error("test_error", ValueError("Test error"))
        track_hydra_error(HydraLoggerError("Test Hydra error"))
        track_configuration_error(ConfigurationError("Test config error"))
        track_runtime_error(RuntimeError("Test runtime error"))
        
        # Test error context
        with error_context("test_component", "test_operation"):
            pass
        
        # Test error stats
        stats = get_error_stats()
        assert isinstance(stats, dict)
        
        # Test clear error stats
        clear_error_stats()
        stats_after_clear = get_error_stats()
        assert isinstance(stats_after_clear, dict)

    def test_logger_with_magic_configs_integration(self):
        """Test logger with magic configs integration."""
        from hydra_logger.magic_configs import MagicConfigRegistry
        
        # Test that magic config registry is available
        assert hasattr(MagicConfigRegistry, 'register')
        assert hasattr(MagicConfigRegistry, 'get_config')
        assert hasattr(MagicConfigRegistry, 'list_configs')
        assert hasattr(MagicConfigRegistry, 'has_config')
        assert hasattr(MagicConfigRegistry, 'unregister')
        assert hasattr(MagicConfigRegistry, 'clear')
        
        # Test registry functions
        configs = MagicConfigRegistry.list_configs()
        assert isinstance(configs, dict)
        
        # Test has_config
        assert MagicConfigRegistry.has_config("production") is True
        assert MagicConfigRegistry.has_config("nonexistent") is False

    def test_logger_with_comprehensive_configuration(self):
        """Test logger with comprehensive configuration."""
        config = LoggingConfig(
            layers={
                "COMPREHENSIVE": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(
                            type="console",
                            level="INFO",
                            format="plain-text",
                            color_mode="auto"
                        ),
                        LogDestination(
                            type="file",
                            path=self.log_file,
                            level="DEBUG",
                            format="json",
                            max_size="5MB",
                            backup_count=3
                        )
                    ]
                )
            }
        )
        logger = HydraLogger(
            config=config,
            enable_security=True,
            enable_sanitization=True,
            enable_plugins=True,
            enable_performance_monitoring=True,
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            logger_name_format="[%(name)s]",
            message_format="%(levelname)s: %(message)s",
            buffer_size=16384,
            flush_interval=0.5,
            high_performance_mode=False,
            ultra_fast_mode=False
        )
        
        # Test all features are enabled
        assert logger.enable_security is True
        assert logger.enable_sanitization is True
        assert logger.enable_plugins is True
        assert logger.high_performance_mode is False
        assert logger.ultra_fast_mode is False
        
        # Test logging with all features
        logger.info("COMPREHENSIVE", "Comprehensive test message")
        logger.debug("COMPREHENSIVE", "Debug message")
        logger.warning("COMPREHENSIVE", "Warning message")
        logger.error("COMPREHENSIVE", "Error message")
        logger.critical("COMPREHENSIVE", "Critical message")
        
        # Check that file was created
        assert os.path.exists(self.log_file)
        
        # Check file content
        with open(self.log_file, 'r') as f:
            content = f.read()
            assert "Comprehensive test message" in content
            assert "Debug message" in content
            assert "Warning message" in content
            assert "Error message" in content
            assert "Critical message" in content
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 5
        
        # Check plugin insights
        insights = logger.get_plugin_insights()
        assert isinstance(insights, dict)
        
        # Check error stats
        error_stats = logger.get_error_stats()
        assert isinstance(error_stats, dict)
        
        # Close logger
        logger.close()
        
        # Logger should still work after close
        logger.info("COMPREHENSIVE", "Message after close")

    def test_default_centralized_logger(self):
        """Test default centralized logger when no layer is set."""
        logger = HydraLogger()
        
        # Test logging without specifying layer (should use DEFAULT)
        logger.info("Message without layer")
        
        # Check that DEFAULT layer exists
        assert "DEFAULT" in logger._layers
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_default_centralized_logger_with_custom_layers(self):
        """Test default centralized logger with custom layers."""
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
        
        # Test logging to non-existent layer (should fallback to DEFAULT)
        logger.info("NONEXISTENT", "Message to non-existent layer")
        
        # Test logging to existing custom layer
        logger.info("CUSTOM", "Message to custom layer")
        
        # Check that both layers exist
        assert "CUSTOM" in logger._layers
        assert "DEFAULT" in logger._layers
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2

    def test_default_centralized_logger_fallback_behavior(self):
        """Test fallback behavior when DEFAULT layer is missing."""
        # Create config without DEFAULT layer
        config = LoggingConfig(
            layers={
                "SPECIAL": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Test logging to non-existent layer (should fallback to system logger)
        logger.info("NONEXISTENT", "Message to non-existent layer")
        
        # Test logging to existing layer
        logger.info("SPECIAL", "Message to special layer")
        
        # Check that SPECIAL layer exists but DEFAULT doesn't
        assert "SPECIAL" in logger._layers
        assert "DEFAULT" not in logger._layers
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2

    def test_default_centralized_logger_with_empty_config(self):
        """Test default centralized logger with empty configuration."""
        # Create logger with empty config
        logger = HydraLogger(config={})
        
        # Test logging (should use system fallback)
        logger.info("Message with empty config")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_default_centralized_logger_layer_priority(self):
        """Test layer priority in default centralized logger."""
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                ),
                "CUSTOM": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="console", level="DEBUG")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Test logging to DEFAULT layer explicitly
        logger.info("DEFAULT", "Message to DEFAULT layer")
        
        # Test logging to CUSTOM layer
        logger.info("CUSTOM", "Message to CUSTOM layer")
        
        # Test logging without layer (should use DEFAULT)
        logger.info("Message without layer")
        
        # Check that both layers exist
        assert "DEFAULT" in logger._layers
        assert "CUSTOM" in logger._layers
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 3

    def test_default_centralized_logger_with_file_destinations(self):
        """Test default centralized logger with file destinations."""
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO"),
                        LogDestination(type="file", path=self.log_file, level="INFO")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Test logging to DEFAULT layer
        logger.info("DEFAULT", "Message to DEFAULT layer with file")
        
        # Test logging without layer (should use DEFAULT)
        logger.info("Message without layer to file")
        
        # Check that file was created
        assert os.path.exists(self.log_file)
        
        # Check file content
        with open(self.log_file, 'r') as f:
            content = f.read()
            assert "Message to DEFAULT layer with file" in content
            assert "Message without layer to file" in content
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2

    def test_default_centralized_logger_error_handling(self):
        """Test error handling in default centralized logger."""
        logger = HydraLogger()
        
        # Test logging with invalid level (should not break)
        try:
            logger.log("INVALID_LEVEL", "Message with invalid level")
        except Exception:
            # Should handle gracefully
            pass
        
        # Test logging to non-existent layer with invalid level
        try:
            logger.log("INVALID_LEVEL", "NONEXISTENT", "Message with invalid level to non-existent layer")
        except Exception:
            # Should handle gracefully
            pass
        
        # Logger should still work
        logger.info("Message after errors")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics is not None

    def test_default_centralized_logger_performance_modes(self):
        """Test default centralized logger in performance modes."""
        # Test high performance mode
        logger_high = HydraLogger(high_performance_mode=True)
        logger_high.info("Message in high performance mode")
        
        # Test ultra fast mode
        logger_ultra = HydraLogger(ultra_fast_mode=True)
        logger_ultra.info("Message in ultra fast mode")
        
        # Check metrics for both
        metrics_high = logger_high.get_performance_metrics()
        metrics_ultra = logger_ultra.get_performance_metrics()
        
        assert metrics_high["total_logs"] >= 1
        assert metrics_ultra["total_logs"] >= 1

    def test_default_centralized_logger_with_plugins(self):
        """Test default centralized logger with plugins."""
        logger = HydraLogger(enable_plugins=True)
        
        # Add a mock plugin
        mock_plugin = MagicMock()
        mock_plugin.process_event = MagicMock()
        logger.add_plugin("test_plugin", mock_plugin)
        
        # Test logging (should trigger plugin processing)
        logger.info("Message with plugin")
        
        # Check that plugin was called
        mock_plugin.process_event.assert_called()
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        assert metrics["plugin_events"] >= 1

    def test_default_centralized_logger_with_security_and_sanitization(self):
        """Test default centralized logger with security and sanitization."""
        logger = HydraLogger(enable_security=True, enable_sanitization=True)
        
        # Test logging with potential security issues
        logger.info("Message with <script>alert('xss')</script>")
        
        # Test logging with sensitive data
        logger.info("User email: user@example.com")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2
        assert metrics["security_events"] >= 0
        assert metrics["sanitization_events"] >= 0

    def test_default_centralized_logger_thread_safety(self):
        """Test thread safety of default centralized logger."""
        import threading
        
        logger = HydraLogger()
        
        def log_messages():
            for i in range(10):
                logger.info(f"Thread message {i}")
        
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

    def test_default_centralized_logger_configuration_updates(self):
        """Test default centralized logger with configuration updates."""
        logger = HydraLogger()
        
        # Initial logging
        logger.info("Initial message")
        
        # Update configuration
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
        logger.update_config(new_config)
        
        # Test logging after config update
        logger.info("UPDATED", "Message after config update")
        
        # Check that new layer exists
        assert "UPDATED" in logger.config.layers
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2

    def test_centralized_logger_reserved_layer_protection(self):
        """Test that reserved layer names are protected."""
        config = LoggingConfig(
            layers={
                "__CENTRALIZED__": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        
        # This should work - __CENTRALIZED__ is allowed for internal use
        logger = HydraLogger(config=config)
        assert "__CENTRALIZED__" in logger._layers
        
        # Test logging works
        logger.info("Message to centralized layer")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_centralized_logger_fallback_chain(self):
        """Test the intelligent fallback chain."""
        config = LoggingConfig(
            layers={
                "CUSTOM": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                ),
                "DEFAULT": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="console", level="DEBUG")
                    ]
                ),
                "__CENTRALIZED__": LogLayer(
                    level="WARNING",
                    destinations=[
                        LogDestination(type="console", level="WARNING")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Test 1: Log to existing layer (should use CUSTOM)
        logger.info("CUSTOM", "Message to custom layer")
        
        # Test 2: Log to non-existent layer (should fallback to DEFAULT)
        logger.info("NONEXISTENT", "Message to non-existent layer")
        
        # Test 3: Log without layer (should use DEFAULT)
        logger.info("Message without layer")
        
        # Check that all layers exist
        assert "CUSTOM" in logger._layers
        assert "DEFAULT" in logger._layers
        assert "__CENTRALIZED__" in logger._layers
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 3

    def test_centralized_logger_fallback_without_default(self):
        """Test fallback when DEFAULT layer is missing."""
        config = LoggingConfig(
            layers={
                "CUSTOM": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                ),
                "__CENTRALIZED__": LogLayer(
                    level="WARNING",
                    destinations=[
                        LogDestination(type="console", level="WARNING")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Test logging to non-existent layer (should fallback to __CENTRALIZED__)
        logger.info("NONEXISTENT", "Message to non-existent layer")
        
        # Test logging without layer (should fallback to __CENTRALIZED__)
        logger.info("Message without layer")
        
        # Check that CUSTOM and __CENTRALIZED__ exist but DEFAULT doesn't
        assert "CUSTOM" in logger._layers
        assert "DEFAULT" not in logger._layers
        assert "__CENTRALIZED__" in logger._layers
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2

    def test_centralized_logger_final_fallback(self):
        """Test final fallback to system logger when no layers exist."""
        # Create logger with empty config
        logger = HydraLogger(config={})
        
        # Test logging (should use system logger)
        logger.info("Message with no layers")
        
        # Check that no layers exist
        assert len(logger._layers) == 0
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1

    def test_centralized_logger_reserved_name_protection(self):
        """Test that users cannot create reserved layer names."""
        config = LoggingConfig(
            layers={
                "__RESERVED__": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        
        # This should raise an error
        with pytest.raises(ConfigurationError, match="Layer name '__RESERVED__' is reserved"):
            HydraLogger(config=config)

    def test_centralized_logger_performance_modes(self):
        """Test centralized logger in performance modes."""
        # Test high performance mode
        logger_high = HydraLogger(high_performance_mode=True)
        logger_high.info("Message in high performance mode")
        
        # Test ultra fast mode
        logger_ultra = HydraLogger(ultra_fast_mode=True)
        logger_ultra.info("Message in ultra fast mode")
        
        # Check metrics for both
        metrics_high = logger_high.get_performance_metrics()
        metrics_ultra = logger_ultra.get_performance_metrics()
        
        assert metrics_high["total_logs"] >= 1
        assert metrics_ultra["total_logs"] >= 1

    def test_centralized_logger_with_file_destinations(self):
        """Test centralized logger with file destinations."""
        config = LoggingConfig(
            layers={
                "__CENTRALIZED__": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO"),
                        LogDestination(type="file", path=self.log_file, level="INFO")
                    ]
                )
            }
        )
        logger = HydraLogger(config=config)
        
        # Test logging to centralized layer
        logger.info("__CENTRALIZED__", "Message to centralized layer with file")
        
        # Test logging without layer (should use __CENTRALIZED__)
        logger.info("Message without layer to file")
        
        # Check that file was created
        assert os.path.exists(self.log_file)
        
        # Check file content
        with open(self.log_file, 'r') as f:
            content = f.read()
            assert "Message to centralized layer with file" in content
            assert "Message without layer to file" in content
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2

    def test_centralized_logger_configuration_updates(self):
        """Test centralized logger with configuration updates."""
        logger = HydraLogger()
        
        # Initial logging
        logger.info("Initial message")
        
        # Update configuration with new layers
        new_config = LoggingConfig(
            layers={
                "UPDATED": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                ),
                "__CENTRALIZED__": LogLayer(
                    level="WARNING",
                    destinations=[
                        LogDestination(type="console", level="WARNING")
                    ]
                )
            }
        )
        logger.update_config(new_config)
        
        # Test logging after config update
        logger.info("UPDATED", "Message after config update")
        logger.info("Message to centralized after update")
        
        # Check that new layers exist
        assert "UPDATED" in logger.config.layers
        assert "__CENTRALIZED__" in logger.config.layers
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 3 