"""Middleware registration and setup."""

from fastapi import FastAPI
from src.app.interfaces.http.middleware.cors import setup_cors
from src.app.interfaces.http.middleware.logging import log_requests_middleware
from src.app.interfaces.http.middleware.jsonapi import jsonapi_content_type_middleware


def setup_middleware(app: FastAPI) -> None:
    """
    Register all middleware for the application.
    
    Middleware execution order (LIFO - Last In, First Out):
    1. JSON:API content-type adjustment (last registered, executes first on response)
    2. Request/Response logging
    3. CORS (first registered, executes first on request)
    
    Args:
        app: FastAPI application instance
    """
    # CORS middleware (executes first on request)
    setup_cors(app)
    
    # Request logging middleware
    app.middleware("http")(log_requests_middleware)
    
    # JSON:API content-type middleware (executes last on response)
    app.middleware("http")(jsonapi_content_type_middleware)
