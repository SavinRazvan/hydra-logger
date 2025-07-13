#!/usr/bin/env python3
"""
Basic Magic Configs Example

This example demonstrates how to use built-in magic configs with HydraLogger.
Shows how to use production, development, and other pre-configured setups.
"""

from hydra_logger import HydraLogger


def demo_basic_magic_configs():
    """Demonstrate basic magic config usage."""
    
    print("=== Basic Magic Configs Example ===")
    print("Demonstrating built-in magic configurations.\n")
    
    # List available magic configs
    print("Available Magic Configs:")
    configs = HydraLogger.list_magic_configs()
    for name, description in configs.items():
        print(f"  - {name}: {description}")
    print()
    
    # Production configuration
    print("--- Production Configuration ---")
    logger_prod = HydraLogger.for_production()
    logger_prod.info("APP", "Application started in production mode")
    logger_prod.info("SECURITY", "Security monitoring enabled")
    logger_prod.info("PERFORMANCE", "Performance tracking active")
    logger_prod.close()
    
    # Development configuration
    print("\n--- Development Configuration ---")
    logger_dev = HydraLogger.for_development()
    logger_dev.info("APP", "Application started in development mode")
    logger_dev.debug("DEBUG", "Debug information available")
    logger_dev.info("DEV", "Development features enabled")
    logger_dev.close()
    
    # Testing configuration
    print("\n--- Testing Configuration ---")
    logger_test = HydraLogger.for_testing()
    logger_test.info("TEST", "Test environment initialized")
    logger_test.info("TEST", "Test logging active")
    logger_test.close()
    
    # Microservice configuration
    print("\n--- Microservice Configuration ---")
    logger_micro = HydraLogger.for_microservice()
    logger_micro.info("SERVICE", "Microservice started")
    logger_micro.info("HEALTH", "Health checks enabled")
    logger_micro.close()
    
    # Web app configuration
    print("\n--- Web App Configuration ---")
    logger_web = HydraLogger.for_web_app()
    logger_web.info("WEB", "Web application started")
    logger_web.info("REQUEST", "Request logging enabled")
    logger_web.close()
    
    # API service configuration
    print("\n--- API Service Configuration ---")
    logger_api = HydraLogger.for_api_service()
    logger_api.info("API", "API service started")
    logger_api.info("AUTH", "Authentication logging enabled")
    logger_api.close()
    
    # Background worker configuration
    print("\n--- Background Worker Configuration ---")
    logger_worker = HydraLogger.for_background_worker()
    logger_worker.info("WORKER", "Background worker started")
    logger_worker.info("TASK", "Task processing enabled")
    logger_worker.close()
    
    print("\n✅ All magic config examples completed!")
    print("Each configuration is optimized for its specific use case.")


if __name__ == "__main__":
    demo_basic_magic_configs() 