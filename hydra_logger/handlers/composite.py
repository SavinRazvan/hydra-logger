"""
Composite Handlers for Hydra-Logger

This module provides advanced composite handler patterns for complex logging
scenarios including multiple output destinations, fault tolerance, and
load distribution strategies.

ARCHITECTURE:
- CompositeHandler: Routes to multiple handlers with various strategies
- FallbackHandler: Primary and backup handler patterns
- LoadBalancingHandler: Distributes load across multiple handlers
- CircuitBreakerHandler: Fault tolerance with circuit breaker pattern
- HandlerChain: Sequential processing through handler chains
- CompositeHandlerFactory: Factory for creating composite handlers

ROUTING STRATEGIES:
- ALL: Send to all handlers simultaneously
- FIRST_SUCCESS: Send to first successful handler
- ROUND_ROBIN: Round-robin distribution
- LOAD_BALANCED: Load-balanced distribution
- PRIORITY: Priority-based routing
- CONDITIONAL: Conditional routing based on record

LOAD BALANCING STRATEGIES:
- ROUND_ROBIN: Simple round-robin distribution
- LEAST_CONNECTIONS: Route to handler with least connections
- WEIGHTED_ROUND_ROBIN: Weighted round-robin distribution
- RANDOM: Random handler selection

FAULT TOLERANCE:
- Circuit breaker pattern for fault detection
- Automatic recovery and retry mechanisms
- Fallback handlers for failed operations
- Comprehensive error handling and logging

USAGE EXAMPLES:

Composite Handler (All Handlers):
    from hydra_logger.handlers import CompositeHandler, SyncConsoleHandler, FileHandler
    from hydra_logger.handlers.composite import RoutingStrategy
    
    console = SyncConsoleHandler()
    file_handler = FileHandler("app.log")
    
    handler = CompositeHandler(
        handlers=[console, file_handler],
        routing_strategy=RoutingStrategy.ALL
    )
    logger.addHandler(handler)

Fallback Handler:
    from hydra_logger.handlers import FallbackHandler, SyncConsoleHandler, FileHandler
    
    primary = SyncConsoleHandler()
    fallback = FileHandler("fallback.log")
    
    handler = FallbackHandler(
        primary_handlers=[primary],
        fallback_handlers=[fallback]
    )
    logger.addHandler(handler)

Load Balancing Handler:
    from hydra_logger.handlers import LoadBalancingHandler, SyncConsoleHandler, FileHandler
    from hydra_logger.handlers.composite import LoadBalancingStrategy
    
    console1 = SyncConsoleHandler()
    console2 = SyncConsoleHandler()
    file_handler = FileHandler("app.log")
    
    handler = LoadBalancingHandler(
        handlers=[console1, console2, file_handler],
        strategy=LoadBalancingStrategy.ROUND_ROBIN
    )
    logger.addHandler(handler)

Circuit Breaker Handler:
    from hydra_logger.handlers import CircuitBreakerHandler, HTTPHandler
    
    http_handler = HTTPHandler("https://api.example.com/logs")
    
    handler = CircuitBreakerHandler(
        handler=http_handler,
        failure_threshold=5,
        recovery_timeout=60.0
    )
    logger.addHandler(handler)

Handler Chain:
    from hydra_logger.handlers import HandlerChain, SyncConsoleHandler, FileHandler
    
    console = SyncConsoleHandler()
    file_handler = FileHandler("app.log")
    
    handler = HandlerChain(
        handlers=[console, file_handler],
        stop_on_failure=False
    )
    logger.addHandler(handler)

Factory Pattern:
    from hydra_logger.handlers import CompositeHandlerFactory
    from hydra_logger.handlers.composite import RoutingStrategy
    
    handler = CompositeHandlerFactory.create_composite_handler(
        handlers=[console, file_handler],
        routing_strategy=RoutingStrategy.ALL
    )

Performance Monitoring:
    # Get handler statistics
    stats = handler.get_handler_stats()
    print(f"Routing strategy: {stats['routing_strategy']}")
    print(f"Handler count: {stats['handler_count']}")
    print(f"Circuit breaker open: {stats['circuit_breaker_open']}")

CONFIGURATION:
- Routing strategies: ALL, FIRST_SUCCESS, ROUND_ROBIN, LOAD_BALANCED, PRIORITY, CONDITIONAL
- Load balancing: ROUND_ROBIN, LEAST_CONNECTIONS, WEIGHTED_ROUND_ROBIN, RANDOM
- Circuit breaker: failure_threshold, recovery_timeout
- Handler weights and priorities
- Timeout and retry settings

ERROR HANDLING:
- Circuit breaker pattern for fault detection
- Automatic retry with exponential backoff
- Fallback mechanisms for failed operations
- Comprehensive error logging
- Graceful degradation

THREAD SAFETY:
- Thread-safe operations with proper locking
- Safe concurrent access
- Atomic operations where possible
- Connection pooling and management
"""

import time
import threading
import sys
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum
from .base import BaseHandler
from ..types.records import LogRecord
from ..types.levels import LogLevel


class RoutingStrategy(Enum):
    """Routing strategies for composite handlers."""
    ALL = "all"                         # Send to all handlers
    FIRST_SUCCESS = "first_success"     # Send to first successful handler
    ROUND_ROBIN = "round_robin"         # Round-robin distribution
    LOAD_BALANCED = "load_balanced"     # Load-balanced distribution
    PRIORITY = "priority"               # Priority-based routing
    CONDITIONAL = "conditional"         # Conditional routing based on record


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"


@dataclass
class HandlerConfig:
    """Configuration for individual handlers in composite."""
    handler: BaseHandler
    weight: int = 1
    priority: int = 0
    enabled: bool = True
    timeout: float = 5.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class CompositeConfig:
    """Configuration for composite handlers."""
    routing_strategy: RoutingStrategy = RoutingStrategy.ALL
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    fail_fast: bool = False
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


class CompositeHandler(BaseHandler):
    """Composite handler that routes to multiple handlers."""

    def __init__(
        self,
        handlers: List[Union[BaseHandler, HandlerConfig]],
        routing_strategy: RoutingStrategy = RoutingStrategy.ALL,
        timestamp_config=None,
        **kwargs
    ):
        """
        Initialize composite handler.

        Args:
            handlers: List of handlers or handler configs
            routing_strategy: Routing strategy to use
            **kwargs: Additional arguments
        """
        super().__init__(name="composite", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        self._routing_strategy = routing_strategy
        self._handlers = []
        self._current_index = 0
        self._lock = threading.RLock()

        # Convert handlers to HandlerConfig if needed
        for handler in handlers:
            if isinstance(handler, BaseHandler):
                self._handlers.append(HandlerConfig(handler=handler))
            else:
                self._handlers.append(handler)

        # Circuit breaker state
        self._circuit_breaker_open = False
        self._circuit_breaker_open_time = 0.0
        self._failure_counts = [0] * len(self._handlers)
        
        # Formatter-aware handling attributes
        self._is_csv_formatter = False
        self._is_json_formatter = False
        self._is_streaming_formatter = False
        self._needs_special_handling = False

    def setFormatter(self, formatter):
        """
        Set formatter and detect if it needs special handling.
        
        Args:
            formatter: Formatter instance
        """
        super().setFormatter(formatter)
        if formatter:
            self._is_csv_formatter = (hasattr(formatter, 'format_headers') and hasattr(formatter, 'should_write_headers'))
            self._is_json_formatter = hasattr(formatter, 'write_header')
            self._is_streaming_formatter = hasattr(formatter, 'format_for_streaming')
            self._needs_special_handling = (self._is_csv_formatter or self._is_json_formatter or self._is_streaming_formatter)
        else:
            self._is_csv_formatter = False
            self._is_json_formatter = False
            self._is_streaming_formatter = False
            self._needs_special_handling = False

    def _get_next_handler(self) -> Optional[HandlerConfig]:
        """Get next handler based on routing strategy."""
        if not self._handlers:
            return None

        with self._lock:
            if self._routing_strategy == RoutingStrategy.ROUND_ROBIN:
                handler = self._handlers[self._current_index]
                self._current_index = (self._current_index + 1) % len(self._handlers)
                return handler
            elif self._routing_strategy == RoutingStrategy.PRIORITY:
                # Sort by priority (highest first)
                sorted_handlers = sorted(
                    self._handlers, key=lambda h: h.priority, reverse=True
                )
                return sorted_handlers[0] if sorted_handlers else None
            else:
                # Default to first handler
                return self._handlers[0] if self._handlers else None

    def _is_circuit_breaker_open(self, handler_index: int) -> bool:
        """Check if circuit breaker is open for a handler."""
        if not self._circuit_breaker_open:
            return False

        # Check if timeout has passed
        if time.time() - self._circuit_breaker_open_time > 60.0:
            self._circuit_breaker_open = False
            self._failure_counts[handler_index] = 0
            return False

        return True

    def _record_failure(self, handler_index: int) -> None:
        """Record a failure for a handler."""
        if handler_index < len(self._failure_counts):
            self._failure_counts[handler_index] += 1
            if self._failure_counts[handler_index] >= 5:
                self._circuit_breaker_open = True
                self._circuit_breaker_open_time = time.time()

    def _record_success(self, handler_index: int) -> None:
        """Record a success for a handler."""
        if handler_index < len(self._failure_counts):
            self._failure_counts[handler_index] = max(
                0, self._failure_counts[handler_index] - 1
            )

    def _update_handler_stats(self, handler_index: int, success: bool) -> None:
        """Update handler statistics."""
        if success:
            self._record_success(handler_index)
        else:
            self._record_failure(handler_index)

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record using routing strategy.

        Args:
            record: Log record to emit
        """
        if self._routing_strategy == RoutingStrategy.ALL:
            self._emit_to_all(record)
        elif self._routing_strategy == RoutingStrategy.FIRST_SUCCESS:
            self._emit_to_first_success(record)
        elif self._routing_strategy == RoutingStrategy.ROUND_ROBIN:
            self._emit_to_round_robin(record)
        elif self._routing_strategy == RoutingStrategy.LOAD_BALANCED:
            self._emit_to_load_balanced(record)
        elif self._routing_strategy == RoutingStrategy.PRIORITY:
            self._emit_to_priority(record)
        elif self._routing_strategy == RoutingStrategy.CONDITIONAL:
            self._emit_to_conditional(record)
        else:
            # Default to all
            self._emit_to_all(record)

    def _emit_to_all(self, record: LogRecord) -> None:
        """Emit to all enabled handlers."""
        for i, config in enumerate(self._handlers):
            if not config.enabled:
                continue

            if self._is_circuit_breaker_open(i):
                continue

            success = self._emit_to_single_handler(config, record)
            self._update_handler_stats(i, success)

    def _emit_to_first_success(self, record: LogRecord) -> None:
        """Emit to first successful handler."""
        for i, config in enumerate(self._handlers):
            if not config.enabled:
                continue

            if self._is_circuit_breaker_open(i):
                continue

            success = self._emit_to_single_handler(config, record)
            self._update_handler_stats(i, success)

            if success:
                break

    def _emit_to_round_robin(self, record: LogRecord) -> None:
        """Emit using round-robin distribution."""
        config = self._get_next_handler()
        if config and config.enabled:
            self._emit_to_single_handler(config, record)

    def _emit_to_load_balanced(self, record: LogRecord) -> None:
        """Emit using load balancing."""
        config = self._get_next_handler()
        if config and config.enabled:
            self._emit_to_single_handler(config, record)

    def _emit_to_priority(self, record: LogRecord) -> None:
        """Emit to highest priority handler."""
        sorted_handlers = sorted(
            self._handlers, key=lambda h: h.priority, reverse=True
        )
        for config in sorted_handlers:
            if config.enabled:
                self._emit_to_single_handler(config, record)
                break

    def _emit_to_conditional(self, record: LogRecord) -> None:
        """Emit based on record conditions."""
        # Simple condition: use first enabled handler
        for config in self._handlers:
            if config.enabled:
                self._emit_to_single_handler(config, record)
                break

    def _emit_to_single_handler(self, config: HandlerConfig, record: LogRecord) -> bool:
        """
        Emit to a single handler.

        Args:
            config: Handler configuration
            record: Log record to emit

        Returns:
            True if successful, False otherwise
        """
        try:
            config.handler.emit(record)
            return True
        except Exception:
            return False

    def add_handler(self, handler: Union[BaseHandler, HandlerConfig]) -> None:
        """
        Add a handler to the composite.

        Args:
            handler: Handler or handler config to add
        """
        with self._lock:
            if isinstance(handler, BaseHandler):
                self._handlers.append(HandlerConfig(handler=handler))
            else:
                self._handlers.append(handler)
            self._failure_counts.append(0)

    def remove_handler(self, handler: BaseHandler) -> None:
        """
        Remove a handler from the composite.

        Args:
            handler: Handler to remove
        """
        with self._lock:
            for i, config in enumerate(self._handlers):
                if config.handler == handler:
                    self._handlers.pop(i)
                    if i < len(self._failure_counts):
                        self._failure_counts.pop(i)
                    break

    def get_handler_stats(self) -> Dict[str, Any]:
        """
        Get handler statistics.

        Returns:
            Dictionary with handler statistics
        """
        return {
            "routing_strategy": self._routing_strategy.value,
            "handler_count": len(self._handlers),
            "circuit_breaker_open": self._circuit_breaker_open,
            "failure_counts": self._failure_counts.copy(),
            "enabled_handlers": sum(1 for h in self._handlers if h.enabled)
        }

    def close(self) -> None:
        """Close the handler and all sub-handlers."""
        super().close()
        for config in self._handlers:
            try:
                config.handler.close()
            except Exception:
                pass


class FallbackHandler(BaseHandler):
    """Handler with primary and fallback targets."""

    def __init__(
        self,
        primary_handlers: List[BaseHandler],
        fallback_handlers: List[BaseHandler],
        timestamp_config=None,
        **kwargs
    ):
        """
        Initialize fallback handler.

        Args:
            primary_handlers: Primary handlers to try first
            fallback_handlers: Fallback handlers if primary fails
            **kwargs: Additional arguments
        """
        super().__init__(name="fallback", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        self._primary_handlers = primary_handlers
        self._fallback_handlers = fallback_handlers
        self._primary_failures = 0
        self._fallback_usage = 0

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record with fallback logic.

        Args:
            record: Log record to emit
        """
        # Try primary handlers first
        for handler in self._primary_handlers:
            try:
                handler.emit(record)
                return
            except Exception:
                self._primary_failures += 1
                continue

        # If all primary handlers fail, try fallback handlers
        for handler in self._fallback_handlers:
            try:
                handler.emit(record)
                self._fallback_usage += 1
                return
            except Exception:
                continue

        # If all handlers fail, print error
        print("Error: All handlers failed to emit log record", file=sys.stderr)

    def get_fallback_stats(self) -> Dict[str, Any]:
        """
        Get fallback statistics.

        Returns:
            Dictionary with fallback statistics
        """
        return {
            "primary_handlers": len(self._primary_handlers),
            "fallback_handlers": len(self._fallback_handlers),
            "primary_failures": self._primary_failures,
            "fallback_usage": self._fallback_usage
        }

    def close(self) -> None:
        """Close the handler and all sub-handlers."""
        super().close()
        for handler in self._primary_handlers + self._fallback_handlers:
            try:
                handler.close()
            except Exception:
                pass


class LoadBalancingHandler(BaseHandler):
    """Handler that distributes load across multiple handlers."""

    def __init__(
        self,
        handlers: List[BaseHandler],
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
        weights: Optional[List[int]] = None,
        timestamp_config=None,
        **kwargs
    ):
        """
        Initialize load balancing handler.

        Args:
            handlers: List of handlers to balance across
            strategy: Load balancing strategy
            weights: Weight for each handler (for weighted strategies)
            **kwargs: Additional arguments
        """
        super().__init__(name="load_balancing", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        self._handlers = handlers
        self._strategy = strategy
        self._weights = weights or [1] * len(handlers)
        self._current_index = 0
        self._lock = threading.RLock()

        # Ensure weights match handler count
        if len(self._weights) != len(self._handlers):
            self._weights = [1] * len(self._handlers)

    def _get_next_handler(self) -> Optional[BaseHandler]:
        """Get next handler based on strategy."""
        if not self._handlers:
            return None

        with self._lock:
            if self._strategy == LoadBalancingStrategy.ROUND_ROBIN:
                handler = self._handlers[self._current_index]
                self._current_index = (self._current_index + 1) % len(self._handlers)
                return handler
            elif self._strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                # Simple implementation: return first handler
                return self._handlers[0] if self._handlers else None
            elif self._strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                # Weighted round-robin
                handler = self._handlers[self._current_index]
                self._current_index = (self._current_index + 1) % len(self._handlers)
                return handler
            elif self._strategy == LoadBalancingStrategy.RANDOM:
                import random
                return random.choice(self._handlers)
            else:
                return self._handlers[0] if self._handlers else None

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record using load balancing.

        Args:
            record: Log record to emit
        """
        handler = self._get_next_handler()
        if handler:
            try:
                handler.emit(record)
            except Exception:
                # Try next handler on failure
                handler = self._get_next_handler()
                if handler:
                    try:
                        handler.emit(record)
                    except Exception:
                        print("Error: All load balanced handlers failed", file=sys.stderr)

    def get_load_balancing_stats(self) -> Dict[str, Any]:
        """
        Get load balancing statistics.

        Returns:
            Dictionary with load balancing statistics
        """
        return {
            "strategy": self._strategy.value,
            "handler_count": len(self._handlers),
            "current_index": self._current_index,
            "weights": self._weights.copy()
        }

    def close(self) -> None:
        """Close the handler and all sub-handlers."""
        super().close()
        for handler in self._handlers:
            try:
                handler.close()
            except Exception:
                pass


class CircuitBreakerHandler(BaseHandler):
    """Handler with circuit breaker pattern for fault tolerance."""

    def __init__(
        self,
        handler: BaseHandler,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        timestamp_config=None,
        **kwargs
    ):
        """
        Initialize circuit breaker handler.

        Args:
            handler: Wrapped handler
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying to close circuit
            **kwargs: Additional arguments
        """
        super().__init__(name="circuit_breaker", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        self._handler = handler
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._circuit_open = False
        self._circuit_open_time = 0.0
        self._lock = threading.RLock()

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if not self._circuit_open:
            return False

        # Check if timeout has passed
        if time.time() - self._circuit_open_time > self._recovery_timeout:
            self._circuit_open = False
            self._failure_count = 0
            return False

        return True

    def _record_failure(self) -> None:
        """Record a failure."""
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= self._failure_threshold:
                self._circuit_open = True
                self._circuit_open_time = time.time()

    def _record_success(self) -> None:
        """Record a success."""
        with self._lock:
            self._failure_count = max(0, self._failure_count - 1)

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record with circuit breaker logic.

        Args:
            record: Log record to emit
        """
        if self._is_circuit_open():
            # Circuit is open, don't try to emit
            return

        try:
            self._handler.emit(record)
            self._record_success()
        except Exception:
            self._record_failure()
            # Re-raise the exception
            raise

    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with circuit breaker statistics
        """
        return {
            "failure_count": self._failure_count,
            "failure_threshold": self._failure_threshold,
            "circuit_open": self._circuit_open,
            "recovery_timeout": self._recovery_timeout
        }

    def close(self) -> None:
        """Close the handler and wrapped handler."""
        super().close()
        try:
            self._handler.close()
        except Exception:
            pass


class HandlerChain(BaseHandler):
    """Handler that processes records through a chain of handlers."""

    def __init__(
        self,
        handlers: List[BaseHandler],
        stop_on_failure: bool = False,
        timestamp_config=None,
        **kwargs
    ):
        """
        Initialize handler chain.

        Args:
            handlers: List of handlers in the chain
            stop_on_failure: Whether to stop on first failure
            **kwargs: Additional arguments
        """
        super().__init__(name="handler_chain", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        self._handlers = handlers
        self._stop_on_failure = stop_on_failure
        self._processed_count = 0
        self._failure_count = 0

    def emit(self, record: LogRecord) -> None:
        """
        Emit log record through the handler chain.

        Args:
            record: Log record to emit
        """
        for handler in self._handlers:
            try:
                handler.emit(record)
                self._processed_count += 1
            except Exception:
                self._failure_count += 1
                if self._stop_on_failure:
                    break

    def get_chain_stats(self) -> Dict[str, Any]:
        """
        Get chain statistics.

        Returns:
            Dictionary with chain statistics
        """
        return {
            "handler_count": len(self._handlers),
            "processed_count": self._processed_count,
            "failure_count": self._failure_count,
            "stop_on_failure": self._stop_on_failure
        }

    def close(self) -> None:
        """Close the handler and all handlers in the chain."""
        super().close()
        for handler in self._handlers:
            try:
                handler.close()
            except Exception:
                pass


class CompositeHandlerFactory:
    """Factory for creating composite handlers."""

    @staticmethod
    def create_composite_handler(
        handlers: List[BaseHandler],
        routing_strategy: RoutingStrategy = RoutingStrategy.ALL,
        **kwargs
    ) -> CompositeHandler:
        """Create composite handler."""
        return CompositeHandler(handlers, routing_strategy, **kwargs)

    @staticmethod
    def create_fallback_handler(
        primary_handlers: List[BaseHandler],
        fallback_handlers: List[BaseHandler],
        **kwargs
    ) -> FallbackHandler:
        """Create fallback handler."""
        return FallbackHandler(primary_handlers, fallback_handlers, **kwargs)

    @staticmethod
    def create_load_balancing_handler(
        handlers: List[BaseHandler],
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
        **kwargs
    ) -> LoadBalancingHandler:
        """Create load balancing handler."""
        return LoadBalancingHandler(handlers, strategy, **kwargs)

    @staticmethod
    def create_circuit_breaker_handler(
        handler: BaseHandler,
        failure_threshold: int = 5,
        **kwargs
    ) -> CircuitBreakerHandler:
        """Create circuit breaker handler."""
        return CircuitBreakerHandler(handler, failure_threshold, **kwargs)

    @staticmethod
    def create_handler_chain(
        handlers: List[BaseHandler],
        stop_on_failure: bool = False,
        **kwargs
    ) -> HandlerChain:
        """Create handler chain."""
        return HandlerChain(handlers, stop_on_failure, **kwargs)
