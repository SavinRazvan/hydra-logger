"""
Example: Basic Async Logger Setup with Custom Configuration

This example demonstrates how to properly initialize and customize
Hydra-Logger's async logging capabilities with working file output,
custom colors, and performance monitoring.

Key concepts:
- Proper async logger initialization with custom config
- Working file logging with rotation
- Custom color schemes and formatting
- Performance monitoring and statistics
- Proper cleanup and shutdown
"""

import asyncio
import os
import time
from pathlib import Path
from hydra_logger import AsyncHydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Custom color scheme for better visibility
class CustomColors:
    """Custom color scheme for the logger."""
    HEADER = "\033[95m"      # Purple
    BLUE = "\033[94m"        # Blue
    CYAN = "\033[96m"        # Cyan
    GREEN = "\033[92m"       # Green
    YELLOW = "\033[93m"      # Yellow
    RED = "\033[91m"         # Red
    BOLD = "\033[1m"         # Bold
    UNDERLINE = "\033[4m"    # Underline
    END = "\033[0m"          # End color

async def create_custom_config(logs_dir: str) -> LoggingConfig:
    """
    Create a custom configuration with multiple layers and destinations.
    
    Args:
        logs_dir (str): Directory for log files
        
    Returns:
        LoggingConfig: Custom logging configuration
    """
    return LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file", 
                        path=os.path.join(logs_dir, "app.log"), 
                        format="text",
                        max_size="5MB",
                        backup_count=3
                    ),
                    LogDestination(type="console", format="text")
                ]
            ),
            "DEBUG": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file", 
                        path=os.path.join(logs_dir, "debug.log"), 
                        format="json",
                        max_size="10MB",
                        backup_count=5
                    )
                ]
            ),
            "ERROR": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="file", 
                        path=os.path.join(logs_dir, "error.log"), 
                        format="json",
                        max_size="5MB",
                        backup_count=3
                    ),
                    LogDestination(type="console", format="text")
                ]
            ),
            "SECURITY": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(
                        type="file", 
                        path=os.path.join(logs_dir, "security.log"), 
                        format="json",
                        max_size="5MB",
                        backup_count=3
                    ),
                    LogDestination(type="console", format="text")
                ]
            ),
            "PERFORMANCE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file", 
                        path=os.path.join(logs_dir, "performance.log"), 
                        format="json",
                        max_size="5MB",
                        backup_count=3
                    )
                ]
            )
        },
        default_level="INFO"
    )

async def main():
    """Main example function demonstrating proper async logger setup."""
    
    print(f"{CustomColors.HEADER}{CustomColors.BOLD}🚀 Starting Custom Async Logger Example{CustomColors.END}")
    print(f"{CustomColors.CYAN}{'=' * 60}{CustomColors.END}")
    
    # Ensure logs directory exists
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    print(f"{CustomColors.GREEN}📁 Logs directory: {logs_dir}{CustomColors.END}")
    
    # Create custom configuration
    config = await create_custom_config(logs_dir)
    
    print(f"{CustomColors.BLUE}⚙️  Creating custom configuration...{CustomColors.END}")
    print(f"   • APP layer: File + Console (INFO level)")
    print(f"   • DEBUG layer: File only (DEBUG level)")
    print(f"   • ERROR layer: File + Console (ERROR level)")
    print(f"   • SECURITY layer: File + Console (WARNING level)")
    print(f"   • PERFORMANCE layer: File only (INFO level)")
    
    # Initialize async logger with custom configuration
    logger = AsyncHydraLogger(
        config=config,
        enable_performance_monitoring=True,
        redact_sensitive=True,
        queue_size=2000,
        batch_size=100,
        batch_timeout=0.5
    )
    
    print(f"\n{CustomColors.GREEN}✅ Async logger initialized successfully{CustomColors.END}")
    print(f"{CustomColors.YELLOW}📊 Performance monitoring: {logger.performance_monitoring}{CustomColors.END}")
    print(f"{CustomColors.YELLOW}🔒 Sensitive data redaction: {logger.redact_sensitive}{CustomColors.END}")
    print(f"{CustomColors.YELLOW}📦 Queue size: {logger.queue_size}{CustomColors.END}")
    print(f"{CustomColors.YELLOW}📦 Batch size: {logger.batch_size}{CustomColors.END}")
    print(f"{CustomColors.YELLOW}⏱️  Batch timeout: {logger.batch_timeout}s{CustomColors.END}")
    
    # Wait for logger to initialize
    await asyncio.sleep(0.2)
    
    # Test all logging levels and layers
    print(f"\n{CustomColors.BLUE}📝 Testing all logging levels and layers:{CustomColors.END}")
    
    # APP layer - general application logs
    await logger.info("APP", "🚀 Application started successfully")
    await logger.info("APP", "📁 Configuration loaded from config.yaml")
    await logger.info("APP", "🔗 Database connection established")
    
    # DEBUG layer - detailed debug information
    await logger.debug("DEBUG", "🔍 Processing user request: GET /api/users")
    await logger.debug("DEBUG", "🔍 Database query executed: SELECT * FROM users")
    await logger.debug("DEBUG", "🔍 Cache hit for key: user_profile_123")
    
    # ERROR layer - error messages
    await logger.error("ERROR", "❌ Database connection failed: Connection timeout")
    await logger.error("ERROR", "❌ API request failed: 500 Internal Server Error")
    await logger.error("ERROR", "❌ File not found: /path/to/config.json")
    
    # SECURITY layer - security-related events
    await logger.security("SECURITY", "🔐 User authentication attempt: john.doe@example.com")
    await logger.security("SECURITY", "🔐 Failed login attempt from IP: 192.168.1.100")
    await logger.security("SECURITY", "🔐 Password reset requested for: jane.smith@example.com")
    
    # PERFORMANCE layer - performance metrics
    await logger.info("PERFORMANCE", "⚡ API response time: 45ms")
    await logger.info("PERFORMANCE", "⚡ Database query time: 12ms")
    await logger.info("PERFORMANCE", "⚡ Memory usage: 128MB")
    
    # Wait for messages to be processed
    await asyncio.sleep(0.5)
    
    # Get and display performance statistics
    print(f"\n{CustomColors.BLUE}📊 Performance Statistics:{CustomColors.END}")
    stats = await logger.get_async_performance_statistics()
    
    if stats:
        print(f"{CustomColors.GREEN}📈 Total messages: {stats.get('total_messages', 0)}{CustomColors.END}")
        print(f"{CustomColors.GREEN}⏱️  Average processing time: {stats.get('avg_processing_time', 0):.2f}ms{CustomColors.END}")
        print(f"{CustomColors.GREEN}🚀 Messages per second: {stats.get('messages_per_second', 0):.2f}{CustomColors.END}")
        print(f"{CustomColors.RED}❌ Total errors: {stats.get('total_errors', 0)}{CustomColors.END}")
        print(f"{CustomColors.RED}📊 Error rate: {stats.get('error_rate', 0):.2f}%{CustomColors.END}")
        print(f"{CustomColors.CYAN}⏰ Uptime: {stats.get('uptime_seconds', 0):.2f}s{CustomColors.END}")
    else:
        print(f"{CustomColors.YELLOW}📊 Performance monitoring disabled{CustomColors.END}")
    
    # Demonstrate concurrent logging
    print(f"\n{CustomColors.BLUE}🔄 Concurrent logging example:{CustomColors.END}")
    
    async def log_concurrent_message(i: int):
        """Log a message with delay."""
        await asyncio.sleep(0.01 * i)  # Staggered delays
        await logger.info("APP", f"🔄 Concurrent message {i} from task {i}")
    
    # Create multiple concurrent logging tasks
    tasks = [log_concurrent_message(i) for i in range(10)]
    await asyncio.gather(*tasks)
    
    print(f"{CustomColors.GREEN}✅ All concurrent messages logged{CustomColors.END}")
    
    # Wait for final processing
    await asyncio.sleep(0.3)
    
    # Get final statistics
    final_stats = await logger.get_async_performance_statistics()
    if final_stats:
        print(f"\n{CustomColors.GREEN}📈 Final message count: {final_stats.get('total_messages', 0)}{CustomColors.END}")
    
    # Check log files
    print(f"\n{CustomColors.BLUE}📁 Checking log files:{CustomColors.END}")
    log_files = [
        "app.log",
        "debug.log", 
        "error.log",
        "security.log",
        "performance.log"
    ]
    
    for log_file in log_files:
        file_path = os.path.join(logs_dir, log_file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"{CustomColors.GREEN}✅ {log_file}: {size} bytes{CustomColors.END}")
        else:
            print(f"{CustomColors.RED}❌ {log_file}: Not found{CustomColors.END}")
    
    # Proper cleanup
    print(f"\n{CustomColors.BLUE}🧹 Cleaning up...{CustomColors.END}")
    await logger.close()
    print(f"{CustomColors.GREEN}✅ Async logger closed successfully{CustomColors.END}")
    
    print(f"\n{CustomColors.HEADER}{CustomColors.BOLD}🎉 Custom async logger example completed!{CustomColors.END}")
    print(f"{CustomColors.CYAN}{'=' * 60}{CustomColors.END}")
    print(f"{CustomColors.YELLOW}💡 Check the logs/ directory to see the generated log files{CustomColors.END}")

if __name__ == "__main__":
    asyncio.run(main()) 