"""
Role: Create sync, async, and composite logger instances from config models.
Used By:
 - `hydra_logger.core.logger_management` convenience APIs.
 - Module-level logger creation helpers in this file.
Depends On:
 - hydra_logger
 - typing
Notes:
 - Creates runtime components through factory APIs for logger factory.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, cast

from ..config.configuration_templates import configuration_templates
from ..config.models import LoggingConfig
from ..loggers.async_logger import AsyncLogger
from ..loggers.composite_logger import CompositeAsyncLogger, CompositeLogger

# Setup module removed - simplified architecture
from ..loggers.sync_logger import SyncLogger

_logger = logging.getLogger(__name__)

_CONFIG_LOADER_KWARGS = frozenset(
    {
        "strict_unknown_fields",
        "max_extends_depth",
        "max_merged_nodes",
        "use_config_cache",
        "encoding",
    }
)


class LoggerFactory:
    """Factory for constructing and caching logger implementations."""

    def __init__(self):
        self._logger_cache = {}
        self._default_config = None

    def create_logger(
        self,
        config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
        logger_type: str = "sync",
        **kwargs,
    ) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a logger instance for the requested runtime mode."""

        # Logs directory structure - simplified (no automatic creation)

        config_path = kwargs.pop("config_path", None)
        loader_kwargs: Dict[str, Any] = {}
        for key in _CONFIG_LOADER_KWARGS:
            if key in kwargs:
                loader_kwargs[key] = kwargs.pop(key)

        if config_path is not None:
            if config is not None:
                raise ValueError("Pass only one of config or config_path")
            from ..config.loader import load_logging_config

            config = load_logging_config(Path(config_path), **loader_kwargs)

        # Parse configuration
        if isinstance(config, dict):
            try:
                config = LoggingConfig(**config)
            except Exception as exc:
                _logger.exception("Invalid logger configuration dict provided: %s", exc)
                raise
        elif config is None:
            config = self._get_default_config()

        # Extension integration: Load and configure extensions
        self._setup_extensions(config)

        # Create logger based on type
        if logger_type == "sync":
            return SyncLogger(config=config, **kwargs)
        elif logger_type == "async":
            return AsyncLogger(config=config, **kwargs)
        elif logger_type == "composite":
            return CompositeLogger(config=config, **kwargs)
        elif logger_type == "composite-async":
            return CompositeAsyncLogger(config=config, **kwargs)
        else:
            raise ValueError(f"Unknown logger type: {logger_type}")

    def create_sync_logger(
        self, config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None, **kwargs
    ) -> SyncLogger:
        """Create a synchronous logger."""
        return cast(
            SyncLogger, self.create_logger(config=config, logger_type="sync", **kwargs)
        )

    def create_async_logger(
        self, config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None, **kwargs
    ) -> AsyncLogger:
        """Create an asynchronous logger."""
        return cast(
            AsyncLogger,
            self.create_logger(config=config, logger_type="async", **kwargs),
        )

    def create_composite_logger(
        self, config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None, **kwargs
    ) -> CompositeLogger:
        """Create a composite logger for complex scenarios."""
        return cast(
            CompositeLogger,
            self.create_logger(config=config, logger_type="composite", **kwargs),
        )

    def create_composite_async_logger(
        self, config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None, **kwargs
    ) -> CompositeAsyncLogger:
        """Create a composite async logger for complex scenarios."""
        return cast(
            CompositeAsyncLogger,
            self.create_logger(config=config, logger_type="composite-async", **kwargs),
        )

    def create_logger_with_template(
        self, template_name: str, logger_type: str = "sync", **kwargs
    ) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a logger from a named template configuration."""
        if not configuration_templates.has_template(template_name):
            _logger.error("Unknown configuration template requested: %s", template_name)
            raise ValueError(f"Unknown configuration template: {template_name}")

        config = configuration_templates.get_template(template_name)
        return self.create_logger(config=config, logger_type=logger_type, **kwargs)

    def create_default_logger(
        self, logger_type: str = "sync", **kwargs
    ) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a default logger with default configuration."""
        return self.create_logger_with_template("default", logger_type, **kwargs)

    def create_development_logger(
        self, logger_type: str = "sync", **kwargs
    ) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a development logger."""
        return self.create_logger_with_template("development", logger_type, **kwargs)

    def create_production_logger(
        self, logger_type: str = "sync", **kwargs
    ) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a production-ready logger."""
        return self.create_logger_with_template("production", logger_type, **kwargs)

    def create_custom_logger(
        self, logger_type: str = "sync", **kwargs
    ) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a custom logger."""
        return self.create_logger_with_template("custom", logger_type, **kwargs)

    def _get_default_config(self) -> LoggingConfig:
        """Get the default configuration."""
        if self._default_config is None:
            from ..config.defaults import get_default_config

            self._default_config = get_default_config()
        return self._default_config

    def _setup_extensions(self, config: LoggingConfig) -> None:
        """Setup extensions based on configuration."""
        if not hasattr(config, "extensions") or not config.extensions:
            return

        try:
            from ..extensions import ExtensionManager

            # Initialize extension manager
            manager = ExtensionManager()

            # Create extensions based on user config
            for extension_name, extension_config in config.extensions.items():
                enabled = extension_config.get("enabled", False)
                extension_type = extension_config.get("type", extension_name)

                # Create extension with user configuration
                manager.create_extension(
                    extension_name, extension_type, **extension_config
                )

                if enabled:
                    _logger.info("Extension '%s' created and enabled", extension_name)
                else:
                    _logger.info("Extension '%s' created but disabled", extension_name)

            # Store manager in config for logger access
            setattr(config, "_extension_manager", manager)

        except ImportError as e:
            _logger.warning("Extension system not available: %s", e)
        except Exception as e:
            _logger.exception("Error setting up extensions: %s", e)

    def set_default_config(self, config: LoggingConfig) -> None:
        """Set the default configuration."""
        self._default_config = config

    def get_cached_logger(
        self, cache_key: str
    ) -> Optional[
        Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]
    ]:
        """Get a cached logger if it exists."""
        return self._logger_cache.get(cache_key)

    def cache_logger(
        self,
        cache_key: str,
        logger: Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger],
    ) -> None:
        """Cache a logger for reuse."""
        self._logger_cache[cache_key] = logger

    def clear_cache(self) -> None:
        """Clear the logger cache."""
        self._logger_cache.clear()


# Global factory instance
logger_factory = LoggerFactory()


# Convenience functions
def create_logger(
    name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None,
    logger_type: str = "sync",
    **kwargs,
) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """Create a logger from a name string or explicit configuration object."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs["name"] = name_or_config
        config = None
    else:
        config = name_or_config

    return logger_factory.create_logger(
        config=config, logger_type=logger_type, **kwargs
    )


def create_sync_logger(
    name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None, **kwargs
) -> SyncLogger:
    """Create a synchronous logger."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs["name"] = name_or_config
        config = None
    else:
        config = name_or_config

    return logger_factory.create_sync_logger(config=config, **kwargs)


def create_async_logger(
    name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None, **kwargs
) -> AsyncLogger:
    """Create an asynchronous logger."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs["name"] = name_or_config
        config = None
    else:
        config = name_or_config

    return logger_factory.create_async_logger(config=config, **kwargs)


def create_composite_logger(
    name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None, **kwargs
) -> CompositeLogger:
    """Create a composite logger."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs["name"] = name_or_config
        config = None
    else:
        config = name_or_config

    return logger_factory.create_composite_logger(config=config, **kwargs)


def create_composite_async_logger(
    name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None, **kwargs
) -> CompositeAsyncLogger:
    """Create a composite async logger."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs["name"] = name_or_config
        config = None
    else:
        config = name_or_config

    return logger_factory.create_composite_async_logger(config=config, **kwargs)


# Magic configuration convenience functions
def create_default_logger(
    logger_type: str = "sync", **kwargs
) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """Create a logger from the default template."""
    return logger_factory.create_default_logger(logger_type=logger_type, **kwargs)


def create_development_logger(
    logger_type: str = "sync", **kwargs
) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """Create a logger from the development template."""
    return logger_factory.create_development_logger(logger_type=logger_type, **kwargs)


def create_production_logger(
    logger_type: str = "sync", **kwargs
) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """Create a logger from the production template."""
    return logger_factory.create_production_logger(logger_type=logger_type, **kwargs)


def create_custom_logger(
    logger_type: str = "sync", **kwargs
) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """Create a logger from the custom template."""
    return logger_factory.create_custom_logger(logger_type=logger_type, **kwargs)
