"""
example_format_json.py
Demonstrates switching to JSON format and customizing JSON output.
"""

import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create logs directory
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_dir, exist_ok=True)

print("=== HydraLogger JSON Format Examples ===\n")

# Example 1: JSON format with proper JSON array structure
print("1. JSON Format with Proper JSON Array Structure:")
config = LoggingConfig(
    layers={
        "JSON": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path=os.path.join(logs_dir, "json_example.json"),
                    format="json"
                ),
                LogDestination(
                    type="console",
                    format="text"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Basic JSON logging
logger.info("JSON", "This is a JSON formatted message.")

# JSON with structured data in message
logger.info("JSON", "User action completed - user_id: 12345, action: login, timestamp: 2024-01-15T10:30:00Z")

logger.error("JSON", "Database connection failed - error_code: DB_CONN_001, retry_count: 3, database: users_db")

print(f"JSON logs written to: {os.path.join(logs_dir, 'json_example.json')}")

print("\n" + "="*50 + "\n")

# Example 2: JSON format explanation
print("2. JSON Format Explanation:")
print("✅ Proper JSON Array Format:")
print("   - Creates a valid JSON array: [{...}, {...}, {...}]")
print("   - Each log entry is a JSON object within the array")
print("   - Can be parsed by any JSON parser")
print("   - Human-readable with proper indentation")
print("   - Suitable for log analysis tools and dashboards")
print("\n❌ Old JSON Lines Format (what we fixed):")
print("   - One JSON object per line")
print("   - Not a valid JSON document")
print("   - Harder to parse and analyze")
print("   - Less suitable for log aggregation tools")

print("\n" + "="*50 + "\n")

# Example 3: JSON structure details
print("3. JSON Log Entry Structure:")
print("Each log entry contains:")
print("- timestamp: ISO format timestamp")
print("- level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
print("- logger: Logger name/layer")
print("- message: The actual log message")
print("- filename: Source file name")
print("- lineno: Line number in source file")

print("\n" + "="*50 + "\n")

# Example 4: JSON vs other formats
print("4. JSON Format vs Other Formats:")
print("JSON Format:")
print("  ✅ Structured data")
print("  ✅ Easy to parse programmatically")
print("  ✅ Good for log analysis tools")
print("  ✅ Human-readable")
print("  ❌ Larger file size")
print("  ❌ Not as compact as CSV")
print("\nText Format:")
print("  ✅ Simple and readable")
print("  ✅ Small file size")
print("  ✅ Easy to grep/search")
print("  ❌ Hard to parse programmatically")
print("  ❌ No structured data")

print(f"\nCheck the JSON file at: {os.path.join(logs_dir, 'json_example.json')}")
print("It will contain a proper JSON array with all log entries!") 