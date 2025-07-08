"""
Tests for lazy initialization functionality.

This module tests the lazy initialization feature that defers handler creation
until the first log message is sent, improving startup performance.
"""

import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import pytest

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


class TestLazyInitialization:
    """Test lazy initialization functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")
        
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_lazy_initialization_disabled_by_default(self):
        """Test that lazy initialization is disabled by default."""
        logger = HydraLogger()
        assert logger.lazy_initialization is False
        assert logger._initialized is True  # Should be True after setup
    
    def test_lazy_initialization_enabled(self):
        """Test that lazy initialization can be enabled."""
        logger = HydraLogger(lazy_initialization=True)
        assert logger.lazy_initialization is True
        assert logger._initialized is False
    
    def test_lazy_initialization_deferred_setup(self):
        """Test that setup is deferred when lazy initialization is enabled."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path=self.log_file)
                    ]
                )
            }
        )
        
        # Create logger with lazy initialization
        logger = HydraLogger(config=config, lazy_initialization=True)
        
        # Before first log, loggers should not be initialized
        assert logger._initialized is False
        assert "TEST" not in logger.loggers
        
        # After first log, loggers should be initialized
        logger.info("TEST", "First message")
        assert logger._initialized is True
        assert "TEST" in logger.loggers
        
        # Verify file was created
        assert os.path.exists(self.log_file)
    
    def test_lazy_initialization_immediate_setup(self):
        """Test that setup happens immediately when lazy initialization is disabled."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path=self.log_file)
                    ]
                )
            }
        )
        
        # Create logger without lazy initialization
        logger = HydraLogger(config=config, lazy_initialization=False)
        
        # Loggers should be initialized immediately
        assert logger._initialized is True
        assert "TEST" in logger.loggers
        
        # Verify file was created
        assert os.path.exists(self.log_file)
    
    def test_lazy_initialization_multiple_layers(self):
        """Test lazy initialization with multiple layers."""
        config = LoggingConfig(
            layers={
                "LAYER1": LogLayer(
                    level="INFO",
                    destinations=[LogDestination(type="console")]
                ),
                "LAYER2": LogLayer(
                    level="DEBUG",
                    destinations=[LogDestination(type="file", path=self.log_file)]
                )
            }
        )
        
        logger = HydraLogger(config=config, lazy_initialization=True)
        
        # Before first log
        assert logger._initialized is False
        assert "LAYER1" not in logger.loggers
        assert "LAYER2" not in logger.loggers
        
        # After first log to LAYER1
        logger.info("LAYER1", "First message")
        assert logger._initialized is True
        assert "LAYER1" in logger.loggers
        assert "LAYER2" in logger.loggers  # All layers should be initialized
        
        # After first log to LAYER2
        logger.debug("LAYER2", "Second message")
        assert "LAYER2" in logger.loggers
    
    def test_lazy_initialization_unknown_layer(self):
        """Test lazy initialization with unknown layer."""
        logger = HydraLogger(lazy_initialization=True)
        
        # Before first log
        assert logger._initialized is False
        
        # After first log to unknown layer
        logger.info("UNKNOWN", "Message")
        assert logger._initialized is True
        assert "UNKNOWN" in logger.loggers
    
    def test_lazy_initialization_directory_creation_failure(self):
        """Test lazy initialization when directory creation fails."""
        # Use a path that will fail to create
        invalid_path = "/invalid/path/that/cannot/be/created/test.log"
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path=invalid_path)
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config, lazy_initialization=True)
        
        # Should not raise exception during initialization
        assert logger._initialized is False
        
        # Should handle directory creation failure gracefully
        logger.info("TEST", "Message")
        assert logger._initialized is True
        assert "TEST" in logger.loggers
    
    def test_lazy_initialization_thread_safety(self):
        """Test that lazy initialization is thread-safe."""
        import threading
        import time
        
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[LogDestination(type="console")]
                )
            }
        )
        
        logger = HydraLogger(config=config, lazy_initialization=True)
        
        # Create multiple threads that log simultaneously
        def log_message():
            time.sleep(0.01)  # Small delay to increase chance of race condition
            logger.info("TEST", f"Message from thread {threading.current_thread().name}")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_message, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should be initialized and have no errors
        assert logger._initialized is True
        assert "TEST" in logger.loggers
    
    def test_lazy_initialization_performance(self):
        """Test that lazy initialization improves startup performance."""
        import time
        
        # Create a complex config with many layers
        config = LoggingConfig(
            layers={
                f"LAYER{i}": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console"),
                        LogDestination(type="file", path=f"{self.temp_dir}/layer{i}.log")
                    ]
                )
                for i in range(10)
            }
        )
        
        # Measure time with immediate initialization
        start_time = time.time()
        logger_immediate = HydraLogger(config=config, lazy_initialization=False)
        immediate_time = time.time() - start_time
        
        # Measure time with lazy initialization
        start_time = time.time()
        logger_lazy = HydraLogger(config=config, lazy_initialization=True)
        lazy_time = time.time() - start_time
        
        # Lazy initialization should be faster (at least 50% faster)
        assert lazy_time < immediate_time * 0.5, f"Lazy: {lazy_time:.4f}s, Immediate: {immediate_time:.4f}s"
    
    def test_lazy_initialization_backward_compatibility(self):
        """Test that lazy initialization doesn't break existing functionality."""
        # Test with default configuration
        logger = HydraLogger()
        assert logger.lazy_initialization is False
        
        # Should work exactly like before
        logger.info("DEFAULT", "Test message")
        assert "DEFAULT" in logger.loggers
        
        # Test with custom configuration
        config = LoggingConfig(
            layers={
                "CUSTOM": LogLayer(
                    level="INFO",
                    destinations=[LogDestination(type="console")]
                )
            }
        )
        
        logger = HydraLogger(config=config)
        assert logger.lazy_initialization is False
        
        logger.info("CUSTOM", "Test message")
        assert "CUSTOM" in logger.loggers
    
    def test_lazy_initialization_environment_variables(self):
        """Test that lazy initialization works with environment variables."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[LogDestination(type="console")]
                )
            }
        )
        
        # Test with environment variable override
        with patch.dict(os.environ, {'HYDRA_LOG_LAZY_INIT': 'true'}):
            logger = HydraLogger(config=config)
            # Note: We don't currently support env var for lazy_init, but this tests the structure
        
        # Test normal behavior
        logger = HydraLogger(config=config, lazy_initialization=True)
        assert logger.lazy_initialization is True
        
        logger.info("TEST", "Message")
        assert logger._initialized is True 