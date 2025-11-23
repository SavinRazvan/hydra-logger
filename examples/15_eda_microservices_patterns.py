#!/usr/bin/env python3
"""
Example 15: EDA & Microservices Patterns

Demonstrates how to use Hydra-Logger in Event-Driven Architecture (EDA)
and microservices with proper resource management.

Key Patterns:
    1. Long-running async services with proper cleanup
    2. Context managers for automatic resource management
    3. Shared logger instances in microservices
    4. Event-driven logging with correlation IDs
    5. Graceful shutdown handling
"""
import asyncio
import signal
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_async_logger

# ============================================================================
# PATTERN 1: Long-Running Service with Auto-Cleanup (Recommended)
# ============================================================================
# Best practice: Use async context manager for automatic cleanup
# This ensures proper resource cleanup even if errors occur

async def microservice_with_auto_cleanup():
    """Microservice using async context manager - automatic cleanup."""
    config = LoggingConfig(
        layers={
            "service": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/examples/15_microservice_auto.jsonl",
                        format="json-lines"
                    )
                ]
            )
        }
    )
    
    # Auto-cleanup: Context manager automatically closes logger
    async with create_async_logger(config, name="Microservice-Auto") as logger:
        await logger.info("[15] Service starting up", layer="service")
        
        # Simulate long-running service (reduced delays for faster examples)
        for i in range(3):
            await asyncio.sleep(0.01)  # Reduced from 0.1s to 0.01s
            await logger.info(f"[15] Processing event {i}", layer="service")
        
        await logger.info("[15] Service shutting down", layer="service")


# ============================================================================
# PATTERN 2: Shared Logger Instance (Microservices Pattern)
# ============================================================================
# Good practice: Single logger instance per service, reused across handlers

class MicroserviceApp:
    """Example microservice with shared logger instance."""
    
    def __init__(self):
        config = LoggingConfig(
            layers={
                "api": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path="logs/examples/15_microservice_shared.jsonl",
                            format="json-lines"
                        )
                    ]
                ),
                "events": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path="logs/examples/15_microservice_events.jsonl",
                            format="json-lines"
                        )
                    ]
                )
            }
        )
        self.logger = create_async_logger(config, name="Microservice-Shared")
        self._shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the microservice."""
        await self.logger.info("[15] Microservice starting", layer="api")
        
        # Setup graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
        
        # Run main loop
        await self.run()
    
    async def run(self):
        """Main service loop."""
        while not self._shutdown_event.is_set():
            # Process events
            await self.handle_event("event_data_123")
            await asyncio.sleep(0.01)  # Reduced from 0.1s to 0.01s
            # Break after first iteration for example (avoid infinite loop)
            break
    
    async def handle_event(self, event_data: str):
        """Handle an event (EDA pattern)."""
        correlation_id = f"corr-{id(event_data)}"
        await self.logger.info(
            f"[15] Processing event: {event_data}",
            layer="events",
            context={"correlation_id": correlation_id}
        )
    
    async def shutdown(self):
        """Graceful shutdown with proper cleanup."""
        await self.logger.info("[15] Shutdown signal received", layer="api")
        self._shutdown_event.set()
        
        # close_async() ensures all writes complete
        await self.logger.close_async()
        # Note: Don't log after close_async() - logger is closed


# ============================================================================
# PATTERN 3: Event-Driven Architecture with Correlation IDs
# ============================================================================

class EventDrivenService:
    """Event-driven service with correlation tracking."""
    
    def __init__(self):
        config = LoggingConfig(
            layers={
                "event_handler": LogLayer(
                    destinations=[
                        LogDestination(
                            type="file",
                            path="logs/examples/15_eda_service.jsonl",
                            format="json-lines"
                        )
                    ]
                )
            }
        )
        self.logger = create_async_logger(config, name="EDA-Service")
    
    async def process_event(self, event_type: str, payload: dict):
        """Process an event with full traceability."""
        correlation_id = payload.get("correlation_id", f"corr-{id(payload)}")
        
        await self.logger.info(
            f"[15] Event received: {event_type}",
            layer="event_handler",
            context={"correlation_id": correlation_id, "event_type": event_type},
            extra=payload
        )
        
        # Process event...
        await asyncio.sleep(0.01)  # Reduced from 0.05s to 0.01s
        
        await self.logger.info(
            f"[15] Event processed: {event_type}",
            layer="event_handler",
            context={"correlation_id": correlation_id}
        )
    
    async def close(self):
        """Cleanup resources."""
        # close_async() ensures all writes complete
        await self.logger.close_async()


# ============================================================================
# PATTERN 4: Graceful Shutdown Handler
# ============================================================================

class GracefulShutdownMixin:
    """Mixin for graceful shutdown in microservices."""
    
    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._shutdown_handlers = []
    
    def register_shutdown_handler(self, handler):
        """Register a cleanup handler."""
        self._shutdown_handlers.append(handler)
    
    async def shutdown(self):
        """Execute all shutdown handlers."""
        await self.logger.info("[15] Executing graceful shutdown")
        
        for handler in self._shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                await self.logger.error(f"[15] Shutdown handler error: {e}")


# ============================================================================
# DEMONSTRATION
# ============================================================================

async def main():
    """Demonstrate all patterns."""
    print("=" * 60)
    print("EDA & Microservices Patterns Demonstration")
    print("=" * 60)
    
    # Pattern 1: Auto-cleanup with context manager
    print("\n[Pattern 1] Auto-cleanup with context manager...")
    await microservice_with_auto_cleanup()
    # No manual sleep needed - context manager handles cleanup automatically
    
    # Pattern 2: Shared logger instance
    print("\n[Pattern 2] Shared logger instance...")
    service = MicroserviceApp()
    # Run briefly for demo
    task = asyncio.create_task(service.start())
    await asyncio.sleep(0.05)  # Reduced from 0.3s to 0.05s
    await service.shutdown()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    # No manual sleep needed - close_async() handles cleanup automatically
    
    # Pattern 3: Event-driven
    print("\n[Pattern 3] Event-driven architecture...")
    eda_service = EventDrivenService()
    await eda_service.process_event("user.created", {
        "correlation_id": "corr-12345",
        "user_id": "user-789"
    })
    await eda_service.close()
    # No manual sleep needed - close() handles cleanup automatically
    
    print("\nExample 15 completed: EDA & Microservices Patterns")
    print("\nKey Takeaways:")
    print(" - Use async context manager for automatic cleanup")
    print(" - Use shared logger instance per microservice")
    print(" - Always close async loggers in shutdown handlers")
    print(" - Use correlation IDs for event tracing")


if __name__ == "__main__":
    asyncio.run(main())
    # No manual sleep needed - close_async() ensures all writes complete
