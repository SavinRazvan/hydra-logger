# AsyncHydraLogger Comprehensive Refactor Plan

## Executive Summary

This document outlines a comprehensive refactor plan for AsyncHydraLogger to achieve feature parity with SyncHydraLogger while maintaining good async performance, data loss protection, and enterprise-grade reliability.

**Current State**: AsyncHydraLogger has fundamental issues with file writing, lacks sync fallbacks, and doesn't match the sync logger's feature completeness.

**Target State**: AsyncHydraLogger that matches SyncHydraLogger's capabilities with async-specific optimizations, data loss protection, and reliable delivery.

---

## CRITICAL PRODUCTION ISSUES (URGENT)

### 0.1 Unawaited Coroutines and Memory Leaks

**Problem**: Runtime warnings indicate unawaited coroutines in production code, leading to memory leaks and potential data loss.

**Root Cause Analysis**:
- `coroutine 'Queue.get' was never awaited` - Queue operations not properly awaited
- `coroutine 'AsyncBatchFileHandler.aclose' was never awaited` - Async cleanup not properly handled
- These warnings indicate coroutines are being created but never awaited, causing memory leaks
- In production, this could lead to resource exhaustion and application crashes

**Production Impact**:
- **Memory Leaks**: Unawaited coroutines accumulate in memory
- **Resource Exhaustion**: Event loop becomes overwhelmed with pending tasks
- **Data Loss**: Messages may be lost when coroutines are garbage collected
- **Application Crashes**: Eventually leads to out-of-memory errors

**Solution Options**:

#### Option A: Comprehensive Coroutine Management (CRITICAL)
- Implement proper coroutine lifecycle management
- Add coroutine tracking and cleanup mechanisms
- Ensure all coroutines are properly awaited or cancelled
- Add memory leak detection and prevention

#### Option B: Sync Fallback for All Async Operations
- When async operations fail, immediately fallback to sync
- Guarantee no data loss even if async system fails
- Simpler but may impact performance

#### Option C: Hybrid Approach with Monitoring
- Implement proper coroutine management
- Add comprehensive monitoring and alerting
- Fallback to sync when async system is unstable

**Implementation Details**:
```python
class CoroutineManager:
    def __init__(self, shutdown_timeout=2.0):
        self._tasks = set()
        self._shutdown_timeout = shutdown_timeout
        self._shutdown_event = asyncio.Event()
        self._cleanup_lock = asyncio.Lock()
    
    def track(self, coro):
        """Track a coroutine with automatic cleanup."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
    
    async def shutdown(self):
        """Professional shutdown with proper timeout handling."""
        async with self._cleanup_lock:
            if not self._tasks:
                return
            
            # Signal shutdown to all tasks
            self._shutdown_event.set()
            
            # Cancel all tasks immediately
            cancel_tasks = [task.cancel() for task in list(self._tasks)]
            
            # Wait for all tasks to complete with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=self._shutdown_timeout
                )
            except asyncio.TimeoutError:
                # Log warning but continue - don't hang the application
                remaining = len([t for t in self._tasks if not t.done()])
                if remaining > 0:
                    print(f"WARNING: {remaining} tasks did not complete within {self._shutdown_timeout}s")
            
            self._tasks.clear()

class SafeAsyncBatchFileHandler(AsyncBatchFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._coroutine_manager = CoroutineManager()
    
    async def emit_async(self, record):
        try:
            # Track the coroutine to ensure it's awaited
            task = await self._coroutine_manager.track_coroutine(
                super().emit_async(record)
            )
            return task
        except Exception as e:
            # Immediate sync fallback if async fails
            self._write_record_sync(record)
            raise

### 0.2 Async Context and Event Loop Issues

**Problem**: Async operations fail when no event loop is running or when event loop context is lost.

**Root Cause Analysis**:
- `RuntimeError: no event loop` when async operations are called outside async context
- Event loop context not properly managed in production environments
- Async operations called from sync code paths

**Production Impact**:
- **Silent Failures**: Async operations fail silently when no event loop
- **Data Loss**: Messages lost when async context is unavailable
- **Inconsistent Behavior**: Same code works in tests but fails in production

**Solution Options**:

#### Option A: Robust Event Loop Detection (CRITICAL)
- Detect event loop availability before async operations
- Fallback to sync operations when no event loop
- Add comprehensive event loop state management

#### Option B: Always-Sync Fallback
- All async operations have immediate sync fallback
- Guarantee delivery regardless of async context
- May impact performance but ensures reliability

#### Option C: Hybrid with Context Detection
- Detect async context availability
- Use async when available, sync when not
- Best balance of performance and reliability

**Implementation Details**:
```python
class AsyncContextManager:
    @staticmethod
    def has_event_loop():
        """Check if we're in an async context with event loop."""
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    
    @staticmethod
    async def safe_async_operation(operation, fallback_operation):
        """Safely execute async operation with sync fallback."""
        if AsyncContextManager.has_event_loop():
            try:
                return await operation()
            except Exception as e:
                # Fallback to sync operation
                return fallback_operation()
        else:
            # No event loop, use sync fallback
            return fallback_operation()

class RobustAsyncHandler(AsyncBatchFileHandler):
    async def emit_async(self, record):
        async def async_emit():
            return await super().emit_async(record)
        
        def sync_emit():
            return self._write_record_sync(record)
        
        return await AsyncContextManager.safe_async_operation(
            async_emit, sync_emit
        )
```

### 0.3 Queue Management and Backpressure Issues

**Problem**: Queue operations not properly managed, leading to memory buildup and potential data loss.

**Root Cause Analysis**:
- Queue.get() coroutines not properly awaited
- No backpressure handling when queues are full
- Memory leaks from unprocessed queue items

**Production Impact**:
- **Memory Exhaustion**: Queues grow unbounded in high-load scenarios
- **Data Loss**: Messages dropped when queues overflow
- **Performance Degradation**: System becomes unresponsive under load

**Solution Options**:

#### Option A: Bounded Queues with Backpressure (CRITICAL)
- Implement bounded queues with configurable limits
- Add backpressure mechanisms to prevent memory buildup
- Implement queue monitoring and alerting

#### Option B: Drop-Oldest Strategy
- When queue is full, drop oldest messages
- Maintain system responsiveness
- May lose important historical data

#### Option C: Adaptive Queue Management
- Dynamically adjust queue size based on system load
- Implement intelligent message prioritization
- Complex but provides best balance

**Implementation Details**:
```python
class BoundedAsyncQueue:
    def __init__(self, maxsize=1000):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._dropped_count = 0
        self._monitor_task = None
    
    async def put(self, item):
        """Put item with backpressure handling."""
        try:
            await self._queue.put(item)
        except asyncio.QueueFull:
            # Drop oldest item and add new one
            try:
                self._queue.get_nowait()  # Remove oldest
                await self._queue.put(item)
                self._dropped_count += 1
            except asyncio.QueueEmpty:
                # Queue is empty, this shouldn't happen
                raise
    
    async def get(self):
        """Get item with proper error handling."""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None  # Timeout, return None to indicate no data

class ProductionReadyAsyncHandler(AsyncBatchFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = BoundedAsyncQueue(maxsize=kwargs.get('max_queue_size', 1000))
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start monitoring queue health."""
        async def monitor_queue():
            while True:
                await asyncio.sleep(5)  # Check every 5 seconds
                queue_size = self._queue.qsize()
                if queue_size > self._queue.maxsize * 0.8:
                    # Alert: queue is getting full
                    print(f"WARNING: Queue is {queue_size}/{self._queue.maxsize} full")
        
        self._monitor_task = asyncio.create_task(monitor_queue())
```

### 0.4 Graceful Shutdown and Resource Cleanup

**Problem**: Async resources not properly cleaned up during shutdown, leading to data loss and resource leaks.

**Root Cause Analysis**:
- `aclose()` coroutines not properly awaited during shutdown
- Pending messages lost when application shuts down
- Event loop not properly closed

**Production Impact**:
- **Data Loss**: Pending messages lost during shutdown
- **Resource Leaks**: File handles and connections not properly closed
- **Inconsistent State**: Application state inconsistent after restart

**Solution Options**:

#### Option A: Comprehensive Shutdown Protocol (CRITICAL)
- Implement proper shutdown sequence for all async resources
- Ensure all pending messages are processed before shutdown
- Add timeout-based shutdown with fallback

#### Option B: Immediate Sync Fallback on Shutdown
- When shutdown is initiated, immediately switch to sync processing
- Guarantee all messages are written before shutdown
- Simpler but may impact shutdown time

#### Option C: Configurable Shutdown Behavior
- User-configurable shutdown behavior
- Balance between shutdown speed and data preservation
- More complex but provides flexibility

**Implementation Details**:
```python
class GracefulShutdownManager:
    def __init__(self, timeout=30.0):
        self._timeout = timeout
        self._shutdown_event = asyncio.Event()
        self._pending_messages = 0
    
    async def shutdown(self):
        """Graceful shutdown with pending message handling."""
        self._shutdown_event.set()
        
        # Wait for pending messages with timeout
        start_time = time.time()
        while self._pending_messages > 0 and (time.time() - start_time) < self._timeout:
            await asyncio.sleep(0.1)
        
        # Force sync processing for remaining messages
        if self._pending_messages > 0:
            await self._force_sync_processing()
        
        # Cleanup all async resources
        await self._cleanup_async_resources()
    
    async def _force_sync_processing(self):
        """Force sync processing of remaining messages."""
        # Implementation to process remaining messages synchronously
        pass
    
    async def _cleanup_async_resources(self):
        """Cleanup all async resources."""
        # Cancel all pending tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

class ProductionAsyncHandler(AsyncBatchFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown_manager = GracefulShutdownManager()
    
    async def aclose(self):
        """Proper async cleanup with pending message handling."""
        try:
            # Process any remaining messages
            await self._process_remaining_messages()
            
            # Cleanup resources
            await super().aclose()
        except Exception as e:
            # Ensure cleanup happens even if errors occur
            await self._emergency_cleanup()
            raise

---

## IMMEDIATE FIXES (URGENT - NEXT 24-48 HOURS)

### I.1 Fix Unawaited Coroutine Warnings

**Problem**: Current test warnings indicate production code has unawaited coroutines.

**Immediate Actions**:

#### Fix 1: Queue.get() Warning
```python
# In AsyncBatchFileHandler._writer method
async def _writer(self):
    while self._running:
        try:
            # Always await queue.get() with timeout
            msg = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            # Process message...
        except asyncio.TimeoutError:
            # Timeout is expected, continue
            continue
        except Exception as e:
            # Log error and continue
            print(f"Error in writer: {e}")
            continue
```

#### Fix 2: aclose() Warning
```python
# In AsyncBatchFileHandler.__del__ method
def __del__(self):
    try:
        # Don't call async methods in __del__
        if hasattr(self, '_sync_file_handle') and self._sync_file_handle:
            self._sync_file_handle.close()
    except Exception:
        # Ignore errors in destructor
        pass
```

#### Fix 3: Event Loop Detection
```python
# In AsyncBatchFileHandler.emit method
def emit(self, record):
    try:
        if self.test_mode:
            self._write_record_sync(record)
        else:
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in async context, use async
                asyncio.create_task(self.emit_async(record))
            except RuntimeError:
                # No event loop, use sync fallback
                self._write_record_sync(record)
    except Exception as e:
        # Always fallback to sync on any error
        self._write_record_sync(record)
```

### I.2 Add Comprehensive Error Handling

**Problem**: Async operations fail silently in production.

**Immediate Actions**:

#### Fix 1: Sync Fallback for All Async Operations
```python
class SafeAsyncBatchFileHandler(AsyncBatchFileHandler):
    async def emit_async(self, record):
        try:
            return await super().emit_async(record)
        except Exception as e:
            # Immediate sync fallback
            self._write_record_sync(record)
            # Log the error for monitoring
            print(f"Async emit failed, used sync fallback: {e}")
            raise  # Re-raise for monitoring
```

#### Fix 2: Bounded Queues
```python
class BoundedAsyncQueue:
    def __init__(self, maxsize=1000):
        self._queue = asyncio.Queue(maxsize=maxsize)
    
    async def put(self, item):
        try:
            await self._queue.put(item)
        except asyncio.QueueFull:
            # Drop oldest item to make room
            try:
                self._queue.get_nowait()
                await self._queue.put(item)
            except asyncio.QueueEmpty:
                # This shouldn't happen, but handle it
                pass
```

### I.3 Add Production Monitoring

**Problem**: No visibility into async system health.

**Immediate Actions**:

#### Fix 1: Health Check Endpoints
```python
class AsyncLoggerHealthCheck:
    def __init__(self, logger):
        self.logger = logger
        self._queue_sizes = {}
        self._error_counts = {}
    
    def get_health_status(self):
        return {
            'queue_sizes': self._queue_sizes,
            'error_counts': self._error_counts,
            'has_event_loop': self._has_event_loop(),
            'pending_tasks': len(asyncio.all_tasks())
        }
    
    def _has_event_loop(self):
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
```

---

## DETAILED SAFE ASYNC ARCHITECTURE PLAN

### **Phase 0: Safe Coroutine Management Foundation (CRITICAL)**

#### **0.1 CoroutineManager Implementation**

**Purpose**: Track all background tasks to prevent unawaited coroutines and ensure proper cleanup.

**Mechanisms to Prevent Deadlocks/Hangs**:

1. **Professional Timeout-Based Cleanup**:
   ```python
   class CoroutineManager:
       def __init__(self, shutdown_timeout=2.0):
           self._tasks = set()
           self._shutdown_timeout = shutdown_timeout
           self._shutdown_event = asyncio.Event()
           self._cleanup_lock = asyncio.Lock()
       
       def track(self, coro):
           """Track a coroutine with automatic cleanup."""
           task = asyncio.create_task(coro)
           self._tasks.add(task)
           task.add_done_callback(self._tasks.discard)
           return task
       
       async def shutdown(self):
           """Professional shutdown with proper timeout handling."""
           async with self._cleanup_lock:
               if not self._tasks:
                   return
               
               # Signal shutdown to all tasks
               self._shutdown_event.set()
               
               # Cancel all tasks immediately
               cancel_tasks = [task.cancel() for task in list(self._tasks)]
               
               # Wait for all tasks to complete with timeout
               try:
                   await asyncio.wait_for(
                       asyncio.gather(*self._tasks, return_exceptions=True),
                       timeout=self._shutdown_timeout
                   )
               except asyncio.TimeoutError:
                   # Log warning but continue - don't hang the application
                   remaining = len([t for t in self._tasks if not t.done()])
                   if remaining > 0:
                       print(f"WARNING: {remaining} tasks did not complete within {self._shutdown_timeout}s")
               
               self._tasks.clear()
   ```

2. **Event Loop Safety with Professional Error Handling**:
   ```python
   class EventLoopManager:
       @staticmethod
       def has_running_loop():
           """Professional check for running event loop."""
           try:
               asyncio.get_running_loop()
               return True
           except RuntimeError:
               return False
       
       @staticmethod
       def safe_create_task(coro):
           """Safely create task only if event loop is running."""
           if EventLoopManager.has_running_loop():
               return asyncio.create_task(coro)
           else:
               raise RuntimeError("No event loop running")
       
       @staticmethod
       async def safe_async_operation(operation, fallback_operation=None):
           """Execute async operation with professional fallback."""
           if EventLoopManager.has_running_loop():
               try:
                   return await operation()
               except Exception as e:
                   if fallback_operation:
                       return fallback_operation()
                   raise
           else:
               if fallback_operation:
                   return fallback_operation()
               raise RuntimeError("No event loop and no fallback provided")
   ```

3. **Professional Graceful Degradation**:
   ```python
   class SafeAsyncHandler:
       def __init__(self):
           self._coroutine_manager = CoroutineManager()
           self._sync_fallback = True
           self._error_tracker = AsyncErrorTracker()
       
       async def emit_async(self, record):
           """Professional async emit with proper error handling."""
           try:
               return await EventLoopManager.safe_async_operation(
                   lambda: self._coroutine_manager.track(self._emit_async_internal(record)),
                   lambda: self._write_record_sync(record)
               )
           except Exception as e:
               self._error_tracker.record_error("emit_async", e)
               return self._write_record_sync(record)
   ```

#### **0.2 Bounded Queue with Professional Backpressure**

**Purpose**: Prevent memory exhaustion and provide predictable behavior.

**Mechanisms to Prevent Memory Issues**:

1. **Professional Queue Implementation**:
   ```python
   class BoundedAsyncQueue:
       def __init__(self, maxsize=1000, policy='drop_oldest', put_timeout=0.1, get_timeout=1.0):
           self._queue = asyncio.Queue(maxsize=maxsize)
           self._policy = policy
           self._dropped_count = 0
           self._put_timeout = put_timeout
           self._get_timeout = get_timeout
           self._monitor_task = None
           self._stats = {
               'puts': 0,
               'gets': 0,
               'drops': 0,
               'timeouts': 0
           }
       
       async def put(self, item):
           """Professional put with configurable backpressure policy."""
           self._stats['puts'] += 1
           
           try:
               await asyncio.wait_for(self._queue.put(item), timeout=self._put_timeout)
           except asyncio.TimeoutError:
               self._stats['timeouts'] += 1
               if self._policy == 'drop_oldest':
                   # Remove oldest, add new
                   try:
                       self._queue.get_nowait()
                       await asyncio.wait_for(self._queue.put(item), timeout=self._put_timeout)
                       self._dropped_count += 1
                       self._stats['drops'] += 1
                   except (asyncio.QueueEmpty, asyncio.TimeoutError):
                       raise asyncio.QueueFull("Queue is full and drop_oldest failed")
               elif self._policy == 'error':
                   raise asyncio.QueueFull("Queue is full")
               else:  # block policy
                   await self._queue.put(item)
       
       async def get(self):
           """Professional get with timeout."""
           self._stats['gets'] += 1
           try:
               return await asyncio.wait_for(self._queue.get(), timeout=self._get_timeout)
           except asyncio.TimeoutError:
               self._stats['timeouts'] += 1
               return None  # Indicate no data available
       
       def get_stats(self):
           """Get comprehensive queue statistics."""
           return {
               'size': self._queue.qsize(),
               'maxsize': self._queue.maxsize(),
               'dropped_count': self._dropped_count,
               'stats': self._stats.copy()
           }
   ```

2. **Professional Memory Monitoring**:
   ```python
   class MemoryMonitor:
       def __init__(self, max_percent=70.0, check_interval=5.0):
           self._max_percent = max_percent
           self._check_interval = check_interval
           self._warning_logged = False
           self._last_check = 0
           self._stats = {
               'checks': 0,
               'warnings': 0,
               'last_memory_percent': 0
           }
       
       def check_memory(self):
           """Professional memory check with caching."""
           current_time = time.time()
           
           # Cache results to avoid excessive checks
           if current_time - self._last_check < self._check_interval:
               return self._last_result
           
           self._stats['checks'] += 1
           self._last_check = current_time
           
           try:
               import psutil
               memory = psutil.virtual_memory()
               self._stats['last_memory_percent'] = memory.percent
               
               if memory.percent > self._max_percent:
                   if not self._warning_logged:
                       print(f"WARNING: Memory usage {memory.percent:.1f}% exceeds {self._max_percent}%")
                       self._warning_logged = True
                       self._stats['warnings'] += 1
                   self._last_result = False
               else:
                   self._warning_logged = False
                   self._last_result = True
               
               return self._last_result
           except Exception:
               # If we can't check memory, assume it's OK
               self._last_result = True
               return True
   ```

#### **0.3 Professional Safe Shutdown Protocol**

**Purpose**: Ensure all data is written and resources are cleaned up.

**Mechanisms to Prevent Data Loss and Hangs**:

1. **Professional Multi-Phase Shutdown**:
   ```python
   class SafeShutdownManager:
       def __init__(self, flush_timeout=5.0, cleanup_timeout=2.0):
           self._flush_timeout = flush_timeout
           self._cleanup_timeout = cleanup_timeout
           self._shutdown_event = asyncio.Event()
           self._phase = 'running'  # running -> flushing -> cleaning -> done
           self._cleanup_lock = asyncio.Lock()
       
       async def shutdown(self):
           """Professional multi-phase shutdown with proper timeouts."""
           async with self._cleanup_lock:
               if self._phase != 'running':
                   return  # Already shutting down
               
               self._phase = 'flushing'
               self._shutdown_event.set()
               
               # Phase 1: Flush remaining messages with timeout
               try:
                   await asyncio.wait_for(self._flush_remaining_messages(), 
                                        timeout=self._flush_timeout)
               except asyncio.TimeoutError:
                   print(f"WARNING: Flush did not complete within {self._flush_timeout}s")
               
               # Phase 2: Cleanup resources with timeout
               self._phase = 'cleaning'
               try:
                   await asyncio.wait_for(self._cleanup_resources(), 
                                        timeout=self._cleanup_timeout)
               except asyncio.TimeoutError:
                   print(f"WARNING: Cleanup did not complete within {self._cleanup_timeout}s")
               
               self._phase = 'done'
       
       async def _flush_remaining_messages(self):
           """Flush all pending messages with proper error handling."""
           # Implementation depends on specific handler
           # Use asyncio.gather with return_exceptions=True
           pass
       
       async def _cleanup_resources(self):
           """Professional cleanup of all async resources."""
           # Cancel all tracked tasks
           # Close file handles
           # Clear queues
           # Use proper asyncio primitives, not sleep()
           pass
   ```

2. **Professional Sync Fallback on Shutdown**:
   ```python
   class SafeAsyncBatchFileHandler:
       async def aclose(self):
           """Professional async close with proper sync fallback."""
           try:
               # Try async shutdown first with timeout
               await asyncio.wait_for(self._shutdown_manager.shutdown(), timeout=10.0)
           except (asyncio.TimeoutError, Exception) as e:
               print(f"Async shutdown failed: {e}")
               # Force sync shutdown immediately
               self._force_sync_shutdown()
       
       def _force_sync_shutdown(self):
           """Professional sync shutdown when async fails."""
           # Close file handles synchronously
           # Flush any remaining messages synchronously
           # Clear queues synchronously
           # No sleep() calls - use proper sync operations
           pass
   ```

#### **0.4 Professional Error Handling and Monitoring**

**Purpose**: Provide visibility into system health and prevent silent failures.

**Mechanisms to Prevent Silent Failures**:

1. **Professional Error Tracking**:
   ```python
   class AsyncErrorTracker:
       def __init__(self):
           self._error_counts = {}
           self._last_error_time = None
           self._error_callbacks = []
           self._error_lock = asyncio.Lock()
       
       async def record_error(self, error_type, error):
           """Professional error recording with proper async handling."""
           async with self._error_lock:
               self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
               self._last_error_time = time.time()
               
               # Call error callbacks with proper exception handling
               for callback in self._error_callbacks:
                   try:
                       if asyncio.iscoroutinefunction(callback):
                           await callback(error_type, error)
                       else:
                           callback(error_type, error)
                   except Exception:
                       # Don't let callback errors break error tracking
                       pass
       
       def get_error_stats(self):
           """Get comprehensive error statistics."""
           return {
               'error_counts': self._error_counts.copy(),
               'last_error_time': self._last_error_time,
               'total_errors': sum(self._error_counts.values())
           }
   ```

2. **Professional Health Monitoring**:
   ```python
   class AsyncHealthMonitor:
       def __init__(self, handler):
           self._handler = handler
           self._start_time = time.time()
           self._last_check = 0
           self._check_interval = 1.0  # Check every second
       
       def get_health_status(self):
           """Get professional health status with caching."""
           current_time = time.time()
           
           # Cache results to avoid excessive checks
           if current_time - self._last_check < self._check_interval:
               return self._cached_status
           
           self._last_check = current_time
           
           try:
               self._cached_status = {
                   'uptime': current_time - self._start_time,
                   'queue_size': self._handler._queue.qsize() if self._handler._queue else 0,
                   'queue_maxsize': self._handler._queue.maxsize if self._handler._queue else 0,
                   'dropped_messages': getattr(self._handler, '_dropped_messages', 0),
                   'has_event_loop': EventLoopManager.has_running_loop(),
                   'pending_tasks': len(asyncio.all_tasks()) if EventLoopManager.has_running_loop() else 0,
                   'memory_ok': self._handler._memory_monitor.check_memory() if hasattr(self._handler, '_memory_monitor') else True,
                   'shutdown_phase': getattr(self._handler._shutdown_manager, '_phase', 'unknown'),
                   'last_check': current_time
               }
               return self._cached_status
           except Exception as e:
               # Return basic status if monitoring fails
               return {
                   'uptime': current_time - self._start_time,
                   'error': str(e),
                   'last_check': current_time
               }
   ```

### **Phase 1: Implementation Steps**

#### **Step 1.1: Implement CoroutineManager**
- Create `CoroutineManager` with timeout-based cleanup
- Add event loop safety checks
- Implement graceful degradation

#### **Step 1.2: Implement Bounded Queue**
- Create `BoundedAsyncQueue` with configurable policies
- Add memory monitoring
- Implement backpressure handling

#### **Step 1.3: Implement Safe Shutdown**
- Create `SafeShutdownManager` with multi-phase shutdown
- Add sync fallback for shutdown
- Implement timeout-based cleanup

#### **Step 1.4: Add Error Handling and Monitoring**
- Create `AsyncErrorTracker` for error monitoring
- Create `AsyncHealthMonitor` for health checks
- Add comprehensive logging

#### **Step 1.5: Integrate into AsyncBatchFileHandler**
- Replace current queue with `BoundedAsyncQueue`
- Add `CoroutineManager` for task tracking
- Add `SafeShutdownManager` for shutdown
- Add error tracking and health monitoring

### **Phase 2: Testing and Validation**

#### **Step 2.1: Deadlock Prevention Tests**
- Test shutdown with hanging tasks
- Test queue overflow scenarios
- Test event loop unavailability

#### **Step 2.2: Memory Safety Tests**
- Test high memory usage scenarios
- Test queue backpressure
- Test memory leak detection

#### **Step 2.3: Data Integrity Tests**
- Test shutdown with pending messages
- Test sync fallback scenarios
- Test error recovery

#### **Step 2.4: Performance Tests**
- Test high-throughput scenarios
- Test concurrent access
- Test resource cleanup

### **Phase 3: Production Deployment**

#### **Step 3.1: Monitoring Integration**
- Add health check endpoints
- Add metrics collection
- Add alerting for critical issues

#### **Step 3.2: Documentation**
- Document async usage patterns
- Document shutdown requirements
- Document monitoring and alerting

#### **Step 3.3: Migration Guide**
- Guide for migrating from current implementation
- Best practices for async logging
- Troubleshooting guide

---

## Implementation Strategy

### 4.1 Development Approach

**Recommended Approach**: Incremental implementation with continuous testing.

**Updated Phase Order**:
0. **CRITICAL PRODUCTION ISSUES** (IMMEDIATE - 24-48 hours)
   - Fix unawaited coroutine warnings
   - Implement sync fallback for all async operations
   - Add bounded queues with backpressure
   - Implement graceful shutdown protocol

1. **IMMEDIATE FIXES** (24-48 hours)
   - Fix Queue.get() and aclose() warnings
   - Add comprehensive error handling
   - Add production monitoring

2. **Phase 1** (Core Reliability) - 1-2 weeks
   - Fix async file writing issues
   - Implement sync fallback system
   - Add data loss protection for critical logs

3. **Phase 2** (Feature Parity) - 2-3 weeks
   - Multiple destinations per layer
   - Multiple format support
   - Magic config system integration
   - Data protection & security
   - Plugin system integration

4. **Phase 3** (Async Enhancements) - 1-2 weeks
   - Zero-copy batch processing
   - Async context propagation
   - Concurrent multi-destination writing
   - Async performance monitoring
   - Graceful shutdown with pending message handling

5. **Phase 4** (Testing) - 1 week
   - Deterministic testing
   - Performance benchmarking
   - Error recovery testing

### 4.2 Risk Mitigation

**CRITICAL RISKS** (Address Immediately):
- **Memory Leaks**: Unawaited coroutines causing resource exhaustion
- **Data Loss**: Async operations failing silently in production
- **Application Crashes**: Event loop becoming overwhelmed
- **Resource Leaks**: File handles and connections not properly closed

**High-Risk Areas**:
- Async file writing fixes (Phase 1.1)
- Sync fallback implementation (Phase 1.2)
- Multiple destination support (Phase 2.1)

**Mitigation Strategies**:
- **Immediate**: Implement sync fallback for all async operations
- **Short-term**: Add comprehensive monitoring and alerting
- **Long-term**: Extensive testing at each phase with incremental rollout

### 4.3 Success Criteria

**CRITICAL SUCCESS CRITERIA** (24-48 hours):
- No unawaited coroutine warnings in tests
- All async operations have sync fallback
- Bounded queues prevent memory exhaustion
- Graceful shutdown preserves all pending messages

**Phase 1 Success**:
- All async file logging tests pass
- No data loss in any scenario
- Sync fallback works reliably

**Phase 2 Success**:
- Feature parity with sync logger
- All sync logger tests pass with async logger
- Performance within 10% of sync logger

**Phase 3 Success**:
- Async-specific performance improvements
- Zero-copy operations working
- Graceful shutdown with no data loss

**Phase 4 Success**:
- Comprehensive test coverage (>95%)
- Performance benchmarks established
- Error recovery tested and verified

### 4.4 Updated Timeline

**CRITICAL TIMELINE**:
- **Next 24 hours**: Fix unawaited coroutine warnings
- **Next 48 hours**: Implement sync fallback and bounded queues
- **Next week**: Complete Phase 1 (Core Reliability)

**REVISED TIMELINE**:
- **Week 1**: Critical production issues + Immediate fixes
- **Week 2-3**: Phase 1 (Core Reliability)
- **Week 4-6**: Phase 2 (Feature Parity)
- **Week 7-8**: Phase 3 (Async Enhancements)
- **Week 9**: Phase 4 (Testing)
- **Total**: 9 weeks (reduced from 8-12 weeks due to critical issues)

### 4.5 Production Readiness Checklist

**IMMEDIATE CHECKLIST** (Next 24-48 hours):
- [ ] Fix all unawaited coroutine warnings
- [ ] Implement sync fallback for all async operations
- [ ] Add bounded queues with backpressure
- [ ] Implement graceful shutdown protocol
- [ ] Add comprehensive error handling
- [ ] Add production monitoring and alerting

**PHASE 1 CHECKLIST**:
- [ ] All async file writing tests pass
- [ ] Sync fallback works for all scenarios
- [ ] No data loss in any error condition
- [ ] Performance acceptable for production use

**PHASE 2 CHECKLIST**:
- [ ] Feature parity with sync logger achieved
- [ ] All sync logger tests pass with async logger
- [ ] Multiple destinations working correctly
- [ ] All formats supported

**PHASE 3 CHECKLIST**:
- [ ] Zero-copy operations implemented
- [ ] Async context propagation working
- [ ] Concurrent multi-destination writing
- [ ] Performance monitoring in place

**PHASE 4 CHECKLIST**:
- [ ] Test coverage >95%
- [ ] Performance benchmarks established
- [ ] Error recovery thoroughly tested
- [ ] Production deployment ready

---

## Conclusion

This refactor plan provides a comprehensive roadmap for transforming AsyncHydraLogger into a reliable async logging system that matches SyncHydraLogger's capabilities while providing async-specific optimizations and guaranteed data delivery.

**CRITICAL UPDATE**: The discovery of unawaited coroutine warnings and potential memory leaks requires immediate attention. These issues could cause serious problems in production, including data loss, resource exhaustion, and application crashes.

The phased approach ensures that critical reliability issues are addressed first, followed by feature parity and performance optimizations. Each phase includes multiple solution options to accommodate different requirements and constraints.

**Next Steps**:
1. **IMMEDIATE**: Address critical production issues (24-48 hours)
2. **SHORT-TERM**: Implement immediate fixes and Phase 1
3. **MEDIUM-TERM**: Complete feature parity (Phase 2)
4. **LONG-TERM**: Optimize performance and testing (Phase 3-4)

**Estimated Timeline**:
- **Critical Issues**: 24-48 hours
- **Phase 1**: 1-2 weeks
- **Phase 2**: 2-3 weeks
- **Phase 3**: 1-2 weeks
- **Phase 4**: 1 week
- **Total**: 9 weeks

This plan ensures that AsyncHydraLogger will be as reliable, feature-complete, and performant as SyncHydraLogger while providing good async capabilities and addressing the critical production issues that could cause data loss and system instability.

---

## IMPLEMENTATION PLAN: REFACTOR vs REBUILD

### **Analysis of Current State**

**Current Issues Identified:**
1. **AsyncBatchFileHandler**: Uses amateurish patterns, has unawaited coroutines, poor error handling
2. **AsyncHydraLogger**: Thin wrapper around sync logger, lacks proper async architecture
3. **AsyncContext**: Basic implementation, missing professional async patterns
4. **No CoroutineManager**: No proper task tracking or cleanup
5. **Poor Error Handling**: Uses print() instead of proper logging
6. **No Health Monitoring**: No visibility into async system health
7. **Inconsistent Patterns**: Mix of sync/async without clear boundaries

### **Decision: REBUILD (Recommended)**

**Why Rebuild:**
- Current implementation has fundamental architectural flaws
- Easier to build correctly from scratch than fix deeply embedded issues
- Can implement professional patterns from the start
- Better separation of concerns and cleaner architecture
- Can maintain backward compatibility through wrapper classes

---

## **PHASE-BY-PHASE IMPLEMENTATION PLAN**

### **PHASE 0: Foundation & Architecture (Week 1)**

#### **Step 0.1: Create Professional Async Skeleton**

**File Structure:**
```
hydra_logger/async_hydra/
├── __init__.py                    # Public API exports
├── core/                          # Core async components
│   ├── __init__.py
│   ├── coroutine_manager.py       # Professional task tracking
│   ├── event_loop_manager.py      # Event loop safety
│   ├── bounded_queue.py           # Professional queue implementation
│   ├── memory_monitor.py          # Memory monitoring
│   ├── shutdown_manager.py        # Safe shutdown protocol
│   ├── error_tracker.py           # Error tracking
│   └── health_monitor.py          # Health monitoring
├── handlers/                      # Async handlers
│   ├── __init__.py
│   ├── base_handler.py            # Base async handler
│   ├── file_handler.py            # Professional async file handler
│   ├── console_handler.py         # Async console handler
│   └── composite_handler.py       # Multi-handler support
├── context/                       # Async context management
│   ├── __init__.py
│   ├── context_manager.py         # Professional context management
│   ├── trace_manager.py           # Distributed tracing
│   └── context_switcher.py        # Context switch detection
├── logger.py                      # Main async logger
├── performance.py                 # Performance monitoring
└── compatibility.py               # Backward compatibility layer
```

#### **Step 0.2: Implement Core Components**

**0.2.1: CoroutineManager (Professional Task Tracking)**
```python
# hydra_logger/async_hydra/core/coroutine_manager.py
class CoroutineManager:
    def __init__(self, shutdown_timeout=2.0):
        self._tasks = set()
        self._shutdown_timeout = shutdown_timeout
        self._shutdown_event = asyncio.Event()
        self._cleanup_lock = asyncio.Lock()
    
    def track(self, coro):
        """Track a coroutine with automatic cleanup."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
    
    async def shutdown(self):
        """Professional shutdown with proper timeout handling."""
        async with self._cleanup_lock:
            if not self._tasks:
                return
            
            # Signal shutdown to all tasks
            self._shutdown_event.set()
            
            # Cancel all tasks immediately
            cancel_tasks = [task.cancel() for task in list(self._tasks)]
            
            # Wait for all tasks to complete with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=self._shutdown_timeout
                )
            except asyncio.TimeoutError:
                remaining = len([t for t in self._tasks if not t.done()])
                if remaining > 0:
                    print(f"WARNING: {remaining} tasks did not complete within {self._shutdown_timeout}s")
            
            self._tasks.clear()
```

**0.2.2: EventLoopManager (Event Loop Safety)**
```python
# hydra_logger/async_hydra/core/event_loop_manager.py
class EventLoopManager:
    @staticmethod
    def has_running_loop():
        """Professional check for running event loop."""
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    
    @staticmethod
    def safe_create_task(coro):
        """Safely create task only if event loop is running."""
        if EventLoopManager.has_running_loop():
            return asyncio.create_task(coro)
        else:
            raise RuntimeError("No event loop running")
    
    @staticmethod
    async def safe_async_operation(operation, fallback_operation=None):
        """Execute async operation with professional fallback."""
        if EventLoopManager.has_running_loop():
            try:
                return await operation()
            except Exception as e:
                if fallback_operation:
                    return fallback_operation()
                raise
        else:
            if fallback_operation:
                return fallback_operation()
            raise RuntimeError("No event loop and no fallback provided")
```

**0.2.3: BoundedAsyncQueue (Professional Queue)**
```python
# hydra_logger/async_hydra/core/bounded_queue.py
class BoundedAsyncQueue:
    def __init__(self, maxsize=1000, policy='drop_oldest', put_timeout=0.1, get_timeout=1.0):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._policy = policy
        self._dropped_count = 0
        self._put_timeout = put_timeout
        self._get_timeout = get_timeout
        self._stats = {
            'puts': 0,
            'gets': 0,
            'drops': 0,
            'timeouts': 0
        }
    
    async def put(self, item):
        """Professional put with configurable backpressure policy."""
        self._stats['puts'] += 1
        
        try:
            await asyncio.wait_for(self._queue.put(item), timeout=self._put_timeout)
        except asyncio.TimeoutError:
            self._stats['timeouts'] += 1
            if self._policy == 'drop_oldest':
                try:
                    self._queue.get_nowait()
                    await asyncio.wait_for(self._queue.put(item), timeout=self._put_timeout)
                    self._dropped_count += 1
                    self._stats['drops'] += 1
                except (asyncio.QueueEmpty, asyncio.TimeoutError):
                    raise asyncio.QueueFull("Queue is full and drop_oldest failed")
            elif self._policy == 'error':
                raise asyncio.QueueFull("Queue is full")
            else:  # block policy
                await self._queue.put(item)
    
    async def get(self):
        """Professional get with timeout."""
        self._stats['gets'] += 1
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=self._get_timeout)
        except asyncio.TimeoutError:
            self._stats['timeouts'] += 1
            return None
```

#### **Step 0.3: Implement Professional Handlers**

**0.3.1: Base Async Handler**
```python
# hydra_logger/async_hydra/handlers/base_handler.py
class BaseAsyncHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._coroutine_manager = CoroutineManager()
        self._error_tracker = AsyncErrorTracker()
        self._health_monitor = AsyncHealthMonitor(self)
    
    async def emit_async(self, record):
        """Professional async emit with proper error handling."""
        try:
            return await EventLoopManager.safe_async_operation(
                lambda: self._coroutine_manager.track(self._emit_async_internal(record)),
                lambda: self._write_record_sync(record)
            )
        except Exception as e:
            await self._error_tracker.record_error("emit_async", e)
            return self._write_record_sync(record)
    
    async def aclose(self):
        """Professional async close."""
        await self._coroutine_manager.shutdown()
        await self._error_tracker.shutdown()
```

**0.3.2: Professional File Handler**
```python
# hydra_logger/async_hydra/handlers/file_handler.py
class ProfessionalAsyncFileHandler(BaseAsyncHandler):
    def __init__(self, filename, **kwargs):
        super().__init__()
        self.filename = filename
        self._queue = BoundedAsyncQueue(maxsize=kwargs.get('max_queue_size', 1000))
        self._memory_monitor = MemoryMonitor()
        self._shutdown_manager = SafeShutdownManager()
        self._writer_task = None
        self._running = False
    
    async def emit_async(self, record):
        """Professional async emit with memory monitoring."""
        if not self._memory_monitor.check_memory():
            return self._write_record_sync(record)
        
        msg = self.format(record) + '\n'
        await self._queue.put(msg)
        
        if self._writer_task is None:
            self._writer_task = self._coroutine_manager.track(self._writer())
    
    async def _writer(self):
        """Professional background writer."""
        async with aiofiles.open(self.filename, 'a', encoding='utf-8') as f:
            while self._running:
                msg = await self._queue.get()
                if msg is None:
                    continue
                
                await f.write(msg)
                await f.flush()
    
    async def aclose(self):
        """Professional async close with data integrity."""
        self._running = False
        await self._shutdown_manager.shutdown()
        await super().aclose()
```

### **PHASE 1: Core Implementation (Week 2)**

#### **Step 1.1: Implement Main Async Logger**
```python
# hydra_logger/async_hydra/logger.py
class AsyncHydraLogger:
    def __init__(self, config=None, **kwargs):
        self._config = config
        self._handlers = []
        self._coroutine_manager = CoroutineManager()
        self._error_tracker = AsyncErrorTracker()
        self._health_monitor = AsyncHealthMonitor(self)
        self._performance_monitor = AsyncPerformanceMonitor()
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup handlers based on configuration."""
        if self._config:
            for destination in self._config.destinations:
                handler = self._create_handler(destination)
                if handler:
                    self._handlers.append(handler)
    
    async def log(self, layer, level, message, **kwargs):
        """Professional async logging."""
        record = self._create_record(layer, level, message, **kwargs)
        
        for handler in self._handlers:
            try:
                await handler.emit_async(record)
            except Exception as e:
                await self._error_tracker.record_error("handler_emit", e)
    
    async def aclose(self):
        """Professional async close."""
        await self._coroutine_manager.shutdown()
        await self._error_tracker.shutdown()
        await self._health_monitor.shutdown()
        
        for handler in self._handlers:
            await handler.aclose()
```

#### **Step 1.2: Implement Context Management**
```python
# hydra_logger/async_hydra/context/context_manager.py
class ProfessionalAsyncContextManager:
    def __init__(self, context=None):
        self.context = context or AsyncContext()
        self._previous_context = None
        self._context_var = contextvars.ContextVar('async_context')
    
    async def __aenter__(self):
        """Professional async context entry."""
        self._previous_context = self._context_var.get(None)
        self._context_var.set(self.context)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Professional async context exit."""
        if self._previous_context is not None:
            self._context_var.set(self._previous_context)
        else:
            self._context_var.set(None)
```

### **PHASE 2: Integration & Testing (Week 3)**

#### **Step 2.1: Create Backward Compatibility Layer**
```python
# hydra_logger/async_hydra/compatibility.py
class BackwardCompatibleAsyncHydraLogger:
    """Backward compatibility wrapper for existing code."""
    
    def __init__(self, *args, **kwargs):
        self._logger = AsyncHydraLogger(*args, **kwargs)
    
    async def info(self, layer_or_message, message=None):
        """Backward compatible info method."""
        if message is None:
            layer, message = "DEFAULT", layer_or_message
        else:
            layer = layer_or_message
        await self._logger.log(layer, "INFO", message)
    
    # ... other backward compatible methods
```

#### **Step 2.2: Update Public API**
```python
# hydra_logger/async_hydra/__init__.py
from .logger import AsyncHydraLogger
from .context.context_manager import ProfessionalAsyncContextManager as AsyncContextManager
from .compatibility import BackwardCompatibleAsyncHydraLogger

__all__ = [
    "AsyncHydraLogger",
    "AsyncContextManager", 
    "BackwardCompatibleAsyncHydraLogger"
]
```

### **PHASE 3: Testing & Validation (Week 4)**

#### **Step 3.1: Comprehensive Test Suite**
```python
# tests/unit/async/test_professional_async_logger.py
class TestProfessionalAsyncLogger:
    @pytest.mark.asyncio
    async def test_basic_logging(self):
        """Test basic async logging functionality."""
        logger = AsyncHydraLogger()
        await logger.log("TEST", "INFO", "Test message")
        # Verify message was logged
    
    @pytest.mark.asyncio
    async def test_memory_backpressure(self):
        """Test memory backpressure handling."""
        # Test high memory usage scenarios
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test graceful shutdown with pending messages."""
        # Test shutdown with pending messages
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test error recovery and fallback."""
        # Test error scenarios and fallbacks
```

#### **Step 3.2: Performance Testing**
```python
# tests/performance/test_async_performance.py
class TestAsyncPerformance:
    @pytest.mark.asyncio
    async def test_high_throughput(self):
        """Test high-throughput logging scenarios."""
        # Test 10,000+ messages per second
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test concurrent access patterns."""
        # Test multiple coroutines logging simultaneously
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage under load."""
        # Test memory usage patterns
```

### **PHASE 4: Documentation & Deployment (Week 5)**

#### **Step 4.1: Update Documentation**
- Update README with new async patterns
- Add migration guide from old async implementation
- Document professional async usage patterns
- Add troubleshooting guide

#### **Step 4.2: Gradual Migration Strategy**
1. **Week 1**: Deploy new implementation alongside old one
2. **Week 2**: Update tests to use new implementation
3. **Week 3**: Migrate internal usage to new implementation
4. **Week 4**: Deprecate old implementation
5. **Week 5**: Remove old implementation

---

## **IMPLEMENTATION TIMELINE**

### **Week 1: Foundation**
- [ ] Create new async_hydra skeleton structure
- [ ] Implement CoroutineManager, EventLoopManager, BoundedAsyncQueue
- [ ] Implement base async handler
- [ ] Basic tests for core components

### **Week 2: Core Implementation**
- [ ] Implement AsyncHydraLogger
- [ ] Implement ProfessionalAsyncFileHandler
- [ ] Implement context management
- [ ] Integration tests

### **Week 3: Integration & Testing**
- [ ] Create backward compatibility layer
- [ ] Update public API
- [ ] Comprehensive test suite
- [ ] Performance testing

### **Week 4: Testing & Validation**
- [ ] End-to-end testing
- [ ] Performance benchmarking
- [ ] Error recovery testing
- [ ] Memory leak testing

### **Week 5: Documentation & Deployment**
- [ ] Update documentation
- [ ] Create migration guide
- [ ] Gradual deployment
- [ ] Monitor and validate

---

## **SUCCESS CRITERIA**

### **Technical Criteria**
- [ ] No unawaited coroutine warnings
- [ ] 100% test coverage for async components
- [ ] Performance within 10% of sync logger
- [ ] Data loss protection in all scenarios
- [ ] Graceful shutdown with pending message handling

### **Quality Criteria**
- [ ] Professional async patterns throughout
- [ ] Comprehensive error handling
- [ ] Health monitoring and alerting
- [ ] Memory leak prevention
- [ ] Production-ready reliability

### **Compatibility Criteria**
- [ ] Backward compatibility maintained
- [ ] Easy migration path
- [ ] No breaking changes for existing users
- [ ] Clear upgrade documentation

This plan ensures we build a **reliable async logging system** from the ground up, with professional patterns, comprehensive testing, and smooth migration path.

---

## **DETAILED ASYNC_HYDRA MODULE STRUCTURE**

### **Current vs New Architecture**

**Current Structure (Problematic):**
```
hydra_logger/async_hydra/
├── __init__.py                    # Basic exports
├── async_batch_file_handler.py    # Amateurish implementation
├── async_logger.py                # Thin wrapper around sync
└── async_context.py               # Basic context management
```

**New Professional Structure:**
```
hydra_logger/async_hydra/
├── __init__.py                    # Public API exports
├── core/                          # Core async components
│   ├── __init__.py
│   ├── coroutine_manager.py       # Professional task tracking
│   ├── event_loop_manager.py      # Event loop safety
│   ├── bounded_queue.py           # Professional queue implementation
│   ├── memory_monitor.py          # Memory monitoring
│   ├── shutdown_manager.py        # Safe shutdown protocol
│   ├── error_tracker.py           # Error tracking
│   └── health_monitor.py          # Health monitoring
├── handlers/                      # Async handlers
│   ├── __init__.py
│   ├── base_handler.py            # Base async handler
│   ├── file_handler.py            # Professional async file handler
│   ├── console_handler.py         # Async console handler
│   └── composite_handler.py       # Multi-handler support
├── context/                       # Async context management
│   ├── __init__.py
│   ├── context_manager.py         # Professional context management
│   ├── trace_manager.py           # Distributed tracing
│   └── context_switcher.py        # Context switch detection
├── logger.py                      # Main async logger
├── performance.py                 # Performance monitoring
└── compatibility.py               # Backward compatibility layer
```

---

## **MODULE DETAILS & RESPONSIBILITIES**

### **1. Core Components (`core/`)**

#### **1.1 `coroutine_manager.py`**
**Purpose**: Professional task tracking and cleanup
**Key Features**:
- Track all background tasks (writer, flushers, monitors)
- Timeout-based cleanup to prevent hangs
- Proper task cancellation and cleanup
- Thread-safe operations with locks

**Classes**:
```python
class CoroutineManager:
    - track(coro): Track a coroutine with automatic cleanup
    - shutdown(): Professional shutdown with timeout
    - get_active_tasks(): Get list of active tasks
    - cancel_all(): Cancel all tracked tasks
```

#### **1.2 `event_loop_manager.py`**
**Purpose**: Event loop safety and fallback management
**Key Features**:
- Safe event loop detection
- Graceful fallback to sync operations
- Professional error handling for async context

**Classes**:
```python
class EventLoopManager:
    - has_running_loop(): Check for running event loop
    - safe_create_task(coro): Safely create tasks
    - safe_async_operation(operation, fallback): Execute with fallback
```

#### **1.3 `bounded_queue.py`**
**Purpose**: Professional async queue with backpressure
**Key Features**:
- Configurable queue policies (drop_oldest, block, error)
- Memory monitoring integration
- Comprehensive statistics tracking
- Timeout-based operations

**Classes**:
```python
class BoundedAsyncQueue:
    - put(item): Professional put with backpressure
    - get(): Professional get with timeout
    - get_stats(): Comprehensive queue statistics
    - get_dropped_count(): Track dropped messages
```

#### **1.4 `memory_monitor.py`**
**Purpose**: Memory usage monitoring and backpressure
**Key Features**:
- Real-time memory usage tracking
- Configurable memory thresholds
- Caching to avoid excessive system calls
- Professional warning system

**Classes**:
```python
class MemoryMonitor:
    - check_memory(): Check if memory usage is acceptable
    - get_memory_stats(): Get detailed memory statistics
    - set_threshold(percent): Configure memory threshold
```

#### **1.5 `shutdown_manager.py`**
**Purpose**: Safe shutdown protocol with data integrity
**Key Features**:
- Multi-phase shutdown (flushing → cleaning → done)
- Timeout-based operations
- Sync fallback when async fails
- Data integrity guarantees

**Classes**:
```python
class SafeShutdownManager:
    - shutdown(): Professional multi-phase shutdown
    - _flush_remaining_messages(): Flush pending messages
    - _cleanup_resources(): Cleanup all resources
```

#### **1.6 `error_tracker.py`**
**Purpose**: Comprehensive error tracking and monitoring
**Key Features**:
- Async-safe error recording
- Error statistics and trends
- Callback system for error handling
- Professional error categorization

**Classes**:
```python
class AsyncErrorTracker:
    - record_error(error_type, error): Record error
    - get_error_stats(): Get error statistics
    - add_error_callback(callback): Add error callback
```

#### **1.7 `health_monitor.py`**
**Purpose**: System health monitoring and alerting
**Key Features**:
- Real-time health status
- Performance metrics
- Queue health monitoring
- Caching for performance

**Classes**:
```python
class AsyncHealthMonitor:
    - get_health_status(): Get comprehensive health status
    - is_healthy(): Check if system is healthy
    - get_performance_metrics(): Get performance data
```

### **2. Handlers (`handlers/`)**

#### **2.1 `base_handler.py`**
**Purpose**: Base class for all async handlers
**Key Features**:
- Common async handler functionality
- Error handling and fallback
- Coroutine management integration
- Professional async patterns

**Classes**:
```python
class BaseAsyncHandler(logging.Handler):
    - emit_async(record): Professional async emit
    - aclose(): Professional async close
    - _write_record_sync(record): Sync fallback
```

#### **2.2 `file_handler.py`**
**Purpose**: Professional async file handler
**Key Features**:
- True async file I/O with aiofiles
- Memory monitoring integration
- Bounded queue with backpressure
- Professional error handling

**Classes**:
```python
class ProfessionalAsyncFileHandler(BaseAsyncHandler):
    - emit_async(record): Async emit with memory monitoring
    - _writer(): Professional background writer
    - aclose(): Async close with data integrity
```

#### **2.3 `console_handler.py`**
**Purpose**: Async console output handler
**Key Features**:
- Async console output
- Performance optimization
- Error handling

**Classes**:
```python
class AsyncConsoleHandler(BaseAsyncHandler):
    - emit_async(record): Async console emit
    - _write_to_console(msg): Write to console
```

#### **2.4 `composite_handler.py`**
**Purpose**: Multi-handler support
**Key Features**:
- Multiple handler management
- Parallel handler execution
- Error isolation between handlers

**Classes**:
```python
class AsyncCompositeHandler:
    - emit_async(record): Emit to all handlers
    - add_handler(handler): Add new handler
    - remove_handler(handler): Remove handler
    - close(): Close all handlers
```

### **3. Context Management (`context/`)**

#### **3.1 `context_manager.py`**
**Purpose**: Professional async context management
**Key Features**:
- Context preservation across async operations
- Thread-safe context operations
- Professional error handling

**Classes**:
```python
class ProfessionalAsyncContextManager:
    - __aenter__(): Professional context entry
    - __aexit__(): Professional context exit
    - get_current_context(): Get current context
    - set_current_context(context): Set context
```

#### **3.2 `trace_manager.py`**
**Purpose**: Distributed tracing support
**Key Features**:
- Trace ID generation and propagation
- Correlation ID management
- Professional tracing patterns

**Classes**:
```python
class AsyncTraceManager:
    - start_trace(trace_id): Start new trace
    - get_trace_id(): Get current trace ID
    - set_correlation_id(correlation_id): Set correlation ID
    - clear_trace(): Clear current trace
```

#### **3.3 `context_switcher.py`**
**Purpose**: Context switch detection
**Key Features**:
- Detect async context switches
- Track context switch patterns
- Professional context monitoring

**Classes**:
```python
class AsyncContextSwitcher:
    - detect_context_switch(context): Detect switches
    - get_switch_count(): Get switch count
    - reset_switch_count(): Reset counter
```

### **4. Main Logger (`logger.py`)**

#### **4.1 Main Logger Class**
**Purpose**: Main async logger implementation
**Key Features**:
- Professional async logging interface
- Handler management
- Performance monitoring integration
- Error handling and recovery

**Classes**:
```python
class AsyncHydraLogger:
    - log(layer, level, message): Professional async logging
    - info/debug/warning/error/critical(): Convenience methods
    - aclose(): Professional async close
    - get_health_status(): Get health status
    - get_performance_metrics(): Get performance data
```

### **5. Performance Monitoring (`performance.py`)**

#### **5.1 Performance Monitor**
**Purpose**: Async performance monitoring
**Key Features**:
- Async operation timing
- Performance statistics
- Memory usage tracking
- Professional metrics

**Classes**:
```python
class AsyncPerformanceMonitor:
    - start_async_processing_timer(): Start timer
    - end_async_processing_timer(start_time): End timer
    - get_async_statistics(): Get statistics
    - reset_async_statistics(): Reset statistics
```

### **6. Backward Compatibility (`compatibility.py`)**

#### **6.1 Compatibility Layer**
**Purpose**: Maintain backward compatibility
**Key Features**:
- Wrapper for existing code
- Gradual migration support
- No breaking changes

**Classes**:
```python
class BackwardCompatibleAsyncHydraLogger:
    - info/debug/warning/error(): Backward compatible methods
    - __init__(*args, **kwargs): Compatible initialization
```

### **7. Public API (`__init__.py`)**

#### **7.1 Public Exports**
**Purpose**: Clean public API
**Exports**:
```python
__all__ = [
    "AsyncHydraLogger",              # Main async logger
    "AsyncContextManager",           # Context management
    "AsyncTraceManager",             # Distributed tracing
    "AsyncHealthMonitor",            # Health monitoring
    "BackwardCompatibleAsyncHydraLogger",  # Compatibility
]
```

---

## **IMPLEMENTATION PRIORITY**

### **Phase 1: Core Foundation (Week 1)**
1. **`core/coroutine_manager.py`** - Task tracking (CRITICAL)
2. **`core/event_loop_manager.py`** - Event loop safety (CRITICAL)
3. **`core/bounded_queue.py`** - Professional queue (CRITICAL)
4. **`core/memory_monitor.py`** - Memory monitoring (HIGH)
5. **`core/shutdown_manager.py`** - Safe shutdown (HIGH)

### **Phase 2: Handlers & Context (Week 2)**
1. **`handlers/base_handler.py`** - Base handler (CRITICAL)
2. **`handlers/file_handler.py`** - File handler (CRITICAL)
3. **`context/context_manager.py`** - Context management (HIGH)
4. **`logger.py`** - Main logger (CRITICAL)

### **Phase 3: Integration & Testing (Week 3)**
1. **`compatibility.py`** - Backward compatibility (HIGH)
2. **`performance.py`** - Performance monitoring (MEDIUM)
3. **`handlers/console_handler.py`** - Console handler (MEDIUM)
4. **`handlers/composite_handler.py`** - Multi-handler (MEDIUM)

### **Phase 4: Advanced Features (Week 4)**
1. **`context/trace_manager.py`** - Distributed tracing (MEDIUM)
2. **`context/context_switcher.py`** - Context switching (LOW)
3. **`core/error_tracker.py`** - Error tracking (HIGH)
4. **`core/health_monitor.py`** - Health monitoring (HIGH)

---

## **MIGRATION STRATEGY**

### **Step 1: Create New Structure**
- Create new directory structure
- Implement core components first
- Maintain existing files during transition

### **Step 2: Implement Core Components**
- Start with CoroutineManager (most critical)
- Add EventLoopManager for safety
- Implement BoundedAsyncQueue for reliability

### **Step 3: Create New Handlers**
- Implement ProfessionalAsyncFileHandler
- Replace old AsyncBatchFileHandler gradually
- Maintain backward compatibility

### **Step 4: Update Public API**
- Update `__init__.py` exports
- Create compatibility layer
- Gradual migration of existing code

### **Step 5: Remove Old Implementation**
- Deprecate old components
- Remove old files
- Update documentation

This detailed module structure ensures we build a **professional, scalable, and maintainable** async logging system with clear separation of concerns and proper async patterns throughout. 