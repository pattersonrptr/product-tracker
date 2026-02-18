"""Request/Response logging middleware."""

import time

from fastapi import Request

from src.config.logging_config import get_logger

logger = get_logger(__name__)


async def log_requests_middleware(request: Request, call_next):
    """
    Log all HTTP requests with timing information.

    Logs:
    - Incoming request method and path
    - Response status code and duration
    - Errors with stack traces

    Args:
        request: FastAPI Request object
        call_next: Next middleware in chain

    Returns:
        Response object from next middleware
    """
    start_time = time.time()

    # Log incoming request
    logger.info(
        f"→ Request: {request.method} {request.url.path}",
        extra={
            'method': request.method,
            'path': request.url.path,
            'client_host': request.client.host if request.client else None
        }
    )

    # Process request
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        log_level = logger.info if response.status_code < 400 else logger.error
        log_level(
            f"← Response: {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
            extra={
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms
            }
        )
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception(
            f"✗ Error: {request.method} {request.url.path} ({duration_ms:.2f}ms): {str(e)}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'duration_ms': duration_ms
            }
        )
        raise
