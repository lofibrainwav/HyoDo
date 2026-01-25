"""
AFO Kingdom Structured Logger
Trinity Score: 眞 (Truth) - Observability & Transparency
Author: AFO Kingdom Development Team
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any


class StructuredLogger:
    """
    JSON-based Structured Logger.
    Compatible with standard logging.Logger but outputs structured JSON.
    """

    def __init__(self, name: str, level: str = "INFO") -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Ensure we have a handler that just outputs the message (JSON)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log(
        self,
        level: str,
        message: str,
        context: dict[str, Any] | None = None,
        exc_info: bool = False,
    ):
        """Internal log method that formats to JSON"""

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "message": message,
            "context": context or {},
        }

        log_json = json.dumps(entry)

        if level == "INFO":
            self.logger.info(log_json)
        elif level == "WARNING":
            self.logger.warning(log_json)
        elif level == "ERROR":
            self.logger.error(log_json, exc_info=exc_info)
        elif level == "DEBUG":
            self.logger.debug(log_json)

    def info(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log info message with context"""
        self._log("INFO", message, context)

    def error(
        self, message: str, context: dict[str, Any] | None = None, exc_info: bool = True
    ) -> None:
        """Log error message with context"""
        self._log("ERROR", message, context, exc_info=exc_info)

    def warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log warning message with context"""
        self._log("WARNING", message, context)

    def debug(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log debug message with context"""
        self._log("DEBUG", message, context)
