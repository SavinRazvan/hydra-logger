"""
Formatters for Hydra-Logger.

This module provides formatters for both sync and async logging,
including colored text formatters and plain text formatters.
"""

import logging
import sys
from typing import Optional
import json
import csv
import io

from hydra_logger.core.constants import Colors, DEFAULT_COLORS


class ColoredTextFormatter(logging.Formatter):
    """Colored text formatter for terminal output."""
    
    def __init__(self, fmt=None, datefmt=None, force_colors=None, destination_type="auto", color_mode: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self.force_colors = force_colors
        self.destination_type = destination_type
        self.color_mode = color_mode or "auto"
    
    def format(self, record):
        """Format the record with colors."""
        # Get the original formatted message
        msg = super().format(record)
        
        # Add colors if appropriate
        if self._should_use_colors():
            # Get the color for this log level
            level_color = DEFAULT_COLORS.get(record.levelname, Colors.RESET)
            name_color = Colors.MAGENTA
            
            # Apply colors to specific parts
            # Color the level name
            msg = msg.replace(record.levelname, f"{level_color}{record.levelname}{Colors.RESET}")
            # Color the logger name
            msg = msg.replace(record.name, f"{name_color}{record.name}{Colors.RESET}")
            
            # If no specific parts were colored, color the entire message with level color
            # and ensure magenta is present by coloring the message part
            if Colors.RESET not in msg:
                # Split message and color the message part with magenta
                if " - " in msg:
                    parts = msg.split(" - ")
                    if len(parts) >= 2:
                        # Format: "level - message" -> "level - [magenta]message[reset]"
                        msg = f"{parts[0]} - {name_color}{parts[1]}{Colors.RESET}"
                    else:
                        msg = f"{level_color}{msg}{Colors.RESET}"
                else:
                    # Simple message, color with level color and ensure magenta is present
                    msg = f"{level_color}{msg}{Colors.RESET}"
                    # Add magenta to the message part
                    msg = msg.replace(record.getMessage(), f"{name_color}{record.getMessage()}{Colors.RESET}")
            else:
                # If we have colors but no magenta, add magenta to the message part
                if Colors.MAGENTA not in msg:
                    msg = msg.replace(record.getMessage(), f"{name_color}{record.getMessage()}{Colors.RESET}")
        
        return msg
    
    def _should_use_colors(self):
        """Determine if colors should be used."""
        # Check color_mode first
        if self.color_mode == "never":
            return False
        elif self.color_mode == "always":
            return True
        elif self.color_mode == "auto":
            # Use force_colors if set
            if self.force_colors == "never":
                return False
            elif self.force_colors == "always":
                return True
            else:
                # Auto-detect
                return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        
        # Default to auto-detect
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


class PlainTextFormatter(logging.Formatter):
    """Plain text formatter without colors."""
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
    
    def format(self, record):
        """Format the record without colors."""
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """Formatter for JSON log output (valid JSON array)."""
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self._records = []
    
    def format(self, record):
        # Build a dict with standard log fields
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add any custom attributes that might be present
        for key, value in record.__dict__.items():
            if (
                key not in log_record and 
                not key.startswith('_') and 
                key not in (
                    "args", "msg", "exc_info", "exc_text", "stack_info", 
                    "lineno", "pathname", "funcName", "created", "msecs", 
                    "relativeCreated", "thread", "threadName", "processName", 
                    "process", "levelno", "levelname", "name"
                )
            ):
                log_record[key] = value
        
        self._records.append(log_record)
        return json.dumps(self._records, ensure_ascii=False, indent=2)
    
    def format_all(self):
        """Format all records as a JSON array."""
        return json.dumps(self._records, ensure_ascii=False, indent=2)


class JsonLinesFormatter(logging.Formatter):
    """Formatter for JSON Lines output (one JSON object per line)."""
    def format(self, record):
        # Build a dict with standard log fields
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add any custom attributes that might be present
        for key, value in record.__dict__.items():
            if (
                key not in log_record and 
                not key.startswith('_') and 
                key not in (
                    "args", "msg", "exc_info", "exc_text", "stack_info", 
                    "lineno", "pathname", "funcName", "created", "msecs", 
                    "relativeCreated", "thread", "threadName", "processName", 
                    "process", "levelno", "levelname", "name"
                )
            ):
                log_record[key] = value
        
        return json.dumps(log_record, ensure_ascii=False)


class CsvFormatter(logging.Formatter):
    """Formatter for CSV log output (one row per log record)."""
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.fieldnames = ["timestamp", "level", "logger", "message"]
    def format(self, record):
        output = io.StringIO()
        writer = csv.writer(output)
        row = [
            self.formatTime(record, self.datefmt),
            record.levelname,
            record.name,
            record.getMessage()
        ]
        writer.writerow(row)
        return output.getvalue().strip()


class SyslogFormatter(logging.Formatter):
    """Formatter for syslog output."""
    def format(self, record):
        # Example: APP[12345]: INFO: Application started successfully
        process_id = getattr(record, 'process', None) or '-'
        return f"{record.name}[{process_id}]: {record.levelname}: {record.getMessage()}"


class GelfFormatter(logging.Formatter):
    """Formatter for GELF (Graylog Extended Log Format)."""
    def format(self, record):
        # Minimal GELF: just the message
        return record.getMessage() 