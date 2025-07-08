"""
example_file_output.py
Demonstrates logging to files with a dedicated logs folder.
"""

import os
from hydra_logger import HydraLogger

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_dir, exist_ok=True)

# File-only logging
logger = HydraLogger()

logger.debug("FILE", "This is a debug message.")
logger.info("FILE", "This message goes to the file only.")
logger.warning("FILE", "This warning is also in the file.")
logger.error("FILE", "This error is logged to the file.")

print(f"Logs written to: {os.path.join(logs_dir, 'example.log')}") 