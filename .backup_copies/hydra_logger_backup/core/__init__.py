"""
Hydra-Logger Core System Components

This module provides the foundational components that power the entire Hydra-Logger system.
It contains the core infrastructure, base classes, exception hierarchy, and essential utilities
that all other modules depend on.

ARCHITECTURE:
- Constants & Enums: System-wide constants, color codes, log levels, queue policies
- Exception Hierarchy: Comprehensive error handling with detailed context
- Base Classes: Abstract base classes for all system components
- Cache Management: High-performance caching for handlers and formatters
- Layer Management: Intelligent layer-based logging organization
- Object Pooling: Memory-efficient LogRecord instance pooling
- Performance Optimization: Compiled logging paths and JIT optimizations
- Memory Management: Advanced memory optimization and GC tuning
- Component Composition: Trait-based component composition system
- Lifecycle Management: Component state and lifecycle tracking
- Validation System: Input validation and configuration checking
- Parallel Processing: Multi-threaded and lock-free logging capabilities
- System Optimization: OS-level optimizations for maximum performance

FEATURES:
- Thread-safe operations throughout
- Memory-efficient object pooling
- Intelligent caching with fallback strategies
- Performance monitoring and optimization
- Comprehensive error handling
- Extensible component architecture
- Zero-allocation patterns where possible
- System-level optimizations

USAGE EXAMPLES:

Basic Core Usage:
    from hydra_logger.core import Colors, LogLevel, CacheManager
    
    # Use color constants
    print(Colors.RED + "Error message" + Colors.RESET)
    
    # Use log levels
    level = LogLevel.INFO
    
    # Use cache manager
    cache = CacheManager()

Component Composition:
    from hydra_logger.core import ComponentComposer, BaseComponent
    
    composer = ComponentComposer()
    # Register and compose components

Object Pooling:
    from hydra_logger.core import get_log_record_pool
    
    pool = get_log_record_pool("my_pool")
    record = pool.get_record()
    # Use record...
    pool.return_record(record)

Performance Optimization:
    from hydra_logger.core import get_compiled_engine, get_memory_optimizer
    
    engine = get_compiled_engine()
    optimizer = get_memory_optimizer()
"""

from .constants import Colors, QueuePolicy, ShutdownPhase
from ..types.levels import LogLevel
from .layer_manager import LayerManager, LayerConfiguration
from .exceptions import (
    HydraLoggerError, ConfigurationError, ValidationError,
    HandlerError, FormatterError, PluginError, SecurityError, MonitoringError
)

__all__ = [
    # Constants
    "Colors",
    "LogLevel",
    "QueuePolicy",
    "ShutdownPhase",
    
    # Layer Management
    "LayerManager",
    "LayerConfiguration",
    
    # Exceptions
    "HydraLoggerError",
    "ConfigurationError",
    "ValidationError",
    "HandlerError",
    "FormatterError",
    "PluginError",
    "SecurityError",
    "MonitoringError"
]
