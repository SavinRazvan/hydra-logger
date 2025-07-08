"""
example_config.py
Demonstrates how to create and use configuration files with HydraLogger.
"""

import os
import yaml
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create logs directory
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_dir, exist_ok=True)

print("=== HydraLogger Configuration File Examples ===\n")

# Example 1: Create a YAML configuration file
print("1. Creating YAML Configuration File:")
config_data = {
    "default_level": "INFO",
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {
                    "type": "file",
                    "path": os.path.join(logs_dir, "app.log"),
                    "format": "text",
                    "max_size": "5MB",
                    "backup_count": 3
                },
                {
                    "type": "console",
                    "format": "text"
                }
            ]
        },
        "API": {
            "level": "DEBUG",
            "destinations": [
                {
                    "type": "file",
                    "path": os.path.join(logs_dir, "api.json"),
                    "format": "json",
                    "max_size": "10MB",
                    "backup_count": 5
                }
            ]
        },
        "ERROR": {
            "level": "ERROR",
            "destinations": [
                {
                    "type": "file",
                    "path": os.path.join(logs_dir, "errors.log"),
                    "format": "text",
                    "max_size": "2MB",
                    "backup_count": 10
                },
                {
                    "type": "console",
                    "format": "text"
                }
            ]
        }
    }
}

# Write YAML config file
config_file = os.path.join(logs_dir, "logging_config.yaml")
with open(config_file, 'w') as f:
    yaml.dump(config_data, f, default_flow_style=False)

print(f"YAML config created: {config_file}")

# Load and use the configuration
logger1 = HydraLogger.from_config(config_file)
logger1.info("APP", "Application started with YAML config.")
logger1.debug("API", "API debug message with JSON format.")
logger1.error("ERROR", "Error message logged to both file and console.")

print("\n" + "="*50 + "\n")

# Example 2: Create a TOML configuration file
print("2. Creating TOML Configuration File:")
toml_config = f"""
default_level = "INFO"

[layers.APP]
level = "INFO"
[[layers.APP.destinations]]
type = "file"
path = "{os.path.join(logs_dir, 'app_toml.log')}"
format = "text"
max_size = "5MB"
backup_count = 3

[[layers.APP.destinations]]
type = "console"
format = "text"

[layers.DEBUG]
level = "DEBUG"
[[layers.DEBUG.destinations]]
type = "file"
path = "{os.path.join(logs_dir, 'debug_toml.json')}"
format = "json"
max_size = "10MB"
backup_count = 5

[layers.SECURITY]
level = "WARNING"
[[layers.SECURITY.destinations]]
type = "file"
path = "{os.path.join(logs_dir, 'security_toml.csv')}"
format = "csv"
max_size = "1MB"
backup_count = 20
"""

# Write TOML config file
toml_config_file = os.path.join(logs_dir, "logging_config.toml")
with open(toml_config_file, 'w') as f:
    f.write(toml_config)

print(f"TOML config created: {toml_config_file}")

# Load and use the TOML configuration
logger2 = HydraLogger.from_config(toml_config_file)
logger2.info("APP", "Application started with TOML config.")
logger2.debug("DEBUG", "Debug message with JSON format.")
logger2.warning("SECURITY", "Security warning with CSV format.")

print("\n" + "="*50 + "\n")

# Example 3: Programmatic configuration
print("3. Programmatic Configuration:")
config3 = LoggingConfig(
    layers={
        "PROGRAMMATIC": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path=os.path.join(logs_dir, "programmatic.log"),
                    format="text",
                    max_size="5MB",
                    backup_count=3
                ),
                LogDestination(
                    type="console",
                    format="text"
                )
            ]
        )
    }
)

logger3 = HydraLogger(config=config3)
logger3.info("PROGRAMMATIC", "This uses programmatic configuration.")

print("\n" + "="*50 + "\n")

# Example 4: Configuration file formats summary
print("4. Configuration File Formats:")
print("Supported formats:")
print("- YAML (.yaml, .yml): Human-readable, widely supported")
print("- TOML (.toml): Simple, readable format")
print("- Programmatic: Direct Python configuration objects")
print("\nConfiguration structure:")
print("- LoggingConfig: Main container")
print("  - layers: Dictionary of LogLayer objects")
print("    - LogLayer: Configuration for a single layer")
print("      - destinations: List of LogDestination objects")
print("        - LogDestination: Configuration for a single destination")

print(f"\nAll configuration files and logs written to: {logs_dir}/")
print("Check the logs directory to see the different configurations in action!") 