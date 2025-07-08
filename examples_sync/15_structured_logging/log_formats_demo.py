#!/usr/bin/env python3
"""
Log Formats Demo: Comprehensive demonstration of all supported log formats in Hydra-Logger.

This example showcases all the different log formats supported by Hydra-Logger:
- text: Plain text format with timestamps and log levels
- json: Structured JSON format for log aggregation and analysis
- csv: Comma-separated values for analytics and data processing
- syslog: Syslog format for system integration
- gelf: Graylog Extended Log Format for centralized logging

Each format is demonstrated with the same log messages to show the differences
in output structure and how they can be used for different purposes.
"""

import os
import time
from pathlib import Path

from hydra_logger import HydraLogger
from hydra_logger.config import LogDestination, LoggingConfig, LogLayer


def create_formats_config(log_base_path):
    """
    Create a configuration that demonstrates all supported log formats.

    Args:
        log_base_path (str): Base path for all log files.

    Returns:
        LoggingConfig: Configuration with examples of all log formats.
    """
    return LoggingConfig(
        layers={
            # Text format - traditional plain text logging
            "TEXT": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "formats", "text.log"),
                        format="text"
                    ),
                    LogDestination(
                        type="console",
                        format="text"
                    )
                ],
            ),
            # JSON format - structured logging for analysis
            "JSON": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "formats", "json.log"),
                        format="json"
                    ),
                    LogDestination(
                        type="console",
                        format="json"
                    )
                ],
            ),
            # CSV format - for analytics and data processing
            "CSV": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "formats", "csv.log"),
                        format="csv"
                    ),
                    LogDestination(
                        type="console",
                        format="csv"
                    )
                ],
            ),
            # Syslog format - for system integration
            "SYSLOG": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "formats", "syslog.log"),
                        format="syslog"
                    ),
                    LogDestination(
                        type="console",
                        format="syslog"
                    )
                ],
            ),
            # GELF format - for centralized logging
            "GELF": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "formats", "gelf.log"),
                        format="gelf"
                    ),
                    LogDestination(
                        type="console",
                        format="gelf"
                    )
                ],
            ),
        }
    )


def demonstrate_text_format(logger):
    """Demonstrate text format logging."""
    print("\n=== Text Format Demo ===")
    print("Text format provides traditional plain text logging with timestamps and log levels.")
    
    logger.debug("TEXT", "This is a debug message in text format")
    logger.info("TEXT", "This is an info message in text format")
    logger.warning("TEXT", "This is a warning message in text format")
    logger.error("TEXT", "This is an error message in text format")
    logger.critical("TEXT", "This is a critical message in text format")


def demonstrate_json_format(logger):
    """Demonstrate JSON format logging."""
    print("\n=== JSON Format Demo ===")
    print("JSON format provides structured logging for easy parsing and analysis.")
    
    logger.debug("JSON", "This is a debug message in JSON format")
    logger.info("JSON", "This is an info message in JSON format")
    logger.warning("JSON", "This is a warning message in JSON format")
    logger.error("JSON", "This is an error message in JSON format")
    logger.critical("JSON", "This is a critical message in JSON format")


def demonstrate_csv_format(logger):
    """Demonstrate CSV format logging."""
    print("\n=== CSV Format Demo ===")
    print("CSV format provides comma-separated values for analytics and data processing.")
    
    logger.debug("CSV", "This is a debug message in CSV format")
    logger.info("CSV", "This is an info message in CSV format")
    logger.warning("CSV", "This is a warning message in CSV format")
    logger.error("CSV", "This is an error message in CSV format")
    logger.critical("CSV", "This is a critical message in CSV format")


def demonstrate_syslog_format(logger):
    """Demonstrate Syslog format logging."""
    print("\n=== Syslog Format Demo ===")
    print("Syslog format provides system integration compatibility.")
    
    logger.debug("SYSLOG", "This is a debug message in syslog format")
    logger.info("SYSLOG", "This is an info message in syslog format")
    logger.warning("SYSLOG", "This is a warning message in syslog format")
    logger.error("SYSLOG", "This is an error message in syslog format")
    logger.critical("SYSLOG", "This is a critical message in syslog format")


def demonstrate_gelf_format(logger):
    """Demonstrate GELF format logging."""
    print("\n=== GELF Format Demo ===")
    print("GELF format provides Graylog Extended Log Format for centralized logging.")
    
    logger.debug("GELF", "This is a debug message in GELF format")
    logger.info("GELF", "This is an info message in GELF format")
    logger.warning("GELF", "This is a warning message in GELF format")
    logger.error("GELF", "This is an error message in GELF format")
    logger.critical("GELF", "This is a critical message in GELF format")


def demonstrate_mixed_formats(logger):
    """Demonstrate using different formats for different purposes."""
    print("\n=== Mixed Formats Demo ===")
    print("Different formats can be used for different purposes in the same application.")
    
    # Application logs in text format
    logger.info("TEXT", "Application started successfully")
    logger.warning("TEXT", "Configuration file not found, using defaults")
    
    # API logs in JSON format for structured analysis
    logger.info("JSON", "API request: GET /api/users")
    logger.error("JSON", "API error: 404 Not Found")
    
    # Performance metrics in CSV format for analytics
    logger.info("CSV", "Response time: 150ms")
    logger.info("CSV", "Memory usage: 85%")
    
    # Security events in syslog format
    logger.warning("SYSLOG", "Failed login attempt from IP 192.168.1.100")
    logger.error("SYSLOG", "Authentication failure for user admin")
    
    # Monitoring alerts in GELF format
    logger.warning("GELF", "High CPU usage detected: 90%")
    logger.error("GELF", "Database connection timeout")


def show_file_contents(log_base_path):
    """Show the contents of generated log files."""
    print("\n" + "="*60)
    print("📄 LOG FILE CONTENTS")
    print("="*60)
    
    formats_dir = os.path.join(log_base_path, "formats")
    if not os.path.exists(formats_dir):
        print("No log files found.")
        return
    
    for filename in sorted(os.listdir(formats_dir)):
        filepath = os.path.join(formats_dir, filename)
        if os.path.isfile(filepath):
            print(f"\n📄 {filename}:")
            print("-" * 40)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    if content.strip():
                        print(content)
                    else:
                        print("(File is empty)")
            except Exception as e:
                print(f"Error reading file: {e}")


def main():
    """
    Main demonstration function.
    
    This function demonstrates all supported log formats in Hydra-Logger,
    showing how each format structures the same log messages differently
    and explaining their use cases.
    """
    
    # Create logs directory
    log_base_path = "logs"
    os.makedirs(log_base_path, exist_ok=True)
    
    print("🎯 Hydra-Logger Log Formats Demo")
    print("=" * 50)
    print("This demo showcases all supported log formats:")
    print("• text: Traditional plain text logging")
    print("• json: Structured JSON for analysis")
    print("• csv: Comma-separated values for analytics")
    print("• syslog: System integration format")
    print("• gelf: Graylog Extended Log Format")
    print()
    
    # Create logger with all format configurations
    config = create_formats_config(log_base_path)
    logger = HydraLogger(config)
    
    # Demonstrate each format
    demonstrate_text_format(logger)
    demonstrate_json_format(logger)
    demonstrate_csv_format(logger)
    demonstrate_syslog_format(logger)
    demonstrate_gelf_format(logger)
    
    # Demonstrate mixed format usage
    demonstrate_mixed_formats(logger)
    
    # Wait a moment for logs to be written
    time.sleep(1)
    
    # Show the generated file contents
    show_file_contents(log_base_path)
    
    print("\n" + "="*60)
    print("✅ Log Formats Demo Completed!")
    print(f"📁 Check the log files in: {os.path.abspath(log_base_path)}/formats/")
    print()
    print("📊 Format Comparison:")
    print("• text: Human-readable, traditional logging")
    print("• json: Machine-readable, structured data")
    print("• csv: Spreadsheet-friendly, analytics-ready")
    print("• syslog: System integration, standard format")
    print("• gelf: Centralized logging, Graylog compatible")


if __name__ == "__main__":
    main() 