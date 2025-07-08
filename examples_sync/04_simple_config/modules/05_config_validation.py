#!/usr/bin/env python3
"""
✅ Configuration Validation: Validate and test configurations

What you'll learn:
- Configuration validation
- Error handling for configurations
- Configuration testing
- Configuration best practices

Time: 15 minutes
Difficulty: Intermediate
"""

import os
import yaml
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def create_test_configs():
    """Create test configuration files for validation."""
    os.makedirs("config_examples", exist_ok=True)
    
    # Valid configuration
    valid_config = """layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/valid.log
        format: text
      - type: console
        level: WARNING
        format: text
"""
    
    with open("config_examples/valid.yaml", "w") as f:
        f.write(valid_config)
    
    # Invalid configuration (missing required fields)
    invalid_config = """layers:
  APP:
    level: INFO
    destinations:
      - type: file
        # Missing path
        format: text
"""
    
    with open("config_examples/invalid.yaml", "w") as f:
        f.write(invalid_config)
    
    # Complex configuration for testing
    complex_config = """layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        format: text
      - type: console
        level: ERROR
        format: json
  
  DEBUG:
    level: DEBUG
    destinations:
      - type: file
        path: logs/debug.log
        format: text
  
  ERRORS:
    level: ERROR
    destinations:
      - type: file
        path: logs/errors.log
        format: text
      - type: console
        level: ERROR
        format: json
"""
    
    with open("config_examples/complex.yaml", "w") as f:
        f.write(complex_config)


def validate_config(config_path):
    """Validate a configuration file."""
    try:
        # Try to load the configuration
        logger = HydraLogger.from_config(config_path)
        return True, "Configuration is valid"
    except Exception as e:
        return False, str(e)


def test_config(config_path, test_name):
    """Test a configuration with sample logging."""
    try:
        logger = HydraLogger.from_config(config_path)
        
        # Test different log levels
        logger.debug("APP", "Debug test message")
        logger.info("APP", "Info test message")
        logger.warning("APP", "Warning test message")
        logger.error("APP", "Error test message")
        
        return True, f"{test_name} configuration test passed"
    except Exception as e:
        return False, f"{test_name} configuration test failed: {e}"


def run_config_validation():
    """Step-by-step configuration validation guide."""
    print("✅ Configuration Validation")
    print("=" * 40)
    
    # Step 1: Understanding configuration validation
    print("\n📊 Step 1: Understanding Configuration Validation")
    print("Configuration validation benefits:")
    print("  ✅ Catch errors early")
    print("  🔧 Ensure configurations work")
    print("  📋 Prevent runtime failures")
    print("  👥 Team collaboration")
    print("  🧪 Automated testing")
    print("  📊 Production reliability")
    
    # Step 2: Create test configurations
    print("\n📦 Step 2: Create Test Configurations")
    print("Creating test configuration files...")
    
    create_test_configs()
    
    print("✅ Test configuration files created!")
    print("   📄 config_examples/valid.yaml - Valid configuration")
    print("   📄 config_examples/invalid.yaml - Invalid configuration")
    print("   📄 config_examples/complex.yaml - Complex configuration")
    
    # Step 3: Validate valid configuration
    print("\n✅ Step 3: Validate Valid Configuration")
    print("Testing valid configuration...")
    
    is_valid, message = validate_config("config_examples/valid.yaml")
    if is_valid:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    
    # Step 4: Validate invalid configuration
    print("\n❌ Step 4: Validate Invalid Configuration")
    print("Testing invalid configuration...")
    
    is_valid, message = validate_config("config_examples/invalid.yaml")
    if is_valid:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        print("   This is expected - the configuration is intentionally invalid")
    
    # Step 5: Test valid configuration
    print("\n🧪 Step 5: Test Valid Configuration")
    print("Testing valid configuration with sample logging...")
    
    test_passed, message = test_config("config_examples/valid.yaml", "Valid")
    if test_passed:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    
    # Step 6: Test complex configuration
    print("\n🧪 Step 6: Test Complex Configuration")
    print("Testing complex configuration with multiple layers...")
    
    test_passed, message = test_config("config_examples/complex.yaml", "Complex")
    if test_passed:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    
    # Step 7: Check generated files
    print("\n📁 Step 7: Check Generated Files")
    print("Files created by configuration tests:")
    
    files_to_check = [
        "logs/valid.log",
        "logs/app.log",
        "logs/debug.log",
        "logs/errors.log"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                print(f"   📄 {file_path}: {len(lines)} lines")
        else:
            print(f"   ❌ {file_path}: Not found")
    
    # Step 8: Validation best practices
    print("\n🎯 Step 8: Validation Best Practices")
    print("Configuration validation best practices:")
    print("  ✅ Validate all configurations")
    print("  ✅ Test with sample data")
    print("  ✅ Check file permissions")
    print("  ✅ Verify directory structure")
    print("  ✅ Test environment variables")
    print("  ✅ Handle validation errors gracefully")
    
    # Step 9: Common validation errors
    print("\n🚨 Step 9: Common Validation Errors")
    print("Common configuration validation errors:")
    print("  ❌ Missing required fields")
    print("  ❌ Invalid log levels")
    print("  ❌ Invalid file paths")
    print("  ❌ Missing directories")
    print("  ❌ Invalid format types")
    print("  ❌ Environment variable issues")
    
    # Step 10: Validation strategies
    print("\n🔍 Step 10: Validation Strategies")
    print("Configuration validation strategies:")
    print("  📋 Schema validation - Check structure")
    print("  🧪 Functional testing - Test with data")
    print("  🔧 Integration testing - Test with system")
    print("  📊 Performance testing - Test performance")
    print("  🛡️ Security testing - Test security")
    print("  📈 Load testing - Test under load")
    
    # Step 11: Automated validation
    print("\n🤖 Step 11: Automated Validation")
    print("Automated configuration validation:")
    print("  ✅ CI/CD integration")
    print("  ✅ Pre-deployment checks")
    print("  ✅ Automated testing")
    print("  ✅ Configuration linting")
    print("  ✅ Format validation")
    print("  ✅ Security scanning")
    
    # Step 12: Next steps
    print("\n🎯 Step 12: Next Steps")
    print("You've learned configuration validation!")
    print("\nNext modules to try:")
    print("  🏗️  05_multiple_layers - Multi-layered logging")
    print("  🔄 06_rotation - Log file rotation")
    print("  🌍 10_environment_detection - Environment-based configs")
    
    print("\n🎉 Configuration validation completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_config_validation() 