# HydraLogger Configuration Quick Reference

## High-Performance Use Cases

### Web Applications (103K messages/sec)
```python
logger = HydraLogger.for_web_app()
```
**Best for**: Web applications, frontend logging

### Development (101K messages/sec)
```python
logger = HydraLogger.for_development()
```
**Best for**: Development workflows, debugging, testing

### Microservices (101K messages/sec)
```python
logger = HydraLogger.for_microservice()
```
**Best for**: Containerized services, distributed systems

### Background Workers (100K messages/sec)
```python
logger = HydraLogger.for_background_worker()
```
**Best for**: Queue processors, scheduled tasks, batch operations

### Production Systems (98K messages/sec)
```python
logger = HydraLogger.for_production()
```
**Best for**: Live production environments, enterprise applications

### API Services (82K messages/sec)
```python
logger = HydraLogger.for_api_service()
```
**Best for**: REST APIs, GraphQL services, high-traffic endpoints

## Production Use Cases

### File Logging (32K messages/sec)
```python
logger = HydraLogger()  # Default configuration
```
**Best for**: Standard file logging, persistent storage

## Performance-Optimized Use Cases

### Bare Metal Mode (~14K messages/sec)
```python
logger = HydraLogger.for_bare_metal()
```
**Best for**: Maximum throughput, minimal overhead
**Trade-off**: Reduced features for speed
**Performance**: 13,808 messages/sec (console), 13,836 messages/sec (file)

### Minimal Features Mode (~14K messages/sec)
```python
logger = HydraLogger.for_minimal_features()
```
**Best for**: Balanced performance and features
**Trade-off**: Good balance of speed and capabilities
**Performance**: 13,796 messages/sec (console), 14,024 messages/sec (file)

## File vs Console Logging

### Console Logging (16K - 103K messages/sec)
```python
# Use for real-time monitoring and debugging
logger.info("DEFAULT", "Real-time log message")
```

### File Logging (14K - 32K messages/sec)
```python
# Use for persistent logging and audit trails
logger.info("DEFAULT", "Persistent log message")
```

## Configuration Selection Guide

| Use Case | Recommended Configuration | Performance | Key Benefit |
|----------|-------------------------|-------------|-------------|
| **Web applications** | `for_web_app()` | 103K/sec | Web request logging |
| **Development** | `for_development()` | 101K/sec | Enhanced debugging |
| **Microservices** | `for_microservice()` | 101K/sec | Lightweight, service-oriented |
| **Background jobs** | `for_background_worker()` | 100K/sec | Batch operation optimization |
| **Production systems** | `for_production()` | 98K/sec | Enterprise-ready features |
| **High-traffic APIs** | `for_api_service()` | 82K/sec | Optimized for request/response |
| **Maximum speed** | `for_bare_metal()` | ~14K/sec | Minimal overhead |
| **Balanced approach** | `for_minimal_features()` | ~14K/sec | Speed + features |

## Performance Tips

### For Maximum Throughput
1. Use specialized configurations (Web App, Development, Microservice)
2. Prefer file logging over console
3. Use Bare Metal mode for critical paths

### For Production Reliability
1. Use Production configuration as default
2. Enable comprehensive error handling
3. Monitor memory usage

### For Development
1. Use Development configuration
2. Enable detailed logging
3. Use console output for real-time debugging

## Performance Comparison

### Console Logging Performance
- **Web App**: 103,344 messages/sec
- **Development**: 100,655 messages/sec
- **Microservice**: 100,743 messages/sec
- **Background Worker**: 99,519 messages/sec
- **Production**: 97,520 messages/sec
- **API Service**: 81,831 messages/sec
- **Default**: 16,140 messages/sec

### File Logging Performance
- **Default File**: 31,692 messages/sec
- **Minimal Features**: 14,024 messages/sec
- **Bare Metal**: 13,836 messages/sec

## Important Notes

- **Memory Management**: All configurations include memory leak detection
- **Error Handling**: Comprehensive fallback mechanisms ensure message delivery
- **Reliability**: Zero memory leaks detected in all tests
- **Compatibility**: All configurations work with both sync and async logging

## Getting Started

```python
from hydra_logger import HydraLogger

# For web applications
logger = HydraLogger.for_web_app()
logger.info("DEFAULT", "Web request processed")

# For development
logger = HydraLogger.for_development()
logger.info("DEFAULT", "Debug message")

# For microservices
logger = HydraLogger.for_microservice()
logger.info("DEFAULT", "Service log message")

# For background workers
logger = HydraLogger.for_background_worker()
logger.info("DEFAULT", "Background job completed")

# For production systems
logger = HydraLogger.for_production()
logger.info("DEFAULT", "Production log message")

# For maximum performance
logger = HydraLogger.for_bare_metal()
logger.info("DEFAULT", "Bare metal log message")
```

---

*Performance data from comprehensive benchmark testing*  
*All configurations tested with 10,000 messages and memory leak detection* 