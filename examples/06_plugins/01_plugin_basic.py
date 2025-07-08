#!/usr/bin/env python3
"""
Plugin System Example

This example demonstrates the plugin system:
- Custom analytics plugin
- Plugin registration and usage
- Plugin lifecycle management
- Custom plugin development
"""

from hydra_logger import HydraLogger, register_plugin, get_plugin, AnalyticsPlugin

class CustomAnalyticsPlugin(AnalyticsPlugin):
    """Custom analytics plugin for demonstration."""
    
    def __init__(self):
        self.log_count = 0
        self.error_count = 0
        self.warning_count = 0
    
    def process_event(self, event: dict):
        """Process each log event for analytics."""
        level = event.get('level', 'INFO')
        message = event.get('message', '')
        
        self.log_count += 1
        
        if level.upper() == "ERROR":
            self.error_count += 1
        elif level.upper() == "WARNING":
            self.warning_count += 1
        
        # Print analytics info (in real app, this would go to analytics service)
        print(f"📊 Analytics: {level} - {message} (Total: {self.log_count}, Errors: {self.error_count}, Warnings: {self.warning_count})")
    
    def get_insights(self):
        """Get analytics insights."""
        return {
            "total_logs": self.log_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "success_rate": ((self.log_count - self.error_count) / self.log_count * 100) if self.log_count > 0 else 0
        }

def demo_plugin_system():
    """Demonstrate the plugin system."""
    
    print("🔌 Plugin System Example")
    print("=" * 50)
    
    # Register custom analytics plugin
    register_plugin("custom_analytics", CustomAnalyticsPlugin)
    
    print("🔧 Plugin registered: CustomAnalyticsPlugin")
    
    # Create logger with plugins enabled
    logger = HydraLogger(enable_plugins=True)
    
    print("🚀 Starting logging with plugin system...")
    
    # Log messages that will be processed by the plugin
    logger.info("DEFAULT", "Application started")
    logger.info("DEFAULT", "Configuration loaded")
    logger.warning("DEFAULT", "High memory usage detected")
    logger.error("DEFAULT", "Authentication failed")
    logger.info("DEFAULT", "Query executed")
    logger.warning("DEFAULT", "Rate limit approaching")
    logger.error("DEFAULT", "Connection timeout")
    
    print("\n📊 Analytics Summary:")
    
    # Get analytics summary from the plugin
    plugin_class = get_plugin("custom_analytics")
    if plugin_class:
        # Create an instance to get insights
        plugin_instance = plugin_class()
        insights = plugin_instance.get_insights()
        print(f"   Total logs: {insights['total_logs']}")
        print(f"   Errors: {insights['error_count']}")
        print(f"   Warnings: {insights['warning_count']}")
        print(f"   Success rate: {insights['success_rate']:.1f}%")
    
    print("\n✅ Plugin system example completed!")
    print("💡 The plugin processed each log message and provided analytics")

if __name__ == "__main__":
    demo_plugin_system() 