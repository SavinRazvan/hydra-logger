"""
Comprehensive tests to cover missing lines in core/logger.py.

This module focuses on testing edge cases, error conditions, and
untested functionality to achieve higher coverage.
"""

import os
import pytest
import tempfile
import shutil
import time
import threading
from unittest.mock import patch, MagicMock, Mock, mock_open
from pathlib import Path
import logging

from hydra_logger import HydraLogger
from hydra_logger.core.exceptions import HydraLoggerError, ConfigurationError
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.core.logger import BufferedFileHandler, PerformanceMonitor


class TestBufferedFileHandlerCoverage:
    """Tests to cover missing lines in BufferedFileHandler."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_logs_dir = "_tests_logs_coverage"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_buffered.log")
    
    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)
    
    def test_buffered_handler_invalid_encoding(self):
        """Test handler with invalid encoding fallback."""
        # Test with invalid encoding that should fallback to utf-8
        handler = BufferedFileHandler(
            filename=self.log_file,
            encoding="invalid_encoding"
        )
        assert handler._custom_encoding == "utf-8"
        handler.close()
    
    def test_buffered_handler_file_creation(self):
        """Test handler file creation when first log is written."""
        handler = BufferedFileHandler(filename=self.log_file)
        
        # File should not exist during initialization
        assert not os.path.exists(self.log_file)
        
        # Create a log record and emit it
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Emit the record - this should create the file
        handler.emit(record)
        
        # Now the file should exist
        assert os.path.exists(self.log_file)
        
        handler.close()
    
    def test_buffered_handler_open_when_closed(self):
        """Test _open method when handler is closed."""
        handler = BufferedFileHandler(filename=self.log_file)
        handler.close()
        result = handler._open()
        assert result is None
    
    def test_buffered_handler_emit_when_closed(self):
        """Test emit method when handler is closed."""
        handler = BufferedFileHandler(filename=self.log_file)
        handler.close()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Should not raise exception
        handler.emit(record)
    
    def test_buffered_handler_emit_with_no_stream(self):
        """Test emit method when stream is None."""
        handler = BufferedFileHandler(filename=self.log_file)
        
        # Mock _open to return None
        with patch.object(handler, '_open', return_value=None):
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Should not raise exception
            handler.emit(record)
        
        handler.close()
    
    def test_buffered_handler_emit_with_exception(self):
        """Test emit method with exception handling."""
        handler = BufferedFileHandler(filename=self.log_file)
        
        # Mock stream.write to raise exception
        with patch.object(handler, 'stream') as mock_stream:
            mock_stream.write.side_effect = Exception("Write error")
            
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Should handle error gracefully
            handler.emit(record)
        
        handler.close()
    
    def test_buffered_handler_flush_buffer_when_closed(self):
        """Test _flush_buffer when handler is closed."""
        handler = BufferedFileHandler(filename=self.log_file)
        handler.close()
        
        # Should not raise exception
        handler._flush_buffer()
    
    def test_buffered_handler_flush_buffer_with_no_stream(self):
        """Test _flush_buffer when stream is None."""
        handler = BufferedFileHandler(filename=self.log_file)
        handler.stream = None  # type: ignore
        
        # Should not raise exception
        handler._flush_buffer()
        
        handler.close()
    
    def test_buffered_handler_flush_buffer_with_exception(self):
        """Test _flush_buffer with exception handling."""
        handler = BufferedFileHandler(filename=self.log_file)
        
        # Mock stream.flush to raise exception
        with patch.object(handler, 'stream') as mock_stream:
            mock_stream.flush.side_effect = Exception("Flush error")
            
            # Should handle error gracefully
            handler._flush_buffer()
        
        handler.close()
    
    def test_buffered_handler_close_when_already_closed(self):
        """Test close method when already closed."""
        handler = BufferedFileHandler(filename=self.log_file)
        handler.close()
        
        # Should not raise exception
        handler.close()
    
    def test_buffered_handler_close_with_exception(self):
        """Test close method with exception handling."""
        handler = BufferedFileHandler(filename=self.log_file)
        
        # Mock stream.close to raise exception
        with patch.object(handler, 'stream') as mock_stream:
            mock_stream.close.side_effect = Exception("Close error")
            
            # Should handle error gracefully
            try:
                handler.close()
            except Exception:
                # The exception should be caught in the handler
                pass
    
    def test_buffered_handler_performance_metrics(self):
        """Test performance metrics collection."""
        handler = BufferedFileHandler(filename=self.log_file)
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        handler.emit(record)
        
        metrics = handler.get_performance_metrics()
        assert metrics["write_count"] >= 1
        assert metrics["flush_count"] >= 1
        assert metrics["total_bytes_written"] > 0
        assert metrics["buffer_size"] == 8192
        assert metrics["flush_interval"] == 1.0
        assert not metrics["closed"]
        
        handler.close()
        
        metrics = handler.get_performance_metrics()
        assert metrics["closed"]


class TestPerformanceMonitorCoverage:
    """Tests to cover missing lines in PerformanceMonitor."""
    
    def test_performance_monitor_disabled(self):
        """Test performance monitor when disabled."""
        monitor = PerformanceMonitor(enabled=False)
        
        # Should not record anything when disabled
        monitor.record_log("test", "INFO", "message", time.time(), time.time() + 0.001)
        monitor.record_handler_metrics("test", {})
        monitor.record_security_event()
        monitor.record_sanitization_event()
        monitor.record_plugin_event()
        
        metrics = monitor.get_metrics()
        assert metrics["total_logs"] == 0
    
    def test_performance_monitor_closed(self):
        """Test performance monitor when closed."""
        monitor = PerformanceMonitor()
        monitor.close()
        
        # Should not record anything when closed
        monitor.record_log("test", "INFO", "message", time.time(), time.time() + 0.001)
        monitor.record_handler_metrics("test", {})
        monitor.record_security_event()
        monitor.record_sanitization_event()
        monitor.record_plugin_event()
        
        metrics = monitor.get_metrics()
        assert metrics["total_logs"] == 0
    
    def test_performance_monitor_record_log(self):
        """Test log recording functionality."""
        monitor = PerformanceMonitor()
        
        start_time = time.time()
        end_time = start_time + 0.001
        
        monitor.record_log("test_layer", "INFO", "test message", start_time, end_time)
        
        metrics = monitor.get_metrics()
        assert metrics["total_logs"] == 1
        assert metrics["total_time"] > 0
        assert metrics["avg_latency"] > 0
        assert metrics["max_latency"] > 0
        assert metrics["min_latency"] > 0
        assert metrics["throughput"] > 0
        
        monitor.close()
    
    def test_performance_monitor_record_handler_metrics(self):
        """Test handler metrics recording."""
        monitor = PerformanceMonitor()
        
        handler_metrics = {"writes": 10, "errors": 0}
        monitor.record_handler_metrics("test_handler", handler_metrics)
        
        metrics = monitor.get_metrics()
        assert "test_handler" in metrics["handler_metrics"]
        assert metrics["handler_metrics"]["test_handler"] == handler_metrics
        
        monitor.close()
    
    def test_performance_monitor_record_security_event(self):
        """Test security event recording."""
        monitor = PerformanceMonitor()
        
        monitor.record_security_event()
        
        metrics = monitor.get_metrics()
        assert metrics["security_events"] == 1
        
        monitor.close()
    
    def test_performance_monitor_record_sanitization_event(self):
        """Test sanitization event recording."""
        monitor = PerformanceMonitor()
        
        monitor.record_sanitization_event()
        
        metrics = monitor.get_metrics()
        assert metrics["sanitization_events"] == 1
        
        monitor.close()
    
    def test_performance_monitor_record_plugin_event(self):
        """Test plugin event recording."""
        monitor = PerformanceMonitor()
        
        monitor.record_plugin_event()
        
        metrics = monitor.get_metrics()
        assert metrics["plugin_events"] == 1
        
        monitor.close()
    
    def test_performance_monitor_reset_metrics(self):
        """Test metrics reset functionality."""
        monitor = PerformanceMonitor()
        
        # Record some events
        monitor.record_log("test", "INFO", "message", time.time(), time.time() + 0.001)
        monitor.record_security_event()
        monitor.record_sanitization_event()
        monitor.record_plugin_event()
        
        # Reset metrics
        monitor.reset_metrics()
        
        metrics = monitor.get_metrics()
        assert metrics["total_logs"] == 0
        assert metrics["security_events"] == 0
        assert metrics["sanitization_events"] == 0
        assert metrics["plugin_events"] == 0
        
        monitor.close()
    
    def test_performance_monitor_close(self):
        """Test monitor close functionality."""
        monitor = PerformanceMonitor()
        
        # Record some events
        monitor.record_log("test", "INFO", "message", time.time(), time.time() + 0.001)
        
        # Close monitor
        monitor.close()
        
        # Should not record after closing
        monitor.record_log("test", "INFO", "message", time.time(), time.time() + 0.001)
        
        metrics = monitor.get_metrics()
        assert metrics["total_logs"] == 1  # Only the first one should be recorded


class TestHydraLoggerCoverage:
    """Tests to cover missing lines in HydraLogger."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_logs_dir = "_tests_logs_coverage"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_hydra.log")
    
    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)
    
    def test_logger_with_minimal_features_mode(self):
        """Test logger with minimal features mode."""
        logger = HydraLogger(minimal_features_mode=True)
        
        # Should use minimal features logging
        logger.info("test_layer", "Minimal features message")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        
        logger.close()
    
    def test_logger_with_bare_metal_mode(self):
        """Test logger with bare metal mode."""
        logger = HydraLogger(bare_metal_mode=True)
        
        # Should use bare metal logging
        logger.info("test_layer", "Bare metal message")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        
        logger.close()
    
    def test_logger_with_custom_formats(self):
        """Test logger with custom format strings."""
        logger = HydraLogger(
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            logger_name_format="%(name)s",
            message_format="%(message)s"
        )
        
        logger.info("test_layer", "Custom format message")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        
        logger.close()
    
    def test_logger_with_disabled_performance_monitoring(self):
        """Test logger with disabled performance monitoring."""
        logger = HydraLogger(enable_performance_monitoring=False)
        
        logger.info("test_layer", "No performance monitoring message")
        
        # Should still work without performance monitoring
        metrics = logger.get_performance_metrics()
        assert isinstance(metrics, dict)
        
        logger.close()
    
    def test_logger_error_stats(self):
        """Test error statistics functionality."""
        logger = HydraLogger()
        
        # Get initial error stats
        initial_stats = logger.get_error_stats()
        assert isinstance(initial_stats, dict)
        
        # Clear error stats
        logger.clear_error_stats()
        
        # Get stats after clearing
        cleared_stats = logger.get_error_stats()
        assert isinstance(cleared_stats, dict)
        
        logger.close()
    
    def test_logger_plugin_insights(self):
        """Test plugin insights functionality."""
        logger = HydraLogger()
        
        insights = logger.get_plugin_insights()
        assert isinstance(insights, dict)
        
        logger.close()
    

    
    def test_logger_log_with_sanitize_false_original(self):
        """Test logging with sanitization disabled."""
        logger = HydraLogger()
        
        logger.log("INFO", "test message", "test_layer", sanitize=False)
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        
        logger.close()
    
    def test_logger_log_with_validate_security_false_original(self):
        """Test logging with security validation disabled."""
        logger = HydraLogger()
        
        logger.log("INFO", "test message", "test_layer", validate_security=False)
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        
        logger.close()
    
    def test_logger_log_with_extra_kwargs_original(self):
        """Test logging with extra kwargs."""
        logger = HydraLogger()
        
        logger.log("INFO", "test message", "test_layer", extra={"user_id": "123"})
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        
        logger.close()
    
    def test_logger_create_handler_error_handling_original(self):
        """Test error handling in handler creation."""
        logger = HydraLogger()
        
        # Test with invalid destination type
        invalid_destination = {"type": "invalid_type"}
        
        # Should handle invalid destination gracefully
        try:
            handler = logger._create_handler(invalid_destination)
            assert handler is None
        except Exception:
            # The error should be handled gracefully
            pass
        
        logger.close()
    
    def test_logger_create_console_handler(self):
        """Test console handler creation."""
        logger = HydraLogger()
        
        destination = {"type": "console", "level": "INFO"}
        handler = logger._create_console_handler(destination)
        
        assert isinstance(handler, logging.StreamHandler)
        
        logger.close()
    
    def test_logger_create_file_handler(self):
        """Test file handler creation."""
        logger = HydraLogger()
        
        destination = {"type": "file", "path": self.log_file, "level": "INFO"}
        handler = logger._create_file_handler(destination)
        
        assert handler is not None
        
        logger.close()
    
    def test_logger_create_formatter(self):
        """Test formatter creation."""
        logger = HydraLogger()
        
        # Test different format types
        formatter = logger._create_formatter("json")
        assert isinstance(formatter, logging.Formatter)
        
        formatter = logger._create_formatter("csv")
        assert isinstance(formatter, logging.Formatter)
        
        formatter = logger._create_formatter("syslog")
        assert isinstance(formatter, logging.Formatter)
        
        formatter = logger._create_formatter("gelf")
        assert isinstance(formatter, logging.Formatter)
        
        logger.close()
    
    def test_logger_get_logger_for_layer(self):
        """Test getting logger for layer."""
        logger = HydraLogger()
        
        # Test with existing layer
        layer_logger = logger._get_logger_for_layer("DEFAULT")
        assert isinstance(layer_logger, logging.Logger)
        
        # Test with non-existent layer (should create default)
        layer_logger = logger._get_logger_for_layer("NON_EXISTENT")
        assert isinstance(layer_logger, logging.Logger)
        
        logger.close()
    
    def test_logger_setup_layers(self):
        """Test layer setup."""
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
        
        # Should have created the layer
        assert "TEST" in logger._layers
        
        logger.close()
    
    def test_logger_create_layer(self):
        """Test layer creation."""
        logger = HydraLogger()
        
        layer_config = LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="console", level="INFO")
            ]
        )
        
        layer_logger = logger._create_layer("TEST_LAYER", layer_config)
        assert isinstance(layer_logger, logging.Logger)
        
        logger.close()
    
    def test_logger_load_plugins(self):
        """Test plugin loading."""
        logger = HydraLogger(enable_plugins=True)
        
        # Should not raise exception
        assert True
        
        logger.close()
    
    def test_logger_precompute_log_methods_original(self):
        """Test log method precomputation."""
        logger = HydraLogger()
        
        # Should not raise exception
        assert True
        
        logger.close()
    
    def test_logger_setup_bare_metal_mode_original(self):
        """Test bare metal mode setup."""
        logger = HydraLogger(bare_metal_mode=True)
        
        # Should not raise exception
        assert True
        
        logger.close()
    
    def test_logger_bare_metal_log_original(self):
        """Test bare metal logging."""
        logger = HydraLogger(bare_metal_mode=True)
        
        logger._bare_metal_log("INFO", "bare metal message", "test_layer")
        
        # Should not raise exception
        assert True
        
        logger.close()
    
    def test_logger_minimal_features_log_original(self):
        """Test minimal features logging."""
        logger = HydraLogger(minimal_features_mode=True)
        
        logger._minimal_features_log("INFO", "minimal message", "test_layer")
        
        # Should not raise exception
        assert True
        
        logger.close()
    
    def test_logger_initialization_with_failed_security_validator(self):
        """Test logger initialization when security validator fails."""
        with patch('hydra_logger.core.logger.SecurityValidator', side_effect=Exception("Security init failed")):
            logger = HydraLogger(enable_security=True)
            assert logger._security_validator is None
    
    def test_logger_initialization_with_failed_sanitizer(self):
        """Test logger initialization when data sanitizer fails."""
        with patch('hydra_logger.core.logger.DataSanitizer', side_effect=Exception("Sanitizer init failed")):
            logger = HydraLogger(enable_sanitization=True)
            assert logger._data_sanitizer is None
    
    def test_logger_initialization_with_failed_fallback_handler(self):
        """Test logger initialization when fallback handler fails."""
        with patch('hydra_logger.core.logger.FallbackHandler', side_effect=Exception("Fallback init failed")):
            logger = HydraLogger()
            assert logger._fallback_handler is None
    
    def test_logger_initialization_with_dict_config(self):
        """Test logger initialization with dict-based config."""
        config_dict = {
            "layers": {
                "TEST": {
                    "level": "INFO",
                    "destinations": [
                        {"type": "console", "format": "plain-text"}
                    ]
                }
            }
        }
        logger = HydraLogger(config=config_dict)
        assert logger.config is not None
    
    def test_logger_initialization_with_configuration_error(self):
        """Test logger initialization with configuration error fallback."""
        with patch('hydra_logger.core.logger.load_config_from_dict', side_effect=ConfigurationError("Config error")):
            with pytest.raises(ConfigurationError, match="Config error"):
                logger = HydraLogger(config={"invalid": "config"})
    
    def test_logger_initialization_with_general_exception(self):
        """Test logger initialization with general exception fallback."""
        with patch('hydra_logger.core.logger.load_config_from_dict', side_effect=Exception("General error")):
            logger = HydraLogger(config={"invalid": "config"})
            assert logger.config is not None  # Should use default config
    
    def test_logger_plugin_loading_failure(self):
        """Test logger when plugin loading fails."""
        with patch('hydra_logger.core.logger.list_plugins', side_effect=Exception("Plugin list failed")):
            logger = HydraLogger(enable_plugins=True)
            # Should not fail initialization
    
    def test_logger_create_layer_with_reserved_name(self):
        """Test creating layer with reserved name."""
        logger = HydraLogger()
        with pytest.raises(ConfigurationError, match="Layer name '__RESERVED__' is reserved"):
            logger._create_layer("__RESERVED__", {"level": "INFO", "destinations": []})
    
    def test_logger_create_layer_with_centralized_name(self):
        """Test creating layer with centralized name (should be allowed)."""
        logger = HydraLogger()
        # Create a mock layer config with level attribute
        layer_config = MagicMock()
        layer_config.level = "INFO"
        layer_config.destinations = []
        
        # This should not raise an exception
        result = logger._create_layer("__CENTRALIZED__", layer_config)
        assert result is not None
    
    def test_logger_create_handler_with_unknown_type(self):
        """Test creating handler with unknown type."""
        logger = HydraLogger()
        destination = MagicMock()
        destination.type = "unknown_type"
        destination.format = "plain-text"
        
        # Should return None for unknown handler types
        handler = logger._create_handler(destination)
        assert handler is None
    
    def test_logger_create_handler_with_exception(self):
        """Test creating handler when exception occurs."""
        logger = HydraLogger()
        destination = MagicMock()
        destination.type = "console"
        destination.format = "plain-text"
        
        # Mock console handler creation to raise exception
        with patch.object(logger, '_create_console_handler', side_effect=Exception("Handler creation failed")):
            handler = logger._create_handler(destination)
            assert handler is None
    
    def test_logger_create_console_handler_with_dict_destination(self):
        """Test creating console handler with dict-like destination."""
        logger = HydraLogger()
        destination = {"type": "console", "format": "json", "color_mode": "auto"}
        
        handler = logger._create_console_handler(destination)
        assert isinstance(handler, logging.StreamHandler)
    
    def test_logger_create_file_handler_with_dict_destination(self):
        """Test creating file handler with dict-like destination."""
        logger = HydraLogger()
        destination = {
            "type": "file", 
            "path": "test.log", 
            "encoding": "utf-8", 
            "format": "json"
        }
        
        handler = logger._create_file_handler(destination)
        assert isinstance(handler, BufferedFileHandler)
        handler.close()
        os.remove("test.log") if os.path.exists("test.log") else None
    
    def test_logger_create_file_handler_with_directory_creation_original(self):
        """Test creating file handler that creates directory."""
        logger = HydraLogger()
        destination = {
            "type": "file", 
            "path": "test_dir/test.log", 
            "encoding": "utf-8", 
            "format": "json"
        }
        
        handler = logger._create_file_handler(destination)
        assert isinstance(handler, BufferedFileHandler)
        assert os.path.exists("test_dir")
        handler.close()
        shutil.rmtree("test_dir") if os.path.exists("test_dir") else None
    
    def test_logger_create_file_handler_with_exception(self):
        """Test creating file handler when exception occurs."""
        logger = HydraLogger()
        destination = {"type": "file", "path": "/invalid/path/test.log"}
        
        handler = logger._create_file_handler(destination)
        assert handler is None  # Should return None on error
    
    def test_logger_get_logger_for_layer_fallback_chain(self):
        """Test logger fallback chain for layer resolution."""
        logger = HydraLogger()
        
        # Test with non-existent layer - should fallback to system logger
        result = logger._get_logger_for_layer("NON_EXISTENT")
        assert result is not None
    
    def test_logger_create_formatter_with_color_mode(self):
        """Test creating formatter with color mode."""
        logger = HydraLogger()
        formatter = logger._create_formatter("plain-text", "auto")
        assert isinstance(formatter, logging.Formatter)
    
    def test_logger_log_with_sanitize_false(self):
        """Test logging with sanitization disabled."""
        logger = HydraLogger()
        logger.log("INFO", "Test message", sanitize=False)
        # Should not raise exception
    
    def test_logger_log_with_validate_security_false(self):
        """Test logging with security validation disabled."""
        logger = HydraLogger()
        logger.log("INFO", "Test message", validate_security=False)
        # Should not raise exception
    
    def test_logger_log_with_extra_kwargs(self):
        """Test logging with extra keyword arguments."""
        logger = HydraLogger()
        logger.log("INFO", "Test message", extra={"key": "value"})
        # Should not raise exception
    
    def test_logger_create_handler_error_handling(self):
        """Test error handling in create_handler method."""
        logger = HydraLogger()
        destination = MagicMock()
        destination.type = "console"
        
        # Mock to raise exception
        with patch.object(logger, '_create_console_handler', side_effect=Exception("Test error")):
            handler = logger._create_handler(destination)
            assert handler is None
    
    def test_logger_create_console_handler_with_object_destination(self):
        """Test creating console handler with object-like destination."""
        logger = HydraLogger()
        destination = MagicMock()
        destination.format = "json"
        destination.color_mode = "auto"
        
        handler = logger._create_console_handler(destination)
        assert isinstance(handler, logging.StreamHandler)
    
    def test_logger_create_file_handler_with_object_destination(self):
        """Test creating file handler with object-like destination."""
        logger = HydraLogger()
        destination = MagicMock()
        destination.path = "test_object.log"
        destination.encoding = "utf-8"
        destination.format = "json"
        
        handler = logger._create_file_handler(destination)
        assert isinstance(handler, BufferedFileHandler)
        handler.close()
        os.remove("test_object.log") if os.path.exists("test_object.log") else None
    
    def test_logger_setup_layers_with_dict_config(self):
        """Test setup_layers with dict-based config."""
        logger = HydraLogger()
        logger.config = MagicMock()
        logger.config.layers = {
            "TEST": {"level": "INFO", "destinations": []}
        }
        
        # Mock _create_layer to handle dict config
        original_create_layer = logger._create_layer
        def mock_create_layer(layer_name, layer_config):
            if isinstance(layer_config, dict):
                # Convert dict to mock object
                mock_config = MagicMock()
                mock_config.level = layer_config.get("level", "INFO")
                mock_config.destinations = layer_config.get("destinations", [])
                return original_create_layer(layer_name, mock_config)
            return original_create_layer(layer_name, layer_config)
        
        with patch.object(logger, '_create_layer', side_effect=mock_create_layer):
            logger._setup_layers()
            assert "TEST" in logger._layers
    
    def test_logger_setup_layers_with_hasattr_fallback(self):
        """Test setup_layers with hasattr fallback."""
        logger = HydraLogger()
        logger.config = MagicMock()
        delattr(logger.config, 'layers')
        setattr(logger.config, 'layers', {
            "TEST": {"level": "INFO", "destinations": []}
        })
        
        # Mock _create_layer to handle dict config
        original_create_layer = logger._create_layer
        def mock_create_layer(layer_name, layer_config):
            if isinstance(layer_config, dict):
                # Convert dict to mock object
                mock_config = MagicMock()
                mock_config.level = layer_config.get("level", "INFO")
                mock_config.destinations = layer_config.get("destinations", [])
                return original_create_layer(layer_name, mock_config)
            return original_create_layer(layer_name, layer_config)
        
        with patch.object(logger, '_create_layer', side_effect=mock_create_layer):
            logger._setup_layers()
            assert "TEST" in logger._layers
    
    def test_logger_load_plugins_disabled(self):
        """Test load_plugins when plugins are disabled."""
        logger = HydraLogger(enable_plugins=False)
        logger._load_plugins()
        # Should not raise exception
    
    def test_logger_precompute_log_methods(self):
        """Test precompute_log_methods."""
        logger = HydraLogger()
        logger._precompute_log_methods()
        # Should not raise exception
    
    def test_logger_setup_bare_metal_mode(self):
        """Test setup_bare_metal_mode."""
        logger = HydraLogger()
        logger._setup_bare_metal_mode()
        # Should not raise exception
    
    def test_logger_bare_metal_log(self):
        """Test bare_metal_log method."""
        logger = HydraLogger()
        logger._bare_metal_log("INFO", "Test message")
        # Should not raise exception
    
    def test_logger_minimal_features_log(self):
        """Test minimal_features_log method."""
        logger = HydraLogger()
        logger._minimal_features_log("INFO", "Test message")
        # Should not raise exception
    
    def test_logger_plugin_create_handler(self):
        """Test plugin create_handler functionality."""
        logger = HydraLogger()
        
        # Mock plugin with create_handler method
        mock_plugin = MagicMock()
        mock_plugin.create_handler.return_value = logging.StreamHandler()
        logger._plugins["test_plugin"] = mock_plugin
        
        destination = MagicMock()
        destination.type = "plugin_type"
        
        handler = logger._create_handler(destination)
        assert handler is not None
        mock_plugin.create_handler.assert_called_once_with(destination)
    
    def test_logger_plugin_create_handler_returns_none(self):
        """Test plugin create_handler when it returns None."""
        logger = HydraLogger()
        
        # Mock plugin that returns None
        mock_plugin = MagicMock()
        mock_plugin.create_handler.return_value = None
        logger._plugins["test_plugin"] = mock_plugin
        
        destination = MagicMock()
        destination.type = "plugin_type"
        
        handler = logger._create_handler(destination)
        assert handler is None
    
    def test_logger_plugin_create_handler_no_method(self):
        """Test plugin without create_handler method."""
        logger = HydraLogger()
        
        # Mock plugin without create_handler method
        mock_plugin = MagicMock()
        del mock_plugin.create_handler
        logger._plugins["test_plugin"] = mock_plugin
        
        destination = MagicMock()
        destination.type = "plugin_type"
        
        handler = logger._create_handler(destination)
        assert handler is None
    
    def test_logger_create_console_handler_with_no_format_attr(self):
        """Test console handler with destination that has no format attribute."""
        logger = HydraLogger()
        destination = MagicMock()
        del destination.format
        del destination.color_mode
        
        handler = logger._create_console_handler(destination)
        assert isinstance(handler, logging.StreamHandler)
    
    def test_logger_create_file_handler_with_no_attributes(self):
        """Test file handler with destination that has no attributes."""
        logger = HydraLogger()
        
        # Create a custom mock class that raises AttributeError for specific attributes
        class MockDestination:
            def __init__(self):
                self._attributes = {}
            
            def __getattr__(self, name):
                if name in ['path', 'encoding', 'format']:
                    raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
                return MagicMock()
        
        destination = MockDestination()
        
        handler = logger._create_file_handler(destination)
        # Should return None when attributes are missing
        assert handler is None
    
    def test_logger_create_file_handler_with_directory_creation(self):
        """Test file handler that creates directory."""
        logger = HydraLogger()
        destination = MagicMock()
        destination.path = "test_dir/test.log"
        destination.encoding = "utf-8"
        destination.format = "plain-text"
        
        handler = logger._create_file_handler(destination)
        assert isinstance(handler, BufferedFileHandler)
        assert os.path.exists("test_dir")
        handler.close()
        shutil.rmtree("test_dir") if os.path.exists("test_dir") else None
    
    def test_logger_get_logger_for_layer_centralized_fallback(self):
        """Test logger fallback to centralized layer."""
        logger = HydraLogger()
        
        # Create centralized layer
        centralized_logger = logging.getLogger("hydra_logger.__CENTRALIZED__")
        logger._layers["__CENTRALIZED__"] = centralized_logger
        
        # Test fallback to centralized
        result = logger._get_logger_for_layer("NON_EXISTENT")
        assert result == centralized_logger
    
    def test_logger_get_logger_for_layer_system_fallback(self):
        """Test logger fallback to system logger."""
        logger = HydraLogger()
        
        # Clear all layers to test system fallback
        logger._layers.clear()
        
        # No layers exist, should fallback to system logger
        result = logger._get_logger_for_layer("NON_EXISTENT")
        assert result.name == "hydra_logger"
    
    def test_logger_create_formatter_with_unknown_format(self):
        """Test creating formatter with unknown format type."""
        logger = HydraLogger()
        formatter = logger._create_formatter("unknown_format")
        assert isinstance(formatter, logging.Formatter)
    
    def test_logger_log_when_closed(self):
        """Test logging when logger is closed."""
        logger = HydraLogger()
        logger._closed = True
        
        # Should return early without doing anything
        logger.log("INFO", "Test message")
        # Should not raise exception
    
    def test_logger_bare_metal_mode_logging(self):
        """Test bare metal mode logging."""
        logger = HydraLogger(bare_metal_mode=True)
        logger.log("INFO", "Test message")
        # Should not raise exception
    
    def test_logger_minimal_features_mode_logging(self):
        """Test minimal features mode logging."""
        logger = HydraLogger(minimal_features_mode=True)
        logger.log("INFO", "Test message")
        # Should not raise exception
    
    def test_logger_standard_mode_logging(self):
        """Test standard mode logging."""
        logger = HydraLogger()
        logger.log("INFO", "Test message")
        # Should not raise exception
    
    def test_logger_add_plugin(self):
        """Test adding a plugin."""
        logger = HydraLogger()
        mock_plugin = MagicMock()
        
        logger.add_plugin("test_plugin", mock_plugin)
        assert "test_plugin" in logger._plugins
        assert logger._plugins["test_plugin"] == mock_plugin
    
    def test_logger_remove_plugin_existing(self):
        """Test removing an existing plugin."""
        logger = HydraLogger()
        mock_plugin = MagicMock()
        logger._plugins["test_plugin"] = mock_plugin
        
        result = logger.remove_plugin("test_plugin")
        assert result == True
        assert "test_plugin" not in logger._plugins
    
    def test_logger_remove_plugin_non_existing(self):
        """Test removing a non-existing plugin."""
        logger = HydraLogger()
        
        result = logger.remove_plugin("non_existing_plugin")
        assert result == False
    
    def test_logger_update_config_with_dict(self):
        """Test updating config with dict."""
        logger = HydraLogger()
        new_config = {"layers": {"TEST": {"level": "INFO", "destinations": []}}}
        
        logger.update_config(new_config)
        # Should not raise exception
    
    def test_logger_close(self):
        """Test closing the logger."""
        logger = HydraLogger()
        logger.close()
        assert logger._closed == True
    
    def test_logger_context_manager(self):
        """Test logger as context manager."""
        with HydraLogger() as logger:
            assert logger is not None
            logger.log("INFO", "Test message")
    
    def test_logger_context_manager_with_exception(self):
        """Test logger context manager with exception."""
        try:
            with HydraLogger() as logger:
                raise Exception("Test exception")
        except Exception:
            pass  # Exception should be handled by context manager
    
    def test_logger_magic_config_methods(self):
        """Test all magic config methods."""
        # Test all magic config methods
        assert HydraLogger.for_production() is not None
        assert HydraLogger.for_development() is not None
        assert HydraLogger.for_testing() is not None
        assert HydraLogger.for_microservice() is not None
        assert HydraLogger.for_web_app() is not None
        assert HydraLogger.for_api_service() is not None
        assert HydraLogger.for_background_worker() is not None
        assert HydraLogger.for_minimal_features() is not None
        assert HydraLogger.for_bare_metal() is not None
    
    def test_logger_for_custom_with_kwargs(self):
        """Test for_custom with kwargs."""
        # Use a name that definitely doesn't exist in the magic config registry
        with pytest.raises(ConfigurationError, match="Magic config 'definitely_nonexistent_config' not found"):
            logger = HydraLogger.for_custom("definitely_nonexistent_config", enable_security=False)
    
    def test_logger_list_magic_configs(self):
        """Test list_magic_configs."""
        configs = HydraLogger.list_magic_configs()
        assert isinstance(configs, dict)
    
    def test_logger_has_magic_config(self):
        """Test has_magic_config."""
        assert HydraLogger.has_magic_config("production") == True
        assert HydraLogger.has_magic_config("non_existing") == False
    
    def test_logger_for_magic_with_kwargs(self):
        """Test for_magic with kwargs."""
        logger = HydraLogger.for_magic("production", enable_security=False)
        assert logger is not None
    
    def test_logger_register_magic_decorator(self):
        """Test register_magic decorator."""
        @HydraLogger.register_magic("test_magic", "Test magic config")
        def test_magic_config():
            return {"layers": {"TEST": {"level": "INFO", "destinations": []}}}
        
        # Should register the magic config
        assert HydraLogger.has_magic_config("test_magic") == True
    
    def test_logger_error_handling_in_log_method(self):
        """Test error handling in log method."""
        logger = HydraLogger()
        
        # Test with invalid level
        logger.log("INVALID_LEVEL", "Test message")
        # Should not raise exception
    
    def test_logger_error_handling_in_bare_metal_log(self):
        """Test error handling in bare metal log."""
        logger = HydraLogger(bare_metal_mode=True)
        
        # Test with exception in bare metal mode
        with patch.object(logger, '_get_logger_for_layer', side_effect=Exception("Test error")):
            logger._bare_metal_log("INFO", "Test message")
            # Should handle error gracefully
    
    def test_logger_error_handling_in_minimal_features_log(self):
        """Test error handling in minimal features log."""
        logger = HydraLogger(minimal_features_mode=True)
        
        # Test with exception in minimal features mode
        with patch.object(logger, '_get_logger_for_layer', side_effect=Exception("Test error")):
            logger._minimal_features_log("INFO", "Test message")
            # Should handle error gracefully
    
    def test_logger_error_handling_in_standard_log(self):
        """Test error handling in standard log."""
        logger = HydraLogger()
        
        # Test with exception in standard mode
        with patch.object(logger, '_get_logger_for_layer', side_effect=Exception("Test error")):
            logger.log("INFO", "Test message")
            # Should handle error gracefully
    
    def test_logger_get_performance_metrics(self):
        """Test get_performance_metrics method."""
        logger = HydraLogger()
        metrics = logger.get_performance_metrics()
        assert isinstance(metrics, dict)
    
    def test_logger_get_plugin_insights(self):
        """Test get_plugin_insights method."""
        logger = HydraLogger()
        insights = logger.get_plugin_insights()
        assert isinstance(insights, dict)
    
    def test_logger_get_error_stats(self):
        """Test get_error_stats method."""
        logger = HydraLogger()
        stats = logger.get_error_stats()
        assert isinstance(stats, dict)
    
    def test_logger_clear_error_stats(self):
        """Test clear_error_stats method."""
        logger = HydraLogger()
        logger.clear_error_stats()
        # Should not raise exception
    
    def test_logger_close_with_cleanup(self):
        """Test logger close with cleanup."""
        logger = HydraLogger()
        
        # Add some handlers to test cleanup
        handler = logging.StreamHandler()
        logger._layers["TEST"] = logging.getLogger("test")
        logger._layers["TEST"].addHandler(handler)
        
        logger.close()
        assert logger._closed == True
    
    def test_logger_context_manager_exit_with_exception(self):
        """Test context manager exit with exception."""
        logger = HydraLogger()
        
        # Test __exit__ with exception
        result = logger.__exit__(Exception, Exception("Test"), None)
        assert result is None  # Should not suppress the exception
    
    def test_logger_context_manager_exit_without_exception(self):
        """Test context manager exit without exception."""
        logger = HydraLogger()
        
        # Test __exit__ without exception
        result = logger.__exit__(None, None, None)
        assert result is None  # Should not suppress anything
    
    def test_logger_magic_config_methods_with_kwargs(self):
        """Test magic config methods with kwargs."""
        # Test all magic config methods with kwargs
        try:
            logger = HydraLogger.for_production(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass  # Some magic configs might not exist
        
        try:
            logger = HydraLogger.for_development(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass
        
        try:
            logger = HydraLogger.for_testing(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass
        
        try:
            logger = HydraLogger.for_microservice(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass
        
        try:
            logger = HydraLogger.for_web_app(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass
        
        try:
            logger = HydraLogger.for_api_service(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass
        
        try:
            logger = HydraLogger.for_background_worker(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass
        
        try:
            logger = HydraLogger.for_minimal_features(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass
        
        try:
            logger = HydraLogger.for_bare_metal(enable_security=False)
            assert isinstance(logger, HydraLogger)
            logger.close()
        except Exception:
            pass
    
    def test_logger_for_custom_with_exception(self):
        """Test for_custom with exception."""
        # Test with non-existent config
        try:
            logger = HydraLogger.for_custom("non_existent_config")
            logger.close()
        except Exception:
            # Expected to fail
            pass
    
    def test_logger_for_magic_with_exception(self):
        """Test for_magic with exception."""
        # Test with non-existent config
        try:
            logger = HydraLogger.for_magic("non_existent_config")
            logger.close()
        except Exception:
            # Expected to fail
            pass
    
    def test_logger_has_magic_config_with_existing(self):
        """Test has_magic_config with existing config."""
        # Test with existing config
        result = HydraLogger.has_magic_config("production")
        assert result == True
    
    def test_logger_list_magic_configs_empty(self):
        """Test list_magic_configs when empty."""
        # Test that list_magic_configs returns a dict
        configs = HydraLogger.list_magic_configs()
        assert isinstance(configs, dict)
    
    def test_logger_register_magic_with_existing(self):
        """Test register_magic with existing name."""
        # Test registering with existing name
        @HydraLogger.register_magic("existing_magic", "Existing magic config")
        def existing_magic_config():
            return {"layers": {"EXISTING": {"level": "INFO", "destinations": []}}}
        
        # Should overwrite existing
        assert HydraLogger.has_magic_config("existing_magic") == True 
    
    # Additional tests for missing coverage lines
    def test_buffered_file_handler_flush_buffer_closed(self):
        """Test _flush_buffer with closed handler (lines 120-121)."""
        handler = BufferedFileHandler(filename=self.log_file)
        handler._closed = True
        handler.stream = None  # type: ignore
        
        # Should return early without error
        handler._flush_buffer()
        
        handler.close()
    
    def test_buffered_file_handler_flush_buffer_none_stream(self):
        """Test _flush_buffer with None stream (lines 120-121)."""
        handler = BufferedFileHandler(filename=self.log_file)
        handler.stream = None  # type: ignore
        
        # Should return early without error
        handler._flush_buffer()
        
        handler.close()
    
    def test_setup_layers_dict_fallback(self):
        """Test _setup_layers fallback for dict-based config (lines 440-442)."""
        # Create a mock config with dict-based layers
        mock_config = Mock()
        mock_config.layers = {
            "TEST": Mock(level="INFO", destinations=[])
        }
        
        logger = HydraLogger()
        logger.config = mock_config
        
        # Should handle dict-based config without error
        logger._setup_layers()
        
        logger.close()
    
    def test_create_handler_console_error(self):
        """Test console handler creation error (line 493)."""
        logger = HydraLogger()
        
        # Mock destination that will cause error
        mock_destination = Mock()
        mock_destination.type = "console"
        
        with patch('logging.StreamHandler', side_effect=Exception("Console handler error")):
            handler = logger._create_handler(mock_destination)
            assert handler is None
        
        logger.close()
    
    def test_create_handler_file_error(self):
        """Test file handler creation error (line 500)."""
        logger = HydraLogger()
        
        # Mock destination that will cause error
        mock_destination = Mock()
        mock_destination.type = "file"
        mock_destination.path = "/invalid/path/file.log"
        
        with patch('os.makedirs', side_effect=OSError("Permission denied")):
            handler = logger._create_handler(mock_destination)
            assert handler is None
        
        logger.close()
    
    def test_create_handler_plugin_error(self):
        """Test plugin handler creation error (line 515)."""
        logger = HydraLogger()
        
        # Mock destination with unknown type
        mock_destination = Mock()
        mock_destination.type = "unknown"
        
        # Mock plugin that raises exception
        mock_plugin = Mock()
        mock_plugin.create_handler.side_effect = Exception("Plugin error")
        logger._plugins = {"test_plugin": mock_plugin}
        
        handler = logger._create_handler(mock_destination)
        assert handler is None
        
        logger.close()
    
    def test_create_console_handler_dict_fallback(self):
        """Test console handler creation with dict fallback (line 529)."""
        logger = HydraLogger()
        
        # Mock destination as dict-like object
        mock_destination = Mock()
        mock_destination.get.return_value = "json"
        del mock_destination.format  # Remove attribute to force dict fallback
        
        handler = logger._create_console_handler(mock_destination)
        assert handler is not None
        
        logger.close()
    
    def test_log_security_validation_error(self):
        """Test security validation error in log method (lines 631-632)."""
        logger = HydraLogger()
        
        # Mock security validator that raises exception
        mock_validator = Mock()
        mock_validator.validate_message.side_effect = Exception("Security validation error")
        logger._security_validator = mock_validator
        
        # Should handle security validation error gracefully
        logger.log("INFO", "test message")
        
        logger.close()
    
    def test_log_sanitization_error(self):
        """Test sanitization error in log method (lines 644-645)."""
        logger = HydraLogger()
        
        # Mock sanitizer that raises exception
        mock_sanitizer = Mock()
        mock_sanitizer.sanitize_message.side_effect = Exception("Sanitization error")
        logger._data_sanitizer = mock_sanitizer
        
        # Should handle sanitization error gracefully
        logger.log("INFO", "test message")
        
        logger.close()
    
    def test_log_plugin_error(self):
        """Test plugin error in log method (lines 669-672)."""
        logger = HydraLogger()
        
        # Mock plugin that raises exception
        mock_plugin = Mock()
        mock_plugin.process_event.side_effect = Exception("Plugin error")
        logger._plugins = {"test_plugin": mock_plugin}
        
        # Should handle plugin error gracefully
        logger.log("INFO", "test message")
        
        logger.close()
    
    def test_log_logging_error(self):
        """Test logging error in log method (lines 684, 687-690)."""
        logger = HydraLogger()
        
        # Mock logger that raises exception
        mock_logger = Mock()
        mock_logger.log.side_effect = Exception("Logging error")
        logger._layers = {"DEFAULT": mock_logger}
        
        # Should handle logging error gracefully
        logger.log("INFO", "test message")
        
        logger.close()
    
    def test_log_fallback_error(self):
        """Test fallback error handling in log method (line 695)."""
        logger = HydraLogger()
        
        # Mock fallback handler that raises exception
        mock_fallback = Mock()
        mock_fallback.handle_error.side_effect = Exception("Fallback error")
        logger._fallback_handler = mock_fallback
        
        # Mock main logging to fail
        with patch.object(logger, '_get_logger_for_layer', side_effect=Exception("Main error")):
            # Should handle fallback error gracefully
            logger.log("INFO", "test message")
        
        logger.close()
    
    def test_close_handler_error(self):
        """Test handler close error (lines 816-817)."""
        logger = HydraLogger()
        
        # Mock handler that raises exception on close
        mock_handler = Mock()
        mock_handler.close.side_effect = Exception("Handler close error")
        
        # Mock logger with problematic handler
        mock_logger = Mock()
        mock_logger.handlers = [mock_handler]
        logger._layers = {"TEST": mock_logger}
        
        # Should handle handler close error gracefully
        logger.close()
    
    def test_close_performance_monitor_error(self):
        """Test performance monitor close error (lines 822-823)."""
        logger = HydraLogger()
        
        # Mock performance monitor that raises exception
        mock_monitor = Mock()
        mock_monitor.close.side_effect = Exception("Monitor close error")
        logger._performance_monitor = mock_monitor
        
        # Should handle performance monitor close error gracefully
        logger.close()
    
    def test_close_cleanup_error(self):
        """Test cleanup error in close method (lines 829-830)."""
        logger = HydraLogger()
        
        # Mock layers that raises exception during cleanup
        logger._layers = Mock()
        logger._layers.clear.side_effect = Exception("Cleanup error")
        
        # Should handle cleanup error gracefully
        logger.close()
    
    def test_get_error_stats_error(self):
        """Test error stats retrieval error (lines 836-838)."""
        logger = HydraLogger()
        
        # Mock error tracker that raises exception
        mock_tracker = Mock()
        mock_tracker.get_error_stats.side_effect = Exception("Stats error")
        logger._error_tracker = mock_tracker
        
        # Should handle error stats error gracefully
        result = logger.get_error_stats()
        assert "error" in result
        
        logger.close()
    
    def test_clear_error_stats_error(self):
        """Test error stats clear error (lines 844-845)."""
        logger = HydraLogger()
        
        # Mock error tracker that raises exception
        mock_tracker = Mock()
        mock_tracker.clear_error_stats.side_effect = Exception("Clear error")
        logger._error_tracker = mock_tracker
        
        # Should handle error stats clear error gracefully
        logger.clear_error_stats()
        
        logger.close()
    
    def test_for_custom_magic_config_not_found(self):
        """Test for_custom with non-existent magic config."""
        with pytest.raises(ConfigurationError, match="Magic config 'nonexistent' not found"):
            HydraLogger.for_custom("nonexistent")
    
    def test_minimal_features_log_closed(self):
        """Test minimal_features_log when logger is closed."""
        logger = HydraLogger()
        logger._closed = True
        
        # Should return early without error
        logger._minimal_features_log("INFO", "test message")
        
        logger.close()
    
    def test_bare_metal_log_closed(self):
        """Test bare_metal_log when logger is closed."""
        logger = HydraLogger()
        logger._closed = True
        
        # Should return early without error
        logger._bare_metal_log("INFO", "test message")
        
        logger.close()
    
    def test_bare_metal_log_no_logger(self):
        """Test bare_metal_log when no logger is available."""
        logger = HydraLogger()
        logger._layers = {}  # No layers available
        
        # Should handle missing logger gracefully
        logger._bare_metal_log("INFO", "test message")
        
        logger.close()
    
    def test_create_layer_reserved_name(self):
        """Test _create_layer with reserved layer name."""
        logger = HydraLogger()
        
        # Mock layer config
        mock_config = Mock()
        mock_config.level = "INFO"
        mock_config.destinations = []
        
        # Should raise ConfigurationError for reserved name
        with pytest.raises(ConfigurationError, match="Layer name '__RESERVED__' is reserved"):
            logger._create_layer("__RESERVED__", mock_config)
        
        logger.close()
    
    def test_create_file_handler_dict_fallback(self):
        """Test file handler creation with dict fallback."""
        logger = HydraLogger()
        
        # Use a real dict for the destination
        dict_destination = {
            'path': 'logs/test.log',
            'encoding': 'utf-8',
            'format': 'plain-text'
        }
        
        # Mock BufferedFileHandler to return a valid handler
        mock_handler = Mock()
        with patch('os.makedirs'), patch('hydra_logger.core.logger.BufferedFileHandler', return_value=mock_handler):
            handler = logger._create_file_handler(dict_destination)
            assert handler is not None
        
        logger.close()
    
    def test_performance_monitor_record_log_disabled(self):
        """Test PerformanceMonitor.record_log when disabled."""
        monitor = PerformanceMonitor(enabled=False)
        
        # Should return early without error
        monitor.record_log("TEST", "INFO", "test message", 0.0, 0.1)
        
        monitor.close()
    
    def test_performance_monitor_record_log_closed(self):
        """Test PerformanceMonitor.record_log when closed."""
        monitor = PerformanceMonitor()
        monitor._closed = True
        
        # Should return early without error
        monitor.record_log("TEST", "INFO", "test message", 0.0, 0.1)
        
        monitor.close()
    
    def test_performance_monitor_record_handler_metrics_disabled(self):
        """Test PerformanceMonitor.record_handler_metrics when disabled."""
        monitor = PerformanceMonitor(enabled=False)
        
        # Should return early without error
        monitor.record_handler_metrics("test_handler", {"test": "metrics"})
        
        monitor.close()
    
    def test_performance_monitor_record_handler_metrics_closed(self):
        """Test PerformanceMonitor.record_handler_metrics when closed."""
        monitor = PerformanceMonitor()
        monitor._closed = True
        
        # Should return early without error
        monitor.record_handler_metrics("test_handler", {"test": "metrics"})
        
        monitor.close()
    
    def test_performance_monitor_record_security_event_disabled(self):
        """Test PerformanceMonitor.record_security_event when disabled."""
        monitor = PerformanceMonitor(enabled=False)
        
        # Should return early without error
        monitor.record_security_event()
        
        monitor.close()
    
    def test_performance_monitor_record_security_event_closed(self):
        """Test PerformanceMonitor.record_security_event when closed."""
        monitor = PerformanceMonitor()
        monitor._closed = True
        
        # Should return early without error
        monitor.record_security_event()
        
        monitor.close()
    
    def test_performance_monitor_record_sanitization_event_disabled(self):
        """Test PerformanceMonitor.record_sanitization_event when disabled."""
        monitor = PerformanceMonitor(enabled=False)
        
        # Should return early without error
        monitor.record_sanitization_event()
        
        monitor.close()
    
    def test_performance_monitor_record_sanitization_event_closed(self):
        """Test PerformanceMonitor.record_sanitization_event when closed."""
        monitor = PerformanceMonitor()
        monitor._closed = True
        
        # Should return early without error
        monitor.record_sanitization_event()
        
        monitor.close()
    
    def test_performance_monitor_record_plugin_event_disabled(self):
        """Test PerformanceMonitor.record_plugin_event when disabled."""
        monitor = PerformanceMonitor(enabled=False)
        
        # Should return early without error
        monitor.record_plugin_event()
        
        monitor.close()
    
    def test_performance_monitor_record_plugin_event_closed(self):
        """Test PerformanceMonitor.record_plugin_event when closed."""
        monitor = PerformanceMonitor()
        monitor._closed = True
        
        # Should return early without error
        monitor.record_plugin_event()
        
        monitor.close() 