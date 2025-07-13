#!/usr/bin/env python3
"""
Async Reliability Features Example

This example demonstrates reliability features including flush, shutdown, and error handling.
Shows how to use AsyncHydraLogger for reliable logging scenarios.
"""

import asyncio
import time
from hydra_logger.async_hydra import AsyncHydraLogger


async def flush_and_await_demo():
    """Demonstrate flush and await capabilities."""
    print("=== Flush and Await Demo ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Log some messages
    await logger.info("FLUSH", "Starting flush demonstration")
    await logger.info("FLUSH", "Logging messages that will be flushed")
    await logger.info("FLUSH", "Ensuring all messages are written before continuing")
    
    # Simulate flush operation
    await logger.info("FLUSH", "Flushing pending messages...")
    await asyncio.sleep(0.1)  # Simulate flush time
    await logger.info("FLUSH", "All messages flushed successfully")
    
    await logger.aclose()


async def graceful_shutdown_demo():
    """Demonstrate graceful shutdown capabilities."""
    print("\n=== Graceful Shutdown Demo ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    async def log_messages():
        """Simulate background logging."""
        for i in range(10):
            await logger.info("SHUTDOWN", f"Background message {i+1}/10")
            await asyncio.sleep(0.1)
    
    # Start background logging
    await logger.info("SHUTDOWN", "Starting graceful shutdown demonstration")
    await logger.info("SHUTDOWN", "Background logging will continue during shutdown")
    
    # Start background task
    task = asyncio.create_task(log_messages())
    
    # Wait a bit, then shutdown
    await asyncio.sleep(0.5)
    await logger.info("SHUTDOWN", "Initiating graceful shutdown...")
    
    # Shutdown the logger
    await logger.aclose()
    
    # Wait for background task to complete
    await task
    
    print("Graceful shutdown completed")


async def test_events_demo():
    """Demonstrate test events and monitoring."""
    print("\n=== Test Events Demo ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate test events
    await logger.info("TEST", "Test event: Application startup")
    await logger.info("TEST", "Test event: Configuration loaded")
    await logger.info("TEST", "Test event: Database connection established")
    await logger.info("TEST", "Test event: Cache initialized")
    await logger.info("TEST", "Test event: All systems ready")
    
    # Simulate test completion
    await logger.info("TEST", "Test event: All tests passed")
    await logger.info("TEST", "Test event: Application shutdown")
    
    await logger.aclose()


async def data_protection_demo():
    """Demonstrate data protection features."""
    print("\n=== Data Protection Demo ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate data protection scenarios
    await logger.info("PROTECTION", "Data protection enabled")
    await logger.info("PROTECTION", "Sensitive data will be automatically sanitized")
    await logger.info("PROTECTION", "PII detection active")
    await logger.info("PROTECTION", "Encryption enabled for sensitive logs")
    
    # Simulate sensitive data logging (would be sanitized in real implementation)
    await logger.info("PROTECTION", "User data: [REDACTED]")
    await logger.info("PROTECTION", "Credit card: [REDACTED]")
    await logger.info("PROTECTION", "Password: [REDACTED]")
    
    await logger.aclose()


async def error_handling_demo():
    """Demonstrate error handling capabilities."""
    print("\n=== Error Handling Demo ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate various error scenarios
    await logger.error("ERROR", "Database connection failed")
    await logger.error("ERROR", "External API timeout")
    await logger.error("ERROR", "File system error")
    await logger.error("ERROR", "Memory allocation failed")
    await logger.error("ERROR", "Network timeout")
    
    # Simulate recovery
    await logger.info("RECOVERY", "Attempting to reconnect to database")
    await logger.info("RECOVERY", "Retrying API call with exponential backoff")
    await logger.info("RECOVERY", "Switching to backup file system")
    await logger.info("RECOVERY", "Freeing memory and retrying")
    await logger.info("RECOVERY", "Switching to backup network")
    
    await logger.aclose()


async def concurrent_reliability_demo():
    """Demonstrate concurrent reliability features."""
    print("\n=== Concurrent Reliability Demo ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    async def worker(worker_id: int, message_count: int):
        """Worker function for concurrent reliability testing."""
        for i in range(message_count):
            await logger.info("CONCURRENT", f"Worker {worker_id} - Message {i+1}/{message_count}")
            await asyncio.sleep(0.01)  # Small delay to simulate work
    
    # Start multiple concurrent workers
    workers = 3
    messages_per_worker = 10
    
    await logger.info("CONCURRENT", f"Starting {workers} concurrent workers")
    await logger.info("CONCURRENT", f"Each worker will log {messages_per_worker} messages")
    
    # Create and run all workers concurrently
    tasks = [worker(i+1, messages_per_worker) for i in range(workers)]
    await asyncio.gather(*tasks)
    
    await logger.info("CONCURRENT", f"All {workers} workers completed successfully")
    await logger.info("CONCURRENT", f"Total messages logged: {workers * messages_per_worker}")
    
    await logger.aclose()


async def shutdown_scenarios_demo():
    """Demonstrate various shutdown scenarios."""
    print("\n=== Shutdown Scenarios Demo ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    async def rapid_logging():
        """Simulate rapid logging during shutdown."""
        for i in range(20):
            await logger.info("SHUTDOWN", f"Rapid message {i+1}/20")
            await asyncio.sleep(0.01)
    
    async def slow_logging():
        """Simulate slow logging during shutdown."""
        for i in range(5):
            await logger.info("SHUTDOWN", f"Slow message {i+1}/5")
            await asyncio.sleep(0.1)
    
    await logger.info("SHUTDOWN", "Starting shutdown scenarios demonstration")
    
    # Start both rapid and slow logging
    rapid_task = asyncio.create_task(rapid_logging())
    slow_task = asyncio.create_task(slow_logging())
    
    # Wait a bit, then shutdown
    await asyncio.sleep(0.2)
    await logger.info("SHUTDOWN", "Initiating shutdown with pending messages...")
    
    # Shutdown the logger
    await logger.aclose()
    
    # Wait for tasks to complete
    await rapid_task
    await slow_task
    
    await logger.info("SHUTDOWN", "Shutdown scenarios completed")


async def recovery_demo():
    """Demonstrate recovery capabilities."""
    print("\n=== Recovery Demo ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate failure and recovery scenarios
    await logger.info("RECOVERY", "System starting up")
    await logger.info("RECOVERY", "All components healthy")
    
    # Simulate a failure
    await logger.error("RECOVERY", "Database connection lost")
    await logger.error("RECOVERY", "Cache service unavailable")
    await logger.error("RECOVERY", "External API down")
    
    # Simulate recovery attempts
    await logger.info("RECOVERY", "Attempting database reconnection...")
    await logger.info("RECOVERY", "Database reconnected successfully")
    
    await logger.info("RECOVERY", "Attempting cache service restart...")
    await logger.info("RECOVERY", "Cache service restored")
    
    await logger.info("RECOVERY", "Attempting API failover...")
    await logger.info("RECOVERY", "Switched to backup API endpoint")
    
    await logger.info("RECOVERY", "All systems recovered")
    await logger.info("RECOVERY", "System fully operational")
    
    await logger.aclose()


async def main():
    """Run all reliability feature examples."""
    print("=== Async Reliability Features Examples ===")
    print("Demonstrating various reliability features.\n")
    
    await flush_and_await_demo()
    await graceful_shutdown_demo()
    await test_events_demo()
    await data_protection_demo()
    await error_handling_demo()
    await concurrent_reliability_demo()
    await shutdown_scenarios_demo()
    await recovery_demo()
    
    print("\n✅ All reliability feature examples completed!")
    print("Check the console output above to see the reliability features.")


if __name__ == "__main__":
    asyncio.run(main()) 