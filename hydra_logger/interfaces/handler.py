"""
Handler Interface for Hydra-Logger

This module defines the abstract interface that all handler implementations
must follow, ensuring consistent behavior across different output destinations.
It provides a standardized contract for handling log records.

ARCHITECTURE:
- HandlerInterface: Abstract interface for all handler implementations
- Defines contract for log record handling and output
- Ensures consistent behavior across different output destinations
- Supports health monitoring and performance metrics

CORE FEATURES:
- Log record emission and handling
- Level-based filtering and validation
- Handler lifecycle management
- Health status monitoring
- Performance metrics collection
- Configuration and state management

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import HandlerInterface
    from hydra_logger.types.records import LogRecord
    from typing import Any, Dict
    
    class ConsoleHandler(HandlerInterface):
        def __init__(self, level: int = 0):
            self.level = level
            self._initialized = True
            self._closed = False
            self._config = {"type": "console", "level": level}
        
        def emit(self, record: LogRecord) -> None:
            print(f"{record.levelname}: {record.message}")
        
        def handle(self, record: LogRecord) -> None:
            if self.isEnabledFor(record.level):
                self.emit(record)
        
        def setLevel(self, level: int) -> None:
            self.level = level
        
        def isEnabledFor(self, level: int) -> bool:
            return level >= self.level
        
        def close(self) -> None:
            self._closed = True
        
        def is_initialized(self) -> bool:
            return self._initialized
        
        def is_closed(self) -> bool:
            return self._closed
        
        def get_config(self) -> Dict[str, Any]:
            return self._config.copy()
        
        def get_handler_type(self) -> str:
            return "console"
        
        def is_healthy(self) -> bool:
            return self._initialized and not self._closed
        
        def get_health_status(self) -> Dict[str, Any]:
            return {
                "healthy": self.is_healthy(),
                "initialized": self._initialized,
                "closed": self._closed
            }
        
        def get_performance_metrics(self) -> Dict[str, Any]:
            return {
                "handler_type": "console",
                "level": self.level,
                "healthy": self.is_healthy()
            }

Handler Usage:
    from hydra_logger.interfaces import HandlerInterface
    from hydra_logger.types.records import LogRecord
    
    def process_handler(handler: HandlerInterface, record: LogRecord):
        \"\"\"Process a log record using any handler that implements HandlerInterface.\"\"\"
        if handler.is_initialized() and not handler.is_closed():
            if handler.is_healthy():
                handler.handle(record)
            else:
                print(f"Handler {handler.get_handler_type()} is unhealthy")
        else:
            print("Handler not available")

Polymorphic Usage:
    from hydra_logger.interfaces import HandlerInterface
    
    def process_handlers(handlers: List[HandlerInterface], record: LogRecord):
        \"\"\"Process record with multiple handlers.\"\"\"
        for handler in handlers:
            if handler.is_initialized() and not handler.is_closed():
                if handler.is_healthy():
                    handler.handle(record)
                else:
                    health_status = handler.get_health_status()
                    print(f"Handler {handler.get_handler_type()} unhealthy: {health_status}")

Health Monitoring:
    from hydra_logger.interfaces import HandlerInterface
    
    def monitor_handlers(handlers: List[HandlerInterface]):
        \"\"\"Monitor health of all handlers.\"\"\"
        for handler in handlers:
            if handler.is_healthy():
                metrics = handler.get_performance_metrics()
                print(f"Handler {handler.get_handler_type()} is healthy: {metrics}")
            else:
                health_status = handler.get_health_status()
                print(f"Handler {handler.get_handler_type()} is unhealthy: {health_status}")

INTERFACE CONTRACTS:
- emit(): Emit a log record to the destination
- handle(): Handle a log record (check level and emit if enabled)
- setLevel(): Set the minimum log level for this handler
- isEnabledFor(): Check if handler is enabled for the given level
- close(): Close the handler and cleanup resources
- is_initialized(): Check if handler is properly initialized
- is_closed(): Check if handler is closed
- get_config(): Get handler configuration
- get_handler_type(): Get the handler type
- is_healthy(): Check if handler is healthy
- get_health_status(): Get handler health status
- get_performance_metrics(): Get handler performance metrics

ERROR HANDLING:
- All methods include proper error handling
- Health checks prevent processing with unhealthy handlers
- Initialization checks ensure proper state
- Clear error messages and status reporting

BENEFITS:
- Consistent handler API across implementations
- Easy testing with mock handlers
- Clear contracts for custom handlers
- Polymorphic usage without tight coupling
- Better health monitoring and performance tracking
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from ..types.records import LogRecord


class HandlerInterface(ABC):
    """
    Abstract interface for all handler implementations.
    
    This interface defines the contract that all handlers must implement,
    ensuring consistent behavior across different output destinations.
    """
    
    @abstractmethod
    def emit(self, record: LogRecord) -> None:
        """
        Emit a log record to the destination.
        
        Args:
            record: Log record to emit
        """
        raise NotImplementedError
    
    @abstractmethod
    def handle(self, record: LogRecord) -> None:
        """
        Handle a log record (check level and emit if enabled).
        
        Args:
            record: Log record to handle
        """
        raise NotImplementedError
    
    @abstractmethod
    def setLevel(self, level: int) -> None:
        """
        Set the minimum log level for this handler.
        
        Args:
            level: Minimum log level
        """
        raise NotImplementedError
    
    @abstractmethod
    def isEnabledFor(self, level: int) -> bool:
        """
        Check if handler is enabled for the given level.
        
        Args:
            level: Log level to check
            
        Returns:
            True if enabled, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def close(self) -> None:
        """Close the handler and cleanup resources."""
        raise NotImplementedError
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if handler is properly initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_closed(self) -> bool:
        """
        Check if handler is closed.
        
        Returns:
            True if closed, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get handler configuration.
        
        Returns:
            Configuration dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_handler_type(self) -> str:
        """
        Get the handler type.
        
        Returns:
            Handler type string
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if handler is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get handler health status.
        
        Returns:
            Health status dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get handler performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        raise NotImplementedError
