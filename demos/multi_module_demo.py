#!/usr/bin/env python3
"""
Multi-Module Demo: Demonstrates how different modules use Hydra-Logger in a real application.

This comprehensive example showcases how Hydra-Logger can be used in a realistic
web application environment with multiple modules and specialized logging requirements.

Key Features Demonstrated:
1. Multi-module logging with custom folder paths for each module
2. Different log levels and filtering per module (DEBUG, INFO, ERROR)
3. Multiple destinations per layer (files, console, error-specific files)
4. Real-world module simulation (APP, AUTH, API, DB, PERF, EMAIL)
5. Custom folder structures and file organization
6. Log level filtering and message routing

The demo simulates a web application with authentication, API handling,
database operations, performance monitoring, and email services, each
with their own specialized logging requirements and folder structures.
"""

import os
import random
import time

from hydra_logger import HydraLogger
from hydra_logger.config import LogDestination, LoggingConfig, LogLayer


def create_app_config(log_base_path):
    """
    Create a comprehensive logging configuration for a web application.

    Args:
        log_base_path (str): Base path for all log files.

    Returns:
        LoggingConfig: Complete configuration with multiple layers for
        different application modules and their specific logging needs.

    This configuration demonstrates a realistic web application setup with:
    - APP: Main application logs with console output for warnings
    - AUTH: Security logs with separate error tracking
    - API: Request/response logs with error separation
    - DB: Database operation logs for debugging
    - PERF: Performance metrics and monitoring
    - EMAIL: Email service logs with error tracking
    - MONITORING: Centralized monitoring with GELF format
    """

    return LoggingConfig(
        layers={
            # Application core logs
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "app", "main.log"),
                        max_size="5MB",
                        backup_count=3,
                        format="text"  # Plain text for general application logs
                    ),
                    LogDestination(
                        type="console", 
                        level="WARNING",
                        format="json"  # JSON format for console warnings
                    ),
                ],
            ),
            # Authentication and security logs
            "AUTH": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "auth", "security.log"),
                        max_size="2MB",
                        backup_count=5,
                        format="syslog"  # Syslog format for security integration
                    ),
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "auth", "errors.json"),
                        max_size="1MB",
                        backup_count=10,
                        format="json"  # JSON format for error analysis
                    ),
                ],
            ),
            # API request/response logs
            "API": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "api", "requests.json"),
                        max_size="10MB",
                        backup_count=3,
                        format="json"  # JSON format for structured API logging
                    ),
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "api", "errors.log"),
                        max_size="2MB",
                        backup_count=5,
                        format="text"  # Plain text for error logs
                    ),
                ],
            ),
            # Database operation logs
            "DB": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "database", "queries.log"),
                        max_size="5MB",
                        backup_count=3,
                        format="text"  # Plain text for database queries
                    )
                ],
            ),
            # Performance and metrics logs
            "PERF": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "performance", "metrics.csv"),
                        max_size="3MB",
                        backup_count=2,
                        format="csv"  # CSV format for performance analytics
                    )
                ],
            ),
            # Email service logs
            "EMAIL": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "email", "outgoing.log"),
                        max_size="2MB",
                        backup_count=5,
                        format="text"  # Plain text for email logs
                    ),
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "email", "errors.json"),
                        max_size="1MB",
                        backup_count=3,
                        format="json"  # JSON format for error analysis
                    ),
                ],
            ),
            # Monitoring and alerting logs
            "MONITORING": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(log_base_path, "monitoring", "alerts.gelf"),
                        max_size="2MB",
                        backup_count=3,
                        format="gelf"  # GELF format for centralized logging
                    )
                ],
            ),
        }
    )


class AppModule:
    """
    Simulates the main application module.

    This module handles application lifecycle events including startup,
    configuration loading, and graceful shutdown procedures.
    """

    def __init__(self, logger):
        """
        Initialize the application module.

        Args:
            logger: HydraLogger instance for logging operations.
        """
        self.logger = logger

    def start(self):
        """
        Simulate application startup process.

        Logs the various stages of application initialization including
        configuration loading, database setup, and server startup.
        """
        self.logger.info("APP", "Application starting up...")
        self.logger.info("APP", "Loading configuration files")
        self.logger.info("APP", "Initializing database connections")
        self.logger.info("APP", "Starting web server on port 8000")
        self.logger.info("APP", "Application startup completed successfully")

    def shutdown(self):
        """
        Simulate application shutdown process.

        Logs the graceful shutdown sequence including connection cleanup
        and server shutdown procedures.
        """
        self.logger.warning("APP", "Shutdown signal received")
        self.logger.info("APP", "Closing database connections")
        self.logger.info("APP", "Stopping web server")
        self.logger.info("APP", "Application shutdown completed")


class AuthModule:
    """
    Simulates the authentication module.

    This module handles user authentication, login attempts, and security
    monitoring with detailed logging for security analysis.
    """

    def __init__(self, logger):
        """
        Initialize the authentication module.

        Args:
            logger: HydraLogger instance for logging operations.
        """
        self.logger = logger

    def login_attempt(self, username, ip_address, success=True):
        """
        Simulate a user login attempt.

        Args:
            username (str): The username attempting to log in.
            ip_address (str): The IP address of the login attempt.
            success (bool): Whether the login attempt was successful.

        Logs both successful and failed login attempts with appropriate
        detail levels for security monitoring and debugging.
        """
        self.logger.debug(
            "AUTH", f"Login attempt from {ip_address} for user: {username}"
        )

        if success:
            self.logger.info("AUTH", f"Successful login for user: {username}")
        else:
            self.logger.error(
                "AUTH", f"Failed login attempt for user: {username} from {ip_address}"
            )

    def security_alert(self, message):
        """
        Log a security alert.

        Args:
            message (str): The security alert message.

        Logs critical security events that require immediate attention.
        """
        self.logger.critical("AUTH", f"SECURITY ALERT: {message}")


class APIModule:
    """
    Simulates the API module.

    This module handles HTTP requests and responses with comprehensive
    logging for request tracking and error monitoring.
    """

    def __init__(self, logger):
        """
        Initialize the API module.

        Args:
            logger: HydraLogger instance for logging operations.
        """
        self.logger = logger

    def handle_request(self, method, endpoint, status_code=200):
        """
        Simulate handling an API request.

        Args:
            method (str): HTTP method (GET, POST, etc.).
            endpoint (str): API endpoint path.
            status_code (int): HTTP status code for the response.

        Logs all API requests and separates errors into a dedicated
        error log file for easier monitoring and debugging.
        """
        self.logger.info("API", f"Request: {method} {endpoint}")

        if status_code >= 400:
            self.logger.error("API", f"Error {status_code} for {method} {endpoint}")
        else:
            self.logger.info("API", f"Response {status_code} for {method} {endpoint}")


class DatabaseModule:
    """
    Simulates the database module.

    This module handles database operations with detailed query logging
    for debugging and performance analysis.
    """

    def __init__(self, logger):
        """
        Initialize the database module.

        Args:
            logger: HydraLogger instance for logging operations.
        """
        self.logger = logger

    def execute_query(self, query, params=None):
        """
        Simulate executing a database query.

        Args:
            query (str): The SQL query to execute.
            params (dict, optional): Query parameters.

        Logs query execution details at DEBUG level for development
        and troubleshooting purposes.
        """
        self.logger.debug("DB", f"Executing query: {query}")
        if params:
            self.logger.debug("DB", f"Query parameters: {params}")

        # Simulate query execution time
        time.sleep(0.01)
        self.logger.debug("DB", "Query executed successfully")

    def connection_pool_status(self):
        """
        Log database connection pool status.

        Provides information about active and available database
        connections for monitoring and capacity planning.
        """
        self.logger.info(
            "DB", "Database connection pool status: 5 active, 10 available"
        )


class PerformanceModule:
    """
    Simulates the performance monitoring module.

    This module tracks system performance metrics including CPU usage,
    memory consumption, and response times for monitoring and alerting.
    """

    def __init__(self, logger):
        """
        Initialize the performance monitoring module.

        Args:
            logger: HydraLogger instance for logging operations.
        """
        self.logger = logger

    def record_metrics(self):
        """
        Record and log system performance metrics.

        Simulates collecting performance data and logs key metrics
        including CPU usage, memory consumption, and response times
        for system monitoring and capacity planning.
        """
        cpu_usage = random.uniform(10, 80)
        memory_usage = random.uniform(100, 500)
        response_time = random.uniform(50, 300)

        self.logger.info("PERF", f"CPU Usage: {cpu_usage:.1f}%")
        self.logger.info("PERF", f"Memory Usage: {memory_usage:.1f}MB")
        self.logger.info("PERF", f"Average Response Time: {response_time:.1f}ms")


class EmailModule:
    """
    Simulates the email service module.

    This module handles email sending operations with comprehensive
    logging for delivery tracking and error monitoring.
    """

    def __init__(self, logger):
        """
        Initialize the email service module.

        Args:
            logger: HydraLogger instance for logging operations.
        """
        self.logger = logger

    def send_email(self, to_address, subject, success=True):
        """
        Simulate sending an email.

        Args:
            to_address (str): The recipient email address.
            subject (str): The email subject line.
            success (bool): Whether the email was sent successfully.

        Logs email sending attempts and results, with errors
        tracked separately for monitoring and troubleshooting.
        """
        self.logger.info("EMAIL", f"Sending email to: {to_address}, Subject: {subject}")

        if success:
            self.logger.info("EMAIL", f"Email sent successfully to: {to_address}")
        else:
            self.logger.error("EMAIL", f"Failed to send email to: {to_address}")


def main():
    """
    Main demonstration function.

    This function orchestrates the complete multi-module demo,
    creating the logging configuration, initializing all modules,
    and simulating realistic application activity to demonstrate
    how Hydra-Logger handles complex logging scenarios with different formats.

    The demo creates a comprehensive log structure with separate
    folders for each module and demonstrates various logging
    patterns, error handling scenarios, and different log formats.
    """

    # Create logs directory
    log_base_path = "demo_logs"
    os.makedirs(log_base_path, exist_ok=True)

    print("🚀 Starting Multi-Module Hydra-Logger Demo")
    print(f"📁 Logs will be saved to: {os.path.abspath(log_base_path)}")
    print("📊 Different log formats will be used:")
    print("   - text: Plain text logs for general application logs")
    print("   - json: Structured JSON for API requests and errors")
    print("   - csv: Comma-separated values for performance metrics")
    print("   - syslog: Syslog format for security logs")
    print("   - gelf: GELF format for centralized monitoring")
    print()

    # Create logger with configuration
    config = create_app_config(log_base_path)
    logger = HydraLogger(config)

    # Initialize all modules
    app = AppModule(logger)
    auth = AuthModule(logger)
    api = APIModule(logger)
    db = DatabaseModule(logger)
    perf = PerformanceModule(logger)
    email = EmailModule(logger)

    print("=== Application Startup ===")
    app.start()
    print()

    print("=== Simulating User Activity ===")

    # Simulate user login attempts
    auth.login_attempt("john.doe", "192.168.1.100", success=True)
    auth.login_attempt("jane.smith", "192.168.1.101", success=False)
    auth.login_attempt("admin", "10.0.0.50", success=True)

    # Simulate API requests
    api.handle_request("GET", "/api/users")
    api.handle_request("POST", "/api/users")
    api.handle_request("GET", "/api/users/123")
    api.handle_request("DELETE", "/api/users/999", status_code=404)
    api.handle_request("POST", "/api/auth/login", status_code=401)

    # Simulate database operations
    db.execute_query("SELECT * FROM users WHERE id = ?", [123])
    db.execute_query(
        "INSERT INTO logs (message, timestamp) VALUES (?, ?)",
        ["test log", "2024-01-01"],
    )
    db.execute_query(
        "UPDATE users SET last_login = ? WHERE id = ?", ["2024-01-01", 123]
    )
    db.connection_pool_status()

    # Simulate performance monitoring
    perf.record_metrics()

    # Simulate email sending
    email.send_email("user@example.com", "Welcome to our service!")
    email.send_email("admin@example.com", "System status report")
    email.send_email("invalid@example.com", "Test email", success=False)

    print()
    print("=== Simulating Security Event ===")
    auth.security_alert("Multiple failed login attempts detected from IP 192.168.1.200")

    print()
    print("=== Simulating Monitoring Events ===")
    logger.info("MONITORING", "System health check completed")
    logger.warning("MONITORING", "High memory usage detected: 85%")
    logger.error("MONITORING", "Database connection timeout")

    print()
    print("=== Application Shutdown ===")
    app.shutdown()

    print()
    print("✅ Demo completed!")
    print(f"📁 Check the log files in: {os.path.abspath(log_base_path)}")
    print()

    # Show the created directory structure
    print("📂 Created log structure:")
    for root, dirs, files in os.walk(log_base_path):
        level = root.replace(log_base_path, "").count(os.sep)
        indent = "  " * level
        print(f"{indent}📂 {os.path.basename(root)}/")
        subindent = "  " * (level + 1)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            # Determine format based on file extension
            if file.endswith('.json'):
                format_info = " (JSON format)"
            elif file.endswith('.csv'):
                format_info = " (CSV format)"
            elif file.endswith('.gelf'):
                format_info = " (GELF format)"
            elif 'security' in file:
                format_info = " (Syslog format)"
            else:
                format_info = " (Text format)"
            print(f"{subindent}📄 {file} ({file_size} bytes){format_info}")


if __name__ == "__main__":
    main()
