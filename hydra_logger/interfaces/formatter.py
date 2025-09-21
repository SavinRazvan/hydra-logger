"""
Formatter Interface for Hydra-Logger

This module defines the abstract interface that all formatter implementations
must follow, ensuring consistent behavior across different output formats.
It provides a standardized contract for formatting log records.

ARCHITECTURE:
- FormatterInterface: Abstract interface for all formatter implementations
- Defines contract for log record formatting and validation
- Ensures consistent behavior across different output formats
- Supports structured and streaming output formats

CORE FEATURES:
- Log record formatting with consistent API
- Format type identification and validation
- Structured output support detection
- Streaming output capability detection
- Record validation and field support
- Configuration and initialization management

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import FormatterInterface
    from hydra_logger.types.records import LogRecord
    from typing import Any, Dict, List
    
    class JSONFormatter(FormatterInterface):
        def __init__(self):
            self._initialized = True
            self._config = {"format_type": "json"}
        
        def format(self, record: LogRecord) -> str:
            import json
            return json.dumps({
                "timestamp": record.timestamp,
                "level": record.levelname,
                "message": record.message,
                "logger": record.logger_name
            })
        
        def get_format_name(self) -> str:
            return "json"
        
        def is_initialized(self) -> bool:
            return self._initialized
        
        def get_config(self) -> Dict[str, Any]:
            return self._config.copy()
        
        def get_format_type(self) -> str:
            return "json"
        
        def is_structured(self) -> bool:
            return True
        
        def supports_streaming(self) -> bool:
            return True
        
        def get_supported_fields(self) -> List[str]:
            return ["timestamp", "level", "message", "logger", "file_name", "line_number"]
        
        def validate_record(self, record: LogRecord) -> bool:
            return hasattr(record, 'message') and record.message is not None

Formatter Usage:
    from hydra_logger.interfaces import FormatterInterface
    from hydra_logger.types.records import LogRecord
    
    def process_formatter(formatter: FormatterInterface, record: LogRecord):
        \"\"\"Process a log record using any formatter that implements FormatterInterface.\"\"\"
        if formatter.is_initialized():
            if formatter.validate_record(record):
                formatted = formatter.format(record)
                print(f"Formatted: {formatted}")
            else:
                print("Record validation failed")
        else:
            print("Formatter not initialized")

Polymorphic Usage:
    from hydra_logger.interfaces import FormatterInterface
    
    def process_formatters(formatters: List[FormatterInterface], record: LogRecord):
        \"\"\"Process record with multiple formatters.\"\"\"
        for formatter in formatters:
            if formatter.is_initialized() and formatter.validate_record(record):
                formatted = formatter.format(record)
                print(f"{formatter.get_format_name()}: {formatted}")

Format Type Detection:
    from hydra_logger.interfaces import FormatterInterface
    
    def categorize_formatters(formatters: List[FormatterInterface]):
        \"\"\"Categorize formatters by type and capabilities.\"\"\"
        structured = []
        streaming = []
        
        for formatter in formatters:
            if formatter.is_structured():
                structured.append(formatter)
            if formatter.supports_streaming():
                streaming.append(formatter)
        
        return structured, streaming

INTERFACE CONTRACTS:
- format(): Format a log record into string representation
- get_format_name(): Get formatter name for identification
- is_initialized(): Check if formatter is properly initialized
- get_config(): Get formatter configuration
- get_format_type(): Get the format type string
- is_structured(): Check if formatter produces structured output
- supports_streaming(): Check if formatter supports streaming output
- get_supported_fields(): Get list of supported record fields
- validate_record(): Validate if record can be formatted

ERROR HANDLING:
- All methods include proper error handling
- Record validation prevents formatting errors
- Initialization checks ensure proper state
- Clear error messages and status reporting

BENEFITS:
- Consistent formatting API across implementations
- Easy testing with mock formatters
- Clear contracts for custom formatters
- Polymorphic usage without tight coupling
- Better format type detection and validation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from ..types.records import LogRecord


class FormatterInterface(ABC):
    """
    Abstract interface for all formatter implementations.
    
    This interface defines the contract that all formatters must implement,
    ensuring consistent behavior across different output formats.
    """
    
    @abstractmethod
    def format(self, record: LogRecord) -> str:
        """
        Format a log record.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted string representation
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_format_name(self) -> str:
        """
        Get formatter name.
        
        Returns:
            Formatter name
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if formatter is properly initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get formatter configuration.
        
        Returns:
            Configuration dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_format_type(self) -> str:
        """
        Get the format type.
        
        Returns:
            Format type string
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_structured(self) -> bool:
        """
        Check if formatter produces structured output.
        
        Returns:
            True if structured, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Check if formatter supports streaming output.
        
        Returns:
            True if streaming supported, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_supported_fields(self) -> List[str]:
        """
        Get list of supported record fields.
        
        Returns:
            List of supported field names
        """
        raise NotImplementedError
    
    @abstractmethod
    def validate_record(self, record: LogRecord) -> bool:
        """
        Validate if record can be formatted by this formatter.
        
        Args:
            record: Log record to validate
            
        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError
