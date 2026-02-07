"""Structured logging configuration using structlog.

This module provides:
- Structlog configuration for JSON and console output
- Custom formatters for Django's logging
- Utility functions for logging with context
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def add_correlation_id(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add correlation ID to log events.

    Args:
        logger: The wrapped logger.
        method_name: The logging method name.
        event_dict: The current event dictionary.

    Returns:
        Event dictionary with correlation_id added.
    """
    from shared.middleware import get_correlation_id

    correlation_id = get_correlation_id()
    if correlation_id and "correlation_id" not in event_dict:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_tenant_id(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add tenant ID to log events.

    Args:
        logger: The wrapped logger.
        method_name: The logging method name.
        event_dict: The current event dictionary.

    Returns:
        Event dictionary with tenant_id added.
    """
    from shared.middleware import get_tenant_id

    tenant_id = get_tenant_id()
    if tenant_id and "tenant_id" not in event_dict:
        event_dict["tenant_id"] = str(tenant_id)
    return event_dict


def drop_color_message_key(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Remove the color_message key from log events.

    Args:
        logger: The wrapped logger.
        method_name: The logging method name.
        event_dict: The current event dictionary.

    Returns:
        Event dictionary without color_message.
    """
    event_dict.pop("color_message", None)
    return event_dict


def configure_structlog(json_format: bool = False) -> None:
    """Configure structlog for the application.

    Args:
        json_format: If True, output JSON format; otherwise, use console format.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_correlation_id,
        add_tenant_id,
    ]

    if json_format:
        # JSON format for production
        shared_processors.append(drop_color_message_key)
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # Console format for development
        renderer = structlog.dev.ConsoleRenderer(
            colors=sys.stdout.isatty(),
        )

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


class StructlogFormatter(logging.Formatter):
    """Custom formatter that outputs logs in structlog JSON format.

    This formatter is used by Django's logging configuration to format
    logs from the standard library using structlog's JSON renderer.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the formatter."""
        super().__init__(*args, **kwargs)
        self._processors: list[Processor] = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            add_correlation_id,
            add_tenant_id,
            structlog.processors.JSONRenderer(),
        ]

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON formatted log string.
        """
        event_dict: EventDict = {
            "event": record.getMessage(),
            "_logger": record.name,
            "_level": record.levelname.lower(),
        }

        # Add exception info if present
        if record.exc_info:
            event_dict["exc_info"] = self.formatException(record.exc_info)

        # Add extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "taskName",
            ):
                event_dict[key] = value

        # Process through structlog processors
        for processor in self._processors:
            event_dict = processor(None, record.levelname.lower(), event_dict)  # type: ignore[arg-type]

        return str(event_dict)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance.

    Args:
        name: Optional logger name. Defaults to caller's module name.

    Returns:
        Configured structlog logger.

    Example:
        logger = get_logger(__name__)
        logger.info("user_created", user_id=str(user.id))
    """
    return structlog.get_logger(name)
