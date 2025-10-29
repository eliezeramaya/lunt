"""
Logging configuration for Lunt API.

Provides structured JSON logging for production environments with:
- Timestamp in ISO format
- Log level
- Logger name
- HTTP request details (method, path, status, latency)
- Trace ID support (for distributed tracing)

NOTE: In development, you can set JSON_LOGS=false in .env for human-readable logs
"""

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds context-aware fields.

    Adds standard fields for all log records:
    - timestamp: ISO 8601 format
    - level: Log level name
    - logger: Logger name
    - message: Log message

    For HTTP requests (if extra fields provided):
    - http.method: HTTP method
    - http.path: Request path
    - http.status_code: Response status
    - latency_ms: Request processing time in milliseconds
    - trace_id: Distributed tracing ID (if available)
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        # Add extra fields if present (e.g., from HTTP middleware)
        if hasattr(record, "http_method"):
            log_record["http.method"] = record.http_method
        if hasattr(record, "http_path"):
            log_record["http.path"] = record.http_path
        if hasattr(record, "status_code"):
            log_record["http.status_code"] = record.status_code
        if hasattr(record, "latency_ms"):
            log_record["latency_ms"] = record.latency_ms
        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id


def configure_logging(
    level: str = "INFO",
    json_logs: bool = True,
) -> None:
    """
    Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output JSON formatted logs. If False, human-readable.

    NOTE: Call this function early in application startup (in main.py)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    if json_logs:
        # JSON formatter for production
        formatter = CustomJsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Configure uvicorn loggers to use the same format
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.handlers = [handler]
        logger.setLevel(log_level)
        logger.propagate = False

    # Log configuration
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": level,
            "json_logs": json_logs,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", extra={"user_id": 123})
    """
    return logging.getLogger(name)
