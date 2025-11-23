"""
Log Record Types for Hydra-Logger

This module defines the core LogRecord class and related types
used for representing log entries throughout the system. It provides
optimized record creation with multiple performance profiles and
 batch processing capabilities.

FEATURES:
- LogRecord: Optimized log record with essential fields
- LogRecordBatch: High-performance batch processing
- LogRecordFactory: Factory for creating records with different profiles
- RecordCreationStrategy: Strategy pattern for record creation
- Performance-optimized record creation and processing

LOG RECORD STRUCTURE:
- Essential fields: timestamp, level_name, layer, file_name, function_name, message
- Optional fields: level, logger_name, line_number
- Custom fields: extra data and context information
- Immutable design for performance and thread safety

PERFORMANCE PROFILES:
- MINIMAL: performance, minimal fields
- CONTEXT: Balanced performance with context information
- AUTO_CONTEXT: Convenience with auto-detected context

RECORD CREATION STRATEGIES:
- Minimal: Fastest creation with essential fields only
- Context: Balanced performance with explicit context
- Auto Context: Convenient creation with automatic context detection

BATCH PROCESSING:
- LogRecordBatch: Optimized batch for high-performance processing
- Configurable batch sizes and processing limits
- Efficient memory usage and processing

USAGE:
    from hydra_logger.types import LogRecord, LogRecordBatch, create_log_record

    # Create log record with minimal strategy
    record = create_log_record(
        level="INFO",
        message="Application started",
        strategy="minimal"
    )

    # Create record with context
    record = create_log_record(
        level="ERROR",
        message="Database connection failed",
        strategy="context",
        file_name="database.py",
        function_name="connect",
        line_number=42
    )

    # Create record with auto-detected context
    record = create_log_record(
        level="DEBUG",
        message="Processing user request",
        strategy="auto_context"
    )

    # Batch processing
    batch = LogRecordBatch(max_size=1000)
    batch.add_record(record1)
    batch.add_record(record2)

    if batch.is_full():
        # Process batch
        for record in batch:
            print(record)
        batch.clear()

    # Use record creation strategy
    from hydra_logger.types import RecordCreationStrategy
    strategy = RecordCreationStrategy("minimal")
    record = strategy.create_record("INFO", "Message", logger_name="MyLogger")
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union, List
from datetime import datetime
import time
# import os  # unused


def extract_filename(full_path: str) -> Optional[str]:
    """Extract just the filename from a full path."""
    if not full_path:
        return None
    try:
        # Handle both Unix and Windows paths
        if "/" in full_path:
            return full_path.split("/")[-1]
        elif "\\" in full_path:
            return full_path.split("\\")[-1]
        else:
            # Already just a filename
            return full_path
    except Exception:
        return None


@dataclass(frozen=True)  # Immutable for performance
class LogRecord:
    """
    Optimized log record - minimal fields for performance.

    Field order as requested:
    1. timestamp, 2. level_name, 3. layer, 4. file_name, 5. function_name, 6. message
    """

    # ESSENTIAL FIELDS (in your exact required order)
    timestamp: float = field(default_factory=time.time)
    level_name: str = "INFO"
    layer: str = "default"
    file_name: Optional[str] = None
    function_name: Optional[str] = None
    message: str = ""

    # OPTIONAL FIELDS (user-customizable)
    level: int = 20  # Default to INFO
    logger_name: str = "HydraLogger"
    line_number: Optional[int] = None

    # CUSTOM FIELDS (user-defined)
    extra: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Minimal post-init - no expensive operations."""
        # Only validate essential fields
        if self.message == "":
            raise ValueError("Message cannot be empty")
        if not self.level_name:
            raise ValueError("Level name cannot be empty")

    @property
    def iso_timestamp(self) -> str:
        """Get ISO formatted timestamp."""
        return datetime.fromtimestamp(self.timestamp).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary - respecting your field order."""
        result = {
            "timestamp": self.timestamp,
            "level_name": self.level_name,
            "layer": self.layer,
            "message": self.message,
            "level": self.level,
            "logger_name": self.logger_name,
        }

        # Only add optional fields if they have values (in your order)
        if self.file_name:
            result["file_name"] = self.file_name
        if self.function_name:
            result["function_name"] = self.function_name
        if self.line_number:
            result["line_number"] = self.line_number
        if self.extra:
            result["extra"] = self.extra
        if self.context:
            result["context"] = self.context

        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(self.to_dict(), default=str)

    def __str__(self) -> str:
        """String representation with your exact field order."""
        parts = [f"[{self.iso_timestamp}]", f"[{self.level_name}]", f"[{self.layer}]"]

        if self.file_name:
            parts.append(f"[{self.file_name}]")
        if self.function_name:
            parts.append(f"[{self.function_name}]")

        parts.append(self.message)
        return " ".join(parts)


# Factory for creating LogRecords with different performance profiles
class LogRecordFactory:
    """Factory for creating LogRecords with different performance profiles."""

    @staticmethod
    def create_minimal(
        level_name: str, message: str, layer: str = "default", **kwargs
    ) -> LogRecord:
        """Create minimal record for performance."""
        return LogRecord(
            timestamp=kwargs.get("timestamp", time.time()),
            level_name=level_name,
            layer=layer,
            file_name=kwargs.get("file_name"),
            function_name=kwargs.get("function_name"),
            message=message,
            level=kwargs.get("level", 20),
            logger_name=kwargs.get("logger_name", "HydraLogger"),
            line_number=kwargs.get("line_number"),
            extra=kwargs.get("extra", {}),
        )

    @staticmethod
    def create_with_context(
        level_name: str,
        message: str,
        layer: str = "default",
        file_name: str = None,
        function_name: str = None,
        line_number: int = None,
        **kwargs,
    ) -> LogRecord:
        """Create record with context - balanced performance."""
        # Extract just file_name if full path provided
        if file_name:
            file_name = extract_filename(file_name)

        return LogRecord(
            timestamp=kwargs.get("timestamp", time.time()),
            level_name=level_name,
            layer=layer,
            file_name=file_name,
            function_name=function_name,
            message=message,
            level=kwargs.get("level", 20),
            logger_name=kwargs.get("logger_name", "HydraLogger"),
            line_number=line_number,
            extra=kwargs.get("extra", {}),
        )

    @staticmethod
    def create_with_auto_context(
        level_name: str, message: str, layer: str = "default", **kwargs
    ) -> LogRecord:
        """Create record with auto-detected context - slower but convenient."""
        file_name = None
        function_name = None
        line_number = None

        try:
            import inspect

            frame = inspect.currentframe()
            if not frame:
                frame = None
            
            # Start by skipping this method (create_with_auto_context)
            if frame:
                frame = frame.f_back
            
            # Skip hydra-logger internal frames
            # Stack typically: user_code -> logger.info -> logger.log -> create_log_record -> RecordCreationStrategy._create_with_auto_context -> create_with_auto_context
            max_skips = 15  # Increased safety limit
            skips = 0
            
            while frame and skips < max_skips:
                try:
                    full_filename = frame.f_code.co_filename
                    
                    # FIX: Handle case where full_filename might be None or empty
                    if not full_filename:
                        frame = frame.f_back
                        skips += 1
                        continue
                    
                    # Simple check: if filename contains 'hydra_logger', skip it
                    # This works for both absolute and relative paths
                    if 'hydra_logger' in full_filename or 'hydra-logger' in full_filename.lower():
                        # Still in hydra-logger, skip this frame
                        frame = frame.f_back
                        skips += 1
                        continue
                    else:
                        # Found user's code!
                        file_name = extract_filename(full_filename)
                        line_number = frame.f_lineno
                        function_name = LogRecordFactory._get_enhanced_function_name(frame)
                        break
                except (AttributeError, KeyError) as e:
                    # Frame might not have expected attributes, skip it
                    frame = frame.f_back
                    skips += 1
                    continue
            
        except Exception as e:
            # FIX: Log error instead of silently failing - helps debug frame inspection issues
            # Silent failure - context is optional, but we should at least know if there's a problem
            import sys
            try:
                # Only log to stderr if in debug mode - don't spam production logs
                if hasattr(sys, '_getframe'):
                    # Debug mode - show what went wrong
                    pass  # Silent for now to maintain performance, but can enable for debugging
            except:
                pass

        return LogRecord(
            timestamp=kwargs.get("timestamp", time.time()),
            level_name=level_name,
            layer=layer,
            file_name=file_name,
            function_name=function_name,
            message=message,
            level=kwargs.get("level", 20),
            logger_name=kwargs.get("logger_name", "HydraLogger"),
            line_number=line_number,
            extra=kwargs.get("extra", {}),
        )

    @staticmethod
    def _get_enhanced_function_name(frame) -> str:
        """
        Get function name with class context if available.

        Args:
            frame: The frame object from inspect.currentframe()

        Returns:
            Enhanced function name (e.g., 'ClassName.method_name' or 'function_name')
        """
        try:
            function_name = frame.f_code.co_name

            # Skip special names that we can't improve
            if function_name in [
                "<lambda>",
                "<listcomp>",
                "<dictcomp>",
                "<setcomp>",
                "<genexpr>",
            ]:
                return function_name

            # Try to get class name from the frame's locals
            if "self" in frame.f_locals:
                class_name = frame.f_locals["self"].__class__.__name__
                return f"{class_name}.{function_name}"
            elif "cls" in frame.f_locals:
                class_name = frame.f_locals["cls"].__name__
                return f"{class_name}.{function_name}"
            else:
                # Check if this is a method by looking at the frame's code object
                # This handles cases where self/cls might not be in locals
                if hasattr(frame.f_code, "co_varnames") and frame.f_code.co_varnames:
                    first_arg = frame.f_code.co_varnames[0]
                    if first_arg == "self" and "self" in frame.f_locals:
                        class_name = frame.f_locals["self"].__class__.__name__
                        return f"{class_name}.{function_name}"
                    elif first_arg == "cls" and "cls" in frame.f_locals:
                        class_name = frame.f_locals["cls"].__name__
                        return f"{class_name}.{function_name}"

                return function_name

        except:
            return function_name if "function_name" in locals() else "<unknown>"


@dataclass
class LogRecordBatch:
    """Optimized batch for high-performance processing."""

    records: List[LogRecord] = field(default_factory=list)
    max_size: int = 1000

    def add_record(self, record: LogRecord) -> bool:
        """Add record. Returns True if batch is full."""
        self.records.append(record)
        return len(self.records) >= self.max_size

    def is_full(self) -> bool:
        """Check if batch is full."""
        return len(self.records) >= self.max_size

    def clear(self) -> None:
        """Clear all records."""
        self.records.clear()

    def __len__(self) -> int:
        """Get record count."""
        return len(self.records)

    def __iter__(self):
        """Iterate over records."""
        return iter(self.records)


# =============================================================================
# RECORD CREATION STRATEGY
# =============================================================================


class RecordCreationStrategy:
    """
    Strategy for creating LogRecord instances based on performance requirements.

    This provides a standardized way to create LogRecord instances across
    all logger implementations while maintaining optimal performance.
    """

    # Performance profiles
    MINIMAL = "minimal"  # Performance focus, minimal fields
    CONTEXT = "context"  # Balanced performance with context
    AUTO_CONTEXT = "auto_context"  # Convenience with auto-detected context

    def __init__(self, strategy: str = MINIMAL):
        """
        Initialize the record creation strategy.

        Args:
            strategy: Creation strategy (minimal, context, auto_context)
        """
        self.strategy = strategy
        self._level_cache = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
            10: "DEBUG",
            20: "INFO",
            30: "WARNING",
            40: "ERROR",
            50: "CRITICAL",
        }

    def create_record(
        self,
        level: Union[str, int],
        message: str,
        logger_name: str = "HydraLogger",
        **kwargs,
    ) -> LogRecord:
        """
        Create a LogRecord using the configured strategy.

        Args:
            level: Log level (string or numeric)
            message: Log message
            logger_name: Name of the logger
            **kwargs: Additional fields

        Returns:
            LogRecord instance
        """
        # Convert level to string for consistency
        if isinstance(level, int):
            level_name = self._level_cache.get(level, "INFO")
            level_int = level
        else:
            level_name = str(level).upper()
            level_int = self._level_cache.get(level_name, 20)

        # Extract common fields
        layer = kwargs.get("layer", "default")

        # Remove layer from kwargs to avoid duplicate argument
        kwargs_clean = kwargs.copy()
        kwargs_clean.pop("layer", None)

        # Choose creation method based on strategy
        if self.strategy == self.MINIMAL:
            return self._create_minimal(
                level_name, message, layer, level_int, logger_name, **kwargs_clean
            )
        elif self.strategy == self.CONTEXT:
            return self._create_with_context(
                level_name, message, layer, level_int, logger_name, **kwargs_clean
            )
        elif self.strategy == self.AUTO_CONTEXT:
            return self._create_with_auto_context(
                level_name, message, layer, level_int, logger_name, **kwargs_clean
            )
        else:
            # Fallback to minimal
            return self._create_minimal(
                level_name, message, layer, level_int, logger_name, **kwargs_clean
            )

    def _create_minimal(
        self,
        level_name: str,
        message: str,
        layer: str,
        level_int: int,
        logger_name: str,
        **kwargs,
    ) -> LogRecord:
        """Create minimal record for performance."""
        # Pass additional parameters through kwargs to respect LogRecordFactory signature
        kwargs.update(
            {"level": level_int, "logger_name": logger_name, "timestamp": time.time()}
        )
        return LogRecordFactory.create_minimal(
            level_name=level_name, message=message, layer=layer, **kwargs
        )

    def _create_with_context(
        self,
        level_name: str,
        message: str,
        layer: str,
        level_int: int,
        logger_name: str,
        **kwargs,
    ) -> LogRecord:
        """Create record with explicit context."""
        # Extract context fields to avoid duplicate arguments
        file_name = kwargs.pop("file_name", None)
        function_name = kwargs.pop("function_name", None)
        line_number = kwargs.pop("line_number", None)

        # Pass additional parameters through kwargs to respect LogRecordFactory signature
        kwargs.update(
            {"level": level_int, "logger_name": logger_name, "timestamp": time.time()}
        )
        return LogRecordFactory.create_with_context(
            level_name=level_name,
            message=message,
            layer=layer,
            file_name=file_name,
            function_name=function_name,
            line_number=line_number,
            **kwargs,
        )

    def _create_with_auto_context(
        self,
        level_name: str,
        message: str,
        layer: str,
        level_int: int,
        logger_name: str,
        **kwargs,
    ) -> LogRecord:
        """Create record with auto-detected context."""
        # Pass additional parameters through kwargs to respect LogRecordFactory signature
        kwargs.update(
            {"level": level_int, "logger_name": logger_name, "timestamp": time.time()}
        )
        return LogRecordFactory.create_with_auto_context(
            level_name=level_name, message=message, layer=layer, **kwargs
        )


# =============================================================================
# GLOBAL STRATEGY INSTANCES AND CONVENIENCE FUNCTIONS
# =============================================================================

# Global strategy instances for different performance profiles
MINIMAL_STRATEGY = RecordCreationStrategy(RecordCreationStrategy.MINIMAL)
CONTEXT_STRATEGY = RecordCreationStrategy(RecordCreationStrategy.CONTEXT)
AUTO_CONTEXT_STRATEGY = RecordCreationStrategy(RecordCreationStrategy.AUTO_CONTEXT)


def get_record_creation_strategy(
    performance_profile: str = "minimal",
) -> RecordCreationStrategy:
    """
    Get a record creation strategy based on performance profile.

    Args:
        performance_profile: Performance profile (minimal, balanced, convenient)

    Returns:
        RecordCreationStrategy instance
    """
    if performance_profile == "minimal":
        return MINIMAL_STRATEGY
    elif performance_profile == "balanced":
        return CONTEXT_STRATEGY
    elif performance_profile == "convenient":
        return AUTO_CONTEXT_STRATEGY
    else:
        return MINIMAL_STRATEGY


def create_log_record(
    level: Union[str, int], message: str, strategy: str = "minimal", **kwargs
) -> LogRecord:
    """
    Convenience function to create a LogRecord with specified strategy.

    Args:
        level: Log level (string or numeric)
        message: Log message
        strategy: Creation strategy (minimal, context, auto_context)
        **kwargs: Additional fields

    Returns:
        LogRecord instance
    """
    creation_strategy = get_record_creation_strategy(strategy)
    return creation_strategy.create_record(level, message, **kwargs)
