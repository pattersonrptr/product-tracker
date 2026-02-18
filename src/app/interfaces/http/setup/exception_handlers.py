"""Exception handlers registration and setup."""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from src.app.interfaces.http.middleware.error_handlers import (
    handle_request_validation_error,
    handle_http_exception,
    handle_generic_exception,
)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for JSON:API compliance.
    
    Handles:
    - RequestValidationError: Invalid request data (422)
    - HTTPException: Standard HTTP exceptions (4xx, 5xx)
    - Exception: Unhandled exceptions (500)
    
    All responses follow JSON:API error format with proper error objects.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_generic_exception)
