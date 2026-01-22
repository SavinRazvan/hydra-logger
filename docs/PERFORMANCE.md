# Hydra-Logger Performance

This document provides detailed performance benchmarks, optimization strategies, and performance characteristics of Hydra-Logger.

---

## Performance Benchmarks

### Latest Benchmark Results

**Test Configuration**: 100K messages, file-only handlers (console I/O is slower)

```
- SyncLogger: 34,469+ messages/second
- AsyncLogger: 24,875+ messages/second  
- CompositeLogger: 32,773+ messages/second (individual), 41,096+ (batched)
- CompositeAsyncLogger: 70,174+ messages/second (individual), 386,399+ (batched)
- Concurrent Logging: 414,508+ messages/second (8 async workers, aggregate)
- File Writing: 33,324+ messages/second (sync), 25,890+ messages/second (async)
```

### Performance Optimizations

**Key Optimizations Implemented:**

- **File-only handlers**: Used for performance testing (console I/O is slower)
- **Batch logging**: Composite logger uses component batch methods when available
- **Fast path**: Direct queue injection bypasses LogRecord creation for simple cases
- **Persistent file handles**: Eliminates open/close overhead per batch
- **Batch writing**: Single I/O operation per batch (all messages joined)
- **Dynamic buffering**: Adaptive buffer sizing based on throughput
- **16MB file buffers**: Large buffers for high throughput
- **Background workers**: Persistent tasks eliminate executor overhead
- **Memory efficiency**: Minimal overhead when features disabled
- **Async task optimization**: Single event loop instead of threads for concurrent tests

---

## Buffer Configuration

### Default Buffer Sizes

- **ConsoleHandler**: 
  - Buffer size: 5,000 messages
  - Flush interval: 0.5 seconds
  
- **FileHandler**: 
  - Buffer size: 50,000 messages
  - Flush interval: 5.0 seconds

- **AsyncLogger**:
  - Main queue: Unbounded
  - Overflow queue: 100,000 messages (maxsize)

### Performance Impact

Larger buffers improve throughput but increase memory usage and latency. The default values are optimized for balanced performance.

---

## Benchmark Results Storage

- Results automatically saved to `benchmark_results/benchmark_YYYY-MM-DD_HH-MM-SS.json`
- Latest results also saved to `benchmark_results/benchmark_latest.json`
- Includes metadata: timestamp, test config, Python version, platform
- Full performance metrics for all logger types and test scenarios

---

## Running Benchmarks

```bash
# Run the comprehensive performance benchmark suite
python3 performance_benchmark.py

# The benchmark tests:
# - SyncLogger, AsyncLogger, CompositeLogger performance
# - Individual message throughput (100K messages)
# - Batch processing efficiency
# - File writing performance
# - Concurrent logging capabilities (8-50 workers)
# - Memory usage patterns
# - Configuration impact on performance
```

---

## Performance Characteristics

### SyncLogger
- **Throughput**: 34K+ messages/second
- **Latency**: Immediate (blocking)
- **Use Case**: Simple applications, debugging, low-volume logging

### AsyncLogger
- **Throughput**: 25K+ messages/second (individual), 414K+ (concurrent)
- **Latency**: Non-blocking (queue-based)
- **Use Case**: High-performance applications, high-volume logging

### CompositeLogger
- **Throughput**: 33K+ messages/second (individual), 41K+ (batched)
- **Latency**: Depends on component loggers
- **Use Case**: Complex scenarios requiring multiple logging strategies

### CompositeAsyncLogger
- **Throughput**: 70K+ messages/second (individual), 386K+ (batched)
- **Latency**: Non-blocking
- **Use Case**: High-performance composite logging

---

## Optimization Strategies

### 1. Buffer Sizing
- Larger buffers = higher throughput, higher memory usage
- Smaller buffers = lower latency, lower throughput
- Default values optimized for balanced performance

### 2. Batch Processing
- Batch multiple messages together
- Single I/O operation per batch
- Significant throughput improvement

### 3. Handler Selection
- File handlers faster than console handlers
- Network handlers slower (network latency)
- Use appropriate handler for use case

### 4. Extension Management
- Disable unused extensions (zero overhead)
- Enable only needed extensions
- Runtime enable/disable for flexibility

### 5. Performance Profiles
- **minimal**: Fastest, no context extraction
- **context**: Balanced, explicit context
- **convenient**: Auto-detects context (slightly slower)

---

## Technical Improvements

### Logger Functionality Fixes
- Fixed `CompositeLogger` missing `_setup_from_config` method
- Fixed `AsyncLogger` coroutine return in async contexts
- Fixed file buffering issues for all handlers
- Fixed multiple destinations functionality
- Fixed `RecursionError` in task cancellation
- Fixed "Task was destroyed but it is pending!" warnings
- Fixed `_worker_task` vs `_worker_tasks` attribute errors
- Fixed optional imports (`yaml`, `toml`) with graceful fallbacks

### Architecture Improvements
- Applied KISS principle throughout
- Implemented event-oriented architecture
- Background worker architecture: Replaced per-flush executor calls with persistent worker tasks
- Queue-based async handling: Non-blocking message queuing for concurrent logging
- Benchmark state management: Proper logger cache cleanup between tests
- Maintained zero overhead when features disabled
- Consistent naming conventions
- Clean, maintainable code structure

### Examples Optimization
- Reduced sleep times in examples for faster execution (2-3x faster)
- All 16 examples passing and verified
- Consistent file extension usage (`.jsonl` for json-lines format)
- Optimized async examples for better performance

---

## Performance Notes

### Console I/O Performance
- Console I/O is slower than file I/O
- Performance benchmarks use file-only handlers
- Console handlers include buffering for better performance
- Colors add minimal overhead (ANSI codes are small)

### File I/O Performance
- File handlers use large buffers (50K messages, 5s flush)
- Persistent file handles eliminate open/close overhead
- Batch writing reduces I/O operations
- 16MB file buffers for high throughput

### Async Performance
- Queue-based processing for non-blocking operations
- Concurrency control with semaphores
- Overflow queue for burst traffic
- Background workers for continuous processing

---

## Related Documentation

- **[WORKFLOW_ARCHITECTURE.md](WORKFLOW_ARCHITECTURE.md)** - Complete workflow details
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Package structure and components
- **[README.md](../README.md)** - Quick start and overview
