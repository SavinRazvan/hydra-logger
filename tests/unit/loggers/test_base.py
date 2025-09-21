"""
Tests for hydra_logger.loggers.base module.

This module tests the BaseLogger abstract class and related functionality.
"""

import pytest
import time
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock
from hydra_logger.loggers.base import BaseLogger, PerformanceProfiles
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel
from hydra_logger.config.models import LoggingConfig


class ConcreteLogger(BaseLogger):
    """Concrete implementation of BaseLogger for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._logs = []
        # Handle security and performance profile parameters
        self._security_enabled = kwargs.get('enable_security', False)
        self._performance_profile = kwargs.get('performance_profile', 'convenient')
    
    def log(self, level, message: str, **kwargs) -> None:
        """Implementation of abstract log method."""
        if not self._initialized:
            raise RuntimeError("Logger not initialized")
        if self._closed:
            raise RuntimeError("Logger is closed")
        
        # Handle empty message validation - allow None for testing
        if message == "":
            raise ValueError("Message cannot be empty")
        
        # Extract extra and context from kwargs
        extra = kwargs.pop('extra', {})
        context = kwargs.pop('context', {})
        
        # Create a simple record for testing
        record = LogRecord(
            message=message,
            level=level,
            level_name=str(level),
            logger_name=self._name,
            layer="test",
            timestamp=time.time(),
            extra=extra,
            context=context
        )
        self._logs.append(record)
        self._log_count += 1
    
    def debug(self, message: str, **kwargs) -> None:
        """Implementation of abstract debug method."""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Implementation of abstract info method."""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Implementation of abstract warning method."""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Implementation of abstract error method."""
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Implementation of abstract critical method."""
        self.log(LogLevel.CRITICAL, message, **kwargs)
    
    def close(self) -> None:
        """Implementation of abstract close method."""
        self._closed = True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Implementation of abstract get_health_status method."""
        return {
            "status": "healthy" if not self._closed else "closed",
            "initialized": self._initialized,
            "log_count": self._log_count,
            "uptime_seconds": time.time() - self._start_time
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        return {
            "log_count": self._log_count,
            "initialized": self._initialized,
            "closed": self._closed,
            "name": self._name,
            "uptime_seconds": time.time() - self._start_time,
            "performance_profile": getattr(self, '_performance_profile', 'convenient'),
            "features": {
                "security": getattr(self, '_enable_security', False),
                "sanitization": getattr(self, '_enable_sanitization', False),
                "plugins": getattr(self, '_enable_plugins', False),
                "monitoring": getattr(self, '_enable_monitoring', False)
            }
        }
    
    def initialize(self) -> None:
        """Initialize the logger."""
        self._initialized = True
    
    # Async methods for testing
    async def alog(self, message: str, level, **kwargs) -> None:
        """Async log method."""
        self.log(level, message, **kwargs)
    
    async def adebug(self, message: str, **kwargs) -> None:
        """Async debug method."""
        self.debug(message, **kwargs)
    
    async def ainfo(self, message: str, **kwargs) -> None:
        """Async info method."""
        self.info(message, **kwargs)
    
    async def awarning(self, message: str, **kwargs) -> None:
        """Async warning method."""
        self.warning(message, **kwargs)
    
    async def aerror(self, message: str, **kwargs) -> None:
        """Async error method."""
        self.error(message, **kwargs)
    
    async def acritical(self, message: str, **kwargs) -> None:
        """Async critical method."""
        self.critical(message, **kwargs)
    
    async def aclose(self) -> None:
        """Async close method."""
        self.close()
    


class TestPerformanceProfiles:
    """Test PerformanceProfiles constants."""
    
    def test_performance_profiles_values(self):
        """Test PerformanceProfiles constant values."""
        assert PerformanceProfiles.MINIMAL == "minimal"
        assert PerformanceProfiles.BALANCED == "balanced"
        assert PerformanceProfiles.CONVENIENT == "convenient"


class TestBaseLogger:
    """Test BaseLogger functionality."""
    
    def test_base_logger_creation(self):
        """Test BaseLogger creation."""
        logger = ConcreteLogger()
        
        assert logger._config is None
        assert logger._initialized is False
        assert logger._closed is False
        assert logger._enable_security is False
        assert logger._enable_sanitization is False
        assert logger._enable_plugins is False
        assert logger._enable_monitoring is False
        assert logger._name == "root"
        assert logger._performance_profile == "convenient"
        assert logger._log_count == 0
        assert logger._start_time > 0
    
    def test_base_logger_with_config(self):
        """Test BaseLogger creation with config."""
        config = LoggingConfig()
        logger = ConcreteLogger(config=config)
        
        assert logger._config == config
    
    def test_base_logger_with_kwargs(self):
        """Test BaseLogger creation with kwargs."""
        logger = ConcreteLogger(
            enable_security=True,
            enable_sanitization=True,
            enable_plugins=True,
            enable_monitoring=True,
            name="test_logger",
            performance_profile="minimal"
        )
        
        assert logger._enable_security is True
        assert logger._enable_sanitization is True
        assert logger._enable_plugins is True
        assert logger._enable_monitoring is True
        assert logger._name == "test_logger"
        assert logger._performance_profile == "minimal"
    
    def test_base_logger_initialization(self):
        """Test BaseLogger initialization."""
        logger = ConcreteLogger()
        
        # Should not be initialized by default
        assert logger._initialized is False
        
        # Initialize
        logger.initialize()
        assert logger._initialized is True
    
    def test_base_logger_double_initialization(self):
        """Test that double initialization doesn't cause issues."""
        logger = ConcreteLogger()
        
        logger.initialize()
        assert logger._initialized is True
        
        # Second initialization should not cause issues
        logger.initialize()
        assert logger._initialized is True
    
    def test_base_logger_log_method(self):
        """Test BaseLogger log method."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Test logging
        logger.log(LogLevel.INFO, "Test message")
        
        assert logger._log_count == 1
        assert len(logger._logs) == 1
        assert logger._logs[0].message == "Test message"
        assert logger._logs[0].level == LogLevel.INFO
    
    def test_base_logger_log_with_kwargs(self):
        """Test BaseLogger log method with kwargs."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Test logging with extra fields
        logger.log(LogLevel.INFO, "Test message", extra={"user_id": 123, "action": "login"})
        
        assert logger._log_count == 1
        assert len(logger._logs) == 1
        record = logger._logs[0]
        assert record.message == "Test message"
        assert record.level == LogLevel.INFO
        assert record.extra["user_id"] == 123
        assert record.extra["action"] == "login"
    
    def test_base_logger_log_with_context(self):
        """Test BaseLogger log method with context."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Test logging with context
        context = {"request_id": "req-123", "user_id": 456}
        logger.log(LogLevel.INFO, "Test message", context=context)
        
        assert logger._log_count == 1
        assert len(logger._logs) == 1
        record = logger._logs[0]
        assert record.message == "Test message"
        assert record.level == LogLevel.INFO
        assert record.context["request_id"] == "req-123"
        assert record.context["user_id"] == 456
    
    def test_base_logger_convenience_methods(self):
        """Test BaseLogger convenience methods."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Test debug
        logger.debug("Debug message")
        assert logger._log_count == 1
        assert logger._logs[0].level == LogLevel.DEBUG
        assert logger._logs[0].message == "Debug message"
        
        # Test info
        logger.info("Info message")
        assert logger._log_count == 2
        assert logger._logs[1].level == LogLevel.INFO
        assert logger._logs[1].message == "Info message"
        
        # Test warning
        logger.warning("Warning message")
        assert logger._log_count == 3
        assert logger._logs[2].level == LogLevel.WARNING
        assert logger._logs[2].message == "Warning message"
        
        # Test error
        logger.error("Error message")
        assert logger._log_count == 4
        assert logger._logs[3].level == LogLevel.ERROR
        assert logger._logs[3].message == "Error message"
        
        # Test critical
        logger.critical("Critical message")
        assert logger._log_count == 5
        assert logger._logs[4].level == LogLevel.CRITICAL
        assert logger._logs[4].message == "Critical message"
    
    def test_base_logger_convenience_methods_with_kwargs(self):
        """Test BaseLogger convenience methods with kwargs."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Test with extra fields
        logger.info("Info message", extra={"key": "value"})
        assert logger._logs[0].extra["key"] == "value"
        
        # Test with context
        logger.warning("Warning message", context={"ctx": "data"})
        assert logger._logs[1].context["ctx"] == "data"
    
    def test_base_logger_log_before_initialization(self):
        """Test that logging before initialization raises error."""
        logger = ConcreteLogger()
        
        with pytest.raises(RuntimeError, match="Logger not initialized"):
            logger.log(LogLevel.INFO, "Test message")
    
    def test_base_logger_log_after_close(self):
        """Test that logging after close raises error."""
        logger = ConcreteLogger()
        logger.initialize()
        logger.close()
        
        with pytest.raises(RuntimeError, match="Logger is closed"):
            logger.log(LogLevel.INFO, "Test message")
    
    def test_base_logger_close(self):
        """Test BaseLogger close method."""
        logger = ConcreteLogger()
        logger.initialize()
        
        assert logger._closed is False
        logger.close()
        assert logger._closed is True
    
    def test_base_logger_double_close(self):
        """Test that double close doesn't cause issues."""
        logger = ConcreteLogger()
        logger.initialize()
        
        logger.close()
        assert logger._closed is True
        
        # Second close should not cause issues
        logger.close()
        assert logger._closed is True
    
    def test_base_logger_get_stats(self):
        """Test BaseLogger get_stats method."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Log some messages
        logger.info("Message 1")
        logger.warning("Message 2")
        logger.error("Message 3")
        
        stats = logger.get_stats()
        
        assert stats["log_count"] == 3
        assert stats["uptime_seconds"] > 0
        assert stats["name"] == "root"
        assert stats["initialized"] is True
        assert stats["closed"] is False
        assert stats["performance_profile"] == "convenient"
        assert stats["features"]["security"] is False
        assert stats["features"]["sanitization"] is False
        assert stats["features"]["plugins"] is False
        assert stats["features"]["monitoring"] is False
    
    def test_base_logger_get_stats_after_close(self):
        """Test BaseLogger get_stats method after close."""
        logger = ConcreteLogger()
        logger.initialize()
        logger.close()
        
        stats = logger.get_stats()
        assert stats["closed"] is True
    
    def test_base_logger_performance_profiles(self):
        """Test different performance profiles."""
        # Test minimal profile
        logger_minimal = ConcreteLogger(performance_profile="minimal")
        assert logger_minimal._performance_profile == "minimal"
        
        # Test balanced profile
        logger_balanced = ConcreteLogger(performance_profile="balanced")
        assert logger_balanced._performance_profile == "balanced"
        
        # Test convenient profile
        logger_convenient = ConcreteLogger(performance_profile="convenient")
        assert logger_convenient._performance_profile == "convenient"
    
    def test_base_logger_name_property(self):
        """Test BaseLogger name property."""
        logger = ConcreteLogger(name="custom_logger")
        assert logger.name == "custom_logger"
        
        # Test default name
        logger_default = ConcreteLogger()
        assert logger_default.name == "root"
    
    def test_base_logger_is_initialized_property(self):
        """Test BaseLogger is_initialized property."""
        logger = ConcreteLogger()
        assert logger.is_initialized is False
        
        logger.initialize()
        assert logger.is_initialized is True
    
    def test_base_logger_is_closed_property(self):
        """Test BaseLogger is_closed property."""
        logger = ConcreteLogger()
        assert logger.is_closed is False
        
        logger.close()
        assert logger.is_closed is True


class TestBaseLoggerAsync:
    """Test BaseLogger async functionality."""
    
    @pytest.mark.asyncio
    async def test_base_logger_async_log(self):
        """Test BaseLogger async log method."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Test async logging
        await logger.alog("Test message", LogLevel.INFO)
        
        assert logger._log_count == 1
        assert len(logger._logs) == 1
        assert logger._logs[0].message == "Test message"
        assert logger._logs[0].level == LogLevel.INFO
    
    @pytest.mark.asyncio
    async def test_base_logger_async_log_with_kwargs(self):
        """Test BaseLogger async log method with kwargs."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Test async logging with extra fields
        await logger.alog("Test message", LogLevel.INFO, extra={"key": "value"})
        
        assert logger._log_count == 1
        assert len(logger._logs) == 1
        record = logger._logs[0]
        assert record.message == "Test message"
        assert record.level == LogLevel.INFO
        assert record.extra["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_base_logger_async_convenience_methods(self):
        """Test BaseLogger async convenience methods."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Test async debug
        await logger.adebug("Debug message")
        assert logger._log_count == 1
        assert logger._logs[0].level == LogLevel.DEBUG
        
        # Test async info
        await logger.ainfo("Info message")
        assert logger._log_count == 2
        assert logger._logs[1].level == LogLevel.INFO
        
        # Test async warning
        await logger.awarning("Warning message")
        assert logger._log_count == 3
        assert logger._logs[2].level == LogLevel.WARNING
        
        # Test async error
        await logger.aerror("Error message")
        assert logger._log_count == 4
        assert logger._logs[3].level == LogLevel.ERROR
        
        # Test async critical
        await logger.acritical("Critical message")
        assert logger._log_count == 5
        assert logger._logs[4].level == LogLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_base_logger_async_log_before_initialization(self):
        """Test that async logging before initialization raises error."""
        logger = ConcreteLogger()
        
        with pytest.raises(RuntimeError, match="Logger not initialized"):
            await logger.alog("Test message", LogLevel.INFO)
    
    @pytest.mark.asyncio
    async def test_base_logger_async_log_after_close(self):
        """Test that async logging after close raises error."""
        logger = ConcreteLogger()
        logger.initialize()
        await logger.aclose()
        
        with pytest.raises(RuntimeError, match="Logger is closed"):
            await logger.alog("Test message", LogLevel.INFO)
    
    @pytest.mark.asyncio
    async def test_base_logger_async_close(self):
        """Test BaseLogger async close method."""
        logger = ConcreteLogger()
        logger.initialize()
        
        assert logger._closed is False
        await logger.aclose()
        assert logger._closed is True


class TestBaseLoggerErrorHandling:
    """Test BaseLogger error handling."""
    
    def test_base_logger_invalid_performance_profile(self):
        """Test BaseLogger with invalid performance profile."""
        # Should not raise error, just use the provided value
        logger = ConcreteLogger(performance_profile="invalid_profile")
        assert logger._performance_profile == "invalid_profile"
    
    def test_base_logger_log_with_invalid_level(self):
        """Test BaseLogger log with invalid level."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Should not raise error, just use the provided value
        logger.log("invalid_level", "Test message")
        assert logger._logs[0].level == "invalid_level"
    
    def test_base_logger_log_with_none_message(self):
        """Test BaseLogger log with None message."""
        logger = ConcreteLogger()
        logger.initialize()
        
        # Should handle None message gracefully
        logger.log(LogLevel.INFO, None)
        assert logger._logs[0].message is None


class TestBaseLoggerIntegration:
    """Integration tests for BaseLogger."""
    
    def test_base_logger_full_workflow(self):
        """Test complete BaseLogger workflow."""
        logger = ConcreteLogger(
            name="integration_test",
            enable_security=True,
            performance_profile="balanced"
        )
        
        # Initial state
        assert logger.is_initialized is False
        assert logger.is_closed is False
        
        # Initialize
        logger.initialize()
        assert logger.is_initialized is True
        
        # Log various messages
        logger.debug("Debug message", extra={"debug": True})
        logger.info("Info message", context={"request_id": "req-123"})
        logger.warning("Warning message", extra={"warning": True}, context={"user": "test"})
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Check stats
        stats = logger.get_stats()
        assert stats["log_count"] == 5
        assert stats["name"] == "integration_test"
        assert stats["features"]["security"] is True
        assert stats["performance_profile"] == "balanced"
        
        # Check logs
        assert len(logger._logs) == 5
        assert logger._logs[0].level == LogLevel.DEBUG
        assert logger._logs[1].level == LogLevel.INFO
        assert logger._logs[2].level == LogLevel.WARNING
        assert logger._logs[3].level == LogLevel.ERROR
        assert logger._logs[4].level == LogLevel.CRITICAL
        
        # Close
        logger.close()
        assert logger.is_closed is True
        
        # Final stats
        final_stats = logger.get_stats()
        assert final_stats["closed"] is True
    
    @pytest.mark.asyncio
    async def test_base_logger_async_full_workflow(self):
        """Test complete BaseLogger async workflow."""
        logger = ConcreteLogger(
            name="async_integration_test",
            enable_monitoring=True,
            performance_profile="minimal"
        )
        
        # Initialize
        logger.initialize()
        
        # Log various messages asynchronously
        await logger.adebug("Async debug message")
        await logger.ainfo("Async info message", extra={"async": True})
        await logger.awarning("Async warning message", context={"async_ctx": "data"})
        await logger.aerror("Async error message")
        await logger.acritical("Async critical message")
        
        # Check stats
        stats = logger.get_stats()
        assert stats["log_count"] == 5
        assert stats["name"] == "async_integration_test"
        assert stats["features"]["monitoring"] is True
        assert stats["performance_profile"] == "minimal"
        
        # Check logs
        assert len(logger._logs) == 5
        
        # Close asynchronously
        await logger.aclose()
        assert logger.is_closed is True


class TestBaseLoggerPerformance:
    """Performance tests for BaseLogger."""
    
    def test_base_logger_logging_performance(self):
        """Test BaseLogger logging performance."""
        logger = ConcreteLogger(performance_profile="minimal")
        logger.initialize()
        
        # Time multiple log operations
        start_time = time.perf_counter()
        for i in range(1000):
            logger.info(f"Message {i}")
        end_time = time.perf_counter()
        
        # Should be fast (less than 0.1 seconds for 1000 operations)
        duration = end_time - start_time
        assert duration < 0.1
        assert logger._log_count == 1000
    
    @pytest.mark.asyncio
    async def test_base_logger_async_logging_performance(self):
        """Test BaseLogger async logging performance."""
        logger = ConcreteLogger(performance_profile="minimal")
        logger.initialize()
        
        # Time multiple async log operations
        start_time = time.perf_counter()
        for i in range(1000):
            await logger.ainfo(f"Async message {i}")
        end_time = time.perf_counter()
        
        # Should be fast (less than 0.2 seconds for 1000 async operations)
        duration = end_time - start_time
        assert duration < 0.2
        assert logger._log_count == 1000
