"""
example_jupyter.py
Best practices for using HydraLogger in Jupyter environments.
"""

from hydra_logger import HydraLogger

# Jupyter-optimized logger
logger = HydraLogger()

# Basic logging in Jupyter
logger.info("JUPYTER", "Starting data analysis...")

# Logging with rich output
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
logger.info("JUPYTER", f"Loaded dataset with shape: {df.shape}")

# Error handling in Jupyter
try:
    result = 10 / 0
except ZeroDivisionError as e:
    logger.error("JUPYTER", f"Division by zero error: {e}")

logger.info("JUPYTER", "Analysis completed successfully!") 