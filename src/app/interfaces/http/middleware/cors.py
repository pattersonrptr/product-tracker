"""CORS middleware configuration."""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the application.
    
    Allows requests from localhost development servers on ports 3000.
    In production, this should be configured with specific origins.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
