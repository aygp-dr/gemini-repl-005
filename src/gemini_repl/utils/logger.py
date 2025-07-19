# Logging System


# [[file:../../../PYTHON-GEMINI-REPL.org::*Logging System][Logging System:1]]
"""Logging system with file and console output."""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class Logger:
    """Custom logger with JSON formatting and multiple outputs."""

    def __init__(self, log_file=None, use_home_dir=True):
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Default to ~/.gemini for persistence, logs/ for development
        if log_file:
            self.log_file = log_file
        elif use_home_dir:
            home_gemini = Path.home() / ".gemini"
            home_gemini.mkdir(exist_ok=True)
            self.log_file = str(home_gemini / "gemini-repl.log")
        else:
            self.log_file = "logs/gemini.log"

        self.log_format = os.getenv("LOG_FORMAT", "json")

        # Ensure log directory exists
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger("gemini_repl")
        self.logger.setLevel(getattr(logging, self.log_level))

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add file handler
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(file_handler)

        # Add console handler for errors
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)

    def _get_formatter(self):
        """Get appropriate formatter based on format setting."""
        if self.log_format == "json":
            return JsonFormatter()
        else:
            return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def set_level(self, level: str):
        """Change log level at runtime."""
        self.logger.setLevel(getattr(logging, level))
        self.log_level = level

    # Logging methods
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log("DEBUG", message, data)

    def info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log("INFO", message, data)

    def warning(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log("WARNING", message, data)

    def error(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log("ERROR", message, data)

    def _log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Internal logging method."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {},
        }

        # Log to file/console
        log_method = getattr(self.logger, level.lower())
        if self.log_format == "json":
            log_method(json.dumps(record))
        else:
            log_method(f"{message} - {json.dumps(data) if data else ''}")

    def shutdown(self):
        """Shutdown logger and cleanup resources."""
        # Close handlers properly
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers.clear()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        return json.dumps(log_obj)


# Logging System:1 ends here
