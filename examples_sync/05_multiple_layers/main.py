#!/usr/bin/env python3
"""
05 - Multiple Layers

This example demonstrates multi-layered logging with Hydra-Logger.
Shows how to organize logs by different concerns and purposes.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time

def main():
    """Demonstrate multi-layered logging."""
    
    print("🏗️ Multiple Layers Demo")
    print("=" * 40)
    
    # Create multi-layer configuration
    config = LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/app/main.log",
                        format="text"
                    ),
                    LogDestination(
                        type="console",
                        level="WARNING",
                        format="text"
                    )
                ]
            ),
            "API": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/api/requests.log",
                        format="json"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/api/errors.log",
                        format="text"
                    )
                ]
            ),
            "DB": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/database/queries.log",
                        format="text"
                    )
                ]
            ),
            "SECURITY": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/security/auth.log",
                        format="syslog"
                    ),
                    LogDestination(
                        type="console",
                        level="ERROR",
                        format="text"
                    )
                ]
            ),
            "PERFORMANCE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/performance/metrics.csv",
                        format="csv"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    # Simulate application startup
    print("\n🚀 Application Startup")
    print("-" * 20)
    logger.info("APP", "Application starting up")
    logger.info("APP", "Configuration loaded successfully")
    logger.info("APP", "Database connection established")
    
    # Simulate API requests
    print("\n🌐 API Requests")
    print("-" * 20)
    
    # Request 1
    start_time = time.time()
    logger.info("API", "API request started", method="GET", endpoint="/api/users", user_id="123")
    logger.debug("DB", "SQL Query", query="SELECT * FROM users WHERE id = 123", duration="50ms")
    time.sleep(0.1)  # Simulate processing
    response_time = (time.time() - start_time) * 1000
    logger.info("API", "API request completed", method="GET", endpoint="/api/users", status_code=200, duration=f"{response_time:.2f}ms")
    logger.info("PERFORMANCE", "API Response Time", endpoint="/api/users", duration=f"{response_time:.2f}ms")
    
    # Request 2
    start_time = time.time()
    logger.info("API", "API request started", method="POST", endpoint="/api/users", user_id="456")
    logger.debug("DB", "SQL Query", query="INSERT INTO users (name, email) VALUES ('John', 'john@example.com')", duration="75ms")
    time.sleep(0.15)  # Simulate processing
    response_time = (time.time() - start_time) * 1000
    logger.info("API", "API request completed", method="POST", endpoint="/api/users", status_code=201, duration=f"{response_time:.2f}ms")
    logger.info("PERFORMANCE", "API Response Time", endpoint="/api/users", duration=f"{response_time:.2f}ms")
    
    # Simulate security events
    print("\n🔒 Security Events")
    print("-" * 20)
    logger.info("SECURITY", "User login successful", user_id="123", ip="192.168.1.100")
    logger.warning("SECURITY", "Failed login attempt", user_id="unknown", ip="192.168.1.101")
    logger.error("SECURITY", "Unauthorized access attempt", user_id="unknown", ip="192.168.1.102", endpoint="/admin")
    logger.info("SECURITY", "Password changed", user_id="123", ip="192.168.1.100")
    
    # Simulate errors
    print("\n❌ Error Handling")
    print("-" * 20)
    logger.error("API", "Database connection failed", error="Connection timeout", retry_count=3)
    logger.error("DB", "Query execution failed", query="SELECT * FROM non_existent_table", error="Table not found")
    logger.critical("APP", "Critical system error", error="Out of memory", action="restarting")
    
    # Simulate performance monitoring
    print("\n📊 Performance Monitoring")
    print("-" * 20)
    logger.info("PERFORMANCE", "Memory Usage", memory_mb=512, max_memory_mb=1024)
    logger.info("PERFORMANCE", "CPU Usage", cpu_percent=45.2, load_average=1.2)
    logger.info("PERFORMANCE", "Active Connections", connections=25, max_connections=100)
    
    # Application shutdown
    print("\n🛑 Application Shutdown")
    print("-" * 20)
    logger.info("APP", "Graceful shutdown initiated")
    logger.info("APP", "Database connections closed")
    logger.info("APP", "Application shutdown complete")
    
    print("\n✅ Multiple layers demo completed!")
    print("📝 Check the logs/ directory for organized log files")
    
    # Show the directory structure
    print("\n📁 Generated Log Structure:")
    print("-" * 30)
    import os
    if os.path.exists("logs"):
        for root, dirs, files in os.walk("logs"):
            level = root.replace("logs", "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")

if __name__ == "__main__":
    main() 