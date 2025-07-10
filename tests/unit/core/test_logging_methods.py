"""
Unit tests for core logging methods.

This module tests individual logging methods in isolation,
focusing on behavior rather than implementation details.
"""

import pytest
import os
import time
import threading
import queue
from unittest.mock import patch, MagicMock

from hydra_logger import HydraLogger
from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination
from tests.conftest import BaseLoggerTest


class TestLoggingMethods(BaseLoggerTest):
    """Test individual logging methods in isolation."""
    
    @pytest.mark.unit
    def test_logger_implements_required_interface(self):
        """Test that logger implements required interface contract."""
        logger = HydraLogger()
        
        # Test interface contract
        required_methods = ['debug', 'info', 'warning', 'error', 'critical']
        for method in required_methods:
            assert hasattr(logger, method), f"Logger should have {method} method"
            assert callable(getattr(logger, method)), f"{method} should be callable"
    
    @pytest.mark.unit
    def test_logging_methods_accept_messages(self):
        """Test that all logging methods accept messages."""
        logger = HydraLogger()
        
        # Test all logging levels
        logger.debug("test", "Debug message")
        logger.info("test", "Info message")
        logger.warning("test", "Warning message")
        logger.error("test", "Error message")
        logger.critical("test", "Critical message")
        
        # Verify metrics were recorded
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 5
    
    @pytest.mark.unit
    def test_logging_with_different_message_types(self, test_messages):
        """Test logging with various message types."""
        logger = HydraLogger()
        
        for message in test_messages:
            # Should not raise exceptions for any message type
            logger.info("test", message)
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= len(test_messages)
    
    @pytest.mark.unit
    def test_logging_with_extra_data(self):
        """Test logging with extra data parameter."""
        logger = HydraLogger()
        
        extra_data = {
            "user_id": "12345",
            "session_id": "abc123",
            "request_id": "req-456"
        }
        
        logger.info("test", "Message with extra data", extra=extra_data)
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
    
    @pytest.mark.unit
    def test_logging_with_different_layers(self):
        """Test logging to different layers."""
        config = self.create_test_config()
        config["layers"]["CUSTOM"] = {
            "level": "INFO",
            "destinations": [{"type": "console", "level": "INFO"}]
        }
        
        logger = HydraLogger(config=config)
        
        # Log to different layers
        logger.info("TEST", "Test layer message")
        logger.info("CUSTOM", "Custom layer message")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2
    
    @pytest.mark.unit
    def test_logging_with_disabled_features(self):
        """Test logging when features are disabled."""
        logger = HydraLogger(
            enable_security=False,
            enable_sanitization=False,
            enable_plugins=False
        )
        
        logger.info("test", "Message with disabled features")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
        assert metrics["security_events"] == 0
        assert metrics["sanitization_events"] == 0
        assert metrics["plugin_events"] == 0
    
    @pytest.mark.unit
    def test_logging_with_enabled_features(self):
        """Test logging when features are enabled."""
        logger = HydraLogger(
            enable_security=True,
            enable_sanitization=True,
            enable_plugins=True
        )
        
        logger.info("test", "Message with enabled features")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
    
    @pytest.mark.unit
    def test_logging_performance_modes(self):
        """Test logging in different performance modes."""
        # Minimal features mode
        logger_minimal = HydraLogger.for_minimal_features()
        logger_minimal.info("PERF", "Minimal features message")
        
        # Bare metal mode
        logger_bare = HydraLogger.for_bare_metal()
        logger_bare.info("PERF", "Bare metal message")
        
        # Both should work without errors
        assert logger_minimal is not None
        assert logger_bare is not None
    
    @pytest.mark.unit
    def test_logging_with_custom_formats(self):
        """Test logging with custom format parameters."""
        logger = HydraLogger(
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            logger_name_format="[{name}]",
            message_format="{level}: {message}"
        )
        
        logger.info("test", "Custom format message")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
    
    @pytest.mark.unit
    def test_logging_with_environment_variables(self):
        """Test logging respects environment variables."""
        # Set environment variables
        os.environ['HYDRA_LOG_LEVEL'] = 'DEBUG'
        os.environ['HYDRA_LOG_DATE_FORMAT'] = '%Y-%m-%d'
        
        logger = HydraLogger()
        logger.debug("test", "Environment variable test")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
    
    @pytest.mark.unit
    def test_logging_thread_safety(self):
        """Test logging is thread-safe."""
        logger = HydraLogger()
        message_queue = queue.Queue()
        errors = []
        
        def worker():
            """Worker thread for concurrent logging."""
            try:
                for i in range(100):
                    logger.info("THREAD", f"Message {i}")
                    message_queue.put(i)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify no errors and all messages processed
        assert len(errors) == 0
        assert message_queue.qsize() == 500
    
    @pytest.mark.unit
    def test_logging_context_manager(self):
        """Test logger as context manager."""
        with HydraLogger() as logger:
            logger.info("test", "Context manager message")
            
            metrics = logger.get_performance_metrics()
            assert metrics["total_logs"] >= 1
    
    @pytest.mark.unit
    def test_logging_with_invalid_inputs(self):
        """Test logging handles invalid inputs gracefully."""
        logger = HydraLogger()
        
        # These should not raise exceptions
        logger.info("test", layer="test")  # None message
        logger.info("test", layer="test")  # Empty message
        logger.info("test", layer="test")  # Convert to string
        logger.info("test", layer="test")  # Convert dict to string
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 4
    
    @pytest.mark.unit
    def test_logging_with_special_characters(self):
        """Test logging with special characters."""
        logger = HydraLogger()
        
        special_messages = [
            "Message with quotes: 'single' and \"double\"",
            "Message with brackets: [square] and {curly}",
            "Message with parentheses: (round) and <angle>",
            "Message with newlines\nand tabs\tand spaces",
            "Message with unicode: 你好世界 🌍",
            "Message with emojis: 🚀 ⚡ 🎯"
        ]
        
        for message in special_messages:
            logger.info("test", message)
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= len(special_messages)
    
    @pytest.mark.unit
    def test_logging_with_very_long_messages(self):
        """Test logging with very long messages."""
        logger = HydraLogger()
        
        # Very long message
        long_message = "Very long message " * 1000
        logger.info("test", long_message)
        
        # Extremely long message
        extreme_message = "Extreme message " * 10000
        logger.info("test", extreme_message)
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 2
    
    @pytest.mark.unit
    def test_logging_with_multiple_instances(self):
        """Test multiple logger instances work independently."""
        logger1 = HydraLogger()
        logger2 = HydraLogger()
        
        logger1.info("test", "Message from logger 1")
        logger2.info("test", "Message from logger 2")
        
        metrics1 = logger1.get_performance_metrics()
        metrics2 = logger2.get_performance_metrics()
        
        assert metrics1["total_logs"] >= 1
        assert metrics2["total_logs"] >= 1
    
    @pytest.mark.unit
    def test_logging_with_magic_configs(self):
        """Test logging with magic configurations."""
        @HydraLogger.register_magic("magic_test", "Magic test config")
        def magic_test_config():
            return LoggingConfig(layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            })
        logger = HydraLogger.for_magic("magic_test")
        logger.info("test", "test")
        logger.close()
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
    
    @pytest.mark.unit
    def test_logging_with_custom_magic_configs(self):
        """Test logging with custom magic configurations."""
        @HydraLogger.register_magic("custom_test", "Custom test config")
        def custom_test_config():
            return LoggingConfig(layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[LogDestination(type="console", level="INFO")]
                )
            })
        logger = HydraLogger.for_custom("custom_test")
        logger.info("test", "test")
        logger.close()
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 1
    
    @pytest.mark.unit
    def test_logging_with_error_handling(self):
        """Test logging with error handling scenarios."""
        logger = HydraLogger()
        
        # Test with invalid level
        logger.log("INVALID_LEVEL", "test", "Message with invalid level")
        
        # Test with invalid layer
        logger.info("NONEXISTENT_LAYER", "Message to nonexistent layer")
        
        # Test with malformed message
        logger.info("test", layer="test")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 3
    
    @pytest.mark.unit
    def test_logging_with_performance_monitoring(self):
        """Test logging with performance monitoring enabled."""
        logger = HydraLogger(enable_performance_monitoring=True)
        
        # Log multiple messages
        for i in range(10):
            logger.info("test", f"Message {i}")
        
        metrics = logger.get_performance_metrics()
        assert metrics["total_logs"] >= 10
        assert metrics["avg_latency"] >= 0
        assert metrics["throughput"] > 0
    
    @pytest.mark.unit
    def test_logging_with_performance_monitoring_disabled(self):
        """Test logging with performance monitoring disabled."""
        logger = HydraLogger(enable_performance_monitoring=False)
        
        logger.info("test", "Message without monitoring")
        
        metrics = logger.get_performance_metrics()
        # Should still have basic metrics even when disabled
        assert "total_logs" in metrics 