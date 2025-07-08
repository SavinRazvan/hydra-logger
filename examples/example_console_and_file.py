"""
example_console_and_file.py
Demonstrates logging to both console and file simultaneously.
"""

import os
from hydra_logger import HydraLogger

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Console and file logging
logger = HydraLogger()

logger.debug("CONSOLE_FILE", "This is a debug message.")
logger.info("CONSOLE_FILE", "This appears in both console and file.")
logger.warning("CONSOLE_FILE", "This warning is also in both places.")
logger.error("CONSOLE_FILE", "This error is logged everywhere.")

print(f"Logs also written to: {os.path.join(logs_dir, 'combined.log')}") 