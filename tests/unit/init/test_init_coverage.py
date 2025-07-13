"""
Test coverage for hydra_logger/__init__.py missing lines.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock


class TestInitCoverage:
    """Test coverage for __init__.py missing lines."""

    def test_import_error_fallback(self):
        """Test the ImportError fallback for LoggingConfig (lines 115-117)."""
        # Mock the import to fail
        with patch.dict(sys.modules, {'hydra_logger.config.models': None}):
            # Import the module again to trigger the fallback
            import importlib
            import hydra_logger
            
            # Reload the module to trigger the ImportError
            importlib.reload(hydra_logger)
            
            # Check that LoggingConfig is None when import fails
            assert hydra_logger.LoggingConfig is None

    def test_create_logger_function(self):
        """Test the create_logger convenience function (line 223)."""
        import hydra_logger
        from hydra_logger import create_logger, HydraLogger
        
        # Test that create_logger is available
        assert 'create_logger' in dir(hydra_logger)
        
        # Test that it returns a HydraLogger instance
        logger = create_logger()
        assert isinstance(logger, HydraLogger)
        
        # Test with custom config
        config = {'layers': {'DEFAULT': {'level': 'INFO'}}}
        logger = create_logger(config=config)
        assert isinstance(logger, HydraLogger)
        
        # Test with disabled features
        logger = create_logger(
            enable_security=False,
            enable_sanitization=False,
            enable_plugins=False
        )
        assert isinstance(logger, HydraLogger)

    def test_create_logger_with_none_config(self):
        """Test create_logger with None config."""
        from hydra_logger import create_logger
        
        logger = create_logger(config=None)
        assert logger is not None

    def test_create_logger_with_dict_config(self):
        """Test create_logger with dictionary config."""
        from hydra_logger import create_logger
        
        config = {
            'layers': {
                'DEFAULT': {
                    'level': 'DEBUG',
                    'destinations': [
                        {'type': 'console', 'level': 'INFO'}
                    ]
                }
            }
        }
        
        logger = create_logger(config=config)
        assert logger is not None

    def test_create_logger_all_parameters(self):
        """Test create_logger with all parameters."""
        from hydra_logger import create_logger
        
        config = {'layers': {'DEFAULT': {'level': 'INFO'}}}
        logger = create_logger(
            config=config,
            enable_security=True,
            enable_sanitization=True,
            enable_plugins=True
        )
        assert logger is not None

    def test_create_logger_disabled_features(self):
        """Test create_logger with disabled features."""
        from hydra_logger import create_logger
        
        logger = create_logger(
            enable_security=False,
            enable_sanitization=False,
            enable_plugins=False
        )
        assert logger is not None

    def test_import_error_with_missing_module(self):
        """Test ImportError when config.models module is completely missing."""
        # Remove the module from sys.modules if it exists
        if 'hydra_logger.config.models' in sys.modules:
            del sys.modules['hydra_logger.config.models']
        
        # Mock the import to raise ImportError only for the specific module
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'hydra_logger.config.models':
                raise ImportError("No module named 'hydra_logger.config.models'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            import importlib
            import hydra_logger
            
            # Reload to trigger the ImportError
            importlib.reload(hydra_logger)
            
            # Check that LoggingConfig is None
            assert hydra_logger.LoggingConfig is None

    def test_import_error_with_module_import_error(self):
        """Test ImportError when importing LoggingConfig from config.models fails."""
        # Mock the module to exist but LoggingConfig to not exist
        mock_module = MagicMock()
        mock_module.LoggingConfig = None
        
        with patch.dict(sys.modules, {'hydra_logger.config.models': mock_module}):
            import importlib
            import hydra_logger
            
            # Reload to trigger the ImportError
            importlib.reload(hydra_logger)
            
            # Check that LoggingConfig is None
            assert hydra_logger.LoggingConfig is None 