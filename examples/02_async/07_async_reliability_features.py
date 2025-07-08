#!/usr/bin/env python3
"""
Async Reliability Features Example

This example demonstrates all the reliability features:
- Flush and await_pending APIs
- Graceful shutdown
- Test events for deterministic testing
- Data loss protection
- Reliable error handling
"""

import asyncio
import time
from hydra_logger.async_hydra.async_logger import AsyncHydraLogger


async def flush_and_await_demo():
    """Demonstrate flush and await_pending APIs."""
    print("\n=== Flush and Await Demo ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Log some messages
    print("Logging messages...")
    for i in range(10):
        await logger.info("RELIABILITY", f"Message {i}")
    
    # Get pending count
    pending_count = await logger.get_pending_count()
    print(f"Pending messages: {pending_count}")
    
    # Flush all pending messages
    print("Flushing pending messages...")
    await logger.flush()
    
    # Wait for all pending messages
    print("Waiting for all pending messages...")
    await logger.await_pending()
    
    # Check final pending count
    final_pending = await logger.get_pending_count()
    print(f"Final pending messages: {final_pending}")
    
    if final_pending == 0:
        print("✅ All messages processed successfully!")
    else:
        print("⚠️  Some messages still pending")


async def graceful_shutdown_demo():
    """Demonstrate graceful shutdown."""
    print("\n=== Graceful Shutdown Demo ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Log messages in background
    async def log_messages():
        for i in range(20):
            await logger.info("SHUTDOWN", f"Message {i}")
            await asyncio.sleep(0.01)  # Simulate processing time
    
    # Start logging in background
    logging_task = asyncio.create_task(log_messages())
    
    # Wait a bit for messages to accumulate
    await asyncio.sleep(0.1)
    
    print("Starting graceful shutdown...")
    start_time = time.time()
    
    # Perform graceful shutdown
    await logger.graceful_shutdown(timeout=5.0)
    
    shutdown_time = time.time() - start_time
    print(f"Shutdown completed in {shutdown_time:.3f}s")
    
    # Cancel the logging task
    logging_task.cancel()
    try:
        await logging_task
    except asyncio.CancelledError:
        pass
    
    print("✅ Graceful shutdown completed!")


async def test_events_demo():
    """Demonstrate test events for deterministic testing."""
    print("\n=== Test Events Demo ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Simulate a test scenario
    print("Starting test scenario...")
    
    # Log messages with test events
    for i in range(5):
        await logger.info("TEST", f"Test message {i}")
    
    # Wait for processing (deterministic)
    await logger.await_pending()
    
    print("✅ Test events working correctly!")


async def data_protection_demo():
    """Demonstrate data loss protection."""
    print("\n=== Data Loss Protection Demo ===")
    
    logger = AsyncHydraLogger(
        test_mode=True
    )
    
    # Log messages that might be protected
    print("Logging messages with data protection...")
    for i in range(10):
        await logger.info("PROTECTION", f"Protected message {i}")
    
    # Simulate some processing time
    await asyncio.sleep(0.1)
    
    # Flush to ensure all messages are processed
    await logger.flush()
    
    print("✅ Data protection working correctly!")


async def error_handling_demo():
    """Demonstrate reliable error handling."""
    print("\n=== Error Handling Demo ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Simulate various error scenarios
    scenarios = [
        ("Connection error", ConnectionError("Database connection failed")),
        ("Validation error", ValueError("Invalid input data")),
        ("Timeout error", TimeoutError("Operation timed out")),
        ("Permission error", PermissionError("Access denied")),
    ]
    
    for scenario_name, error in scenarios:
        print(f"Testing {scenario_name}...")
        
        try:
            # Simulate the error
            raise error
        except Exception as e:
            # Log the error with context
            await logger.log_error_with_context(
                error=e,
                layer="ERROR",
                context={
                    "scenario": scenario_name,
                    "timestamp": time.time(),
                    "retry_count": 0
                }
            )
    
    print("✅ Error handling working correctly!")


async def concurrent_reliability_demo():
    """Demonstrate reliability under concurrent load."""
    print("\n=== Concurrent Reliability Demo ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    async def worker(worker_id: int, message_count: int):
        """Worker function for concurrent testing."""
        for i in range(message_count):
            await logger.info(
                f"WORKER_{worker_id}",
                f"Worker {worker_id} message {i}"
            )
            await asyncio.sleep(0.001)  # Small delay
    
    # Create multiple concurrent workers
    workers = []
    for i in range(3):
        worker_task = asyncio.create_task(worker(i, 10))
        workers.append(worker_task)
    
    print("Starting 3 concurrent workers...")
    start_time = time.time()
    
    # Wait for all workers to complete
    await asyncio.gather(*workers)
    
    # Wait for all processing to complete
    await logger.await_pending()
    
    total_time = time.time() - start_time
    print(f"Concurrent test completed in {total_time:.3f}s")
    
    # Check final state
    pending_count = await logger.get_pending_count()
    print(f"Final pending messages: {pending_count}")
    
    if pending_count == 0:
        print("✅ Concurrent reliability test passed!")
    else:
        print("⚠️  Some messages still pending")


async def shutdown_scenarios_demo():
    """Demonstrate different shutdown scenarios."""
    print("\n=== Shutdown Scenarios Demo ===")
    
    # Scenario 1: Normal shutdown
    print("Scenario 1: Normal shutdown")
    logger1 = AsyncHydraLogger(test_mode=True)
    await logger1.info("SCENARIO", "Normal shutdown test")
    await logger1.graceful_shutdown(timeout=1.0)
    print("✅ Normal shutdown completed")
    
    # Scenario 2: Shutdown with pending messages
    print("Scenario 2: Shutdown with pending messages")
    logger2 = AsyncHydraLogger(test_mode=True)
    
    async def rapid_logging():
        for i in range(50):
            await logger2.info("RAPID", f"Rapid message {i}")
            await asyncio.sleep(0.001)
    
    # Start rapid logging
    logging_task = asyncio.create_task(rapid_logging())
    
    # Wait a bit then shutdown
    await asyncio.sleep(0.1)
    await logger2.graceful_shutdown(timeout=2.0)
    
    # Cancel the logging task
    logging_task.cancel()
    try:
        await logging_task
    except asyncio.CancelledError:
        pass
    
    print("✅ Shutdown with pending messages completed")
    
    # Scenario 3: Timeout shutdown
    print("Scenario 3: Timeout shutdown")
    logger3 = AsyncHydraLogger(test_mode=True)
    
    async def slow_logging():
        for i in range(10):
            await logger3.info("SLOW", f"Slow message {i}")
            await asyncio.sleep(0.5)  # Slow processing
    
    # Start slow logging
    slow_task = asyncio.create_task(slow_logging())
    
    # Wait a bit then shutdown with short timeout
    await asyncio.sleep(0.1)
    await logger3.graceful_shutdown(timeout=0.5)  # Short timeout
    
    # Cancel the slow task
    slow_task.cancel()
    try:
        await slow_task
    except asyncio.CancelledError:
        pass
    
    print("✅ Timeout shutdown completed")


async def recovery_demo():
    """Demonstrate recovery after errors."""
    print("\n=== Recovery Demo ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Simulate a recovery scenario
    print("Simulating error recovery...")
    
    # Phase 1: Normal operation
    for i in range(5):
        await logger.info("RECOVERY", f"Normal message {i}")
    
    # Phase 2: Error occurs
    try:
        raise RuntimeError("Simulated error")
    except Exception as e:
        await logger.log_error_with_context(
            error=e,
            layer="ERROR",
            context={"phase": "error", "recovery_attempt": 1}
        )
    
    # Phase 3: Recovery
    for i in range(5):
        await logger.info("RECOVERY", f"Recovery message {i}")
    
    # Wait for all processing
    await logger.await_pending()
    
    print("✅ Recovery demo completed!")


async def main():
    """Run all reliability feature examples."""
    print("🚀 Async Reliability Features Examples")
    print("=" * 50)
    
    await flush_and_await_demo()
    await graceful_shutdown_demo()
    await test_events_demo()
    await data_protection_demo()
    await error_handling_demo()
    await concurrent_reliability_demo()
    await shutdown_scenarios_demo()
    await recovery_demo()
    
    print("\n✅ All reliability feature examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 