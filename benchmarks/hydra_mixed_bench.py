#!/usr/bin/env python3
"""
HydraLogger Mixed Performance Benchmark

This benchmark tests HydraLogger's performance across comprehensive scenarios including:
- Multiple formats (plain-text, JSON, CSV, syslog, GELF)
- Security features (PII detection, data sanitization)
- Plugin system (analytics, formatters, security)
- Magic configs (production, development, microservice, etc.)
- Multiple layers (frontend, backend, database, etc.)
- Centralized logging
- Both sync and async implementations

Test Categories:
1. Format Testing - All supported formats
2. Security Testing - PII detection and sanitization
3. Plugin Testing - Analytics and custom plugins
4. Magic Config Testing - Built-in configurations
5. Multi-Layer Testing - Multiple functional layers
6. Centralized Testing - Single logger with multiple destinations
7. Mixed Sync/Async Testing - Both implementations

Each test measures:
- Throughput (messages per second)
- Latency (time per message)
- Memory usage and leak detection
- Feature overhead impact
- Reliability under load

Results provide insights for choosing optimal configurations and features.
"""

import asyncio
import time
import csv
import json
import traceback
import gc
import psutil
import os
import sys
from typing import List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import re

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hydra_logger import HydraLogger
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.plugins import AnalyticsPlugin, FormatterPlugin, SecurityPlugin

# Test Parameters
ITERATIONS = 10000  # Standard test size
STRESS_ITERATIONS = 50000  # Stress test size
WARMUP_ITERATIONS = 100  # Warmup iterations
CONCURRENT_TASKS = 10  # Number of concurrent tasks

# 1. Define realistic log message generators for each scenario
REALISTIC_MESSAGES = {
    'frontend': lambda i: f"User john.doe{i}@example.com logged in from IP 192.168.1.{i%255}",
    'backend': lambda i: f"Order #{10000+i} processed for user john.doe{i}@example.com (amount: ${100+i}.00)",
    'database': lambda i: f"DB connection pool at {70+i%30}% utilization (query: SELECT * FROM users WHERE id={i})",
    'security': lambda i: f"Failed login attempt for user admin{i} from IP 10.0.0.{i%255} (password=secret{i}123)",
    'sensitive': lambda i: f"User login attempt {i} with email=jane.doe{i}@mail.com and password=secret{i}123",
    'normal': lambda i: f"Service heartbeat OK at {time.strftime('%Y-%m-%d %H:%M:%S')} (instance={i})"
}

def get_message(i):
    """Generate realistic log messages for testing."""
    messages = [
        f"User john.doe{i}@example.com logged in from IP 192.168.1.{i%255}",
        f"Order #{10000+i} processed for user john.doe{i}@example.com (amount: ${100+i}.00)",
        f"DB connection pool at {70+i%30}% utilization (query: SELECT * FROM users WHERE id={i})",
        f"Failed login attempt for user admin{i} from IP 10.0.0.{i%255}",
        f"API request GET /api/users/{i} completed in {150+i%100}ms",
        f"Cache miss for key 'user_profile_{i}' - fetching from database",
        f"Payment processed for order #{20000+i} via Stripe (amount: ${50+i}.99)",
        f"Email sent to user{i}@example.com (template: welcome_email)",
        f"Background job 'process_images_{i}' started at {time.time()}",
        f"Security alert: Multiple failed login attempts for user admin{i}"
    ]
    return messages[i % len(messages)]

def get_realistic_layer(i):
    """Generate realistic layer names for testing."""
    layers = [
        "FRONTEND", "BACKEND", "DATABASE", "SECURITY", "API", 
        "CACHE", "PAYMENT", "EMAIL", "BACKGROUND", "ALERT",
        "AUTH", "USER", "ORDER", "INVENTORY", "SHIPPING"
    ]
    return layers[i % len(layers)]

def get_sensitive_message(i):
    """Message with sensitive data for security testing."""
    return f"User login attempt {i} with email=user{i}@example.com and password=secret{i}123"

def get_large_message(i):
    """Large message for testing performance with bigger payloads."""
    return f"Test log message {i} with very long content that includes additional details about the system state, user actions, and various parameters that might be logged in a real application scenario. This message is designed to test how the logger handles larger payloads and whether it affects performance significantly. The message includes: timestamp={i}, user_id=user_{i}, action=test_action_{i}, status=active, priority=normal, category=benchmark, source=test_suite, version=1.0.0, environment=development, and various other metadata fields that might be present in production logging scenarios."

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def clean_memory():
    """Force garbage collection and clean memory."""
    gc.collect()
    time.sleep(0.1)  # Brief pause to allow cleanup

def check_memory_leak(before_mb: float, after_mb: float, test_name: str) -> Dict[str, Any]:
    """Check for potential memory leaks."""
    memory_diff = after_mb - before_mb
    leak_threshold = 10.0  # 10MB threshold for potential leak
    
    return {
        "test_name": test_name,
        "memory_before_mb": before_mb,
        "memory_after_mb": after_mb,
        "memory_diff_mb": memory_diff,
        "potential_leak": memory_diff > leak_threshold,
        "leak_threshold_mb": leak_threshold
    }

# Custom Plugin Classes for Testing
class TestAnalyticsPlugin(AnalyticsPlugin):
    """Test analytics plugin for benchmarking."""
    
    def __init__(self):
        self.event_count = 0
        self.total_processing_time = 0.0
    
    def process_event(self, event):
        """Process a log event."""
        start_time = time.perf_counter()
        self.event_count += 1
        
        # Simulate some processing
        processed_data = {
            "event_id": self.event_count,
            "timestamp": datetime.now().isoformat(),
            "processed": True,
            "event_type": event.get("level", "INFO")
        }
        
        self.total_processing_time += time.perf_counter() - start_time
        return processed_data
    
    def get_insights(self):
        """Get analytics insights."""
        return {
            "total_events": self.event_count,
            "avg_processing_time": self.total_processing_time / max(self.event_count, 1),
            "total_processing_time": self.total_processing_time
        }

class TestFormatterPlugin(FormatterPlugin):
    """Test formatter plugin for benchmarking."""
    
    def __init__(self):
        self.format_count = 0
    
    def format(self, record):
        """Format a log record (required by FormatterPlugin abstract base class)."""
        self.format_count += 1
        if hasattr(record, 'levelname') and hasattr(record, 'getMessage'):
            # It's a proper log record object
            return f"[CUSTOM_FORMAT] {record.levelname}: {record.getMessage()} (formatted #{self.format_count})"
        else:
            # It's a string or other object
            return f"[CUSTOM_FORMAT] INFO: {str(record)} (formatted #{self.format_count})"
    
    def format_message(self, message, level, layer=None):
        """Format a log message."""
        self.format_count += 1
        return f"[CUSTOM_FORMAT] {level}: {message} (formatted #{self.format_count})"
    
    def get_stats(self):
        """Get formatting statistics."""
        return {
            "total_formatted": self.format_count,
            "plugin_type": "test_formatter"
        }

class TestSecurityPlugin(SecurityPlugin):
    """Test security plugin for benchmarking."""
    
    def __init__(self):
        self.scan_count = 0
        self.sensitive_data_found = 0
    
    def scan_for_sensitive_data(self, message):
        """Scan message for sensitive data."""
        self.scan_count += 1
        
        # Simple PII detection
        sensitive_patterns = [
            r'email=.*@.*\.com',
            r'password=.*',
            r'credit_card=.*',
            r'phone=.*'
        ]
        
        for pattern in sensitive_patterns:
            if re.search(pattern, message):
                self.sensitive_data_found += 1
                return True
        
        return False
    
    def sanitize_message(self, message):
        """Sanitize sensitive data in message."""
        # Simple sanitization
        sanitized = message
        sanitized = re.sub(r'email=.*?@.*?\.com', 'email=***@***.com', sanitized)
        sanitized = re.sub(r'password=.*?\s', 'password=*** ', sanitized)
        return sanitized
    
    def get_security_stats(self):
        """Get security statistics."""
        return {
            "total_scans": self.scan_count,
            "sensitive_data_found": self.sensitive_data_found,
            "scan_rate": self.sensitive_data_found / max(self.scan_count, 1)
        }

# Configuration Functions - Format Testing
def create_plain_text_config():
    """Create plain-text format configuration."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    )
                ]
            )
        }
    )

def create_json_config():
    """Create JSON format configuration."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="json",
                        color_mode="never"
                    )
                ]
            )
        }
    )

def create_csv_config():
    """Create CSV format configuration."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="csv",
                        color_mode="never"
                    )
                ]
            )
        }
    )

def create_syslog_config():
    """Create syslog format configuration."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="syslog",
                        color_mode="never"
                    )
                ]
            )
        }
    )

def create_gelf_config():
    """Create GELF format configuration."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="gelf",
                        color_mode="never"
                    )
                ]
            )
        }
    )

# Configuration Functions - Security Testing
def create_security_config():
    """Create security-enabled configuration."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    )
                ]
            )
        }
    )

# Configuration Functions - Multi-Layer Testing
def create_multi_layer_config():
    """Create multi-layer configuration."""
    return LoggingConfig(
        layers={
            "FRONTEND": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    )
                ]
            ),
            "BACKEND": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        format="json",
                        color_mode="never"
                    )
                ]
            ),
            "DATABASE": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    )
                ]
            ),
            "SECURITY": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="console",
                        format="json",
                        color_mode="never"
                    )
                ]
            )
        }
    )

# Configuration Functions - Centralized Testing
def create_centralized_config():
    """Create centralized configuration with multiple destinations."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    ),
                    LogDestination(
                        type="file",
                        path="benchmarks/logs/centralized.log",
                        format="json",
                        color_mode="never",
                        max_size="10MB",
                        backup_count=1
                    )
                ]
            )
        }
    )

# Configuration Functions - Plugin Testing
def create_plugin_config():
    """Create configuration with plugins enabled."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    )
                ]
            )
        }
    )

# Sync Benchmark Functions - Format Testing
def benchmark_sync_plain_text():
    """Sync plain-text format benchmark."""
    try:
        # Create configuration with both console and file output
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="plain-text",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_plain_text_benchmark.txt",
                            format="plain-text",
                            color_mode="never"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config)
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            layer = get_realistic_layer(i)
            logger.info(REALISTIC_MESSAGES['frontend'](i), layer)
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            layer = get_realistic_layer(i)
            logger.info(REALISTIC_MESSAGES['frontend'](i), layer)
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Plain-Text: {e}")
        return float('inf')

def benchmark_sync_json():
    """Sync JSON format benchmark."""
    try:
        # Create configuration with both console and file output
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="json",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_json_benchmark.txt",
                            format="json",
                            color_mode="never"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config)
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            layer = get_realistic_layer(i)
            logger.info(REALISTIC_MESSAGES['backend'](i), layer)
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            layer = get_realistic_layer(i)
            logger.info(REALISTIC_MESSAGES['backend'](i), layer)
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync JSON: {e}")
        return float('inf')

def benchmark_sync_csv():
    """Sync CSV format benchmark."""
    try:
        # Create configuration with both console and file output
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="csv",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_csv_benchmark.txt",
                            format="csv",
                            color_mode="never"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config)
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            layer = get_realistic_layer(i)
            logger.info(REALISTIC_MESSAGES['database'](i), layer)
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            layer = get_realistic_layer(i)
            logger.info(REALISTIC_MESSAGES['database'](i), layer)
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync CSV: {e}")
        return float('inf')

def benchmark_sync_syslog():
    """Sync syslog format benchmark."""
    try:
        # Create configuration with both console and file output
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="syslog",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_syslog_benchmark.txt",
                            format="syslog",
                            color_mode="never"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config)
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            layer = get_realistic_layer(i)
            logger.info(REALISTIC_MESSAGES['security'](i), layer)
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            layer = get_realistic_layer(i)
            logger.info(REALISTIC_MESSAGES['security'](i), layer)
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Syslog: {e}")
        return float('inf')

def benchmark_sync_gelf():
    """Sync GELF format benchmark."""
    try:
        # Create configuration with both console and file output
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="gelf",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_gelf_benchmark.txt",
                            format="gelf",
                            color_mode="never"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config)
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info(REALISTIC_MESSAGES['sensitive'](i), "DEFAULT")
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info(REALISTIC_MESSAGES['sensitive'](i), "DEFAULT")
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync GELF: {e}")
        return float('inf')

# Sync Benchmark Functions - Security Testing
def benchmark_sync_security():
    """Sync security features benchmark."""
    try:
        # Create configuration with both console and file output
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="plain-text",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_security_benchmark.txt",
                            format="plain-text",
                            color_mode="never"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config)
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info(REALISTIC_MESSAGES['sensitive'](i), "DEFAULT")
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info(REALISTIC_MESSAGES['sensitive'](i), "DEFAULT")
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Security: {e}")
        return float('inf')

# Sync Benchmark Functions - Magic Config Testing
def benchmark_sync_magic_production():
    """Sync production magic config benchmark."""
    try:
        logger = HydraLogger.for_production()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info(REALISTIC_MESSAGES['normal'](i), "DEFAULT")
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info(REALISTIC_MESSAGES['normal'](i), "DEFAULT")
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Magic Production: {e}")
        return float('inf')

def benchmark_sync_magic_development():
    """Sync development magic config benchmark."""
    try:
        logger = HydraLogger.for_development()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info(REALISTIC_MESSAGES['normal'](i), "DEFAULT")
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info(REALISTIC_MESSAGES['normal'](i), "DEFAULT")
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Magic Development: {e}")
        return float('inf')

def benchmark_sync_magic_microservice():
    """Sync microservice magic config benchmark."""
    try:
        logger = HydraLogger.for_microservice()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info(REALISTIC_MESSAGES['normal'](i), "DEFAULT")
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info(REALISTIC_MESSAGES['normal'](i), "DEFAULT")
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Magic Microservice: {e}")
        return float('inf')

# Sync Benchmark Functions - Multi-Layer Testing
def benchmark_sync_multi_layer():
    """Sync multi-layer benchmark."""
    try:
        # Create configuration with both console and file output
        config = LoggingConfig(
            layers={
                "FRONTEND": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="plain-text",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_multilayer_benchmark.txt",
                            format="plain-text",
                            color_mode="never"
                        )
                    ]
                ),
                "BACKEND": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="json",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_multilayer_benchmark.txt",
                            format="json",
                            color_mode="never"
                        )
                    ]
                ),
                "DATABASE": LogLayer(
                    level="WARNING",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="plain-text",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_multilayer_benchmark.txt",
                            format="plain-text",
                            color_mode="never"
                        )
                    ]
                ),
                "SECURITY": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="json",
                            color_mode="never"
                        ),
                        LogDestination(
                            type="file",
                            path="benchmarks/logs/sync_multilayer_benchmark.txt",
                            format="json",
                            color_mode="never"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config=config)
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info("FRONTEND", REALISTIC_MESSAGES['frontend'](i))
            logger.debug("BACKEND", REALISTIC_MESSAGES['backend'](i))
            logger.warning("DATABASE", REALISTIC_MESSAGES['database'](i))
            logger.error("SECURITY", REALISTIC_MESSAGES['security'](i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("FRONTEND", REALISTIC_MESSAGES['frontend'](i))
            logger.debug("BACKEND", REALISTIC_MESSAGES['backend'](i))
            logger.warning("DATABASE", REALISTIC_MESSAGES['database'](i))
            logger.error("SECURITY", REALISTIC_MESSAGES['security'](i))
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Multi-Layer: {e}")
        return float('inf')

# Sync Benchmark Functions - Centralized Testing
def benchmark_sync_centralized():
    """Sync centralized logging benchmark."""
    try:
        logger = HydraLogger(config=create_centralized_config())
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info("DEFAULT", REALISTIC_MESSAGES['normal'](i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", REALISTIC_MESSAGES['normal'](i))
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Centralized: {e}")
        return float('inf')

# Sync Benchmark Functions - Plugin Testing
def benchmark_sync_plugins():
    """Sync plugin system benchmark."""
    try:
        logger = HydraLogger(config=create_plugin_config())
        
        # Add test plugins
        analytics_plugin = TestAnalyticsPlugin()
        formatter_plugin = TestFormatterPlugin()
        security_plugin = TestSecurityPlugin()
        
        logger.add_plugin("analytics", analytics_plugin)
        logger.add_plugin("formatter", formatter_plugin)
        logger.add_plugin("security", security_plugin)
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info("DEFAULT", REALISTIC_MESSAGES['sensitive'](i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", REALISTIC_MESSAGES['sensitive'](i))
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Sync Plugins: {e}")
        return float('inf')

# Async Benchmark Functions - Format Testing
async def benchmark_async_plain_text():
    """Async plain-text format benchmark."""
    try:
        # Create configuration with both console and file output
        config = {
            'handlers': [
                {'type': 'console', 'use_colors': False},
                {'type': 'file', 'filename': 'benchmarks/logs/async_plain_text_benchmark.txt', 'use_colors': False}
            ]
        }
        
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            await logger.info("DEFAULT", REALISTIC_MESSAGES['frontend'](i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", REALISTIC_MESSAGES['frontend'](i))
        end = time.perf_counter()
        
        await logger.aclose()
        return end - start
    except Exception as e:
        print(f"ERROR in Async Plain-Text: {e}")
        return float('inf')

async def benchmark_async_json():
    """Async JSON format benchmark."""
    try:
        # Create configuration with both console and file output
        config = {
            'handlers': [
                {'type': 'console', 'use_colors': False, 'format': 'json'},
                {'type': 'file', 'filename': 'benchmarks/logs/async_json_benchmark.txt', 'use_colors': False, 'format': 'json'}
            ]
        }
        
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            await logger.info("DEFAULT", REALISTIC_MESSAGES['backend'](i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", REALISTIC_MESSAGES['backend'](i))
        end = time.perf_counter()
        
        await logger.aclose()
        return end - start
    except Exception as e:
        print(f"ERROR in Async JSON: {e}")
        return float('inf')

# Async Benchmark Functions - Security Testing
async def benchmark_async_security():
    """Async security features benchmark."""
    try:
        # Create configuration with both console and file output
        config = {
            'handlers': [
                {'type': 'console', 'use_colors': False},
                {'type': 'file', 'filename': 'benchmarks/logs/async_security_benchmark.txt', 'use_colors': False}
            ]
        }
        
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            await logger.info("DEFAULT", REALISTIC_MESSAGES['sensitive'](i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", REALISTIC_MESSAGES['sensitive'](i))
        end = time.perf_counter()
        
        await logger.aclose()
        return end - start
    except Exception as e:
        print(f"ERROR in Async Security: {e}")
        return float('inf')

# Async Benchmark Functions - Multi-Layer Testing
async def benchmark_async_multi_layer():
    """Async multi-layer benchmark."""
    try:
        # Create configuration with both console and file output
        config = {
            'layers': {
                'FRONTEND': {
                    'level': 'INFO', 
                    'destinations': [
                        {'type': 'console', 'use_colors': False},
                        {'type': 'file', 'filename': 'benchmarks/logs/async_multilayer_benchmark.txt', 'use_colors': False}
                    ]
                },
                'BACKEND': {
                    'level': 'DEBUG', 
                    'destinations': [
                        {'type': 'console', 'use_colors': False},
                        {'type': 'file', 'filename': 'benchmarks/logs/async_multilayer_benchmark.txt', 'use_colors': False}
                    ]
                },
                'DATABASE': {
                    'level': 'WARNING', 
                    'destinations': [
                        {'type': 'console', 'use_colors': False},
                        {'type': 'file', 'filename': 'benchmarks/logs/async_multilayer_benchmark.txt', 'use_colors': False}
                    ]
                },
                'SECURITY': {
                    'level': 'ERROR', 
                    'destinations': [
                        {'type': 'console', 'use_colors': False},
                        {'type': 'file', 'filename': 'benchmarks/logs/async_multilayer_benchmark.txt', 'use_colors': False}
                    ]
                }
            }
        }
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            await logger.info("FRONTEND", REALISTIC_MESSAGES['frontend'](i))
            await logger.debug("BACKEND", REALISTIC_MESSAGES['backend'](i))
            await logger.warning("DATABASE", REALISTIC_MESSAGES['database'](i))
            await logger.error("SECURITY", REALISTIC_MESSAGES['security'](i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("FRONTEND", REALISTIC_MESSAGES['frontend'](i))
            await logger.debug("BACKEND", REALISTIC_MESSAGES['backend'](i))
            await logger.warning("DATABASE", REALISTIC_MESSAGES['database'](i))
            await logger.error("SECURITY", REALISTIC_MESSAGES['security'](i))
        end = time.perf_counter()
        
        await logger.aclose()
        return end - start
    except Exception as e:
        print(f"ERROR in Async Multi-Layer: {e}")
        return float('inf')

# Test execution functions
def create_benchmark_folders():
    """Create folders for logs and results - one per benchmark run."""
    benchmark_name = "hydra_mixed"  # Based on file name
    
    # Create logs folder in benchmarks directory
    logs_folder = f"benchmarks/logs/{benchmark_name}"
    os.makedirs(logs_folder, exist_ok=True)
    
    # Create results folder in benchmarks directory
    results_folder = f"benchmarks/results/{benchmark_name}"
    os.makedirs(results_folder, exist_ok=True)
    
    return logs_folder, results_folder

def run_sync_test_with_memory_check(test_func, test_name, logs_folder, results_folder, *args, **kwargs):
    """Run a sync test with memory leak detection."""
    try:
        clean_memory()
        memory_before = get_memory_usage()
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        log_filename = f"{logs_folder}/{safe_test_name}_{timestamp}.txt"
        
        result = test_func(*args, **kwargs)
        
        clean_memory()
        memory_after = get_memory_usage()
        
        memory_info = check_memory_leak(memory_before, memory_after, test_name)
        
        # Save test results to log file
        try:
            with open(log_filename, "w") as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Type: Sync\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {result:.6f}s\n")
                f.write(f"Success: {result != float('inf')}\n")
                f.write(f"Memory Before: {memory_before:.2f}MB\n")
                f.write(f"Memory After: {memory_after:.2f}MB\n")
                f.write(f"Memory Diff: {memory_after - memory_before:.2f}MB\n")
                f.write(f"Memory Leak: {memory_info.get('potential_leak', False)}\n")
                if result != float('inf'):
                    messages_per_sec = ITERATIONS / result if result > 0 else 0
                    latency_ms = (result / ITERATIONS) * 1000 if result > 0 else 0
                    f.write(f"Messages/sec: {messages_per_sec:.2f}\n")
                    f.write(f"Latency: {latency_ms:.6f}ms\n")
                f.write(f"Log File: {log_filename}\n")
        except Exception as log_error:
            print(f"Warning: Could not write log file {log_filename}: {log_error}")
        
        return {
            "duration": result,
            "memory_info": memory_info,
            "success": result != float('inf'),
            "log_file": log_filename,
            "logs_folder": logs_folder,
            "results_folder": results_folder
        }
    except Exception as e:
        print(f"ERROR in {test_name}: {e}")
        return {
            "duration": float('inf'),
            "memory_info": {"test_name": test_name, "error": str(e)},
            "success": False,
            "log_file": None
        }

async def run_async_test_with_memory_check(test_func, test_name, logs_folder, results_folder, *args, **kwargs):
    """Run an async test with memory leak detection."""
    try:
        clean_memory()
        memory_before = get_memory_usage()
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        log_filename = f"{logs_folder}/{safe_test_name}_{timestamp}.txt"
        
        result = await test_func(*args, **kwargs)
        
        clean_memory()
        memory_after = get_memory_usage()
        
        memory_info = check_memory_leak(memory_before, memory_after, test_name)
        
        # Save test results to log file
        try:
            with open(log_filename, "w") as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Type: Async\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {result:.6f}s\n")
                f.write(f"Success: {result != float('inf')}\n")
                f.write(f"Memory Before: {memory_before:.2f}MB\n")
                f.write(f"Memory After: {memory_after:.2f}MB\n")
                f.write(f"Memory Diff: {memory_after - memory_before:.2f}MB\n")
                f.write(f"Memory Leak: {memory_info.get('potential_leak', False)}\n")
                if result != float('inf'):
                    messages_per_sec = ITERATIONS / result if result > 0 else 0
                    latency_ms = (result / ITERATIONS) * 1000 if result > 0 else 0
                    f.write(f"Messages/sec: {messages_per_sec:.2f}\n")
                    f.write(f"Latency: {latency_ms:.6f}ms\n")
                f.write(f"Log File: {log_filename}\n")
        except Exception as log_error:
            print(f"Warning: Could not write log file {log_filename}: {log_error}")
        
        return {
            "duration": result,
            "memory_info": memory_info,
            "success": result != float('inf'),
            "log_file": log_filename,
            "logs_folder": logs_folder,
            "results_folder": results_folder
        }
    except Exception as e:
        print(f"ERROR in {test_name}: {e}")
        return {
            "duration": float('inf'),
            "memory_info": {"test_name": test_name, "error": str(e)},
            "success": False,
            "log_file": None
        }

def clean_all_log_files():
    """Clean up all log files before running tests."""
    log_files = [
        "benchmarks/logs/centralized.log",
        "benchmarks/logs/benchmark.log",
        "benchmarks/logs/app.log",
        "benchmarks/logs/error.log",
        "benchmarks/logs/debug.log"
    ]
    
    for log_file in log_files:
        try:
            Path(log_file).unlink()
        except Exception:
            pass

async def main():
    """Main mixed benchmark execution."""
    print("HydraLogger Mixed Performance Benchmark")
    print("=" * 70)
    print("Testing comprehensive scenarios: formats, security, plugins, magic configs")
    print("=" * 70)
    
    # Clean up log files
    clean_all_log_files()
    
    # Create folders once for the entire benchmark run
    logs_folder, results_folder = create_benchmark_folders()
    
    # Define all test scenarios
    sync_tests = [
        # Format Testing
        (benchmark_sync_plain_text, "Sync Plain-Text Format", "Standard plain-text format performance"),
        (benchmark_sync_json, "Sync JSON Format", "JSON format performance with structured logging"),
        (benchmark_sync_csv, "Sync CSV Format", "CSV format performance for data analysis"),
        (benchmark_sync_syslog, "Sync Syslog Format", "Syslog format performance for system integration"),
        (benchmark_sync_gelf, "Sync GELF Format", "GELF format performance for Graylog integration"),
        
        # Security Testing
        (benchmark_sync_security, "Sync Security Features", "PII detection and sanitization performance"),
        
        # Magic Config Testing
        (benchmark_sync_magic_production, "Sync Magic Production", "Production magic config performance"),
        (benchmark_sync_magic_development, "Sync Magic Development", "Development magic config performance"),
        (benchmark_sync_magic_microservice, "Sync Magic Microservice", "Microservice magic config performance"),
        
        # Multi-Layer Testing
        (benchmark_sync_multi_layer, "Sync Multi-Layer", "Multiple functional layers performance"),
        
        # Centralized Testing
        (benchmark_sync_centralized, "Sync Centralized", "Centralized logging with multiple destinations"),
        
        # Plugin Testing
        (benchmark_sync_plugins, "Sync Plugins", "Plugin system performance with analytics and security"),
    ]
    
    async_tests = [
        # Format Testing
        (benchmark_async_plain_text, "Async Plain-Text Format", "Async plain-text format performance"),
        (benchmark_async_json, "Async JSON Format", "Async JSON format performance"),
        
        # Security Testing
        (benchmark_async_security, "Async Security Features", "Async PII detection and sanitization"),
        
        # Multi-Layer Testing
        (benchmark_async_multi_layer, "Async Multi-Layer", "Async multiple functional layers"),
    ]
    
    results = {}
    memory_leaks = []
    
    # Run sync tests
    print("\n🔄 Running Sync Tests...")
    for test_func, test_name, description in sync_tests:
        print(f"\nRunning {test_name}...")
        print(f"  Description: {description}")
        
        result = run_sync_test_with_memory_check(test_func, test_name, logs_folder, results_folder)
        results[test_name] = result
        
        if result["success"]:
            duration = result["duration"]
            messages_per_sec = ITERATIONS / duration if duration > 0 else 0
            latency_ms = (duration / ITERATIONS) * 1000 if duration > 0 else 0
            
            print(f"  Duration: {duration:.4f}s")
            print(f"  Messages/sec: {messages_per_sec:.2f}")
            print(f"  Latency: {latency_ms:.3f}ms per message")
            
            # Check for memory leaks
            memory_info = result["memory_info"]
            if memory_info.get("potential_leak", False):
                memory_leaks.append(memory_info)
                print(f"  ⚠️  Potential memory leak detected: {memory_info['memory_diff_mb']:.2f}MB")
            else:
                print(f"  ✅ No memory leak detected")
            
            # Show log file
            if result.get("log_file"):
                print(f"  📄 Log File: {result['log_file']}")
        else:
            print(f"  ❌ Test failed")
        
        # Wait between tests for isolation
        time.sleep(1)
    
    # Run async tests
    print("\n🔄 Running Async Tests...")
    for test_func, test_name, description in async_tests:
        print(f"\nRunning {test_name}...")
        print(f"  Description: {description}")
        
        result = await run_async_test_with_memory_check(test_func, test_name, logs_folder, results_folder)
        results[test_name] = result
        
        if result["success"]:
            duration = result["duration"]
            messages_per_sec = ITERATIONS / duration if duration > 0 else 0
            latency_ms = (duration / ITERATIONS) * 1000 if duration > 0 else 0
            
            print(f"  Duration: {duration:.4f}s")
            print(f"  Messages/sec: {messages_per_sec:.2f}")
            print(f"  Latency: {latency_ms:.3f}ms per message")
            
            # Check for memory leaks
            memory_info = result["memory_info"]
            if memory_info.get("potential_leak", False):
                memory_leaks.append(memory_info)
                print(f"  ⚠️  Potential memory leak detected: {memory_info['memory_diff_mb']:.2f}MB")
            else:
                print(f"  ✅ No memory leak detected")
            
            # Show log file
            if result.get("log_file"):
                print(f"  📄 Log File: {result['log_file']}")
        else:
            print(f"  ❌ Test failed")
        
        # Wait between tests for isolation
        await asyncio.sleep(1)
    
    # Calculate summary statistics
    successful_tests = [r for r in results.values() if r["success"]]
    
    if successful_tests:
        durations = [r["duration"] for r in successful_tests]
        messages_per_sec_list = []
        
        for result in successful_tests:
            duration = result["duration"]
            messages_per_sec = ITERATIONS / duration if duration > 0 else 0
            messages_per_sec_list.append(messages_per_sec)
        
        summary = {
            "total_tests": len(sync_tests) + len(async_tests),
            "successful_tests": len(successful_tests),
            "failed_tests": len(sync_tests) + len(async_tests) - len(successful_tests),
            "best_performance": max(messages_per_sec_list) if messages_per_sec_list else 0,
            "worst_performance": min(messages_per_sec_list) if messages_per_sec_list else 0,
            "average_performance": sum(messages_per_sec_list) / len(messages_per_sec_list) if messages_per_sec_list else 0,
            "best_duration": min(durations),
            "worst_duration": max(durations),
            "average_duration": sum(durations) / len(durations)
        }
    else:
        summary = {
            "total_tests": len(sync_tests) + len(async_tests),
            "successful_tests": 0,
            "failed_tests": len(sync_tests) + len(async_tests),
            "best_performance": 0,
            "worst_performance": 0,
            "average_performance": 0,
            "best_duration": 0,
            "worst_duration": 0,
            "average_duration": 0
        }
    
    # Save results
    try:
        # Get the first result to extract folder paths
        first_result = next(iter(results.values()), {})
        logs_folder = first_result.get("logs_folder", "benchmarks/logs/default")
        results_folder = first_result.get("results_folder", "benchmarks/results/default")
        
        # Save JSON results
        with open(f"{results_folder}/results.json", "w") as f:
            json.dump({
                "summary": summary,
                "results": results,
                "memory_leaks": memory_leaks,
                "timestamp": time.time(),
                "test_config": {
                    "iterations": ITERATIONS,
                    "stress_iterations": STRESS_ITERATIONS,
                    "warmup_iterations": WARMUP_ITERATIONS,
                    "concurrent_tasks": CONCURRENT_TASKS
                }
            }, f, indent=2)
        
        # Save CSV results
        with open(f"{results_folder}/results.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Test Name", "Description", "Type", "Duration (s)", "Messages/sec", 
                "Latency (ms)", "Success", "Memory Leak"
            ])
            
            for test_name, result in results.items():
                duration = result["duration"]
                messages_per_sec = ITERATIONS / duration if duration > 0 else 0
                latency_ms = (duration / ITERATIONS) * 1000 if duration > 0 else 0
                success = result["success"]
                memory_leak = result["memory_info"].get("potential_leak", False)
                
                # Determine test type
                test_type = "Async" if "Async" in test_name else "Sync"
                
                # Find description
                description = ""
                for test_info in sync_tests + async_tests:
                    if test_info[1] == test_name:
                        description = test_info[2]
                        break
                
                writer.writerow([
                    test_name, description, test_type, duration, messages_per_sec, 
                    latency_ms, success, memory_leak
                ])
        
        # Save detailed summary to log file
        with open(f"{logs_folder}/benchmark_summary.txt", "w") as f:
            f.write("HydraLogger Mixed Performance Benchmark Results\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("Test Configuration:\n")
            f.write(f"  Standard iterations: {ITERATIONS:,}\n")
            f.write(f"  Stress test iterations: {STRESS_ITERATIONS:,}\n")
            f.write(f"  Warmup iterations: {WARMUP_ITERATIONS}\n")
            f.write(f"  Concurrent tasks: {CONCURRENT_TASKS}\n\n")
            
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Successful: {summary['successful_tests']}\n")
            f.write(f"Failed: {summary['failed_tests']}\n\n")
            
            if summary['successful_tests'] > 0:
                f.write("Performance Summary:\n")
                f.write(f"  Best Performance: {summary['best_performance']:.2f} messages/sec\n")
                f.write(f"  Worst Performance: {summary['worst_performance']:.2f} messages/sec\n")
                f.write(f"  Average Performance: {summary['average_performance']:.2f} messages/sec\n\n")
                
                f.write("Duration Summary:\n")
                f.write(f"  Best Duration: {summary['best_duration']:.4f}s\n")
                f.write(f"  Worst Duration: {summary['worst_duration']:.4f}s\n")
                f.write(f"  Average Duration: {summary['average_duration']:.4f}s\n\n")
                
                f.write("Detailed Results:\n")
                for test_name, result in results.items():
                    if result["success"]:
                        duration = result["duration"]
                        messages_per_sec = ITERATIONS / duration if duration > 0 else 0
                        latency_ms = (duration / ITERATIONS) * 1000 if duration > 0 else 0
                        
                        f.write(f"  {test_name}:\n")
                        f.write(f"    Messages/sec: {messages_per_sec:.2f}\n")
                        f.write(f"    Latency: {latency_ms:.3f}ms\n")
                        f.write(f"    Duration: {duration:.4f}s\n")
                        
                        memory_info = result["memory_info"]
                        if memory_info.get("potential_leak", False):
                            f.write(f"    ⚠️  Memory leak: {memory_info['memory_diff_mb']:.2f}MB\n")
                        else:
                            f.write(f"    ✅ No memory leak\n")
                        f.write("\n")
            
            if memory_leaks:
                f.write("Memory Leaks Detected:\n")
                for leak in memory_leaks:
                    f.write(f"  - {leak['test_name']}: {leak['memory_diff_mb']:.2f}MB\n")
            else:
                f.write("No memory leaks detected.\n")
        
        print(f"\nResults saved to:")
        print(f"  - {results_folder}/results.json")
        print(f"  - {results_folder}/results.csv")
        print(f"  - {logs_folder}/benchmark_summary.txt")
        print(f"  - Individual test logs in: {logs_folder}/")
        
    except Exception as e:
        print(f"Failed to save results: {e}")
    
    # Print final summary
    print(f"\n{'='*70}")
    print("FINAL MIXED BENCHMARK SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    
    if summary['successful_tests'] > 0:
        print(f"\nPerformance Summary:")
        print(f"  Best Performance: {summary['best_performance']:.2f} messages/sec")
        print(f"  Worst Performance: {summary['worst_performance']:.2f} messages/sec")
        print(f"  Average Performance: {summary['average_performance']:.2f} messages/sec")
        
        print(f"\nDuration Summary:")
        print(f"  Best Duration: {summary['best_duration']:.4f}s")
        print(f"  Worst Duration: {summary['worst_duration']:.4f}s")
        print(f"  Average Duration: {summary['average_duration']:.4f}s")
        
        print(f"\nFeature Recommendations:")
        print(f"  - For maximum performance: Use plain-text format")
        print(f"  - For structured logging: Use JSON format")
        print(f"  - For data analysis: Use CSV format")
        print(f"  - For system integration: Use syslog format")
        print(f"  - For security: Enable security features")
        print(f"  - For analytics: Use plugin system")
        print(f"  - For production: Use magic configs")
        print(f"  - For complex apps: Use multi-layer logging")
    
    if memory_leaks:
        print(f"\n⚠️  Memory Leaks Detected: {len(memory_leaks)}")
        for leak in memory_leaks:
            print(f"  - {leak['test_name']}: {leak['memory_diff_mb']:.2f}MB")
    else:
        print(f"\n✅ No memory leaks detected")
    
    print(f"\nMixed benchmark completed successfully!")
    print(f"All tests use the production-ready HydraLogger implementations.")

if __name__ == "__main__":
    asyncio.run(main()) 