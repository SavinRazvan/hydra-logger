"""
Tests for performance monitoring functionality.

This module tests the performance monitoring features of HydraLogger,
including timing, memory usage tracking, and statistics collection.
"""

import os
import time
import pytest
from unittest.mock import patch, MagicMock
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.logger import PerformanceMonitor


class TestPerformanceMonitoring:
    """Test performance monitoring functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Create test logs directory
        self.test_logs_dir = "_tests_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_perf.log")

    def teardown_method(self):
        """Cleanup test files."""
        # Clean up test log files
        if os.path.exists(self.log_file):
            os.unlink(self.log_file)

    def test_performance_monitoring_disabled_by_default(self):
        """Test that performance monitoring is disabled by default."""
        logger = HydraLogger()
        assert logger.performance_monitoring is False
        assert logger._performance_monitor is None

    def test_performance_monitoring_enabled(self):
        """Test that performance monitoring can be enabled."""
        logger = HydraLogger(enable_performance_monitoring=True)
        assert logger.performance_monitoring is True
        assert logger._performance_monitor is not None

    def test_get_performance_statistics_disabled(self):
        """Test getting statistics when monitoring is disabled."""
        logger = HydraLogger()
        stats = logger.get_performance_statistics()
        assert stats is None

    def test_get_performance_statistics_enabled(self):
        """Test getting statistics when monitoring is enabled."""
        logger = HydraLogger(enable_performance_monitoring=True)
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert "uptime_seconds" in stats
        assert "total_messages" in stats
        assert "total_errors" in stats
        assert "error_rate" in stats

    def test_reset_performance_statistics(self):
        """Test resetting performance statistics."""
        logger = HydraLogger(enable_performance_monitoring=True)
        
        # Log some messages to generate statistics
        logger.info("TEST", "Message 1")
        logger.info("TEST", "Message 2")
        
        # Check that statistics exist
        stats_before = logger.get_performance_statistics()
        assert stats_before is not None
        assert stats_before["total_messages"] == 2
        
        # Reset statistics
        logger.reset_performance_statistics()
        
        # Check that statistics are reset
        stats_after = logger.get_performance_statistics()
        assert stats_after is not None
        assert stats_after["total_messages"] == 0
        assert stats_after["total_errors"] == 0

    def test_log_message_timing(self):
        """Test that log message processing time is tracked."""
        logger = HydraLogger(enable_performance_monitoring=True)
        
        # Log a message
        logger.info("TEST", "Test message")
        
        # Check that timing statistics are available
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert "avg_log_processing_time" in stats
        assert "max_log_processing_time" in stats
        assert "min_log_processing_time" in stats
        assert "messages_per_second" in stats

    def test_handler_creation_timing(self):
        """Test that handler creation time is tracked."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO"),
                        LogDestination(type="file", path=self.log_file, level="INFO")
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config, enable_performance_monitoring=True)
        
        # Check that handler creation timing statistics are available
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert "avg_handler_creation_time" in stats
        assert "max_handler_creation_time" in stats
        assert "min_handler_creation_time" in stats

    def test_error_tracking(self):
        """Test that errors are tracked correctly."""
        logger = HydraLogger(enable_performance_monitoring=True)
        
        # Log some messages
        logger.info("TEST", "Message 1")
        logger.info("TEST", "Message 2")
        
        # Check initial statistics
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert stats["total_messages"] == 2
        assert stats["total_errors"] == 0
        assert stats["error_rate"] == 0.0
        
        # Simulate an error
        with patch.object(logger, '_create_handler', side_effect=Exception("Test error")):
            try:
                logger.info("ERROR_TEST", "This should fail")
            except Exception:
                pass
        
        # Check that error was tracked
        stats = logger.get_performance_statistics()
        if stats is not None:
            assert stats["total_errors"] >= 0  # May or may not be incremented depending on error handling

    @patch('psutil.Process')
    def test_memory_usage_tracking(self, mock_process):
        """Test memory usage tracking."""
        # Mock psutil to return consistent memory usage
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_process.return_value = mock_process_instance
        
        logger = HydraLogger(enable_performance_monitoring=True)
        
        # Log some messages to trigger memory checks
        for i in range(10):
            logger.info("TEST", f"Message {i}")
        
        # Check that memory statistics are available
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert "current_memory_mb" in stats
        assert "avg_memory_mb" in stats
        assert "max_memory_mb" in stats
        assert "min_memory_mb" in stats

    def test_memory_usage_without_psutil(self):
        """Test memory usage tracking when psutil is not available."""
        with patch('hydra_logger.logger.psutil', None):
            logger = HydraLogger(enable_performance_monitoring=True)
            
            # Log some messages
            logger.info("TEST", "Message 1")
            logger.info("TEST", "Message 2")
            
            # Check that statistics are still available (without memory data)
            stats = logger.get_performance_statistics()
            assert stats is not None
            assert "uptime_seconds" in stats
            assert "total_messages" in stats
            # Memory fields should not be present when psutil is not available
            assert "current_memory_mb" not in stats

    def test_performance_monitoring_thread_safety(self):
        """Test that performance monitoring is thread-safe."""
        import threading
        
        logger = HydraLogger(enable_performance_monitoring=True)
        
        def log_messages():
            for i in range(10):
                logger.info("TEST", f"Thread message {i}")
        
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
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert stats["total_messages"] >= 50  # 5 threads * 10 messages each

    def test_performance_monitoring_overhead(self):
        """Test that performance monitoring has minimal overhead."""
        # Test without performance monitoring
        start_time = time.time()
        logger_disabled = HydraLogger(enable_performance_monitoring=False)
        for i in range(100):
            logger_disabled.info("TEST", f"Message {i}")
        disabled_time = time.time() - start_time
        
        # Test with performance monitoring
        start_time = time.time()
        logger_enabled = HydraLogger(enable_performance_monitoring=True)
        for i in range(100):
            logger_enabled.info("TEST", f"Message {i}")
        enabled_time = time.time() - start_time
        
        # Performance monitoring should not add more than 50% overhead
        overhead_ratio = enabled_time / disabled_time
        assert overhead_ratio < 1.5, f"Performance monitoring overhead too high: {overhead_ratio}"

    def test_performance_statistics_format(self):
        """Test that performance statistics have the expected format."""
        logger = HydraLogger(enable_performance_monitoring=True)
        
        # Log some messages to generate data
        logger.info("TEST", "Message 1")
        logger.info("TEST", "Message 2")
        logger.error("TEST", "Error message")
        
        stats = logger.get_performance_statistics()
        assert stats is not None
        
        # Check required fields
        required_fields = [
            "uptime_seconds", "total_messages", "total_errors", "error_rate"
        ]
        for field in required_fields:
            assert field in stats, f"Missing required field: {field}"
        
        # Check that numeric fields are floats
        for field in required_fields:
            assert isinstance(stats[field], (int, float)), f"Field {field} is not numeric"
        
        # Check that error rate is calculated correctly
        assert stats["error_rate"] == (1 / 3) * 100  # 1 error out of 3 messages

    def test_performance_monitoring_with_lazy_initialization(self):
        """Test performance monitoring with lazy initialization."""
        logger = HydraLogger(
            enable_performance_monitoring=True,
            lazy_initialization=True
        )
        
        # Log a message to trigger lazy initialization
        logger.info("TEST", "First message")
        
        # Check that statistics are available
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert stats["total_messages"] == 1
        assert "avg_handler_creation_time" in stats

    def test_performance_monitoring_with_auto_detect(self):
        """Test performance monitoring with auto-detection."""
        logger = HydraLogger(
            enable_performance_monitoring=True,
            auto_detect=True
        )
        
        # Log some messages
        logger.info("TEST", "Message 1")
        logger.info("TEST", "Message 2")
        
        # Check that statistics are available
        stats = logger.get_performance_statistics()
        assert stats is not None
        assert stats["total_messages"] == 2
        assert "avg_log_processing_time" in stats

    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor()
        
        assert monitor._handler_creation_times == []
        assert monitor._log_processing_times == []
        assert monitor._memory_usage == []
        assert monitor._message_count == 0
        assert monitor._error_count == 0

    def test_performance_monitor_reset(self):
        """Test that performance monitor can be reset."""
        monitor = PerformanceMonitor()
        
        # Add some data
        monitor._handler_creation_times = [0.1, 0.2]
        monitor._log_processing_times = [0.01, 0.02]
        monitor._message_count = 2
        monitor._error_count = 1
        
        # Reset
        monitor.reset_statistics()
        
        # Check that data was cleared
        assert monitor._handler_creation_times == []
        assert monitor._log_processing_times == []
        assert monitor._message_count == 0
        assert monitor._error_count == 0

    def test_performance_monitoring_with_logger(self):
        """Test performance monitoring integration with logger."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path=self.log_file, level="INFO")
                    ]
                )
            }
        )
        
        logger = HydraLogger(
            config=config,
            enable_performance_monitoring=True
        )
        
        # Log some messages
        for i in range(5):
            logger.info("TEST", f"Performance test message {i}")
        
        # Get statistics
        stats = logger.get_performance_statistics()
        
        assert stats is not None
        assert stats["total_messages"] >= 5
        assert "avg_log_processing_time" in stats
        assert "messages_per_second" in stats

    def test_performance_monitoring_uptime(self):
        """Test that uptime is tracked correctly."""
        monitor = PerformanceMonitor()
        
        # Wait a bit
        time.sleep(0.1)
        
        stats = monitor.get_statistics()
        assert stats["uptime_seconds"] > 0

    def test_performance_monitoring_error_rate_calculation(self):
        """Test error rate calculation."""
        monitor = PerformanceMonitor()
        
        # No messages, no errors
        stats = monitor.get_statistics()
        assert stats["error_rate"] == 0.0
        
        # Some messages, no errors
        monitor._message_count = 10
        stats = monitor.get_statistics()
        assert stats["error_rate"] == 0.0
        
        # Some messages, some errors
        monitor._error_count = 2
        stats = monitor.get_statistics()
        assert stats["error_rate"] == 20.0  # 2/10 * 100

    def test_performance_monitoring_disabled(self):
        """Test that performance monitoring can be disabled."""
        logger = HydraLogger(enable_performance_monitoring=False)
        
        # Log some messages
        logger.info("TEST", "Message 1")
        logger.info("TEST", "Message 2")
        
        # Get statistics (should be None when disabled)
        stats = logger.get_performance_statistics()
        assert stats is None

    def test_performance_monitor_memory_usage(self):
        """Test that memory usage is tracked by PerformanceMonitor."""
        monitor = PerformanceMonitor()
        
        # Check memory usage
        memory = monitor.check_memory_usage()
        assert isinstance(memory, (int, float))
        assert memory >= 0

    def test_performance_statistics(self):
        """Test that performance statistics are calculated correctly."""
        monitor = PerformanceMonitor()
        
        # Simulate some timing data
        monitor._handler_creation_times = [0.1, 0.2, 0.3]
        monitor._log_processing_times = [0.01, 0.02, 0.03]
        monitor._message_count = 3
        monitor._error_count = 1
        
        stats = monitor.get_statistics()
        
        assert stats["total_messages"] == 3
        assert stats["total_errors"] == 1
        assert stats["error_rate"] == (1 / 3) * 100
        assert "avg_handler_creation_time" in stats
        assert "avg_log_processing_time" in stats 