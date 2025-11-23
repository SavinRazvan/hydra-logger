# Hydra-Logger: EDA & Microservices Guide

## Overview

Hydra-Logger is **fully compatible** with Event-Driven Architecture (EDA) and microservices. It provides multiple patterns for resource management, automatic cleanup, and long-running services.

## ✅ Key Features for EDA & Microservices

### 1. **Automatic Cleanup Mechanisms**

Your loggers have **multiple layers of automatic cleanup**:

#### a) Context Manager Support (Recommended)
```python
# ✅ AUTOMATIC CLEANUP: Context manager handles everything
async with create_async_logger(config) as logger:
    await logger.info("Message")
    # Logger automatically closed - no manual cleanup needed
```

#### b) `atexit` Handlers (Emergency Fallback)
```python
# ✅ AUTOMATIC: Handlers register with atexit for cleanup on exit
# If you forget to close, Python will clean up automatically
logger = create_async_logger(config)
await logger.info("Message")
# Even if you forget close_async(), atexit will clean up handlers
```

#### c) Destructor Fallbacks
```python
# ✅ AUTOMATIC: __del__ methods provide backup cleanup
# Handlers have destructors that clean up if atexit fails
```

### 2. **No Hardcoded Limitations**

- ✅ **No hardcoded timeouts** that break long-running services
- ✅ **No hardcoded resource limits** that prevent scaling
- ✅ **Dynamic concurrency** based on system memory
- ✅ **Overflow queue** handles burst traffic automatically
- ✅ **Thread-safe** for concurrent access from multiple event handlers

### 3. **Event Loop Compatibility**

- ✅ **Works with any async framework** (FastAPI, aiohttp, asyncio, etc.)
- ✅ **Event loop aware** - detects running loops automatically
- ✅ **Graceful handling** when event loop closes
- ✅ **Worker tasks** automatically cancelled on shutdown

## Resource Management Patterns

### Pattern 1: Short-Lived Operations (Automatic Cleanup)

**Best for:** Request handlers, API endpoints, event handlers

```python
async def handle_request(request):
    """Request handler - logger cleaned up automatically."""
    async with create_async_logger(config) as logger:
        await logger.info("Processing request")
        # Process request...
        # ✅ No manual cleanup needed
```

### Pattern 2: Long-Running Services (Shared Instance)

**Best for:** Microservices, background workers, event processors

```python
class Microservice:
    def __init__(self):
        # ✅ Create logger once, reuse across all operations
        self.logger = create_async_logger(config, name="MyService")
    
    async def start(self):
        await self.logger.info("Service starting")
        # Run service...
    
    async def shutdown(self):
        # ✅ Manual cleanup for long-running services
        await self.logger.close_async()
```

### Pattern 3: Graceful Shutdown

**Best for:** Production microservices

```python
class Microservice:
    def __init__(self):
        self.logger = create_async_logger(config)
        self._shutdown = asyncio.Event()
    
    async def run(self):
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, self._handle_shutdown)
        loop.add_signal_handler(signal.SIGINT, self._handle_shutdown)
        
        # Main loop
        while not self._shutdown.is_set():
            await self.process_events()
            await asyncio.sleep(0.1)
        
        # ✅ Cleanup before exit
        await self.logger.close_async()
    
    def _handle_shutdown(self):
        self._shutdown.set()
```

### Pattern 4: Event-Driven Architecture

**Best for:** EDA, event sourcing, message queues

```python
class EventProcessor:
    def __init__(self):
        self.logger = create_async_logger(config)
    
    async def process_event(self, event):
        correlation_id = event.get("correlation_id")
        await self.logger.info(
            "Processing event",
            layer="events",
            context={"correlation_id": correlation_id},
            extra=event
        )
        # Process event...
    
    # ✅ Logger persists for multiple events
    # ✅ Close only when service shuts down
```

## Do You Need Manual Cleanup?

### ✅ YES - Manual Cleanup Recommended For:

1. **Long-running services** (microservices, background workers)
   ```python
   # At service shutdown
   await logger.close_async()
   ```

2. **Shared logger instances** (singleton loggers)
   ```python
   # When service terminates
   await shared_logger.close_async()
   ```

3. **Graceful shutdown scenarios**
   ```python
   # In shutdown handler
   await logger.close_async()
   ```

### ✅ NO - Automatic Cleanup Works For:

1. **Request handlers** (FastAPI, aiohttp endpoints)
   ```python
   async def endpoint():
       async with logger:  # Auto-cleanup
           await logger.info("Handling request")
   ```

2. **Short-lived operations**
   ```python
   async def process():
       async with logger:  # Auto-cleanup
           await logger.info("Processing")
   ```

3. **Event handlers** (if using context manager)
   ```python
   async def on_event(event):
       async with logger:  # Auto-cleanup per event
           await logger.info(f"Event: {event}")
   ```

## What Happens If You Don't Close?

### ✅ Automatic Safety Mechanisms:

1. **`atexit` handlers** - Cleanup on process exit
2. **Destructors (`__del__`)** - Cleanup when object is garbage collected
3. **Event loop cleanup** - Tasks cancelled when loop closes

### ⚠️ Best Practice:

**Always close explicitly** for production code:
- ✅ Prevents resource leaks
- ✅ Ensures buffers are flushed
- ✅ Cancels background tasks cleanly
- ✅ Provides predictable shutdown behavior

## Microservices Best Practices

### 1. One Logger Per Service
```python
# ✅ GOOD: Single logger instance per microservice
class PaymentService:
    logger = create_async_logger(config, name="PaymentService")
    
    @classmethod
    async def process_payment(cls, data):
        await cls.logger.info("Processing payment", extra=data)
```

### 2. Correlation IDs
```python
# ✅ GOOD: Track requests across services
await logger.info(
    "Processing order",
    context={"correlation_id": request_id, "service": "payment"}
)
```

### 3. Layer-Based Logging
```python
# ✅ GOOD: Different layers for different concerns
config = LoggingConfig(layers={
    "api": LogLayer(...),      # API requests
    "events": LogLayer(...),   # Event processing
    "errors": LogLayer(...),   # Error handling
})
```

### 4. Health Checks
```python
# ✅ GOOD: Monitor logger health
health = logger.get_health_status()
if health["status"] != "healthy":
    # Alert monitoring system
    pass
```

## EDA Patterns

### Event Correlation
```python
# ✅ Track events through the system
async def handle_event(event):
    correlation_id = event.get("correlation_id", generate_id())
    
    await logger.info(
        f"Event: {event['type']}",
        layer="events",
        context={"correlation_id": correlation_id},
        extra=event
    )
```

### Event Batching
```python
# ✅ Batch multiple events for performance
events = [event1, event2, event3]
await logger.log_batch([
    ("INFO", f"Event: {e['type']}", {"layer": "events", "extra": e})
    for e in events
])
```

### Async Processing
```python
# ✅ Non-blocking event processing
async def process_event_stream():
    async for event in event_stream:
        # Logger won't block event processing
        await logger.info("Processing event", layer="events")
        await process(event)
```

## Common Questions

### Q: Do I need to close async loggers manually?

**A:** It depends:
- ✅ **Short-lived operations**: Use context manager (automatic)
- ✅ **Long-running services**: Close manually in shutdown handler
- ✅ **Emergency fallback**: `atexit` handlers provide cleanup

### Q: What if I forget to close?

**A:** Multiple safety nets:
1. `atexit` handlers clean up on process exit
2. Destructors clean up on garbage collection
3. Event loop cleanup cancels tasks

### Q: Can I use the same logger across multiple async functions?

**A:** ✅ Yes! Loggers are thread-safe and async-safe:
```python
logger = create_async_logger(config)  # Create once

async def handler1():
    await logger.info("From handler 1")

async def handler2():
    await logger.info("From handler 2")

# Both can use the same logger concurrently
```

### Q: Will loggers work in FastAPI/aiohttp/etc?

**A:** ✅ Yes! Works with any async framework:
```python
from fastapi import FastAPI
app = FastAPI()
logger = create_async_logger(config)

@app.get("/")
async def root():
    await logger.info("Request received")
    return {"message": "Hello"}
```

### Q: How do I handle graceful shutdown?

**A:** Close logger in shutdown handler:
```python
async def shutdown():
    await logger.close_async()  # Cleanup resources
```

## Summary

✅ **Hydra-Logger is production-ready for EDA and microservices**
- Automatic cleanup mechanisms
- No hardcoded limitations
- Thread-safe and async-safe
- Multiple resource management patterns
- Works with any async framework

✅ **Best Practices:**
- Use context managers for short-lived operations
- Use shared instances with manual cleanup for long-running services
- Always close in graceful shutdown handlers
- Use correlation IDs for event tracing
- Monitor logger health in production

