#!/usr/bin/env python3
"""
Manual module import and functionality checks for Hydra Logger.

This script can:
- Check if all major modules can be imported
- Run basic functionality tests for each module

Usage:
  python manual_module_checks.py [imports|functionality|all]

Default is 'all'.
"""
import sys
import os
import tempfile
import shutil
import asyncio
from pathlib import Path

def test_module_import(module_name, description):
    print(f"🔍 Testing {description} ({module_name})...")
    try:
        __import__(module_name)
        print(f"✅ {description} import successful")
        return True
    except Exception as e:
        print(f"❌ {description} import failed: {e}")
        return False

def run_import_checks():
    print("🚀 Module Import Checks")
    print("=" * 50)
    modules = [
        ("hydra_logger.core.logger", "Core Logger"),
        ("hydra_logger.core.constants", "Core Constants"),
        ("hydra_logger.core.error_handler", "Error Handler"),
        ("hydra_logger.core.exceptions", "Exceptions"),
        ("hydra_logger.config.loaders", "Config Loaders"),
        ("hydra_logger.config.models", "Config Models"),
        ("hydra_logger.config.constants", "Config Constants"),
        ("hydra_logger.data_protection.fallbacks", "Data Protection Fallbacks"),
        ("hydra_logger.data_protection.security", "Data Protection Security"),
        ("hydra_logger.plugins.registry", "Plugin Registry"),
        ("hydra_logger.plugins.base", "Plugin Base"),
        ("hydra_logger.async_hydra.async_logger", "Async Logger"),
        ("hydra_logger.async_hydra.async_handlers", "Async Handlers"),
        ("hydra_logger.magic_configs", "Magic Configs"),
    ]
    for module, desc in modules:
        test_module_import(module, desc)
    print("\n✅ Module import checks complete!\n")

def test_core_logger():
    print("🔍 Testing Core Logger functionality...")
    try:
        from hydra_logger.core.logger import HydraLogger
        logger = HydraLogger()
        assert logger is not None
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.close()
        print("✅ Core Logger functionality PASS")
        return True
    except Exception as e:
        print(f"❌ Core Logger test failed: {e}")
        return False

def test_core_constants():
    print("🔍 Testing Core Constants functionality...")
    try:
        from hydra_logger.core.constants import LOG_LEVELS, DEFAULT_COLORS, NAMED_COLORS
        assert LOG_LEVELS and DEFAULT_COLORS and NAMED_COLORS
        assert isinstance(LOG_LEVELS, dict)
        print("✅ Core Constants functionality PASS")
        return True
    except Exception as e:
        print(f"❌ Core Constants test failed: {e}")
        return False

def test_error_handler():
    print("🔍 Testing Error Handler functionality...")
    try:
        from hydra_logger.core.error_handler import (
            ErrorTracker, error_context
        )
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test_errors.log")
        tracker = ErrorTracker(log_file=log_file)
        tracker.track_error("test_error", ValueError("Test error"), component="test")
        with error_context("test_component", "test_operation"):
            pass
        tracker.close()
        shutil.rmtree(temp_dir)
        print("✅ Error Handler functionality PASS")
        return True
    except Exception as e:
        print(f"❌ Error Handler test failed: {e}")
        return False

def test_config_loaders():
    print("🔍 Testing Config Loaders functionality...")
    try:
        from hydra_logger.config.loaders import get_default_config, load_config_from_dict
        default_config = get_default_config()
        config = load_config_from_dict({"log_level": "INFO"})
        assert default_config and config
        print("✅ Config Loaders functionality PASS")
        return True
    except Exception as e:
        print(f"❌ Config Loaders test failed: {e}")
        return False

def test_data_protection():
    print("🔍 Testing Data Protection functionality...")
    try:
        from hydra_logger.data_protection.fallbacks import FallbackHandler
        from hydra_logger.data_protection.security import DataSanitizer, SecurityValidator
        FallbackHandler(); DataSanitizer(); SecurityValidator()
        print("✅ Data Protection functionality PASS")
        return True
    except Exception as e:
        print(f"❌ Data Protection test failed: {e}")
        return False

def test_plugins():
    print("🔍 Testing Plugin System functionality...")
    try:
        from hydra_logger.plugins.registry import get_plugin, list_plugins
        plugins = list_plugins()
        assert isinstance(plugins, dict)
        assert callable(get_plugin)
        print("✅ Plugin System functionality PASS")
        return True
    except Exception as e:
        print(f"❌ Plugin System test failed: {e}")
        return False

async def test_async_logger():
    print("🔍 Testing Async Logger functionality...")
    try:
        from hydra_logger.async_hydra.async_logger import AsyncHydraLogger
        logger = AsyncHydraLogger()
        assert logger is not None
        await logger.close()
        print("✅ Async Logger functionality PASS")
        return True
    except Exception as e:
        print(f"❌ Async Logger test failed: {e}")
        return False

def test_magic_configs():
    print("🔍 Testing Magic Configs functionality...")
    try:
        from hydra_logger.magic_configs import MagicConfigRegistry
        registry = MagicConfigRegistry()
        configs = registry.list_configs()
        assert isinstance(configs, dict)
        print("✅ Magic Configs functionality PASS")
        return True
    except Exception as e:
        print(f"❌ Magic Configs test failed: {e}")
        return False

async def run_functionality_checks():
    print("🚀 Module Functionality Checks")
    print("=" * 50)
    tests = [
        ("Core Logger", test_core_logger),
        ("Core Constants", test_core_constants),
        ("Error Handler", test_error_handler),
        ("Config Loaders", test_config_loaders),
        ("Data Protection", test_data_protection),
        ("Plugin System", test_plugins),
        ("Magic Configs", test_magic_configs),
    ]
    results = {}
    for name, func in tests:
        if name == "Async Logger":
            results[name] = "PASS" if await test_async_logger() else "FAIL"
        else:
            results[name] = "PASS" if func() else "FAIL"
    # Async logger test
    results["Async Logger"] = "PASS" if await test_async_logger() else "FAIL"
    print("\n📊 FUNCTIONALITY TEST RESULTS")
    for name, result in results.items():
        print(f"  {name}: {result}")
    print(f"\n🎯 Overall: {sum(1 for r in results.values() if r == 'PASS')}/{len(results)} modules PASS\n")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("imports", "all"):
        run_import_checks()
    if mode in ("functionality", "all"):
        asyncio.run(run_functionality_checks())

if __name__ == "__main__":
    main() 