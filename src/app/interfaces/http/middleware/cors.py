"""CORS middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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
        allow_origins=[
            # Legacy CRA frontend (port 3000)
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            # New Vite frontend (port 5173 default, 5174 fallback)
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
