#!/usr/bin/env python3
"""
📄 File Formats: Different file formats for logs

What you'll learn:
- Text format for human-readable logs
- JSON format for structured data
- CSV format for data analysis
- Format selection for different use cases

Time: 15 minutes
Difficulty: Intermediate
"""

import os
import json
import csv
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_file_formats():
    """Step-by-step file formats guide."""
    print("📄 File Formats")
    print("=" * 40)
    
    # Step 1: Understanding file formats
    print("\n📊 Step 1: Understanding File Formats")
    print("Different formats for different use cases:")
    print("  📝 Text - Human-readable, traditional logging")
    print("  📋 JSON - Structured data, machine-readable")
    print("  📊 CSV - Tabular data, spreadsheet analysis")
    print("  📡 Syslog - System logging standard")
    print("  🌐 GELF - Graylog Extended Log Format")
    
    # Step 2: Text format
    print("\n📝 Step 2: Text Format")
    print("Creating text format configuration...")
    
    os.makedirs("logs/formats", exist_ok=True)
    
    text_config = LoggingConfig(
        layers={
            "TEXT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/formats/text_output.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    text_logger = HydraLogger(text_config)
    
    print("✅ Text format configuration created!")
    print("   - Human-readable format")
    print("   - Traditional logging style")
    print("   - Easy to read and grep")
    print("   - File: logs/formats/text_output.log")
    
    # Step 3: Log with text format
    print("\n📝 Step 3: Log with Text Format")
    print("Logging messages in text format...")
    
    text_logger.info("TEXT", "Application started")
    text_logger.info("TEXT", "User login", user_id="123", ip="192.168.1.100")
    text_logger.warning("TEXT", "Database connection slow", duration="2.5s")
    text_logger.error("TEXT", "API request failed", endpoint="/api/users", status_code=500)
    
    print("✅ Text format messages logged!")
    
    # Step 4: JSON format
    print("\n📋 Step 4: JSON Format")
    print("Creating JSON format configuration...")
    
    json_config = LoggingConfig(
        layers={
            "JSON": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/formats/json_output.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    json_logger = HydraLogger(json_config)
    
    print("✅ JSON format configuration created!")
    print("   - Structured data format")
    print("   - Machine-readable")
    print("   - Perfect for log analysis tools")
    print("   - File: logs/formats/json_output.log")
    
    # Step 5: Log with JSON format
    print("\n📝 Step 5: Log with JSON Format")
    print("Logging messages in JSON format...")
    
    json_logger.info("JSON", "Application started")
    json_logger.info("JSON", "User login", user_id="123", ip="192.168.1.100")
    json_logger.warning("JSON", "Database connection slow", duration="2.5s")
    json_logger.error("JSON", "API request failed", endpoint="/api/users", status_code=500)
    
    print("✅ JSON format messages logged!")
    
    # Step 6: CSV format
    print("\n📊 Step 6: CSV Format")
    print("Creating CSV format configuration...")
    
    csv_config = LoggingConfig(
        layers={
            "CSV": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/formats/csv_output.csv",
                        format="csv"
                    )
                ]
            )
        }
    )
    
    csv_logger = HydraLogger(csv_config)
    
    print("✅ CSV format configuration created!")
    print("   - Tabular data format")
    print("   - Perfect for spreadsheet analysis")
    print("   - Easy to import into Excel/Google Sheets")
    print("   - File: logs/formats/csv_output.csv")
    
    # Step 7: Log with CSV format
    print("\n📝 Step 7: Log with CSV Format")
    print("Logging messages in CSV format...")
    
    csv_logger.info("CSV", "Application started")
    csv_logger.info("CSV", "User login", user_id="123", ip="192.168.1.100")
    csv_logger.warning("CSV", "Database connection slow", duration="2.5s")
    csv_logger.error("CSV", "API request failed", endpoint="/api/users", status_code=500)
    
    print("✅ CSV format messages logged!")
    
    # Step 8: Format comparison
    print("\n📊 Step 8: Format Comparison")
    print("Comparing different formats:")
    
    files_to_check = [
        ("logs/formats/text_output.log", "Text Format"),
        ("logs/formats/json_output.log", "JSON Format"),
        ("logs/formats/csv_output.csv", "CSV Format")
    ]
    
    for file_path, format_name in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.splitlines()
                print(f"   📄 {format_name}:")
                print(f"      File: {file_path}")
                print(f"      Size: {len(content)} characters")
                print(f"      Lines: {len(lines)}")
                if lines:
                    print(f"      Sample: {lines[0][:50]}...")
                print()
        else:
            print(f"   ❌ {format_name}: File not found")
    
    # Step 9: Format use cases
    print("\n💡 Step 9: Format Use Cases")
    print("When to use each format:")
    print("  📝 Text Format:")
    print("     ✅ Human-readable logs")
    print("     ✅ Traditional logging")
    print("     ✅ Easy to grep and search")
    print("     ✅ Good for debugging")
    print()
    print("  📋 JSON Format:")
    print("     ✅ Structured data logging")
    print("     ✅ Log analysis tools")
    print("     ✅ Machine-readable")
    print("     ✅ Complex data structures")
    print()
    print("  📊 CSV Format:")
    print("     ✅ Data analysis")
    print("     ✅ Spreadsheet import")
    print("     ✅ Statistical analysis")
    print("     ✅ Tabular data")
    
    # Step 10: Best practices
    print("\n🎯 Step 10: Best Practices")
    print("File format best practices:")
    print("  ✅ Choose format based on use case")
    print("  ✅ Use text for human reading")
    print("  ✅ Use JSON for structured data")
    print("  ✅ Use CSV for data analysis")
    print("  ✅ Consider log analysis tools")
    print("  ✅ Plan for log processing")
    
    # Step 11: Next steps
    print("\n🎯 Step 11: Next Steps")
    print("You've learned file formats!")
    print("\nNext modules to try:")
    print("  🗂️  05_file_organization.py - Organize logs by purpose")
    
    print("\n🎉 File formats completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_file_formats() 