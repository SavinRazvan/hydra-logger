#!/usr/bin/env python3
"""
Timestamp Format Examples for Hydra-Logger

This example demonstrates how to use the comprehensive timestamp formatting system
in Hydra-Logger with different formats, precision levels, and configurations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from hydra_logger.utils.time import (
    TimestampConfig, 
    TimestampFormat, 
    TimestampPrecision,
    TimestampFormatter
)
from hydra_logger.formatters.text import PlainTextFormatter
from hydra_logger.formatters.json import JsonLinesFormatter
from hydra_logger.types.records import LogRecord
from datetime import datetime, timezone


def demonstrate_timestamp_configs():
    """Demonstrate different timestamp configuration presets."""
    print("=" * 60)
    print("TIMESTAMP CONFIGURATION PRESETS")
    print("=" * 60)
    
    # Create a test log record
    record = LogRecord(
        message="Sample log message",
        level=20,
        level_name="INFO",
        logger_name="example_logger",
        layer="demo",
        timestamp=datetime.now(timezone.utc).timestamp()
    )
    
    # Test different preset configurations
    configs = [
        ("RFC3339 Standard", TimestampConfig.rfc3339_standard()),
        ("RFC3339 High Precision", TimestampConfig.rfc3339_high_precision()),
        ("Unix Timestamp", TimestampConfig.unix_timestamp()),
        ("Unix Milliseconds", TimestampConfig.unix_millis()),
        ("Human Readable", TimestampConfig.human_readable()),
        ("Compact", TimestampConfig.compact()),
        ("Legacy", TimestampConfig.legacy()),
    ]
    
    for name, config in configs:
        formatter = PlainTextFormatter(timestamp_config=config)
        formatted = formatter.format(record)
        print(f"{name:20}: {formatted}")


def demonstrate_custom_timestamp_configs():
    """Demonstrate custom timestamp configurations."""
    print("\n" + "=" * 60)
    print("CUSTOM TIMESTAMP CONFIGURATIONS")
    print("=" * 60)
    
    # Create a test log record
    record = LogRecord(
        message="Custom timestamp demo",
        level=30,
        level_name="WARNING",
        logger_name="custom_logger",
        layer="demo",
        timestamp=datetime.now(timezone.utc).timestamp()
    )
    
    # Custom configurations
    custom_configs = [
        ("RFC3339 with Timezone", TimestampConfig(
            format_type=TimestampFormat.RFC3339_TZ,
            precision=TimestampPrecision.SECONDS,
            timezone_name="America/New_York"
        )),
        ("Compact with Microseconds", TimestampConfig(
            format_type=TimestampFormat.COMPACT_MICRO,
            precision=TimestampPrecision.MICROSECONDS,
            timezone_name="UTC"
        )),
        ("Unix Nanoseconds", TimestampConfig(
            format_type=TimestampFormat.UNIX_NANOS,
            precision=TimestampPrecision.NANOSECONDS,
            timezone_name="UTC"
        )),
        ("Human with Milliseconds", TimestampConfig(
            format_type=TimestampFormat.HUMAN_READABLE_MICRO,
            precision=TimestampPrecision.MILLISECONDS,
            timezone_name="UTC"
        )),
    ]
    
    for name, config in custom_configs:
        formatter = PlainTextFormatter(timestamp_config=config)
        formatted = formatter.format(record)
        print(f"{name:25}: {formatted}")


def demonstrate_json_formatter():
    """Demonstrate JSON formatter with different timestamp formats."""
    print("\n" + "=" * 60)
    print("JSON FORMATTER WITH TIMESTAMP CONFIGURATIONS")
    print("=" * 60)
    
    # Create a test log record
    record = LogRecord(
        message="JSON timestamp demo",
        level=10,
        level_name="DEBUG",
        logger_name="json_logger",
        layer="demo",
        timestamp=datetime.now(timezone.utc).timestamp()
    )
    
    # Test JSON formatter with different timestamp configs
    json_configs = [
        ("RFC3339 Standard", TimestampConfig.rfc3339_standard()),
        ("RFC3339 Microseconds", TimestampConfig.rfc3339_high_precision()),
        ("Unix Timestamp", TimestampConfig.unix_timestamp()),
        ("Unix Milliseconds", TimestampConfig.unix_millis()),
    ]
    
    for name, config in json_configs:
        formatter = JsonLinesFormatter(timestamp_config=config)
        formatted = formatter.format(record)
        print(f"{name:20}: {formatted}")


def demonstrate_timestamp_formatter_direct():
    """Demonstrate direct usage of TimestampFormatter."""
    print("\n" + "=" * 60)
    print("DIRECT TIMESTAMP FORMATTER USAGE")
    print("=" * 60)
    
    # Current time
    now = datetime.now(timezone.utc)
    
    # Test different formats directly
    formats = [
        TimestampFormat.RFC3339,
        TimestampFormat.RFC3339_MICRO,
        TimestampFormat.RFC3339_NANO,
        TimestampFormat.UNIX_SECONDS,
        TimestampFormat.UNIX_MILLIS,
        TimestampFormat.UNIX_MICROS,
        TimestampFormat.UNIX_NANOS,
        TimestampFormat.HUMAN_READABLE,
        TimestampFormat.HUMAN_READABLE_MICRO,
        TimestampFormat.COMPACT,
        TimestampFormat.COMPACT_MICRO,
    ]
    
    for format_type in formats:
        formatted = TimestampFormatter.format_timestamp(now, format_type)
        print(f"{format_type.value:20}: {formatted}")


def demonstrate_timestamp_parsing():
    """Demonstrate timestamp parsing capabilities."""
    print("\n" + "=" * 60)
    print("TIMESTAMP PARSING EXAMPLES")
    print("=" * 60)
    
    # Test parsing different timestamp formats
    test_timestamps = [
        ("2023-12-25T15:30:45Z", TimestampFormat.RFC3339),
        ("2023-12-25T15:30:45.123456Z", TimestampFormat.RFC3339_MICRO),
        ("1703518245", TimestampFormat.UNIX_SECONDS),
        ("1703518245123", TimestampFormat.UNIX_MILLIS),
        ("2023-12-25 15:30:45", TimestampFormat.HUMAN_READABLE),
    ]
    
    for timestamp_str, format_type in test_timestamps:
        try:
            parsed = TimestampFormatter.parse_timestamp(timestamp_str, format_type)
            print(f"{timestamp_str:25} -> {parsed}")
        except Exception as e:
            print(f"{timestamp_str:25} -> ERROR: {e}")


def demonstrate_configuration_serialization():
    """Demonstrate configuration serialization and deserialization."""
    print("\n" + "=" * 60)
    print("CONFIGURATION SERIALIZATION")
    print("=" * 60)
    
    # Create a custom configuration
    config = TimestampConfig(
        format_type=TimestampFormat.RFC3339_MICRO,
        precision=TimestampPrecision.MICROSECONDS,
        timezone_name="America/Los_Angeles",
        include_timezone=True
    )
    
    print("Original Configuration:")
    print(f"  Format: {config.format_type.value}")
    print(f"  Precision: {config.precision.value}")
    print(f"  Timezone: {config.timezone_name}")
    print(f"  Include Timezone: {config.include_timezone}")
    
    # Serialize to dictionary
    config_dict = config.to_dict()
    print(f"\nSerialized to dict: {config_dict}")
    
    # Deserialize from dictionary
    restored_config = TimestampConfig.from_dict(config_dict)
    print(f"\nRestored Configuration:")
    print(f"  Format: {restored_config.format_type.value}")
    print(f"  Precision: {restored_config.precision.value}")
    print(f"  Timezone: {restored_config.timezone_name}")
    print(f"  Include Timezone: {restored_config.include_timezone}")
    
    # Test that they produce the same output
    test_time = datetime.now(timezone.utc)
    original_output = config.format_timestamp(test_time)
    restored_output = restored_config.format_timestamp(test_time)
    
    print(f"\nOutput comparison:")
    print(f"  Original:  {original_output}")
    print(f"  Restored:  {restored_output}")
    print(f"  Match:     {original_output == restored_output}")


def main():
    """Run all timestamp format demonstrations."""
    print("HYDRA-LOGGER TIMESTAMP FORMATTING SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("This example shows how to use the comprehensive timestamp")
    print("formatting system in Hydra-Logger with different formats,")
    print("precision levels, and configurations.")
    
    demonstrate_timestamp_configs()
    demonstrate_custom_timestamp_configs()
    demonstrate_json_formatter()
    demonstrate_timestamp_formatter_direct()
    demonstrate_timestamp_parsing()
    demonstrate_configuration_serialization()
    
    print("\n" + "=" * 60)
    print("USAGE SUMMARY")
    print("=" * 60)
    print("1. Use preset configurations for common use cases:")
    print("   - TimestampConfig.rfc3339_standard()")
    print("   - TimestampConfig.rfc3339_high_precision()")
    print("   - TimestampConfig.unix_timestamp()")
    print("   - TimestampConfig.human_readable()")
    print("   - TimestampConfig.compact()")
    print()
    print("2. Create custom configurations:")
    print("   config = TimestampConfig(")
    print("       format_type=TimestampFormat.RFC3339_MICRO,")
    print("       precision=TimestampPrecision.MICROSECONDS,")
    print("       timezone_name='UTC'")
    print("   )")
    print()
    print("3. Use with formatters:")
    print("   formatter = PlainTextFormatter(timestamp_config=config)")
    print("   formatter = JsonLinesFormatter(timestamp_config=config)")
    print()
    print("4. Direct timestamp formatting:")
    print("   TimestampFormatter.format_timestamp(dt, format_type)")
    print("   TimestampFormatter.get_current_timestamp(format_type)")
    print()
    print("5. Configuration serialization:")
    print("   config_dict = config.to_dict()")
    print("   config = TimestampConfig.from_dict(config_dict)")


if __name__ == "__main__":
    main()
