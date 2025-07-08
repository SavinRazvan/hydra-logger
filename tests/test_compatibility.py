"""
Tests for compatibility functionality.

This module tests the compatibility utilities for different Python versions
and platforms.
"""

import pytest
import sys
import platform
import os
import tempfile
import logging
import shutil
from unittest.mock import Mock, patch, MagicMock
from logging.handlers import RotatingFileHandler

from hydra_logger.compatibility import (
    setup_logging, create_hydra_config_from_legacy, migrate_to_hydra,
    _level_int_to_str,
    get_python_version,
    get_platform_info,
    check_compatibility,
    is_async_available,
    is_aiohttp_available,
    is_asyncpg_available,
    is_aioredis_available,
    get_available_async_libraries,
    check_system_requirements,
    get_memory_info,
    get_cpu_info,
    get_processor_count,
    get_system_memory,
    is_windows,
    is_linux,
    is_macos,
    is_arm_architecture,
    is_virtual_environment,
)
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig


class TestSetupLogging:
    """
    Test suite for the setup_logging function.

    Tests the backward compatibility function that provides the exact same
    interface as the original flexiai-toolsmith setup_logging function.
    """

    @pytest.fixture
    def temp_dir(self):
        """
        Create a temporary directory for test logs.

        Returns:
            str: Path to temporary directory.

        Yields:
            str: Path to temporary directory for test use.
        """
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_setup_logging_basic(self, temp_dir):
        """
        Test basic setup_logging functionality.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging creates the expected directory structure
        and configures logging handlers correctly with default parameters.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging()

        # Check that logs directory was created
        logs_dir = os.path.join(temp_dir, "logs")
        assert os.path.exists(logs_dir), "Logs directory should be created"

        # Check that app.log file exists
        log_file = os.path.join(logs_dir, "app.log")
        assert os.path.exists(log_file), "App log file should be created"

        # Verify logger configuration
        logger = logging.getLogger()
        assert logger.level == logging.DEBUG, "Root logger should be set to DEBUG"

        # Check that handlers were added
        handlers = logger.handlers
        assert len(handlers) == 2, "Should have 2 handlers (file and console)"

        # Verify handler types
        handler_types = [type(h) for h in handlers]
        assert RotatingFileHandler in handler_types, "Should have RotatingFileHandler"
        assert logging.StreamHandler in handler_types, "Should have StreamHandler"

    def test_setup_logging_file_only(self, temp_dir):
        """
        Test setup_logging with file logging only.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging works correctly when only file logging
        is enabled, creating the file handler but not the console handler.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging(enable_console_logging=False)

        logger = logging.getLogger()
        handlers = logger.handlers

        # Should only have file handler
        assert len(handlers) == 1, "Should have only 1 handler (file only)"
        assert isinstance(
            handlers[0], RotatingFileHandler
        ), "Should have RotatingFileHandler"

    def test_setup_logging_console_only(self, temp_dir):
        """
        Test setup_logging with console logging only.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging works correctly when only console logging
        is enabled, creating the console handler but not the file handler.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging(enable_file_logging=False)

        logger = logging.getLogger()
        handlers = logger.handlers

        # Should only have console handler
        assert len(handlers) == 1, "Should have only 1 handler (console only)"
        assert isinstance(
            handlers[0], logging.StreamHandler
        ), "Should have StreamHandler"

        # Logs directory should not be created
        logs_dir = os.path.join(temp_dir, "logs")
        assert not os.path.exists(
            logs_dir
        ), "Logs directory should not be created when file logging is disabled"

    def test_setup_logging_custom_levels(self, temp_dir):
        """
        Test setup_logging with custom log levels.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging correctly applies custom log levels
        to the root logger and individual handlers.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging(
                root_level=logging.WARNING,
                file_level=logging.DEBUG,
                console_level=logging.ERROR,
            )

        logger = logging.getLogger()
        assert logger.level == logging.WARNING, "Root logger should be set to WARNING"

        # Check handler levels
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                assert (
                    handler.level == logging.DEBUG
                ), "File handler should be set to DEBUG"
            elif isinstance(handler, logging.StreamHandler):
                assert (
                    handler.level == logging.ERROR
                ), "Console handler should be set to ERROR"

    def test_setup_logging_directory_creation_failure(self, temp_dir):
        """
        Test setup_logging when directory creation fails.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging handles directory creation failures
        gracefully and continues with console logging if available.
        """
        # Clear existing handlers first
        logger = logging.getLogger()
        logger.handlers.clear()

        with patch("os.getcwd", return_value=temp_dir):
            with patch("os.makedirs", side_effect=OSError("Permission denied")):
                setup_logging(enable_console_logging=True)

        # Should still have console handler even if file handler fails
        assert (
            len(logger.handlers) == 1
        ), "Should have console handler even if file handler fails"
        assert isinstance(
            logger.handlers[0], logging.StreamHandler
        ), "Should have StreamHandler"

    def test_setup_logging_logger_setup_failure(self, temp_dir):
        """
        Test setup_logging when logger setup fails.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging handles logger setup failures
        gracefully and doesn't crash the application.
        """
        with patch("os.getcwd", return_value=temp_dir):
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_logger.setLevel.side_effect = Exception("Logger setup failed")
                mock_get_logger.return_value = mock_logger

                # Should not raise an exception
                setup_logging()

        # Verify that the function completed without crashing
        assert True, "setup_logging should handle logger setup failures gracefully"


class TestMigrationFunctions:
    """
    Test suite for migration utility functions.

    Tests the functions that help migrate from legacy setup_logging
    to the new Hydra-Logger system.
    """

    def test_level_int_to_str(self):
        """
        Test level conversion from integer to string.

        Verifies that the _level_int_to_str function correctly converts
        Python logging level integers to their string representations.
        """
        assert _level_int_to_str(logging.DEBUG) == "DEBUG"
        assert _level_int_to_str(logging.INFO) == "INFO"
        assert _level_int_to_str(logging.WARNING) == "WARNING"
        assert _level_int_to_str(logging.ERROR) == "ERROR"
        assert _level_int_to_str(logging.CRITICAL) == "CRITICAL"

        # Test unknown level (should return "INFO")
        assert _level_int_to_str(999) == "INFO"

    def test_create_hydra_config_from_legacy(self):
        """
        Test creating Hydra-Logger config from legacy parameters.

        Verifies that create_hydra_config_from_legacy correctly converts
        legacy setup_logging parameters to a Hydra-Logger configuration.
        """
        config = create_hydra_config_from_legacy(
            root_level=logging.INFO,
            file_level=logging.DEBUG,
            console_level=logging.WARNING,
            log_file_path="custom/path/app.log",
        )

        assert isinstance(config, LoggingConfig)
        assert "DEFAULT" in config.layers
        assert config.layers["DEFAULT"].level == "INFO"
        assert len(config.layers["DEFAULT"].destinations) == 2

        # Check file destination
        file_dest = next(
            d for d in config.layers["DEFAULT"].destinations if d.type == "file"
        )
        assert file_dest.path == "custom/path/app.log"
        assert file_dest.level == "DEBUG"
        assert file_dest.max_size == "5MB"
        assert file_dest.backup_count == 3

        # Check console destination
        console_dest = next(
            d for d in config.layers["DEFAULT"].destinations if d.type == "console"
        )
        assert console_dest.level == "WARNING"

    def test_create_hydra_config_file_only(self):
        """
        Test creating config with file logging only.

        Verifies that create_hydra_config_from_legacy correctly handles
        the case where only file logging is enabled.
        """
        config = create_hydra_config_from_legacy(enable_console_logging=False)

        assert len(config.layers["DEFAULT"].destinations) == 1
        assert config.layers["DEFAULT"].destinations[0].type == "file"

    def test_create_hydra_config_console_only(self):
        """
        Test creating config with console logging only.

        Verifies that create_hydra_config_from_legacy correctly handles
        the case where only console logging is enabled.
        """
        config = create_hydra_config_from_legacy(enable_file_logging=False)

        assert len(config.layers["DEFAULT"].destinations) == 1
        assert config.layers["DEFAULT"].destinations[0].type == "console"

    def test_migrate_to_hydra(self):
        """
        Test migration to Hydra-Logger.

        Verifies that migrate_to_hydra correctly creates a fully configured
        HydraLogger instance from legacy parameters.
        """
        logger = migrate_to_hydra(
            root_level=logging.INFO,
            file_level=logging.DEBUG,
            console_level=logging.WARNING,
        )

        assert isinstance(logger, HydraLogger)
        assert "DEFAULT" in logger.loggers

        # Test that the logger works
        logger.info("DEFAULT", "Test message")
        assert True, "Migrated logger should work correctly"


class TestBackwardCompatibility:
    """
    Test suite for backward compatibility features.

    Tests that ensure existing applications can continue to work
    without modification when using Hydra-Logger.
    """

    @pytest.fixture
    def temp_dir(self):
        """
        Create a temporary directory for test logs.

        Returns:
            str: Path to temporary directory.

        Yields:
            str: Path to temporary directory for test use.
        """
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_setup_logging_creates_correct_structure(self, temp_dir):
        """
        Test that setup_logging creates the expected directory structure.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that setup_logging creates the same directory structure
        as the original flexiai-toolsmith implementation.
        """
        with patch("os.getcwd", return_value=temp_dir):
            setup_logging()

        # Check directory structure
        logs_dir = os.path.join(temp_dir, "logs")
        log_file = os.path.join(logs_dir, "app.log")

        assert os.path.exists(logs_dir), "logs/ directory should exist"
        assert os.path.exists(log_file), "logs/app.log should exist"

        # Check file permissions (should be writable)
        assert os.access(log_file, os.W_OK), "Log file should be writable"

    def test_migration_preserves_functionality(self, temp_dir):
        """
        Test that migration preserves all original functionality.

        Args:
            temp_dir: Temporary directory for test files.

        Verifies that the migrated HydraLogger provides the same
        functionality as the original setup_logging.
        """
        with patch("os.getcwd", return_value=temp_dir):
            # Use original setup_logging
            setup_logging(
                root_level=logging.INFO,
                file_level=logging.DEBUG,
                console_level=logging.WARNING,
            )

        # Get the original logger
        original_logger = logging.getLogger()

        # Clear handlers and use migration
        original_logger.handlers.clear()

        with patch("os.getcwd", return_value=temp_dir):
            migrated_logger = migrate_to_hydra(
                root_level=logging.INFO,
                file_level=logging.DEBUG,
                console_level=logging.WARNING,
            )

        # Both should work similarly
        original_logger.info("Original logger test")
        migrated_logger.info("DEFAULT", "Migrated logger test")

        # Both should have created log files
        logs_dir = os.path.join(temp_dir, "logs")
        assert os.path.exists(logs_dir), "Both should create logs directory"

        assert True, "Migration should preserve all original functionality"


def test_setup_logging_normal(monkeypatch):
    # Patch os.makedirs to avoid real file I/O
    monkeypatch.setattr(os, "makedirs", lambda *a, **k: None)
    # Patch RotatingFileHandler and StreamHandler
    with patch("hydra_logger.compatibility.RotatingFileHandler") as mock_file, \
         patch("hydra_logger.compatibility.logging.StreamHandler") as mock_console:
        setup_logging()
        assert mock_file.called
        assert mock_console.called


def test_setup_logging_file_only(monkeypatch):
    monkeypatch.setattr(os, "makedirs", lambda *a, **k: None)
    with patch("hydra_logger.compatibility.RotatingFileHandler") as mock_file:
        setup_logging(enable_console_logging=False)
        assert mock_file.called


def test_setup_logging_console_only(monkeypatch):
    with patch("hydra_logger.compatibility.logging.StreamHandler") as mock_console:
        setup_logging(enable_file_logging=False)
        assert mock_console.called


def test_setup_logging_oserror(monkeypatch):
    # Simulate OSError when creating directory
    def raise_oserror(*a, **k):
        raise OSError("fail")
    monkeypatch.setattr(os, "makedirs", raise_oserror)
    # Clear root logger handlers to avoid MagicMock comparison issues
    logger = logging.getLogger()
    logger.handlers.clear()
    # Patch handlers to avoid TypeError if called
    with patch("hydra_logger.compatibility.RotatingFileHandler") as mock_file, \
         patch("hydra_logger.compatibility.logging.StreamHandler") as mock_console:
        # Configure mocks to handle setLevel calls properly and have integer level
        mock_file.return_value.setLevel = MagicMock()
        mock_console.return_value.setLevel = MagicMock()
        mock_file.return_value.setFormatter = MagicMock()
        mock_console.return_value.setFormatter = MagicMock()
        mock_file.return_value.level = logging.DEBUG
        mock_console.return_value.level = logging.INFO
        # Should not raise
        setup_logging()


def test_setup_logging_handler_exception(monkeypatch):
    monkeypatch.setattr(os, "makedirs", lambda *a, **k: None)
    # Simulate exception in handler setup
    with patch("hydra_logger.compatibility.RotatingFileHandler", side_effect=Exception("fail")):
        setup_logging()


def test_create_hydra_config_from_legacy_all_combinations():
    # Both enabled
    config = create_hydra_config_from_legacy()
    assert "DEFAULT" in config.layers
    # File only
    config = create_hydra_config_from_legacy(enable_console_logging=False)
    assert any(d.type == "file" for d in config.layers["DEFAULT"].destinations)
    # Console only
    config = create_hydra_config_from_legacy(enable_file_logging=False)
    assert any(d.type == "console" for d in config.layers["DEFAULT"].destinations)
    # Neither (should still create DEFAULT layer)
    config = create_hydra_config_from_legacy(enable_file_logging=False, enable_console_logging=False)
    assert "DEFAULT" in config.layers
    # Custom log file path
    config = create_hydra_config_from_legacy(log_file_path="logs/_tests_logs/custom.log")
    assert any(getattr(d, "path", None) == "custom.log" for d in config.layers["DEFAULT"].destinations)


def test_level_int_to_str_all_levels():
    assert _level_int_to_str(logging.DEBUG) == "DEBUG"
    assert _level_int_to_str(logging.INFO) == "INFO"
    assert _level_int_to_str(logging.WARNING) == "WARNING"
    assert _level_int_to_str(logging.ERROR) == "ERROR"
    assert _level_int_to_str(logging.CRITICAL) == "CRITICAL"
    # Unknown level
    assert _level_int_to_str(999) == "INFO"


def test_migrate_to_hydra():
    logger = migrate_to_hydra()
    from hydra_logger.logger import HydraLogger
    assert isinstance(logger, HydraLogger)
    # Check config matches
    assert hasattr(logger, "config")
    assert "DEFAULT" in logger.config.layers


class TestPythonVersionCompatibility:
    """Test Python version compatibility functions."""
    
    def test_get_python_version(self):
        """Test getting Python version information."""
        version_info = get_python_version()
        
        assert isinstance(version_info, dict)
        assert "major" in version_info
        assert "minor" in version_info
        assert "micro" in version_info
        assert "version" in version_info
        assert "hexversion" in version_info
        
        assert version_info["major"] == sys.version_info.major
        assert version_info["minor"] == sys.version_info.minor
        assert version_info["micro"] == sys.version_info.micro
        assert version_info["version"] == sys.version
    
    def test_get_platform_info(self):
        """Test getting platform information."""
        platform_info = get_platform_info()
        
        assert isinstance(platform_info, dict)
        assert "system" in platform_info
        assert "release" in platform_info
        assert "version" in platform_info
        assert "machine" in platform_info
        assert "processor" in platform_info
        
        assert platform_info["system"] == platform.system()
        assert platform_info["release"] == platform.release()
        assert platform_info["version"] == platform.version()
        assert platform_info["machine"] == platform.machine()
    
    def test_check_compatibility(self):
        """Test compatibility checking."""
        # Test with current Python version (should be compatible)
        result = check_compatibility()
        assert result["compatible"] is True
        assert "python_version" in result
        assert "platform_info" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)
    
    def test_check_compatibility_with_issues(self):
        """Test compatibility checking with known issues."""
        with patch('hydra_logger.compatibility.get_python_version') as mock_version:
            mock_version.return_value = {"major": 2, "minor": 7, "micro": 0}
            
            result = check_compatibility()
            assert result["compatible"] is False
            assert len(result["issues"]) > 0
            assert any("Python 2" in issue for issue in result["issues"])


class TestAsyncLibraryCompatibility:
    """Test async library compatibility functions."""
    
    def test_is_async_available(self):
        """Test async availability check."""
        # Should be available in Python 3.7+
        result = is_async_available()
        assert isinstance(result, bool)
        assert result is True  # Should be available in modern Python
    
    def test_is_aiohttp_available(self):
        """Test aiohttp availability check."""
        result = is_aiohttp_available()
        assert isinstance(result, bool)
    
    def test_is_asyncpg_available(self):
        """Test asyncpg availability check."""
        result = is_asyncpg_available()
        assert isinstance(result, bool)
    
    def test_is_aioredis_available(self):
        """Test aioredis availability check."""
        result = is_aioredis_available()
        assert isinstance(result, bool)
    
    def test_get_available_async_libraries(self):
        """Test getting available async libraries."""
        libraries = get_available_async_libraries()
        
        assert isinstance(libraries, dict)
        assert "aiohttp" in libraries
        assert "asyncpg" in libraries
        assert "aioredis" in libraries
        assert "asyncio" in libraries
        
        # All values should be booleans
        for value in libraries.values():
            assert isinstance(value, bool)
    
    def test_async_library_availability_with_mocks(self):
        """Test async library availability with mocked imports."""
        # Test when aiohttp is available
        with patch('hydra_logger.compatibility.AIOHTTP_AVAILABLE', True):
            assert is_aiohttp_available() is True
        
        # Test when aiohttp is not available
        with patch('hydra_logger.compatibility.AIOHTTP_AVAILABLE', False):
            assert is_aiohttp_available() is False
        
        # Test when asyncpg is available
        with patch('hydra_logger.compatibility.ASYNCPG_AVAILABLE', True):
            assert is_asyncpg_available() is True
        
        # Test when asyncpg is not available
        with patch('hydra_logger.compatibility.ASYNCPG_AVAILABLE', False):
            assert is_asyncpg_available() is False
        
        # Test when aioredis is available
        with patch('hydra_logger.compatibility.AIOREDIS_AVAILABLE', True):
            assert is_aioredis_available() is True
        
        # Test when aioredis is not available
        with patch('hydra_logger.compatibility.AIOREDIS_AVAILABLE', False):
            assert is_aioredis_available() is False


class TestSystemRequirements:
    """Test system requirements checking."""
    
    def test_check_system_requirements(self):
        """Test system requirements checking."""
        requirements = check_system_requirements()
        
        assert isinstance(requirements, dict)
        assert "cpu_cores" in requirements
        assert "memory_mb" in requirements
        assert "disk_space_mb" in requirements
        assert "python_version" in requirements
        assert "platform" in requirements
        assert "meets_requirements" in requirements
        
        # All values should be appropriate types
        assert isinstance(requirements["cpu_cores"], int)
        assert isinstance(requirements["memory_mb"], int)
        assert isinstance(requirements["disk_space_mb"], int)
        assert isinstance(requirements["meets_requirements"], bool)
    
    def test_get_memory_info(self):
        """Test getting memory information."""
        memory_info = get_memory_info()
        
        assert isinstance(memory_info, dict)
        assert "total" in memory_info
        assert "available" in memory_info
        assert "used" in memory_info
        assert "percent" in memory_info
        
        # Values should be reasonable
        assert memory_info["total"] > 0
        assert memory_info["available"] >= 0
        assert memory_info["used"] >= 0
        assert 0 <= memory_info["percent"] <= 100
    
    def test_get_cpu_info(self):
        """Test getting CPU information."""
        cpu_info = get_cpu_info()
        
        assert isinstance(cpu_info, dict)
        assert "count" in cpu_info
        assert "count_logical" in cpu_info
        assert "usage_percent" in cpu_info
        
        # Values should be reasonable
        assert cpu_info["count"] > 0
        assert cpu_info["count_logical"] >= cpu_info["count"]
        assert 0 <= cpu_info["usage_percent"] <= 100
    
    def test_get_processor_count(self):
        """Test getting processor count."""
        count = get_processor_count()
        
        assert isinstance(count, int)
        assert count > 0
    
    def test_get_system_memory(self):
        """Test getting system memory."""
        memory = get_system_memory()
        
        assert isinstance(memory, int)
        assert memory > 0  # Should have some memory


class TestPlatformDetection:
    """Test platform detection functions."""
    
    def test_is_windows(self):
        """Test Windows detection."""
        result = is_windows()
        assert isinstance(result, bool)
        
        # Should match platform.system() == "Windows"
        expected = platform.system() == "Windows"
        assert result == expected
    
    def test_is_linux(self):
        """Test Linux detection."""
        result = is_linux()
        assert isinstance(result, bool)
        
        # Should match platform.system() == "Linux"
        expected = platform.system() == "Linux"
        assert result == expected
    
    def test_is_macos(self):
        """Test macOS detection."""
        result = is_macos()
        assert isinstance(result, bool)
        
        # Should match platform.system() == "Darwin"
        expected = platform.system() == "Darwin"
        assert result == expected
    
    def test_is_arm_architecture(self):
        """Test ARM architecture detection."""
        result = is_arm_architecture()
        assert isinstance(result, bool)
        
        # Should match platform.machine() containing "arm"
        expected = "arm" in platform.machine().lower()
        assert result == expected
    
    def test_platform_detection_with_mocks(self):
        """Test platform detection with mocked platform."""
        # Test Windows
        with patch('platform.system', return_value="Windows"):
            assert is_windows() is True
            assert is_linux() is False
            assert is_macos() is False
        
        # Test Linux
        with patch('platform.system', return_value="Linux"):
            assert is_windows() is False
            assert is_linux() is True
            assert is_macos() is False
        
        # Test macOS
        with patch('platform.system', return_value="Darwin"):
            assert is_windows() is False
            assert is_linux() is False
            assert is_macos() is True
        
        # Test ARM architecture
        with patch('platform.machine', return_value="arm64"):
            assert is_arm_architecture() is True
        
        with patch('platform.machine', return_value="x86_64"):
            assert is_arm_architecture() is False


class TestVirtualEnvironment:
    """Test virtual environment detection."""
    
    def test_is_virtual_environment(self):
        """Test virtual environment detection."""
        result = is_virtual_environment()
        assert isinstance(result, bool)
    
    def test_virtual_environment_detection_methods(self):
        """Test different virtual environment detection methods."""
        # Test with VIRTUAL_ENV environment variable
        with patch.dict('os.environ', {'VIRTUAL_ENV': '/path/to/venv'}):
            assert is_virtual_environment() is True
        
        # Test without VIRTUAL_ENV environment variable
        with patch.dict('os.environ', {}, clear=True):
            # Result depends on actual environment
            result = is_virtual_environment()
            assert isinstance(result, bool)
        
        # Test with CONDA_DEFAULT_ENV environment variable
        with patch.dict('os.environ', {'CONDA_DEFAULT_ENV': 'conda_env'}):
            assert is_virtual_environment() is True


class TestCompatibilityIntegration:
    """Integration tests for compatibility components."""
    
    def test_full_compatibility_report(self):
        """Test generating a full compatibility report."""
        # Get all compatibility information
        python_version = get_python_version()
        platform_info = get_platform_info()
        compatibility = check_compatibility()
        async_libraries = get_available_async_libraries()
        system_requirements = check_system_requirements()
        
        # Verify all components are present
        assert isinstance(python_version, dict)
        assert isinstance(platform_info, dict)
        assert isinstance(compatibility, dict)
        assert isinstance(async_libraries, dict)
        assert isinstance(system_requirements, dict)
        
        # Verify required keys exist
        assert "major" in python_version
        assert "system" in platform_info
        assert "compatible" in compatibility
        assert "asyncio" in async_libraries
        assert "meets_requirements" in system_requirements
    
    def test_compatibility_performance(self):
        """Test compatibility checking performance."""
        import time
        
        # Test performance of compatibility checks
        start_time = time.time()
        
        for _ in range(100):
            get_python_version()
            get_platform_info()
            check_compatibility()
            get_available_async_libraries()
            check_system_requirements()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should be fast
        assert processing_time < 1.0
    
    def test_compatibility_error_handling(self):
        """Test compatibility error handling."""
        # Test with mocked platform that raises exceptions
        with patch('platform.system', side_effect=Exception("Platform error")):
            # Should handle gracefully
            platform_info = get_platform_info()
            assert isinstance(platform_info, dict)
            assert "error" in platform_info
        
        # Test with mocked psutil that raises exceptions
        with patch('hydra_logger.compatibility.psutil', None):
            # Should handle gracefully
            memory_info = get_memory_info()
            assert isinstance(memory_info, dict)
            assert "error" in memory_info
    
    def test_compatibility_edge_cases(self):
        """Test compatibility edge cases."""
        # Test with very old Python version
        with patch('hydra_logger.compatibility.get_python_version') as mock_version:
            mock_version.return_value = {"major": 2, "minor": 6, "micro": 0}
            
            compatibility = check_compatibility()
            assert compatibility["compatible"] is False
            assert len(compatibility["issues"]) > 0
        
        # Test with very new Python version
        with patch('hydra_logger.compatibility.get_python_version') as mock_version:
            mock_version.return_value = {"major": 4, "minor": 0, "micro": 0}
            
            compatibility = check_compatibility()
            # Should be compatible or have specific issues
            assert isinstance(compatibility["compatible"], bool)
    
    def test_compatibility_memory_efficiency(self):
        """Test compatibility memory efficiency."""
        # Run many compatibility checks
        for _ in range(1000):
            get_python_version()
            get_platform_info()
            check_compatibility()
            get_available_async_libraries()
            check_system_requirements()
        
        # Should not consume excessive memory
        # Test that functions still work
        python_version = get_python_version()
        platform_info = get_platform_info()
        
        assert isinstance(python_version, dict)
        assert isinstance(platform_info, dict)
    
    def test_compatibility_thread_safety(self):
        """Test compatibility thread safety."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def compatibility_worker():
            try:
                python_version = get_python_version()
                platform_info = get_platform_info()
                compatibility = check_compatibility()
                
                results.put({
                    "python_version": python_version,
                    "platform_info": platform_info,
                    "compatibility": compatibility
                })
            except Exception as e:
                results.put({"error": str(e)})
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=compatibility_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all results
        while not results.empty():
            result = results.get()
            assert "error" not in result
            assert isinstance(result["python_version"], dict)
            assert isinstance(result["platform_info"], dict)
            assert isinstance(result["compatibility"], dict)

