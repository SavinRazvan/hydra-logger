#!/usr/bin/env python3
"""
09 - Custom Formatters

This example demonstrates custom formatting with Hydra-Logger.
Shows how to create custom log formats and patterns.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def main():
    """Demonstrate custom formatting."""
    
    print("🎨 Custom Formatters Demo")
    print("=" * 40)
    
    # Create configuration with custom formatters
    config = LoggingConfig(
        layers={
            "CUSTOM": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/custom_formatters/simple.log",
                        format="text"
                    )
                ]
            ),
            "JSON_CUSTOM": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/custom_formatters/json_custom.json",
                        format="json"
                    )
                ]
            ),
            "CSV_CUSTOM": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/custom_formatters/csv_custom.csv",
                        format="csv"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n📝 Custom Formatting Examples")
    print("-" * 30)
    
    # Example 1: Simple custom formatting
    print("\n🎨 Example 1: Simple custom formatting")
    print("-" * 40)
    
    logger.info("CUSTOM", "User action completed",
                user_id="123",
                action="login",
                timestamp="2025-01-27T10:30:15Z",
                ip_address="192.168.1.100")
    
    logger.info("CUSTOM", "Database operation",
                operation="SELECT",
                table="users",
                duration="150ms",
                rows_returned=25)
    
    # Example 2: JSON custom formatting
    print("\n🎨 Example 2: JSON custom formatting")
    print("-" * 40)
    
    logger.info("JSON_CUSTOM", "API request processed",
                method="POST",
                endpoint="/api/users",
                status_code=201,
                response_time="250ms",
                user_agent="Mozilla/5.0",
                request_id="req_12345")
    
    logger.info("JSON_CUSTOM", "System event",
                event_type="user_registration",
                user_id="456",
                email="user@example.com",
                registration_source="web_form",
                verification_status="pending")
    
    # Example 3: CSV custom formatting
    print("\n🎨 Example 3: CSV custom formatting")
    print("-" * 40)
    
    logger.info("CSV_CUSTOM", "Performance metric",
                metric_name="response_time",
                value="150",
                unit="ms",
                endpoint="/api/users",
                timestamp="2025-01-27T10:30:15Z")
    
    logger.info("CSV_CUSTOM", "Error occurrence",
                error_type="ValidationError",
                error_count="5",
                affected_users="12",
                resolution_time="30",
                severity="medium")
    
    # Example 4: Structured data logging
    print("\n🎨 Example 4: Structured data logging")
    print("-" * 40)
    
    # User activity
    logger.info("CUSTOM", "User activity tracked",
                user_id="789",
                activity_type="page_view",
                page_url="/dashboard",
                session_duration="15m",
                referrer="google.com")
    
    # Business metrics
    logger.info("JSON_CUSTOM", "Business metric recorded",
                metric="revenue",
                value="1250.50",
                currency="USD",
                period="daily",
                date="2025-01-27")
    
    # System health
    logger.info("CSV_CUSTOM", "System health check",
                component="database",
                status="healthy",
                response_time="50ms",
                connections="25",
                uptime="99.9%")
    
    # Example 5: Custom log patterns
    print("\n🎨 Example 5: Custom log patterns")
    print("-" * 40)
    
    # Audit trail
    logger.info("CUSTOM", "Audit trail entry",
                action="data_access",
                user_id="123",
                resource="customer_data",
                access_type="read",
                timestamp="2025-01-27T10:30:15Z",
                ip_address="192.168.1.100")
    
    # Security event
    logger.info("JSON_CUSTOM", "Security event detected",
                event_type="failed_login",
                user_id="unknown",
                ip_address="192.168.1.101",
                attempt_count="3",
                lockout_duration="15m")
    
    # Performance monitoring
    logger.info("CSV_CUSTOM", "Performance monitoring",
                metric="cpu_usage",
                value="45.2",
                unit="%",
                threshold="80",
                alert_level="normal")
    
    print("\n✅ Custom formatters demo completed!")
    print("📝 Check the logs/custom_formatters/ directory for formatted logs")
    
    # Show format examples
    print("\n📄 Format Examples:")
    print("-" * 20)
    print("• Simple: Human-readable text format")
    print("• JSON: Structured data for machine processing")
    print("• CSV: Tabular data for analysis")
    
    # Show generated files
    print("\n📁 Generated Files:")
    print("-" * 20)
    import os
    formatters_dir = "logs/custom_formatters"
    if os.path.exists(formatters_dir):
        for file in sorted(os.listdir(formatters_dir)):
            file_path = os.path.join(formatters_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  {file} ({size} bytes)")

if __name__ == "__main__":
    main() 