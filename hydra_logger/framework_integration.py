"""
Framework integration module for HydraLogger.

This module provides one-line setup for popular Python web frameworks:
- FastAPI: Middleware integration with async support
- Django: Settings integration with async view support
- Flask: Extension integration with async route support

Each framework gets automatic configuration detection and optimized logging setup
with both sync and async capabilities.

Note: This module does not require any framework dependencies to be installed.
Framework detection and integration only work if the respective frameworks are available.
"""

import os
from typing import Optional, Any, Union

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Import async components
try:
    from hydra_logger.async_hydra import AsyncHydraLogger
    from hydra_logger.async_hydra.async_context import AsyncContextManager, get_async_context, AsyncContext, set_async_context
    ASYNC_AVAILABLE = True
    AsyncHydraLoggerType = AsyncHydraLogger
except ImportError:
    ASYNC_AVAILABLE = False
    AsyncHydraLogger = None
    AsyncHydraLoggerType = type(None)
    AsyncContext = None
    set_async_context = None


class FrameworkDetector:
    """Detect the current web framework and environment without requiring dependencies."""
    
    @staticmethod
    def detect_framework() -> Optional[str]:
        """
        Detect the current web framework.
        
        Returns:
            Optional[str]: Framework name ('fastapi', 'django', 'flask') or None
        """
        # Check for FastAPI
        try:
            import fastapi  # type: ignore
            return 'fastapi'
        except ImportError:
            pass
        
        # Check for Django
        try:
            import django  # type: ignore
            return 'django'
        except ImportError:
            pass
        
        # Check for Flask
        try:
            import flask  # type: ignore
            return 'flask'
        except ImportError:
            pass
        
        return None
    
    @staticmethod
    def detect_environment() -> str:
        """
        Detect the current environment.
        
        Returns:
            str: Environment name ('development', 'production', 'testing')
        """
        # Check environment variables
        env = os.getenv('ENVIRONMENT', '').lower()
        if env in ('development', 'production', 'testing'):
            return env
        
        # Framework-specific detection
        if os.getenv('FLASK_ENV') == 'development':
            return 'development'
        elif os.getenv('DJANGO_SETTINGS_MODULE'):
            return 'production' if os.getenv('DJANGO_DEBUG') != 'True' else 'development'
        elif os.getenv('NODE_ENV'):
            node_env = os.getenv('NODE_ENV')
            return node_env.lower() if node_env else 'development'
        
        # Default to development
        return 'development'
    
    @staticmethod
    def detect_async_capabilities() -> bool:
        """
        Detect if the current framework supports async operations.
        
        Returns:
            bool: True if async capabilities detected, False otherwise
        """
        if not ASYNC_AVAILABLE:
            return False
        
        framework = FrameworkDetector.detect_framework()
        
        if framework == 'fastapi':
            return True  # FastAPI is inherently async
        elif framework == 'django':
            # Check for Django async support (Django 3.1+)
            try:
                import django  # type: ignore
                django_version = django.VERSION
                return django_version >= (3, 1)
            except (ImportError, AttributeError):
                return False
        elif framework == 'flask':
            # Check for Flask async support (Flask 2.0+ with async support)
            try:
                import flask  # type: ignore
                flask_version = flask.__version__
                major, minor = map(int, flask_version.split('.')[:2])
                return major >= 2
            except (ImportError, ValueError):
                return False
        
        return False


class MagicConfig:
    """Magic configuration system for automatic framework detection and setup."""
    
    @staticmethod
    def auto_setup() -> HydraLogger:
        """
        Automatically detect framework and setup logging.
        
        Returns:
            HydraLogger: Configured logger instance
        """
        framework = FrameworkDetector.detect_framework()
        environment = FrameworkDetector.detect_environment()
        
        if framework == 'fastapi':
            return MagicConfig._setup_fastapi(environment)
        elif framework == 'django':
            return MagicConfig._setup_django(environment)
        elif framework == 'flask':
            return MagicConfig._setup_flask(environment)
        else:
            # Generic setup for non-framework applications
            return HydraLogger()
    
    @staticmethod
    def auto_setup_async() -> Any:
        """
        Automatically detect framework and setup async logging.
        
        Returns:
            Union[HydraLogger, AsyncHydraLogger]: Configured logger instance
        """
        if not ASYNC_AVAILABLE:
            return MagicConfig.auto_setup()
        
        framework = FrameworkDetector.detect_framework()
        environment = FrameworkDetector.detect_environment()
        has_async_capabilities = FrameworkDetector.detect_async_capabilities()
        
        if not has_async_capabilities:
            return MagicConfig.auto_setup()
        
        if framework == 'fastapi':
            return MagicConfig._setup_fastapi_async(environment)
        elif framework == 'django':
            return MagicConfig._setup_django_async(environment)
        elif framework == 'flask':
            return MagicConfig._setup_flask_async(environment)
        else:
            # Generic async setup for non-framework applications
            if AsyncHydraLogger is not None:
                return AsyncHydraLogger()
            else:
                return HydraLogger()
    
    @staticmethod
    def _setup_fastapi(environment: str) -> HydraLogger:
        """Setup FastAPI-specific configuration."""
        config = LoggingConfig(
            layers={
                "HTTP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/fastapi.log", format="json")
                    ]
                ),
                "API": LogLayer(
                    level="DEBUG" if environment == "development" else "INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/api.log", format="json")
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/error.log", format="json")
                    ]
                )
            }
        )
        
        return HydraLogger(
            config=config,
            enable_performance_monitoring=True,
            redact_sensitive=True
        )
    
    @staticmethod
    def _setup_fastapi_async(environment: str) -> Any:
        """Setup FastAPI-specific async configuration."""
        if AsyncHydraLogger is None:
            return MagicConfig._setup_fastapi(environment)
        
        config = LoggingConfig(
            layers={
                "HTTP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/fastapi_async.log", format="json")
                    ]
                ),
                "API": LogLayer(
                    level="DEBUG" if environment == "development" else "INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/api_async.log", format="json")
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/error_async.log", format="json")
                    ]
                )
            }
        )
        
        return AsyncHydraLogger(
            config=config,
            enable_performance_monitoring=True,
            redact_sensitive=True
        )
    
    @staticmethod
    def _setup_django(environment: str) -> HydraLogger:
        """Setup Django-specific configuration."""
        config = LoggingConfig(
            layers={
                "DJANGO": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/django.log", format="json")
                    ]
                ),
                "REQUEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/request.log", format="json")
                    ]
                ),
                "SECURITY": LogLayer(
                    level="WARNING",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/security.log", format="json")
                    ]
                )
            }
        )
        
        return HydraLogger(
            config=config,
            enable_performance_monitoring=True,
            redact_sensitive=True
        )
    
    @staticmethod
    def _setup_django_async(environment: str) -> Any:
        """Setup Django-specific async configuration."""
        if AsyncHydraLogger is None:
            return MagicConfig._setup_django(environment)
        
        config = LoggingConfig(
            layers={
                "DJANGO": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/django_async.log", format="json")
                    ]
                ),
                "REQUEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/request_async.log", format="json")
                    ]
                ),
                "SECURITY": LogLayer(
                    level="WARNING",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/security_async.log", format="json")
                    ]
                )
            }
        )
        
        return AsyncHydraLogger(
            config=config,
            enable_performance_monitoring=True,
            redact_sensitive=True
        )
    
    @staticmethod
    def _setup_flask(environment: str) -> HydraLogger:
        """Setup Flask-specific configuration."""
        config = LoggingConfig(
            layers={
                "FLASK": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/flask.log", format="json")
                    ]
                ),
                "REQUEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/request.log", format="json")
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/error.log", format="json")
                    ]
                )
            }
        )
        
        return HydraLogger(
            config=config,
            enable_performance_monitoring=True,
            redact_sensitive=True
        )
    
    @staticmethod
    def _setup_flask_async(environment: str) -> Any:
        """Setup Flask-specific async configuration."""
        if AsyncHydraLogger is None:
            return MagicConfig._setup_flask(environment)
        
        config = LoggingConfig(
            layers={
                "FLASK": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/flask_async.log", format="json")
                    ]
                ),
                "REQUEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/request_async.log", format="json")
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="logs/_tests_logs/error_async.log", format="json")
                    ]
                )
            }
        )
        
        return AsyncHydraLogger(
            config=config,
            enable_performance_monitoring=True,
            redact_sensitive=True
        )


# Convenience functions for one-line setup
def auto_setup() -> HydraLogger:
    """
    Automatic framework detection and setup.
    
    Returns:
        HydraLogger: Configured logger instance
    """
    return MagicConfig.auto_setup()


def auto_setup_async() -> Any:
    """
    Automatic framework detection and async setup.
    
    Returns:
        Union[HydraLogger, AsyncHydraLogger]: Configured logger instance
    """
    return MagicConfig.auto_setup_async() 