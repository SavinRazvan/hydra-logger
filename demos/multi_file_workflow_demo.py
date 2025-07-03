#!/usr/bin/env python3
"""
Multi-File Workflow Demo for Hydra-Logger

This comprehensive example demonstrates how to set up logging across multiple Python files
and classes in a real-world application scenario with support for multiple log formats.

Features demonstrated:
1. Distributed logging - each module logs to its own file with different formats
2. Centralized logging - all modules log to a single master file
3. Class-based logging with proper context
4. Cross-module logging with consistent formatting
5. Different log levels for different components
6. Error tracking across the entire application
7. Multiple log formats (text, JSON, CSV, syslog, GELF)
8. Performance monitoring and analytics

Project Structure:
├── main.py                    # Application entry point
├── modules/
│   ├── __init__.py
│   ├── user_manager.py       # User management module
│   ├── database_handler.py   # Database operations
│   ├── api_client.py         # External API interactions
│   └── notification_service.py # Email/SMS notifications
├── utils/
│   ├── __init__.py
│   └── helpers.py            # Utility functions
└── config/
    ├── logging_config.yaml   # Distributed logging config
    └── centralized_config.yaml # Centralized logging config
"""

import sys
import os
from pathlib import Path
import time

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def create_logging_configs():
    """Create the logging configuration files for the demo."""

    # Distributed logging configuration with multiple formats
    distributed_config = """
# Distributed Logging Configuration with Multiple Formats
# Each module logs to its own file + centralized master log

default_level: INFO

layers:
  # Centralized master log - captures everything in JSON format
  MASTER:
    level: DEBUG
    destinations:
      - type: file
        path: "workflow_logs/master/app.log"
        format: text
        max_size: "20MB"
        backup_count: 5
      - type: file
        path: "workflow_logs/master/app.json"
        format: json
        max_size: "20MB"
        backup_count: 5
      - type: console
        level: INFO
        format: json
  
  # User management module - text and JSON formats
  USER_MANAGER:
    level: INFO
    destinations:
      - type: file
        path: "workflow_logs/modules/user_manager.log"
        format: text
        max_size: "10MB"
        backup_count: 3
      - type: file
        path: "workflow_logs/modules/user_manager.json"
        format: json
        max_size: "10MB"
        backup_count: 3
      - type: file
        path: "workflow_logs/master/app.log"
        level: INFO
        format: text
  
  # Database operations - text and CSV for analytics
  DATABASE:
    level: INFO
    destinations:
      - type: file
        path: "workflow_logs/modules/database.log"
        format: text
        max_size: "15MB"
        backup_count: 5
      - type: file
        path: "workflow_logs/modules/database_analytics.csv"
        format: csv
        max_size: "15MB"
        backup_count: 5
      - type: file
        path: "workflow_logs/master/app.log"
        level: INFO
        format: text
  
  # API interactions - JSON for structured data
  API:
    level: INFO
    destinations:
      - type: file
        path: "workflow_logs/modules/api.log"
        format: text
        max_size: "10MB"
        backup_count: 3
      - type: file
        path: "workflow_logs/modules/api.json"
        format: json
        max_size: "10MB"
        backup_count: 3
      - type: file
        path: "workflow_logs/master/app.log"
        level: INFO
        format: text
  
  # Notification service - syslog format for system integration
  NOTIFICATIONS:
    level: INFO
    destinations:
      - type: file
        path: "workflow_logs/modules/notifications.log"
        format: syslog
        max_size: "5MB"
        backup_count: 3
      - type: file
        path: "workflow_logs/master/app.log"
        level: INFO
        format: text
  
  # Utility functions - debug level with text format
  UTILS:
    level: DEBUG
    destinations:
      - type: file
        path: "workflow_logs/modules/utils.log"
        format: text
        max_size: "5MB"
        backup_count: 2
      - type: file
        path: "workflow_logs/master/app.log"
        level: DEBUG
        format: text
  
  # Performance monitoring - CSV format for analytics
  PERFORMANCE:
    level: INFO
    destinations:
      - type: file
        path: "workflow_logs/performance/metrics.csv"
        format: csv
        max_size: "10MB"
        backup_count: 5
      - type: file
        path: "workflow_logs/performance/monitoring.json"
        format: json
        max_size: "10MB"
        backup_count: 5
  
  # Errors and critical issues - syslog and GELF formats
  ERRORS:
    level: ERROR
    destinations:
      - type: file
        path: "workflow_logs/errors/critical.log"
        format: syslog
        max_size: "5MB"
        backup_count: 10
      - type: file
        path: "workflow_logs/errors/critical.gelf"
        format: gelf
        max_size: "5MB"
        backup_count: 10
      - type: file
        path: "workflow_logs/master/app.log"
        level: ERROR
        format: text
      - type: console
        level: ERROR
        format: json
"""

    # Centralized logging configuration with multiple formats
    centralized_config = """
# Centralized Logging Configuration with Multiple Formats
# All modules log to a single master file with different levels and formats

default_level: INFO

layers:
  # Main application log - everything goes here in multiple formats
  APP:
    level: DEBUG
    destinations:
      - type: file
        path: "workflow_logs/centralized/app.log"
        format: text
        max_size: "50MB"
        backup_count: 10
      - type: file
        path: "workflow_logs/centralized/app.json"
        format: json
        max_size: "50MB"
        backup_count: 10
      - type: file
        path: "workflow_logs/centralized/app.csv"
        format: csv
        max_size: "50MB"
        backup_count: 10
      - type: console
        level: INFO
        format: json
  
  # Critical errors only - syslog and GELF formats
  CRITICAL:
    level: ERROR
    destinations:
      - type: file
        path: "workflow_logs/centralized/errors.log"
        format: syslog
        max_size: "10MB"
        backup_count: 5
      - type: file
        path: "workflow_logs/centralized/errors.gelf"
        format: gelf
        max_size: "10MB"
        backup_count: 5
      - type: console
        level: ERROR
        format: json
"""

    # Create config directory
    config_dir = Path("demos/examples/config_examples")
    config_dir.mkdir(parents=True, exist_ok=True)

    # Write configuration files
    with open(config_dir / "workflow_distributed_config.yaml", "w") as f:
        f.write(distributed_config.strip())

    with open(config_dir / "workflow_centralized_config.yaml", "w") as f:
        f.write(centralized_config.strip())

    print("✅ Created logging configuration files:")
    print(f"   📄 {config_dir / 'workflow_distributed_config.yaml'}")
    print(f"   📄 {config_dir / 'workflow_centralized_config.yaml'}")


def run_distributed_logging_demo():
    """Run the distributed logging demo with multiple formats."""
    print("\n" + "=" * 60)
    print("🚀 DISTRIBUTED LOGGING DEMO (Multi-Format)")
    print("=" * 60)
    print("Each module logs to its own file + centralized master log")
    print("Formats: text, JSON, CSV, syslog, GELF")

    # Load distributed logging configuration
    config_path = "demos/examples/config_examples/workflow_distributed_config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return

    logger = HydraLogger.from_config(config_path)

    # Import modules
    try:
        from demos.demo_modules.api_client import APIClient
        from demos.demo_modules.database_handler import DatabaseHandler
        from demos.demo_modules.helpers import Utils
        from demos.demo_modules.notification_service import NotificationService
        from demos.demo_modules.user_manager import UserManager
    except ImportError as e:
        print(f"❌ Failed to import demo modules: {e}")
        print("Make sure all demo modules are available")
        return

    # Initialize components
    user_mgr = UserManager(logger)
    db_handler = DatabaseHandler(logger)
    api_client = APIClient(logger)
    notification_service = NotificationService(logger)
    utils = Utils(logger)

    # Simulate application workflow
    logger.info("MASTER", "Starting distributed logging demo workflow")
    start_time = time.time()

    try:
        # Step 1: Database connection
        if db_handler.connect():
            logger.info("MASTER", "Database connected successfully")

        # Step 2: Create user
        user_data = user_mgr.create_user("john_doe", "john@example.com")
        if user_data:
            logger.info("MASTER", f"User created: {user_data['username']}")

        # Step 3: Save to database
        formatted_data = utils.format_user_data(user_data)
        if db_handler.save_user_data(formatted_data):
            logger.info("MASTER", "User data saved to database")

        # Step 4: Fetch additional data from API
        api_data = api_client.get_user_data(user_data["id"])
        if api_data:
            logger.info("MASTER", "Additional user data fetched from API")

        # Step 5: Send welcome notification
        if notification_service.send_welcome_notification(user_data):
            logger.info("MASTER", "Welcome notification sent")

        # Step 6: Update user profile
        if user_mgr.update_profile(user_data["id"], {"bio": "New bio"}):
            logger.info("MASTER", "User profile updated")

        # Step 7: Update via API
        if api_client.update_user_profile(user_data["id"], {"bio": "Updated bio"}):
            logger.info("MASTER", "User profile updated via API")

        # Step 8: Send notification
        if api_client.send_notification(user_data["id"], "Profile updated!"):
            logger.info("MASTER", "Profile update notification sent")

        # Step 9: Create audit log
        audit_entry = utils.create_audit_log("profile_update", user_data["id"])
        logger.info("MASTER", "Audit log created")

        # Step 10: Log performance metrics
        end_time = time.time()
        duration = end_time - start_time
        logger.info("PERFORMANCE", f"Workflow completed in {duration:.3f} seconds")

        # Step 11: Disconnect database
        db_handler.disconnect()
        logger.info("MASTER", "Database disconnected")

        logger.info("MASTER", "Distributed logging demo completed successfully")

    except Exception as e:
        logger.error("ERRORS", f"Demo workflow failed: {str(e)}")
        raise


def run_centralized_logging_demo():
    """Run the centralized logging demo with multiple formats."""
    print("\n" + "=" * 60)
    print("🎯 CENTRALIZED LOGGING DEMO (Multi-Format)")
    print("=" * 60)
    print("All modules log to a single master file in multiple formats")
    print("Formats: text, JSON, CSV, syslog, GELF")

    # Load centralized logging configuration
    config_path = "demos/examples/config_examples/workflow_centralized_config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return

    logger = HydraLogger.from_config(config_path)

    # Import modules
    try:
        from demos.demo_modules.api_client import APIClient
        from demos.demo_modules.database_handler import DatabaseHandler
        from demos.demo_modules.helpers import Utils
        from demos.demo_modules.notification_service import NotificationService
        from demos.demo_modules.user_manager import UserManager
    except ImportError as e:
        print(f"❌ Failed to import demo modules: {e}")
        print("Make sure all demo modules are available")
        return

    # Initialize components
    user_mgr = UserManager(logger)
    db_handler = DatabaseHandler(logger)
    api_client = APIClient(logger)
    notification_service = NotificationService(logger)
    utils = Utils(logger)

    # Simulate application workflow
    logger.info("APP", "Starting centralized logging demo workflow")
    start_time = time.time()

    try:
        # Step 1: Database connection
        if db_handler.connect():
            logger.info("APP", "Database connected successfully")

        # Step 2: Create multiple users
        users = []
        for i in range(3):
            user_data = user_mgr.create_user(f"user_{i}", f"user{i}@example.com")
            if user_data:
                users.append(user_data)
                logger.info("APP", f"User created: {user_data['username']}")

        # Step 3: Process each user
        for user in users:
            # Save to database
            formatted_data = utils.format_user_data(user)
            if db_handler.save_user_data(formatted_data):
                logger.info("APP", f"User data saved: {user['username']}")

            # Fetch API data
            api_data = api_client.get_user_data(user["id"])
            if api_data:
                logger.info("APP", f"API data fetched: {user['username']}")

            # Send notification
            if notification_service.send_welcome_notification(user):
                logger.info("APP", f"Welcome sent: {user['username']}")

        # Step 4: Simulate some errors
        try:
            # This will fail
            user_mgr.authenticate_user("nonexistent", "wrong")
        except:
            logger.error("CRITICAL", "Authentication error (expected)")

        try:
            # This will also fail
            api_client.get_user_data(99999)
        except:
            logger.warning("APP", "API error (expected)")

        # Step 5: Log performance metrics
        end_time = time.time()
        duration = end_time - start_time
        logger.info("APP", f"Workflow completed in {duration:.3f} seconds")

        # Step 6: Cleanup
        db_handler.disconnect()
        logger.info("APP", "Database disconnected")

        logger.info("APP", "Centralized logging demo completed successfully")

    except Exception as e:
        logger.error("CRITICAL", f"Demo workflow failed: {str(e)}")
        raise


def show_log_structure():
    """Show the generated log structure with format information."""
    print("\n" + "=" * 60)
    print("📁 GENERATED LOG STRUCTURE (Multi-Format)")
    print("=" * 60)

    # Find all log files
    log_files = list(Path(".").rglob("workflow_logs/**/*.*"))
    log_files = [f for f in log_files if f.suffix in ['.log', '.json', '.csv', '.gelf']]

    if not log_files:
        print("❌ No log files found. Run the demos first!")
        return

    # Group by directory
    log_structure = {}
    for log_file in sorted(log_files):
        relative_path = log_file.relative_to(Path("."))
        directory = str(relative_path.parent)

        if directory not in log_structure:
            log_structure[directory] = []

        file_info = {
            "name": relative_path.name,
            "size": log_file.stat().st_size if log_file.exists() else 0,
            "format": log_file.suffix[1:] if log_file.suffix else "unknown"
        }
        log_structure[directory].append(file_info)

    # Display structure
    for directory, files in log_structure.items():
        print(f"\n📂 {directory}/")
        for file_info in files:
            size_str = f"{file_info['size']} bytes" if file_info['size'] > 0 else "empty"
            format_emoji = {
                "log": "📄",
                "json": "📊",
                "csv": "📈",
                "gelf": "📋"
            }.get(file_info['format'], "📄")
            print(f"   {format_emoji} {file_info['name']} ({size_str}) [{file_info['format'].upper()}]")

    # Show sample content from different formats
    print(f"\n📋 Sample log content:")
    
    # Text format sample
    master_log = Path("workflow_logs/master/app.log")
    if master_log.exists():
        print(f"\n📄 Text format sample ({master_log}):")
        with open(master_log, "r") as f:
            lines = f.readlines()
            for line in lines[-3:]:  # Last 3 lines
                print(f"   {line.strip()}")
    
    # JSON format sample
    master_json = Path("workflow_logs/master/app.json")
    if master_json.exists():
        print(f"\n📊 JSON format sample ({master_json}):")
        with open(master_json, "r") as f:
            lines = f.readlines()
            for line in lines[-2:]:  # Last 2 lines
                print(f"   {line.strip()}")
    
    # CSV format sample
    db_csv = Path("workflow_logs/modules/database_analytics.csv")
    if db_csv.exists():
        print(f"\n📈 CSV format sample ({db_csv}):")
        with open(db_csv, "r") as f:
            lines = f.readlines()
            for line in lines[-2:]:  # Last 2 lines
                print(f"   {line.strip()}")


def main():
    """Main function to run the multi-file workflow demo."""
    print("🚀 Multi-File Workflow Demo for Hydra-Logger (Multi-Format)")
    print("=" * 60)
    print("This demo shows how to set up logging across multiple Python files")
    print("and classes with both distributed and centralized approaches.")
    print("Supports multiple log formats: text, JSON, CSV, syslog, GELF")

    # Create necessary files and directories
    create_logging_configs()

    # Run demos
    try:
        run_distributed_logging_demo()
        run_centralized_logging_demo()

        # Show results
        show_log_structure()

        print("\n" + "=" * 60)
        print("✅ Multi-File Workflow Demo Completed!")
        print("=" * 60)
        print("\n📚 What you learned:")
        print("   • How to set up logging across multiple Python files")
        print("   • Distributed logging (each module to its own file)")
        print("   • Centralized logging (all modules to one master file)")
        print("   • Class-based logging with proper context")
        print("   • Cross-module logging with consistent formatting")
        print("   • Error tracking across the entire application")
        print("   • Multiple log formats (text, JSON, CSV, syslog, GELF)")
        print("   • Performance monitoring and analytics")

        print("\n📁 Check the generated logs:")
        print("   • Distributed: workflow_logs/modules/ (individual files)")
        print("   • Centralized: workflow_logs/centralized/ (single file)")
        print("   • Master log: workflow_logs/master/ (everything)")
        print("   • Errors: workflow_logs/errors/ (critical issues)")
        print("   • Performance: workflow_logs/performance/ (metrics)")

        print("\n🎯 Format examples:")
        print("   • Text (.log): Human-readable logs")
        print("   • JSON (.json): Structured data for analysis")
        print("   • CSV (.csv): Analytics and reporting")
        print("   • Syslog (.log): System integration")
        print("   • GELF (.gelf): Graylog integration")

    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
