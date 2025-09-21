"""
Data models for benchmark results and configuration.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    
    # Test identification
    test_name: str
    logger_type: str
    
    # Performance metrics
    iterations: int
    total_time: float
    messages_per_second: float
    avg_time_per_message: float
    
    # Memory metrics
    memory_start_mb: float
    memory_end_mb: float
    memory_delta_mb: float
    
    # Output validation
    format_type: str
    destination_type: str
    file_created: bool = False
    file_size_bytes: int = 0
    lines_written: int = 0
    
    # Error tracking
    errors_occurred: bool = False
    error_count: int = 0
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'test_name': self.test_name,
            'logger_type': self.logger_type,
            'iterations': self.iterations,
            'total_time': self.total_time,
            'messages_per_second': self.messages_per_second,
            'avg_time_per_message': self.avg_time_per_message,
            'memory_start_mb': self.memory_start_mb,
            'memory_end_mb': self.memory_end_mb,
            'memory_delta_mb': self.memory_delta_mb,
            'format_type': self.format_type,
            'destination_type': self.destination_type,
            'file_created': self.file_created,
            'file_size_bytes': self.file_size_bytes,
            'lines_written': self.lines_written,
            'errors_occurred': self.errors_occurred,
            'error_count': self.error_count,
            'metadata': self.metadata or {}
        }


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests."""
    
    # Test parameters
    iterations: int = 50000
    warmup_iterations: int = 100
    
    # Logger configuration
    logger_name: str = "TestLogger"
    logger_kwargs: Optional[Dict[str, Any]] = None
    
    # Output configuration
    output_dir: str = "benchmarks/_results"
    logs_dir: str = "benchmarks/_logs"
    
    # Performance settings
    enable_memory_measurement: bool = True
    enable_file_validation: bool = True
    
    # Validation settings
    validate_output: bool = True
    check_file_creation: bool = True
    check_line_count: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'iterations': self.iterations,
            'warmup_iterations': self.warmup_iterations,
            'logger_name': self.logger_name,
            'logger_kwargs': self.logger_kwargs or {},
            'output_dir': self.output_dir,
            'logs_dir': self.logs_dir,
            'enable_memory_measurement': self.enable_memory_measurement,
            'enable_file_validation': self.enable_file_validation,
            'validate_output': self.validate_output,
            'check_file_creation': self.check_file_creation,
            'check_line_count': self.check_line_count
        }
