#!/usr/bin/env python3
"""
🌍 Environment Configuration: Environment variable substitution concepts

What you'll learn:
- Environment variable substitution concepts
- Dynamic configuration patterns
- Configuration flexibility
- Configuration best practices

Time: 15 minutes
Difficulty: Intermediate
"""

import os
import yaml
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def create_env_config():
    """Create example environment-based configuration files."""
    os.makedirs("config_examples", exist_ok=True)
    
    # Environment-based YAML configuration (for demonstration)
    env_config = """layers:
  ENV:
    level: INFO  # In real usage: ${HYDRA_LOG_LEVEL:-INFO}
    destinations:
      - type: file
        path: logs/env_config.log  # In real usage: ${HYDRA_LOG_PATH:-logs/env_config.log}
        format: text
      - type: console
        level: WARNING  # In real usage: ${HYDRA_CONSOLE_LEVEL:-WARNING}
        format: text  # In real usage: ${HYDRA_CONSOLE_FORMAT:-text}
  
  DEBUG:
    level: DEBUG  # In real usage: ${HYDRA_DEBUG_LEVEL:-DEBUG}
    destinations:
      - type: file
        path: logs/debug_env.log  # In real usage: ${HYDRA_DEBUG_PATH:-logs/debug_env.log}
        format: text
"""
    
    with open("config_examples/env_config.yaml", "w") as f:
        f.write(env_config)


def run_env_config():
    """Step-by-step environment configuration guide."""
    print("🌍 Environment Configuration")
    print("=" * 40)
    
    # Step 1: Understanding environment configuration
    print("\n📊 Step 1: Understanding Environment Configuration")
    print("Environment configuration benefits:")
    print("  🌍 Dynamic configuration")
    print("  🔧 Environment-specific settings")
    print("  📋 Flexible deployment")
    print("  👥 Team collaboration")
    print("  🧪 Easy testing")
    print("  📊 Production ready")
    
    # Step 2: Create environment configuration files
    print("\n📦 Step 2: Create Environment Configuration Files")
    print("Creating example environment configuration files...")
    
    create_env_config()
    
    print("✅ Environment configuration files created!")
    print("   📄 config_examples/env_config.yaml - Environment-based configuration")
    
    # Step 3: Explain environment variable concepts
    print("\n🌍 Step 3: Environment Variable Concepts")
    print("In production environments, you would use environment variables:")
    print("  📝 ${HYDRA_LOG_LEVEL:-INFO} - Log level with default")
    print("  📝 ${HYDRA_LOG_PATH:-logs/app.log} - Log path with default")
    print("  📝 ${HYDRA_CONSOLE_LEVEL:-WARNING} - Console level with default")
    print("  📝 ${HYDRA_CONSOLE_FORMAT:-text} - Console format with default")
    print("  📝 ${HYDRA_DEBUG_LEVEL:-DEBUG} - Debug level with default")
    print("  📝 ${HYDRA_DEBUG_PATH:-logs/debug.log} - Debug path with default")
    
    # Step 4: Load configuration
    print("\n📝 Step 4: Load Configuration")
    print("Loading configuration (using hardcoded values for this example)...")
    
    try:
        logger = HydraLogger.from_config("config_examples/env_config.yaml")
        print("✅ Configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return
    
    # Step 5: Test configuration
    print("\n📝 Step 5: Test Configuration")
    print("Logging messages with configuration...")
    
    logger.debug("DEBUG", "Debug message")
    logger.info("ENV", "Info message")
    logger.warning("ENV", "Warning message")
    logger.error("ENV", "Error message")
    
    print("✅ Configuration tested!")
    
    # Step 6: Environment variable syntax explanation
    print("\n💡 Step 6: Environment Variable Syntax")
    print("Environment variable substitution syntax (for reference):")
    print("  ${VAR_NAME} - Required environment variable")
    print("  ${VAR_NAME:-default} - Optional with default value")
    print("  ${VAR_NAME:-} - Optional with empty default")
    print("  ${VAR_NAME:-INFO} - Optional with INFO default")
    print("  ${VAR_NAME:-logs/default.log} - Optional with path default")
    
    # Step 7: Check generated files
    print("\n📁 Step 7: Check Generated Files")
    print("Files created by configuration:")
    
    files_to_check = [
        "logs/env_config.log",
        "logs/debug_env.log"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                print(f"   📄 {file_path}: {len(lines)} lines")
        else:
            print(f"   ❌ {file_path}: Not found")
    
    # Step 8: Environment configuration benefits
    print("\n💡 Step 8: Environment Configuration Benefits")
    print("Benefits of environment-based configuration:")
    print("  🌍 Dynamic - Different configs per environment")
    print("  🔧 Flexible - Easy to change without code")
    print("  📋 Secure - Sensitive data in environment")
    print("  👥 Collaborative - Teams can set their own envs")
    print("  🧪 Testable - Easy to test different configs")
    print("  📊 Deployable - Works with deployment systems")
    
    # Step 9: Real-world usage examples
    print("\n🌍 Step 9: Real-World Usage Examples")
    print("How environment variables would be used in production:")
    print("  🐳 Docker: docker run -e HYDRA_LOG_LEVEL=DEBUG app")
    print("  ☸️  Kubernetes: env: [{name: HYDRA_LOG_LEVEL, value: INFO}]")
    print("  🚀 Heroku: heroku config:set HYDRA_LOG_LEVEL=INFO")
    print("  🔧 Local: export HYDRA_LOG_LEVEL=DEBUG")
    print("  📋 CI/CD: environment: HYDRA_LOG_LEVEL: INFO")
    
    # Step 10: Environment configuration best practices
    print("\n🎯 Step 10: Environment Configuration Best Practices")
    print("Environment configuration best practices:")
    print("  ✅ Use meaningful variable names")
    print("  ✅ Provide sensible defaults")
    print("  ✅ Document all variables")
    print("  ✅ Use consistent naming conventions")
    print("  ✅ Validate environment variables")
    print("  ✅ Handle missing variables gracefully")
    
    # Step 11: Next steps
    print("\n🎯 Step 11: Next Steps")
    print("You've learned environment configuration concepts!")
    print("\nNext modules to try:")
    print("  ✅ 05_config_validation.py - Configuration validation")
    
    print("\n🎉 Environment configuration completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_env_config() 