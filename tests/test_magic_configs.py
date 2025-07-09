"""
Comprehensive tests for magic configs module.

This module tests all functionality in hydra_logger.magic_configs
to achieve 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock

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
    high_performance_config,
    _register_builtin_magic_configs
)
from hydra_logger.config.models import LoggingConfig
from hydra_logger.core.exceptions import HydraLoggerError


class TestMagicConfigRegistry:
    """Test MagicConfigRegistry class."""

    def test_magic_config_registry_init(self):
        """Test MagicConfigRegistry initialization."""
        # MagicConfigRegistry uses class attributes, not instance attributes
        assert hasattr(MagicConfigRegistry, '_configs')
        assert hasattr(MagicConfigRegistry, '_descriptions')
        assert isinstance(MagicConfigRegistry._configs, dict)
        assert isinstance(MagicConfigRegistry._descriptions, dict)

    def test_register_decorator_success(self):
        """Test successful registration with decorator."""
        @MagicConfigRegistry.register("test_config", "Test configuration")
        def test_config():
            return LoggingConfig()
        
        assert "test_config" in MagicConfigRegistry._configs
        assert "test_config" in MagicConfigRegistry._descriptions
        assert MagicConfigRegistry._descriptions["test_config"] == "Test configuration"

    def test_register_decorator_invalid_function(self):
        """Test registration with invalid function."""
        with pytest.raises(HydraLoggerError, match="must be a callable function"):
            MagicConfigRegistry.register("invalid", "Test")(None)

    def test_register_decorator_invalid_name_empty_string(self):
        """Test registration with empty string name."""
        with pytest.raises(HydraLoggerError, match="must be a non-empty string"):
            MagicConfigRegistry.register("", "Test")(lambda: LoggingConfig())

    def test_register_decorator_invalid_name_whitespace(self):
        """Test registration with whitespace-only name."""
        with pytest.raises(HydraLoggerError, match="must be a non-empty string"):
            MagicConfigRegistry.register("   ", "Test")(lambda: LoggingConfig())

    def test_register_decorator_invalid_name_not_string(self):
        """Test registration with non-string name."""
        with pytest.raises(HydraLoggerError, match="must be a non-empty string"):
            MagicConfigRegistry.register(123, "Test")(lambda: LoggingConfig())  # type: ignore

    def test_register_decorator_invalid_return_type(self):
        """Test registration with invalid return type."""
        @MagicConfigRegistry.register("invalid_return", "Test")
        def invalid_return():
            return "not a LoggingConfig"
        
        with pytest.raises(HydraLoggerError, match="must return a LoggingConfig instance"):
            MagicConfigRegistry.get_config("invalid_return")

    def test_register_decorator_function_error(self):
        """Test registration with function that raises error."""
        @MagicConfigRegistry.register("error_config", "Test")
        def error_config():
            raise Exception("Test error")
        
        with pytest.raises(HydraLoggerError, match="Failed to create magic config"):
            MagicConfigRegistry.get_config("error_config")

    def test_get_config_success(self):
        """Test getting existing config."""
        @MagicConfigRegistry.register("test_get", "Test get config")
        def test_get():
            return LoggingConfig()
        
        config = MagicConfigRegistry.get_config("test_get")
        assert isinstance(config, LoggingConfig)

    def test_get_config_not_found(self):
        """Test getting non-existent config."""
        with pytest.raises(HydraLoggerError, match="not found"):
            MagicConfigRegistry.get_config("non_existent")

    def test_get_config_not_found_with_available_configs(self):
        """Test getting non-existent config when other configs exist."""
        # Clear existing configs first
        MagicConfigRegistry.clear()
        
        @MagicConfigRegistry.register("available_config", "Available config")
        def available_config():
            return LoggingConfig()
        
        with pytest.raises(HydraLoggerError, match="Available configs: available_config"):
            MagicConfigRegistry.get_config("non_existent")

    def test_get_config_not_found_with_no_configs(self):
        """Test getting non-existent config when no configs exist."""
        # Clear all configs
        MagicConfigRegistry.clear()
        
        with pytest.raises(HydraLoggerError, match="Available configs: none"):
            MagicConfigRegistry.get_config("non_existent")

    def test_get_config_function_error(self):
        """Test getting config with function error."""
        @MagicConfigRegistry.register("error_get", "Test")
        def error_get():
            raise Exception("Function error")
        
        with pytest.raises(HydraLoggerError, match="Failed to create magic config"):
            MagicConfigRegistry.get_config("error_get")

    def test_get_config_hydra_logger_error_re_raise(self):
        """Test that HydraLoggerError is re-raised as-is."""
        @MagicConfigRegistry.register("hydra_error", "Test")
        def hydra_error():
            raise HydraLoggerError("Original error")
        
        with pytest.raises(HydraLoggerError, match="Original error"):
            MagicConfigRegistry.get_config("hydra_error")

    def test_list_configs(self):
        """Test listing all configs."""
        # Clear existing configs for clean test
        MagicConfigRegistry.clear()
        
        @MagicConfigRegistry.register("config1", "First config")
        def config1():
            return LoggingConfig()
        
        @MagicConfigRegistry.register("config2", "Second config")
        def config2():
            return LoggingConfig()
        
        configs = MagicConfigRegistry.list_configs()
        assert "config1" in configs
        assert "config2" in configs
        assert configs["config1"] == "First config"
        assert configs["config2"] == "Second config"

    def test_has_config_true(self):
        """Test checking for existing config."""
        @MagicConfigRegistry.register("test_has", "Test has config")
        def test_has():
            return LoggingConfig()
        
        assert MagicConfigRegistry.has_config("test_has") is True

    def test_has_config_false(self):
        """Test checking for non-existent config."""
        assert MagicConfigRegistry.has_config("non_existent") is False

    def test_unregister_existing(self):
        """Test unregistering existing config."""
        @MagicConfigRegistry.register("test_unregister", "Test unregister")
        def test_unregister():
            return LoggingConfig()
        
        assert MagicConfigRegistry.has_config("test_unregister") is True
        
        result = MagicConfigRegistry.unregister("test_unregister")
        assert result is True
        assert MagicConfigRegistry.has_config("test_unregister") is False

    def test_unregister_existing_with_description(self):
        """Test unregistering existing config that has description."""
        @MagicConfigRegistry.register("test_unregister_desc", "Test unregister with desc")
        def test_unregister_desc():
            return LoggingConfig()
        
        assert "test_unregister_desc" in MagicConfigRegistry._descriptions
        
        result = MagicConfigRegistry.unregister("test_unregister_desc")
        assert result is True
        assert "test_unregister_desc" not in MagicConfigRegistry._descriptions

    def test_unregister_non_existing(self):
        """Test unregistering non-existing config."""
        result = MagicConfigRegistry.unregister("non_existent")
        assert result is False

    def test_clear(self):
        """Test clearing all configs."""
        @MagicConfigRegistry.register("test_clear1", "Test clear 1")
        def test_clear1():
            return LoggingConfig()
        
        @MagicConfigRegistry.register("test_clear2", "Test clear 2")
        def test_clear2():
            return LoggingConfig()
        
        assert len(MagicConfigRegistry._configs) > 0
        assert len(MagicConfigRegistry._descriptions) > 0
        
        MagicConfigRegistry.clear()
        
        assert len(MagicConfigRegistry._configs) == 0
        assert len(MagicConfigRegistry._descriptions) == 0


class TestRegisterMagicConfig:
    """Test register_magic_config function."""

    def test_register_magic_config_success(self):
        """Test successful registration with convenience function."""
        @register_magic_config("test_convenience", "Test convenience")
        def test_convenience():
            return LoggingConfig()
        
        assert "test_convenience" in MagicConfigRegistry._configs
        assert "test_convenience" in MagicConfigRegistry._descriptions
        assert MagicConfigRegistry._descriptions["test_convenience"] == "Test convenience"

    def test_register_magic_config_no_description(self):
        """Test registration without description."""
        @register_magic_config("test_no_desc")
        def test_no_desc():
            return LoggingConfig()
        
        assert "test_no_desc" in MagicConfigRegistry._configs
        assert MagicConfigRegistry._descriptions["test_no_desc"] == ""


class TestBuiltinConfigs:
    """Test built-in magic configurations."""

    def test_production_config(self):
        """Test production configuration."""
        config = production_config()
        assert isinstance(config, LoggingConfig)
        assert "APP" in config.layers
        assert "SECURITY" in config.layers
        assert "PERFORMANCE" in config.layers

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
        assert "TEST" in config.layers

    def test_microservice_config(self):
        """Test microservice configuration."""
        config = microservice_config()
        assert isinstance(config, LoggingConfig)
        assert "SERVICE" in config.layers
        assert "HEALTH" in config.layers

    def test_web_app_config(self):
        """Test web app configuration."""
        config = web_app_config()
        assert isinstance(config, LoggingConfig)
        assert "WEB" in config.layers
        assert "REQUEST" in config.layers
        assert "ERROR" in config.layers

    def test_api_service_config(self):
        """Test API service configuration."""
        config = api_service_config()
        assert isinstance(config, LoggingConfig)
        assert "API" in config.layers
        assert "AUTH" in config.layers
        assert "RATE_LIMIT" in config.layers

    def test_background_worker_config(self):
        """Test background worker configuration."""
        config = background_worker_config()
        assert isinstance(config, LoggingConfig)
        assert "WORKER" in config.layers
        assert "TASK" in config.layers
        assert "PROGRESS" in config.layers

    def test_high_performance_config(self):
        """Test high performance configuration."""
        config = high_performance_config()
        assert isinstance(config, LoggingConfig)
        assert "DEFAULT" in config.layers
        assert "PERFORMANCE" in config.layers


class TestHydraLoggerIntegration:
    """Test HydraLogger integration with magic configs."""

    def setup_method(self):
        _register_builtin_magic_configs()

    def test_hydra_logger_register_magic(self):
        """Test HydraLogger.register_magic."""
        from hydra_logger import HydraLogger
        
        @HydraLogger.register_magic("test_integration", "Test integration")
        def test_integration():
            return LoggingConfig()
        
        assert "test_integration" in MagicConfigRegistry._configs

    def test_hydra_logger_for_custom_success(self):
        """Test HydraLogger.for_custom with existing config."""
        from hydra_logger import HydraLogger
        
        @HydraLogger.register_magic("test_for_custom", "Test for custom")
        def test_for_custom():
            return LoggingConfig()
        
        logger = HydraLogger.for_custom("test_for_custom")
        assert isinstance(logger, HydraLogger)

    def test_hydra_logger_for_custom_not_found(self):
        """Test HydraLogger.for_custom with non-existent config."""
        from hydra_logger import HydraLogger
        from hydra_logger.core.exceptions import ConfigurationError
        
        with pytest.raises(ConfigurationError, match="not found"):
            HydraLogger.for_custom("non_existent")

    def test_hydra_logger_list_magic_configs(self):
        """Test HydraLogger.list_magic_configs."""
        from hydra_logger import HydraLogger
        
        configs = HydraLogger.list_magic_configs()
        assert isinstance(configs, dict)

    def test_hydra_logger_has_magic_config(self):
        """Test HydraLogger.has_magic_config."""
        from hydra_logger import HydraLogger
        
        # Test with existing config (production should be registered)
        assert HydraLogger.has_magic_config("production") is True
        
        # Test with non-existent config
        assert HydraLogger.has_magic_config("non_existent") is False

    def test_hydra_logger_builtin_magic_configs(self):
        """Test HydraLogger built-in magic config methods."""
        from hydra_logger import HydraLogger
        
        # Test production
        logger = HydraLogger.for_production()
        assert isinstance(logger, HydraLogger)
        
        # Test development
        logger = HydraLogger.for_development()
        assert isinstance(logger, HydraLogger)
        
        # Test testing
        logger = HydraLogger.for_testing()
        assert isinstance(logger, HydraLogger)
        
        # Test microservice
        logger = HydraLogger.for_microservice()
        assert isinstance(logger, HydraLogger)
        
        # Test web_app
        logger = HydraLogger.for_web_app()
        assert isinstance(logger, HydraLogger)
        
        # Test api_service
        logger = HydraLogger.for_api_service()
        assert isinstance(logger, HydraLogger)
        
        # Test background_worker
        logger = HydraLogger.for_background_worker()
        assert isinstance(logger, HydraLogger)
        
        # Test high_performance (now minimal_features)
        logger = HydraLogger.for_minimal_features()
        assert isinstance(logger, HydraLogger)
        
        # Test ultra_fast (now bare_metal)
        logger = HydraLogger.for_bare_metal()
        assert isinstance(logger, HydraLogger)


class TestMagicConfigRegistryThreadSafety:
    """Test thread safety of MagicConfigRegistry."""

    def test_concurrent_registration(self):
        """Test concurrent registration of configs."""
        import threading
        import time
        
        def register_config_thread(config_id):
            time.sleep(0.01)  # Small delay to increase race condition chance
            @MagicConfigRegistry.register(f"config_{config_id}", f"Config {config_id}")
            def test_config():
                return LoggingConfig()
        
        # Clear existing configs
        MagicConfigRegistry.clear()
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_config_thread, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all configs were registered
        for i in range(5):
            assert MagicConfigRegistry.has_config(f"config_{i}")

    def test_concurrent_access(self):
        """Test concurrent access to registered configs."""
        import threading
        import time
        
        @MagicConfigRegistry.register("test_concurrent", "Test concurrent")
        def test_concurrent():
            return LoggingConfig()
        
        def access_config_thread(thread_id):
            for _ in range(10):
                try:
                    config = MagicConfigRegistry.get_config("test_concurrent")
                    assert isinstance(config, LoggingConfig)
                except Exception as e:
                    print(f"Thread {thread_id} error: {e}")
                time.sleep(0.001)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=access_config_thread, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()


class TestMagicConfigRegistryErrorHandling:
    """Test error handling in MagicConfigRegistry."""

    def test_register_invalid_function(self):
        """Test registering invalid function."""
        with pytest.raises(HydraLoggerError, match="must be a callable function"):
            MagicConfigRegistry.register("invalid", "Test")(None)

    def test_register_function_returning_wrong_type(self):
        """Test registering function returning wrong type."""
        @MagicConfigRegistry.register("wrong_return", "Test")
        def wrong_return():
            return "not a LoggingConfig"
        
        with pytest.raises(HydraLoggerError, match="must return a LoggingConfig instance"):
            MagicConfigRegistry.get_config("wrong_return")

    def test_register_function_raising_exception(self):
        """Test registering function that raises exception."""
        @MagicConfigRegistry.register("exception_func", "Test")
        def exception_func():
            raise Exception("Test exception")
        
        with pytest.raises(HydraLoggerError, match="Failed to create magic config"):
            MagicConfigRegistry.get_config("exception_func")

    def test_get_config_not_found_with_available_configs(self):
        """Test getting non-existent config when other configs exist."""
        @MagicConfigRegistry.register("available_config", "Available config")
        def available_config():
            return LoggingConfig()
        
        with pytest.raises(HydraLoggerError, match="Available configs: available_config"):
            MagicConfigRegistry.get_config("non_existent")

    def test_get_config_not_found_with_no_configs(self):
        """Test getting non-existent config when no configs exist."""
        # Clear all configs
        MagicConfigRegistry.clear()
        
        with pytest.raises(HydraLoggerError, match="Available configs: none"):
            MagicConfigRegistry.get_config("non_existent")

    def test_get_config_function_error(self):
        """Test getting config with function error."""
        @MagicConfigRegistry.register("error_func", "Test")
        def error_func():
            raise Exception("Function error")
        
        with pytest.raises(HydraLoggerError, match="Failed to create magic config"):
            MagicConfigRegistry.get_config("error_func")


class TestMagicConfigRegistryIntegration:
    """Test integration scenarios for MagicConfigRegistry."""

    def test_config_with_complex_layers(self):
        """Test config with complex layer structure."""
        @MagicConfigRegistry.register("complex_config", "Complex configuration")
        def complex_config():
            from hydra_logger.config import LogLayer, LogDestination
            
            return LoggingConfig(
                layers={
                    "MAIN": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(type="console", level="INFO"),
                            LogDestination(type="file", path="logs/main.log", level="INFO")
                        ]
                    ),
                    "ERROR": LogLayer(
                        level="ERROR",
                        destinations=[
                            LogDestination(type="file", path="logs/error.log", level="ERROR")
                        ]
                    )
                }
            )
        
        config = MagicConfigRegistry.get_config("complex_config")
        assert isinstance(config, LoggingConfig)
        assert "MAIN" in config.layers
        assert "ERROR" in config.layers

    def test_config_with_custom_settings(self):
        """Test config with custom settings."""
        @MagicConfigRegistry.register("custom_settings", "Custom settings")
        def custom_settings():
            from hydra_logger.config import LogLayer, LogDestination
            
            return LoggingConfig(
                layers={
                    "CUSTOM": LogLayer(
                        level="DEBUG",
                        destinations=[
                            LogDestination(
                                type="file",
                                path="logs/custom.log",
                                format="json",
                                level="DEBUG",
                                color_mode="never"
                            )
                        ]
                    )
                }
            )
        
        config = MagicConfigRegistry.get_config("custom_settings")
        assert isinstance(config, LoggingConfig)
        assert "CUSTOM" in config.layers

    def test_multiple_config_registration_and_cleanup(self):
        """Test multiple config registration and cleanup."""
        # Clear existing configs
        MagicConfigRegistry.clear()
        
        # Register multiple configs
        for i in range(5):
            @MagicConfigRegistry.register(f"test_multi_{i}", f"Test multi {i}")
            def test_multi():
                return LoggingConfig()
        
        # Verify all are registered
        for i in range(5):
            assert MagicConfigRegistry.has_config(f"test_multi_{i}")
        
        # Unregister some
        for i in range(2):
            assert MagicConfigRegistry.unregister(f"test_multi_{i}") is True
        
        # Verify remaining
        for i in range(2, 5):
            assert MagicConfigRegistry.has_config(f"test_multi_{i}")
        
        # Clear all
        MagicConfigRegistry.clear()
        
        # Verify none remain
        for i in range(5):
            assert not MagicConfigRegistry.has_config(f"test_multi_{i}")


class TestBuiltinConfigsComprehensive:
    """Comprehensive tests for all built-in configs."""

    def setup_method(self):
        _register_builtin_magic_configs()

    def test_all_builtin_configs_are_callable(self):
        """Test that all built-in configs can be called."""
        configs = [
            production_config,
            development_config,
            testing_config,
            microservice_config,
            web_app_config,
            api_service_config,
            background_worker_config,
            high_performance_config
        ]
        
        for config_func in configs:
            config = config_func()
            assert isinstance(config, LoggingConfig)

    def test_builtin_configs_are_registered(self):
        """Test that all built-in configs are registered in the registry."""
        expected_configs = [
            "production",
            "development", 
            "testing",
            "microservice",
            "web_app",
            "api_service",
            "background_worker",
            "high_performance"
        ]
        
        for config_name in expected_configs:
            assert MagicConfigRegistry.has_config(config_name), f"Config {config_name} not found"

    def test_builtin_configs_return_valid_configs(self):
        """Test that all built-in configs return valid LoggingConfig instances."""
        config_names = [
            "production",
            "development",
            "testing", 
            "microservice",
            "web_app",
            "api_service",
            "background_worker",
            "high_performance"
        ]
        
        for config_name in config_names:
            config = MagicConfigRegistry.get_config(config_name)
            assert isinstance(config, LoggingConfig)
            assert hasattr(config, 'layers')
            assert isinstance(config.layers, dict) 

class TestBuiltinConfigsCoverage:
    """Covers all re-registered built-in config functions for 100% coverage."""
    def test_all_reregistered_builtin_configs_are_callable(self):
        from hydra_logger.magic_configs import _register_builtin_magic_configs
        _register_builtin_magic_configs()
        # Call each re-registered config function by name
        from hydra_logger.magic_configs import (
            production_config, development_config, testing_config, microservice_config, web_app_config, api_service_config, background_worker_config, high_performance_config
        )
        configs = [
            production_config,
            development_config,
            testing_config,
            microservice_config,
            web_app_config,
            api_service_config,
            background_worker_config,
            high_performance_config
        ]
        for config_func in configs:
            config = config_func()
            assert hasattr(config, 'layers')
            assert isinstance(config.layers, dict) 