"""
example_colors.py
Demonstrates how to customize log colors for different levels and outputs.
"""

import os
from hydra_logger import HydraLogger

print("=== HydraLogger Color Customization Examples ===\n")

# Example 1: Default colors
print("1. Default Professional Colors:")
logger = HydraLogger()
logger.debug("DEFAULT", "This is a cyan debug message.")
logger.info("DEFAULT", "This is a green info message.")
logger.warning("DEFAULT", "This is a yellow warning message.")
logger.error("DEFAULT", "This is a red error message.")
logger.critical("DEFAULT", "This is a bright red critical message.")

print("\n" + "="*50 + "\n")

# Example 2: Custom colors using environment variables
print("2. Custom Colors (using environment variables):")
os.environ["HYDRA_LOG_COLOR_DEBUG"] = "bright_cyan"
os.environ["HYDRA_LOG_COLOR_INFO"] = "bright_green"
os.environ["HYDRA_LOG_COLOR_WARNING"] = "bright_yellow"
os.environ["HYDRA_LOG_COLOR_ERROR"] = "bright_red"
os.environ["HYDRA_LOG_COLOR_CRITICAL"] = "bright_magenta"
os.environ["HYDRA_LOG_LAYER_COLOR"] = "bright_blue"

logger2 = HydraLogger()
logger2.debug("CUSTOM", "This is a bright cyan debug message.")
logger2.info("CUSTOM", "This is a bright green info message.")
logger2.warning("CUSTOM", "This is a bright yellow warning message.")
logger2.error("CUSTOM", "This is a bright red error message.")
logger2.critical("CUSTOM", "This is a bright magenta critical message.")

print("\n" + "="*50 + "\n")

# Example 3: Disable colors
print("3. Colors Disabled:")
os.environ["HYDRA_LOG_NO_COLOR"] = "1"
logger3 = HydraLogger()
logger3.info("NO_COLOR", "This message has no colors.")
logger3.error("NO_COLOR", "This error has no colors.")

print("\n" + "="*50 + "\n")

# Example 4: Force colors
print("4. Force Colors (even in non-TTY environments):")
os.environ.pop("HYDRA_LOG_NO_COLOR", None)  # Remove no-color setting
os.environ["HYDRA_LOG_FORCE_COLOR"] = "1"
os.environ["HYDRA_LOG_COLOR_INFO"] = "green"
os.environ["HYDRA_LOG_COLOR_ERROR"] = "red"
os.environ["HYDRA_LOG_LAYER_COLOR"] = "cyan"

logger4 = HydraLogger()
logger4.info("FORCE", "This message has forced colors.")
logger4.error("FORCE", "This error has forced colors.")

print("\n" + "="*50 + "\n")

# Example 5: Available named colors
print("5. Available Named Colors:")
print("Basic colors: red, green, yellow, blue, magenta, cyan, white")
print("Bright colors: bright_red, bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan")
print("\nEnvironment variables you can set:")
print("- HYDRA_LOG_COLOR_DEBUG")
print("- HYDRA_LOG_COLOR_INFO") 
print("- HYDRA_LOG_COLOR_WARNING")
print("- HYDRA_LOG_COLOR_ERROR")
print("- HYDRA_LOG_COLOR_CRITICAL")
print("- HYDRA_LOG_LAYER_COLOR")
print("- HYDRA_LOG_NO_COLOR (set to '1', 'true', or 'yes' to disable)")
print("- HYDRA_LOG_FORCE_COLOR (set to '1', 'true', or 'yes' to force)")

print("\n" + "="*50 + "\n")

# Example 6: ANSI codes (advanced)
print("6. Using ANSI Codes (Advanced):")
os.environ["HYDRA_LOG_COLOR_INFO"] = "\\033[32m"  # Green
os.environ["HYDRA_LOG_COLOR_ERROR"] = "\\033[31m"  # Red
os.environ["HYDRA_LOG_LAYER_COLOR"] = "\\033[35m"  # Magenta

logger5 = HydraLogger()
logger5.info("ANSI", "This uses ANSI color codes.")
logger5.error("ANSI", "This error uses ANSI color codes.")