"""
Validation utilities for benchmark results.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def validate_file_output(file_path: str, expected_lines: int = None) -> Dict[str, Any]:
    """Validate that a log file was created and contains expected content."""
    result = {
        'file_exists': False,
        'file_size_bytes': 0,
        'lines_written': 0,
        'is_valid': False,
        'errors': []
    }
    
    try:
        file_path_obj = Path(file_path)
        
        # Check if file exists
        if not file_path_obj.exists():
            result['errors'].append(f"File does not exist: {file_path}")
            return result
        
        result['file_exists'] = True
        result['file_size_bytes'] = file_path_obj.stat().st_size
        
        # Count lines
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                result['lines_written'] = sum(1 for _ in f)
        except UnicodeDecodeError:
            # For binary files, estimate based on file size
            result['lines_written'] = max(1, result['file_size_bytes'] // 100)
        
        # Validate line count if expected
        if expected_lines is not None:
            if result['lines_written'] < expected_lines * 0.9:  # Allow 10% tolerance
                result['errors'].append(f"Expected ~{expected_lines} lines, got {result['lines_written']}")
            else:
                result['is_valid'] = True
        else:
            result['is_valid'] = True
            
    except Exception as e:
        result['errors'].append(f"Validation error: {str(e)}")
    
    return result


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate benchmark configuration."""
    result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Required fields
    required_fields = ['iterations', 'logger_name']
    for field in required_fields:
        if field not in config:
            result['errors'].append(f"Missing required field: {field}")
            result['is_valid'] = False
    
    # Validate iterations
    if 'iterations' in config:
        iterations = config['iterations']
        if not isinstance(iterations, int) or iterations <= 0:
            result['errors'].append("iterations must be a positive integer")
            result['is_valid'] = False
        elif iterations > 1000000:
            result['warnings'].append("Very high iteration count may cause performance issues")
    
    # Validate logger name
    if 'logger_name' in config:
        logger_name = config['logger_name']
        if not isinstance(logger_name, str) or not logger_name.strip():
            result['errors'].append("logger_name must be a non-empty string")
            result['is_valid'] = False
    
    return result


def validate_benchmark_environment() -> Dict[str, Any]:
    """Validate that the benchmark environment is properly set up."""
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check if we can import required modules
    try:
        import psutil
    except ImportError:
        result['errors'].append("psutil module not available for memory measurement")
        result['valid'] = False
    
    # Check if we can create directories
    try:
        results_dir = Path("benchmarks/_results")
        logs_dir = Path("benchmarks/_logs")
        
        results_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)
        
        # Test write permissions
        test_file = results_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        
    except Exception as e:
        result['errors'].append(f"Cannot create benchmark directories: {str(e)}")
        result['valid'] = False
    
    # Check available memory
    try:
        import psutil
        available_memory = psutil.virtual_memory().available / 1024 / 1024 / 1024  # GB
        if available_memory < 1.0:
            result['warnings'].append(f"Low available memory: {available_memory:.1f}GB")
    except Exception:
        pass
    
    return result


def validate_benchmark_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a benchmark result for consistency."""
    validation = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check required fields
    required_fields = ['test_name', 'logger_type', 'iterations', 'total_time', 'messages_per_second']
    for field in required_fields:
        if field not in result:
            validation['errors'].append(f"Missing required field: {field}")
            validation['is_valid'] = False
    
    # Validate performance metrics
    if 'iterations' in result and 'total_time' in result:
        iterations = result['iterations']
        total_time = result['total_time']
        
        if iterations <= 0:
            validation['errors'].append("iterations must be positive")
            validation['is_valid'] = False
        
        if total_time < 0:
            validation['errors'].append("total_time must be non-negative")
            validation['is_valid'] = False
        
        if total_time > 0 and 'messages_per_second' in result:
            expected_mps = iterations / total_time
            actual_mps = result['messages_per_second']
            tolerance = 0.01  # 1% tolerance
            
            if abs(expected_mps - actual_mps) / expected_mps > tolerance:
                validation['warnings'].append(f"messages_per_second calculation may be incorrect: expected {expected_mps:.2f}, got {actual_mps:.2f}")
    
    # Check for suspicious values
    if 'messages_per_second' in result:
        mps = result['messages_per_second']
        if mps > 10000000:  # 10M msg/s is suspiciously high
            validation['warnings'].append(f"Very high messages_per_second: {mps:,.0f} (may indicate measurement error)")
        elif mps < 1:
            validation['warnings'].append(f"Very low messages_per_second: {mps:.2f}")
    
    return validation
