"""
Hydra-Logger: A dynamic, multi-headed logging system for Python applications.

A standalone, reusable logging module that supports:
- Multi-layered logging with different destinations per layer
- Custom folder paths for each log file
- Configuration via YAML/TOML files
- Backward compatibility with simple setup_logging()
"""

from hydra_logger.compatibility import migrate_to_hydra, setup_logging
from hydra_logger.config import LogDestination, LoggingConfig, LogLayer
from hydra_logger.logger import HydraLogger, HydraLoggerError

__version__ = "0.2.0"
__author__ = "Savin Ionut Razvan"

__all__ = [
    "HydraLogger",
    "HydraLoggerError",
    "LoggingConfig",
    "LogLayer",
    "LogDestination",
    "setup_logging",
    "migrate_to_hydra",
]
