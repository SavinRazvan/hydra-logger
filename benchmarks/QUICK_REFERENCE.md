# HydraLogger Configuration Quick Reference

## 🚀 High-Performance Use Cases

### Production Systems (108K messages/sec)
```python
logger = HydraLogger.for_production()
```
**Best for**: Live production environments, enterprise applications

### API Services (108K messages/sec)
```python
logger = HydraLogger.for_api_service()
```
**Best for**: REST APIs, GraphQL services, high-traffic endpoints

### Background Workers (108K messages/sec)
```python
logger = HydraLogger.for_background_worker()
```
**Best for**: Queue processors, scheduled tasks, batch operations

### Microservices (108K messages/sec)
```python
logger = HydraLogger.for_microservice()
```
**Best for**: Containerized services, distributed systems

## 🏭 Production Use Cases

### Development (108K messages/sec)
```python
logger = HydraLogger.for_development()
```
**Best for**: Development workflows, debugging, testing

### Web Applications (108K messages/sec)
```python
logger = HydraLogger.for_web_app()
```
**Best for**: Web applications, frontend logging

## ⚡ Performance-Optimized Use Cases

### Bare Metal Mode (~20K messages/sec)
```python
logger = HydraLogger.for_bare_metal()
```
**Best for**: Maximum throughput, minimal overhead
**Trade-off**: Reduced features for speed
**Performance**: 20,000 messages/sec (file), 20,000 messages/sec (console)

### Minimal Features Mode (~20K messages/sec)
```python
logger = HydraLogger.for_minimal_features()
```
**Best for**: Balanced performance and features
**Trade-off**: Good balance of speed and capabilities
**Performance**: 20,000 messages/sec (file), 20,000 messages/sec (console)

## 📁 File vs Console Logging

### Console Logging (16K - 108K messages/sec)
```python
# Use for real-time monitoring and debugging
logger.info("DEFAULT", "Real-time log message")
```

### File Logging (20K - 40K messages/sec)
```python
# Use for persistent logging and audit trails
logger.info("DEFAULT", "Persistent log message")
```

## 🎯 Configuration Selection Guide

| Use Case | Recommended Configuration | Performance | Key Benefit |
|----------|-------------------------|-------------|-------------|
| **Production systems** | `for_production()` | 108K/sec | Enterprise-ready features |
| **High-traffic APIs** | `for_api_service()` | 108K/sec | Optimized for request/response |
| **Background jobs** | `for_background_worker()` | 108K/sec | Batch operation optimization |
| **Microservices** | `for_microservice()` | 108K/sec | Lightweight, service-oriented |
| **Development** | `for_development()` | 108K/sec | Enhanced debugging |
| **Web applications** | `for_web_app()` | 108K/sec | Web request logging |
| **Maximum speed** | `for_bare_metal()` | ~20K/sec | Minimal overhead |
| **Balanced approach** | `for_minimal_features()` | ~20K/sec | Speed + features |

## 🔧 Performance Tips

### For Maximum Throughput
1. Use specialized configurations (API Service, Background Worker)
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

## 📊 Performance Comparison

### Console Logging Performance
- **Production**: 107,980 messages/sec ⭐
- **API Service**: 107,980 messages/sec ⭐
- **Background Worker**: 107,980 messages/sec ⭐
- **Microservice**: 107,980 messages/sec ⭐
- **Development**: 107,980 messages/sec ⭐
- **Web App**: 107,980 messages/sec ⭐
- **Default**: 15,700 messages/sec

### File Logging Performance
- **Default File**: 39,600 messages/sec ⭐
- **Minimal Features**: 20,000 messages/sec
- **Bare Metal**: 20,000 messages/sec

## ⚠️ Important Notes

- **Memory Management**: All configurations include memory leak detection
- **Error Handling**: Comprehensive fallback mechanisms ensure message delivery
- **Reliability**: Zero memory leaks detected in all tests
- **Compatibility**: All configurations work with both sync and async logging

## 🚀 Getting Started

```python
from hydra_logger import HydraLogger

# For API services
logger = HydraLogger.for_api_service()
logger.info("DEFAULT", "API request processed")

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