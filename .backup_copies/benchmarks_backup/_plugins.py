#!/usr/bin/env python3
"""
Real Hydra-Logger Plugins using actual components with proper naming.

This module creates benchmark plugins that use the ACTUAL hydra_logger components
with their REAL names and configurations, not custom implementations.
"""

import os
import sys
import time
import asyncio
from typing import List, Tuple, Dict, Any, Union, Type
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ACTUAL hydra_logger components
from hydra_logger import SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger
from hydra_logger.handlers.console import SyncConsoleHandler, AsyncConsoleHandler
from hydra_logger.handlers.file import SyncFileHandler, AsyncFileHandler, FileHandler
from hydra_logger.handlers.network import HTTPHandler
from hydra_logger.handlers.database import SQLiteHandler
from hydra_logger.handlers.null import NullHandler
from hydra_logger.formatters.json import JsonLinesFormatter
from hydra_logger.formatters.text import PlainTextFormatter, FastPlainTextFormatter
from hydra_logger.formatters.color import ColoredFormatter
from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination


class LoggerBenchmark(ABC):
    """Abstract base class for any logger implementation with performance optimizations."""
    
    def __init__(self, **kwargs):
        """Initialize the logger with any configuration."""
        self.name = kwargs.get('name', self.__class__.__name__)
        self.log_file = None
        self._performance_stats = {
            'total_messages': 0,
            'batch_count': 0,
            'last_batch_size': 0
        }
    
    @abstractmethod
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a single message."""
        pass
    
    def log_batch(self, messages: List[tuple]) -> None:
        """Log multiple messages in batch with performance tracking."""
        if not messages:
            return
        
        self._performance_stats['batch_count'] += 1
        self._performance_stats['last_batch_size'] = len(messages)
        self._performance_stats['total_messages'] += len(messages)
        
        # Use optimized batch processing if available
        if hasattr(self, 'log_batch_optimized'):
            self.log_batch_optimized(messages)
        else:
            # Fallback to individual logging
            for level, message, kwargs in messages:
                self.log(level, message, **kwargs)
    
    def log_batch_optimized(self, messages: List[tuple]) -> None:
        """Optimized batch logging - override in subclasses for maximum performance."""
        # Default implementation - can be overridden for better performance
        for level, message, kwargs in messages:
            self.log(level, message, **kwargs)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this logger."""
        return self._performance_stats.copy()
    
    def close(self) -> None:
        """Cleanup and close the logger."""
        pass


# ============================================================================
# CONFIGURATION FACTORY - Eliminate Code Duplication
# ============================================================================

class LoggerConfigFactory:
    """Factory for creating optimized logger configurations."""
    
    @staticmethod
    def create_file_config(log_file: str, format_type: str, **kwargs) -> LoggingConfig:
        """Create optimized file logger configuration."""
        return LoggingConfig(
            default_level="INFO",
            buffer_size=kwargs.get('buffer_size', 1048576),  # 1MB default
            flush_interval=kwargs.get('flush_interval', 0.5),  # 0.5s default
            layers={
                "file": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=log_file,
                            format=format_type
                        )
                    ]
                )
            }
        )
    
    @staticmethod
    def create_plain_text_with_timestamp_config(log_file: str, **kwargs) -> LoggingConfig:
        """Create plain text logger configuration with timestamp format."""
        return LoggingConfig(
            default_level="INFO",
            buffer_size=kwargs.get('buffer_size', 1048576),  # 1MB default
            flush_interval=kwargs.get('flush_interval', 0.5),  # 0.5s default
            layers={
                "file": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=log_file,
                            format="plain-text"
                        )
                    ]
                )
            }
        )
    
    @staticmethod
    def create_console_config(use_colors: bool = True, **kwargs) -> LoggingConfig:
        """Create optimized console logger configuration."""
        return LoggingConfig(
            default_level="INFO",
            buffer_size=kwargs.get('buffer_size', 10000),  # Smaller buffer for console
            flush_interval=kwargs.get('flush_interval', 0.1),  # Faster flush for console
            layers={
                "console": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="colored" if use_colors else "plain-text",
                            use_colors=use_colors
                        )
                    ]
                )
            }
        )
    
    @staticmethod
    def create_memory_config(**kwargs) -> LoggingConfig:
        """Create optimized memory logger configuration."""
        return LoggingConfig(
            default_level="INFO",
            layers={
                "memory": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="null")
                    ]
                )
            }
        )
    
    @staticmethod
    def create_network_config(endpoint: str, **kwargs) -> LoggingConfig:
        """Create optimized network logger configuration."""
        return LoggingConfig(
            default_level="INFO",
            buffer_size=kwargs.get('buffer_size', 10000),
            flush_interval=kwargs.get('flush_interval', 0.1),
            layers={
                "network": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_cloud",
                            url=endpoint,
                            format="json-lines",
                            service="http"
                        )
                    ]
                )
            }
        )


# ============================================================================
# SYNC LOGGERS - Using REAL Hydra-Logger Components
# ============================================================================

class HydraSyncFileLogger(LoggerBenchmark):
    """Optimized sync file logger with high-performance batch processing."""
    
    def __init__(self, name: str = "HydraSyncFileLogger", 
                 log_file: str = None,
                 format_type: str = "json-lines",
                 **kwargs):
        super().__init__(name=name, **kwargs)
        short_name = self._get_short_name(name, format_type)
        self.log_file = log_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{short_name}.{self._get_file_extension(format_type)}"))
        
        # Use factory for configuration
        config = LoggerConfigFactory.create_file_config(
            log_file=self.log_file,
            format_type=format_type,
            **kwargs
        )
        
        # Create real SyncLogger
        self.logger = SyncLogger(name=name, config=config)
    
    def _get_file_extension(self, format_type: str) -> str:
        """Get appropriate file extension for format type."""
        extensions = {
            "json-lines": "jsonl",
            "json": "json",
            "csv": "csv",
            "plain-text": "log",
            "fast-plain": "log",
            "detailed": "log",
            "syslog": "log",
            "gelf": "log",
            "logstash": "log",
            "binary": "bin",
            "binary-compact": "bin",
            "binary-extended": "bin"
        }
        return extensions.get(format_type, "log")
    
    def _get_short_name(self, name: str, format_type: str) -> str:
        """Get short, descriptive filename."""
        # Remove common prefixes and suffixes
        short_name = name.lower()
        
        # Remove "hydra" prefix
        if short_name.startswith('hydra'):
            short_name = short_name[5:]
        
        # Remove "logger" suffix
        if short_name.endswith('logger'):
            short_name = short_name[:-6]
        
        # Handle specific cases for better clarity
        name_mapping = {
            'syncfile': 'sync_file',
            'syncconsole': 'sync_console', 
            'syncmemory': 'sync_memory',
            'syncnetwork': 'sync_network',
            'syncdatabase': 'sync_database',
            'synccomposite': 'sync_composite',
            'asyncfile': 'async_file',
            'asyncconsole': 'async_console',
            'asyncmemory': 'async_memory',
            'asynccomposite': 'async_composite',
            'asyncplaintext': 'async_plain',
            'asyncjsonlines': 'async_json',
            'asynccsv': 'async_csv',
            'plaintext': 'plain',
            'fastplain': 'fast',
            'detailed': 'detailed',
            'jsonlines': 'json',
            'json': 'json',
            'colored': 'colored',
            'csv': 'csv',
            'syslog': 'syslog',
            'gelf': 'gelf',
            'logstash': 'logstash',
            'binary': 'binary',
            'binarycompact': 'binary_compact',
            'binaryextended': 'binary_extended'
        }
        
        return name_mapping.get(short_name, short_name)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger."""
        self.logger.log(level, message, layer="file", **kwargs)
    
    def log_batch_optimized(self, messages: List[tuple]) -> None:
        """Optimized batch processing for maximum performance."""
        # Process messages in chunks to avoid memory issues
        chunk_size = 1000
        for i in range(0, len(messages), chunk_size):
            chunk = messages[i:i + chunk_size]
            for level, message, kwargs in chunk:
                self.logger.log(level, message, layer="file", **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger."""
        self.logger.close()


class HydraSyncConsoleLogger(LoggerBenchmark):
    """Real sync console logger using actual SyncLogger + SyncConsoleHandler + ColoredFormatter."""
    
    def __init__(self, name: str = "HydraSyncConsoleLogger",
                 use_colors: bool = True,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        
        # Create real Hydra-Logger configuration
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "console": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",  # Use 'console' type for SyncConsoleHandler
                            format="colored" if use_colors else "plain-text",  # Correct format for console
                            use_colors=use_colors
                        )
                    ]
                )
            }
        )
        
        # Create real SyncLogger
        self.logger = SyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger."""
        self.logger.log(level, message, layer="console", **kwargs)
    
    def log_batch(self, messages: List[tuple]) -> None:
        """Log multiple messages in batch using real Hydra-Logger."""
        for level, message, kwargs in messages:
            self.logger.log(level, message, layer="console", **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger."""
        self.logger.close()


class HydraSyncMemoryLogger(LoggerBenchmark):
    """Real sync memory logger using actual SyncLogger + NullHandler (fastest possible)."""
    
    def __init__(self, name: str = "HydraSyncMemoryLogger",
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        
        # Create real Hydra-Logger configuration with NullHandler
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "memory": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="null")  # Use 'null' type for NullHandler
                    ]
                )
            }
        )
        
        # Create real SyncLogger
        self.logger = SyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger (no output)."""
        self.logger.log(level, message, layer="memory", **kwargs)
    
    def log_batch(self, messages: List[tuple]) -> None:
        """Log multiple messages in batch using real Hydra-Logger."""
        for level, message, kwargs in messages:
            self.logger.log(level, message, layer="memory", **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger."""
        self.logger.close()


class HydraSyncNetworkLogger(LoggerBenchmark):
    """Real sync network logger using actual SyncLogger + HTTPHandler + JsonLinesFormatter."""
    
    def __init__(self, name: str = "HydraSyncNetworkLogger",
                 endpoint: str = "http://localhost:8080/logs",
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        
        # Create real Hydra-Logger configuration
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "network": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_cloud",  # Use async_cloud for HTTP network
                            url=endpoint,
                            format="json-lines",  # Correct format for network/cloud
                            service="http"  # Required for async_cloud
                        )
                    ]
                )
            }
        )
        
        # Create real SyncLogger
        self.logger = SyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger."""
        self.logger.log(level, message, layer="network", **kwargs)
    
    def log_batch(self, messages: List[tuple]) -> None:
        """Log multiple messages in batch using real Hydra-Logger."""
        for level, message, kwargs in messages:
            self.logger.log(level, message, layer="network", **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger."""
        self.logger.close()


class HydraSyncDatabaseLogger(LoggerBenchmark):
    """Real sync database logger using actual SyncLogger + SQLiteHandler + JsonLinesFormatter."""
    
    def __init__(self, name: str = "HydraSyncDatabaseLogger",
                 db_file: str = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        short_name = self._get_short_name(name, "json-lines")
        self.db_file = db_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{short_name}.db"))
        
        # Create real Hydra-Logger configuration
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "database": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",  # Use 'file' type for SQLite (stored as file)
                            path=self.db_file,
                            format="json-lines"  # Correct format for database/file
                        )
                    ]
                )
            }
        )
        
        # Create real SyncLogger
        self.logger = SyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger."""
        self.logger.log(level, message, layer="database", **kwargs)
    
    def log_batch(self, messages: List[tuple]) -> None:
        """Log multiple messages in batch using real Hydra-Logger."""
        for level, message, kwargs in messages:
            self.logger.log(level, message, layer="database", **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger."""
        self.logger.close()


class HydraSyncCompositeLogger(LoggerBenchmark):
    """Real sync composite logger using actual CompositeLogger with multiple components."""
    
    def __init__(self, name: str = "HydraSyncCompositeLogger",
                 log_file: str = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        
        # Create individual logger components
        console_config = LoggingConfig(
            default_level="INFO",
            layers={
                "console": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="colored",  # Correct format for console
                            use_colors=True
                        )
                    ]
                )
            }
        )
        console_logger = SyncLogger(name=f"{name}_console", config=console_config)
        
        # File logger component
        log_path = log_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{name.lower()}.log"))
        file_config = LoggingConfig(
            default_level="INFO",
            layers={
                "file": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=log_path,
                            format="json-lines"  # Correct format for file
                        )
                    ]
                )
            }
        )
        file_logger = SyncLogger(name=f"{name}_file", config=file_config)
        
        # Create real CompositeLogger with actual components
        self.logger = CompositeLogger(name=name, components=[console_logger, file_logger])
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger CompositeLogger."""
        # Log to all components with proper layer routing
        for component in self.logger.components:
            if hasattr(component, 'log'):
                if 'console' in component.name:
                    component.log(level, message, layer="console", **kwargs)
                elif 'file' in component.name:
                    component.log(level, message, layer="file", **kwargs)
                else:
                    component.log(level, message, **kwargs)
    
    def log_batch(self, messages: List[tuple]) -> None:
        """Log multiple messages in batch using real Hydra-Logger CompositeLogger."""
        for level, message, kwargs in messages:
            for component in self.logger.components:
                if hasattr(component, 'log'):
                    if 'console' in component.name:
                        component.log(level, message, layer="console", **kwargs)
                    elif 'file' in component.name:
                        component.log(level, message, layer="file", **kwargs)
                    else:
                        component.log(level, message, **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger CompositeLogger."""
        self.logger.close()


# ============================================================================
# ASYNC LOGGERS - Using REAL Hydra-Logger Components
# ============================================================================

class HydraAsyncFileLogger(LoggerBenchmark):
    """Real async file logger using actual AsyncLogger + AsyncFileHandler + JsonLinesFormatter."""
    
    def __init__(self, name: str = "HydraAsyncFileLogger", 
                 log_file: str = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        self.log_file = log_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{name.lower()}.jsonl"))
        
        # Create real Hydra-Logger configuration
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "async_file": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_file",  # Use 'async_file' type for AsyncFileHandler
                            path=self.log_file,
                            format="json-lines"  # Correct format for async file
                        )
                    ]
                )
            }
        )
        
        # Create real AsyncLogger
        self.logger = AsyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger AsyncLogger."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.logger.log(level, message, layer="async_file", **kwargs))
        except RuntimeError:
            asyncio.run(self.logger.log(level, message, layer="async_file", **kwargs))
    
    async def alog(self, level: str, message: str, **kwargs) -> None:
        """Async log a message using real Hydra-Logger AsyncLogger."""
        await self.logger.log(level, message, layer="async_file", **kwargs)
    
    async def log_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
        for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_file", **kwargs)
        
    async def alog_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
        for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_file", **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger AsyncLogger."""
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()
    
    async def aclose(self) -> None:
        """Async close the real Hydra-Logger AsyncLogger."""
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()


class HydraAsyncConsoleLogger(LoggerBenchmark):
    """Real async console logger using actual AsyncLogger + AsyncConsoleHandler + ColoredFormatter."""
    
    def __init__(self, name: str = "HydraAsyncConsoleLogger",
                 use_colors: bool = True,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        
        # Create real Hydra-Logger configuration
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "async_console": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_console",  # Use 'async_console' type for AsyncConsoleHandler
                            format="colored" if use_colors else "plain-text",  # Correct format for async console
                            use_colors=use_colors
                        )
                    ]
                )
            }
        )
        
        # Create real AsyncLogger
        self.logger = AsyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger AsyncLogger."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.logger.log(level, message, layer="async_console", **kwargs))
        except RuntimeError:
            asyncio.run(self.logger.log(level, message, layer="async_console", **kwargs))
    
    async def alog(self, level: str, message: str, **kwargs) -> None:
        """Async log a message using real Hydra-Logger AsyncLogger."""
        await self.logger.log(level, message, layer="async_console", **kwargs)
    
    async def log_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
        for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_console", **kwargs)
    
    async def alog_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
        for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_console", **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger AsyncLogger."""
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()
    
    async def aclose(self) -> None:
        """Async close the real Hydra-Logger AsyncLogger."""
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()


class HydraAsyncMemoryLogger(LoggerBenchmark):
    """Real async memory logger using actual AsyncLogger + NullHandler (fastest possible)."""
    
    def __init__(self, name: str = "HydraAsyncMemoryLogger",
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        
        # Create real Hydra-Logger configuration with NullHandler
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "async_memory": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="null")  # Use 'null' type for NullHandler
                    ]
                )
            }
        )
        
        # Create real AsyncLogger
        self.logger = AsyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger AsyncLogger (no output)."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.logger.log(level, message, layer="async_memory", **kwargs))
        except RuntimeError:
            asyncio.run(self.logger.log(level, message, layer="async_memory", **kwargs))
    
    async def alog(self, level: str, message: str, **kwargs) -> None:
        """Async log a message using real Hydra-Logger AsyncLogger."""
        await self.logger.log(level, message, layer="async_memory", **kwargs)
    
    async def log_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
                    for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_memory", **kwargs)
    
    async def alog_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
        for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_memory", **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger AsyncLogger."""
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()
    
    async def aclose(self) -> None:
        """Async close the real Hydra-Logger AsyncLogger."""
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()


class HydraAsyncCompositeLogger(LoggerBenchmark):
    """Real async composite logger using actual CompositeAsyncLogger with multiple components."""
    
    def __init__(self, name: str = "HydraAsyncCompositeLogger",
                 log_file: str = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        
        # Create individual async logger components
        console_config = LoggingConfig(
            default_level="INFO",
            layers={
                "async_console": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_console",
                            format="colored",  # Correct format for async console
                            use_colors=True
                        )
                    ]
                )
            }
        )
        console_logger = AsyncLogger(name=f"{name}_console", config=console_config)
        
        # File logger component
        log_path = log_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{name.lower()}.log"))
        file_config = LoggingConfig(
            default_level="INFO",
            layers={
                "async_file": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_file",
                            path=log_path,
                            format="json-lines"  # Correct format for async file
                        )
                    ]
                )
            }
        )
        file_logger = AsyncLogger(name=f"{name}_file", config=file_config)
        
        # Create real CompositeAsyncLogger with actual components
        self.logger = CompositeAsyncLogger(name=name, components=[console_logger, file_logger])
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger CompositeAsyncLogger."""
        for component in self.logger.components:
            if hasattr(component, 'log'):
                if 'console' in component.name:
                    asyncio.create_task(component.log(level, message, layer="async_console", **kwargs))
                elif 'file' in component.name:
                    asyncio.create_task(component.log(level, message, layer="async_file", **kwargs))
                else:
                    asyncio.create_task(component.log(level, message, **kwargs))
    
    async def alog(self, level: str, message: str, **kwargs) -> None:
        """Async log a message using real Hydra-Logger CompositeAsyncLogger."""
        for component in self.logger.components:
            if hasattr(component, 'log'):
                if 'console' in component.name:
                    await component.log(level, message, layer="async_console", **kwargs)
                elif 'file' in component.name:
                    await component.log(level, message, layer="async_file", **kwargs)
                else:
                    await component.log(level, message, **kwargs)
    
    async def log_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger CompositeAsyncLogger."""
        for level, message, kwargs in messages:
            for component in self.logger.components:
                if hasattr(component, 'log'):
                    if 'console' in component.name:
                        await component.log(level, message, layer="async_console", **kwargs)
                    elif 'file' in component.name:
                        await component.log(level, message, layer="async_file", **kwargs)
                    else:
                        await component.log(level, message, **kwargs)
    
    async def alog_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger CompositeAsyncLogger."""
        for level, message, kwargs in messages:
            for component in self.logger.components:
                if hasattr(component, 'log'):
                    if 'console' in component.name:
                        await component.log(level, message, layer="async_console", **kwargs)
                    elif 'file' in component.name:
                        await component.log(level, message, layer="async_file", **kwargs)
                    else:
                        await component.log(level, message, **kwargs)
    
    def close(self) -> None:
        """Close the real Hydra-Logger CompositeAsyncLogger."""
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()
    
    async def aclose(self) -> None:
        """Async close the real Hydra-Logger CompositeAsyncLogger."""
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()


# ============================================================================
# ASYNC FORMAT-SPECIFIC LOGGERS - Complete Async Support
# ============================================================================

class HydraAsyncPlainTextLogger(LoggerBenchmark):
    """Async plain text logger using plain-text format."""
    
    def __init__(self, name: str = "HydraAsyncPlainTextLogger", 
                 log_file: str = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        short_name = self._get_short_name(name, "json-lines")
        self.log_file = log_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{short_name}.log"))
        
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "async_file": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_file",
                            path=self.log_file,
                            format="plain-text"
                        )
                    ]
                )
            }
        )
        
        self.logger = AsyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.logger.log(level, message, layer="async_file", **kwargs))
        except RuntimeError:
            asyncio.run(self.logger.log(level, message, layer="async_file", **kwargs))
    
    async def alog(self, level: str, message: str, **kwargs) -> None:
        await self.logger.log(level, message, layer="async_file", **kwargs)
    
    async def log_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
        for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_file", **kwargs)
    
    def close(self) -> None:
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()
    
    async def aclose(self) -> None:
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()


class HydraAsyncJsonLinesLogger(LoggerBenchmark):
    """Async JSON Lines logger using json-lines format."""
    
    def __init__(self, name: str = "HydraAsyncJsonLinesLogger", 
                 log_file: str = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        self.log_file = log_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{name.lower()}.jsonl"))
        
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "async_file": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_file",
                            path=self.log_file,
                            format="json-lines"
                        )
                    ]
                )
            }
        )
        
        self.logger = AsyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.logger.log(level, message, layer="async_file", **kwargs))
        except RuntimeError:
            asyncio.run(self.logger.log(level, message, layer="async_file", **kwargs))
    
    async def alog(self, level: str, message: str, **kwargs) -> None:
        await self.logger.log(level, message, layer="async_file", **kwargs)
    
    async def log_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
        for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_file", **kwargs)
    
    def close(self) -> None:
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()
    
    async def aclose(self) -> None:
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()


class HydraAsyncCsvLogger(LoggerBenchmark):
    """Async CSV logger using csv format."""
    
    def __init__(self, name: str = "HydraAsyncCsvLogger", 
                 log_file: str = None,
                 **kwargs):
        super().__init__(name=name, **kwargs)  # Initialize base class with _performance_stats
        self.log_file = log_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{name.lower()}.csv"))
        
        config = LoggingConfig(
            default_level="INFO",
            layers={
                "async_file": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_file",
                            path=self.log_file,
                            format="csv"
                        )
                    ]
                )
            }
        )
        
        self.logger = AsyncLogger(name=name, config=config)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.logger.log(level, message, layer="async_file", **kwargs))
        except RuntimeError:
            asyncio.run(self.logger.log(level, message, layer="async_file", **kwargs))
    
    async def alog(self, level: str, message: str, **kwargs) -> None:
        await self.logger.log(level, message, layer="async_file", **kwargs)
    
    async def log_batch(self, messages: List[tuple]) -> None:
        """Async log multiple messages in batch using real Hydra-Logger AsyncLogger."""
        for level, message, kwargs in messages:
            await self.logger.log(level, message, layer="async_file", **kwargs)
    
    def close(self) -> None:
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()
    
    async def aclose(self) -> None:
        # AsyncLogger.close() is not a coroutine, just call it directly
        self.logger.close()


# ============================================================================
# FORMAT-SPECIFIC LOGGER FACTORY - Replace Individual Format Loggers
# ============================================================================

class FormatSpecificLogger(LoggerBenchmark):
    """Generic logger for any format type with optimized performance."""
    
    def __init__(self, name: str = None, format_type: str = "plain-text", log_file: str = None, **kwargs):
        # Set default name if not provided
        if name is None:
            name = f"{format_type.title()}Logger"
        
        super().__init__(name=name, **kwargs)
        self.format_type = format_type
        short_name = self._get_short_name(name, format_type)
        self.log_file = log_file or os.path.abspath(os.path.join(os.getcwd(), "benchmarks", "_logs", f"{short_name}.{self._get_file_extension(format_type)}"))
    
    def _get_file_extension(self, format_type: str) -> str:
        """Get appropriate file extension for format type."""
        extensions = {
            "json-lines": "jsonl",
            "json": "json",
            "csv": "csv",
            "plain-text": "log",
            "fast-plain": "log",
            "detailed": "log",
            "syslog": "log",
            "gelf": "log",
            "logstash": "log",
            "binary": "bin",
            "binary-compact": "bin",
            "binary-extended": "bin"
        }
        return extensions.get(format_type, "log")
    
    def _get_short_name(self, name: str, format_type: str) -> str:
        """Get short, descriptive filename."""
        # Remove common prefixes and suffixes
        short_name = name.lower()
        
        # Remove "hydra" prefix
        if short_name.startswith('hydra'):
            short_name = short_name[5:]
        
        # Remove "logger" suffix
        if short_name.endswith('logger'):
            short_name = short_name[:-6]
        
        # Handle specific cases for better clarity
        name_mapping = {
            'syncfile': 'sync_file',
            'syncconsole': 'sync_console', 
            'syncmemory': 'sync_memory',
            'syncnetwork': 'sync_network',
            'syncdatabase': 'sync_database',
            'synccomposite': 'sync_composite',
            'asyncfile': 'async_file',
            'asyncconsole': 'async_console',
            'asyncmemory': 'async_memory',
            'asynccomposite': 'async_composite',
            'asyncplaintext': 'async_plain',
            'asyncjsonlines': 'async_json',
            'asynccsv': 'async_csv',
            'plaintext': 'plain',
            'fastplain': 'fast',
            'detailed': 'detailed',
            'jsonlines': 'json',
            'json': 'json',
            'colored': 'colored',
            'csv': 'csv',
            'syslog': 'syslog',
            'gelf': 'gelf',
            'logstash': 'logstash',
            'binary': 'binary',
            'binarycompact': 'binary_compact',
            'binaryextended': 'binary_extended'
        }
        
        return name_mapping.get(short_name, short_name)
    
    def _configure_plain_text_with_timestamps(self, logger, format_type: str):
        """Configure plain text formatter with timestamps for better readability."""
        if format_type == "plain-text":
            from hydra_logger.formatters.text import PlainTextFormatter
            from hydra_logger.config.models import TimestampConfig
            
            # Create custom formatter with timestamps
            formatter = PlainTextFormatter(
                format_string="[{timestamp}] [{level_name}] [{layer}] {message}",
                timestamp_config=TimestampConfig(format_type="HUMAN_READABLE")
            )
            
            # Apply formatter to file handler
            for handler in logger._handlers.values():
                if hasattr(handler, 'formatter'):
                    handler.setFormatter(formatter)
                    break
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message using real Hydra-Logger."""
        # Handle layer argument properly
        layer = kwargs.pop('layer', 'file')
        self.logger.log(level, message, layer=layer, **kwargs)
    
    def log_batch(self, messages: List[Tuple[str, str]], **kwargs) -> None:
        """Log multiple messages efficiently."""
        layer = kwargs.pop('layer', 'file')
        for level, message in messages:
            self.logger.log(level, message, layer=layer, **kwargs)
    
    def close(self) -> None:
        """Close the logger."""
        if hasattr(self, 'logger'):
            self.logger.close()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self._performance_stats


# ============================================================================
# PLUGIN REGISTRY - Centralized Plugin Management
# ============================================================================

def create_format_logger(format_type: str, name: str = None, **kwargs):
    """Factory function to create format-specific loggers."""
    if name is None:
        name = f"Plugin_{format_type}"
    
    return FormatSpecificLogger(name=name, format_type=format_type, **kwargs)

# Registry of all available logger plugins
LOGGER_PLUGINS = {
    # Format-specific plugins (using factory)
    "plain_text": lambda **kwargs: create_format_logger("plain-text", **kwargs),
    "fast_plain": lambda **kwargs: create_format_logger("fast-plain", **kwargs),
    "detailed": lambda **kwargs: create_format_logger("detailed", **kwargs),
    "json_lines": lambda **kwargs: create_format_logger("json-lines", **kwargs),
    "json": lambda **kwargs: create_format_logger("json", **kwargs),
    "colored": lambda **kwargs: create_format_logger("colored", **kwargs),
    "csv": lambda **kwargs: create_format_logger("csv", **kwargs),
    "syslog": lambda **kwargs: create_format_logger("syslog", **kwargs),
    "gelf": lambda **kwargs: create_format_logger("gelf", **kwargs),
    "logstash": lambda **kwargs: create_format_logger("logstash", **kwargs),
    "binary": lambda **kwargs: create_format_logger("binary", **kwargs),
    "binary_compact": lambda **kwargs: create_format_logger("binary-compact", **kwargs),
    "binary_extended": lambda **kwargs: create_format_logger("binary-extended", **kwargs),
    
    # Original sync plugins
    "sync_file": HydraSyncFileLogger,
    "sync_console": HydraSyncConsoleLogger,
    "sync_memory": HydraSyncMemoryLogger,
    "sync_network": HydraSyncNetworkLogger,
    "sync_database": HydraSyncDatabaseLogger,
    "sync_composite": HydraSyncCompositeLogger,
    
    # Original async plugins
    "async_file": HydraAsyncFileLogger,
    "async_console": HydraAsyncConsoleLogger,
    "async_memory": HydraAsyncMemoryLogger,
    "async_composite": HydraAsyncCompositeLogger,
    
    # Async format-specific plugins
    "async_plain_text": HydraAsyncPlainTextLogger,
    "async_json_lines": HydraAsyncJsonLinesLogger,
    "async_csv": HydraAsyncCsvLogger,
}

def get_plugin(plugin_name: str) -> Type[LoggerBenchmark]:
    """Get a plugin class by name."""
    return LOGGER_PLUGINS.get(plugin_name)

def list_plugins() -> List[str]:
    """List all available plugin names."""
    return list(LOGGER_PLUGINS.keys())

def get_plugin_info(plugin_name: str) -> Dict[str, Any]:
    """Get information about a plugin."""
    plugin_class = get_plugin(plugin_name)
    if plugin_class:
    return {
        "name": plugin_name,
        "class": plugin_class.__name__,
            "description": plugin_class.__doc__ or "No description available"
    }
    return None
