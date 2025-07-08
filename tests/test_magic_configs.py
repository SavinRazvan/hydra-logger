"""
Tests for magic configs functionality.

This module tests the magic configuration system including
registration, validation, and built-in configurations.
"""

import pytest
from unittest.mock import patch, MagicMock

from hydra_logger import HydraLogger
from hydra_logger.core.exceptions import HydraLoggerError
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.magic_configs import (
    MagicConfigRegistry,
    register_magic_config,
    production_config,
    development_config,
    testing_config,
    microservice_config,
    web_app_config,
    api_service_config,
    background_worker_config,
    high_performance_config
)


class TestMagicConfigRegistry:
    """Test MagicConfigRegistry functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Clear any existing configs
        MagicConfigRegistry.clear()

    def teardown_method(self):
        """Cleanup test environment."""
        # Clear any test configs
        MagicConfigRegistry.clear()

    def test_register_magic_config(self):
        """Test registering a magic configuration."""
        @MagicConfigRegistry.register("test_config", "Test configuration")
        def test_config():
            return LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Check that config was registered
        assert MagicConfigRegistry.has_config("test_config")
        assert "test_config" in MagicConfigRegistry.list_configs()
        assert MagicConfigRegistry.list_configs()["test_config"] == "Test configuration"

    def test_register_magic_config_without_description(self):
        """Test registering a magic configuration without description."""
        @MagicConfigRegistry.register("test_config_no_desc")
        def test_config_no_desc():
            return LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Check that config was registered
        assert MagicConfigRegistry.has_config("test_config_no_desc")
        assert "test_config_no_desc" in MagicConfigRegistry.list_configs()
        assert MagicConfigRegistry.list_configs()["test_config_no_desc"] == ""

    def test_get_config(self):
        """Test getting a registered magic configuration."""
        @MagicConfigRegistry.register("test_get_config", "Test get config")
        def test_get_config():
            return LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Get the config
        config = MagicConfigRegistry.get_config("test_get_config")
        assert isinstance(config, LoggingConfig)
        assert "TEST" in config.layers

    def test_get_nonexistent_config(self):
        """Test getting a non-existent magic configuration."""
        with pytest.raises(HydraLoggerError) as exc_info:
            MagicConfigRegistry.get_config("nonexistent_config")
        
        assert "Magic config 'nonexistent_config' not found" in str(exc_info.value)

    def test_list_configs(self):
        """Test listing magic configurations."""
        # Register a test config
        @MagicConfigRegistry.register("test_list_config", "Test list config")
        def test_list_config():
            return LoggingConfig(layers={})
        
        configs = MagicConfigRegistry.list_configs()
        assert isinstance(configs, dict)
        assert "test_list_config" in configs
        assert configs["test_list_config"] == "Test list config"

    def test_has_config(self):
        """Test checking if magic config exists."""
        # Test non-existing config
        assert MagicConfigRegistry.has_config("nonexistent_config") is False
        
        # Register a config
        @MagicConfigRegistry.register("test_has_config", "Test has config")
        def test_has_config():
            return LoggingConfig(layers={})
        
        # Test existing config
        assert MagicConfigRegistry.has_config("test_has_config") is True

    def test_unregister_config(self):
        """Test unregistering a magic configuration."""
        @MagicConfigRegistry.register("test_unregister", "Test unregister")
        def test_unregister():
            return LoggingConfig(layers={})
        
        # Check that config was registered
        assert MagicConfigRegistry.has_config("test_unregister")
        
        # Unregister the config
        result = MagicConfigRegistry.unregister("test_unregister")
        assert result is True
        
        # Check that config was unregistered
        assert not MagicConfigRegistry.has_config("test_unregister")
        assert "test_unregister" not in MagicConfigRegistry.list_configs()

    def test_unregister_nonexistent_config(self):
        """Test unregistering a non-existent magic configuration."""
        result = MagicConfigRegistry.unregister("nonexistent_config")
        assert result is False

    def test_clear_configs(self):
        """Test clearing all magic configurations."""
        # Register some configs
        @MagicConfigRegistry.register("test_clear1", "Test clear 1")
        def test_clear1():
            return LoggingConfig(layers={})
        
        @MagicConfigRegistry.register("test_clear2", "Test clear 2")
        def test_clear2():
            return LoggingConfig(layers={})
        
        # Check that configs were registered
        assert len(MagicConfigRegistry.list_configs()) >= 2
        
        # Clear all configs
        MagicConfigRegistry.clear()
        
        # Check that all configs were cleared
        assert len(MagicConfigRegistry.list_configs()) == 0

    def test_register_invalid_config(self):
        """Test registering an invalid magic configuration."""
        with pytest.raises(HydraLoggerError) as exc_info:
            @MagicConfigRegistry.register("invalid_config", "Invalid config")
            def invalid_config():
                return "not a LoggingConfig"  # This should cause an error
        
        assert "Magic config 'invalid_config' must return a LoggingConfig instance" in str(exc_info.value)

    def test_register_non_callable(self):
        """Test registering a non-callable magic configuration."""
        with pytest.raises(HydraLoggerError) as exc_info:
            MagicConfigRegistry.register("non_callable", "Non callable")(None)
        
        assert "Magic config 'non_callable' must be a callable function" in str(exc_info.value)

    def test_register_config_with_exception(self):
        """Test registering a magic configuration that raises an exception."""
        def config_with_exception():
            raise ValueError("Test exception")
        
        with pytest.raises(HydraLoggerError) as exc_info:
            MagicConfigRegistry.register("exception_config", "Exception config")(config_with_exception)
        
        assert "Magic config 'exception_config' failed validation" in str(exc_info.value)


class TestRegisterMagicConfigFunction:
    """Test the register_magic_config convenience function."""

    def setup_method(self):
        """Setup test environment."""
        MagicConfigRegistry.clear()

    def teardown_method(self):
        """Cleanup test environment."""
        MagicConfigRegistry.clear()

    def test_register_magic_config_function(self):
        """Test the register_magic_config convenience function."""
        @register_magic_config("test_convenience", "Test convenience function")
        def test_convenience():
            return LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Check that config was registered
        assert MagicConfigRegistry.has_config("test_convenience")
        assert "test_convenience" in MagicConfigRegistry.list_configs()


class TestBuiltInMagicConfigs:
    """Test built-in magic configurations."""

    def test_production_config(self):
        """Test production configuration."""
        config = production_config()
        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert "SECURITY" in config.layers

    def test_development_config(self):
        """Test development configuration."""
        config = development_config()
        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert "DEBUG" in config.layers

    def test_testing_config(self):
        """Test testing configuration."""
        config = testing_config()
        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert "TEST" in config.layers

    def test_microservice_config(self):
        """Test microservice configuration."""
        config = microservice_config()
        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert "HEALTH" in config.layers

    def test_web_app_config(self):
        """Test web app configuration."""
        config = web_app_config()
        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert "REQUEST" in config.layers
        assert "SECURITY" in config.layers

    def test_api_service_config(self):
        """Test API service configuration."""
        config = api_service_config()
        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert "API" in config.layers
        assert "SECURITY" in config.layers

    def test_background_worker_config(self):
        """Test background worker configuration."""
        config = background_worker_config()
        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert "WORKER" in config.layers

    def test_high_performance_config(self):
        """Test high performance configuration."""
        config = high_performance_config()
        assert isinstance(config, LoggingConfig)
        assert "PERFORMANCE" in config.layers


class TestHydraLoggerMagicConfigMethods:
    """Test HydraLogger magic config methods."""

    def setup_method(self):
        """Setup test environment."""
        MagicConfigRegistry.clear()

    def teardown_method(self):
        """Cleanup test environment."""
        MagicConfigRegistry.clear()

    def test_register_magic_class_method(self):
        """Test HydraLogger.register_magic class method."""
        @HydraLogger.register_magic("test_class_method", "Test class method")
        def test_class_method():
            return LoggingConfig(
                layers={
                    "TEST": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Check that config was registered
        assert HydraLogger.has_magic_config("test_class_method")
        assert "test_class_method" in HydraLogger.list_magic_configs()

    def test_for_custom_class_method(self):
        """Test HydraLogger.for_custom class method."""
        @HydraLogger.register_magic("test_for_custom", "Test for custom")
        def test_for_custom():
            return LoggingConfig(
                layers={
                    "CUSTOM": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Create logger with custom config
        logger = HydraLogger.for_custom("test_for_custom")
        assert logger is not None
        assert "CUSTOM" in logger.config.layers

    def test_for_custom_with_kwargs(self):
        """Test HydraLogger.for_custom with additional kwargs."""
        @HydraLogger.register_magic("test_for_custom_kwargs", "Test for custom kwargs")
        def test_for_custom_kwargs():
            return LoggingConfig(
                layers={
                    "CUSTOM_KWARGS": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO")
                        ]
                    )
                }
            )
        
        # Create logger with custom config and kwargs
        logger = HydraLogger.for_custom("test_for_custom_kwargs", enable_security=False)
        assert logger is not None
        assert "CUSTOM_KWARGS" in logger.config.layers
        assert logger.enable_security is False

    def test_list_magic_configs_class_method(self):
        """Test HydraLogger.list_magic_configs class method."""
        configs = HydraLogger.list_magic_configs()
        assert isinstance(configs, dict)
        # Should have built-in configs
        assert "production" in configs
        assert "development" in configs
        assert "testing" in configs

    def test_has_magic_config_class_method(self):
        """Test HydraLogger.has_magic_config class method."""
        # Test existing config
        assert HydraLogger.has_magic_config("production") is True
        # Test non-existing config
        assert HydraLogger.has_magic_config("nonexistent_config") is False

    def test_for_production_class_method(self):
        """Test HydraLogger.for_production class method."""
        logger = HydraLogger.for_production()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_development_class_method(self):
        """Test HydraLogger.for_development class method."""
        logger = HydraLogger.for_development()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_testing_class_method(self):
        """Test HydraLogger.for_testing class method."""
        logger = HydraLogger.for_testing()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_microservice_class_method(self):
        """Test HydraLogger.for_microservice class method."""
        logger = HydraLogger.for_microservice()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_web_app_class_method(self):
        """Test HydraLogger.for_web_app class method."""
        logger = HydraLogger.for_web_app()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_api_service_class_method(self):
        """Test HydraLogger.for_api_service class method."""
        logger = HydraLogger.for_api_service()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_background_worker_class_method(self):
        """Test HydraLogger.for_background_worker class method."""
        logger = HydraLogger.for_background_worker()
        assert logger is not None
        assert "APP" in logger.config.layers

    def test_for_high_performance_class_method(self):
        """Test HydraLogger.for_high_performance class method."""
        logger = HydraLogger.for_high_performance()
        assert logger is not None
        assert logger.high_performance_mode is True
        assert logger.enable_security is False
        assert logger.enable_sanitization is False
        assert logger.enable_plugins is False

    def test_for_ultra_fast_class_method(self):
        """Test HydraLogger.for_ultra_fast class method."""
        logger = HydraLogger.for_ultra_fast()
        assert logger is not None
        assert logger.ultra_fast_mode is True
        assert logger.enable_security is False
        assert logger.enable_sanitization is False
        assert logger.enable_plugins is False

    def test_for_custom_error_handling(self):
        """Test error handling in for_custom method."""
        with pytest.raises(HydraLoggerError):
            HydraLogger.for_custom("nonexistent_config")

    def test_for_custom_with_config_error(self):
        """Test error handling in for_custom method with config error."""
        @HydraLogger.register_magic("error_config", "Error config")
        def error_config():
            raise ValueError("Test error")
        
        with pytest.raises(HydraLoggerError) as exc_info:
            HydraLogger.for_custom("error_config")
        
        assert "Failed to create magic config 'error_config'" in str(exc_info.value) 