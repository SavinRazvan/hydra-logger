#!/usr/bin/env python3
"""
🗂️ File Organization: Organize logs by purpose

What you'll learn:
- Organize logs by component
- Separate logs by purpose
- Professional log structure
- Log organization best practices

Time: 15 minutes
Difficulty: Intermediate
"""

import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_file_organization():
    """Step-by-step file organization guide."""
    print("🗂️ File Organization")
    print("=" * 40)
    
    # Step 1: Understanding log organization
    print("\n📊 Step 1: Understanding Log Organization")
    print("Why organize logs by purpose:")
    print("  🎯 Easier to find specific information")
    print("  📊 Better for log analysis")
    print("  🔍 Simpler debugging")
    print("  📈 Improved performance")
    print("  🛡️ Better security monitoring")
    
    # Step 2: Create organized directory structure
    print("\n📁 Step 2: Create Organized Directory Structure")
    print("Creating professional log directory structure...")
    
    # Create organized directory structure
    directories = [
        "logs/organized/app",
        "logs/organized/database", 
        "logs/organized/api",
        "logs/organized/security",
        "logs/organized/performance"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ Created: {directory}")
    
    # Step 3: Application logs
    print("\n📱 Step 3: Application Logs")
    print("Creating application-specific logging...")
    
    app_config = LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/organized/app/app.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    app_logger = HydraLogger(app_config)
    
    print("✅ Application logging configured!")
    print("   - Path: logs/organized/app/app.log")
    print("   - Purpose: General application events")
    
    # Step 4: Log application events
    print("\n📝 Step 4: Log Application Events")
    print("Logging application-specific events...")
    
    app_logger.info("APP", "Application started")
    app_logger.info("APP", "User session created", user_id="123", session_id="abc123")
    app_logger.info("APP", "Configuration loaded", config_version="1.2.3")
    app_logger.warning("APP", "Feature flag enabled", feature="beta_dashboard")
    
    print("✅ Application events logged!")
    
    # Step 5: Database logs
    print("\n🗄️ Step 5: Database Logs")
    print("Creating database-specific logging...")
    
    db_config = LoggingConfig(
        layers={
            "DB": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/organized/database/db.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    db_logger = HydraLogger(db_config)
    
    print("✅ Database logging configured!")
    print("   - Path: logs/organized/database/db.log")
    print("   - Purpose: Database operations and queries")
    
    # Step 6: Log database events
    print("\n📝 Step 6: Log Database Events")
    print("Logging database-specific events...")
    
    db_logger.info("DB", "Database connection established")
    db_logger.info("DB", "Query executed", query="SELECT * FROM users", duration="150ms")
    db_logger.info("DB", "Transaction committed", table="orders", rows_affected=5)
    db_logger.warning("DB", "Slow query detected", query="SELECT * FROM logs", duration="2.5s")
    
    print("✅ Database events logged!")
    
    # Step 7: API logs
    print("\n🌐 Step 7: API Logs")
    print("Creating API-specific logging...")
    
    api_config = LoggingConfig(
        layers={
            "API": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/organized/api/api.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    api_logger = HydraLogger(api_config)
    
    print("✅ API logging configured!")
    print("   - Path: logs/organized/api/api.log")
    print("   - Purpose: API requests and responses")
    
    # Step 8: Log API events
    print("\n📝 Step 8: Log API Events")
    print("Logging API-specific events...")
    
    api_logger.info("API", "API request received", method="GET", endpoint="/api/users")
    api_logger.info("API", "Response sent", status_code=200, response_time="45ms")
    api_logger.info("API", "Authentication successful", user_id="123", ip="192.168.1.100")
    api_logger.warning("API", "Rate limit approaching", user_id="123", requests=95)
    
    print("✅ API events logged!")
    
    # Step 9: Security logs
    print("\n🛡️ Step 9: Security Logs")
    print("Creating security-specific logging...")
    
    security_config = LoggingConfig(
        layers={
            "SECURITY": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/organized/security/security.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    security_logger = HydraLogger(security_config)
    
    print("✅ Security logging configured!")
    print("   - Path: logs/organized/security/security.log")
    print("   - Purpose: Security events and alerts")
    
    # Step 10: Log security events
    print("\n📝 Step 10: Log Security Events")
    print("Logging security-specific events...")
    
    security_logger.warning("SECURITY", "Failed login attempt", user_id="unknown", ip="192.168.1.200")
    security_logger.warning("SECURITY", "Suspicious activity detected", user_id="123", activity="multiple_failed_logins")
    security_logger.error("SECURITY", "Unauthorized access attempt", endpoint="/admin", ip="10.0.0.50")
    security_logger.info("SECURITY", "Password changed successfully", user_id="123")
    
    print("✅ Security events logged!")
    
    # Step 11: Performance logs
    print("\n⚡ Step 11: Performance Logs")
    print("Creating performance-specific logging...")
    
    perf_config = LoggingConfig(
        layers={
            "PERF": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/organized/performance/perf.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    perf_logger = HydraLogger(perf_config)
    
    print("✅ Performance logging configured!")
    print("   - Path: logs/organized/performance/perf.log")
    print("   - Purpose: Performance metrics and monitoring")
    
    # Step 12: Log performance events
    print("\n📝 Step 12: Log Performance Events")
    print("Logging performance-specific events...")
    
    perf_logger.info("PERF", "Memory usage", memory_mb=512, memory_percent=25)
    perf_logger.info("PERF", "CPU usage", cpu_percent=15, load_average=0.5)
    perf_logger.info("PERF", "Response time", endpoint="/api/users", response_time="45ms")
    perf_logger.warning("PERF", "High memory usage", memory_mb=1024, memory_percent=80)
    
    print("✅ Performance events logged!")
    
    # Step 13: Check organized structure
    print("\n📁 Step 13: Check Organized Structure")
    print("Organized log files created:")
    
    files_to_check = [
        ("logs/organized/app/app.log", "Application Logs"),
        ("logs/organized/database/db.log", "Database Logs"),
        ("logs/organized/api/api.log", "API Logs"),
        ("logs/organized/security/security.log", "Security Logs"),
        ("logs/organized/performance/perf.log", "Performance Logs")
    ]
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                print(f"   📄 {description}: {len(lines)} lines")
        else:
            print(f"   ❌ {description}: File not found")
    
    # Step 14: Organization benefits
    print("\n💡 Step 14: Organization Benefits")
    print("Benefits of organized logging:")
    print("  🎯 Easier debugging - find specific issues quickly")
    print("  📊 Better analysis - analyze specific components")
    print("  🔍 Targeted monitoring - monitor specific areas")
    print("  📈 Performance - smaller files are faster to process")
    print("  🛡️ Security - separate security events for monitoring")
    print("  📋 Compliance - organized logs for audit requirements")
    
    # Step 15: Best practices
    print("\n🎯 Step 15: Best Practices")
    print("Log organization best practices:")
    print("  ✅ Organize by component or purpose")
    print("  ✅ Use meaningful directory names")
    print("  ✅ Separate concerns (app, db, api, security)")
    print("  ✅ Use appropriate log levels for each component")
    print("  ✅ Plan for log analysis and monitoring")
    print("  ✅ Consider log retention policies")
    
    # Step 16: Next steps
    print("\n🎯 Step 16: Next Steps")
    print("You've learned file organization!")
    print("\nNext modules to try:")
    print("  📊 04_simple_config - Custom configuration")
    print("  🔄 06_rotation - Log file rotation")
    print("  🏗️  05_multiple_layers - Multi-layered logging")
    
    print("\n🎉 File organization completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_file_organization() 