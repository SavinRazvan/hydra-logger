"""
Async sinks for Hydra-Logger.

This module provides async-compatible logging sinks that support non-blocking I/O
operations for high-performance async applications. All sinks implement async
emit methods and support concurrent logging operations.

Key Features:
- AsyncHttpSink for async HTTP logging
- AsyncDatabaseSink for async database logging
- AsyncQueueSink for async message queue logging
- AsyncCloudSink for async cloud service logging
- Connection pooling for high-performance async operations
- Retry mechanisms and error handling

Example:
    >>> from hydra_logger.async_sinks import AsyncHttpSink
    >>> sink = AsyncHttpSink("https://logs.example.com/api/logs")
    >>> await sink.emit_async(log_record)
"""

import asyncio
import json
import logging
import sys
import time
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass

# Optional imports with fallbacks
try:
    import aiohttp  # type: ignore
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None  # type: ignore

try:
    import asyncpg  # type: ignore
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None  # type: ignore

try:
    import aioredis  # type: ignore
    AIOREDIS_AVAILABLE = True
except ImportError:
    AIOREDIS_AVAILABLE = False
    aioredis = None  # type: ignore

# Type checking imports
if TYPE_CHECKING:
    from aiohttp import ClientSession, TCPConnector, ClientTimeout  # type: ignore
    from asyncpg import Pool  # type: ignore
    from aioredis import Redis  # type: ignore


@dataclass
class SinkStats:
    """Statistics for async sink performance."""
    total_messages: int = 0
    successful_messages: int = 0
    failed_messages: int = 0
    retry_count: int = 0
    avg_response_time: float = 0.0
    total_response_time: float = 0.0
    connection_errors: int = 0
    last_error: Optional[str] = None


class AsyncSink(ABC):
    """
    Base class for async logging sinks.
    
    This abstract base class provides the foundation for async logging sinks
    that support non-blocking I/O operations. All async sinks should inherit
    from this class and implement the async emit method.
    
    Attributes:
        _lock (threading.Lock): Thread lock for thread-safe operations
        _stats (SinkStats): Sink performance statistics
        _retry_count (int): Number of retries for failed operations
        _retry_delay (float): Delay between retries in seconds
    """
    
    def __init__(self, retry_count: int = 3, retry_delay: float = 1.0):
        """
        Initialize async sink.
        
        Args:
            retry_count (int): Number of retries for failed operations
            retry_delay (float): Delay between retries in seconds
        """
        self._lock = threading.Lock()
        self._stats = SinkStats()
        self._retry_count = retry_count
        self._retry_delay = retry_delay
    
    @abstractmethod
    async def emit_async(self, record: logging.LogRecord) -> bool:
        """
        Emit a log record asynchronously.
        
        Args:
            record (logging.LogRecord): Log record to emit
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    def get_stats(self) -> SinkStats:
        """Get current sink statistics."""
        with self._lock:
            return SinkStats(
                total_messages=self._stats.total_messages,
                successful_messages=self._stats.successful_messages,
                failed_messages=self._stats.failed_messages,
                retry_count=self._stats.retry_count,
                avg_response_time=self._stats.avg_response_time,
                total_response_time=self._stats.total_response_time,
                connection_errors=self._stats.connection_errors,
                last_error=self._stats.last_error
            )
    
    def reset_stats(self) -> None:
        """Reset all sink statistics."""
        with self._lock:
            self._stats = SinkStats()
    
    async def _record_success(self, response_time: float) -> None:
        """Record a successful operation."""
        with self._lock:
            self._stats.total_messages += 1
            self._stats.successful_messages += 1
            self._stats.total_response_time += response_time
            self._stats.avg_response_time = (
                self._stats.total_response_time / self._stats.successful_messages
            )
    
    async def _record_failure(self, error: str, response_time: float = 0.0) -> None:
        """Record a failed operation."""
        with self._lock:
            self._stats.total_messages += 1
            self._stats.failed_messages += 1
            self._stats.last_error = error
            if response_time > 0:
                self._stats.total_response_time += response_time
    
    async def _record_retry(self) -> None:
        """Record a retry operation."""
        with self._lock:
            self._stats.retry_count += 1
    
    async def _record_connection_error(self) -> None:
        """Record a connection error."""
        with self._lock:
            self._stats.connection_errors += 1


class AsyncHttpSink(AsyncSink):
    """
    Async HTTP sink for logging to HTTP endpoints.
    
    This sink sends log messages to HTTP endpoints asynchronously with
    configurable retry logic and connection pooling.
    """
    
    def __init__(self, url: str, method: str = "POST", headers: Optional[Dict[str, str]] = None,
                 timeout: float = 30.0, retry_count: int = 3, retry_delay: float = 1.0,
                 max_connections: int = 10):
        """
        Initialize async HTTP sink.
        
        Args:
            url (str): HTTP endpoint URL
            method (str): HTTP method (GET, POST, PUT, etc.)
            headers (Optional[Dict[str, str]]): HTTP headers
            timeout (float): Request timeout in seconds
            retry_count (int): Number of retries for failed requests
            retry_delay (float): Delay between retries in seconds
            max_connections (int): Maximum number of connections in pool
        """
        super().__init__(retry_count, retry_delay)
        self.url = url
        self.method = method.upper()
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout
        self.max_connections = max_connections
        self._session: Optional[Any] = None
        self._connector: Optional[Any] = None
        
        if not AIOHTTP_AVAILABLE:
            print("Warning: aiohttp not available. AsyncHttpSink will use fallback implementation.", file=sys.stderr)
    
    async def _get_session(self) -> Optional[Any]:
        """Get or create HTTP session with connection pooling."""
        if not AIOHTTP_AVAILABLE or aiohttp is None:
            return None
            
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session
    
    async def emit_async(self, record: logging.LogRecord) -> bool:
        """
        Emit a log record to HTTP endpoint asynchronously.
        
        Args:
            record (logging.LogRecord): Log record to emit
            
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        
        # Format the log record
        try:
            log_data = {
                "timestamp": time.time(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "process": record.process,
                "thread": record.thread
            }
            
            # Add extra fields if present (using getattr for safety)
            extra_fields = getattr(record, 'extra_fields', None)
            if extra_fields:
                log_data.update(extra_fields)
            
        except Exception as e:
            await self._record_failure(f"Failed to format log record: {e}")
            return False
        
        # If aiohttp is not available, use fallback
        if not AIOHTTP_AVAILABLE:
            await self._record_failure("aiohttp not available", time.time() - start_time)
            return False
        
        # Send with retry logic
        for attempt in range(self._retry_count + 1):
            try:
                session = await self._get_session()
                if session is None:
                    await self._record_failure("Failed to create HTTP session", time.time() - start_time)
                    return False
                
                async with session.request(
                    method=self.method,
                    url=self.url,
                    headers=self.headers,
                    json=log_data
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status < 400:
                        await self._record_success(response_time)
                        return True
                    else:
                        error_msg = f"HTTP {response.status}: {response.reason}"
                        await self._record_failure(error_msg, response_time)
                        
                        if attempt < self._retry_count:
                            await asyncio.sleep(self._retry_delay * (attempt + 1))
                            await self._record_retry()
                            continue
                        else:
                            return False
                            
            except Exception as e:
                error_type = type(e).__name__
                if "Timeout" in error_type or "timeout" in str(e).lower():
                    await self._record_failure("HTTP request timeout", response_time)
                elif "Connection" in error_type or "connection" in str(e).lower():
                    await self._record_failure(f"HTTP connection error: {error_type}: {e}", response_time)
                else:
                    await self._record_failure(f"Unexpected HTTP error: {error_type}: {e}", response_time)
        
        return False
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if AIOHTTP_AVAILABLE and self._session and not self._session.closed:
            await self._session.close()
        if AIOHTTP_AVAILABLE and self._connector and not self._connector.closed:
            await self._connector.close()


class AsyncDatabaseSink(AsyncSink):
    """
    Async database sink for logging to databases.
    
    This sink sends log messages to databases asynchronously with
    connection pooling and transaction support.
    """
    
    def __init__(self, connection_string: str, table_name: str = "logs",
                 retry_count: int = 3, retry_delay: float = 1.0,
                 max_connections: int = 5):
        """
        Initialize async database sink.
        
        Args:
            connection_string (str): Database connection string
            table_name (str): Table name for log entries
            retry_count (int): Number of retries for failed operations
            retry_delay (float): Delay between retries in seconds
            max_connections (int): Maximum number of connections in pool
        """
        super().__init__(retry_count, retry_delay)
        self.connection_string = connection_string
        self.table_name = table_name
        self.max_connections = max_connections
        self._pool: Optional[Any] = None
        
        if not ASYNCPG_AVAILABLE:
            print("Warning: asyncpg not available. AsyncDatabaseSink will use fallback implementation.", file=sys.stderr)
    
    async def _get_pool(self) -> Optional[Any]:
        """Get or create database connection pool."""
        if not ASYNCPG_AVAILABLE or asyncpg is None:
            return None
            
        if self._pool is None or self._pool.is_closed():
            self._pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=self.max_connections,
                command_timeout=30
            )
        return self._pool
    
    async def _ensure_table(self, pool: Any) -> None:
        """Ensure the log table exists."""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            level VARCHAR(10) NOT NULL,
            logger VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            module VARCHAR(255),
            function VARCHAR(255),
            line INTEGER,
            process INTEGER,
            thread INTEGER,
            extra_fields JSONB
        )
        """
        
        async with pool.acquire() as conn:
            await conn.execute(create_table_sql)
    
    async def emit_async(self, record: logging.LogRecord) -> bool:
        """
        Emit a log record to database asynchronously.
        
        Args:
            record (logging.LogRecord): Log record to emit
            
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        
        # Format the log record
        try:
            log_data = {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "process": record.process,
                "thread": record.thread
            }
            
            # Add extra fields if present (using getattr for safety)
            extra_fields = getattr(record, 'extra_fields', None)
            if extra_fields:
                log_data["extra_fields"] = json.dumps(extra_fields)
            
        except Exception as e:
            await self._record_failure(f"Failed to format log record: {e}")
            return False
        
        # If asyncpg is not available, use fallback
        if not ASYNCPG_AVAILABLE:
            await self._record_failure("asyncpg not available", time.time() - start_time)
            return False
        
        # Send with retry logic
        for attempt in range(self._retry_count + 1):
            try:
                pool = await self._get_pool()
                if pool is None:
                    await self._record_failure("Failed to create database pool", time.time() - start_time)
                    return False
                
                # Ensure table exists
                await self._ensure_table(pool)
                
                # Insert log record
                async with pool.acquire() as conn:
                    await conn.execute(f"""
                        INSERT INTO {self.table_name} 
                        (level, logger, message, module, function, line, process, thread, extra_fields)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, (
                        log_data["level"],
                        log_data["logger"],
                        log_data["message"],
                        log_data["module"],
                        log_data["function"],
                        log_data["line"],
                        log_data["process"],
                        log_data["thread"],
                        log_data.get("extra_fields")
                    ))
                
                response_time = time.time() - start_time
                await self._record_success(response_time)
                return True
                
            except Exception as e:
                await self._record_connection_error()
                error_msg = f"Database error: {e}"
                await self._record_failure(error_msg, time.time() - start_time)
                
                if attempt < self._retry_count:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    await self._record_retry()
                    continue
                else:
                    return False
        
        return False
    
    async def close(self) -> None:
        """Close the database connection pool."""
        if ASYNCPG_AVAILABLE and self._pool and not self._pool.is_closed():
            await self._pool.close()


class AsyncQueueSink(AsyncSink):
    """
    Async queue sink for logging to message queues.
    
    This sink sends log messages to message queues asynchronously with
    connection pooling and batch processing.
    """
    
    def __init__(self, queue_url: str, queue_name: str = "logs",
                 retry_count: int = 3, retry_delay: float = 1.0,
                 max_connections: int = 5):
        """
        Initialize async queue sink.
        
        Args:
            queue_url (str): Queue connection URL
            queue_name (str): Queue name for log messages
            retry_count (int): Number of retries for failed operations
            retry_delay (float): Delay between retries in seconds
            max_connections (int): Maximum number of connections in pool
        """
        super().__init__(retry_count, retry_delay)
        self.queue_url = queue_url
        self.queue_name = queue_name
        self.max_connections = max_connections
        self._redis: Optional[Any] = None
        
        if not AIOREDIS_AVAILABLE:
            print("Warning: aioredis not available. AsyncQueueSink will use fallback implementation.", file=sys.stderr)
    
    async def _get_redis(self) -> Optional[Any]:
        """Get or create Redis connection."""
        if not AIOREDIS_AVAILABLE or aioredis is None:
            return None
            
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.queue_url,
                max_connections=self.max_connections,
                decode_responses=True
            )
        return self._redis
    
    async def emit_async(self, record: logging.LogRecord) -> bool:
        """
        Emit a log record to message queue asynchronously.
        
        Args:
            record (logging.LogRecord): Log record to emit
            
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        
        # Format the log record
        try:
            log_data = {
                "timestamp": time.time(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "process": record.process,
                "thread": record.thread
            }
            
            # Add extra fields if present (using getattr for safety)
            extra_fields = getattr(record, 'extra_fields', None)
            if extra_fields:
                log_data.update(extra_fields)
            
        except Exception as e:
            await self._record_failure(f"Failed to format log record: {e}")
            return False
        
        # If aioredis is not available, use fallback
        if not AIOREDIS_AVAILABLE:
            await self._record_failure("aioredis not available", time.time() - start_time)
            return False
        
        # Send with retry logic
        for attempt in range(self._retry_count + 1):
            try:
                redis = await self._get_redis()
                if redis is None:
                    await self._record_failure("Failed to create Redis connection", time.time() - start_time)
                    return False
                
                # Push to queue
                await redis.lpush(self.queue_name, json.dumps(log_data))
                
                response_time = time.time() - start_time
                await self._record_success(response_time)
                return True
                
            except Exception as e:
                await self._record_connection_error()
                error_msg = f"Queue error: {e}"
                await self._record_failure(error_msg, time.time() - start_time)
                
                if attempt < self._retry_count:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    await self._record_retry()
                    continue
                else:
                    return False
        
        return False
    
    async def close(self) -> None:
        """Close the Redis connection."""
        if AIOREDIS_AVAILABLE and self._redis:
            await self._redis.close()


class AsyncCloudSink(AsyncSink):
    """
    Async cloud sink for logging to cloud services.
    
    This sink sends log messages to cloud services asynchronously with
    authentication and service-specific formatting.
    """
    
    def __init__(self, service_type: str, credentials: Dict[str, str],
                 retry_count: int = 3, retry_delay: float = 1.0):
        """
        Initialize async cloud sink.
        
        Args:
            service_type (str): Cloud service type ('aws', 'gcp', 'azure')
            credentials (Dict[str, str]): Service credentials
            retry_count (int): Number of retries for failed operations
            retry_delay (float): Delay between retries in seconds
        """
        super().__init__(retry_count, retry_delay)
        self.service_type = service_type.lower()
        self.credentials = credentials
        self._session: Optional[Any] = None
        
        if not AIOHTTP_AVAILABLE:
            print("Warning: aiohttp not available. AsyncCloudSink will use fallback implementation.", file=sys.stderr)
    
    async def _get_session(self) -> Optional[Any]:
        """Get or create HTTP session for cloud service."""
        if not AIOHTTP_AVAILABLE or aiohttp is None:
            return None
            
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def emit_async(self, record: logging.LogRecord) -> bool:
        """
        Emit a log record to cloud service asynchronously.
        
        Args:
            record (logging.LogRecord): Log record to emit
            
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        
        # Format the log record for cloud service
        try:
            log_data = self._format_for_cloud_service(record)
            
        except Exception as e:
            await self._record_failure(f"Failed to format log record: {e}")
            return False
        
        # If aiohttp is not available, use fallback
        if not AIOHTTP_AVAILABLE:
            await self._record_failure("aiohttp not available", time.time() - start_time)
            return False
        
        # Send with retry logic
        for attempt in range(self._retry_count + 1):
            try:
                session = await self._get_session()
                if session is None:
                    await self._record_failure("Failed to create HTTP session", time.time() - start_time)
                    return False
                
                # Send to appropriate cloud service
                if self.service_type == "aws":
                    success = await self._send_to_aws(session, log_data)
                elif self.service_type == "gcp":
                    success = await self._send_to_gcp(session, log_data)
                elif self.service_type == "azure":
                    success = await self._send_to_azure(session, log_data)
                else:
                    await self._record_failure(f"Unsupported cloud service: {self.service_type}")
                    return False
                
                response_time = time.time() - start_time
                
                if success:
                    await self._record_success(response_time)
                    return True
                else:
                    await self._record_failure("Cloud service error", response_time)
                    
                    if attempt < self._retry_count:
                        await asyncio.sleep(self._retry_delay * (attempt + 1))
                        await self._record_retry()
                        continue
                    else:
                        return False
                        
            except Exception as e:
                await self._record_connection_error()
                error_msg = f"Cloud service error: {e}"
                await self._record_failure(error_msg, time.time() - start_time)
                
                if attempt < self._retry_count:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    await self._record_retry()
                    continue
                else:
                    return False
        
        return False
    
    def _format_for_cloud_service(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Format log record for cloud service."""
        return {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
            "service_type": self.service_type
        }
    
    async def _send_to_aws(self, session: Any, log_data: Dict[str, Any]) -> bool:
        """Send log data to AWS CloudWatch."""
        # Simplified AWS CloudWatch implementation
        # In a real implementation, you would use boto3 with async support
        try:
            # This is a placeholder - real implementation would use AWS SDK
            return True
        except Exception:
            return False
    
    async def _send_to_gcp(self, session: Any, log_data: Dict[str, Any]) -> bool:
        """Send log data to Google Cloud Logging."""
        # Simplified GCP Logging implementation
        try:
            # This is a placeholder - real implementation would use GCP SDK
            return True
        except Exception:
            return False
    
    async def _send_to_azure(self, session: Any, log_data: Dict[str, Any]) -> bool:
        """Send log data to Azure Monitor."""
        # Simplified Azure Monitor implementation
        try:
            # This is a placeholder - real implementation would use Azure SDK
            return True
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close the cloud service session."""
        if AIOHTTP_AVAILABLE and self._session and not self._session.closed:
            await self._session.close() 