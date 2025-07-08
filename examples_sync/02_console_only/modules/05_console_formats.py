#!/usr/bin/env python3
"""
📄 Console Formats: Different output formats for console

What you'll learn:
- Text format (default)
- JSON format for structured logging
- Format customization
- Format best practices

Time: 15 minutes
Difficulty: Intermediate
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_console_formats():
    """Step-by-step console formats guide."""
    print("📄 Console Formats")
    print("=" * 40)
    
    # Step 1: Understanding formats
    print("\n📊 Step 1: Understanding Output Formats")
    print("Hydra-Logger supports different console output formats:")
    print("  📝 text   - Human-readable format (default)")
    print("  📄 json   - Structured JSON format")
    print("  📊 csv    - Comma-separated values")
    print("  📋 syslog - Standard syslog format")
    print("  📈 gelf   - Graylog Extended Log Format")
    
    # Step 2: Text format (default)
    print("\n📝 Step 2: Text Format (Default)")
    print("Creating console configuration with text format...")
    
    text_config = LoggingConfig(
        layers={
            "TEXT": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        level="DEBUG",
                        format="text"
                    )
                ]
            )
        }
    )
    
    text_logger = HydraLogger(text_config)
    
    print("✅ Text format configuration created!")
    print("   - Human-readable output")
    print("   - Colored by default")
    print("   - Perfect for development and debugging")
    
    # Step 3: Log with text format
    print("\n📝 Step 3: Log with Text Format")
    print("Logging messages with text format...")
    
    text_logger.debug("TEXT", "Debug message with text format")
    text_logger.info("TEXT", "Info message with text format")
    text_logger.warning("TEXT", "Warning message with text format")
    text_logger.error("TEXT", "Error message with text format")
    
    print("✅ Text format demonstrated!")
    
    # Step 4: JSON format
    print("\n📄 Step 4: JSON Format")
    print("Creating console configuration with JSON format...")
    
    json_config = LoggingConfig(
        layers={
            "JSON": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        level="DEBUG",
                        format="json"
                    )
                ]
            )
        }
    )
    
    json_logger = HydraLogger(json_config)
    
    print("✅ JSON format configuration created!")
    print("   - Structured JSON output")
    print("   - Machine-readable format")
    print("   - Perfect for log aggregation and analysis")
    
    # Step 5: Log with JSON format
    print("\n📄 Step 5: Log with JSON Format")
    print("Logging messages with JSON format...")
    
    json_logger.debug("JSON", "Debug message with JSON format")
    json_logger.info("JSON", "Info message with JSON format")
    json_logger.warning("JSON", "Warning message with JSON format")
    json_logger.error("JSON", "Error message with JSON format")
    
    print("✅ JSON format demonstrated!")
    
    # Step 6: CSV format
    print("\n📊 Step 6: CSV Format")
    print("Creating console configuration with CSV format...")
    
    csv_config = LoggingConfig(
        layers={
            "CSV": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        level="DEBUG",
                        format="csv"
                    )
                ]
            )
        }
    )
    
    csv_logger = HydraLogger(csv_config)
    
    print("✅ CSV format configuration created!")
    print("   - Comma-separated values")
    print("   - Perfect for data analysis")
    print("   - Easy to import into spreadsheets")
    
    # Step 7: Log with CSV format
    print("\n📊 Step 7: Log with CSV Format")
    print("Logging messages with CSV format...")
    
    csv_logger.debug("CSV", "Debug message with CSV format")
    csv_logger.info("CSV", "Info message with CSV format")
    csv_logger.warning("CSV", "Warning message with CSV format")
    csv_logger.error("CSV", "Error message with CSV format")
    
    print("✅ CSV format demonstrated!")
    
    # Step 8: Syslog format
    print("\n📋 Step 8: Syslog Format")
    print("Creating console configuration with syslog format...")
    
    syslog_config = LoggingConfig(
        layers={
            "SYSLOG": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        level="DEBUG",
                        format="syslog"
                    )
                ]
            )
        }
    )
    
    syslog_logger = HydraLogger(syslog_config)
    
    print("✅ Syslog format configuration created!")
    print("   - Standard syslog format")
    print("   - Perfect for system integration")
    print("   - Compatible with syslog servers")
    
    # Step 9: Log with syslog format
    print("\n📋 Step 9: Log with Syslog Format")
    print("Logging messages with syslog format...")
    
    syslog_logger.debug("SYSLOG", "Debug message with syslog format")
    syslog_logger.info("SYSLOG", "Info message with syslog format")
    syslog_logger.warning("SYSLOG", "Warning message with syslog format")
    syslog_logger.error("SYSLOG", "Error message with syslog format")
    
    print("✅ Syslog format demonstrated!")
    
    # Step 10: Format comparison
    print("\n📊 Step 10: Format Comparison")
    print("When to use each format:")
    print("  📝 text   - Development, debugging, human reading")
    print("  📄 json   - Log aggregation, analysis, machine processing")
    print("  📊 csv    - Data analysis, spreadsheets, reporting")
    print("  📋 syslog - System integration, server logs")
    print("  📈 gelf   - Graylog integration, centralized logging")
    
    # Step 11: Format best practices
    print("\n🎯 Step 11: Format Best Practices")
    print("Format usage best practices:")
    print("  ✅ Use text format for development and debugging")
    print("  ✅ Use JSON format for production and log aggregation")
    print("  ✅ Use CSV format for data analysis and reporting")
    print("  ✅ Use syslog format for system integration")
    print("  ✅ Choose format based on your use case")
    print("  ✅ Consider performance impact of different formats")
    
    # Step 12: Advanced format techniques
    print("\n🚀 Step 12: Advanced Format Techniques")
    print("Advanced format customization:")
    print("  🎨 Custom format strings")
    print("  📊 Structured data in JSON")
    print("  🔄 Format switching based on environment")
    print("  📱 Multiple formats for different destinations")
    
    # Step 13: Next steps
    print("\n🎯 Step 13: Next Steps")
    print("You've learned console output formats!")
    print("\nNext steps:")
    print("  💼 Try cli_app.py - Real CLI application")
    print("  📚 Explore other examples in examples_sync/")
    print("  🚀 Read the main documentation for advanced features")
    
    print("\n🎉 Console formats completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_console_formats() 