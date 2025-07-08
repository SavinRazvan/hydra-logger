# 17 - Database Logging

## 🎯 Overview

This example demonstrates how to use Hydra-Logger for database-specific logging scenarios. It shows:
- Database operation logging
- Query performance monitoring
- Transaction logging
- Error tracking for database operations
- Best practices for database logging

## 🚀 Running the Example

```bash
python main.py
```

## 📊 Expected Output

```
🗄️ Database Logging Demo
========================================
✅ Database logging demo complete! Check logs/database_logging/db_operations.log.
```

### Generated Log File
Check `logs/database_logging/db_operations.log` for database operation logs.

## 🔑 Key Concepts

### **Database Logging Benefits**
- Track database performance
- Monitor query execution times
- Debug database issues
- Audit database operations
- Optimize database usage

### **Database-Specific Considerations**
- **Query Performance**: Log slow queries and execution times
- **Transaction Tracking**: Monitor transaction boundaries
- **Error Handling**: Capture database errors with context
- **Connection Management**: Log connection events
- **Data Sensitivity**: Avoid logging sensitive data

### **Common Database Operations to Log**
- **SELECT**: Read operations
- **INSERT**: Create operations
- **UPDATE**: Modify operations
- **DELETE**: Remove operations
- **TRANSACTION**: Multi-step operations
- **CONNECTION**: Connection events

## 🎨 Code Example

```python
import time
import random
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def simulate_database_operation(logger, operation_type, table_name, duration_ms):
    """Simulate a database operation with logging."""
    
    # Log operation start
    start_time = time.time()
    logger.info("DB_OPERATION", f"Starting {operation_type} operation",
               operation=operation_type,
               table=table_name,
               start_time=start_time)
    
    # Simulate database work
    time.sleep(duration_ms / 1000)
    
    # Log operation completion
    end_time = time.time()
    duration = (end_time - start_time) * 1000
    
    logger.info("DB_OPERATION", f"Completed {operation_type} operation",
               operation=operation_type,
               table=table_name,
               duration_ms=duration,
               end_time=end_time)

def main():
    # Configure logger for database operations
    config = LoggingConfig(layers={
        "DB_OPERATION": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/database_logging/db_operations.log",
                    format="json"
                )
            ]
        )
    })
    
    logger = HydraLogger(config)
    
    # Simulate various database operations
    operations = [
        ("SELECT", "users", 50),
        ("INSERT", "orders", 120),
        ("UPDATE", "products", 80),
        ("DELETE", "temp_data", 30)
    ]
    
    for op_type, table, duration in operations:
        simulate_database_operation(logger, op_type, table, duration)
```

## 🧪 Database Logging Patterns

### **Query Performance Logging**
```python
import time
import functools

def log_query_performance(logger):
    """Decorator to log query performance."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                logger.info("QUERY", "Database query completed",
                           query_name=func.__name__,
                           duration_ms=duration,
                           success=True)
                
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error("QUERY", "Database query failed",
                           query_name=func.__name__,
                           duration_ms=duration,
                           error=str(e),
                           success=False)
                raise
        
        return wrapper
    return decorator

# Usage
@log_query_performance(logger)
def get_user_by_id(user_id):
    # Simulate database query
    time.sleep(0.1)
    return {"id": user_id, "name": "John Doe"}
```

### **Transaction Logging**
```python
class TransactionLogger:
    def __init__(self, logger):
        self.logger = logger
        self.transaction_id = None
    
    def begin_transaction(self, transaction_name):
        """Log transaction start."""
        self.transaction_id = f"txn_{int(time.time() * 1000)}"
        
        self.logger.info("TRANSACTION", "Transaction started",
                        transaction_id=self.transaction_id,
                        transaction_name=transaction_name,
                        start_time=time.time())
    
    def commit_transaction(self):
        """Log transaction commit."""
        if self.transaction_id:
            self.logger.info("TRANSACTION", "Transaction committed",
                           transaction_id=self.transaction_id,
                           end_time=time.time())
            self.transaction_id = None
    
    def rollback_transaction(self, reason):
        """Log transaction rollback."""
        if self.transaction_id:
            self.logger.warning("TRANSACTION", "Transaction rolled back",
                              transaction_id=self.transaction_id,
                              reason=reason,
                              end_time=time.time())
            self.transaction_id = None

# Usage
txn_logger = TransactionLogger(logger)
txn_logger.begin_transaction("user_registration")
# ... perform operations ...
txn_logger.commit_transaction()
```

### **Connection Pool Logging**
```python
class ConnectionPoolLogger:
    def __init__(self, logger):
        self.logger = logger
        self.active_connections = 0
        self.max_connections = 10
    
    def get_connection(self):
        """Log connection acquisition."""
        if self.active_connections >= self.max_connections:
            self.logger.warning("CONNECTION", "Connection pool exhausted",
                              active_connections=self.active_connections,
                              max_connections=self.max_connections)
            return None
        
        self.active_connections += 1
        connection_id = f"conn_{int(time.time() * 1000)}"
        
        self.logger.info("CONNECTION", "Connection acquired",
                        connection_id=connection_id,
                        active_connections=self.active_connections)
        
        return connection_id
    
    def release_connection(self, connection_id):
        """Log connection release."""
        self.active_connections -= 1
        
        self.logger.info("CONNECTION", "Connection released",
                        connection_id=connection_id,
                        active_connections=self.active_connections)

# Usage
pool_logger = ConnectionPoolLogger(logger)
conn_id = pool_logger.get_connection()
# ... use connection ...
pool_logger.release_connection(conn_id)
```

## 📚 Use Cases

### **ORM Integration**
```python
class ORMLogger:
    def __init__(self, logger):
        self.logger = logger
    
    def log_model_operation(self, model_name, operation, **kwargs):
        """Log ORM model operations."""
        self.logger.info("ORM", f"{operation} operation on {model_name}",
                        model=model_name,
                        operation=operation,
                        **kwargs)
    
    def log_query(self, sql, params=None, duration_ms=None):
        """Log SQL queries."""
        self.logger.debug("SQL", "SQL query executed",
                         sql=sql,
                         params=params,
                         duration_ms=duration_ms)

# Usage
orm_logger = ORMLogger(logger)
orm_logger.log_model_operation("User", "create", user_id=123)
orm_logger.log_query("SELECT * FROM users WHERE id = %s", [123], 50)
```

### **Database Migration Logging**
```python
def log_migration(logger, migration_name, version):
    """Log database migration operations."""
    logger.info("MIGRATION", f"Starting migration: {migration_name}",
               migration_name=migration_name,
               version=version,
               start_time=time.time())
    
    try:
        # Simulate migration
        time.sleep(0.5)
        
        logger.info("MIGRATION", f"Migration completed: {migration_name}",
                   migration_name=migration_name,
                   version=version,
                   end_time=time.time(),
                   success=True)
        
    except Exception as e:
        logger.error("MIGRATION", f"Migration failed: {migration_name}",
                    migration_name=migration_name,
                    version=version,
                    error=str(e),
                    success=False)
        raise

# Usage
log_migration(logger, "Add user table", "001")
```

### **Database Health Monitoring**
```python
class DatabaseHealthMonitor:
    def __init__(self, logger):
        self.logger = logger
        self.last_check = 0
    
    def check_health(self):
        """Monitor database health metrics."""
        current_time = time.time()
        
        # Simulate health check
        is_healthy = random.choice([True, True, True, False])  # 75% healthy
        response_time = random.uniform(10, 100)  # 10-100ms
        
        self.logger.info("HEALTH", "Database health check",
                        is_healthy=is_healthy,
                        response_time_ms=response_time,
                        check_time=current_time)
        
        if not is_healthy:
            self.logger.warning("HEALTH", "Database health issue detected",
                              response_time_ms=response_time)
        
        self.last_check = current_time

# Usage
health_monitor = DatabaseHealthMonitor(logger)
health_monitor.check_health()
```

## ⚡ Performance Strategies

### **1. Batch Database Logging**
```python
class BatchDatabaseLogger:
    def __init__(self, logger, batch_size=100):
        self.logger = logger
        self.batch_size = batch_size
        self.batch = []
    
    def log_operation(self, operation, **kwargs):
        """Add operation to batch."""
        self.batch.append({
            "operation": operation,
            "timestamp": time.time(),
            **kwargs
        })
        
        if len(self.batch) >= self.batch_size:
            self.flush()
    
    def flush(self):
        """Flush batch to database."""
        if self.batch:
            self.logger.info("BATCH", f"Batch of {len(self.batch)} operations",
                           operations=self.batch)
            self.batch = []

# Usage
batch_logger = BatchDatabaseLogger(logger)
for i in range(1000):
    batch_logger.log_operation("SELECT", table="users", user_id=i)
batch_logger.flush()
```

### **2. Slow Query Detection**
```python
class SlowQueryDetector:
    def __init__(self, logger, threshold_ms=1000):
        self.logger = logger
        self.threshold_ms = threshold_ms
    
    def log_query(self, query_name, duration_ms, **kwargs):
        """Log query with slow query detection."""
        self.logger.info("QUERY", f"Query executed: {query_name}",
                        query_name=query_name,
                        duration_ms=duration_ms,
                        **kwargs)
        
        if duration_ms > self.threshold_ms:
            self.logger.warning("SLOW_QUERY", f"Slow query detected: {query_name}",
                              query_name=query_name,
                              duration_ms=duration_ms,
                              threshold_ms=self.threshold_ms,
                              **kwargs)

# Usage
slow_detector = SlowQueryDetector(logger, threshold_ms=500)
slow_detector.log_query("complex_join", 750, table="orders")
```

### **3. Connection Monitoring**
```python
class ConnectionMonitor:
    def __init__(self, logger):
        self.logger = logger
        self.connection_count = 0
        self.max_connections = 20
    
    def log_connection_event(self, event_type, **kwargs):
        """Log connection events."""
        if event_type == "acquired":
            self.connection_count += 1
        elif event_type == "released":
            self.connection_count -= 1
        
        self.logger.info("CONNECTION", f"Connection {event_type}",
                        event_type=event_type,
                        active_connections=self.connection_count,
                        max_connections=self.max_connections,
                        **kwargs)
        
        # Alert if approaching limit
        if self.connection_count > self.max_connections * 0.8:
            self.logger.warning("CONNECTION", "Connection pool approaching limit",
                              active_connections=self.connection_count,
                              max_connections=self.max_connections)

# Usage
conn_monitor = ConnectionMonitor(logger)
conn_monitor.log_connection_event("acquired", connection_id="conn_123")
conn_monitor.log_connection_event("released", connection_id="conn_123")
```

## 🔍 Error Handling

### **Database Error Logging**
```python
def log_database_error(logger, error, context=None):
    """Log database errors with context."""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": time.time()
    }
    
    if context:
        error_data.update(context)
    
    logger.error("DB_ERROR", "Database error occurred",
                **error_data)

# Usage
try:
    # Database operation
    pass
except Exception as e:
    log_database_error(logger, e, {
        "operation": "user_insert",
        "user_id": 123,
        "table": "users"
    })
```

### **Retry Logic Logging**
```python
class RetryLogger:
    def __init__(self, logger, max_retries=3):
        self.logger = logger
        self.max_retries = max_retries
    
    def log_retry_attempt(self, operation, attempt, error=None):
        """Log retry attempts."""
        self.logger.warning("RETRY", f"Retry attempt {attempt} for {operation}",
                           operation=operation,
                           attempt=attempt,
                           max_retries=self.max_retries,
                           error=str(error) if error else None)
    
    def log_retry_success(self, operation, attempts):
        """Log successful retry."""
        self.logger.info("RETRY", f"Operation {operation} succeeded after {attempts} attempts",
                        operation=operation,
                        attempts=attempts)
    
    def log_retry_failure(self, operation, attempts, final_error):
        """Log retry failure."""
        self.logger.error("RETRY", f"Operation {operation} failed after {attempts} attempts",
                         operation=operation,
                         attempts=attempts,
                         final_error=str(final_error))

# Usage
retry_logger = RetryLogger(logger)
retry_logger.log_retry_attempt("database_query", 1, "Connection timeout")
retry_logger.log_retry_success("database_query", 2)
```

## 📚 Best Practices

### **1. Avoid Logging Sensitive Data**
```python
def secure_database_logging():
    logger = HydraLogger()
    
    # Good: Log operation without sensitive data
    logger.info("DB", "User authentication",
               user_id=123,
               operation="login",
               success=True)
    
    # Avoid: Logging sensitive information
    # logger.info("DB", "User login", password="secret123")  # BAD!
```

### **2. Use Structured Logging**
```python
def structured_database_logging():
    logger = HydraLogger()
    
    # Structured logging with context
    logger.info("DB", "Database operation",
               operation="INSERT",
               table="users",
               duration_ms=150,
               rows_affected=1,
               user_id=123,
               timestamp=time.time())
```

### **3. Monitor Performance Impact**
```python
def performance_monitored_logging():
    logger = HydraLogger()
    
    start_time = time.time()
    
    # Database operation
    time.sleep(0.1)  # Simulate work
    
    logging_time = (time.time() - start_time) * 1000
    
    # Only log if it doesn't impact performance significantly
    if logging_time < 10:  # Less than 10ms
        logger.info("DB", "Operation completed",
                   duration_ms=logging_time)
```

## 📚 Next Steps

After understanding this example, try:
- **16_cloud_integration** - Cloud platform integration
- **18_queue_based** - Queue-based logging patterns
- **19_monitoring_integration** - Monitoring system integration 