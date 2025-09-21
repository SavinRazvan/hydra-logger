"""
Tests for hydra_logger.types.levels module.
"""

import pytest
import logging
from hydra_logger.types.levels import LogLevel, LogLevelManager


class TestLogLevel:
    """Test LogLevel enum functionality."""
    
    def test_log_level_enum_values(self):
        """Test that LogLevel enum has correct values matching Python logging."""
        assert LogLevel.NOTSET == 0
        assert LogLevel.DEBUG == 10
        assert LogLevel.INFO == 20
        assert LogLevel.WARNING == 30
        assert LogLevel.ERROR == 40
        assert LogLevel.CRITICAL == 50
    
    def test_log_level_matches_python_logging(self):
        """Test that LogLevel values match Python's standard logging levels."""
        assert LogLevel.NOTSET == logging.NOTSET
        assert LogLevel.DEBUG == logging.DEBUG
        assert LogLevel.INFO == logging.INFO
        assert LogLevel.WARNING == logging.WARNING
        assert LogLevel.ERROR == logging.ERROR
        assert LogLevel.CRITICAL == logging.CRITICAL
    
    def test_log_level_enum_names(self):
        """Test that LogLevel enum has correct names matching Python logging."""
        assert LogLevel.NOTSET.name == "NOTSET"
        assert LogLevel.DEBUG.name == "DEBUG"
        assert LogLevel.INFO.name == "INFO"
        assert LogLevel.WARNING.name == "WARNING"
        assert LogLevel.ERROR.name == "ERROR"
        assert LogLevel.CRITICAL.name == "CRITICAL"
    
    def test_log_level_comparison(self):
        """Test LogLevel comparison operations."""
        # Test less than
        assert LogLevel.NOTSET < LogLevel.DEBUG
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR
        assert LogLevel.ERROR < LogLevel.CRITICAL
        
        # Test greater than
        assert LogLevel.DEBUG > LogLevel.NOTSET
        assert LogLevel.INFO > LogLevel.DEBUG
        assert LogLevel.WARNING > LogLevel.INFO
        assert LogLevel.ERROR > LogLevel.WARNING
        assert LogLevel.CRITICAL > LogLevel.ERROR
        
        # Test equal
        assert LogLevel.NOTSET == LogLevel.NOTSET
        assert LogLevel.DEBUG == LogLevel.DEBUG
        assert LogLevel.INFO == LogLevel.INFO
    
    def test_log_level_str_representation(self):
        """Test LogLevel string representation."""
        assert str(LogLevel.NOTSET) == "0"
        assert str(LogLevel.DEBUG) == "10"
        assert str(LogLevel.INFO) == "20"
        assert str(LogLevel.WARNING) == "30"
        assert str(LogLevel.ERROR) == "40"
        assert str(LogLevel.CRITICAL) == "50"
    
    def test_log_level_repr(self):
        """Test LogLevel repr representation."""
        assert repr(LogLevel.NOTSET) == "<LogLevel.NOTSET: 0>"
        assert repr(LogLevel.DEBUG) == "<LogLevel.DEBUG: 10>"
        assert repr(LogLevel.INFO) == "<LogLevel.INFO: 20>"
        assert repr(LogLevel.WARNING) == "<LogLevel.WARNING: 30>"
        assert repr(LogLevel.ERROR) == "<LogLevel.ERROR: 40>"
        assert repr(LogLevel.CRITICAL) == "<LogLevel.CRITICAL: 50>"


class TestLogLevelManager:
    """Test LogLevelManager functionality."""
    
    def test_get_name(self):
        """Test LogLevelManager get_name method."""
        assert LogLevelManager.get_name(LogLevel.NOTSET) == "NOTSET"
        assert LogLevelManager.get_name(LogLevel.DEBUG) == "DEBUG"
        assert LogLevelManager.get_name(LogLevel.INFO) == "INFO"
        assert LogLevelManager.get_name(LogLevel.WARNING) == "WARNING"
        assert LogLevelManager.get_name(LogLevel.ERROR) == "ERROR"
        assert LogLevelManager.get_name(LogLevel.CRITICAL) == "CRITICAL"
    
    def test_get_level_from_string(self):
        """Test LogLevelManager get_level from string."""
        assert LogLevelManager.get_level("NOTSET") == LogLevel.NOTSET
        assert LogLevelManager.get_level("DEBUG") == LogLevel.DEBUG
        assert LogLevelManager.get_level("INFO") == LogLevel.INFO
        assert LogLevelManager.get_level("WARNING") == LogLevel.WARNING
        assert LogLevelManager.get_level("ERROR") == LogLevel.ERROR
        assert LogLevelManager.get_level("CRITICAL") == LogLevel.CRITICAL
    
    def test_get_level_case_insensitive(self):
        """Test LogLevelManager get_level case insensitive."""
        assert LogLevelManager.get_level("notset") == LogLevel.NOTSET
        assert LogLevelManager.get_level("NotSet") == LogLevel.NOTSET
        assert LogLevelManager.get_level("NOTSET") == LogLevel.NOTSET
        
        assert LogLevelManager.get_level("debug") == LogLevel.DEBUG
        assert LogLevelManager.get_level("Debug") == LogLevel.DEBUG
        assert LogLevelManager.get_level("DEBUG") == LogLevel.DEBUG
        
        assert LogLevelManager.get_level("error") == LogLevel.ERROR
        assert LogLevelManager.get_level("Error") == LogLevel.ERROR
        assert LogLevelManager.get_level("ERROR") == LogLevel.ERROR
    
    def test_get_level_from_int(self):
        """Test LogLevelManager get_level from integer."""
        assert LogLevelManager.get_level(0) == LogLevel.NOTSET
        assert LogLevelManager.get_level(10) == LogLevel.DEBUG
        assert LogLevelManager.get_level(20) == LogLevel.INFO
        assert LogLevelManager.get_level(30) == LogLevel.WARNING
        assert LogLevelManager.get_level(40) == LogLevel.ERROR
        assert LogLevelManager.get_level(50) == LogLevel.CRITICAL
    
    def test_get_level_from_enum(self):
        """Test LogLevelManager get_level from LogLevel enum."""
        assert LogLevelManager.get_level(LogLevel.NOTSET) == LogLevel.NOTSET
        assert LogLevelManager.get_level(LogLevel.DEBUG) == LogLevel.DEBUG
        assert LogLevelManager.get_level(LogLevel.INFO) == LogLevel.INFO
        assert LogLevelManager.get_level(LogLevel.WARNING) == LogLevel.WARNING
        assert LogLevelManager.get_level(LogLevel.ERROR) == LogLevel.ERROR
        assert LogLevelManager.get_level(LogLevel.CRITICAL) == LogLevel.CRITICAL
    
    def test_get_level_invalid_string(self):
        """Test LogLevelManager get_level with invalid string."""
        # Should return INFO as default for invalid strings
        assert LogLevelManager.get_level("INVALID") == LogLevel.INFO
        assert LogLevelManager.get_level("") == LogLevel.INFO
        assert LogLevelManager.get_level("debug_info") == LogLevel.INFO
    
    def test_get_level_invalid_int(self):
        """Test LogLevelManager get_level with invalid integer."""
        # Should return the integer as-is for invalid integers
        assert LogLevelManager.get_level(99) == 99
        assert LogLevelManager.get_level(-1) == -1
    
    def test_is_valid_level(self):
        """Test LogLevelManager is_valid_level method."""
        # Valid levels
        assert LogLevelManager.is_valid_level(LogLevel.NOTSET) is True
        assert LogLevelManager.is_valid_level(LogLevel.DEBUG) is True
        assert LogLevelManager.is_valid_level("DEBUG") is True
        assert LogLevelManager.is_valid_level(10) is True
        
        # Invalid levels
        assert LogLevelManager.is_valid_level("INVALID") is False
        assert LogLevelManager.is_valid_level(99) is False
        assert LogLevelManager.is_valid_level("") is False
    
    def test_all_levels(self):
        """Test LogLevelManager all_levels method."""
        all_levels = LogLevelManager.all_levels()
        
        assert len(all_levels) == 6  # NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
        assert LogLevel.NOTSET in all_levels
        assert LogLevel.DEBUG in all_levels
        assert LogLevel.INFO in all_levels
        assert LogLevel.WARNING in all_levels
        assert LogLevel.ERROR in all_levels
        assert LogLevel.CRITICAL in all_levels
    
    def test_all_names(self):
        """Test LogLevelManager all_names method."""
        all_names = LogLevelManager.all_names()
        
        assert len(all_names) >= 6  # At least the basic levels
        assert "DEBUG" in all_names
        assert "INFO" in all_names
        assert "WARNING" in all_names
        assert "ERROR" in all_names
        assert "CRITICAL" in all_names
        assert "WARN" in all_names  # Alias
        assert "FATAL" in all_names  # Alias
    
    def test_get_color(self):
        """Test LogLevelManager get_color method."""
        # NOTSET might not have a color defined, so we test what's available
        assert LogLevelManager.get_color(LogLevel.DEBUG) == "cyan"
        assert LogLevelManager.get_color(LogLevel.INFO) == "green"
        assert LogLevelManager.get_color(LogLevel.WARNING) == "yellow"
        assert LogLevelManager.get_color(LogLevel.ERROR) == "red"
        assert LogLevelManager.get_color(LogLevel.CRITICAL) == "bright_red"
    
    def test_get_color_from_string(self):
        """Test LogLevelManager get_color from string."""
        assert LogLevelManager.get_color("DEBUG") == "cyan"
        assert LogLevelManager.get_color("INFO") == "green"
        assert LogLevelManager.get_color("WARNING") == "yellow"
        assert LogLevelManager.get_color("ERROR") == "red"
        assert LogLevelManager.get_color("CRITICAL") == "bright_red"
    
    def test_is_enabled(self):
        """Test LogLevelManager is_enabled method."""
        # NOTSET level should be enabled for all levels (lowest level)
        assert LogLevelManager.is_enabled(LogLevel.NOTSET, LogLevel.NOTSET) is True
        assert LogLevelManager.is_enabled(LogLevel.NOTSET, LogLevel.DEBUG) is True
        assert LogLevelManager.is_enabled(LogLevel.NOTSET, LogLevel.INFO) is True
        assert LogLevelManager.is_enabled(LogLevel.NOTSET, LogLevel.WARNING) is True
        assert LogLevelManager.is_enabled(LogLevel.NOTSET, LogLevel.ERROR) is True
        assert LogLevelManager.is_enabled(LogLevel.NOTSET, LogLevel.CRITICAL) is True
        
        # DEBUG level should be enabled for DEBUG and above
        assert LogLevelManager.is_enabled(LogLevel.DEBUG, LogLevel.NOTSET) is False
        assert LogLevelManager.is_enabled(LogLevel.DEBUG, LogLevel.DEBUG) is True
        assert LogLevelManager.is_enabled(LogLevel.DEBUG, LogLevel.INFO) is True
        assert LogLevelManager.is_enabled(LogLevel.DEBUG, LogLevel.WARNING) is True
        assert LogLevelManager.is_enabled(LogLevel.DEBUG, LogLevel.ERROR) is True
        assert LogLevelManager.is_enabled(LogLevel.DEBUG, LogLevel.CRITICAL) is True
        
        # INFO level should be enabled for INFO and above
        assert LogLevelManager.is_enabled(LogLevel.INFO, LogLevel.NOTSET) is False
        assert LogLevelManager.is_enabled(LogLevel.INFO, LogLevel.DEBUG) is False
        assert LogLevelManager.is_enabled(LogLevel.INFO, LogLevel.INFO) is True
        assert LogLevelManager.is_enabled(LogLevel.INFO, LogLevel.WARNING) is True
        assert LogLevelManager.is_enabled(LogLevel.INFO, LogLevel.ERROR) is True
        assert LogLevelManager.is_enabled(LogLevel.INFO, LogLevel.CRITICAL) is True
        
        # CRITICAL level should only be enabled for CRITICAL
        assert LogLevelManager.is_enabled(LogLevel.CRITICAL, LogLevel.NOTSET) is False
        assert LogLevelManager.is_enabled(LogLevel.CRITICAL, LogLevel.DEBUG) is False
        assert LogLevelManager.is_enabled(LogLevel.CRITICAL, LogLevel.INFO) is False
        assert LogLevelManager.is_enabled(LogLevel.CRITICAL, LogLevel.WARNING) is False
        assert LogLevelManager.is_enabled(LogLevel.CRITICAL, LogLevel.ERROR) is False
        assert LogLevelManager.is_enabled(LogLevel.CRITICAL, LogLevel.CRITICAL) is True
    
    def test_is_enabled_with_strings(self):
        """Test LogLevelManager is_enabled with string levels."""
        assert LogLevelManager.is_enabled("INFO", "DEBUG") is False
        assert LogLevelManager.is_enabled("INFO", "INFO") is True
        assert LogLevelManager.is_enabled("INFO", "WARNING") is True
        assert LogLevelManager.is_enabled("INFO", "ERROR") is True
        assert LogLevelManager.is_enabled("INFO", "CRITICAL") is True
    
    def test_normalize_level(self):
        """Test LogLevelManager normalize_level method."""
        assert LogLevelManager.normalize_level("DEBUG") == LogLevel.DEBUG
        assert LogLevelManager.normalize_level(20) == LogLevel.INFO
        assert LogLevelManager.normalize_level(LogLevel.WARNING) == LogLevel.WARNING
        
        # Invalid levels should default to INFO
        assert LogLevelManager.normalize_level("INVALID") == LogLevel.INFO
        assert LogLevelManager.normalize_level(99) == LogLevel.INFO


class TestLogLevelIntegration:
    """Integration tests for LogLevel and LogLevelManager."""
    
    def test_level_roundtrip(self):
        """Test converting level to string and back."""
        levels = [LogLevel.NOTSET, LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        
        for level in levels:
            # Convert to string
            level_name = LogLevelManager.get_name(level)
            
            # Convert back to level
            converted_level = LogLevelManager.get_level(level_name)
            
            assert converted_level == level
    
    def test_level_comparison_consistency(self):
        """Test that level comparisons are consistent across different representations."""
        levels = [
            (LogLevel.NOTSET, "NOTSET", 0),
            (LogLevel.DEBUG, "DEBUG", 10),
            (LogLevel.INFO, "INFO", 20),
            (LogLevel.WARNING, "WARNING", 30),
            (LogLevel.ERROR, "ERROR", 40),
            (LogLevel.CRITICAL, "CRITICAL", 50)
        ]
        
        for i, (enum_level, str_level, int_level) in enumerate(levels):
            for j, (other_enum, other_str, other_int) in enumerate(levels):
                if i < j:
                    # Lower levels should be less than higher levels
                    assert enum_level < other_enum
                    assert LogLevelManager.get_level(str_level) < LogLevelManager.get_level(other_str)
                    assert int_level < other_int
                elif i > j:
                    # Higher levels should be greater than lower levels
                    assert enum_level > other_enum
                    assert LogLevelManager.get_level(str_level) > LogLevelManager.get_level(other_str)
                    assert int_level > other_int
                else:
                    # Same levels should be equal
                    assert enum_level == other_enum
                    assert LogLevelManager.get_level(str_level) == LogLevelManager.get_level(other_str)
                    assert int_level == other_int


class TestConvenienceFunctions:
    """Test convenience functions for backward compatibility."""
    
    def test_get_level_name_function(self):
        """Test get_level_name convenience function."""
        from hydra_logger.types.levels import get_level_name
        
        # Test with LogLevel enum
        assert get_level_name(LogLevel.INFO) == "INFO"
        assert get_level_name(LogLevel.ERROR) == "ERROR"
        assert get_level_name(LogLevel.DEBUG) == "DEBUG"
        
        # Test with integer
        assert get_level_name(20) == "INFO"
        assert get_level_name(40) == "ERROR"
        assert get_level_name(10) == "DEBUG"
        
        # Test with string (should return uppercase)
        assert get_level_name("info") == "INFO"
        assert get_level_name("error") == "ERROR"
    
    def test_get_level_function(self):
        """Test get_level convenience function."""
        from hydra_logger.types.levels import get_level
        
        # Test with string
        assert get_level("INFO") == 20
        assert get_level("ERROR") == 40
        assert get_level("DEBUG") == 10
        assert get_level("info") == 20  # Case insensitive
        
        # Test with integer
        assert get_level(20) == 20
        assert get_level(40) == 40
        assert get_level(10) == 10
        
        # Test with LogLevel enum
        assert get_level(LogLevel.INFO) == 20
        assert get_level(LogLevel.ERROR) == 40
        assert get_level(LogLevel.DEBUG) == 10
        
        # Test with invalid input (should return INFO)
        assert get_level("INVALID") == 20
        assert get_level(999) == 999  # Returns the integer as-is
        
        # Test with LogLevel enum (should return int value)
        assert get_level(LogLevel.INFO) == 20
        assert get_level(LogLevel.ERROR) == 40
        
        # Test with invalid type (should return INFO)
        assert get_level(None) == 20
        assert get_level(1.5) == 20
        assert get_level(object()) == 20
    
    def test_is_valid_level_function(self):
        """Test is_valid_level convenience function."""
        from hydra_logger.types.levels import is_valid_level
        
        # Test with valid string levels
        assert is_valid_level("INFO") is True
        assert is_valid_level("ERROR") is True
        assert is_valid_level("DEBUG") is True
        assert is_valid_level("info") is True  # Case insensitive
        
        # Test with valid integer levels
        assert is_valid_level(20) is True
        assert is_valid_level(40) is True
        assert is_valid_level(10) is True
        
        # Test with LogLevel enum
        assert is_valid_level(LogLevel.INFO) is True
        assert is_valid_level(LogLevel.ERROR) is True
        assert is_valid_level(LogLevel.DEBUG) is True
        
        # Test with invalid inputs
        assert is_valid_level("INVALID") is False
        assert is_valid_level(999) is False
        assert is_valid_level(None) is False
        assert is_valid_level([]) is False
    
    def test_all_levels_function(self):
        """Test all_levels convenience function."""
        from hydra_logger.types.levels import all_levels
        
        levels = all_levels()
        assert isinstance(levels, list)
        assert len(levels) == 6  # NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
        assert 0 in levels  # NOTSET
        assert 10 in levels  # DEBUG
        assert 20 in levels  # INFO
        assert 30 in levels  # WARNING
        assert 40 in levels  # ERROR
        assert 50 in levels  # CRITICAL
    
    def test_all_level_names_function(self):
        """Test all_level_names convenience function."""
        from hydra_logger.types.levels import all_level_names
        
        names = all_level_names()
        assert isinstance(names, list)
        assert len(names) >= 6  # At least NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
        assert "NOTSET" in names
        assert "DEBUG" in names
        assert "INFO" in names
        assert "WARNING" in names
        assert "ERROR" in names
        assert "CRITICAL" in names


class TestLogLevelManagerEdgeCases:
    """Test LogLevelManager edge cases for 100% coverage."""
    
    def test_get_level_with_loglevel_enum(self):
        """Test get_level with LogLevel enum (line 76)."""
        # This should hit line 76: return int(level)
        assert LogLevelManager.get_level(LogLevel.INFO) == 20
        assert LogLevelManager.get_level(LogLevel.ERROR) == 40
        assert LogLevelManager.get_level(LogLevel.DEBUG) == 10
    
    def test_get_level_with_invalid_type(self):
        """Test get_level with invalid type (line 80)."""
        # This should hit line 80: return LogLevel.INFO
        assert LogLevelManager.get_level(None) == 20
        assert LogLevelManager.get_level(1.5) == 20
        assert LogLevelManager.get_level(object()) == 20
    
    def test_is_valid_level_with_loglevel_enum(self):
        """Test is_valid_level with LogLevel enum (line 88)."""
        # This should hit line 88: return True
        assert LogLevelManager.is_valid_level(LogLevel.INFO) is True
        assert LogLevelManager.is_valid_level(LogLevel.ERROR) is True
        assert LogLevelManager.is_valid_level(LogLevel.DEBUG) is True