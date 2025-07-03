"""
Hydra-Logger: A dynamic, multi-headed logging system for Python applications.

A standalone, reusable logging module that supports:
- Multi-layered logging with different destinations per layer
- Custom folder paths for each log file
- Configuration via YAML/TOML files
- Backward compatibility with simple setup_logging()
"""

from hydra_logger.logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.compatibility import setup_logging, migrate_to_hydra

__version__ = "0.1.0"
__author__ = "Hydra-Logger Team"

__all__ = [
    "HydraLogger",
    "LoggingConfig", 
    "LogLayer",
    "LogDestination",
    "setup_logging",
    "migrate_to_hydra"
] 