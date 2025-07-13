"""
Tests for formatters module.

This module tests the ColoredTextFormatter and PlainTextFormatter classes
to achieve 100% coverage of the formatters module.
"""

import logging
import sys
from unittest.mock import patch, MagicMock
import pytest

from hydra_logger.core.formatters import ColoredTextFormatter, PlainTextFormatter
from hydra_logger.core.constants import Colors, DEFAULT_COLORS


class TestColoredTextFormatter:
    """Tests for ColoredTextFormatter."""
    
    def test_colored_text_formatter_initialization(self):
        """Test ColoredTextFormatter initialization."""
        # Test with default parameters
        formatter = ColoredTextFormatter()
        assert formatter.force_colors is None
        assert formatter.destination_type == "auto"
        assert formatter.color_mode == "auto"
        
        # Test with custom parameters
        formatter = ColoredTextFormatter(
            fmt="%(levelname)s - %(message)s",
            datefmt="%Y-%m-%d",
            force_colors="always",
            destination_type="console",
            color_mode="always"
        )
        assert formatter.force_colors == "always"
        assert formatter.destination_type == "console"
        assert formatter.color_mode == "always"
    
    def test_colored_text_formatter_color_mode_never(self):
        """Test formatter with color_mode='never'."""
        formatter = ColoredTextFormatter(color_mode="never")
        
        # Create a test record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Should not contain color codes
        assert Colors.RESET not in formatted
        assert Colors.MAGENTA not in formatted
        assert "Test message" in formatted
    
    def test_colored_text_formatter_color_mode_always(self):
        """Test formatter with color_mode='always'."""
        formatter = ColoredTextFormatter(color_mode="always")
        
        # Create a test record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Should contain color codes
        assert Colors.RESET in formatted
        assert Colors.MAGENTA in formatted
        assert "Test message" in formatted
    
    def test_colored_text_formatter_color_mode_auto_with_force_colors_never(self):
        """Test formatter with color_mode='auto' and force_colors='never'."""
        formatter = ColoredTextFormatter(color_mode="auto", force_colors="never")
        
        # Create a test record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Should not contain color codes
        assert Colors.RESET not in formatted
        assert Colors.MAGENTA not in formatted
        assert "Test message" in formatted
    
    def test_colored_text_formatter_color_mode_auto_with_force_colors_always(self):
        """Test formatter with color_mode='auto' and force_colors='always'."""
        formatter = ColoredTextFormatter(color_mode="auto", force_colors="always")
        
        # Create a test record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Should contain color codes
        assert Colors.RESET in formatted
        assert Colors.MAGENTA in formatted
        assert "Test message" in formatted
    
    def test_colored_text_formatter_color_mode_auto_with_tty(self):
        """Test formatter with color_mode='auto' and TTY detection."""
        formatter = ColoredTextFormatter(color_mode="auto")
        
        # Mock sys.stdout.isatty to return True
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            
            # Create a test record
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Format the record
            formatted = formatter.format(record)
            
            # Should contain color codes
            assert Colors.RESET in formatted
            assert Colors.MAGENTA in formatted
            assert "Test message" in formatted
    
    def test_colored_text_formatter_color_mode_auto_without_tty(self):
        """Test formatter with color_mode='auto' without TTY."""
        formatter = ColoredTextFormatter(color_mode="auto")
        
        # Mock sys.stdout.isatty to return False
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = False
            
            # Create a test record
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Format the record
            formatted = formatter.format(record)
            
            # Should not contain color codes
            assert Colors.RESET not in formatted
            assert Colors.MAGENTA not in formatted
            assert "Test message" in formatted
    
    def test_colored_text_formatter_color_mode_auto_without_isatty_attribute(self):
        """Test formatter with color_mode='auto' when stdout has no isatty attribute."""
        formatter = ColoredTextFormatter(color_mode="auto")
        
        # Mock sys.stdout without isatty attribute
        with patch('sys.stdout') as mock_stdout:
            # Remove isatty attribute
            if hasattr(mock_stdout, 'isatty'):
                delattr(mock_stdout, 'isatty')
            
            # Create a test record
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Format the record
            formatted = formatter.format(record)
            
            # Should not contain color codes
            assert Colors.RESET not in formatted
            assert Colors.MAGENTA not in formatted
            assert "Test message" in formatted
    
    def test_colored_text_formatter_with_different_levels(self):
        """Test formatter with different log levels."""
        formatter = ColoredTextFormatter(color_mode="always")
        
        # Test different levels
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
        
        for level in levels:
            record = logging.LogRecord(
                name="test_logger",
                level=level,
                pathname="test.py",
                lineno=1,
                msg=f"Test message for {level}",
                args=(),
                exc_info=None
            )
            
            formatted = formatter.format(record)
            
            # Should contain color codes
            assert Colors.RESET in formatted
            assert Colors.MAGENTA in formatted
            assert f"Test message for {level}" in formatted
    
    def test_colored_text_formatter_with_custom_format(self):
        """Test formatter with custom format string."""
        custom_format = "%(levelname)s - %(name)s - %(message)s"
        formatter = ColoredTextFormatter(fmt=custom_format, color_mode="always")
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should contain the custom format elements
        assert "INFO" in formatted
        assert "test_logger" in formatted
        assert "Test message" in formatted
        assert Colors.RESET in formatted
        assert Colors.MAGENTA in formatted
    
    def test_colored_text_formatter_with_date_format(self):
        """Test formatter with custom date format."""
        formatter = ColoredTextFormatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            color_mode="always"
        )
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should contain date and color codes
        assert " - " in formatted
        assert "Test message" in formatted
        assert Colors.RESET in formatted
        assert Colors.MAGENTA in formatted
    
    def test_colored_text_formatter_with_exception(self):
        """Test formatter with exception information."""
        formatter = ColoredTextFormatter(color_mode="always")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Test message with exception",
                args=(),
                exc_info=sys.exc_info()
            )
            
            formatted = formatter.format(record)
            
            # Should contain color codes and exception info
            assert Colors.RESET in formatted
            assert Colors.MAGENTA in formatted
            assert "Test message with exception" in formatted
            assert "ValueError" in formatted
    
    def test_colored_text_formatter_invalid_color_mode(self):
        """Test formatter with invalid color_mode."""
        formatter = ColoredTextFormatter(color_mode="invalid_mode")
        
        # Create a test record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Should fall back to auto-detect behavior
        formatted = formatter.format(record)
        assert "Test message" in formatted


class TestPlainTextFormatter:
    """Tests for PlainTextFormatter."""
    
    def test_plain_text_formatter_initialization(self):
        """Test PlainTextFormatter initialization."""
        # Test with default parameters
        formatter = PlainTextFormatter()
        assert formatter is not None
        
        # Test with custom parameters
        formatter = PlainTextFormatter(
            fmt="%(levelname)s - %(message)s",
            datefmt="%Y-%m-%d"
        )
        assert formatter is not None
    
    def test_plain_text_formatter_format(self):
        """Test PlainTextFormatter format method."""
        formatter = PlainTextFormatter()
        
        # Create a test record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Should not contain color codes
        assert Colors.RESET not in formatted
        assert Colors.MAGENTA not in formatted
        assert "Test message" in formatted
    
    def test_plain_text_formatter_with_custom_format(self):
        """Test PlainTextFormatter with custom format."""
        custom_format = "%(levelname)s - %(name)s - %(message)s"
        formatter = PlainTextFormatter(fmt=custom_format)
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should contain the custom format elements without colors
        assert "INFO" in formatted
        assert "test_logger" in formatted
        assert "Test message" in formatted
        assert Colors.RESET not in formatted
        assert Colors.MAGENTA not in formatted
    
    def test_plain_text_formatter_with_date_format(self):
        """Test PlainTextFormatter with custom date format."""
        formatter = PlainTextFormatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should contain date without color codes
        assert " - " in formatted
        assert "Test message" in formatted
        assert Colors.RESET not in formatted
        assert Colors.MAGENTA not in formatted
    
    def test_plain_text_formatter_with_exception(self):
        """Test PlainTextFormatter with exception information."""
        formatter = PlainTextFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Test message with exception",
                args=(),
                exc_info=sys.exc_info()
            )
            
            formatted = formatter.format(record)
            
            # Should contain exception info without color codes
            assert "Test message with exception" in formatted
            assert "ValueError" in formatted
            assert Colors.RESET not in formatted
            assert Colors.MAGENTA not in formatted


class TestFormatterIntegration:
    """Integration tests for formatters."""
    
    def test_formatter_comparison(self):
        """Test that colored and plain formatters produce different output."""
        colored_formatter = ColoredTextFormatter(color_mode="always")
        plain_formatter = PlainTextFormatter()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        colored_output = colored_formatter.format(record)
        plain_output = plain_formatter.format(record)
        
        # Outputs should be different
        assert colored_output != plain_output
        
        # Colored should contain color codes
        assert Colors.RESET in colored_output
        assert Colors.MAGENTA in colored_output
        
        # Plain should not contain color codes
        assert Colors.RESET not in plain_output
        assert Colors.MAGENTA not in plain_output
    
    def test_formatter_with_logger(self):
        """Test formatters with actual logger."""
        # Create a logger
        logger = logging.getLogger("test_formatter_logger")
        logger.setLevel(logging.INFO)
        
        # Test logging
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.write = MagicMock()
            
            # Create handlers with different formatters and set stream to mocked stdout
            colored_handler = logging.StreamHandler(mock_stdout)
            colored_handler.setFormatter(ColoredTextFormatter(color_mode="always"))
            
            plain_handler = logging.StreamHandler(mock_stdout)
            plain_handler.setFormatter(PlainTextFormatter())
            
            # Add handlers to logger
            logger.addHandler(colored_handler)
            logger.addHandler(plain_handler)
            
            # Test logging
            logger.info("Test message")
            
            # Verify that write was called (formatters worked)
            assert mock_stdout.write.called


if __name__ == "__main__":
    pytest.main([__file__]) 