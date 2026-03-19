"""
Role: Implements hydra_logger.loggers.base functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - abc
 - asyncio
 - hydra_logger
 - time
 - typing
Notes:
 - Implements logger orchestration and routing for base.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from ..config.models import LoggingConfig
from ..core.exceptions import HydraLoggerError
from ..types.records import LogRecord


# Performance profile constants for LogRecord creation
class PerformanceProfiles:
    """Performance profile constants for LogRecord creation."""

    MINIMAL = "minimal"  # Performance focus, minimal fields
    BALANCED = "balanced"  # Balanced performance with context
    CONVENIENT = "convenient"  # Convenience with auto-detected context


class BaseLogger(ABC):
    """Abstract base class for all logger implementations."""

    def __init__(
        self, config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None, **kwargs
    ):
        """Initialize the base logger."""
        self._config = self._coerce_config(config)
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
        # Use 'convenient' profile by default to enable auto-detection of
        # file_name, function_name, line_number
        self._performance_profile = kwargs.get("performance_profile", "convenient")
        self._record_creation_strategy = None
        self._setup_record_creation_strategy()

        # Performance counters
        self._log_count = 0
        self._start_time = time.time()

        # Initialize if config is provided
        if self._config:
            self._initialize_from_config(self._config)

    def _coerce_config(
        self, config: Optional[Union[LoggingConfig, Dict[str, Any]]]
    ) -> Optional[LoggingConfig]:
        """Normalize dict-based configs into LoggingConfig."""
        if config is None:
            return None
        if isinstance(config, LoggingConfig):
            return config
        if isinstance(config, dict):
            return LoggingConfig(**config)
        return None

    # =============================================================================
    # MAGIC CONFIGURATION METHODS
    # =============================================================================

    def for_production(self) -> "BaseLogger":
        """Apply production configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("production"):
            self._config = magic_configs.get_template("production")
            self._initialize_from_config(self._config)
        return self

    def for_development(self) -> "BaseLogger":
        """Apply development configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("development"):
            self._config = magic_configs.get_template("development")
            self._initialize_from_config(self._config)
        return self

    def for_testing(self) -> "BaseLogger":
        """Apply testing configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("testing"):
            self._config = magic_configs.get_template("testing")
            self._initialize_from_config(self._config)
        return self

    def for_microservice(self) -> "BaseLogger":
        """Apply microservice configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("microservice"):
            self._config = magic_configs.get_template("microservice")
            self._initialize_from_config(self._config)
        return self

    def for_web_app(self) -> "BaseLogger":
        """Apply web application configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("web_app"):
            self._config = magic_configs.get_template("web_app")
            self._initialize_from_config(self._config)
        return self

    def for_api_service(self) -> "BaseLogger":
        """Apply API service configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("api_service"):
            self._config = magic_configs.get_template("api_service")
            self._initialize_from_config(self._config)
        return self

    def for_background_worker(self) -> "BaseLogger":
        """Apply background worker configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("background_worker"):
            self._config = magic_configs.get_template("background_worker")
            self._initialize_from_config(self._config)
        return self

    def for_high_performance(self) -> "BaseLogger":
        """Apply high performance configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("high_performance"):
            self._config = magic_configs.get_template("high_performance")
            self._initialize_from_config(self._config)
        return self

    def for_minimal(self) -> "BaseLogger":
        """Apply minimal configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("minimal"):
            self._config = magic_configs.get_template("minimal")
            self._initialize_from_config(self._config)
        return self

    def for_debug(self) -> "BaseLogger":
        """Apply debug configuration."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template("debug"):
            self._config = magic_configs.get_template("debug")
            self._initialize_from_config(self._config)
        return self

    def with_magic_config(self, config_name: str) -> "BaseLogger":
        """Apply a custom magic configuration by name."""
        from ..config.configuration_templates import (
            configuration_templates as magic_configs,
        )

        if magic_configs.has_template(config_name):
            self._config = magic_configs.get_template(config_name)
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

    def initialize(self) -> None:
        """Initialize logger from current config when available."""
        if self._config is not None:
            self._initialize_from_config(self._config)

    async def emit_async(self, record: LogRecord) -> None:
        """Default async emit delegates to sync log call."""
        self.log(record.level, record.message, layer=record.layer, extra=record.extra)

    def log_batch(self, records: List[LogRecord]) -> None:
        """Default batch logging implementation."""
        for record in records:
            self.log(
                record.level, record.message, layer=record.layer, extra=record.extra
            )

    async def close_async(self) -> None:
        """Default async close delegates to close()."""
        self.close()

    async def aclose(self) -> None:
        """Compatibility alias for async close."""
        await self.close_async()

    @property
    def file_path(self) -> Optional[str]:
        """Optional file destination path exposed by file-based loggers."""
        return None

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
        if hasattr(self, "close_async") and asyncio.iscoroutinefunction(
            self.close_async
        ):
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
            except BaseException:
                pass
