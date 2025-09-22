"""
Colored Formatter for Hydra-Logger

This module provides a simple, clean colored formatter for console output.
Colors are applied to log levels and layers for better readability.

ARCHITECTURE:
- ColoredFormatter: Simple colored text formatter for console output
- Color codes for different log levels and layers
- Clean, readable colored output
- Simple boolean control: use_colors=True/False

COLOR SCHEME:
- DEBUG: Blue
- INFO: Green  
- WARNING: Yellow
- ERROR: Red
- CRITICAL: Bright Red
- LAYER: Cyan

USAGE EXAMPLES:

Basic Colored Formatting:
    from hydra_logger.formatters.colored_formatter import ColoredFormatter
    
    # Create colored formatter
    formatter = ColoredFormatter(use_colors=True)
    
    # Create non-colored formatter (falls back to plain text)
    formatter = ColoredFormatter(use_colors=False)

Custom Format String:
    from hydra_logger.formatters.colored_formatter import ColoredFormatter
    
    # Custom format with colors
    formatter = ColoredFormatter(
        format_string="{timestamp} {level_name} {layer} {message}",
        use_colors=True
    )
"""

from typing import Optional
from .text_formatter import PlainTextFormatter
from ..types.records import LogRecord
from ..utils.time_utility import TimestampConfig
from ..core.constants import Colors


class ColoredFormatter(PlainTextFormatter):
    """
    Colored text formatter for console output.
    
    Extends PlainTextFormatter with color support for log levels and layers.
    Colors are only applied when use_colors=True.
    Uses the centralized Colors constants from core.constants.
    """
    
    # Level colors using existing constants
    LEVEL_COLORS = {
        'DEBUG': Colors.BLUE,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BRIGHT_RED,
    }
    
    def __init__(
        self, 
        format_string: str = None, 
        timestamp_config: Optional[TimestampConfig] = None,
        use_colors: bool = True
    ):
        """
        Initialize colored formatter.
        
        Args:
            format_string: Format template using {field} placeholders
            timestamp_config: Configuration for timestamp formatting
            use_colors: Whether to use colors (default: True)
        """
        super().__init__(format_string, timestamp_config)
        self.use_colors = use_colors
    
    def _colorize(self, text: str, color_code: str) -> str:
        """
        Apply color to text if colors are enabled.
        
        Args:
            text: Text to colorize
            color_code: ANSI color code from Colors constants
            
        Returns:
            Colorized text or original text if colors disabled
        """
        if not self.use_colors:
            return text
        
        return f"{color_code}{text}{Colors.RESET}"
    
    def _colorize_level(self, level_name: str) -> str:
        """
        Apply color to log level.
        
        Args:
            level_name: Log level name
            
        Returns:
            Colorized level name
        """
        color_code = self.LEVEL_COLORS.get(level_name.upper(), Colors.WHITE)
        return self._colorize(level_name, color_code)
    
    def _colorize_layer(self, layer: str) -> str:
        """
        Apply color to layer name using layer-specific colors.
        
        Args:
            layer: Layer name
            
        Returns:
            Colorized layer name
        """
        # Use the existing layer color mapping from constants
        color_code = Colors.get_layer_color(layer)
        return self._colorize(layer, color_code)
    
    def format(self, record: LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted and colorized log message
        """
        # Get the base formatted message
        message = super().format(record)
        
        if not self.use_colors:
            return message
        
        # Apply colors to level and layer in the message
        # This is a simple approach - we'll replace the level and layer in the formatted string
        level_name = getattr(record, 'level_name', 'INFO')
        layer = getattr(record, 'layer', 'default')
        
        # Colorize level and layer
        colored_level = self._colorize_level(level_name)
        colored_layer = self._colorize_layer(layer)
        
        # Replace in the formatted message
        message = message.replace(level_name, colored_level)
        message = message.replace(layer, colored_layer)
        
        return message
