"""
Centralized logging configuration for the application.

Features:
- Structured logging with context
- Automatic log rotation
- Different log levels per environment
- Colored output for development
- JSON logs for production
- Separate logs per module
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path

from src.config import settings


class ColoredFormatter(logging.Formatter):
    """
    Colored log formatter for console output (development).
    Makes logs easier to read during development.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
            )

        # Format the message
        formatted = super().format(record)
        return formatted


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for production logs.
    Makes logs easy to parse and analyze with log aggregation tools.
    """

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint

        return json.dumps(log_data)


def setup_logging(
    app_name: str = "product-tracker",
    log_level: str | None = None,
    log_dir: Path | None = None,
    enable_console: bool = True,
    enable_file: bool = True,
    json_logs: bool = False,
) -> None:
    """
    Configure logging for the entire application.

    Args:
        app_name: Name of the application (used for log file names)
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        enable_console: Enable console (stdout) logging
        enable_file: Enable file logging
        json_logs: Use JSON format for logs (recommended for production)
    """

    # Determine log level
    if log_level is None:
        log_level = getattr(settings, "LOG_LEVEL", "INFO")

    # Determine log directory
    if log_dir is None:
        log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console Handler (for development)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        if json_logs:
            console_formatter = JsonFormatter()
        else:
            console_formatter = ColoredFormatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File Handler (rotating logs)
    if enable_file:
        # Main application log (all levels)
        main_log_file = log_dir / f"{app_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # Capture everything in file

        if json_logs:
            file_formatter = JsonFormatter()
        else:
            file_formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Error log (only errors and critical)
        error_log_file = log_dir / f"{app_name}-error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)

    # Log the configuration
    root_logger.info(
        f"Logging configured: level={log_level}, console={enable_console}, "
        f"file={enable_file}, json={json_logs}, dir={log_dir}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Usage:
        logger = get_logger(__name__)
        logger.info("This is an info message")
        logger.error("This is an error message")

    Args:
        name: Name of the logger (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter to add contextual information to logs.

    Usage:
        logger = LoggerAdapter(get_logger(__name__), {'user_id': 123, 'request_id': 'abc'})
        logger.info("User logged in")  # Will include user_id and request_id
    """

    def process(self, msg, kwargs):
        # Add extra context to the log record
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


# Example usage functions for common patterns
def log_api_request(
    logger: logging.Logger, method: str, path: str, user_id: int | None = None
):
    """Helper to log API requests consistently."""
    extra = {"endpoint": f"{method} {path}"}
    if user_id:
        extra["user_id"] = user_id
    logger.info(f"API Request: {method} {path}", extra=extra)


def log_api_response(
    logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float
):
    """Helper to log API responses consistently."""
    extra = {
        "endpoint": f"{method} {path}",
        "status_code": status_code,
        "duration_ms": duration_ms,
    }
    level = logging.INFO if 200 <= status_code < 400 else logging.ERROR
    logger.log(
        level,
        f"API Response: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
        extra=extra,
    )


def log_database_query(
    logger: logging.Logger, query_type: str, table: str, duration_ms: float
):
    """Helper to log database queries consistently."""
    extra = {"query_type": query_type, "table": table, "duration_ms": duration_ms}
    logger.debug(
        f"DB Query: {query_type} on {table} ({duration_ms:.2f}ms)", extra=extra
    )


def log_user_action(logger: logging.Logger, user_id: int, action: str, resource: str):
    """Helper to log user actions consistently."""
    extra = {"user_id": user_id, "action": action, "resource": resource}
    logger.info(f"User {user_id} {action} {resource}", extra=extra)
