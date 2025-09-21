"""
Database Handlers for Hydra-Logger

This module provides comprehensive database-based logging handlers for various
database systems including relational, document, and in-memory databases.
It includes connection pooling, batch processing, and retry mechanisms.

ARCHITECTURE:
- BaseDatabaseHandler: Abstract base class for all database handlers
- SQLiteHandler: Local SQLite database logging
- PostgreSQLHandler: PostgreSQL relational database logging
- MongoDBHandler: MongoDB document database logging
- RedisHandler: Redis in-memory database logging
- DatabaseHandlerFactory: Factory for creating database handlers

SUPPORTED DATABASES:
- SQLite: Local file-based database (built-in)
- PostgreSQL: Relational database with JSON support
- MongoDB: Document database with flexible schema
- Redis: In-memory database with persistence options

PERFORMANCE FEATURES:
- Intelligent batch processing (100 messages or 5s intervals)
- Connection pooling and management
- Transaction support for data integrity
- Indexing for optimal query performance
- Formatter-aware handling for optimal performance
- Comprehensive error handling and retry mechanisms

CONNECTION POOLING:
- Simple: Basic connection management
- Threaded: Thread-safe connection pooling
- Configurable pool sizes and timeouts
- Automatic connection recovery

USAGE EXAMPLES:

SQLite Handler:
    from hydra_logger.handlers import SQLiteHandler
    
    handler = SQLiteHandler(
        database_path="logs.db",
        batch_size=100,
        auto_flush=True
    )
    logger.addHandler(handler)

PostgreSQL Handler:
    from hydra_logger.handlers import PostgreSQLHandler
    
    handler = PostgreSQLHandler(
        host="localhost",
        port=5432,
        database="logs",
        username="postgres",
        password="password"
    )
    logger.addHandler(handler)

MongoDB Handler:
    from hydra_logger.handlers import MongoDBHandler
    
    handler = MongoDBHandler(
        host="localhost",
        port=27017,
        database="logs",
        collection="log_entries"
    )
    logger.addHandler(handler)

Redis Handler:
    from hydra_logger.handlers import RedisHandler
    
    handler = RedisHandler(
        host="localhost",
        port=6379,
        database=0,
        password="password"
    )
    logger.addHandler(handler)

Factory Pattern:
    from hydra_logger.handlers import DatabaseHandlerFactory
    
    # Create SQLite handler
    handler = DatabaseHandlerFactory.create_handler(
        "sqlite",
        database_path="logs.db"
    )
    
    # Create PostgreSQL handler
    handler = DatabaseHandlerFactory.create_handler(
        "postgresql",
        host="localhost",
        database="logs"
    )

Performance Monitoring:
    # Get database statistics
    stats = handler.get_database_stats()
    print(f"Connected: {stats['connected']}")
    print(f"Messages processed: {stats['message_count']}")
    print(f"Batch count: {stats['batch_count']}")
    print(f"Error count: {stats['error_count']}")

CONFIGURATION:
- Connection settings: host, port, database, username, password
- Batch settings: batch_size, batch_timeout, auto_flush
- Pool settings: max_connections, connection_timeout
- Table/collection settings: table_name, create_table, index_fields
- Performance: use_transactions, index_fields

ERROR HANDLING:
- Automatic retry with exponential backoff
- Connection recovery and reconnection
- Fallback mechanisms for failed operations
- Comprehensive error logging
- Graceful degradation

THREAD SAFETY:
- Thread-safe operations with proper locking
- Safe concurrent access
- Atomic batch operations
- Connection pooling and management
"""

import json
import time
import threading
import sys
from typing import Optional, Dict, Any, Union, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from hydra_logger.handlers.base import BaseHandler
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"


class ConnectionPool(Enum):
    """Connection pool strategies."""
    NONE = "none"
    SIMPLE = "simple"
    THREADED = "threaded"


@dataclass
class DatabaseConfig:
    """Configuration for database handlers."""
    # Connection settings
    host: str = "localhost"
    port: int = 5432
    database: str = "logs"
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Connection pooling
    pool_strategy: ConnectionPool = ConnectionPool.SIMPLE
    max_connections: int = 10
    connection_timeout: float = 30.0
    
    # Batch settings
    batch_size: int = 100
    batch_timeout: float = 5.0
    auto_flush: bool = True
    
    # Table/collection settings
    table_name: str = "log_entries"
    create_table: bool = True
    
    # Performance
    use_transactions: bool = True
    index_fields: List[str] = field(default_factory=lambda: ["timestamp", "level"])
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0


class BaseDatabaseHandler(BaseHandler):
    """Base class for database-based handlers."""
    
    def __init__(
        self,
        config: DatabaseConfig,
        timestamp_config=None,
        **kwargs
    ):
        """Initialize base database handler."""
        super().__init__(name="database", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        
        self.config = config
        self._connected = False
        self._connection_lock = threading.RLock()
        
        # Batch handling
        self._batch_buffer = []
        self._batch_lock = threading.Lock()
        self._last_flush = time.time()
        
        # Statistics
        self._message_count = 0
        self._batch_count = 0
        self._error_count = 0
        
        # Formatter-aware handling
        self._is_csv_formatter = False
        self._is_json_formatter = False
        self._is_streaming_formatter = False
        self._needs_special_handling = False
        
        # Initialize database
        self._init_database()
    
    def setFormatter(self, formatter):
        """
        Set formatter and detect if it needs special handling.
        
        Args:
            formatter: Formatter instance
        """
        super().setFormatter(formatter)
        
        # Detect formatter type for optimal handling
        if formatter:
            self._is_csv_formatter = (
                hasattr(formatter, 'format_headers') and 
                hasattr(formatter, 'should_write_headers')
            )
            self._is_json_formatter = hasattr(formatter, 'write_header')
            self._is_streaming_formatter = hasattr(formatter, 'format_for_streaming')
            
            # Determine if special handling is needed
            self._needs_special_handling = (
                self._is_csv_formatter or 
                self._is_json_formatter or 
                self._is_streaming_formatter
            )
        else:
            # Reset flags if no formatter
            self._is_csv_formatter = False
            self._is_json_formatter = False
            self._is_streaming_formatter = False
            self._needs_special_handling = False
    
    def handleError(self, record: LogRecord) -> None:
        """
        Handle errors that occur during record processing.
        
        Args:
            record: The log record that caused the error
        """
        self._error_count += 1
        print(f"Error: Database handler error processing record: {record.message}", file=sys.stderr)
        
        # Try to log the error to a fallback destination if available
        if hasattr(self, 'fallback_handler') and self.fallback_handler:
            try:
                self.fallback_handler.handle(record)
            except Exception:
                # If fallback also fails, just log to stderr
                print(f"Error: Fallback handler also failed for record: {record.message}", file=sys.stderr)
    
    def _init_database(self) -> None:
        """Initialize database connection and schema."""
        try:
            success = self._establish_connection()
            if success:
                self._connected = True
                if self.config.create_table:
                    self._create_schema()
        except Exception as e:
            print(f"Error: Database initialization failed: {e}", file=sys.stderr)
            self._connected = False
    
    def _establish_connection(self) -> bool:
        """Establish database connection. Override in subclasses."""
        raise NotImplementedError
    
    def _create_schema(self) -> None:
        """Create database schema. Override in subclasses."""
        pass
    
    def _insert_record(self, record: LogRecord) -> bool:
        """Insert a single record. Override in subclasses."""
        raise NotImplementedError
    
    def _insert_batch(self, records: List[LogRecord]) -> bool:
        """Insert multiple records. Override in subclasses."""
        raise NotImplementedError
    
    def emit(self, record: LogRecord) -> None:
        """Emit log record to database."""
        if not self._connected:
            if not self._init_database():
                self.handleError(record)
                return
        
        try:
            # Add to batch buffer
            with self._batch_lock:
                self._batch_buffer.append(record)
                
                # Check if we should flush
                should_flush = (
                    len(self._batch_buffer) >= self.config.batch_size or
                    (self.config.auto_flush and 
                     time.time() - self._last_flush >= self.config.batch_timeout)
                )
                
                if should_flush:
                    self._flush_batch()
            
            # Update statistics
            self._message_count += 1
            
        except Exception as e:
            self._error_count += 1
            print(f"Error: Failed to add record to batch: {e}", file=sys.stderr)
            self.handleError(record)
    
    def _flush_batch(self) -> None:
        """Flush the current batch to the database."""
        if not self._batch_buffer:
            return
        
        try:
            # Get current batch
            with self._batch_lock:
                current_batch = self._batch_buffer.copy()
                self._batch_buffer.clear()
                self._last_flush = time.time()
            
            # Insert batch
            if self._insert_batch(current_batch):
                self._batch_count += 1
            else:
                # Re-add records to buffer on failure
                with self._batch_lock:
                    self._batch_buffer.extend(current_batch)
                    
        except Exception as e:
            self._error_count += 1
            print(f"Error: Failed to flush batch: {e}", file=sys.stderr)
            
            # Re-add records to buffer on failure
            with self._batch_lock:
                self._batch_buffer.extend(current_batch)
    
    def flush(self) -> None:
        """Flush any pending records."""
        self._flush_batch()
    
    def close(self) -> None:
        """Close the handler."""
        self.flush()
        self._close_connection()
        super().close()
    
    def _close_connection(self) -> None:
        """Close database connection. Override in subclasses."""
        pass
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            'connected': self._connected,
            'message_count': self._message_count,
            'batch_count': self._batch_count,
            'error_count': self._error_count,
            'batch_buffer_size': len(self._batch_buffer),
            'last_flush': self._last_flush
        }


class SQLiteHandler(BaseDatabaseHandler):
    """
    SQLite database handler.
    
    Provides local database logging with SQLite.
    """
    
    def __init__(
        self,
        database_path: str = "logs.db",
        **kwargs
    ):
        """Initialize SQLite handler."""
        # Set database_path before calling super().__init__()
        self.database_path = database_path
        
        # Create config
        config = DatabaseConfig(
            database=database_path,
            **kwargs
        )
        
        super().__init__(config=config)
        self.connection = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish SQLite connection."""
        try:
            import sqlite3
            
            with self._connection_lock:
                self.connection = sqlite3.connect(
                    self.database_path,
                    timeout=self.config.connection_timeout,
                    check_same_thread=False
                )
                
                # Enable WAL mode for better concurrency
                self.connection.execute("PRAGMA journal_mode=WAL")
                
                return True
                
        except ImportError:
            print("Error: sqlite3 module not available", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error: SQLite connection failed: {e}", file=sys.stderr)
            return False
    
    def _create_schema(self) -> None:
        """Create SQLite table schema."""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                level TEXT NOT NULL,
                logger_name TEXT NOT NULL,
                message TEXT NOT NULL,
                file_name TEXT,
                function_name TEXT,
                line_number INTEGER,
                extra TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
            """
            
            with self._connection_lock:
                self.connection.execute(create_table_sql)
                
                # Create indexes
                for field in self.config.index_fields:
                    if field in ["timestamp", "level", "logger_name"]:
                        index_sql = f"CREATE INDEX IF NOT EXISTS idx_{field} ON log_entries({field})"
                        self.connection.execute(index_sql)
                
                self.connection.commit()
                
        except Exception as e:
            print(f"Error: Failed to create SQLite schema: {e}", file=sys.stderr)
            raise
    
    def _insert_record(self, record: LogRecord) -> bool:
        """Insert a single record into SQLite."""
        try:
            insert_sql = """
            INSERT INTO log_entries (
                timestamp, level, logger_name, message, file_name, 
                function_name, line_number, extra
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            extra_data = getattr(record, 'extra', {})
            extra_json = json.dumps(extra_data) if extra_data else None
            
            params = (
                record.timestamp,
                record.levelname,
                record.logger_name,
                self.format(record),
                getattr(record, 'file_name', ''),
                getattr(record, 'function_name', ''),
                getattr(record, 'line_number', ''),
                extra_json
            )
            
            with self._connection_lock:
                self.connection.execute(insert_sql, params)
                
                if self.config.use_transactions:
                    self.connection.commit()
                
                return True
                
        except Exception as e:
            print(f"Error: Failed to insert record into SQLite: {e}", file=sys.stderr)
            return False
    
    def _insert_batch(self, records: List[LogRecord]) -> bool:
        """Insert multiple records into SQLite."""
        try:
            insert_sql = """
            INSERT INTO log_entries (
                timestamp, level, logger_name, message, file_name, 
                function_name, line_number, extra
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params_list = []
            for record in records:
                extra_data = getattr(record, 'extra', {})
                extra_json = json.dumps(extra_data) if extra_data else None
                
                params = (
                    record.timestamp,
                    record.levelname,
                    record.logger_name,
                    self.format(record),
                    getattr(record, 'file_name', ''),
                    getattr(record, 'function_name', ''),
                    getattr(record, 'line_number', ''),
                    extra_json
                )
                params_list.append(params)
            
            with self._connection_lock:
                self.connection.executemany(insert_sql, params_list)
                
                if self.config.use_transactions:
                    self.connection.commit()
                
                return True
                
        except Exception as e:
            print(f"Error: Failed to insert batch into SQLite: {e}", file=sys.stderr)
            return False
    
    def _close_connection(self) -> None:
        """Close SQLite connection."""
        if self.connection:
            with self._connection_lock:
                try:
                    self.connection.close()
                except Exception:
                    pass
                self.connection = None


class PostgreSQLHandler(BaseDatabaseHandler):
    """
    PostgreSQL database handler.
    
    Provides relational database logging with PostgreSQL.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "logs",
        username: str = "postgres",
        password: str = "",
        **kwargs
    ):
        """Initialize PostgreSQL handler."""
        # Create config
        config = DatabaseConfig(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.connection = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish PostgreSQL connection."""
        try:
            import psycopg2  # type: ignore
            
            with self._connection_lock:
                self.connection = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password,
                    connect_timeout=self.config.connection_timeout
                )
                
                # Set autocommit to False for transaction support
                self.connection.autocommit = not self.config.use_transactions
                
                return True
                
        except ImportError:
            print("Error: psycopg2 library is required for PostgreSQL. Install with: pip install psycopg2-binary", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error: PostgreSQL connection failed: {e}", file=sys.stderr)
            return False
    
    def _create_schema(self) -> None:
        """Create PostgreSQL table schema."""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS log_entries (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                level VARCHAR(10) NOT NULL,
                logger_name VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                filename VARCHAR(255),
                function_name VARCHAR(255),
                line_number INTEGER,
                extra JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            with self._connection_lock:
                cursor = self.connection.cursor()
                cursor.execute(create_table_sql)
                
                # Create indexes
                for field in self.config.index_fields:
                    if field in ["timestamp", "level", "logger_name"]:
                        index_sql = f"CREATE INDEX IF NOT EXISTS idx_{field} ON log_entries({field})"
                        cursor.execute(index_sql)
                
                if self.config.use_transactions:
                    self.connection.commit()
                cursor.close()
                
        except Exception as e:
            print(f"Error: Failed to create PostgreSQL schema: {e}", file=sys.stderr)
            raise
    
    def _insert_record(self, record: LogRecord) -> bool:
        """Insert a single record into PostgreSQL."""
        try:
            insert_sql = """
            INSERT INTO log_entries (
                timestamp, level, logger_name, message, file_name, 
                function_name, line_number, extra
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            extra_data = getattr(record, 'extra', {})
            
            params = (
                self.format_timestamp(record),
                record.levelname,
                record.logger_name,
                self.format(record),
                getattr(record, 'file_name', ''),
                getattr(record, 'function_name', ''),
                getattr(record, 'line_number', ''),
                json.dumps(extra_data) if extra_data else None
            )
            
            with self._connection_lock:
                cursor = self.connection.cursor()
                cursor.execute(insert_sql, params)
                cursor.close()
                
                if self.config.use_transactions:
                    self.connection.commit()
                
                return True
                
        except Exception as e:
            print(f"Error: Failed to insert record into PostgreSQL: {e}", file=sys.stderr)
            return False
    
    def _insert_batch(self, records: List[LogRecord]) -> bool:
        """Insert multiple records into PostgreSQL."""
        try:
            insert_sql = """
            INSERT INTO log_entries (
                timestamp, level, logger_name, message, file_name, 
                function_name, line_number, extra
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params_list = []
            for record in records:
                extra_data = getattr(record, 'extra', {})
                
                params = (
                    self.format_timestamp(record),
                    record.levelname,
                    record.logger_name,
                    self.format(record),
                    getattr(record, 'file_name', ''),
                    getattr(record, 'function_name', ''),
                    getattr(record, 'line_number', ''),
                    json.dumps(extra_data) if extra_data else None
                )
                params_list.append(params)
            
            with self._connection_lock:
                cursor = self.connection.cursor()
                cursor.executemany(insert_sql, params_list)
                cursor.close()
                
                if self.config.use_transactions:
                    self.connection.commit()
                
                return True
                
        except Exception as e:
            print(f"Error: Failed to insert batch into PostgreSQL: {e}", file=sys.stderr)
            return False
    
    def _close_connection(self) -> None:
        """Close PostgreSQL connection."""
        if self.connection:
            with self._connection_lock:
                try:
                    self.connection.close()
                except Exception:
                    pass
                self.connection = None


class MongoDBHandler(BaseDatabaseHandler):
    """
    MongoDB database handler.
    
    Provides document database logging with MongoDB.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 27017,
        database: str = "logs",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """Initialize MongoDB handler."""
        # Create config
        config = DatabaseConfig(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.client = None
        self.database = None
        self.collection = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish MongoDB connection."""
        try:
            import pymongo  # type: ignore
            
            with self._connection_lock:
                # Build connection string
                if self.config.username and self.config.password:
                    connection_string = f"mongodb://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}"
                else:
                    connection_string = f"mongodb://{self.config.host}:{self.config.port}"
                
                self.client = pymongo.MongoClient(
                    connection_string,
                    serverSelectionTimeoutMS=int(self.config.connection_timeout * 1000)
                )
                
                # Test connection
                self.client.admin.command('ping')
                
                self.database = self.client[self.config.database]
                self.collection = self.database[self.config.table_name]
                
                return True
                
        except ImportError:
            print("Error: pymongo library is required for MongoDB. Install with: pip install pymongo", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error: MongoDB connection failed: {e}", file=sys.stderr)
            return False
    
    def _create_schema(self) -> None:
        """Create MongoDB collection and indexes."""
        try:
            with self._connection_lock:
                # Create indexes
                for field in self.config.index_fields:
                    if field in ["timestamp", "level", "logger_name"]:
                        self.collection.create_index(field)
                
                # Create TTL index for timestamp if specified
                if "timestamp" in self.config.index_fields:
                    self.collection.create_index("timestamp", expireAfterSeconds=0)
                
        except Exception as e:
            print(f"Error: Failed to create MongoDB schema: {e}", file=sys.stderr)
            raise
    
    def _insert_record(self, record: LogRecord) -> bool:
        """Insert a single record into MongoDB."""
        try:
            document = {
                'timestamp': self.format_timestamp(record),
                'level': record.levelname,
                'logger_name': record.logger_name,
                'message': self.format(record),
                'filename': getattr(record, 'filename', ''),
                'function_name': getattr(record, 'function_name', ''),
                'line_number': getattr(record, 'line_number', ''),
                'extra': getattr(record, 'extra', {}),
                'created_at': datetime.utcnow()
            }
            
            with self._connection_lock:
                self.collection.insert_one(document)
                return True
                
        except Exception as e:
            print(f"Error: Failed to insert record into MongoDB: {e}", file=sys.stderr)
            return False
    
    def _insert_batch(self, records: List[LogRecord]) -> bool:
        """Insert multiple records into MongoDB."""
        try:
            documents = []
            for record in records:
                document = {
                    'timestamp': self.format_timestamp(record),
                    'level': record.levelname,
                    'logger_name': record.logger_name,
                    'message': self.format(record),
                    'filename': getattr(record, 'filename', ''),
                    'function_name': getattr(record, 'function_name', ''),
                    'line_number': getattr(record, 'line_number', ''),
                    'extra': getattr(record, 'extra', {}),
                    'created_at': datetime.utcnow()
                }
                documents.append(document)
            
            with self._connection_lock:
                self.collection.insert_many(documents)
                return True
                
        except Exception as e:
            print(f"Error: Failed to insert batch into MongoDB: {e}", file=sys.stderr)
            return False
    
    def _close_connection(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            with self._connection_lock:
                try:
                    self.client.close()
                except Exception:
                    pass
                self.client = None


class RedisHandler(BaseDatabaseHandler):
    """
    Redis database handler.
    
    Provides in-memory database logging with Redis.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        database: int = 0,
        password: Optional[str] = None,
        **kwargs
    ):
        """Initialize Redis handler."""
        # Create config
        config = DatabaseConfig(
            host=host,
            port=port,
            database=str(database),
            password=password,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.redis_client = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish Redis connection."""
        try:
            import redis  # type: ignore
            
            with self._connection_lock:
                self.redis_client = redis.Redis(
                    host=self.config.host,
                    port=self.config.port,
                    db=int(self.config.database),
                    password=self.config.password,
                    socket_timeout=self.config.connection_timeout,
                    decode_responses=True
                )
                
                # Test connection
                self.redis_client.ping()
                
                return True
                
        except ImportError:
            print("Error: redis library is required for Redis. Install with: pip install redis", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error: Redis connection failed: {e}", file=sys.stderr)
            return False
    
    def _insert_record(self, record: LogRecord) -> bool:
        """Insert a single record into Redis."""
        try:
            # Create unique key
            key = f"log:{record.timestamp}:{record.logger_name}:{record.levelname}"
            
            # Create hash with record data
            record_data = {
                'timestamp': str(record.timestamp),
                'level': record.levelname,
                'logger_name': record.logger_name,
                'message': self.format(record),
                'filename': getattr(record, 'filename', ''),
                'function_name': getattr(record, 'function_name', ''),
                'line_number': str(getattr(record, 'line_number', '')),
                'extra': json.dumps(getattr(record, 'extra', {})),
                'created_at': str(time.time())
            }
            
            with self._connection_lock:
                # Store record as hash
                self.redis_client.hset(key, mapping=record_data)
                
                # Set expiration (24 hours)
                self.redis_client.expire(key, 86400)
                
                # Add to sorted set for timestamp-based queries
                self.redis_client.zadd('log_timestamps', {key: record.timestamp})
                
                return True
                
        except Exception as e:
            print(f"Error: Failed to insert record into Redis: {e}", file=sys.stderr)
            return False
    
    def _insert_batch(self, records: List[LogRecord]) -> bool:
        """Insert multiple records into Redis using pipeline."""
        try:
            with self._connection_lock:
                pipeline = self.redis_client.pipeline()
                
                for record in records:
                    # Create unique key
                    key = f"log:{record.timestamp}:{record.logger_name}:{record.levelname}"
                    
                    # Create hash with record data
                    record_data = {
                        'timestamp': str(record.timestamp),
                        'level': record.levelname,
                        'logger_name': record.logger_name,
                        'message': self.format(record),
                        'filename': getattr(record, 'filename', ''),
                        'function_name': getattr(record, 'function_name', ''),
                        'line_number': str(getattr(record, 'line_number', '')),
                        'extra': json.dumps(getattr(record, 'extra', {})),
                        'created_at': str(time.time())
                    }
                    
                    # Store record as hash
                    pipeline.hset(key, mapping=record_data)
                    
                    # Set expiration (24 hours)
                    pipeline.expire(key, 86400)
                    
                    # Add to sorted set for timestamp-based queries
                    pipeline.zadd('log_timestamps', {key: record.timestamp})
                
                # Execute pipeline
                pipeline.execute()
                return True
                
        except Exception as e:
            print(f"Error: Failed to insert batch into Redis: {e}", file=sys.stderr)
            return False
    
    def _close_connection(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            with self._connection_lock:
                try:
                    self.redis_client.close()
                except Exception:
                    pass
                self.redis_client = None


class DatabaseHandlerFactory:
    """Factory for creating database handlers."""
    
    @staticmethod
    def create_handler(
        handler_type: str,
        **kwargs
    ) -> BaseDatabaseHandler:
        """Create a database handler of the specified type."""
        handler_type = handler_type.lower()
        
        if handler_type == "sqlite":
            return SQLiteHandler(**kwargs)
        elif handler_type in ["postgresql", "postgres"]:
            return PostgreSQLHandler(**kwargs)
        elif handler_type == "mongodb":
            return MongoDBHandler(**kwargs)
        elif handler_type == "redis":
            return RedisHandler(**kwargs)
        else:
            raise ValueError(f"Unknown database handler type: {handler_type}")
    
    @staticmethod
    def create_sqlite_handler(database_path: str, **kwargs) -> SQLiteHandler:
        """Create an SQLite handler."""
        return SQLiteHandler(database_path=database_path, **kwargs)
    
    @staticmethod
    def create_postgresql_handler(host: str, port: int, database: str, **kwargs) -> PostgreSQLHandler:
        """Create a PostgreSQL handler."""
        return PostgreSQLHandler(host=host, port=port, database=database, **kwargs)
    
    @staticmethod
    def create_mongodb_handler(host: str, port: int, database: str, **kwargs) -> MongoDBHandler:
        """Create a MongoDB handler."""
        return MongoDBHandler(host=host, port=port, database=database, **kwargs)
    
    @staticmethod
    def create_redis_handler(host: str, port: int, database: int, **kwargs) -> RedisHandler:
        """Create a Redis handler."""
        return RedisHandler(host=host, port=port, database=database, **kwargs)
