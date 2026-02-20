"""Structured JSON logging configuration for TutorFlow API."""
import logging
import json
import sys
from datetime import datetime
from typing import Any
from pythonjsonlogger import jsonlogger

from config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add application context
        log_record["app"] = settings.APP_NAME
        log_record["environment"] = settings.ENVIRONMENT
        log_record["version"] = settings.APP_VERSION

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging(
    level: str = "INFO",
    service_name: str = "tutorflow-api",
) -> logging.Logger:
    """Configure structured JSON logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name of the service for logs

    Returns:
        Configured root logger
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Use custom JSON formatter
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(logger)s %(message)s",
        timestamp=True
    )
    handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(handler)

    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    return root_logger


class LogContext:
    """Context manager for adding contextual information to logs."""

    def __init__(self, **context: Any):
        """Initialize log context.

        Args:
            **context: Key-value pairs to add to log records
        """
        self.context = context
        self.old_factory = None

    def __enter__(self):
        """Enter context and add log record factory."""
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        self.old_factory = logging.getLogRecordFactory()
        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore old factory."""
        logging.setLogRecordFactory(self.old_factory)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Structured log helpers
def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: int | None = None,
    request_id: str | None = None,
):
    """Log HTTP request with structured data."""
    logger = get_logger("tutorflow.request")
    logger.info(
        "HTTP request",
        extra={
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "request_id": request_id,
        }
    )


def log_error(
    error_type: str,
    error_message: str,
    endpoint: str | None = None,
    user_id: int | None = None,
    extra: dict[str, Any] | None = None,
):
    """Log error with structured data."""
    logger = get_logger("tutorflow.error")
    logger.error(
        error_message,
        extra={
            "error_type": error_type,
            "endpoint": endpoint,
            "user_id": user_id,
            **(extra or {}),
        }
    )


def log_business_event(
    event_type: str,
    event_data: dict[str, Any],
    user_id: int | None = None,
):
    """Log business event with structured data."""
    logger = get_logger("tutorflow.business")
    logger.info(
        event_type,
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "event_data": event_data,
        }
    )


def log_external_service_call(
    service: str,
    operation: str,
    status: str,
    duration_ms: float,
    extra: dict[str, Any] | None = None,
):
    """Log external service call with structured data."""
    logger = get_logger("tutorflow.external")
    logger.info(
        f"{service} - {operation}",
        extra={
            "service": service,
            "operation": operation,
            "status": status,
            "duration_ms": duration_ms,
            **(extra or {}),
        }
    )
