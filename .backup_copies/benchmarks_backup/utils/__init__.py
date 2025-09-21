"""
Benchmark utilities for Hydra-Logger

This module provides utility functions and classes for benchmarking
logger implementations.
"""

from .models import BenchmarkResult, BenchmarkConfig
from .performance import measure_memory, calculate_performance_metrics, analyze_results
from .validation import validate_file_output, validate_config, validate_benchmark_environment
from .constants import RESULTS_DIR, LOGS_DIR, DEFAULT_ITERATIONS, DEFAULT_WARMUP_ITERATIONS

__all__ = [
    'BenchmarkResult',
    'BenchmarkConfig', 
    'measure_memory',
    'calculate_performance_metrics',
    'analyze_results',
    'validate_file_output',
    'validate_config',
    'validate_benchmark_environment',
    'RESULTS_DIR',
    'LOGS_DIR',
    'DEFAULT_ITERATIONS',
    'DEFAULT_WARMUP_ITERATIONS'
]
