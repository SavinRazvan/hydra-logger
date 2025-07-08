#!/usr/bin/env python3
"""
⚙️ Configuration Manager: Real application with configuration management

This example demonstrates a configuration management system
that uses different configuration formats and validation.

Features:
- Multiple configuration formats
- Configuration validation
- Configuration switching
- Configuration testing
- Real application integration

Time: 15 minutes
Difficulty: Intermediate
"""

import os
import yaml
import json
from datetime import datetime
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


class ConfigurationManager:
    """Configuration management system with multiple formats."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        # Create log directories
        os.makedirs("logs/examples", exist_ok=True)
        os.makedirs("config_examples", exist_ok=True)
        
        # Create different configuration formats
        self.create_configurations()
        
        # Initialize with default configuration
        self.current_config = "basic"
        self.logger = self.load_configuration("basic")
        
    def create_configurations(self):
        """Create example configurations in different formats."""
        
        # Basic configuration
        basic_config = {
            "layers": {
                "APP": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/examples/config_manager.log",
                            "format": "text"
                        },
                        {
                            "type": "console",
                            "level": "WARNING",
                            "format": "text"
                        }
                    ]
                }
            }
        }
        
        with open("config_examples/basic.yaml", "w") as f:
            yaml.dump(basic_config, f, default_flow_style=False, indent=2)
        
        # Advanced configuration
        advanced_config = {
            "layers": {
                "APP": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/examples/app.log",
                            "format": "text"
                        },
                        {
                            "type": "console",
                            "level": "ERROR",
                            "format": "json"
                        }
                    ]
                },
                "DEBUG": {
                    "level": "DEBUG",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/examples/debug.log",
                            "format": "text"
                        }
                    ]
                },
                "ERRORS": {
                    "level": "ERROR",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/examples/errors.log",
                            "format": "text"
                        }
                    ]
                }
            }
        }
        
        with open("config_examples/advanced.yaml", "w") as f:
            yaml.dump(advanced_config, f, default_flow_style=False, indent=2)
        
        # JSON configuration
        json_config = {
            "layers": {
                "APP": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/examples/json_config.log",
                            "format": "json"
                        }
                    ]
                }
            }
        }
        
        with open("config_examples/json_config.json", "w") as f:
            json.dump(json_config, f, indent=2)
    
    def load_configuration(self, config_name):
        """Load a configuration by name."""
        config_files = {
            "basic": "config_examples/basic.yaml",
            "advanced": "config_examples/advanced.yaml",
            "json": "config_examples/json_config.json"
        }
        
        if config_name not in config_files:
            raise ValueError(f"Unknown configuration: {config_name}")
        
        config_path = config_files[config_name]
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            logger = HydraLogger.from_config(config_path)
            self.logger.info("APP", f"Configuration '{config_name}' loaded successfully")
            return logger
        except Exception as e:
            print(f"❌ Failed to load configuration '{config_name}': {e}")
            raise
    
    def switch_configuration(self, config_name):
        """Switch to a different configuration."""
        self.logger.info("APP", f"Switching from '{self.current_config}' to '{config_name}'")
        
        try:
            self.logger = self.load_configuration(config_name)
            self.current_config = config_name
            self.logger.info("APP", f"Configuration switched to '{config_name}'")
            return True
        except Exception as e:
            self.logger.error("APP", f"Failed to switch configuration: {e}")
            return False
    
    def test_configuration(self, config_name):
        """Test a configuration with sample data."""
        self.logger.info("APP", f"Testing configuration '{config_name}'")
        
        try:
            test_logger = self.load_configuration(config_name)
            
            # Test different log levels
            test_logger.debug("APP", "Debug test message")
            test_logger.info("APP", "Info test message")
            test_logger.warning("APP", "Warning test message")
            test_logger.error("APP", "Error test message")
            
            self.logger.info("APP", f"Configuration '{config_name}' test completed")
            return True
        except Exception as e:
            self.logger.error("APP", f"Configuration '{config_name}' test failed: {e}")
            return False
    
    def list_configurations(self):
        """List available configurations."""
        configs = ["basic", "advanced", "json"]
        self.logger.info("APP", f"Available configurations: {', '.join(configs)}")
        return configs
    
    def validate_configuration(self, config_name):
        """Validate a configuration."""
        self.logger.info("APP", f"Validating configuration '{config_name}'")
        
        try:
            test_logger = self.load_configuration(config_name)
            self.logger.info("APP", f"Configuration '{config_name}' is valid")
            return True
        except Exception as e:
            self.logger.error("APP", f"Configuration '{config_name}' is invalid: {e}")
            return False


def run_config_manager():
    """Run the configuration manager example."""
    print("⚙️ Configuration Manager Example")
    print("=" * 40)
    print("This example demonstrates configuration management in practice.")
    print("The configuration manager will:")
    print("  ✅ Create multiple configuration formats")
    print("  ✅ Switch between configurations")
    print("  ✅ Test configurations")
    print("  ✅ Validate configurations")
    print("  ✅ Log configuration operations")
    print()
    
    # Initialize configuration manager
    manager = ConfigurationManager()
    
    print("📋 Available configurations:")
    configs = manager.list_configurations()
    for config in configs:
        print(f"   📄 {config}")
    
    print("\n🧪 Testing all configurations...")
    
    # Test each configuration
    for config in configs:
        print(f"\n📝 Testing {config} configuration...")
        success = manager.test_configuration(config)
        if success:
            print(f"✅ {config} configuration test passed")
        else:
            print(f"❌ {config} configuration test failed")
    
    print("\n✅ Validating all configurations...")
    
    # Validate each configuration
    for config in configs:
        print(f"\n🔍 Validating {config} configuration...")
        valid = manager.validate_configuration(config)
        if valid:
            print(f"✅ {config} configuration is valid")
        else:
            print(f"❌ {config} configuration is invalid")
    
    print("\n🔄 Switching configurations...")
    
    # Switch between configurations
    for config in configs:
        print(f"\n🔄 Switching to {config} configuration...")
        success = manager.switch_configuration(config)
        if success:
            print(f"✅ Switched to {config} configuration")
        else:
            print(f"❌ Failed to switch to {config} configuration")
    
    print("\n📁 Generated files:")
    print("Check the following directories for generated files:")
    print("  📄 logs/examples/ - Application logs")
    print("  📄 config_examples/ - Configuration files")
    
    print("\n🎉 Configuration manager example completed!")


if __name__ == "__main__":
    run_config_manager() 