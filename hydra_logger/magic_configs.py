"""
Custom Magic Config System for Hydra-Logger.

This module provides a registry system for custom logging configurations
that can be applied with simple method calls like HydraLogger.for_my_app().
"""

import functools
from typing import Dict, Callable, Any, Optional
from hydra_logger.config import LoggingConfig
from hydra_logger.core.exceptions import HydraLoggerError


class MagicConfigRegistry:
    """
    Registry for custom magic configurations.
    
    Allows users to register custom logging configurations that can be
    applied with simple method calls like HydraLogger.for_my_app().
    """
    
    _configs: Dict[str, Callable[[], LoggingConfig]] = {}
    _descriptions: Dict[str, str] = {}
    
    @classmethod
    def register(cls, name: str, description: str = "") -> Callable:
        """
        Register a custom magic configuration.
        
        Args:
            name: The name of the magic config (e.g., "my_app")
            description: Optional description of the config
            
        Returns:
            Decorator function that registers the config
            
        Example:
            @HydraLogger.register_magic("production")
            def production_config():
                return LoggingConfig(...)
        """
        def decorator(func: Callable[[], LoggingConfig]) -> Callable[[], LoggingConfig]:
            if not callable(func):
                raise HydraLoggerError(f"Magic config '{name}' must be a callable function")
            
            # Validate the function returns a LoggingConfig
            try:
                result = func()
                if not isinstance(result, LoggingConfig):
                    raise HydraLoggerError(
                        f"Magic config '{name}' must return a LoggingConfig instance, got {type(result)}"
                    )
            except Exception as e:
                raise HydraLoggerError(f"Magic config '{name}' failed validation: {e}")
            
            cls._configs[name] = func
            cls._descriptions[name] = description
            
            return func
        
        return decorator
    
    @classmethod
    def get_config(cls, name: str) -> LoggingConfig:
        """
        Get a registered magic configuration.
        
        Args:
            name: The name of the magic config
            
        Returns:
            The LoggingConfig instance
            
        Raises:
            HydraLoggerError: If the config is not found
        """
        if name not in cls._configs:
            available = ", ".join(sorted(cls._configs.keys())) if cls._configs else "none"
            raise HydraLoggerError(
                f"Magic config '{name}' not found. Available configs: {available}"
            )
        
        try:
            return cls._configs[name]()
        except Exception as e:
            raise HydraLoggerError(f"Failed to create magic config '{name}': {e}")
    
    @classmethod
    def list_configs(cls) -> Dict[str, str]:
        """
        List all registered magic configurations.
        
        Returns:
            Dictionary mapping config names to descriptions
        """
        return cls._descriptions.copy()
    
    @classmethod
    def has_config(cls, name: str) -> bool:
        """
        Check if a magic config is registered.
        
        Args:
            name: The name of the magic config to check
            
        Returns:
            True if the config exists, False otherwise
        """
        return name in cls._configs
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a magic configuration.
        
        Args:
            name: The name of the magic config to unregister
            
        Returns:
            True if the config was unregistered, False if it didn't exist
        """
        if name in cls._configs:
            del cls._configs[name]
            if name in cls._descriptions:
                del cls._descriptions[name]
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered magic configurations."""
        cls._configs.clear()
        cls._descriptions.clear()


# Convenience function for registering magic configs
def register_magic_config(name: str, description: str = "") -> Callable:
    """
    Register a custom magic configuration.
    
    This is a convenience function that provides the same functionality
    as HydraLogger.register_magic() but can be imported directly.
    
    Args:
        name: The name of the magic config (e.g., "my_app")
        description: Optional description of the config
        
    Returns:
        Decorator function that registers the config
        
    Example:
        @register_magic_config("production", "Production logging config")
        def production_config():
            return LoggingConfig(...)
    """
    return MagicConfigRegistry.register(name, description)


# Built-in magic configurations
@register_magic_config("production", "Production-ready logging configuration")
def production_config() -> LoggingConfig:
    """Production logging configuration with comprehensive logging."""
    from hydra_logger.config import LogLayer, LogDestination
    
    return LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="INFO",
                        color_mode="auto"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/app.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/errors.log",
                        format="json",
                        level="ERROR",
                        color_mode="never"
                    )
                ]
            ),
            "SECURITY": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/security.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            ),
            "PERFORMANCE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/performance.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            )
        }
    )


@register_magic_config("development", "Development-friendly logging configuration")
def development_config() -> LoggingConfig:
    """Development logging configuration with colored console output."""
    from hydra_logger.config import LogLayer, LogDestination
    
    return LoggingConfig(
        layers={
            "APP": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="DEBUG",
                        color_mode="always"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/dev.log",
                        format="plain-text",
                        level="DEBUG",
                        color_mode="never"
                    )
                ]
            ),
            "DEBUG": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="DEBUG",
                        color_mode="always"
                    )
                ]
            )
        }
    )


@register_magic_config("testing", "Testing-focused logging configuration")
def testing_config() -> LoggingConfig:
    """Testing logging configuration with minimal output."""
    from hydra_logger.config import LogLayer, LogDestination
    
    return LoggingConfig(
        layers={
            "TEST": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="WARNING",
                        color_mode="auto"
                    )
                ]
            )
        }
    )


@register_magic_config("microservice", "Microservice-optimized logging configuration")
def microservice_config() -> LoggingConfig:
    """Microservice logging configuration with structured output."""
    from hydra_logger.config import LogLayer, LogDestination
    
    return LoggingConfig(
        layers={
            "SERVICE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="json",
                        level="INFO",
                        color_mode="auto"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/service.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            ),
            "HEALTH": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="INFO",
                        color_mode="auto"
                    )
                ]
            )
        }
    )


@register_magic_config("web_app", "Web application logging configuration")
def web_app_config() -> LoggingConfig:
    """Web application logging configuration with request/response logging."""
    from hydra_logger.config import LogLayer, LogDestination
    
    return LoggingConfig(
        layers={
            "WEB": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="INFO",
                        color_mode="auto"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/web.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            ),
            "REQUEST": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/requests.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            ),
            "ERROR": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="ERROR",
                        color_mode="always"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/errors.log",
                        format="json",
                        level="ERROR",
                        color_mode="never"
                    )
                ]
            )
        }
    )


@register_magic_config("api_service", "API service logging configuration")
def api_service_config() -> LoggingConfig:
    """API service logging configuration with API-specific logging."""
    from hydra_logger.config import LogLayer, LogDestination
    
    return LoggingConfig(
        layers={
            "API": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="json",
                        level="INFO",
                        color_mode="auto"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/api.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            ),
            "AUTH": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/auth.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            ),
            "RATE_LIMIT": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="WARNING",
                        color_mode="always"
                    )
                ]
            )
        }
    )


@register_magic_config("background_worker", "Background worker logging configuration")
def background_worker_config() -> LoggingConfig:
    """Background worker logging configuration with task-specific logging."""
    from hydra_logger.config import LogLayer, LogDestination
    
    return LoggingConfig(
        layers={
            "WORKER": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="INFO",
                        color_mode="auto"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/worker.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            ),
            "TASK": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/tasks.log",
                        format="json",
                        level="INFO",
                        color_mode="never"
                    )
                ]
            ),
            "PROGRESS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="INFO",
                        color_mode="auto"
                    )
                ]
            )
        }
    )


@MagicConfigRegistry.register("high_performance", "Ultra-fast logging configuration optimized for maximum throughput")
def high_performance_config():
    """High-performance configuration optimized for maximum throughput."""
    from hydra_logger.config import LogLayer, LogDestination
    
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/high_performance.log",
                        format="plain-text",
                        color_mode="never",
                        max_size="10MB",
                        backup_count=2
                    ),
                    LogDestination(
                        type="console",
                        format="plain-text", 
                        color_mode="never"
                    )
                ]
            ),
            "PERFORMANCE": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/performance.log",
                        format="plain-text",
                        color_mode="never",
                        max_size="50MB",
                        backup_count=1
                    )
                ]
            )
        },
        default_level="INFO"
    )
 