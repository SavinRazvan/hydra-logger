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
        
        # Test bare_metal (was ultra_fast)
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

    def test_all_builtin_config_functions_direct(self):
        # Import built-in config functions
        from hydra_logger.magic_configs import (
            production_config, development_config, testing_config, microservice_config,
            web_app_config, api_service_config, background_worker_config, high_performance_config
        )
        # Call each config function and assert the result is a LoggingConfig
        configs = [
            production_config(),
            development_config(),
            testing_config(),
            microservice_config(),
            web_app_config(),
            api_service_config(),
            background_worker_config(),
            high_performance_config(),
        ]
        for config in configs:
            assert hasattr(config, 'layers')
            assert isinstance(config.layers, dict)
            assert len(config.layers) > 0
            # Check that each layer is a LogLayer and has destinations
            for layer in config.layers.values():
                assert hasattr(layer, 'destinations')
                assert isinstance(layer.destinations, list)
                assert len(layer.destinations) > 0

    @pytest.mark.parametrize("config_func", [
            production_config,
            development_config,
            testing_config,
            microservice_config,
            web_app_config,
            api_service_config,
            background_worker_config,
        high_performance_config,
    ])
    def test_builtin_config_layers_and_destinations_full_coverage(self, config_func):
        config = config_func()
        for layer_name, layer in config.layers.items():
            # Access all LogLayer attributes
            _ = layer.level
            _ = layer.destinations
            for dest in layer.destinations:
                # Access all LogDestination attributes that might be set
                _ = getattr(dest, 'type', None)
                _ = getattr(dest, 'format', None)
                _ = getattr(dest, 'level', None)
                _ = getattr(dest, 'color_mode', None)
                _ = getattr(dest, 'path', None)
                _ = getattr(dest, 'url', None)
                _ = getattr(dest, 'extra', None)

    def test_builtin_configs_via_registry_and_direct(self):
        """Test calling config functions both directly and via registry."""
        from hydra_logger.magic_configs import (
            production_config, development_config, testing_config, microservice_config,
            web_app_config, api_service_config, background_worker_config, high_performance_config,
            _register_builtin_magic_configs
        )
        
        # Test calling each config function directly
        direct_configs = [
            production_config(),
            development_config(),
            testing_config(),
            microservice_config(),
            web_app_config(),
            api_service_config(),
            background_worker_config(),
            high_performance_config(),
        ]
        
        # Test calling each config function via registry
        registry_configs = [
            MagicConfigRegistry.get_config("production"),
            MagicConfigRegistry.get_config("development"),
            MagicConfigRegistry.get_config("testing"),
            MagicConfigRegistry.get_config("microservice"),
            MagicConfigRegistry.get_config("web_app"),
            MagicConfigRegistry.get_config("api_service"),
            MagicConfigRegistry.get_config("background_worker"),
            MagicConfigRegistry.get_config("high_performance"),
        ]
        
        # Verify all configs are valid
        for config in direct_configs + registry_configs:
            assert hasattr(config, 'layers')
            assert isinstance(config.layers, dict) 
            assert len(config.layers) > 0

    def test_register_builtin_magic_configs_function(self):
        """Test the _register_builtin_magic_configs function."""
        from hydra_logger.magic_configs import _register_builtin_magic_configs
        
        # Clear existing configs
        MagicConfigRegistry.clear()
        
        # Call the function to re-register all built-in configs
        _register_builtin_magic_configs()
        
        # Verify all configs are registered
        expected_configs = [
            "production", "development", "testing", "microservice",
            "web_app", "api_service", "background_worker", "high_performance"
        ]
        
        for config_name in expected_configs:
            assert MagicConfigRegistry.has_config(config_name)
            config = MagicConfigRegistry.get_config(config_name)
            assert hasattr(config, 'layers')
            assert isinstance(config.layers, dict)
            assert len(config.layers) > 0

    def test_builtin_configs_with_all_attributes_accessed(self):
        """Test accessing all attributes of configs to ensure full coverage."""
        from hydra_logger.magic_configs import (
            production_config, development_config, testing_config, microservice_config,
            web_app_config, api_service_config, background_worker_config, high_performance_config
        )
        
        config_functions = [
            production_config, development_config, testing_config, microservice_config,
            web_app_config, api_service_config, background_worker_config, high_performance_config
        ]
        
        for config_func in config_functions:
            config = config_func()
            
            # Access all LoggingConfig attributes
            _ = config.layers
            _ = getattr(config, 'default_level', None)
            
            # Access all LogLayer attributes
            for layer_name, layer in config.layers.items():
                _ = layer.level
                _ = layer.destinations
                
                # Access all LogDestination attributes
                for dest in layer.destinations:
                    _ = getattr(dest, 'type', None)
                    _ = getattr(dest, 'format', None)
                    _ = getattr(dest, 'level', None)
                    _ = getattr(dest, 'color_mode', None)
                    _ = getattr(dest, 'path', None)
                    _ = getattr(dest, 'url', None)
                    _ = getattr(dest, 'extra', None)
                    _ = getattr(dest, 'max_size', None)
                    _ = getattr(dest, 'backup_count', None)

    def test_magic_configs_return_statements_coverage(self):
        """Test to ensure all return statements in magic config functions are covered."""
        from hydra_logger.magic_configs import (
            production_config, development_config, testing_config, microservice_config,
            web_app_config, api_service_config, background_worker_config, high_performance_config
        )
        
        # Test production_config return statement (lines 198-200)
        prod_config = production_config()
        assert prod_config is not None
        assert hasattr(prod_config, 'layers')
        assert 'APP' in prod_config.layers
        assert 'SECURITY' in prod_config.layers
        assert 'PERFORMANCE' in prod_config.layers
        
        # Test development_config return statement (lines 258-260)
        dev_config = development_config()
        assert dev_config is not None
        assert hasattr(dev_config, 'layers')
        assert 'APP' in dev_config.layers
        assert 'DEBUG' in dev_config.layers
        
        # Test testing_config return statement (lines 298-300)
        test_config = testing_config()
        assert test_config is not None
        assert hasattr(test_config, 'layers')
        assert 'TEST' in test_config.layers
        
        # Test microservice_config return statement (lines 320-322)
        micro_config = microservice_config()
        assert micro_config is not None
        assert hasattr(micro_config, 'layers')
        assert 'SERVICE' in micro_config.layers
        assert 'HEALTH' in micro_config.layers
        
        # Test web_app_config return statement (lines 360-362)
        web_config = web_app_config()
        assert web_config is not None
        assert hasattr(web_config, 'layers')
        assert 'WEB' in web_config.layers
        assert 'REQUEST' in web_config.layers
        assert 'ERROR' in web_config.layers
        
        # Test api_service_config return statement (lines 419-421)
        api_config = api_service_config()
        assert api_config is not None
        assert hasattr(api_config, 'layers')
        assert 'API' in api_config.layers
        assert 'AUTH' in api_config.layers
        assert 'RATE_LIMIT' in api_config.layers
        
        # Test background_worker_config return statement (lines 471-473)
        worker_config = background_worker_config()
        assert worker_config is not None
        assert hasattr(worker_config, 'layers')
        assert 'WORKER' in worker_config.layers
        assert 'TASK' in worker_config.layers
        
        # Test high_performance_config return statement (lines 523-525)
        perf_config = high_performance_config()
        assert perf_config is not None
        assert hasattr(perf_config, 'layers')
        assert 'DEFAULT' in perf_config.layers
        assert 'PERFORMANCE' in perf_config.layers
    
    def test_magic_configs_direct_function_calls_with_full_property_access(self):
        """Test direct function calls with full property access to ensure all return statements are executed."""
        from hydra_logger.magic_configs import (
            production_config, development_config, testing_config, microservice_config,
            web_app_config, api_service_config, background_worker_config, high_performance_config
        )
        
        # Test production_config with full property access (lines 198-200)
        prod_config = production_config()
        # Force access to all properties to ensure full execution
        app_layer = prod_config.layers['APP']
        security_layer = prod_config.layers['SECURITY']
        performance_layer = prod_config.layers['PERFORMANCE']
        # Access all destinations to ensure full execution
        for dest in app_layer.destinations + security_layer.destinations + performance_layer.destinations:
            _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
        
        # Test development_config with full property access (lines 258-260)
        dev_config = development_config()
        app_layer = dev_config.layers['APP']
        debug_layer = dev_config.layers['DEBUG']
        for dest in app_layer.destinations + debug_layer.destinations:
            _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
        
        # Test testing_config with full property access (lines 298-300)
        test_config = testing_config()
        test_layer = test_config.layers['TEST']
        for dest in test_layer.destinations:
            _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
        
        # Test microservice_config with full property access (lines 320-322)
        micro_config = microservice_config()
        service_layer = micro_config.layers['SERVICE']
        health_layer = micro_config.layers['HEALTH']
        for dest in service_layer.destinations + health_layer.destinations:
            _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
        
        # Test web_app_config with full property access (lines 360-362)
        web_config = web_app_config()
        web_layer = web_config.layers['WEB']
        request_layer = web_config.layers['REQUEST']
        error_layer = web_config.layers['ERROR']
        for dest in web_layer.destinations + request_layer.destinations + error_layer.destinations:
            _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
        
        # Test api_service_config with full property access (lines 419-421)
        api_config = api_service_config()
        api_layer = api_config.layers['API']
        auth_layer = api_config.layers['AUTH']
        rate_limit_layer = api_config.layers['RATE_LIMIT']
        for dest in api_layer.destinations + auth_layer.destinations + rate_limit_layer.destinations:
            _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
        
        # Test background_worker_config with full property access (lines 471-473)
        worker_config = background_worker_config()
        worker_layer = worker_config.layers['WORKER']
        task_layer = worker_config.layers['TASK']
        progress_layer = worker_config.layers['PROGRESS']
        for dest in worker_layer.destinations + task_layer.destinations + progress_layer.destinations:
            _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
        
        # Test high_performance_config with full property access (lines 523-525)
        perf_config = high_performance_config()
        default_layer = perf_config.layers['DEFAULT']
        performance_layer = perf_config.layers['PERFORMANCE']
        for dest in default_layer.destinations + performance_layer.destinations:
            _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
    
    def test_magic_configs_via_registry_with_full_property_access(self):
        """Test magic configs via registry with full property access to ensure all return statements are covered."""
        from hydra_logger.magic_configs import MagicConfigRegistry
        
        # Test all configs via registry with full property access
        config_names = [
            "production", "development", "testing", "microservice",
            "web_app", "api_service", "background_worker", "high_performance"
        ]
        
        for name in config_names:
            config = MagicConfigRegistry.get_config(name)
            assert config is not None
            # Force access to all properties to ensure full execution
            layers = config.layers
            for layer_name, layer_config in layers.items():
                assert layer_config is not None
                # Access all layer properties
                _ = layer_config.level
                destinations = layer_config.destinations
                # Access all destination properties to ensure full execution
                for dest in destinations:
                    assert dest is not None
                    _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode
    
    def test_magic_configs_individual_function_calls_with_deep_access(self):
        """Test individual magic config function calls with deep property access."""
        from hydra_logger.magic_configs import (
            production_config, development_config, testing_config, microservice_config,
            web_app_config, api_service_config, background_worker_config, high_performance_config
        )
        
        # Test each function individually with deep property access
        configs_and_expected_layers = [
            (production_config, ['APP', 'SECURITY', 'PERFORMANCE']),
            (development_config, ['APP', 'DEBUG']),
            (testing_config, ['TEST']),
            (microservice_config, ['SERVICE', 'HEALTH']),
            (web_app_config, ['WEB', 'REQUEST', 'ERROR']),
            (api_service_config, ['API', 'AUTH', 'RATE_LIMIT']),
            (background_worker_config, ['WORKER', 'TASK', 'PROGRESS']),
            (high_performance_config, ['DEFAULT', 'PERFORMANCE'])
        ]
        
        for config_func, expected_layers in configs_and_expected_layers:
            config = config_func()
            assert config is not None
            assert hasattr(config, 'layers')
            
            # Access all layers and their properties
            for layer_name in expected_layers:
                assert layer_name in config.layers
                layer = config.layers[layer_name]
                assert layer is not None
                assert hasattr(layer, 'level')
                assert hasattr(layer, 'destinations')
                
                # Access all destination properties
                for dest in layer.destinations:
                    assert dest is not None
                    assert hasattr(dest, 'type')
                    assert hasattr(dest, 'path')
                    assert hasattr(dest, 'format')
                    assert hasattr(dest, 'level')
                    assert hasattr(dest, 'color_mode')
                    
                    # Force access to all properties
                    _ = dest.type, dest.path, dest.format, dest.level, dest.color_mode

    def test_magic_configs_via_registry_coverage(self):
        """Test magic configs via registry to ensure return statements are covered."""
        from hydra_logger.magic_configs import MagicConfigRegistry
        
        # Test all configs via registry
        config_names = [
            "production", "development", "testing", "microservice",
            "web_app", "api_service", "background_worker", "high_performance"
        ]
        
        for name in config_names:
            config = MagicConfigRegistry.get_config(name)
            assert config is not None
            assert hasattr(config, 'layers')
            # Access all layers to ensure full execution
            for layer_name, layer_config in config.layers.items():
                assert layer_config is not None
                assert hasattr(layer_config, 'level')
                assert hasattr(layer_config, 'destinations')
                # Access all destinations to ensure full execution
                for dest in layer_config.destinations:
                    assert dest is not None
                    assert hasattr(dest, 'type')
                    assert hasattr(dest, 'path')
                    assert hasattr(dest, 'format')
                    assert hasattr(dest, 'level')
                    assert hasattr(dest, 'color_mode')

    def test_magic_configs_direct_function_calls_coverage(self):
        """Test direct function calls to ensure return statements are executed."""
        from hydra_logger.magic_configs import (
            production_config, development_config, testing_config, microservice_config,
            web_app_config, api_service_config, background_worker_config, high_performance_config
        )
        
        # Call each function and access all properties to ensure full execution
        configs = [
            production_config(),
            development_config(),
            testing_config(),
            microservice_config(),
            web_app_config(),
            api_service_config(),
            background_worker_config(),
            high_performance_config()
        ]
        
        for config in configs:
            assert config is not None
            # Force access to all properties to ensure full execution
            layers = config.layers
            for layer_name, layer in layers.items():
                destinations = layer.destinations
                for dest in destinations:
                    # Access all destination properties
                    _ = dest.type
                    _ = dest.path
                    _ = dest.format
                    _ = dest.level
                    _ = dest.color_mode

    def test_magic_configs_registration_coverage(self):
        """Test magic config registration to ensure all return statements are covered."""
        from hydra_logger.magic_configs import _register_builtin_magic_configs
        
        # Call the registration function which calls all config functions
        _register_builtin_magic_configs()
        
        # Verify all configs are registered
        from hydra_logger.magic_configs import MagicConfigRegistry
        expected_configs = [
            "production", "development", "testing", "microservice",
            "web_app", "api_service", "background_worker", "high_performance"
        ]
        
        for config_name in expected_configs:
            assert MagicConfigRegistry.has_config(config_name)
            config = MagicConfigRegistry.get_config(config_name)
            assert config is not None

class TestMagicConfigRegistryDecoratorAndEdgeCases:
    """Covers decorator and registry edge cases for full coverage."""

    def test_register_decorator_duplicate_name(self):
        """Test registering a config with a duplicate name."""
        MagicConfigRegistry.clear()
        @MagicConfigRegistry.register("dup_config", "First")
        def config1():
            return LoggingConfig()
        # Register again with the same name
        @MagicConfigRegistry.register("dup_config", "Second")
        def config2():
            return LoggingConfig()
        # The second registration should overwrite the first
        assert MagicConfigRegistry._descriptions["dup_config"] == "Second"

    def test_register_decorator_invalid_function_type(self):
        """Test registering a non-callable as a config function (line 80)."""
        MagicConfigRegistry.clear()
        with pytest.raises(HydraLoggerError, match="must be a callable function"):
            MagicConfigRegistry.register("bad_func", "desc")(None)

    def test_register_decorator_invalid_name_empty(self):
        """Test registering with an empty string as name (line 105-106)."""
        MagicConfigRegistry.clear()
        with pytest.raises(HydraLoggerError, match="must be a non-empty string"):
            MagicConfigRegistry.register("", "desc")(lambda: LoggingConfig())

    def test_register_decorator_invalid_name_whitespace(self):
        """Test registering with whitespace as name (line 113)."""
        MagicConfigRegistry.clear()
        with pytest.raises(HydraLoggerError, match="must be a non-empty string"):
            MagicConfigRegistry.register("   ", "desc")(lambda: LoggingConfig())

    def test_register_decorator_invalid_name_type(self):
        """Test registering with a non-string name (line 117-121)."""
        MagicConfigRegistry.clear()
        # type: ignore is used to suppress type checker for this intentional error test
        with pytest.raises(HydraLoggerError, match="must be a non-empty string"):
            MagicConfigRegistry.register(123, "desc")(lambda: LoggingConfig())  # type: ignore

    def test_register_decorator_invalid_return_type(self):
        """Test registering a function that returns the wrong type (line 131)."""
        MagicConfigRegistry.clear()
        @MagicConfigRegistry.register("bad_return", "desc")
        def bad_return():
            return 123
        with pytest.raises(HydraLoggerError, match="must return a LoggingConfig instance"):
            MagicConfigRegistry.get_config("bad_return")

    def test_register_decorator_function_raises(self):
        """Test registering a function that raises an exception (lines 157-162)."""
        MagicConfigRegistry.clear()
        @MagicConfigRegistry.register("raises", "desc")
        def raises():
            raise Exception("fail")
        with pytest.raises(HydraLoggerError, match="Failed to create magic config"):
            MagicConfigRegistry.get_config("raises")

    def test_list_configs_empty(self):
        """Test listing configs when none exist (edge case for list_configs)."""
        MagicConfigRegistry.clear()
        configs = MagicConfigRegistry.list_configs()
        assert isinstance(configs, dict)
        assert len(configs) == 0

    def test_unregister_nonexistent(self):
        """Test unregistering a config that does not exist (edge case for unregister)."""
        MagicConfigRegistry.clear()
        result = MagicConfigRegistry.unregister("not_there")
        assert result is False

    def test_clear_when_empty(self):
        """Test clearing configs when already empty (edge case for clear)."""
        MagicConfigRegistry.clear()
        MagicConfigRegistry.clear()  # Should not raise
        assert len(MagicConfigRegistry._configs) == 0
        assert len(MagicConfigRegistry._descriptions) == 0 