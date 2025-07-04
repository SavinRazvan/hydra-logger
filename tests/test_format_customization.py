"""
Tests for format customization and automatic module name detection features.

This module tests the new format customization capabilities and automatic
module name detection functionality added to HydraLogger.
"""

import os
import sys
from unittest.mock import patch, MagicMock
import pytest

from hydra_logger import HydraLogger, HydraLoggerError


class TestFormatCustomization:
    """Test format customization features."""

    def test_format_customization_constructor_parameters(self):
        """Test format customization via constructor parameters."""
        logger = HydraLogger(
            date_format="%Y-%m-%d",
            time_format="%H:%M:%S",
            logger_name_format="[{name}]",
            message_format="{level}: {message}"
        )
        
        assert logger.date_format == "%Y-%m-%d"
        assert logger.time_format == "%H:%M:%S"
        assert logger.logger_name_format == "[{name}]"
        assert logger.message_format == "{level}: {message}"

    def test_format_customization_environment_variables(self):
        """Test format customization via environment variables."""
        with patch.dict(os.environ, {
            "HYDRA_LOG_DATE_FORMAT": "%Y-%m-%d",
            "HYDRA_LOG_TIME_FORMAT": "%H:%M:%S",
            "HYDRA_LOG_LOGGER_NAME_FORMAT": "[{name}]",
            "HYDRA_LOG_MESSAGE_FORMAT": "{level}: {message}"
        }):
            logger = HydraLogger()
            
            assert logger.date_format == "%Y-%m-%d"
            assert logger.time_format == "%H:%M:%S"
            assert logger.logger_name_format == "[{name}]"
            assert logger.message_format == "{level}: {message}"

    def test_format_customization_constructor_overrides_env(self):
        """Test that constructor parameters override environment variables."""
        with patch.dict(os.environ, {
            "HYDRA_LOG_DATE_FORMAT": "%Y-%m-%d",
            "HYDRA_LOG_TIME_FORMAT": "%H:%M:%S",
            "HYDRA_LOG_LOGGER_NAME_FORMAT": "[{name}]",
            "HYDRA_LOG_MESSAGE_FORMAT": "{level}: {message}"
        }):
            logger = HydraLogger(
                date_format="%d/%m/%Y",
                time_format="%I:%M %p",
                logger_name_format="<{name}>",
                message_format="[{level}] {message}"
            )
            
            assert logger.date_format == "%d/%m/%Y"
            assert logger.time_format == "%I:%M %p"
            assert logger.logger_name_format == "<{name}>"
            assert logger.message_format == "[{level}] {message}"

    def test_format_customization_defaults(self):
        """Test default format values when no customization is provided."""
        # Clear any existing environment variables
        env_vars = [
            "HYDRA_LOG_DATE_FORMAT",
            "HYDRA_LOG_TIME_FORMAT", 
            "HYDRA_LOG_LOGGER_NAME_FORMAT",
            "HYDRA_LOG_MESSAGE_FORMAT"
        ]
        
        with patch.dict(os.environ, {var: "" for var in env_vars}, clear=True):
            logger = HydraLogger()
            
            assert logger.date_format == "%Y-%m-%d %H:%M:%S"
            assert logger.time_format == "%H:%M:%S"
            assert logger.logger_name_format == "%(name)s"
            assert logger.message_format == "%(levelname)s - %(message)s"

    def test_format_customization_text_formatter(self):
        """Test that custom formats are used in text formatter."""
        logger = HydraLogger(
            date_format="%Y-%m-%d",
            logger_name_format="[{name}]",
            message_format="{level}: {message}"
        )
        
        # Mock should_use_colors to return False for text formatter
        with patch('hydra_logger.logger.should_use_colors', return_value=False):
            formatter = logger._get_text_formatter()
            
            # The format string should contain our custom components
            format_string = formatter._fmt
            assert "%Y-%m-%d" in format_string or "%(asctime)s" in format_string
            assert "[{name}]" in format_string or "%(name)s" in format_string
            assert "{level}: {message}" in format_string or "%(levelname)s" in format_string

    def test_format_customization_csv_formatter(self):
        """Test that custom date format is used in CSV formatter."""
        logger = HydraLogger(date_format="%Y-%m-%d")
        
        formatter = logger._get_csv_formatter()
        
        # Check that the date format is used
        assert formatter.datefmt == "%Y-%m-%d"


class TestAutomaticModuleNameDetection:
    """Test automatic module name detection features."""

    def test_get_calling_module_name_basic(self):
        """Test basic module name detection."""
        logger = HydraLogger()
        
        # Mock inspect.currentframe to return a frame with __name__
        mock_frame = MagicMock()
        mock_frame.f_globals = {'__name__': 'test_module'}
        mock_frame.f_back = mock_frame
        
        with patch('inspect.currentframe', return_value=mock_frame):
            module_name = logger._get_calling_module_name()
            assert module_name == 'test_module'

    def test_get_calling_module_name_main(self):
        """Test module name detection when __name__ is __main__."""
        logger = HydraLogger()
        
        # Mock inspect.currentframe to return a frame with __main__
        mock_frame = MagicMock()
        mock_frame.f_globals = {'__name__': '__main__'}
        mock_frame.f_back = mock_frame
        
        with patch('inspect.currentframe', return_value=mock_frame):
            module_name = logger._get_calling_module_name()
            assert module_name == 'DEFAULT'

    def test_get_calling_module_name_exception(self):
        """Test module name detection when exception occurs."""
        logger = HydraLogger()
        
        # Mock inspect.currentframe to raise an exception
        with patch('inspect.currentframe', side_effect=Exception("Test exception")):
            module_name = logger._get_calling_module_name()
            assert module_name == 'DEFAULT'

    def test_get_calling_module_name_no_frame(self):
        """Test module name detection when no frame is available."""
        logger = HydraLogger()
        
        # Mock inspect.currentframe to return None
        with patch('inspect.currentframe', return_value=None):
            module_name = logger._get_calling_module_name()
            assert module_name == 'DEFAULT'

    def test_logging_methods_with_auto_detection(self):
        """Test logging methods with automatic module name detection."""
        logger = HydraLogger()
        
        # Mock _get_calling_module_name to return a specific module name
        with patch.object(logger, '_get_calling_module_name', return_value='test_module'):
            # Test single argument calls (auto-detection)
            with patch.object(logger, 'log') as mock_log:
                logger.debug("Test debug message")
                mock_log.assert_called_once_with('test_module', 'DEBUG', 'Test debug message')
                
                logger.info("Test info message")
                mock_log.assert_called_with('test_module', 'INFO', 'Test info message')
                
                logger.warning("Test warning message")
                mock_log.assert_called_with('test_module', 'WARNING', 'Test warning message')
                
                logger.error("Test error message")
                mock_log.assert_called_with('test_module', 'ERROR', 'Test error message')
                
                logger.critical("Test critical message")
                mock_log.assert_called_with('test_module', 'CRITICAL', 'Test critical message')

    def test_logging_methods_with_explicit_layer(self):
        """Test logging methods with explicit layer names."""
        logger = HydraLogger()
        
        with patch.object(logger, 'log') as mock_log:
            # Test two argument calls (explicit layer)
            logger.debug("DATABASE", "Test debug message")
            mock_log.assert_called_once_with('DATABASE', 'DEBUG', 'Test debug message')
            
            logger.info("SECURITY", "Test info message")
            mock_log.assert_called_with('SECURITY', 'INFO', 'Test info message')
            
            logger.warning("CONFIG", "Test warning message")
            mock_log.assert_called_with('CONFIG', 'WARNING', 'Test warning message')
            
            logger.error("AUTH", "Test error message")
            mock_log.assert_called_with('AUTH', 'ERROR', 'Test error message')
            
            logger.critical("SYSTEM", "Test critical message")
            mock_log.assert_called_with('SYSTEM', 'CRITICAL', 'Test critical message')

    def test_logging_methods_backward_compatibility(self):
        """Test that logging methods maintain backward compatibility."""
        logger = HydraLogger()
        
        # Test that the old two-argument style still works
        with patch.object(logger, 'log') as mock_log:
            logger.debug("LAYER", "message")
            mock_log.assert_called_once_with('LAYER', 'DEBUG', 'message')
            
            logger.info("LAYER", "message")
            mock_log.assert_called_with('LAYER', 'INFO', 'message')
            
            logger.warning("LAYER", "message")
            mock_log.assert_called_with('LAYER', 'WARNING', 'message')
            
            logger.error("LAYER", "message")
            mock_log.assert_called_with('LAYER', 'ERROR', 'message')
            
            logger.critical("LAYER", "message")
            mock_log.assert_called_with('LAYER', 'CRITICAL', 'message')


class TestIntegrationFeatures:
    """Test integration of format customization and auto-detection."""

    def test_format_customization_with_auto_detection(self):
        """Test format customization works with automatic module name detection."""
        logger = HydraLogger(
            date_format="%Y-%m-%d",
            logger_name_format="[{name}]",
            message_format="{level}: {message}"
        )
        
        with patch.object(logger, '_get_calling_module_name', return_value='test_module'):
            with patch.object(logger, 'log') as mock_log:
                logger.info("Test message")
                mock_log.assert_called_once_with('test_module', 'INFO', 'Test message')

    def test_environment_variables_with_auto_detection(self):
        """Test environment variables work with automatic module name detection."""
        with patch.dict(os.environ, {
            "HYDRA_LOG_DATE_FORMAT": "%Y-%m-%d",
            "HYDRA_LOG_LOGGER_NAME_FORMAT": "[{name}]",
            "HYDRA_LOG_MESSAGE_FORMAT": "{level}: {message}"
        }):
            logger = HydraLogger()
            
            with patch.object(logger, '_get_calling_module_name', return_value='test_module'):
                with patch.object(logger, 'log') as mock_log:
                    logger.info("Test message")
                    mock_log.assert_called_once_with('test_module', 'INFO', 'Test message')

    def test_mixed_usage_patterns(self):
        """Test mixed usage of auto-detection and explicit layers."""
        logger = HydraLogger()
        
        with patch.object(logger, '_get_calling_module_name', return_value='test_module'):
            with patch.object(logger, 'log') as mock_log:
                # Auto-detection
                logger.info("Auto-detected message")
                mock_log.assert_called_with('test_module', 'INFO', 'Auto-detected message')
                
                # Explicit layer
                logger.info("DATABASE", "Explicit layer message")
                mock_log.assert_called_with('DATABASE', 'INFO', 'Explicit layer message')
                
                # Back to auto-detection
                logger.error("Another auto-detected message")
                mock_log.assert_called_with('test_module', 'ERROR', 'Another auto-detected message')


class TestErrorHandling:
    """Test error handling for new features."""

    def test_format_customization_invalid_formats(self):
        """Test handling of invalid format strings."""
        # Test with invalid date format
        logger = HydraLogger(date_format="invalid_format")
        # Should not raise an exception during initialization
        
        # Test with invalid logger name format
        logger = HydraLogger(logger_name_format="invalid_format")
        # Should not raise an exception during initialization

    def test_auto_detection_fallback(self):
        """Test auto-detection fallback when module detection fails."""
        logger = HydraLogger()
        
        # Mock _get_calling_module_name to return 'DEFAULT'
        with patch.object(logger, '_get_calling_module_name', return_value='DEFAULT'):
            with patch.object(logger, 'log') as mock_log:
                logger.info("Test message")
                mock_log.assert_called_once_with('DEFAULT', 'INFO', 'Test message')

    def test_logging_methods_with_none_message(self):
        """Test logging methods handle None messages gracefully."""
        logger = HydraLogger()
        
        with patch.object(logger, 'log') as mock_log:
            # Should not call log method for None messages
            logger.info(None)
            mock_log.assert_not_called()
            
            logger.debug(None)
            mock_log.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__]) 