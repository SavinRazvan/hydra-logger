"""
Logger Interface for Hydra-Logger

This module defines the abstract interface that all logger implementations
must follow, ensuring consistent behavior across sync, async, and composite loggers.
It provides a standardized contract for logging operations.

ARCHITECTURE:
- LoggerInterface: Abstract interface for all logger implementations
- Defines contract for logging operations and handler management
- Ensures consistent behavior across different logger types
- Supports health monitoring and configuration management

CORE FEATURES:
- Logging operations at all levels (debug, info, warning, error, critical)
- Handler management and registration
- Logger lifecycle management
- Health status monitoring
- Configuration and state management

SUPPORTED LOGGER TYPES:
- SyncLogger: Synchronous logging with immediate output
- AsyncLogger: Asynchronous logging with queue-based processing
- CompositeLogger: Composite pattern for multiple logger components
- CompositeAsyncLogger: Async version of composite logger

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import LoggerInterface
    from hydra_logger.types.levels import LogLevel
    from typing import Any, Dict, Union, List
    
    class CustomLogger(LoggerInterface):
        def __init__(self):
            self._handlers = {}
            self._initialized = True
            self._closed = False
            self._config = {"type": "custom"}
        
        def log(self, level: Union[int, str, LogLevel], message: str, **kwargs) -> None:
            # Implement logging logic
            print(f"{level}: {message}")
        
        def debug(self, message: str, **kwargs) -> None:
            self.log("DEBUG", message, **kwargs)
        
        def info(self, message: str, **kwargs) -> None:
            self.log("INFO", message, **kwargs)
        
        def warning(self, message: str, **kwargs) -> None:
            self.log("WARNING", message, **kwargs)
        
        def error(self, message: str, **kwargs) -> None:
            self.log("ERROR", message, **kwargs)
        
        def critical(self, message: str, **kwargs) -> None:
            self.log("CRITICAL", message, **kwargs)
        
        def add_handler(self, name: str, handler: Any) -> bool:
            self._handlers[name] = handler
            return True
        
        def remove_handler(self, name: str) -> bool:
            if name in self._handlers:
                del self._handlers[name]
                return True
            return False
        
        def get_handlers(self) -> Dict[str, Any]:
            return self._handlers.copy()
        
        def is_initialized(self) -> bool:
            return self._initialized
        
        def is_closed(self) -> bool:
            return self._closed
        
        def close(self) -> None:
            self._closed = True
        
        def get_config(self) -> Dict[str, Any]:
            return self._config.copy()
        
        def get_health_status(self) -> Dict[str, Any]:
            return {
                "healthy": self._initialized and not self._closed,
                "initialized": self._initialized,
                "closed": self._closed,
                "handler_count": len(self._handlers)
            }

Logger Usage:
    from hydra_logger.interfaces import LoggerInterface
    
    def use_logger(logger: LoggerInterface):
        \"\"\"Use any logger that implements LoggerInterface.\"\"\"
        if logger.is_initialized() and not logger.is_closed():
            logger.info("This is an info message")
            logger.error("This is an error message")
            
            # Check health status
            health = logger.get_health_status()
            print(f"Logger health: {health}")
        else:
            print("Logger not available")

Polymorphic Usage:
    from hydra_logger.interfaces import LoggerInterface
    
    def use_loggers(loggers: List[LoggerInterface]):
        \"\"\"Use multiple loggers with the same interface.\"\"\"
        for logger in loggers:
            if logger.is_initialized() and not logger.is_closed():
                logger.info("Message from logger")
                
                # Get logger configuration
                config = logger.get_config()
                print(f"Logger config: {config}")
            else:
                print("Logger not available")

Handler Management:
    from hydra_logger.interfaces import LoggerInterface
    
    def manage_handlers(logger: LoggerInterface):
        \"\"\"Manage handlers using the logger interface.\"\"\"
        # Add handlers
        if logger.add_handler("console", console_handler):
            print("Console handler added")
        
        if logger.add_handler("file", file_handler):
            print("File handler added")
        
        # List handlers
        handlers = logger.get_handlers()
        print(f"Registered handlers: {list(handlers.keys())}")
        
        # Remove handler
        if logger.remove_handler("console"):
            print("Console handler removed")

INTERFACE CONTRACTS:
- log(): Log a message at the specified level
- debug(): Log a debug message
- info(): Log an info message
- warning(): Log a warning message
- error(): Log an error message
- critical(): Log a critical message
- add_handler(): Add a handler to the logger
- remove_handler(): Remove a handler from the logger
- get_handlers(): Get all registered handlers
- is_initialized(): Check if logger is properly initialized
- is_closed(): Check if logger is closed
- close(): Close the logger and cleanup resources
- get_config(): Get logger configuration
- get_health_status(): Get logger health status

ERROR HANDLING:
- All methods include proper error handling
- Health checks prevent logging with unhealthy loggers
- Initialization checks ensure proper state
- Clear error messages and status reporting

BENEFITS:
- Consistent logging API across implementations
- Easy testing with mock loggers
- Clear contracts for custom loggers
- Polymorphic usage without tight coupling
- Better health monitoring and configuration management
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List
from ..types.records import LogRecord
from ..types.levels import LogLevel


class LoggerInterface(ABC):
    """
    Abstract interface for all logger implementations.
    
    This interface defines the contract that all loggers must implement,
    ensuring consistent behavior across different implementations.
    """
    
    @abstractmethod
    def log(self, level: Union[int, str, LogLevel], message: str, **kwargs) -> None:
        """
        Log a message at the specified level.
        
        Args:
            level: Log level (int, string, or LogLevel enum)
            message: Log message
            **kwargs: Additional context and metadata
        """
        raise NotImplementedError
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        raise NotImplementedError
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        raise NotImplementedError
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        raise NotImplementedError
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        raise NotImplementedError
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        raise NotImplementedError
    
    @abstractmethod
    def add_handler(self, name: str, handler: Any) -> bool:
        """
        Add a handler to the logger.
        
        Args:
            name: Handler name
            handler: Handler instance
            
        Returns:
            True if handler was added successfully
        """
        raise NotImplementedError
    
    @abstractmethod
    def remove_handler(self, name: str) -> bool:
        """
        Remove a handler from the logger.
        
        Args:
            name: Handler name
            
        Returns:
            True if handler was removed successfully
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_handlers(self) -> Dict[str, Any]:
        """
        Get all registered handlers.
        
        Returns:
            Dictionary of handler names to handler instances
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if logger is properly initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_closed(self) -> bool:
        """
        Check if logger is closed.
        
        Returns:
            True if closed, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def close(self) -> None:
        """Close the logger and cleanup resources."""
        raise NotImplementedError
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get logger configuration.
        
        Returns:
            Configuration dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get logger health status.
        
        Returns:
            Health status dictionary
        """
        raise NotImplementedError
