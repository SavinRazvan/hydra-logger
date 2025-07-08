"""
Shared constants for Hydra-Logger.

This module defines all shared constants used throughout the Hydra-Logger system.
"""


# Version information
__version__ = "0.4.0"
__author__ = "Savin Ionut Razvan"

# Log levels
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

# Valid log formats
VALID_FORMATS = ["plain", "text", "json", "csv", "syslog", "gelf"]

# Valid destination types
VALID_DESTINATION_TYPES = ["file", "console", "async_http", "async_database", "async_queue", "async_cloud"]

# Default configuration
DEFAULT_CONFIG = {
    "default_level": "DEBUG",
    "layers": {
        "__CENTRALIZED__": {
            "level": "DEBUG",
            "destinations": [
                {
                    "type": "console",
                    "level": "DEBUG",
                    "format": "plain-text"
                }
            ]
        }
    }
}

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

# Named colors mapping
NAMED_COLORS = {
    "red": Colors.RED,
    "green": Colors.GREEN,
    "yellow": Colors.YELLOW,
    "blue": Colors.BLUE,
    "magenta": Colors.MAGENTA,
    "cyan": Colors.CYAN,
    "white": Colors.WHITE,
    "bright_red": Colors.BRIGHT_RED,
    "bright_green": Colors.BRIGHT_GREEN,
    "bright_yellow": Colors.BRIGHT_YELLOW,
    "bright_blue": Colors.BRIGHT_BLUE,
    "bright_magenta": Colors.BRIGHT_MAGENTA,
    "bright_cyan": Colors.BRIGHT_CYAN,
}

# Default colors for log levels
DEFAULT_COLORS = {
    "DEBUG": Colors.CYAN,
    "INFO": Colors.GREEN,
    "WARNING": Colors.YELLOW,
    "ERROR": Colors.RED,
    "CRITICAL": Colors.BRIGHT_RED,
}

# Performance settings
PERFORMANCE_SETTINGS = {
    "default_queue_size": 1000,
    "default_batch_size": 100,
    "default_batch_timeout": 1.0,
    "default_buffer_size": 8192,
    "default_flush_interval": 1.0,
    "memory_check_interval": 60,
}

# File settings
FILE_SETTINGS = {
    "default_encoding": "utf-8",
    "default_max_bytes": 5 * 1024 * 1024,  # 5MB
    "default_backup_count": 3,
    "default_buffer_size": 8192,
}

# Async settings
ASYNC_SETTINGS = {
    "default_retry_count": 3,
    "default_retry_delay": 1.0,
    "default_timeout": 30.0,
    "default_max_connections": 10,
}

# Plugin settings
PLUGIN_SETTINGS = {
    "default_cache_size": 1000,
    "default_plugin_timeout": 10.0,
}

# Analytics settings
ANALYTICS_SETTINGS = {
    "default_event_buffer_size": 10000,
    "default_metrics_interval": 60,
    "default_export_interval": 300,
}

# Environment variables
ENV_VARS = {
    "HYDRA_LOG_COLOR_DEBUG": "HYDRA_LOG_COLOR_DEBUG",
    "HYDRA_LOG_COLOR_INFO": "HYDRA_LOG_COLOR_INFO",
    "HYDRA_LOG_COLOR_WARNING": "HYDRA_LOG_COLOR_WARNING",
    "HYDRA_LOG_COLOR_ERROR": "HYDRA_LOG_COLOR_ERROR",
    "HYDRA_LOG_COLOR_CRITICAL": "HYDRA_LOG_COLOR_CRITICAL",
    "HYDRA_LOG_DATE_FORMAT": "HYDRA_LOG_DATE_FORMAT",
    "HYDRA_LOG_TIME_FORMAT": "HYDRA_LOG_TIME_FORMAT",
    "HYDRA_LOG_LOGGER_NAME_FORMAT": "HYDRA_LOG_LOGGER_NAME_FORMAT",
    "HYDRA_LOG_MESSAGE_FORMAT": "HYDRA_LOG_MESSAGE_FORMAT",
    "HYDRA_LOG_ENABLE_PERFORMANCE": "HYDRA_LOG_ENABLE_PERFORMANCE",
    "HYDRA_LOG_ENABLE_ANALYTICS": "HYDRA_LOG_ENABLE_ANALYTICS",
    "HYDRA_LOG_REDACT_SENSITIVE": "HYDRA_LOG_REDACT_SENSITIVE",
    "HYDRA_LOG_LAZY_INITIALIZATION": "HYDRA_LOG_LAZY_INITIALIZATION",
}

# Default formats
DEFAULT_FORMATS = {
    "date_format": "%Y-%m-%d %H:%M:%S",
    "time_format": "%H:%M:%S",
    "logger_name_format": "%(name)s",
    "message_format": "%(levelname)s - %(message)s",
}

# PII patterns for redaction
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "password": r'password["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
    "api_key": r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
    "token": r'token["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
    "secret": r'secret["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',
    "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "phone": r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
}

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "fastapi": ["fastapi", "uvicorn"],
    "django": ["django"],
    "flask": ["flask"],
    "tornado": ["tornado"],
    "aiohttp": ["aiohttp"],
}

# Cloud provider detection patterns
CLOUD_PROVIDER_PATTERNS = {
    "aws": ["AWS_", "EC2_", "ECS_", "LAMBDA_"],
    "gcp": ["GOOGLE_CLOUD_", "GCP_", "KUBERNETES_"],
    "azure": ["AZURE_", "AZURE_CLOUD_"],
    "heroku": ["HEROKU_", "DYNO_"],
    "digitalocean": ["DIGITALOCEAN_", "DROPLET_"],
} 