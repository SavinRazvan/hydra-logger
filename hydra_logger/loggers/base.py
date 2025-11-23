"""
Base Logger Abstract Class for Hydra-Logger

This module defines the abstract base class that all logger implementations
must inherit from, providing a common interface and shared functionality.
It serves as the foundation for all logging operations in Hydra-Logger.

ARCHITECTURE:
- BaseLogger: Abstract base class for all logger implementations
- Defines common interface and shared functionality
- Provides magic configuration methods for easy setup
- Implements standardized LogRecord creation
- Supports performance profiling and optimization

CORE FEATURES:
- Abstract logging interface with level-specific methods
- Magic configuration methods for common use cases
- Standardized LogRecord creation with performance profiles
- Context manager support (sync and async)
- Performance profiling and optimization
- Feature flag management (security, plugins, monitoring)

SUPPORTED LOGGER TYPES:
- SyncLogger: Synchronous logging with immediate output
- AsyncLogger: Asynchronous logging with queue-based processing
- CompositeLogger: Composite pattern for multiple logger components
- CompositeAsyncLogger: Async version of composite logger

PERFORMANCE PROFILES:
- MINIMAL: Performance focus, minimal fields
- BALANCED: Balanced performance with context
- CONVENIENT: Convenience with auto-detected context

USAGE EXAMPLES:

Basic Logger Implementation:
    from hydra_logger.loggers.base import BaseLogger
    from hydra_logger.types.records import LogRecord
    from hydra_logger.types.levels import LogLevel

    class CustomLogger(BaseLogger):
        def log(self, level, message, **kwargs):
            # Implement logging logic
            print(f"{level}: {message}")

        def debug(self, message, **kwargs):
            self.log(LogLevel.DEBUG, message, **kwargs)

        def info(self, message, **kwargs):
            self.log(LogLevel.INFO, message, **kwargs)

        # ... implement other required methods

Magic Configuration Usage:
    from hydra_logger.loggers.base import BaseLogger

    # Create logger with magic configuration
    logger = BaseLogger().for_production()
    logger = BaseLogger().for_development()
    logger = BaseLogger().for_high_performance()
    logger = BaseLogger().for_minimal()
    logger = BaseLogger().for_debug()

    # Custom magic configuration
    logger = BaseLogger().with_magic_config("api_service")

Performance Profile Management:
    from hydra_logger.loggers.base import BaseLogger

    # Create logger with specific performance profile
    logger = BaseLogger(performance_profile="minimal")

    # Change performance profile at runtime
    logger.set_performance_profile("convenient")

    # Get current profile
    profile = logger.get_performance_profile()
    print(f"Current profile: {profile}")

Context Manager Usage:
    from hydra_logger.loggers.base import BaseLogger

    # Synchronous context manager
    with BaseLogger() as logger:
        logger.info("This is a test message")

    # Asynchronous context manager
    async with BaseLogger() as logger:
        await logger.info("This is an async test message")

Feature Management:
    from hydra_logger.loggers.base import BaseLogger

    # Create logger with specific features
    logger = BaseLogger(
        enable_security=True,
        enable_plugins=True,
        enable_monitoring=True
    )

    # Check feature status
    if logger.is_security_enabled():
        print("Security features enabled")

    if logger.is_plugins_enabled():
        print("Plugin system enabled")

    if logger.is_monitoring_enabled():
        print("Performance monitoring enabled")

LogRecord Creation:
    from hydra_logger.loggers.base import BaseLogger

    # Create logger
    logger = BaseLogger()

    # Create LogRecord using standardized method
    record = logger.create_log_record(
        level="INFO",
        message="Test message",
        layer="default",
        file_name="test.py",
        function_name="test_function",
        line_number=42
    )

    # Get record creation statistics
    stats = logger.get_record_creation_stats()
    print(f"Record creation stats: {stats}")

ABSTRACT METHODS:
- log(): Log a message at the specified level
- debug(): Log a debug message
- info(): Log an info message
- warning(): Log a warning message
- error(): Log an error message
- critical(): Log a critical message
- close(): Close the logger and cleanup resources
- get_health_status(): Get the health status of the logger

MAGIC CONFIGURATION METHODS:
- for_production(): Apply production configuration
- for_development(): Apply development configuration
- for_testing(): Apply testing configuration
- for_microservice(): Apply microservice configuration
- for_web_app(): Apply web application configuration
- for_api_service(): Apply API service configuration
- for_background_worker(): Apply background worker configuration
- for_high_performance(): Apply high performance configuration
- for_minimal(): Apply minimal configuration
- for_debug(): Apply debug configuration
- with_magic_config(): Apply custom magic configuration

PERFORMANCE OPTIMIZATION:
- Standardized LogRecord creation with strategy pattern
- Performance profiling with configurable levels
- Memory optimization and resource management
- Context manager support for automatic cleanup
- Feature flag system for optional components

ERROR HANDLING:
- Graceful error handling with fallback mechanisms
- Automatic resource cleanup on errors
- Health monitoring and status reporting
- Silent error handling for performance

BENEFITS:
- Consistent interface across all logger implementations
- Easy configuration with magic methods
- High performance with configurable profiles
- Feature set with optional components
- Production-ready with monitoring and health checks
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from ..types.records import LogRecord
from ..config.models import LoggingConfig
from ..core.exceptions import HydraLoggerError


# Performance profile constants for LogRecord creation
class PerformanceProfiles:
    """Performance profile constants for LogRecord creation."""

    MINIMAL = "minimal"  # Performance focus, minimal fields
    BALANCED = "balanced"  # Balanced performance with context
    CONVENIENT = "convenient"  # Convenience with auto-detected context


class BaseLogger(ABC):
    """Abstract base class for all logger implementations."""

    def __init__(self, config: Optional[LoggingConfig] = None, **kwargs):
        """Initialize the base logger."""
        self._config = config
        self._initialized = False
        self._closed = False
        # Disable all features by default for performance
        self._enable_security = kwargs.get("enable_security", False)
        self._enable_sanitization = kwargs.get("enable_sanitization", False)
        self._enable_data_protection = kwargs.get("enable_data_protection", False)
        self._enable_plugins = kwargs.get("enable_plugins", False)
        self._enable_monitoring = kwargs.get("enable_monitoring", False)

        # Logger name for identification (like Python logging)
        self._name = kwargs.get("name", "root")

        # LogRecord creation strategy
        # Use 'convenient' profile by default to enable auto-detection of file_name, function_name, line_number
        self._performance_profile = kwargs.get("performance_profile", "convenient")
        self._record_creation_strategy = None
        self._setup_record_creation_strategy()

        # Performance counters
        self._log_count = 0
        self._start_time = time.time()

        # Initialize if config is provided
        if config:
            self._initialize_from_config(config)

    # =============================================================================
    # MAGIC CONFIGURATION METHODS
    # =============================================================================

    def for_production(self) -> "BaseLogger":
        """Apply production configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("production"):
            self._config = magic_configs.get_config("production")
            self._initialize_from_config(self._config)
        return self

    def for_development(self) -> "BaseLogger":
        """Apply development configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("development"):
            self._config = magic_configs.get_config("development")
            self._initialize_from_config(self._config)
        return self

    def for_testing(self) -> "BaseLogger":
        """Apply testing configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("testing"):
            self._config = magic_configs.get_config("testing")
            self._initialize_from_config(self._config)
        return self

    def for_microservice(self) -> "BaseLogger":
        """Apply microservice configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("microservice"):
            self._config = magic_configs.get_config("microservice")
            self._initialize_from_config(self._config)
        return self

    def for_web_app(self) -> "BaseLogger":
        """Apply web application configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("web_app"):
            self._config = magic_configs.get_config("web_app")
            self._initialize_from_config(self._config)
        return self

    def for_api_service(self) -> "BaseLogger":
        """Apply API service configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("api_service"):
            self._config = magic_configs.get_config("api_service")
            self._initialize_from_config(self._config)
        return self

    def for_background_worker(self) -> "BaseLogger":
        """Apply background worker configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("background_worker"):
            self._config = magic_configs.get_config("background_worker")
            self._initialize_from_config(self._config)
        return self

    def for_high_performance(self) -> "BaseLogger":
        """Apply high performance configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("high_performance"):
            self._config = magic_configs.get_config("high_performance")
            self._initialize_from_config(self._config)
        return self

    def for_minimal(self) -> "BaseLogger":
        """Apply minimal configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("minimal"):
            self._config = magic_configs.get_config("minimal")
            self._initialize_from_config(self._config)
        return self

    def for_debug(self) -> "BaseLogger":
        """Apply debug configuration."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config("debug"):
            self._config = magic_configs.get_config("debug")
            self._initialize_from_config(self._config)
        return self

    def with_magic_config(self, config_name: str) -> "BaseLogger":
        """Apply a custom magic configuration by name."""
        from ..config.configuration_templates import magic_configs

        if magic_configs.has_config(config_name):
            self._config = magic_configs.get_config(config_name)
            self._initialize_from_config(self._config)
        else:
            raise ValueError(f"Unknown magic config: {config_name}")
        return self

    # =============================================================================
    # ABSTRACT METHODS
    # =============================================================================

    @abstractmethod
    def log(self, level: Union[str, int], message: str, **kwargs) -> None:
        """Log a message at the specified level."""
        pass

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the logger and cleanup resources."""
        pass

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the logger."""
        pass

    def _initialize_from_config(self, config: LoggingConfig) -> None:
        """Initialize the logger from configuration."""
        try:
            self._config = config
            self._setup_handlers()
            self._setup_formatters()
            self._setup_plugins()
            self._setup_monitoring()
            self._initialized = True
        except Exception as e:
            raise HydraLoggerError(f"Failed to initialize logger: {e}")

    def _setup_handlers(self) -> None:
        """Setup handlers from configuration."""
        # This will be implemented by subclasses
        pass

    def _setup_formatters(self) -> None:
        """Setup formatters from configuration."""
        # This will be implemented by subclasses
        pass

    def _setup_plugins(self) -> None:
        """Setup plugins from configuration."""
        # This will be implemented by subclasses
        pass

    def _setup_monitoring(self) -> None:
        """Setup monitoring from configuration."""
        # This will be implemented by subclasses
        pass


    def get_config(self) -> Optional[LoggingConfig]:
        """Get the current configuration."""
        return self._config

    @property
    def name(self) -> str:
        """Get the logger name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the logger name."""
        self._name = value

    @property
    def is_initialized(self) -> bool:
        """Check if the logger is initialized."""
        return self._initialized

    @property
    def is_closed(self) -> bool:
        """Check if the logger is closed."""
        return self._closed

    def is_security_enabled(self) -> bool:
        """Check if security features are enabled."""
        return self._enable_security

    def is_sanitization_enabled(self) -> bool:
        """Check if data sanitization is enabled."""
        return self._enable_sanitization

    def is_plugins_enabled(self) -> bool:
        """Check if plugins are enabled."""
        return self._enable_plugins

    def is_monitoring_enabled(self) -> bool:
        """Check if monitoring is enabled."""
        return self._enable_monitoring

    # =============================================================================
    # STANDARDIZED LOGRECORD CREATION
    # =============================================================================

    def _setup_record_creation_strategy(self) -> None:
        """Setup the record creation strategy based on performance profile."""
        try:
            from ..types.records import get_record_creation_strategy

            self._record_creation_strategy = get_record_creation_strategy(
                self._performance_profile
            )
        except ImportError:
            # Fallback if record_creation module is not available
            self._record_creation_strategy = None

    def create_log_record(
        self, level: Union[str, int], message: str, **kwargs
    ) -> LogRecord:
        """
        Create a LogRecord using the standardized strategy.

        This method provides a consistent way to create LogRecord instances
        across all logger implementations while maintaining optimal performance.

        Args:
            level: Log level (string or numeric)
            message: Log message
            **kwargs: Additional fields

        Returns:
            LogRecord instance
        """
        if self._record_creation_strategy:
            return self._record_creation_strategy.create_record(
                level=level, message=message, logger_name=self._name, **kwargs
            )
        else:
            # Fallback to direct LogRecord creation - FOLLOW CORRECT FIELD ORDER
            from ..types.records import LogRecord

            return LogRecord(
                timestamp=time.time(),
                level_name=(
                    str(level)
                    if isinstance(level, str)
                    else self._get_level_name(level)
                ),
                layer=kwargs.get("layer", "default"),
                file_name=kwargs.get("file_name"),
                function_name=kwargs.get("function_name"),
                message=message,
                level=self._get_level_int(level),
                logger_name=self._name,
                line_number=kwargs.get("line_number"),
                extra=kwargs.get("extra", {}),
            )

    def _get_level_name(self, level: int) -> str:
        """Get level name from numeric level."""
        level_map = {
            10: "DEBUG",
            20: "INFO",
            30: "WARNING",
            40: "ERROR",
            50: "CRITICAL",
        }
        return level_map.get(level, "INFO")

    def _get_level_int(self, level: Union[str, int]) -> int:
        """Get numeric level from string or int level."""
        if isinstance(level, int):
            return level
        level_map = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }
        return level_map.get(str(level).upper(), 20)

    def set_performance_profile(self, profile: str) -> None:
        """
        Change the performance profile at runtime.

        Args:
            profile: Performance profile (minimal, balanced, convenient)
        """
        self._performance_profile = profile
        self._setup_record_creation_strategy()

    def get_performance_profile(self) -> str:
        """Get the current performance profile."""
        return self._performance_profile

    def get_record_creation_stats(self) -> Dict[str, Any]:
        """Get statistics about record creation."""
        return {
            "performance_profile": self._performance_profile,
            "strategy": (
                self._record_creation_strategy.strategy
                if self._record_creation_strategy
                else "fallback"
            ),
            "log_count": self._log_count,
            "uptime": time.time() - self._start_time,
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        
        Properly handles async cleanup for all logger types.
        Tries close_async() or aclose() first, then falls back to sync close().
        """
        # Check for async close methods first (close_async, aclose)
        if hasattr(self, "close_async") and asyncio.iscoroutinefunction(self.close_async):
            await self.close_async()
        elif hasattr(self, "aclose") and asyncio.iscoroutinefunction(self.aclose):
            await self.aclose()
        elif hasattr(self, "close") and asyncio.iscoroutinefunction(self.close):
            await self.close()
        else:
            # Fallback to sync close if no async method available
            if hasattr(self, "close"):
                self.close()

    def __del__(self):
        """Destructor to ensure cleanup."""
        if hasattr(self, "_closed") and not self._closed:
            try:
                # Check if close is async method
                if asyncio.iscoroutinefunction(self.close):
                    # Can't await in __del__, just mark as closed
                    self._closed = True
                else:
                    self.close()
            except:
                pass
