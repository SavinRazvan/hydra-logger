"""
Comprehensive tests for framework integration module.

This module tests the framework integration capabilities of Hydra-Logger,
including framework detection, automatic configuration, and integration
with popular Python web frameworks.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from hydra_logger.framework_integration import (
    FrameworkDetector,
    MagicConfig,
    auto_setup,
    auto_setup_async
)
from hydra_logger import HydraLogger


class TestFrameworkDetector:
    """Test framework detection capabilities."""
    
    def test_detect_framework_no_frameworks(self):
        """Test framework detection when no frameworks are installed."""
        # Test with no frameworks available
        with patch('builtins.__import__', side_effect=ImportError):
            result = FrameworkDetector.detect_framework()
            assert result is None

    def test_detect_framework_fastapi(self):
        """Test FastAPI framework detection."""
        mock_fastapi = MagicMock()
        with patch.dict('sys.modules', {'fastapi': mock_fastapi}):
            result = FrameworkDetector.detect_framework()
            assert result == 'fastapi'

    def test_detect_framework_django(self):
        """Test Django framework detection."""
        mock_django = MagicMock()
        with patch.dict('sys.modules', {'django': mock_django}):
            result = FrameworkDetector.detect_framework()
            assert result == 'django'

    def test_detect_framework_flask(self):
        """Test Flask framework detection."""
        mock_flask = MagicMock()
        with patch.dict('sys.modules', {'flask': mock_flask}):
            result = FrameworkDetector.detect_framework()
            assert result == 'flask'

    def test_detect_environment_development(self):
        """Test environment detection for development."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            result = FrameworkDetector.detect_environment()
            assert result == 'development'

    def test_detect_environment_production(self):
        """Test environment detection for production."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            result = FrameworkDetector.detect_environment()
            assert result == 'production'
    
    def test_detect_environment_testing(self):
        """Test environment detection for testing."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
            result = FrameworkDetector.detect_environment()
            assert result == 'testing'
    
    def test_detect_environment_flask_dev(self):
        """Test Flask environment detection."""
        with patch.dict(os.environ, {'FLASK_ENV': 'development'}):
            result = FrameworkDetector.detect_environment()
            assert result == 'development'

    def test_detect_environment_django_production(self):
        """Test Django production environment detection."""
        with patch.dict(os.environ, {
            'DJANGO_SETTINGS_MODULE': 'myapp.settings',
            'DJANGO_DEBUG': 'False'
        }):
            result = FrameworkDetector.detect_environment()
            assert result == 'production'
    
    def test_detect_environment_django_development(self):
        """Test Django development environment detection."""
        with patch.dict(os.environ, {
            'DJANGO_SETTINGS_MODULE': 'myapp.settings',
            'DJANGO_DEBUG': 'True'
        }):
            result = FrameworkDetector.detect_environment()
            assert result == 'development'

    def test_detect_environment_node_env(self):
        """Test Node.js environment detection."""
        with patch.dict(os.environ, {'NODE_ENV': 'production'}):
            result = FrameworkDetector.detect_environment()
            assert result == 'production'

    def test_detect_environment_default(self):
        """Test default environment detection."""
        with patch.dict(os.environ, {}, clear=True):
            result = FrameworkDetector.detect_environment()
            assert result == 'development'

    def test_detect_async_capabilities_no_async(self):
        """Test async capabilities detection when async is not available."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', False):
            result = FrameworkDetector.detect_async_capabilities()
            assert result is False

    def test_detect_async_capabilities_fastapi(self):
        """Test async capabilities detection for FastAPI."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='fastapi'):
                result = FrameworkDetector.detect_async_capabilities()
                assert result is True
    
    def test_detect_async_capabilities_django_async(self):
        """Test async capabilities detection for Django with async support."""
        mock_django = MagicMock()
        mock_django.VERSION = (3, 1, 0)
        
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='django'):
                with patch.dict('sys.modules', {'django': mock_django}):
                    result = FrameworkDetector.detect_async_capabilities()
                    assert result is True
    
    def test_detect_async_capabilities_django_sync(self):
        """Test async capabilities detection for Django without async support."""
                mock_django = MagicMock()
        mock_django.VERSION = (2, 2, 0)

        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='django'):
                with patch.dict('sys.modules', {'django': mock_django}):
                    result = FrameworkDetector.detect_async_capabilities()
                    assert result is False
    
    def test_detect_async_capabilities_flask_async(self):
        """Test async capabilities detection for Flask with async support."""
        mock_flask = MagicMock()
        mock_flask.__version__ = '2.0.0'
        
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='flask'):
                with patch.dict('sys.modules', {'flask': mock_flask}):
                    result = FrameworkDetector.detect_async_capabilities()
                    assert result is True
    
    def test_detect_async_capabilities_flask_sync(self):
        """Test async capabilities detection for Flask without async support."""
                mock_flask = MagicMock()
        mock_flask.__version__ = '1.1.0'

        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='flask'):
                with patch.dict('sys.modules', {'flask': mock_flask}):
                    result = FrameworkDetector.detect_async_capabilities()
                    assert result is False
    
    def test_detect_async_capabilities_unknown_framework(self):
        """Test async capabilities detection for unknown framework."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value=None):
                result = FrameworkDetector.detect_async_capabilities()
                assert result is False


class TestMagicConfig:
    """Test magic configuration capabilities."""

    def test_auto_setup_fastapi(self):
        """Test auto setup for FastAPI."""
        with patch.object(FrameworkDetector, 'detect_framework', return_value='fastapi'):
            with patch.object(FrameworkDetector, 'detect_environment', return_value='development'):
                with patch.object(MagicConfig, '_setup_fastapi') as mock_setup:
                    mock_setup.return_value = HydraLogger()
                    result = MagicConfig.auto_setup()
                    assert isinstance(result, HydraLogger)
                    mock_setup.assert_called_once_with('development')

    def test_auto_setup_django(self):
        """Test auto setup for Django."""
        with patch.object(FrameworkDetector, 'detect_framework', return_value='django'):
            with patch.object(FrameworkDetector, 'detect_environment', return_value='production'):
                with patch.object(MagicConfig, '_setup_django') as mock_setup:
                    mock_setup.return_value = HydraLogger()
                    result = MagicConfig.auto_setup()
                    assert isinstance(result, HydraLogger)
                    mock_setup.assert_called_once_with('production')

    def test_auto_setup_flask(self):
        """Test auto setup for Flask."""
        with patch.object(FrameworkDetector, 'detect_framework', return_value='flask'):
            with patch.object(FrameworkDetector, 'detect_environment', return_value='development'):
                with patch.object(MagicConfig, '_setup_flask') as mock_setup:
                    mock_setup.return_value = HydraLogger()
                    result = MagicConfig.auto_setup()
                    assert isinstance(result, HydraLogger)
                    mock_setup.assert_called_once_with('development')

    def test_auto_setup_generic(self):
        """Test auto setup for generic application."""
        with patch.object(FrameworkDetector, 'detect_framework', return_value=None):
            result = MagicConfig.auto_setup()
            assert isinstance(result, HydraLogger)

    def test_auto_setup_async_no_async_available(self):
        """Test async auto setup when async is not available."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', False):
            result = MagicConfig.auto_setup_async()
            assert isinstance(result, HydraLogger)

    def test_auto_setup_async_no_async_capabilities(self):
        """Test async auto setup when framework doesn't support async."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_async_capabilities', return_value=False):
                result = MagicConfig.auto_setup_async()
                assert isinstance(result, HydraLogger)

    def test_auto_setup_async_fastapi(self):
        """Test async auto setup for FastAPI."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='fastapi'):
                with patch.object(FrameworkDetector, 'detect_environment', return_value='development'):
                    with patch.object(FrameworkDetector, 'detect_async_capabilities', return_value=True):
                        with patch.object(MagicConfig, '_setup_fastapi_async') as mock_setup:
                            mock_setup.return_value = HydraLogger()
                            result = MagicConfig.auto_setup_async()
                            assert isinstance(result, HydraLogger)
                            mock_setup.assert_called_once_with('development')
    
    def test_auto_setup_async_django(self):
        """Test async auto setup for Django."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='django'):
                with patch.object(FrameworkDetector, 'detect_environment', return_value='production'):
                    with patch.object(FrameworkDetector, 'detect_async_capabilities', return_value=True):
                        with patch.object(MagicConfig, '_setup_django_async') as mock_setup:
                            mock_setup.return_value = HydraLogger()
                            result = MagicConfig.auto_setup_async()
                            assert isinstance(result, HydraLogger)
                            mock_setup.assert_called_once_with('production')
    
    def test_auto_setup_async_flask(self):
        """Test async auto setup for Flask."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='flask'):
                with patch.object(FrameworkDetector, 'detect_environment', return_value='development'):
                    with patch.object(FrameworkDetector, 'detect_async_capabilities', return_value=True):
                        with patch.object(MagicConfig, '_setup_flask_async') as mock_setup:
                            mock_setup.return_value = HydraLogger()
                            result = MagicConfig.auto_setup_async()
                            assert isinstance(result, HydraLogger)
                            mock_setup.assert_called_once_with('development')
    
    def test_auto_setup_async_generic_with_async_logger(self):
        """Test async auto setup for generic app with async logger available."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value=None):
                with patch.object(FrameworkDetector, 'detect_async_capabilities', return_value=True):
                    with patch('hydra_logger.framework_integration.AsyncHydraLogger') as mock_async_logger:
                        mock_async_logger.return_value = HydraLogger()
                        result = MagicConfig.auto_setup_async()
                        assert isinstance(result, HydraLogger)
    
    def test_auto_setup_async_generic_without_async_logger(self):
        """Test async auto setup for generic app without async logger."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value=None):
                with patch.object(FrameworkDetector, 'detect_async_capabilities', return_value=True):
                    with patch('hydra_logger.framework_integration.AsyncHydraLogger', None):
                        result = MagicConfig.auto_setup_async()
                        assert isinstance(result, HydraLogger)
    
    def test_setup_fastapi(self):
        """Test FastAPI setup."""
        result = MagicConfig._setup_fastapi('development')
        assert isinstance(result, HydraLogger)
    
    def test_setup_fastapi_async(self):
        """Test FastAPI async setup."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch('hydra_logger.framework_integration.AsyncHydraLogger') as mock_async_logger:
                mock_async_logger.return_value = HydraLogger()
                result = MagicConfig._setup_fastapi_async('development')
                assert isinstance(result, HydraLogger)
    
    def test_setup_fastapi_async_fallback(self):
        """Test FastAPI async setup fallback."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch('hydra_logger.framework_integration.AsyncHydraLogger', None):
                result = MagicConfig._setup_fastapi_async('development')
                assert isinstance(result, HydraLogger)
    
    def test_setup_django(self):
        """Test Django setup."""
        result = MagicConfig._setup_django('production')
        assert isinstance(result, HydraLogger)
    
    def test_setup_django_async(self):
        """Test Django async setup."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch('hydra_logger.framework_integration.AsyncHydraLogger') as mock_async_logger:
                mock_async_logger.return_value = HydraLogger()
                result = MagicConfig._setup_django_async('production')
                assert isinstance(result, HydraLogger)
    
    def test_setup_django_async_fallback(self):
        """Test Django async setup fallback."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch('hydra_logger.framework_integration.AsyncHydraLogger', None):
                result = MagicConfig._setup_django_async('production')
                assert isinstance(result, HydraLogger)
    
    def test_setup_flask(self):
        """Test Flask setup."""
        result = MagicConfig._setup_flask('development')
        assert isinstance(result, HydraLogger)
    
    def test_setup_flask_async(self):
        """Test Flask async setup."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch('hydra_logger.framework_integration.AsyncHydraLogger') as mock_async_logger:
                mock_async_logger.return_value = HydraLogger()
                result = MagicConfig._setup_flask_async('development')
                assert isinstance(result, HydraLogger)
    
    def test_setup_flask_async_fallback(self):
        """Test Flask async setup fallback."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch('hydra_logger.framework_integration.AsyncHydraLogger', None):
                result = MagicConfig._setup_flask_async('development')
                assert isinstance(result, HydraLogger)


class TestModuleFunctions:
    """Test module-level functions."""

    def test_auto_setup_function(self):
        """Test the auto_setup function."""
        with patch.object(MagicConfig, 'auto_setup') as mock_auto_setup:
            mock_auto_setup.return_value = HydraLogger()
            result = auto_setup()
            assert isinstance(result, HydraLogger)
            mock_auto_setup.assert_called_once()

    def test_auto_setup_async_function(self):
        """Test the auto_setup_async function."""
        with patch.object(MagicConfig, 'auto_setup_async') as mock_auto_setup_async:
            mock_auto_setup_async.return_value = HydraLogger()
            result = auto_setup_async()
            assert isinstance(result, HydraLogger)
            mock_auto_setup_async.assert_called_once()


class TestFrameworkIntegrationEndToEnd:
    """End-to-end tests for framework integration."""
    
    def test_framework_integration_with_mocks(self):
        """Test framework integration with mocked dependencies."""
        # Test FastAPI integration
        with patch.object(FrameworkDetector, 'detect_framework', return_value='fastapi'):
            with patch.object(FrameworkDetector, 'detect_environment', return_value='development'):
                logger = auto_setup()
                assert isinstance(logger, HydraLogger)
        
        # Test Django integration
        with patch.object(FrameworkDetector, 'detect_framework', return_value='django'):
            with patch.object(FrameworkDetector, 'detect_environment', return_value='production'):
                logger = auto_setup()
                assert isinstance(logger, HydraLogger)
        
        # Test Flask integration
        with patch.object(FrameworkDetector, 'detect_framework', return_value='flask'):
            with patch.object(FrameworkDetector, 'detect_environment', return_value='development'):
                logger = auto_setup()
                assert isinstance(logger, HydraLogger)
    
    def test_async_framework_integration_with_mocks(self):
        """Test async framework integration with mocked dependencies."""
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='fastapi'):
                with patch.object(FrameworkDetector, 'detect_environment', return_value='development'):
                    with patch.object(FrameworkDetector, 'detect_async_capabilities', return_value=True):
                        logger = auto_setup_async()
                        assert isinstance(logger, HydraLogger)
    
    def test_error_handling_in_framework_detection(self):
        """Test error handling in framework detection."""
        # Test with import errors
        with patch('builtins.__import__', side_effect=ImportError):
            result = FrameworkDetector.detect_framework()
            assert result is None
        
        # Test with attribute errors
        mock_django = MagicMock()
        del mock_django.VERSION
        with patch.dict('sys.modules', {'django': mock_django}):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='django'):
                result = FrameworkDetector.detect_async_capabilities()
                assert result is False
        
        # Test with value errors
        mock_flask = MagicMock()
        mock_flask.__version__ = 'invalid_version'
        with patch.dict('sys.modules', {'flask': mock_flask}):
            with patch.object(FrameworkDetector, 'detect_framework', return_value='flask'):
                result = FrameworkDetector.detect_async_capabilities()
                assert result is False


class TestFrameworkIntegrationReal:
    def test_real_setup_fastapi(self):
        logger = MagicConfig._setup_fastapi('development')
        assert isinstance(logger, HydraLogger)
        logger = MagicConfig._setup_fastapi('production')
        assert isinstance(logger, HydraLogger)

    def test_real_setup_django(self):
        logger = MagicConfig._setup_django('development')
        assert isinstance(logger, HydraLogger)
        logger = MagicConfig._setup_django('production')
        assert isinstance(logger, HydraLogger)

    def test_real_setup_flask(self):
        logger = MagicConfig._setup_flask('development')
        assert isinstance(logger, HydraLogger)
        logger = MagicConfig._setup_flask('production')
        assert isinstance(logger, HydraLogger)

    def test_real_auto_setup(self):
        logger = MagicConfig.auto_setup()
        assert isinstance(logger, HydraLogger)

    def test_real_auto_setup_async(self):
        logger = MagicConfig.auto_setup_async()
        assert isinstance(logger, HydraLogger)

    def test_real_framework_detector(self):
        result = FrameworkDetector.detect_framework()
        assert result is None
        env = FrameworkDetector.detect_environment()
        assert env == 'development'
        cap = FrameworkDetector.detect_async_capabilities()
        assert cap is False

    def test_import_error_scenario(self):
        """Test the ImportError scenario when async components are not available."""
        # This test covers lines 32-37 in framework_integration.py
        # by testing the scenario where async components fail to import
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', False):
            # Test that auto_setup_async falls back to sync when async is not available
            logger = MagicConfig.auto_setup_async()
            assert isinstance(logger, HydraLogger)
            
            # Test that detect_async_capabilities returns False when async is not available
            cap = FrameworkDetector.detect_async_capabilities()
            assert cap is False

    def test_error_branches(self):
        with patch('hydra_logger.framework_integration.ASYNC_AVAILABLE', True):
            with patch('hydra_logger.framework_integration.FrameworkDetector.detect_framework', return_value='django'):
                with patch('hydra_logger.framework_integration.django', create=True) as mock_django:
                    del mock_django.VERSION
                    cap = FrameworkDetector.detect_async_capabilities()
                    assert cap is False
            with patch('hydra_logger.framework_integration.FrameworkDetector.detect_framework', return_value='flask'):
                with patch('hydra_logger.framework_integration.flask', create=True) as mock_flask:
                    mock_flask.__version__ = 'invalid_version'
                    cap = FrameworkDetector.detect_async_capabilities()
                    assert cap is False

    @pytest.mark.asyncio
    async def test_async_logger_initialization():
        """Test async logger initialization."""
        from hydra_logger.async_hydra.async_logger import AsyncHydraLogger
        
        # Create async logger
        async_logger = AsyncHydraLogger(enable_performance_monitoring=True)
        
        # Initialize async components
        await async_logger.initialize()
        
        # Test logging
        await async_logger.info("test_async", "Async logger initialized successfully")
        
        # Test performance statistics
        stats = await async_logger.get_async_performance_statistics()
        assert stats is not None
        
        # Cleanup
        await async_logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logger_with_config():
        """Test async logger with custom configuration."""
        from hydra_logger.async_hydra.async_logger import AsyncHydraLogger
        from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
        
        # Create custom config
        config = LoggingConfig(
            layers={
                "async_test": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", path=None),
                        LogDestination(type="file", path="test_async.log", max_size="1MB")
                    ]
                )
            }
        )
        
        # Create async logger with config
        async_logger = AsyncHydraLogger(config=config)
        
        # Initialize
        await async_logger.initialize()
        
        # Test logging
        await async_logger.info("async_test", "Testing async logger with custom config")
        
        # Cleanup
        await async_logger.close()
        
        # Clean up test file
        if os.path.exists("test_async.log"):
            os.remove("test_async.log") 