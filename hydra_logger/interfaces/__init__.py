"""
Interfaces Module for Hydra-Logger

This module provides comprehensive abstract interfaces and contracts for all
system components. These interfaces ensure consistent behavior and enable
polymorphic usage across different implementations.

ARCHITECTURE:
- LoggerInterface: Abstract interface for all logger implementations
- HandlerInterface: Abstract interface for all handler implementations
- FormatterInterface: Abstract interface for all formatter implementations
- PluginInterface: Abstract interface for all plugin implementations
- MonitorInterface: Abstract interface for all monitoring implementations
- SecurityInterface: Abstract interface for all security implementations
- ConfigInterface: Abstract interface for all configuration implementations
- RegistryInterface: Abstract interface for all registry implementations
- LifecycleInterface: Abstract interface for all lifecycle management implementations

CORE INTERFACES:
- LoggerInterface: Defines contract for sync, async, and composite loggers
- HandlerInterface: Defines contract for all output destination handlers
- FormatterInterface: Defines contract for all log record formatters
- PluginInterface: Defines contract for all plugin implementations

SYSTEM INTERFACES:
- MonitorInterface: Defines contract for performance and health monitoring
- SecurityInterface: Defines contract for security and threat detection
- ConfigInterface: Defines contract for configuration management
- RegistryInterface: Defines contract for component registration and discovery
- LifecycleInterface: Defines contract for component lifecycle management

DESIGN PRINCIPLES:
- Interface Segregation: Each interface focuses on a specific responsibility
- Dependency Inversion: High-level modules depend on abstractions, not concretions
- Open/Closed: Open for extension, closed for modification
- Liskov Substitution: Implementations can be substituted without breaking functionality

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import LoggerInterface, HandlerInterface
    from hydra_logger.types.records import LogRecord
    
    class CustomLogger(LoggerInterface):
        def log(self, level, message, **kwargs):
            # Custom implementation
            pass
        
        def debug(self, message, **kwargs):
            self.log("DEBUG", message, **kwargs)
        
        # ... implement all required methods
    
    class CustomHandler(HandlerInterface):
        def emit(self, record: LogRecord):
            # Custom implementation
            pass
        
        # ... implement all required methods

Interface Validation:
    from hydra_logger.interfaces import LoggerInterface
    
    def validate_logger(logger) -> bool:
        \"\"\"Validate that logger implements LoggerInterface.\"\"\"
        return isinstance(logger, LoggerInterface)
    
    # Check if logger implements the interface
    if validate_logger(my_logger):
        print("Logger implements LoggerInterface")

Polymorphic Usage:
    from hydra_logger.interfaces import HandlerInterface
    
    def process_handlers(handlers: List[HandlerInterface]):
        \"\"\"Process any handlers that implement HandlerInterface.\"\"\"
        for handler in handlers:
            if handler.is_healthy():
                handler.emit(record)
            else:
                print(f"Handler {handler.get_handler_type()} is unhealthy")

INTERFACE CONTRACTS:
- All interfaces define abstract methods that must be implemented
- Methods include proper type hints and documentation
- Return types are clearly specified
- Error handling is consistent across implementations
- Performance characteristics are documented

BENEFITS:
- Consistent API across all implementations
- Easy testing with mock implementations
- Clear contracts for custom implementations
- Polymorphic usage without tight coupling
- Better code maintainability and extensibility
"""

from .logger import LoggerInterface
from .handler import HandlerInterface
from .formatter import FormatterInterface
from .plugin import PluginInterface
from .monitor import MonitorInterface
from .security import SecurityInterface
from .config import ConfigInterface
from .registry import RegistryInterface
from .lifecycle import LifecycleInterface

__all__ = [
    # Core interfaces
    "LoggerInterface",
    "HandlerInterface", 
    "FormatterInterface",
    "PluginInterface",
    
    # System interfaces
    "MonitorInterface",
    "SecurityInterface",
    "ConfigInterface",
    "RegistryInterface",
    "LifecycleInterface",
]
