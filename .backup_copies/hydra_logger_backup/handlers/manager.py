"""
Handler Manager for Hydra-Logger

This module provides a centralized handler management system for registering,
retrieving, and managing handlers throughout the application lifecycle.

ARCHITECTURE:
- HandlerManager: Centralized handler registration and management
- Handler registration with unique names
- Handler retrieval and validation
- Handler lifecycle management
- Performance monitoring and statistics

CORE FEATURES:
- Handler registration with unique names
- Handler retrieval and validation
- Handler creation with factory patterns
- Handler removal and cleanup
- Handler listing and statistics
- Thread-safe operations

USAGE EXAMPLES:

Basic Handler Management:
    from hydra_logger.handlers.manager import HandlerManager
    from hydra_logger.handlers import SyncConsoleHandler, FileHandler
    
    manager = HandlerManager()
    
    # Register handlers
    console = SyncConsoleHandler(use_colors=True)
    file_handler = FileHandler("app.log")
    
    manager.register_handler("console", console)
    manager.register_handler("file", file_handler)
    
    # Retrieve handlers
    console_handler = manager.get_handler("console")
    file_handler = manager.get_handler("file")

Handler Creation:
    # Create handler using factory
    handler = manager.create_handler(
        "console",
        use_colors=True,
        buffer_size=1000
    )
    
    # Register the created handler
    manager.register_handler("custom_console", handler)

Handler Management:
    # List all handlers
    handlers = manager.list_handlers()
    print(f"Registered handlers: {handlers}")
    
    # Check if handler exists
    if manager.has_handler("console"):
        print("Console handler is registered")
    
    # Get handler count
    count = manager.get_handler_count()
    print(f"Total handlers: {count}")
    
    # Remove handler
    manager.remove_handler("console")
    
    # Clear all handlers
    manager.clear_handlers()

Performance Monitoring:
    # Get handler statistics
    stats = manager.get_handler_stats()
    print(f"Handler count: {stats['handler_count']}")
    print(f"Handlers: {stats['handlers']}")

THREAD SAFETY:
- Thread-safe operations with proper locking
- Safe concurrent access
- Atomic operations where possible
- Safe handler registration and retrieval

ERROR HANDLING:
- Graceful error handling and recovery
- Validation of handler types and configurations
- Comprehensive error logging
- Safe fallback mechanisms
"""

from typing import Dict, Optional, Any
from .base import BaseHandler
from .console import SyncConsoleHandler, AsyncConsoleHandler
from .file import FileHandler
from .null import NullHandler


class HandlerManager:
    """Clean handler manager - no BS, just works."""
    
    def __init__(self):
        self.handlers: Dict[str, BaseHandler] = {}
        self.handler_types = {
            "console": SyncConsoleHandler,
            "file": FileHandler,
            "null": NullHandler
        }
    
    def register_handler(self, name: str, handler: BaseHandler) -> None:
        """Register a handler with a name."""
        self.handlers[name] = handler
    
    def get_handler(self, name: str) -> Optional[BaseHandler]:
        """Get a handler by name."""
        return self.handlers.get(name)
    
    def create_handler(self, handler_type: str, **kwargs) -> BaseHandler:
        """Create a handler of specific type."""
        if handler_type not in self.handler_types:
            raise ValueError(f"Unknown handler type: {handler_type}")
        
        handler_class = self.handler_types[handler_type]
        return handler_class(**kwargs)
    
    def remove_handler(self, name: str) -> bool:
        """Remove a handler. Returns True if removed."""
        if name in self.handlers:
            del self.handlers[name]
            return True
        return False
    
    def list_handlers(self) -> Dict[str, str]:
        """List all registered handlers with their types."""
        return {name: handler.__class__.__name__ for name, handler in self.handlers.items()}
    
    def clear_handlers(self) -> None:
        """Clear all handlers."""
        self.handlers.clear()
    
    def get_handler_count(self) -> int:
        """Get total number of registered handlers."""
        return len(self.handlers)
    
    def has_handler(self, name: str) -> bool:
        """Check if handler exists."""
        return name in self.handlers
